"""Conversación local mediante la API de Ollama, sin herramientas ejecutables."""
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener, ProxyHandler


class Conversacion:
    def __init__(self, modelo='qwen3:4b'):
        self.modelo = modelo
        self.historial = []
        # El servicio está en la PC: no enviar conversaciones a un proxy del sistema.
        self.http = build_opener(ProxyHandler({}))

    def responder(self, texto):
        if not texto.strip():
            return 'No te escuché. Vuelve a intentarlo.'
        mensajes = [{'role': 'system', 'content': (
            'Eres Jarvis, un asistente amable. Habla en español con respuestas breves '
            'y naturales, sin Markdown. No tienes herramientas ni acceso a la PC desde '
            'esta conversación. No afirmes que ejecutaste acciones. Para abrir programas '
            'indica los comandos: abre calculadora, abre bloc de notas, abre explorador. '
            'No inventes resultados ni acceso a archivos.')}]
        mensajes += self.historial + [{'role': 'user', 'content': texto}]
        solicitud = Request('http://127.0.0.1:11434/api/chat', data=json.dumps({
            'model': self.modelo, 'messages': mensajes, 'stream': False,
            'think': False, 'options': {'num_predict': 200, 'num_ctx': 4096},
        }).encode(), headers={'Content-Type': 'application/json'})
        try:
            with self.http.open(solicitud, timeout=180) as respuesta:
                datos = json.load(respuesta)
            contenido = datos['message']['content'].strip()
            if not contenido:
                raise ValueError('respuesta vacía')
        except HTTPError as error:
            if error.code == 404:
                return f'Falta el modelo local. Ejecuta en otra ventana: ollama pull {self.modelo}'
            return f'Ollama devolvió un error ({error.code}). Revisa su ventana e inténtalo de nuevo.'
        except (URLError, TimeoutError, OSError):
            return 'No pude conectar con la IA local. Abre Ollama y comprueba que el modelo esté instalado.'
        except (ValueError, KeyError, TypeError):
            return 'La IA local devolvió una respuesta inválida. Inténtalo de nuevo.'
        self.historial = (self.historial + [
            {'role': 'user', 'content': texto}, {'role': 'assistant', 'content': contenido}
        ])[-12:]
        return contenido
