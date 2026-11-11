import hashlib
import py_compile
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path, PurePosixPath

from .storage import HOME

APP_ROOT = Path(__file__).resolve().parent.parent
BACKUPS = HOME / "backups"
ALLOWED = {".py", ".md", ".txt", ".bat", ".png", ".ico", ".json", ".svg"}
SKIP_DIRS = {"__pycache__", ".pytest_cache", "build", "dist", ".venv", "venv", ".git", ".github"}
NAMES = {"VERSION", "LICENSE", ".gitignore"}
SCRIPTS = {"build_exe.bat", "criar_atalho.bat", "rodar_testes.bat"}
REQUIRED = {"VERSION", "main.py", "cs2coach/__init__.py", "cs2coach/ui.py"}
RELEASES = "https://github.com/Lucas-oss444/CS2_analytics/releases"
MAX_FILES, MAX_TOTAL = 500, 50 * 1024 ** 2


class UpdateError(Exception):
    pass


def parse_version(text):
    m = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", text.strip())
    if not m:
        raise UpdateError(f"versão inválida: {text.strip()[:20]!r}")
    return tuple(int(x) for x in m.groups())


def current_version(root=APP_ROOT):
    try:
        return (root / "VERSION").read_text(encoding="utf-8").strip()
    except OSError:
        return "0.0.0"


def changelog_entry(text, version):
    m = re.search(rf"^## {re.escape(version)}\b.*?$(.*?)(?=^##? |\Z)", text, re.M | re.S)
    return m.group(1).strip() if m else ""


def _members(z):
    infos = [i for i in z.infolist() if not i.is_dir()]
    if not infos or len(infos) > MAX_FILES:
        raise UpdateError("o pacote está vazio ou tem arquivos demais.")
    names = [PurePosixPath(i.filename) for i in infos]
    top = names[0].parts[0]
    nested = all(len(n.parts) > 1 and n.parts[0] == top for n in names)
    prefix = top if nested and PurePosixPath("VERSION") not in names else None
    total, files = 0, {}
    for info, name in zip(infos, names):
        if "\\" in info.filename or name.is_absolute() or ".." in name.parts or ":" in info.filename:
            raise UpdateError(f"caminho perigoso no pacote: {info.filename}")
        if stat.S_ISLNK(info.external_attr >> 16):
            raise UpdateError(f"link simbólico não permitido: {info.filename}")
        rel = PurePosixPath(*name.parts[1:]) if prefix else name
        if set(rel.parts) & SKIP_DIRS:
            continue
        if (rel.suffix.lower() not in ALLOWED and rel.name not in NAMES) or \
                (rel.suffix.lower() == ".bat" and str(rel) not in SCRIPTS):
            raise UpdateError(f"tipo de arquivo não permitido: {rel}")
        total += info.file_size
        if total > MAX_TOTAL:
            raise UpdateError("o pacote é grande demais.")
        files[str(rel)] = info
    missing = REQUIRED - set(files)
    if missing:
        raise UpdateError("não é um pacote do CS2 Analytics (faltam: " + ", ".join(sorted(missing)) + ").")
    return files


def inspect(zip_path, root=APP_ROOT):
    try:
        with zipfile.ZipFile(zip_path) as z:
            files = _members(z)
            version = z.read(files["VERSION"]).decode("utf-8", "replace").strip()
            parse_version(version)
            log = z.read(files["CHANGELOG.md"]).decode("utf-8", "replace") if "CHANGELOG.md" in files else ""
            new_req = z.read(files["requirements.txt"]) if "requirements.txt" in files else b""
    except zipfile.BadZipFile as e:
        raise UpdateError("o arquivo não é um .zip válido.") from e
    old_req = (root / "requirements.txt").read_bytes() if (root / "requirements.txt").exists() else b""
    return {
        "sha256": hashlib.sha256(Path(zip_path).read_bytes()).hexdigest(),
        "version": version,
        "current": current_version(root),
        "newer": parse_version(version) > parse_version(current_version(root)),
        "changes": changelog_entry(log, version),
        "files": len(files),
        "requirements_changed": new_req.strip() != old_req.strip(),
    }


def _app_files(root):
    for p in root.rglob("*"):
        rel = p.relative_to(root)
        if p.is_file() and not set(rel.parts) & SKIP_DIRS and (p.suffix.lower() in ALLOWED or p.name in NAMES):
            yield rel


def backup(root=APP_ROOT):
    dest = BACKUPS / f"{current_version(root)}_{datetime.now():%Y%m%d-%H%M%S}"
    for rel in _app_files(root):
        (dest / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root / rel, dest / rel)
    backups = sorted(BACKUPS.iterdir())
    for old in backups[:-5]:
        shutil.rmtree(old, ignore_errors=True)
    return dest


def install(zip_path, root=APP_ROOT):
    info = inspect(zip_path, root)
    with tempfile.TemporaryDirectory(prefix="cs2coach_update_", dir=HOME) as tmp:
        stage = Path(tmp)
        with zipfile.ZipFile(zip_path) as z:
            files = _members(z)
            for rel, member in files.items():
                target = (stage / rel).resolve()
                if stage.resolve() not in target.parents:
                    raise UpdateError(f"caminho perigoso no pacote: {rel}")
                target.parent.mkdir(parents=True, exist_ok=True)
                with z.open(member) as src, open(target, "wb") as out:
                    shutil.copyfileobj(src, out)
        for py in stage.rglob("*.py"):
            try:
                py_compile.compile(str(py), cfile=str(Path(tmp) / "check.pyc"), doraise=True)
            except py_compile.PyCompileError as e:
                raise UpdateError(f"a atualização tem erro de código em {py.relative_to(stage)}; nada foi alterado.") from e
        saved = backup(root)
        _replace(stage, root)
    return saved, info


def _replace(src, root):
    new = set(_app_files(src))
    for rel in set(_app_files(root)) - new:
        if rel.parts[0] in ("cs2coach", "tests") and rel.suffix == ".py":
            (root / rel).unlink()
    for rel in new:
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src / rel, root / rel)


def backups():
    return sorted(BACKUPS.iterdir(), reverse=True) if BACKUPS.exists() else []


def rollback(root=APP_ROOT):
    available = backups()
    if not available:
        raise UpdateError("não há versão anterior salva.")
    latest = available[0]
    _replace(latest, root)
    shutil.rmtree(latest, ignore_errors=True)
    return current_version(root)


def install_requirements(root=APP_ROOT):
    result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(root / "requirements.txt")],
                            capture_output=True, text=True)
    return result.returncode == 0, (result.stdout + result.stderr)[-2000:]
