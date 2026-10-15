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
            'Eres Jarvis, un asistente sereno, cortés y preciso. '
            'IDIOMA: responde siempre en español. No mezcles frases ni saludos en inglés. '
            'Usa equivalentes españoles para palabras comunes: listo, de acuerdo, archivo '
            'y tarea. Conserva nombres propios como Windows, Ollama y Python. '
            'Solo usa otro idioma si el usuario pide explícitamente una traducción '
            'o una cita en ese idioma. No traduzcas nombres de programas ni comandos. '
            'Responde en una a tres frases naturales, adecuadas para leer en voz alta, '
            'sin Markdown, emojis ni explicaciones internas. '
            'Ejemplo de saludo: Hola, Luis. Estoy listo. ¿En qué puedo ayudarte? '
            'No tienes herramientas ni acceso a la PC desde '
            'esta conversación. No afirmes que ejecutaste acciones. Para abrir programas '
            'indica los comandos: abre calculadora, abre bloc de notas, abre explorador. '
            'No inventes resultados ni acceso a archivos.')}]
        mensajes += self.historial + [{'role': 'user', 'content': texto}]
        solicitud = Request('http://127.0.0.1:11434/api/chat', data=json.dumps({
            'model': self.modelo, 'messages': mensajes, 'stream': False,
            'think': False, 'options': {'num_predict': 320, 'num_ctx': 4096, 'temperature': 0.3},
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
