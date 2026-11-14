# VERSIÓN: 1.0.0
# CAMBIOS: 1.0.0: fichero nuevo (T-323, D-112).
# ANTERIOR: ninguna (fichero nuevo)
"""T-323: P10 usa el paquete de R2 y solo consulta el INE (HEAD): sin cambios usa R2, cambiado para y avisa, sin red degrada con aviso."""
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import yaml

from herramientas import p10_desde_r2 as p

ROOT = Path(__file__).resolve().parents[1]
# Valores independientes de la huella oficial medida el 2026-11-14 (ver orchestracion/fuentes_r2.json).
BYTES_2025 = 60298555
HEAD_IGUAL = {"content-length": str(BYTES_2025), "last-modified": "Tue, 04 Nov 2025 10:00:00 GMT"}


def _indice(td: Path) -> Path:
    ruta = td / "indice.json"
    ruta.write_text(json.dumps({"fuentes": {
        "seccionado_2025.zip": {"origen_url": "https://www.ine.es/prodyser/cartografia/seccionado_2025.zip", "bytes": BYTES_2025, "descargado_en": "2026-11-14"},
        "65034.csv.zip": {"origen_url": "https://www.ine.es/jaxiT3/files/t/csv_bdsc/65034.csv", "bytes": 75489355, "descargado_en": "2026-02-16"},
    }}), encoding="utf-8")
    return ruta


def _paquete_falso(t, work):
    d = Path(work) / "pkg"
    d.mkdir(parents=True)
    (d / "manifest.json").write_text("{}", encoding="utf-8")
    return d


class P10DesdeR2(unittest.TestCase):
    def _preparar(self, head, restaurar=_paquete_falso):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = p.preparar("aut02", "2025", "2025", "2025", td / ".ddd-source-package", restaurar=restaurar, head=head, indice=_indice(td))
            return rc, out.getvalue() + err.getvalue(), (td / ".ddd-source-package" / "manifest.json").is_file()

    def test_ine_sin_cambios_usa_r2(self):
        rc, log, restaurado = self._preparar(lambda u: (200, HEAD_IGUAL))
        self.assertEqual(rc, 0)
        self.assertTrue(restaurado)
        self.assertNotIn("::error::", log)

    def test_ine_cambiado_por_tamano_para_y_avisa(self):
        rc, log, restaurado = self._preparar(lambda u: (200, {**HEAD_IGUAL, "content-length": "60298999"}))
        self.assertEqual(rc, p.SALIDA_CAMBIADA)
        self.assertFalse(restaurado)
        self.assertIn("::error::FUENTE_INE_CAMBIADA seccionado_2025.zip", log)

    def test_ine_cambiado_por_fecha_para_y_avisa(self):
        rc, log, _ = self._preparar(lambda u: (200, {**HEAD_IGUAL, "last-modified": "Mon, 16 Nov 2026 08:00:00 GMT"}))
        self.assertEqual(rc, p.SALIDA_CAMBIADA)
        self.assertIn("FUENTE_INE_CAMBIADA", log)

    def test_sin_red_o_503_o_403_degrada_con_aviso(self):
        def sin_red(u):
            raise OSError("red caída")
        for head in (sin_red, lambda u: (503, {}), lambda u: (403, {})):
            rc, log, restaurado = self._preparar(head)
            self.assertEqual(rc, 0)
            self.assertTrue(restaurado)
            self.assertIn("::warning::P10_INE_SIN_COMPROBAR", log)
            self.assertNotIn("::error::", log)

    def test_sin_paquete_en_r2_adquiere_como_antes(self):
        def no_hay_red(u):
            raise AssertionError("sin paquete no se consulta al INE")
        rc, log, restaurado = self._preparar(no_hay_red, restaurar=lambda t, w: None)
        self.assertEqual(rc, 0)
        self.assertFalse(restaurado)
        self.assertIn("P10_SIN_PAQUETE_R2", log)

    def test_paquete_corrupto_bloquea(self):
        from herramientas.bateria_motor import PaqueteP10Corrupto

        def corrupto(t, w):
            raise PaqueteP10Corrupto("sha256 distinto")
        rc, log, _ = self._preparar(lambda u: (200, HEAD_IGUAL), restaurar=corrupto)
        self.assertEqual(rc, p.SALIDA_CORRUPTO)
        self.assertIn("P10_PAQUETE_R2_CORRUPTO", log)

    def test_no_descarga_cuerpo_solo_head(self):
        visto = []
        self._preparar(lambda u: (visto.append(u) or (200, HEAD_IGUAL)))
        self.assertEqual(len(visto), 2)

    def test_indice_real_cubre_las_fuentes_ine(self):
        nombres, faltan = p.fuentes_necesarias("2025", "2025")
        self.assertEqual((nombres, faltan), (["seccionado_2025.zip", "65034.csv.zip"], []))

    def test_workflow_cableado(self):
        s = (ROOT / ".github/workflows/preparacion-fuentes.yml").read_text(encoding="utf-8")
        wf = yaml.safe_load(s)
        pasos = wf["jobs"]["territoriales"]["steps"]
        ids = [x.get("id") for x in pasos]
        self.assertLess(ids.index("previous"), ids.index("r2"))
        self.assertLess(ids.index("r2"), ids.index("acquire"))
        self.assertIn("p10_desde_r2.py preparar", pasos[ids.index("r2")]["run"])
        self.assertIn("steps.r2.outputs.desde_r2 != 'true'", pasos[ids.index("acquire")]["if"])


if __name__ == "__main__":
    unittest.main()
