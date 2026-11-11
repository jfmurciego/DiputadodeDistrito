"""T-251: la descarga distingue cuota de egress (transitorio) de artefacto caducado (definitivo).

Respuestas de `gh run download` simuladas; sin red ni esperas reales.
"""
import os
import stat
import subprocess
import tempfile
import textwrap
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


def _gate_run():
    import yaml
    wf = yaml.safe_load((Path(__file__).resolve().parents[1]
                         / ".github/workflows/_reutilizable-puerta-validacion.yml").read_text(encoding="utf-8"))
    return next(step["run"] for job in wf["jobs"].values() for step in job["steps"]
                if "herramientas.validar_puerta_ejecucion" in str(step.get("run", "")))


def _bloque(run, inicio, fin, incluir_fin=True):
    lineas = run.splitlines()
    i = next(n for n, l in enumerate(lineas) if inicio in l)
    j = next(n for n in range(i + 1, len(lineas)) if fin in lineas[n])
    return textwrap.dedent("\n".join(lineas[i:j + (1 if incluir_fin else 0)]))


class DescargarBajoErrexit(unittest.TestCase):
    """T-251b: el paso corre con `bash -eo pipefail` (shell: bash); la 1.3.0 moría con exit 1 en silencio."""

    @classmethod
    def setUpClass(cls):
        run = _gate_run()
        cls.funcion = _bloque(run, "descargar() {", "dl_msg=") + "\n}"
        cls.artefacto = _bloque(run, 'descargar "$ARTIFACT_NAME"', "esac")
        cls.auditoria = _bloque(run, 'descargar "$audit_name"', '[[ "$from_release" == true ]]') + "\nfi"

    def _ejecutar(self, cuerpo, rc, err=""):
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp) / "bin" / "python"
            fake.parent.mkdir()
            fake.write_text('#!/bin/sh\nprintf "%s" "$FAKE_ERR" >&2\nexit "$FAKE_RC"\n')
            fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
            script = "\n".join([
                'emit_blocked() { echo "BLOQUEADO $2 $1"; exit "$2"; }',
                "mkdir -p .ddd-gate", self.funcion,
                'ARTIFACT_NAME=ddd-state-1-M06; audit_name=ddd-audit-1; resolved_run_id=1; from_release=false',
                cuerpo, 'echo "SIGUE rc=$dl_rc"'])
            env = dict(os.environ, PATH=f"{fake.parent}:{os.environ['PATH']}", FAKE_RC=str(rc), FAKE_ERR=err,
                       GITHUB_REPOSITORY="o/r")
            return subprocess.run(["bash", "-eo", "pipefail", "-c", script], cwd=tmp, env=env,
                                  capture_output=True, text=True)

    def test_artefacto_por_codigo(self):
        casos = {0: (0, "SIGUE rc=0"),
                 75: (75, "BLOQUEADO 75 ARTIFACT_EGRESS_QUOTA: cuota"),
                 44: (44, "BLOQUEADO 44 ARTIFACT_MISSING: caducado"),
                 42: (42, "BLOQUEADO 42 No se pudo descargar ddd-state-1-M06: ARTIFACT_DOWNLOAD_FAILED: x")}
        msgs = {0: "", 75: "::error::ARTIFACT_EGRESS_QUOTA: cuota\n", 44: "::error::ARTIFACT_MISSING: caducado\n",
                42: "::warning::aviso\n::error::ARTIFACT_DOWNLOAD_FAILED: x\n"}
        for rc, (esperado_rc, esperado_out) in casos.items():
            with self.subTest(rc=rc):
                p = self._ejecutar(self.artefacto, rc, msgs[rc])
                self.assertEqual(p.returncode, esperado_rc, p.stdout + p.stderr)
                self.assertIn(esperado_out, p.stdout)

    def test_auditoria_por_codigo(self):
        p = self._ejecutar(self.auditoria, 0)
        self.assertEqual((p.returncode, p.stdout.strip()), (0, "SIGUE rc=0"), p.stderr)
        p = self._ejecutar(self.auditoria, 75, "::error::ARTIFACT_EGRESS_QUOTA: cuota\n")
        self.assertEqual(p.returncode, 75, p.stderr)
        self.assertIn("BLOQUEADO 75 ARTIFACT_EGRESS_QUOTA", p.stdout)
        p = self._ejecutar(self.auditoria, 44, "::error::ARTIFACT_MISSING: caducado\n")
        self.assertEqual(p.returncode, 43, p.stderr)
        self.assertIn("BLOQUEADO 43 Falta certificación ddd-audit-1", p.stdout)


if __name__ == "__main__":
    unittest.main()
