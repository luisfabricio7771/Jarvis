@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Falta instalar Jarvis. Consulta README.md.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" jarvis.py --ia --piper "modelos\piper\es_MX-ald-medium.onnx"
pause
