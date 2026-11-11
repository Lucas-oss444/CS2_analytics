import shutil
import zipfile
from pathlib import Path

import pytest

from cs2coach import updater

REPO = Path(__file__).resolve().parent.parent


@pytest.fixture
def root(tmp_path, monkeypatch):
    app = tmp_path / "app"
    shutil.copytree(REPO, app, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", "dist", "build"))
    monkeypatch.setattr(updater, "HOME", tmp_path)
    monkeypatch.setattr(updater, "BACKUPS", tmp_path / "backups")
    return app


def package(tmp_path, version="9.0.0", extra=None, drop=(), name="up.zip"):
    path = tmp_path / name
    with zipfile.ZipFile(path, "w") as z:
        for f in REPO.rglob("*"):
            rel = f.relative_to(REPO).as_posix()
            if f.is_file() and "__pycache__" not in rel and ".pytest_cache" not in rel and rel not in drop:
                data = f.read_bytes()
                if rel == "VERSION":
                    data = version.encode()
                if rel == "CHANGELOG.md":
                    data = f"## {version}\n- novidade de teste\n\n".encode() + data
                z.writestr(f"cs2coach/{rel}", data)
        for arcname, data in (extra or {}).items():
            z.writestr(arcname, data)
    return path


def test_install_and_rollback(tmp_path, root):
    old = updater.current_version(root)
    pkg = package(tmp_path, extra={"cs2coach/cs2coach/novo.py": "X = 1\n"})
    info = updater.inspect(pkg, root)
    assert info["newer"] and info["version"] == "9.0.0" and "novidade de teste" in info["changes"]
    backup, _ = updater.install(pkg, root)
    assert updater.current_version(root) == "9.0.0"
    assert (root / "cs2coach" / "novo.py").exists()
    assert (backup / "VERSION").read_text().strip() == old
    assert updater.rollback(root) == old
    assert not (root / "cs2coach" / "novo.py").exists()


@pytest.mark.parametrize("extra", [
    {"cs2coach/../../evil.py": "x"},
    {"/etc/evil.py": "x"},
    {"cs2coach/cs2coach/malware.exe": "MZ"},
    {"cs2coach/cs2coach/script.ps1": "rm"},
    {"cs2coach/instalar.bat": "del /q *"},
])
def test_rejects_dangerous_packages(tmp_path, root, extra):
    pkg = package(tmp_path, extra=extra)
    with pytest.raises(updater.UpdateError):
        updater.install(pkg, root)
    assert updater.current_version(root) != "9.0.0"
    assert not (tmp_path.parent / "evil.py").exists()


def test_rejects_symlink(tmp_path, root):
    pkg = package(tmp_path)
    with zipfile.ZipFile(pkg, "a") as z:
        info = zipfile.ZipInfo("cs2coach/cs2coach/link.py")
        info.external_attr = (0o120777 << 16)
        z.writestr(info, "/etc/passwd")
    with pytest.raises(updater.UpdateError, match="link"):
        updater.install(pkg, root)


def test_rejects_broken_code_without_touching_app(tmp_path, root):
    before = (root / "cs2coach" / "ui.py").read_bytes()
    pkg = package(tmp_path, drop=("cs2coach/ui.py",), extra={"cs2coach/cs2coach/ui.py": "def quebrado(:\n"})
    with pytest.raises(updater.UpdateError, match="erro de código"):
        updater.install(pkg, root)
    assert (root / "cs2coach" / "ui.py").read_bytes() == before
    assert not updater.backups()


def test_rejects_foreign_zip(tmp_path, root):
    pkg = tmp_path / "outro.zip"
    with zipfile.ZipFile(pkg, "w") as z:
        z.writestr("leia.txt", "oi")
    with pytest.raises(updater.UpdateError, match="não é um pacote"):
        updater.inspect(pkg, root)
    bad = tmp_path / "bad.zip"
    bad.write_bytes(b"nao e zip")
    with pytest.raises(updater.UpdateError):
        updater.inspect(bad, root)


def test_older_version_is_flagged(tmp_path, root):
    assert not updater.inspect(package(tmp_path, version="0.0.1"), root)["newer"]
