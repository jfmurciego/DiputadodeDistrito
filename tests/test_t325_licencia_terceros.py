"""Versión 1.1.0 — T-557 (D-218): la cláusula de terceros vive ahora en AVISOS_LICENCIA.md (LICENSE es el texto oficial de PolyForm). 1.0.0 — T-325 (D-123, decisión del propietario 2026-11-15): LICENSE recoge el material de terceros de la galería.
Fecha: 2026-11-15. Estado: candidato. Anterior: ninguna (fichero nuevo).
El cambio de LICENSE se limita al texto literal acordado en el apartado 3 y a su cabecera; todo lo demás queda byte a byte igual.
"""
import hashlib
import re
import unittest
from pathlib import Path

R = Path(__file__).resolve().parents[1]
CLAUSULA = ("Material de terceros. Las fotografías de la galería territorial del visor (`visor/v2/galeria/`) no son obra del titular. "
            "Se rigen por su propia licencia Creative Commons (CC BY, CC BY-SA o CC0), indicada para cada una en "
            "`visor/v2/galeria/NOTICE.md`, y no por esta licencia.")
SHA_LICENSE_ANTERIOR = "47d51e56998e0085e7bc19eb5851acff63624ec9fe9083784cfd3e72e7c9e486"  # literal: LICENSE 1.0.0 de origin/main (15-11)
LEGACY = R / "legacy" / "licencias" / "LICENSE_pre_t325_20261115.txt"


def _plano(t):
    return re.sub(r"\s+", " ", t)


class LicenciaTerceros(unittest.TestCase):
    def setUp(self):
        self.t = (R / "AVISOS_LICENCIA.md").read_text(encoding="utf-8")

    def test_clausula_literal_una_sola_vez(self):
        self.assertEqual(_plano(self.t).count(CLAUSULA.replace("- ", "")), 1)

    @unittest.skipUnless(LEGACY.is_file(), "legacy/ no entra en la imagen de CI (.dockerignore)")
    def test_copia_anterior_intacta(self):
        self.assertEqual(hashlib.sha256(LEGACY.read_bytes()).hexdigest(), SHA_LICENSE_ANTERIOR)

    def test_notice_existe_y_se_rige_cada_foto_por_su_licencia(self):
        n = (R / "visor" / "v2" / "galeria" / "NOTICE.md").read_text(encoding="utf-8")
        self.assertIn("se rige por su propia licencia", _plano(n))


if __name__ == "__main__":
    unittest.main()
