@echo off
rem Arraste imagens e/ou PDFs em cima deste arquivo para gerar o app Visor.
cd /d "%~dp0"
python visor_hp.py %* -o saida
echo.
pause
