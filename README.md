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

## Conversación y voz más natural (versión 2)

La conversación usa **Ollama** en tu PC y la voz neuronal usa **Piper**. No requieren una API de pago. Internet se necesita para instalar programas y descargar los modelos. El audio y las conversaciones se procesan localmente. La memoria conserva solo los últimos seis intercambios durante la sesión; di `olvida la conversación` para borrarla. El modelo de conversación no ejecuta herramientas ni comandos del sistema.

### 1. Actualizar sin perder tus modelos

Si ya tenías Jarvis, extrae el ZIP nuevo en otra carpeta y copia sus archivos a la carpeta anterior, aceptando reemplazar los archivos del programa. Conserva tus carpetas `.venv` y `modelos`. Abre PowerShell en esa carpeta.

### 2. Instalar el modelo de conversación

Descarga e instala Ollama para Windows desde https://ollama.com/download/windows . Abre Ollama. Cierra y vuelve a abrir PowerShell para que reconozca el comando y ejecuta:

```powershell
ollama pull qwen3:4b
ollama run qwen3:4b "Responde en español: hola"
```

La descarga ocupa varios GB. El tiempo de respuesta depende del equipo. Un equipo con 32 GB de RAM y una NVIDIA RTX 3060 Ti es un buen punto de partida para este modelo. Si necesitas algo más pequeño, descarga `qwen3:1.7b` y utiliza `--modelo-ia qwen3:1.7b` al arrancar Jarvis. Mantén Ollama funcionando en segundo plano; no expongas su puerto a Internet.

Puedes probar primero la conversación sin cambiar la voz:

```powershell
.\.venv\Scripts\python.exe jarvis.py --ia
```

O usar teclado:

```powershell
.\.venv\Scripts\python.exe jarvis.py --texto --ia
```

### 3. Instalar la voz local mexicana

Desde la carpeta del proyecto ejecuta uno por uno:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-voz.txt
New-Item -ItemType Directory -Force modelos\piper
Push-Location modelos\piper
..\..\.venv\Scripts\python.exe -m piper.download_voices es_MX-ald-medium
Pop-Location
```

La descarga deja `es_MX-ald-medium.onnx` y `es_MX-ald-medium.onnx.json` juntos dentro de `modelos/piper`. El catálogo y las licencias de cada voz están en https://huggingface.co/rhasspy/piper-voices ; consulta la ficha del modelo antes de redistribuir sus archivos.

### 4. Arrancar con IA y voz neuronal

```powershell
.\.venv\Scripts\python.exe jarvis.py --ia --piper modelos\piper\es_MX-ald-medium.onnx
```

Después de completar la instalación también puedes hacer doble clic en **iniciar-jarvis.bat**. Su ventana queda abierta si hay un error. Sigue pulsando Enter antes de hablar. Prueba `hola, cómo estás`, `explícame qué es una galaxia` y `abre calculadora`. La primera respuesta puede tardar mientras Ollama carga el modelo. Piper carga su modelo por respuesta en esta primera integración, lo que añade una pequeña espera.

Para volver a las voces de Windows, omite `--piper`. Puedes elegir entre las instaladas:

```powershell
.\.venv\Scripts\python.exe jarvis.py --listar-voces
.\.venv\Scripts\python.exe jarvis.py --ia --voz 0 --velocidad 165
```

Las pruebas automatizadas comprueban el manejo de respuestas y fallos de Ollama mediante simulación; no verifican la calidad real del modelo o de la voz. La reproducción de audio, el micrófono, el rendimiento GPU y la instalación de Piper deben validarse en Windows.
