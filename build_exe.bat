pip install pyinstaller
pyinstaller --noconfirm --windowed --name CS2Analytics --icon assets\icon.ico --add-data "assets;assets" --add-data "VERSION;." --collect-all demoparser2 main.py
