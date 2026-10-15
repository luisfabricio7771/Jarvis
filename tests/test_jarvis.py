import tempfile
import unittest
from pathlib import Path
from jarvis import Jarvis


class ComandosTest(unittest.TestCase):
    def test_notas_busqueda_y_no_sobrescritura(self):
        with tempfile.TemporaryDirectory() as carpeta:
            j = Jarvis(carpeta)
            j.ejecutar('crea nota Primera idea')
            j.ejecutar('Jarvis crea nota Segunda idea')
            self.assertEqual((Path(carpeta) / 'nota-1.txt').read_text(), 'Primera idea\n')
            self.assertEqual((Path(carpeta) / 'nota-2.txt').read_text(), 'Segunda idea\n')
            self.assertIn('nota-1.txt', j.ejecutar('busca archivo nota-1')[0])
            self.assertIn('No encontré', j.ejecutar('busca archivo inexistente')[0])

    def test_comandos_arbitrarios_no_se_ejecutan(self):
        with tempfile.TemporaryDirectory() as carpeta:
            j = Jarvis(carpeta)
            self.assertIn('No reconozco', j.ejecutar('borra todos mis archivos')[0])
            self.assertTrue(j.ejecutar('salir')[1])
            self.assertFalse(list(Path(carpeta).iterdir()))


if __name__ == '__main__':
    unittest.main()
