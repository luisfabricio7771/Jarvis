"""Asistente local para Windows. Ejecuta --texto para probar sin micrófono."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import unicodedata


def normalizar(texto):
    return ''.join(c for c in unicodedata.normalize('NFD', texto.lower()) if unicodedata.category(c) != 'Mn').strip()


class Jarvis:
    def __init__(self, carpeta):
        self.carpeta = Path(carpeta).expanduser().resolve()
        self.carpeta.mkdir(parents=True, exist_ok=True)

    def ejecutar(self, texto):
        orden = normalizar(texto)
        if orden.startswith('jarvis '):
            texto = texto[7:]
            orden = normalizar(texto)
        if orden in ('salir', 'terminar', 'adios'):
            return 'Hasta luego.', True
        if orden in ('ayuda', 'que puedes hacer'):
            return ('Di: abre calculadora, abre bloc de notas, busca archivo informe, '
                    'crea nota comprar leche, o salir. Solo busco dentro de la carpeta autorizada.'), False
        apps = {'abre calculadora': ['calc.exe'], 'abre bloc de notas': ['notepad.exe'],
                'abre explorador': ['explorer.exe', str(self.carpeta)]}
        if orden in apps:
            if sys.platform != 'win32':
                return 'Abrir aplicaciones requiere Windows.', False
            subprocess.Popen(apps[orden], shell=False)
            return 'Aplicación abierta.', False
        if orden.startswith('busca archivo '):
            consulta = orden[len('busca archivo '):].strip()
            if not consulta:
                return 'Indica un nombre de archivo.', False
            encontrados = []
            for raiz, dirs, archivos in os.walk(self.carpeta, followlinks=False):
                dirs[:] = [d for d in dirs if not (Path(raiz) / d).is_symlink()]
                for nombre in archivos:
                    ruta = Path(raiz) / nombre
                    if ruta.is_symlink():
                        continue
                    if consulta in normalizar(nombre):
                        encontrados.append(str(ruta.relative_to(self.carpeta)))
                        if len(encontrados) == 10:
                            break
                if len(encontrados) == 10:
                    break
            return ('Encontré: ' + '; '.join(encontrados) if encontrados else 'No encontré archivos con ese nombre.'), False
        if orden.startswith('crea nota '):
            contenido = texto[len('crea nota '):].strip()
            if not contenido:
                return 'Dime qué quieres anotar.', False
            # Exclusive creation prevents overwriting existing files or following symlinks.
            for numero in range(1, 10001):
                ruta = self.carpeta / f'nota-{numero}.txt'
                try:
                    with ruta.open('x', encoding='utf-8') as archivo:
                        archivo.write(contenido + '\n')
                    return f'Nota guardada: {ruta.name}.', False
                except FileExistsError:
                    continue
            return 'No hay un nombre de nota disponible.', False
        return 'No reconozco ese comando. Di ayuda para conocer las opciones.', False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--texto', action='store_true', help='Usar teclado sin dependencias de voz')
    parser.add_argument('--carpeta', default=str(Path.home() / 'Jarvis'), help='Carpeta autorizada para notas y búsquedas')
    parser.add_argument('--modelo', default='modelos/vosk-es', help='Directorio del modelo español Vosk descomprimido')
    args = parser.parse_args()
    asistente = Jarvis(args.carpeta)
    motor = None
    if not args.texto:
        try:
            import pyttsx3
            import sounddevice as sd
            from vosk import Model, KaldiRecognizer
            import queue
            motor = pyttsx3.init()
            for voz in motor.getProperty('voices'):
                if 'spanish' in voz.name.lower() or 'español' in voz.name.lower():
                    motor.setProperty('voice', voz.id)
                    break
            modelo = Model(args.modelo)
        except Exception as error:
            parser.exit(1, f'No se pudo iniciar la voz: {error}\nConsulta README.md o utiliza --texto.\n')

    def responder(mensaje):
        print('Jarvis:', mensaje)
        if motor:
            motor.say(mensaje)
            motor.runAndWait()

    responder('Jarvis listo. Di ayuda para empezar.')
    while True:
        try:
            if args.texto:
                texto = input('Tú: ')
            else:
                input('Pulsa Enter para hablar (Ctrl+C para salir)...')
                cola = queue.Queue(maxsize=32)

                def capturar(datos, frames, tiempo, estado):
                    try:
                        cola.put_nowait(bytes(datos))
                    except queue.Full:
                        pass

                reconocedor = KaldiRecognizer(modelo, 16000)
                print('Escuchando...')
                with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                                       channels=1, callback=capturar):
                    while True:
                        if reconocedor.AcceptWaveform(cola.get(timeout=15)):
                            texto = json.loads(reconocedor.Result()).get('text', '')
                            break
                print('Tú:', texto)
            respuesta, salir = asistente.ejecutar(texto)
            responder(respuesta)
            if salir:
                break
        except (KeyboardInterrupt, EOFError):
            print('\nHasta luego.')
            break
        except Exception as error:
            print(f'No se pudo completar la operación: {error}')


if __name__ == '__main__':
    main()
