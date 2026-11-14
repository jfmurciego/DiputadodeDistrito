"""
PROYECTO: Diputado de Distrito
PRUEBA: permisos del job de archivado del almacén M06 (T-302)
VERSIÓN: 1.0.0
FECHA: 2026-11-14
CAMBIO: solo `archivar_almacen_m06` tiene contents: write (ve los borradores almacen-m06-*); los demás jobs y el workflow, read.
ANTERIOR: ninguna (fichero nuevo).
"""
import unittest
from pathlib import Path

import yaml

WF = Path(__file__).resolve().parents[1] / ".github/workflows/bateria-motor.yml"


class PermisosAlmacenM06(unittest.TestCase):
    def setUp(self):
        self.wf = yaml.safe_load(WF.read_text(encoding="utf-8"))

    def test_solo_el_job_de_archivado_escribe(self):
        self.assertEqual({"contents": "read"}, self.wf["permissions"])
        for nombre, job in self.wf["jobs"].items():
            permisos = job.get("permissions") or {}
            if nombre == "archivar_almacen_m06":
                self.assertEqual({"contents": "write"}, permisos)
            else:
                self.assertNotIn("write", permisos.values(), nombre)

    def test_el_job_no_escribe_en_github(self):
        pasos = self.wf["jobs"]["archivar_almacen_m06"]["steps"]
        texto = "\n".join(str(p.get("run", "")) for p in pasos)
        for prohibido in ("git push", "git commit", "release edit", "release delete", "release create", "-X DELETE", "-X POST", "-X PATCH"):
            self.assertNotIn(prohibido, texto)


if __name__ == "__main__":
    unittest.main()
