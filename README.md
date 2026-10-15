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

### Si la conversación mezcla idiomas

Actualiza `inteligencia.py` desde este repositorio y reinicia Jarvis para borrar el historial anterior. La configuración solicita respuestas breves en español y usa temperatura 0.3. Es una preferencia del modelo, no una garantía de idioma: si persiste, conserva el texto exacto de la respuesta para diagnosticarlo. Cambiar la voz de Piper no cambia las palabras generadas por Ollama.

## Peticiones naturales y planes con confirmación

El modelo predeterminado ahora es **qwen2.5:3b**, que respondió en español durante las pruebas del usuario. Activa las herramientas propuestas por IA con:

```powershell
.\.venv\Scripts\python.exe jarvis.py --ia --acciones --piper modelos\piper\es_ES-davefx-medium.onnx
```

Para probar con teclado usa `--texto --ia --acciones`. No se añaden dependencias. Copia también el nuevo archivo `acciones.py` al actualizar. El inicio por doble clic usa ahora este modelo, DaveFX y `--acciones`.

Ejemplos: «Necesito hacer unas cuentas», «Crea una nota que diga comprar leche y ábrela», «Busca archivos con informe en el nombre». Jarvis muestra y lee un plan de hasta cuatro acciones. Di **confirmar** o **cancelar** en el siguiente turno (pulsa Enter antes de hablar). El plan no se ejecuta hasta confirmarlo. Si una propuesta es ambigua, cancélala y reformula. Si falla un paso se detienen los siguientes; los cambios anteriores no se revierten automáticamente.

La IA solo puede proponer calculadora, bloc de notas, explorador, búsquedas por nombre, creación de notas y apertura de una nota creada en el plan o de la última nota de la sesión. El programa valida todas las acciones antes de ejecutar la primera; no acepta rutas, programas ni comandos arbitrarios del modelo. Las notas se guardan en la carpeta autorizada, por defecto `%USERPROFILE%\Jarvis`, y se comprueba su contenido. Abrir un programa informa que Windows recibió la solicitud; no demuestra que la ventana sea visible.

Los comandos exactos anteriores, como `crea nota hola` o `abre calculadora`, siguen ejecutándose directamente como antes. Para obtener un plan usa una petición natural. La memoria es temporal, limitada a seis intercambios, y los resultados confirmados se guardan como contexto. No hay todavía memoria persistente ni envío de mensajes, borrado o compras. Las pruebas del planificador usan respuestas simuladas; la precisión de las peticiones naturales debe comprobarse con el modelo real en Windows.


## Contexto de notas y recuperación de conversación

La última nota se conserva entre turnos mientras Jarvis está abierto. «Ábrela», «abre la nota» y «puedes abrir la nota en el bloc de notas» proponen abrir esa nota y requieren confirmación. «Dónde la guardaste» devuelve su ruta completa. No se adivinan rutas externas y se verifica que el archivo siga existiendo dentro de la carpeta autorizada al confirmar. Al reiniciar no se recupera automáticamente la nota de la sesión anterior.

Ollama recibe el historial y datos reales de la carpeta y la última nota. La salida usa un esquema JSON de herramientas, además de validación independiente en Python. Una respuesta mal formada se intenta reparar una vez. Si sigue fallando, Jarvis continúa en modo de conversación y avisa que no ejecutó acciones. Los problemas de conexión y modelo ausente se muestran por separado. Ayudar a organizar pendientes no requiere crear archivos: la IA tiene instrucciones de preguntar por tareas y fechas, usando lo que ya le has dicho.

Para comprobar primero la comprensión sin errores del micrófono:

```powershell
.\.venv\Scripts\python.exe jarvis.py --texto --ia --acciones
```

Prueba: «Ayúdame a organizar mi día; pregúntame mis pendientes», responde con tus tareas y horarios; después «Crea una nota que diga comprar leche», «confirmar», «dónde la guardaste», «ábrela», «confirmar». Para probar la voz omite `--texto` y añade `--piper modelos\piper\es_ES-davefx-medium.onnx`.

Las pruebas cubren los flujos anteriores con respuestas simuladas del modelo y apertura simulada de aplicaciones. No demuestran la calidad de razonamiento del modelo real ni la precisión de Vosk: si algo falla, compara primero el texto mostrado en `Tú:` con lo que dijiste. El modelo pequeño de 3B sigue teniendo limitaciones de comprensión; estas mejoras corrigen contexto y manejo de herramientas, no aumentan su tamaño.
