"""Voces de Windows o síntesis neuronal local con Piper."""
from pathlib import Path
import subprocess
import sys
import tempfile


class Voz:
    def __init__(self, modelo_piper=None, indice=None, velocidad=165):
        self.modelo = Path(modelo_piper).resolve() if modelo_piper else None
        self.motor = None
        if self.modelo:
            if sys.platform != 'win32':
                raise ValueError('La reproducción Piper integrada requiere Windows.')
            if not self.modelo.is_file() or not Path(str(self.modelo) + '.json').is_file():
                raise ValueError('Faltan el modelo Piper .onnx o su archivo .onnx.json. Consulta README.md.')
        else:
            import pyttsx3
            self.motor = pyttsx3.init()
            voces = self.motor.getProperty('voices')
            if indice is not None:
                if not 0 <= indice < len(voces):
                    raise ValueError('Índice de voz inválido. Usa --listar-voces.')
                self.motor.setProperty('voice', voces[indice].id)
            else:
                for voz in voces:
                    if any(t in voz.name.lower() for t in ('spanish', 'español', 'mexico', 'mexican')):
                        self.motor.setProperty('voice', voz.id)
                        break
            self.motor.setProperty('rate', velocidad)

    def decir(self, mensaje):
        if self.motor:
            self.motor.say(mensaje)
            self.motor.runAndWait()
            return
        import winsound
        with tempfile.TemporaryDirectory(prefix='jarvis-voz-') as carpeta:
            audio = str(Path(carpeta) / 'respuesta.wav')
            subprocess.run([sys.executable, '-m', 'piper', '--model', str(self.modelo),
                            '--output_file', audio], input=mensaje, text=True,
                           encoding='utf-8', check=True, timeout=120, capture_output=True)
            winsound.PlaySound(audio, winsound.SND_FILENAME)
