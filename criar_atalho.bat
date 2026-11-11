@echo off
cd /d "%~dp0"
set "PYW="
for /f "delims=" %%i in ('python -c "import sys, os; print(os.path.join(os.path.dirname(sys.executable), 'pythonw.exe'))" 2^>nul') do set "PYW=%%i"
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
 "$menu = [Environment]::GetFolderPath('Programs');" ^
 "$old = @((Join-Path $menu 'CS2 Coach.lnk'), (Join-Path $menu 'CS Analytics.lnk'), (Join-Path ([Environment]::GetFolderPath('Desktop')) 'CS2 Coach.lnk'));" ^
 "$exe = Join-Path $PWD 'dist\CS2Analytics\CS2Analytics.exe';" ^
 "$pyw = $env:PYW;" ^
 "if (-not (Test-Path $exe) -and -not ($pyw -and (Test-Path $pyw))) { Write-Host 'Python nao encontrado. Instale o Python e rode pip install -r requirements.txt antes.'; exit 1 };" ^
 "$s = (New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path $menu 'CS2 Analytics.lnk'));" ^
 "if (Test-Path $exe) { $s.TargetPath = $exe } else { $q = [char]34; $s.TargetPath = $pyw; $s.Arguments = $q + (Join-Path $PWD 'main.py') + $q };" ^
 "$s.WorkingDirectory = $PWD.Path;" ^
 "$s.IconLocation = (Join-Path $PWD 'assets\icon.ico') + ',0';" ^
 "$s.Description = 'CS2 Analytics';" ^
 "$s.Save();" ^
 "foreach ($o in $old) { if (Test-Path $o) { Remove-Item $o } };" ^
 "Write-Host 'Atalho criado no Menu Iniciar. Abra o Iniciar, busque CS2 Analytics, clique com o botao direito e escolha Fixar na barra de tarefas.'"
ie4uinit.exe -show >nul 2>&1
pause
