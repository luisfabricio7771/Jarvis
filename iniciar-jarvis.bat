@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Falta instalar Jarvis. Consulta README.md.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" jarvis.py --ia --acciones --modelo-ia qwen2.5:3b --piper "modelos\piper\es_ES-davefx-medium.onnx"
pause
