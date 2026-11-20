@echo off
REM ============================================================
REM  Build de Invendesk.exe (app de escritorio independiente)
REM  Requisitos: Python 3.10+ y `pip install openpyxl pyinstaller`
REM
REM  Uso:  build.bat
REM
REM  Resultado:
REM    dist\Invendesk.exe      -> ejecutable único, corre sin Python
REM    (opcional) installer\   -> instalador con Inno Setup (Setup.iss)
REM ============================================================
setlocal

cd /d "%~dp0"

echo [1/2] Limpiando builds anteriores...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo [2/2] Empaquetando con PyInstaller (onefile, sin consola)...
py -m PyInstaller --noconfirm --clean Invendesk.spec || goto :error

echo.
echo OK. Ejecutable generado en: dist\Invendesk.exe
echo.
echo Para crear un instalador de Windows, abre Setup.iss con Inno Setup
echo (https://jrsoftware.org/isinfo.php) y compila el proyecto.
exit /b 0

:error
echo.
echo ERROR: el empaquetado fallo. Revisa que tengas: py -m pip install openpyxl pyinstaller
exit /b 1