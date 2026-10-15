import io
import json
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import URLError, HTTPError
from inteligencia import Conversacion
from jarvis import Jarvis


class ConversacionTest(unittest.TestCase):
    def test_sesion_y_peticion_local(self):
        c = Conversacion()
        with patch.object(c.http, 'open', side_effect=lambda *a, **k: io.BytesIO(
                json.dumps({'message': {'content': 'Hola, ¿cómo estás?'}}).encode())) as abrir:
            for _ in range(8):
                self.assertIn('Hola', c.responder('Hola'))
            solicitud = abrir.call_args.args[0]
            self.assertEqual(solicitud.full_url, 'http://127.0.0.1:11434/api/chat')
            cuerpo = json.loads(solicitud.data)
            self.assertFalse(cuerpo['stream'])
            self.assertFalse(cuerpo['think'])
            self.assertEqual(len(c.historial), 12)
            self.assertNotIn('tools', cuerpo)

    def test_servidor_ausente_y_modelo_ausente(self):
        c = Conversacion()
        with patch.object(c.http, 'open', side_effect=URLError('offline')):
            self.assertIn('Abre Ollama', c.responder('hola'))
        with patch.object(c.http, 'open', side_effect=HTTPError('', 404, '', {}, None)):
            self.assertIn('ollama pull qwen3:4b', c.responder('hola'))
        self.assertEqual(c.historial, [])

    def test_comandos_no_pasan_al_modelo_y_se_puede_olvidar(self):
        c = Conversacion()
        with tempfile.TemporaryDirectory() as carpeta:
            j = Jarvis(carpeta, c)
            with patch.object(c, 'responder', return_value='Hola') as responder:
                j.ejecutar('crea nota mi idea')
                responder.assert_not_called()
                self.assertEqual(j.ejecutar('como estas'), ('Hola', False))
                c.historial.append({'role': 'user', 'content': 'hola'})
                j.ejecutar('olvida la conversación')
                self.assertEqual(c.historial, [])


if __name__ == '__main__':
    unittest.main()
