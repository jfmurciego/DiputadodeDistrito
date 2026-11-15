# VERSIÓN: 1.2.0
# CAMBIOS: 1.2.0: id no canónico (T-336) → ACQUIRE; canónico → REUSE. 1.1.0: años pedidos ≠ contrato, Last-Modified solo avisa (cabeceras reales de 65034.csv), 200 sin cabeceras, BadZipFile. 1.0.0: fichero nuevo (T-323, D-112).
# ANTERIOR: ninguna (fichero nuevo; 1.0.0 solo existió en esta PR)
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


def _paquete_falso(t, work, territory_id=None):
    d = Path(work) / "pkg"
    d.mkdir(parents=True)
    (d / "bundle.bin").write_bytes(b"no es un zip")  # el bundle no es un ZIP: paquete_territory_mismatch solo compara el manifiesto
    (d / "manifest.json").write_text(json.dumps({"path": "bundle.bin", "territory_id": territory_id or "aut02"}), encoding="utf-8")
    return d


class P10DesdeR2(unittest.TestCase):
    def _preparar(self, head, restaurar=_paquete_falso, anios=lambda t: ("2025", "2025", "2025"), pedido=("2025", "2025", "2025")):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = p.preparar("aut02", *pedido, td / ".ddd-source-package", restaurar=restaurar, head=head, indice=_indice(td), anios=anios)
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

    def test_last_modified_posterior_solo_avisa(self):
        rc, log, restaurado = self._preparar(lambda u: (200, {**HEAD_IGUAL, "last-modified": "Mon, 16 Nov 2026 08:00:00 GMT"}))
        self.assertEqual(rc, 0)
        self.assertTrue(restaurado)
        self.assertNotIn("::error::", log)

    def test_cabeceras_reales_65034_no_paran(self):
        # HEAD real al INE el 2026-11-14: 200, Last-Modified 2026-10-27 (posterior a la copia del 2026-02-16), sin Content-Length (chunked).
        real = {"content-type": "text/plain;charset=ISO-8859-15", "last-modified": "Tue, 27 Oct 2026 12:45:44 GMT", "transfer-encoding": "chunked"}
        rc, log, restaurado = self._preparar(lambda u: (200, HEAD_IGUAL if u.endswith(".zip") else real))
        self.assertEqual(rc, 0)
        self.assertTrue(restaurado)
        self.assertIn("::warning::P10_INE_SIN_COMPROBAR 65034.csv.zip", log)

    def test_200_sin_cabeceras_solo_avisa(self):
        rc, log, restaurado = self._preparar(lambda u: (200, {}))
        self.assertEqual(rc, 0)
        self.assertTrue(restaurado)
        self.assertIn("no devolvió Content-Length ni Last-Modified", log)

    def test_anios_pedidos_distintos_del_contrato_no_usan_r2(self):
        def no_restaurar(t, w):
            raise AssertionError("no debe restaurar un paquete de otro año")
        rc, log, restaurado = self._preparar(lambda u: (200, HEAD_IGUAL), restaurar=no_restaurar, pedido=("2025", "2026", "2026"))
        self.assertEqual(rc, 0)
        self.assertFalse(restaurado)
        self.assertIn("P10_R2_ANIOS_DISTINTOS", log)

    def test_id_no_canonico_no_se_reutiliza(self):
        # T-336: el paquete de R2 lleva un id distinto del canónico → ACQUIRE, sin consultar al INE.
        def no_hay_red(u):
            raise AssertionError("no se consulta al INE si el paquete no es reutilizable")
        rc, log, restaurado = self._preparar(no_hay_red, restaurar=lambda t, w: _paquete_falso(t, w, "aragon"))
        self.assertEqual(rc, 0)
        self.assertFalse(restaurado)
        self.assertIn("P10_R2_ID_NO_CANONICO", log)

    def test_id_canonico_sigue_en_reuse(self):
        rc, log, restaurado = self._preparar(lambda u: (200, HEAD_IGUAL), restaurar=lambda t, w: _paquete_falso(t, w, "aut02"))
        self.assertEqual(rc, 0)
        self.assertTrue(restaurado)
        self.assertNotIn("P10_R2_ID_NO_CANONICO", log)

    def test_zip_corrupto_sale_53(self):
        import zipfile

        def mal_zip(t, w):
            raise zipfile.BadZipFile("File is not a zip file")
        rc, log, _ = self._preparar(lambda u: (200, HEAD_IGUAL), restaurar=mal_zip)
        self.assertEqual(rc, p.SALIDA_CORRUPTO)

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
        previo = pasos[ids.index("r2") - 1]
        self.assertIn("requirements.lock", previo["run"])
        self.assertIn("steps.r2.outputs.desde_r2 != 'true'", pasos[ids.index("acquire")]["if"])


if __name__ == "__main__":
    unittest.main()
