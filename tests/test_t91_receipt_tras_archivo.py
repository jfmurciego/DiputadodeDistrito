import unittest
from pathlib import Path

WF = Path(".github/workflows/_reutilizable-incorporacion-electoral.yml")


class ReceiptTrasArchivo(unittest.TestCase):
    def test_registro_electoral_va_despues_del_archivo_en_origen(self):
        t = WF.read_text(encoding="utf-8")
        archivo = t.index("- name: Archivo en origen")
        registro = t.index("- name: Registrar disponibilidad del producto electoral")
        self.assertLess(archivo, registro, "el receipt no puede escribirse antes de que el archivo en origen pase")


if __name__ == "__main__":
    unittest.main()
