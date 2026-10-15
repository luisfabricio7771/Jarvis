import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from acciones import validar_plan
from inteligencia import Conversacion
from jarvis import Jarvis


def plan(*acciones):
    return {'respuesta': '', 'acciones': list(acciones)}


class PlanesTest(unittest.TestCase):
    def test_rechaza_comandos_rutas_y_argumentos_extra(self):
        for acciones in [
            [{'tipo': 'terminal', 'comando': 'echo hola'}],
            [{'tipo': 'abrir_aplicacion', 'aplicacion': 'powershell.exe'}],
            [{'tipo': 'crear_nota', 'contenido': 'hola', 'ruta': '../externo'}],
            [{'tipo': 'abrir_nota_creada'}],
            [{'tipo': 'crear_nota', 'contenido': 'hola'}] * 5,
        ]:
            with self.subTest(acciones=acciones), self.assertRaises(ValueError):
                validar_plan(plan(*acciones))

    def test_plan_no_ejecuta_hasta_confirmacion_y_no_se_repite(self):
        with tempfile.TemporaryDirectory() as carpeta:
            c = Conversacion()
            j = Jarvis(carpeta, c, acciones=True)
            with patch.object(c, 'planificar', return_value=plan({'tipo': 'crear_nota', 'contenido': 'Comprar leche'})):
                self.assertIn('confirmar', j.ejecutar('Anota comprar leche')[0])
                self.assertEqual(list(Path(carpeta).iterdir()), [])
                self.assertIn('pendiente', j.ejecutar('otra cosa')[0])
                self.assertIn('verificada', j.ejecutar('confirmar')[0])
                self.assertEqual((Path(carpeta) / 'nota-1.txt').read_text(), 'Comprar leche\n')
                self.assertIn('No hay', j.ejecutar('confirmar')[0])
                self.assertEqual(len(list(Path(carpeta).iterdir())), 1)

    def test_cancelacion_y_plan_invalido_no_modifican_archivos(self):
        with tempfile.TemporaryDirectory() as carpeta:
            c = Conversacion()
            j = Jarvis(carpeta, c, acciones=True)
            with patch.object(c, 'planificar', return_value=plan({'tipo': 'crear_nota', 'contenido': 'hola'})):
                j.ejecutar('anota hola')
                self.assertIn('cancelado', j.ejecutar('cancelar')[0])
            with patch.object(c, 'responder', return_value='¿Qué necesitas?'), patch.object(c, 'planificar', return_value=plan(
                    {'tipo': 'crear_nota', 'contenido': 'hola'}, {'tipo': 'terminal'})):
                self.assertIn('No ejecuté acciones', j.ejecutar('haz algo')[0])
            self.assertEqual(list(Path(carpeta).iterdir()), [])

    def test_crear_y_abrir_nota_utiliza_la_ruta_real(self):
        with tempfile.TemporaryDirectory() as carpeta:
            c = Conversacion()
            j = Jarvis(carpeta, c, acciones=True)
            propuesto = plan({'tipo': 'crear_nota', 'contenido': 'Estudiar'}, {'tipo': 'abrir_nota_creada'})
            with patch.object(c, 'planificar', return_value=propuesto):
                j.ejecutar('Crea una nota y ábrela')
            with patch('jarvis.sys.platform', 'win32'), patch('jarvis.subprocess.Popen') as abrir:
                resultado = j.ejecutar('confirmar')[0]
            self.assertIn('Paso 2', resultado)
            abrir.assert_called_once_with(['notepad.exe', str(Path(carpeta).resolve() / 'nota-1.txt')], shell=False)

    def test_fallo_detiene_los_pasos_restantes(self):
        with tempfile.TemporaryDirectory() as carpeta:
            j = Jarvis(carpeta)
            propuesto = plan({'tipo': 'abrir_aplicacion', 'aplicacion': 'calculadora'},
                             {'tipo': 'crear_nota', 'contenido': 'No debe crearse'})
            with patch('jarvis.sys.platform', 'win32'), patch('jarvis.subprocess.Popen', side_effect=OSError('no disponible')):
                self.assertIn('Detuve', j.ejecutar_plan(propuesto))
            self.assertEqual(list(Path(carpeta).iterdir()), [])

    def test_api_json_y_memoria_sin_ejecutar_respuestas(self):
        c = Conversacion()
        respuesta = plan()
        respuesta['respuesta'] = 'Hola, Luis.'
        with patch.object(c.http, 'open', return_value=io.BytesIO(json.dumps({
                'message': {'content': json.dumps(respuesta)}}).encode())) as abrir:
            self.assertEqual(c.planificar('hola'), respuesta)
            cuerpo = json.loads(abrir.call_args.args[0].data)
            self.assertEqual(cuerpo['format']['type'], 'object')
            self.assertEqual(cuerpo['model'], 'qwen2.5:3b')
            self.assertEqual(c.historial[-1]['content'], 'Hola, Luis.')


