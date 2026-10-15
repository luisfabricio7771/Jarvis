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
    def __init__(self, carpeta, conversacion=None, acciones=False):
        self.acciones = acciones
        self.pendiente = None
        self.peticion_pendiente = ''
        self.ultima_nota = None
        self.conversacion = conversacion
        self.carpeta = Path(carpeta).expanduser().resolve()
        self.carpeta.mkdir(parents=True, exist_ok=True)

    def ejecutar(self, texto):
        orden = normalizar(texto)
        if orden.startswith('jarvis '):
            texto = texto[7:]
            orden = normalizar(texto)
        if self.pendiente is not None:
            if orden in ('cancelar', 'salir', 'terminar', 'adios'):
                self.pendiente = None
                if orden == 'cancelar':
                    return 'Plan cancelado. No ejecuté ninguna acción.', False
            elif orden == 'confirmar':
                plan, self.pendiente = self.pendiente, None
                resultado = self.ejecutar_plan(plan)
                self.conversacion.recordar(self.peticion_pendiente, resultado)
                return resultado, False
            else:
                return 'Hay un plan pendiente. Di confirmar o cancelar antes de continuar.', False
        if orden in ('confirmar', 'cancelar'):
            return 'No hay ningún plan pendiente.', False
        if orden == 'olvida la conversacion':
            if self.conversacion:
                self.conversacion.historial.clear()
            return 'He olvidado esta conversación.', False
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
            return 'Solicitud de apertura enviada a Windows.', False
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
                    if ruta.read_text(encoding='utf-8') != contenido + '\n':
                        raise OSError('No se pudo verificar la nota guardada')
                    self.ultima_nota = ruta
                    return f'Nota guardada y verificada: {ruta.name}.', False
                except FileExistsError:
                    continue
            return 'No hay un nombre de nota disponible.', False
        if self.conversacion:
            if self.acciones:
                from acciones import validar_plan, describir
                try:
                    plan = validar_plan(self.conversacion.planificar(texto))
                except Exception:
                    return ('No pude obtener un plan válido de la IA local. No ejecuté acciones. '
                            'Comprueba Ollama o reformula la petición.'), False
                if not plan['acciones']:
                    return plan['respuesta'] or '¿Qué necesitas hacer?', False
                self.pendiente = plan
                self.peticion_pendiente = texto
                pasos = '; '.join(f'{n}. {describir(a)}' for n, a in enumerate(plan['acciones'], 1))
                return f'Propongo: {pasos}. Di confirmar para ejecutar o cancelar.', False
            return self.conversacion.responder(texto), False
        return 'No reconozco ese comando. Di ayuda para conocer las opciones.', False


    def ejecutar_plan(self, plan):
        from acciones import validar_plan
        validar_plan(plan)
        resultados = []
        self.ultima_nota = None
        for numero, accion in enumerate(plan['acciones'], 1):
            try:
                tipo = accion['tipo']
                if tipo == 'abrir_nota_creada':
                    if sys.platform != 'win32':
                        raise OSError('Abrir notas requiere Windows')
                    ruta = self.ultima_nota
                    if ruta is None or ruta.is_symlink() or ruta.resolve().parent != self.carpeta or not ruta.is_file():
                        raise OSError('La nota creada ya no está disponible')
                    subprocess.Popen(['notepad.exe', str(ruta)], shell=False)
                    resultado = 'Solicitud de apertura de la nota enviada a Windows.'
                else:
                    comando = {'abrir_aplicacion': lambda: 'abre ' + accion['aplicacion'],
                               'crear_nota': lambda: 'crea nota ' + accion['contenido'],
                               'buscar_archivos': lambda: 'busca archivo ' + accion['consulta']}[tipo]()
                    if tipo == 'abrir_aplicacion' and sys.platform != 'win32':
                        raise OSError('Abrir aplicaciones requiere Windows')
                    if tipo == 'crear_nota':
                        self.ultima_nota = None
                    resultado, _ = self.ejecutar(comando)
                    if tipo == 'crear_nota' and self.ultima_nota is None:
                        raise OSError('No se pudo crear la nota')
                resultados.append(f'Paso {numero}: {resultado}')
            except Exception as error:
                resultados.append(f'Paso {numero} falló: {error}. Detuve los pasos restantes. '
                                  'Los pasos anteriores no se deshacen automáticamente.')
                break
        return ' '.join(resultados) or 'No hay acciones que ejecutar.'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--texto', action='store_true', help='Usar teclado sin dependencias de voz')
    parser.add_argument('--carpeta', default=str(Path.home() / 'Jarvis'), help='Carpeta autorizada para notas y búsquedas')
    parser.add_argument('--modelo', default='modelos/vosk-es', help='Directorio del modelo español Vosk descomprimido')
    parser.add_argument('--ia', action='store_true', help='Conversar con Ollama en esta PC')
    parser.add_argument('--modelo-ia', default='qwen2.5:3b', help='Modelo instalado en Ollama')
    parser.add_argument('--piper', help='Ruta al modelo de voz Piper .onnx (opcional)')
    parser.add_argument('--voz', type=int, help='Número de voz Windows')
    parser.add_argument('--listar-voces', action='store_true', help='Mostrar voces Windows y salir')
    parser.add_argument('--velocidad', type=int, default=165, help='Velocidad de la voz Windows')
    parser.add_argument('--acciones', action='store_true', help='Proponer planes con herramientas y confirmación (requiere --ia)')
    args = parser.parse_args()
    if args.acciones and not args.ia:
        parser.error('--acciones requiere --ia')
    if args.listar_voces:
        import pyttsx3
        motor = pyttsx3.init()
        for numero, voz in enumerate(motor.getProperty('voices')):
            print(f'{numero}: {voz.name}')
        motor.stop()
        return
    conversacion = None
    if args.ia:
        from inteligencia import Conversacion
        conversacion = Conversacion(args.modelo_ia)
    asistente = Jarvis(args.carpeta, conversacion, args.acciones)
    motor = None
    if not args.texto:
        try:
            from voz import Voz
            import sounddevice as sd
            from vosk import Model, KaldiRecognizer
            import queue
            motor = Voz(args.piper, args.voz, args.velocidad)
            modelo = Model(args.modelo)
        except Exception as error:
            parser.exit(1, f'No se pudo iniciar la voz: {error}\nConsulta README.md o utiliza --texto.\n')

    def responder(mensaje):
        print('Jarvis:', mensaje)
        if motor:
            try:
                motor.decir(mensaje)
            except Exception as error:
                print(f'No pude reproducir la voz: {error}. La respuesta aparece arriba.')

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
