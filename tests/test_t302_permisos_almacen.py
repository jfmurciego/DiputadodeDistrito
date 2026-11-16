"""
PROYECTO: Diputado de Distrito
PRUEBA: permisos de P80 (T-302, T-369)
VERSIÓN: 1.1.0
FECHA: 2026-11-16
CAMBIO: T-369: el job `archivar_almacen_m06` (único con contents: write) se retiró con bateria-motor.yml; P80 queda solo en lectura.
ANTERIOR: 1.0.0 (T-302).
"""
import unittest
from pathlib import Path

import yaml

WF = Path(__file__).resolve().parents[1] / ".github/workflows/p80-verificacion-motor.yml"


class PermisosP80(unittest.TestCase):
    def test_ningun_job_escribe_y_no_esta_el_archivado_del_almacen(self):
        wf = yaml.safe_load(WF.read_text(encoding="utf-8"))
        self.assertEqual({"contents": "read"}, wf["permissions"])
        self.assertEqual(set(wf["jobs"]), {"bateria", "plan", "competicion", "aceptacion"})
        for nombre, job in wf["jobs"].items():
            self.assertNotIn("write", (job.get("permissions") or {}).values(), nombre)


if __name__ == "__main__":
    unittest.main()