class ContextoTest(unittest.TestCase):
    def test_crear_preguntar_ubicacion_y_abrir_en_otro_turno(self):
        with tempfile.TemporaryDirectory() as carpeta:
            c = Conversacion()
            j = Jarvis(carpeta, c, acciones=True)
            with patch.object(c, 'planificar', return_value=plan({'tipo': 'crear_nota', 'contenido': 'Comprar leche a las siete'})):
                j.ejecutar('Crea una nota que diga comprar leche a las siete')
            j.ejecutar('confirmar')
            nota = Path(carpeta).resolve() / 'nota-1.txt'
            self.assertIn(str(nota), j.ejecutar('donde la guardaste')[0])
            self.assertIn('confirmar', j.ejecutar('abre la')[0])
            with patch('jarvis.sys.platform', 'win32'), patch('jarvis.subprocess.Popen') as abrir:
                self.assertIn('enviada', j.ejecutar('confirmar')[0])
            abrir.assert_called_once_with(['notepad.exe', str(nota)], shell=False)
            self.assertEqual(j.ultima_nota, nota)
            self.assertEqual(c.contexto['ultima_nota'], str(nota))

    def test_no_hay_nota_pide_aclaracion_y_no_acepta_rutas_externas(self):
        with tempfile.TemporaryDirectory() as carpeta, tempfile.TemporaryDirectory() as fuera:
            j = Jarvis(carpeta)
            self.assertIn('¿Qué archivo', j.ejecutar('abrela')[0])
            externa = Path(fuera) / 'externa.txt'
            externa.write_text('fuera')
            j.ultima_nota = externa
            self.assertIn('¿Qué archivo', j.ejecutar('abre la nota')[0])
            self.assertIsNone(j.pendiente)

    def test_buscar_no_olvida_nota_y_archivo_eliminado_no_se_abre(self):
        with tempfile.TemporaryDirectory() as carpeta:
            j = Jarvis(carpeta)
            j.ejecutar('crea nota hola')
            nota = j.ultima_nota
            j.ejecutar_plan(plan({'tipo': 'buscar_archivos', 'consulta': 'nota'}))
            self.assertEqual(j.ultima_nota, nota)
            j.ejecutar('abrela')
            nota.unlink()
            with patch('jarvis.sys.platform', 'win32'), patch('jarvis.subprocess.Popen') as abrir:
                self.assertIn('falló', j.ejecutar('confirmar')[0])
                abrir.assert_not_called()

    def test_repara_una_respuesta_invalida_sin_guardar_acciones_falsas(self):
        c = Conversacion()
        valido = {'respuesta': '¿Cuáles son tus pendientes?', 'acciones': []}
        with patch.object(c.http, 'open', side_effect=[
            io.BytesIO(json.dumps({'message': {'content': '{"respuesta":"incompleta"}'}}).encode()),
            io.BytesIO(json.dumps({'message': {'content': json.dumps(valido)}}).encode()),
        ]) as abrir:
            self.assertEqual(c.planificar('Ayúdame a organizar mi día'), valido)
            self.assertEqual(abrir.call_count, 2)
        self.assertEqual(len(c.historial), 2)

    def test_fallo_formato_recurre_a_conversacion_sin_herramientas(self):
        with tempfile.TemporaryDirectory() as carpeta:
            c = Conversacion()
            j = Jarvis(carpeta, c, acciones=True)
            with patch.object(c, 'planificar', side_effect=ValueError('formato')), patch.object(
                    c, 'responder', return_value='¿Cuáles son tus pendientes y para cuándo?'):
                self.assertIn('¿Cuáles son tus pendientes', j.ejecutar('Ayúdame a organizar')[0])
            self.assertIsNone(j.pendiente)
            self.assertEqual(list(Path(carpeta).iterdir()), [])

    def test_contexto_y_historial_llegan_al_planificador(self):
        c = Conversacion()
        c.contexto = {'ultima_nota': 'C:/Users/Luis/Jarvis/nota-1.txt'}
        c.recordar('Anota comprar leche', 'Nota guardada y verificada: C:/Users/Luis/Jarvis/nota-1.txt')
        with patch.object(c.http, 'open', return_value=io.BytesIO(json.dumps({'message': {
                'content': json.dumps(plan({'tipo': 'abrir_ultima_nota'}))}}).encode())) as abrir:
            c.planificar('puedes abrir la nota en el bloc de notas')
            cuerpo = json.loads(abrir.call_args.args[0].data)
            self.assertIn('C:/Users/Luis/Jarvis/nota-1.txt', cuerpo['messages'][0]['content'])
            self.assertEqual(cuerpo['messages'][1]['content'], 'Anota comprar leche')

    def test_ollama_desconectado_da_error_de_conexion(self):
        from urllib.error import URLError
        with tempfile.TemporaryDirectory() as carpeta:
            c = Conversacion()
            j = Jarvis(carpeta, c, acciones=True)
            with patch.object(c, 'planificar', side_effect=URLError('offline')):
                self.assertIn('Comprueba que esté abierto', j.ejecutar('necesito ayuda')[0])
