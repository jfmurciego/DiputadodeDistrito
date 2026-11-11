"""T-251: la descarga distingue cuota de egress (transitorio) de artefacto caducado (definitivo).

Respuestas de `gh run download` simuladas; sin red ni esperas reales.
"""
import subprocess
import unittest
from pathlib import Path

from herramientas import descargar_artefacto as d

EGRESS = "error downloading ddd-state-1-M06: HTTP 503: Egress is over the account limit. (https://api.github.com/...)"
EXPIRED = "no valid artifacts found to download"
GONE = "HTTP 410: Artifact has expired"


class Guion:
    def __init__(self, *respuestas):
        self.respuestas = list(respuestas)
        self.llamadas = []

    def __call__(self, cmd):
        self.llamadas.append(list(cmd))
        rc, err = self.respuestas.pop(0)
        return subprocess.CompletedProcess(cmd, rc, "", err)


class DescargarArtefacto(unittest.TestCase):
    def _run(self, guion, esperas=(30, 60, 120)):
        dormidas = []
        r = d.descargar("o/r", "123", "ddd-state-123-M06", "dst", runner=guion, dormir=dormidas.append, esperas=esperas)
        return r, dormidas

    def test_egress_transitorio_reintenta_y_luego_descarga(self):
        guion = Guion((1, EGRESS), (1, EGRESS), (0, ""))
        r, dormidas = self._run(guion)
        self.assertEqual((r.rc, r.clase, r.intentos), (0, "ok", 3))
        self.assertEqual(dormidas, [30, 60])
        self.assertEqual(guion.llamadas[0],
                         ["gh", "run", "download", "123", "--repo", "o/r", "--name", "ddd-state-123-M06", "--dir", "dst"])

    def test_egress_agotado_es_cuota_no_artefacto_perdido(self):
        guion = Guion(*[(1, EGRESS)] * 4)
        r, dormidas = self._run(guion)
        self.assertEqual((r.rc, r.clase, r.intentos), (75, "egress", 4))
        self.assertEqual(dormidas, [30, 60, 120])
        self.assertIn("ARTIFACT_EGRESS_QUOTA", r.mensaje)
        self.assertIn("Settings → Billing", r.mensaje)
        self.assertIn("NO un artefacto perdido", r.mensaje)
        self.assertNotIn("Remediación", r.mensaje)

    def test_caducado_es_definitivo_sin_reintento_y_con_remediacion(self):
        for err in (EXPIRED, GONE, "HTTP 404: Not Found"):
            with self.subTest(err=err):
                guion = Guion((1, err))
                r, dormidas = self._run(guion)
                self.assertEqual((r.rc, r.clase, r.intentos), (44, "missing", 1))
                self.assertEqual(dormidas, [])
                self.assertIn("ARTIFACT_MISSING", r.mensaje)
                self.assertIn("Generar desde fuente territorial acreditada", r.mensaje)

    def test_otro_fallo_no_se_reintenta(self):
        r, dormidas = self._run(Guion((1, "HTTP 401: Bad credentials")))
        self.assertEqual((r.rc, r.clase), (42, "other"))
        self.assertEqual(dormidas, [])

    def test_falsos_positivos_son_otro_fallo_sin_reintento(self):
        for err in ("HTTP 500: Internal Server Error", "HTTP 502: Bad Gateway",
                    "HTTP 503: Service Unavailable", "HTTP 403: Forbidden",
                    "gh: command not found", "error: token expired, run gh auth login"):
            with self.subTest(err=err):
                guion = Guion((1, err))
                r, dormidas = self._run(guion)
                self.assertEqual((r.rc, r.clase, r.intentos), (42, "other", 1))
                self.assertEqual(dormidas, [])

    def test_remediacion_por_tipo_de_artefacto(self):
        self.assertIn("preparacion-resultados-electorales.yml", d.remediacion("ddd-audit-electoral-9", "9"))
        self.assertIn("Reutilizar progreso existente", d.remediacion("ddd-state-9-M08", "9"))
        self.assertIn("run 9", d.remediacion("otro", "9"))

    def test_tope_por_defecto_razonable(self):
        self.assertLessEqual(sum(d.ESPERAS_S), 20 * 60)
        self.assertGreaterEqual(len(d.ESPERAS_S), 3)


class PuertaUsaLaDescargaClasificada(unittest.TestCase):
    def test_la_puerta_no_llama_a_gh_run_download_directamente(self):
        wf = (Path(__file__).resolve().parents[1] / ".github/workflows/_reutilizable-puerta-validacion.yml").read_text()
        self.assertNotIn("gh run download", wf)
        self.assertEqual(wf.count("herramientas.descargar_artefacto"), 2)
        self.assertIn("ARTIFACT_EGRESS_QUOTA", wf)


if __name__ == "__main__":
    unittest.main()
