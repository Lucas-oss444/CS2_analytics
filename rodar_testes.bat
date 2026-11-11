@echo off
cd /d "%~dp0"
python -c "import pytest" 2>nul || python -m pip install pytest
python -m pytest -q tests
pause
