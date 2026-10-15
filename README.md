# Jarvis para Windows

Primera versión gratuita y local: reconoce comandos en español con Vosk y responde con las voces de Windows. Funciona sin una API ni suscripción. Es un prototipo de comandos definidos; aún no incorpora conversación libre ni un modelo de lenguaje.

## Instalación en Windows

Instala Python 3.11 o 3.12 de https://www.python.org/downloads/windows/ y abre PowerShell en esta carpeta:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Descarga `vosk-model-small-es-0.42` desde https://alphacephei.com/vosk/models (modelo español pequeño). Descomprime su contenido de manera que existan `modelos/vosk-es/am`, `modelos/vosk-es/conf`, etc. También puedes pasar otra ubicación con `--modelo`.

Activa el acceso al micrófono para aplicaciones de escritorio en la configuración de privacidad de Windows. Para respuesta hablada en español, instala una voz española desde la configuración de voz de Windows si no tienes ninguna.

```powershell
.\.venv\Scripts\python.exe jarvis.py
```

Pulsa Enter, habla y espera una pausa para terminar el comando. El micrófono solo se abre después de pulsar Enter y se cierra antes de responder. Ctrl+C sale. No hay activación permanente por palabra clave.

## Comandos

- `ayuda`
- `abre calculadora`
- `abre bloc de notas`
- `abre explorador`
- `crea nota comprar leche`
- `busca archivo informe`
- `salir`

Se puede anteponer «Jarvis». Las notas y búsquedas usan únicamente la carpeta `Jarvis` de tu usuario; las notas tienen nombres nuevos y no sobrescriben archivos. Puedes autorizar otra carpeta explícitamente:

```powershell
.\.venv\Scripts\python.exe jarvis.py --carpeta "$HOME\Documents\Jarvis"
```

No ejecuta comandos de terminal dictados, ni borra archivos, envía mensajes o compra. Estas capacidades necesitan herramientas específicas y confirmaciones antes de incorporarlas.

## Desarrollo y pruebas

El modo texto no requiere instalar dependencias ni descargar modelos:

```powershell
py jarvis.py --texto
py -m unittest discover -s tests -v
```

En Linux se pueden probar comandos de archivos y modo texto, pero abrir programas y validar las voces de Windows requiere una PC Windows. Las dependencias de voz y el modelo deben descargarse una vez; después el reconocimiento y la síntesis son locales.
