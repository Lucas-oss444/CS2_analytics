import os
import tempfile

_home = tempfile.mkdtemp(prefix="cs2test_home_")
os.environ["HOME"] = os.environ["USERPROFILE"] = _home
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
