"""Versión 1.0.0 — T-557 (D-218, decisión del propietario): LICENSE es el texto oficial de PolyForm Strict 1.0.0.
Fecha: 2026-11-28. Estado: candidato. Anterior: ninguna (fichero nuevo).
Valor esperado literal (no recalculado): sha256 y tamaño del fichero PolyForm-Strict-1.0.0.md de la etiqueta 1.0.0 de
github.com/polyformproject/polyform-licenses, descargado de raw.githubusercontent.com (blob git 90abd0e6c64a135f42451762337a397bf27f4862).
"""
import hashlib
import re
import unittest
from pathlib import Path

R = Path(__file__).resolve().parents[1]
SHA_OFICIAL = "9eb48619fbc193ab7bb327b090cfcc703000265b83e670f81f231d0b1c43c56e"
BYTES_OFICIAL = 3593
MENCION = "PolyForm Strict 1.0.0"


class LicenciaPolyform(unittest.TestCase):
    def test_license_coincide_byte_a_byte_con_el_oficial(self):
        b = (R / "LICENSE").read_bytes()
        self.assertEqual(len(b), BYTES_OFICIAL)
        self.assertEqual(hashlib.sha256(b).hexdigest(), SHA_OFICIAL)
        self.assertTrue(b.startswith(b"# PolyForm Strict License 1.0.0\n"))

    def test_mencionan_la_licencia(self):
        for rel in ("README.md", "CONTRIBUTING.md", "AVISOS_LICENCIA.md", "paquetes/deslinde/README.md",
                    "documentacion_publica/docs/metodo.md"):
            self.assertIn(MENCION, (R / rel).read_text(encoding="utf-8"), rel)
        cff = (R / "CITATION.cff").read_text(encoding="utf-8")
        self.assertRegex(cff, r"(?m)^license: PolyForm-Strict-1\.0\.0$")
        py = (R / "paquetes/deslinde/pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('license = {text = "PolyForm-Strict-1.0.0"}', py)

    def test_ningun_fichero_declara_otra_licencia_para_el_codigo(self):
        prohibidos = re.compile(r"licencia propietaria|sin licencia de uso|\*\*Código\*\*: Apache|license:\s*Apache|"
                                r"Recomendaci[óo]n:\s*\*\*Apache")
        for rel in ("README.md", "CONTRIBUTING.md", "CITATION.cff", "AVISOS_LICENCIA.md", "paquetes/deslinde/README.md",
                    "paquetes/deslinde/pyproject.toml", "documentacion_publica/docs/metodo.md"):
            self.assertIsNone(prohibidos.search((R / rel).read_text(encoding="utf-8")), rel)


if __name__ == "__main__":
    unittest.main()
