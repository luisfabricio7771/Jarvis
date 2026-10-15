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
            with patch.object(c, 'planificar', return_value=plan(
                    {'tipo': 'crear_nota', 'contenido': 'hola'}, {'tipo': 'terminal'})):
                self.assertIn('plan válido', j.ejecutar('haz algo')[0])
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
            self.assertEqual(cuerpo['format'], 'json')
            self.assertEqual(cuerpo['model'], 'qwen2.5:3b')
            self.assertEqual(c.historial[-1]['content'], 'Hola, Luis.')
