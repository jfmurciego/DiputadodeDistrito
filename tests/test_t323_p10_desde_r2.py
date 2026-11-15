# VERSIÓN: 1.3.0
# CAMBIOS: 1.3.0: padrón 65034 descargado y comparado por sha256 (D-112). 1.2.0: id no canónico (T-336) → ACQUIRE; canónico → REUSE. 1.1.0: años pedidos ≠ contrato, Last-Modified solo avisa (cabeceras reales de 65034.csv), 200 sin cabeceras, BadZipFile. 1.0.0: fichero nuevo (T-323, D-112).
# ANTERIOR: ninguna (fichero nuevo; 1.0.0 solo existió en esta PR)
"""T-323: P10 usa el paquete de R2 y solo consulta el INE (HEAD): sin cambios usa R2, cambiado para y avisa, sin red degrada con aviso."""
import hashlib
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
# Contenido sintético del padrón: ';' en el INE, tabulador en la copia; el sha256 esperado es el de la versión tabulada, calculado aparte.
PADRON_VIVO = [b"Total Nacional;Provincias;Total\r\n", b"Total Nacional;;49.128.297\r\n"]
PADRON_SHA = hashlib.sha256(b"Total Nacional\tProvincias\tTotal\r\nTotal Nacional\t\t49.128.297\r\n").hexdigest()
HEAD_IGUAL = {"content-length": str(BYTES_2025), "last-modified": "Tue, 04 Nov 2025 10:00:00 GMT"}


def _indice(td: Path) -> Path:
    ruta = td / "indice.json"
    ruta.write_text(json.dumps({"fuentes": {
        "seccionado_2025.zip": {"origen_url": "https://www.ine.es/prodyser/cartografia/seccionado_2025.zip", "bytes": BYTES_2025, "descargado_en": "2026-11-14"},
        "65034.csv.zip": {"origen_url": "https://www.ine.es/jaxiT3/files/t/csv_bdsc/65034.csv", "bytes": 75489355, "descargado_en": "2026-02-16", "contenido_sha256": PADRON_SHA},
    }}), encoding="utf-8")
    return ruta


def _paquete_falso(t, work, territory_id=None):
    d = Path(work) / "pkg"
    d.mkdir(parents=True)
    (d / "bundle.bin").write_bytes(b"no es un zip")  # el bundle no es un ZIP: paquete_territory_mismatch solo compara el manifiesto
    (d / "manifest.json").write_text(json.dumps({"path": "bundle.bin", "territory_id": territory_id or "aut02"}), encoding="utf-8")
    return d


class P10DesdeR2(unittest.TestCase):
    def _preparar(self, head, restaurar=_paquete_falso, anios=lambda t: ("2025", "2025", "2025"), pedido=("2025", "2025", "2025"), descargar=lambda u: iter(PADRON_VIVO)):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = p.preparar("aut02", *pedido, td / ".ddd-source-package", restaurar=restaurar, head=head, indice=_indice(td), anios=anios, descargar=descargar)
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

    def test_padron_igual_sigue_y_se_descarga_entero(self):
        pedidos = []
        rc, log, restaurado = self._preparar(lambda u: (200, HEAD_IGUAL), descargar=lambda u: (pedidos.append(u) or iter(PADRON_VIVO)))
        self.assertEqual(rc, 0)
        self.assertTrue(restaurado)
        self.assertEqual(pedidos, ["https://www.ine.es/jaxiT3/files/t/csv_bdsc/65034.csv"])

    def test_padron_con_sha_distinto_para(self):
        rc, log, restaurado = self._preparar(lambda u: (200, HEAD_IGUAL), descargar=lambda u: iter([PADRON_VIVO[0], b"Total Nacional;;49.128.298\r\n"]))
        self.assertEqual(rc, p.SALIDA_CAMBIADA)
        self.assertFalse(restaurado)
        self.assertIn("::error::FUENTE_INE_CAMBIADA 65034.csv.zip", log)

    def test_padron_sin_red_degrada_con_aviso(self):
        def sin_red(u):
            raise OSError("red caída")
            yield b""
        rc, log, restaurado = self._preparar(lambda u: (200, HEAD_IGUAL), descargar=sin_red)
        self.assertEqual(rc, 0)
        self.assertTrue(restaurado)
        self.assertIn("::warning::P10_INE_SIN_COMPROBAR 65034.csv.zip: no se pudo descargar", log)

    def test_padron_cortado_a_medias_degrada_con_aviso(self):
        def corta(u):
            yield PADRON_VIVO[0]
            raise ConnectionResetError("reset")
        rc, log, _ = self._preparar(lambda u: (200, HEAD_IGUAL), descargar=corta)
        self.assertEqual(rc, 0)
        self.assertIn("no se pudo descargar", log)

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

    def test_el_seccionado_solo_va_por_head(self):
        visto = []
        self._preparar(lambda u: (visto.append(u) or (200, HEAD_IGUAL)))
        self.assertEqual(visto, ["https://www.ine.es/prodyser/cartografia/seccionado_2025.zip"])

    def test_indice_real_cubre_las_fuentes_ine(self):
        nombres, faltan = p.fuentes_necesarias("2025", "2025")
        self.assertEqual((nombres, faltan), (["seccionado_2025.zip", "65034.csv.zip"], []))
        real = json.loads((ROOT / "orchestracion/fuentes_r2.json").read_text(encoding="utf-8"))["fuentes"]
        # Valor independiente: sha256 del miembro 65034.csv de la copia (zip 91d3ff9a…), medido el 2026-11-15.
        self.assertEqual(real["65034.csv.zip"]["contenido_sha256"], "1938833dea5c4ac1e722e0038c1ed2295c1efa446b930a560e4afd6eb8c18c2a")

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
