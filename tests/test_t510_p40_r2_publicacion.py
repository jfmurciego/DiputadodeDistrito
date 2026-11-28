"""T-510 (P40 1.8.0, «solución B»): las subidas a R2 de la web salen del job de Pages a `subir_r2`, con `environment: publicacion`.

PROYECTO: Diputado de Distrito · VERSIÓN: 1.0.0 · FECHA: 2026-11-28 · ESTADO: candidato · ANTERIOR: ninguna (fichero nuevo)

(1) Todo paso de P40 que usa secrets/vars de los buckets de la web (R2_WEB_*, R2_SITIO_*) está en un job con `environment: publicacion`, y todo
    secreto R2 va en el env del PASO, nunca del job. (2) Pages no cambia: deshecho T-510 (`tests/_t510.py`), P40 es IGUAL a la 1.7.0 congelada
    (sha256 abajo); `subir_r2` no despliega, no registra y no reconstruye: recibe el artefacto `github-pages-<intento>` de `publicar`.
    (3) Un fallo de la subida no rompe nada: pasos con continue-on-error y un resumen que, ejecutado de verdad bajo `bash -eo pipefail`,
    sale 0 y dice R2_SUBIDA_FALLIDA en el log y en el resumen del run. Cada comprobación lleva su control negativo.
"""
import copy
import hashlib
import json
import os
import re
import subprocess
import tarfile
import tempfile
import unittest
from pathlib import Path

import yaml

from tests import _t510

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / ".github" / "workflows" / "p40-publicacion.yml"
FIX = ROOT / "tests" / "fixtures" / "t510" / "p40-publicacion_1.7.0.yml"
SHA_FIX = "99f8188dd0c41d790ca4eda60d41956774c6b21025abb562b66eca81085893eb"
WEB = re.compile(r"\b(?:secrets|vars)\.R2_(?:WEB|SITIO)_\w+")
R2_SECRETO = re.compile(r"\bsecrets\.R2_\w+")


def carga(texto):
    return yaml.safe_load(texto)


def pasos_web_fuera_de_publicacion(d):
    return sorted((j, s.get("name") or s.get("uses")) for j, job in d["jobs"].items() for s in job.get("steps", [])
                  if WEB.search(json.dumps(s)) and job.get("environment") != "publicacion")


def secretos_r2_fuera_del_paso(d):
    malos = []
    for j, job in d["jobs"].items():
        if R2_SECRETO.search(json.dumps({k: v for k, v in job.items() if k != "steps"})):
            malos.append((j, "job"))
        for s in job.get("steps", []):
            if R2_SECRETO.search(json.dumps({k: v for k, v in s.items() if k != "env"})):
                malos.append((j, s.get("name")))
    return malos


def paso(job, nombre):
    hay = [s for s in job["steps"] if s.get("name") == nombre]
    assert len(hay) == 1, nombre
    return hay[0]


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = carga(WF.read_text(encoding="utf-8"))
        cls.j = cls.d["jobs"]["subir_r2"]


class EntornoPublicacion(Base):
    def test_pasos_de_los_buckets_web_en_publicacion(self):
        self.assertEqual(pasos_web_fuera_de_publicacion(self.d), [])
        self.assertGreaterEqual(sum(bool(WEB.search(json.dumps(s))) for s in self.j["steps"]), 2)  # no es vacuo

    def test_control_negativo_paso_web_en_pages(self):
        d = copy.deepcopy(self.d)
        d["jobs"]["publicar"]["steps"].append(paso(d["jobs"]["subir_r2"], "Datos de la web en R2 (T-430)"))
        self.assertIn(("publicar", "Datos de la web en R2 (T-430)"), pasos_web_fuera_de_publicacion(d))
        d = copy.deepcopy(self.d)
        d["jobs"]["subir_r2"]["environment"] = "github-pages"
        self.assertTrue(pasos_web_fuera_de_publicacion(d))

    def test_secretos_r2_en_el_env_del_paso(self):
        self.assertEqual(secretos_r2_fuera_del_paso(self.d), [])
        self.assertTrue(R2_SECRETO.search(json.dumps(self.j["steps"])))  # no es vacuo

    def test_control_negativo_secreto_en_el_job(self):
        d = copy.deepcopy(self.d)
        d["jobs"]["subir_r2"]["env"]["AWS_ACCESS_KEY_ID"] = "${{ secrets.R2_WEB_ACCESS_KEY_ID }}"
        self.assertIn(("subir_r2", "job"), secretos_r2_fuera_del_paso(d))
        d = copy.deepcopy(self.d)
        paso(d["jobs"]["subir_r2"], "Web en R2 (T-430)")["run"] += "\necho ${{ secrets.R2_SITIO_ACCESS_KEY_ID }}"
        self.assertIn(("subir_r2", "Web en R2 (T-430)"), secretos_r2_fuera_del_paso(d))


class PagesIgual(Base):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        assert FIX.is_file(), "falta la copia congelada de P40 1.7.0"  # nunca se salta
        assert hashlib.sha256(FIX.read_bytes()).hexdigest() == SHA_FIX, "la copia congelada de P40 1.7.0 cambió"
        cls.antes = carga(FIX.read_text(encoding="utf-8"))

    def test_deshacer_t510_da_la_1_7_0(self):
        self.assertEqual(_t510.deshacer_p40(self.d), self.antes)

    def test_job_de_pages_intacto(self):
        a, b = self.antes["jobs"]["publicar"], self.d["jobs"]["publicar"]
        for k in ("environment", "concurrency", "needs", "if", "runs-on", "env"):
            self.assertEqual(a[k], b[k], k)
        self.assertEqual(b["concurrency"]["group"], "ddd-pages-prod")
        dep = lambda job: [s for s in job["steps"] if str(s.get("uses", "")).startswith(("actions/deploy-pages", "actions/upload-pages-artifact"))]
        self.assertEqual(dep(a), dep(b))

    def test_control_negativo_equivalencia(self):
        for mutar in (lambda d: d["jobs"]["publicar"]["concurrency"].__setitem__("group", "otro"),
                      lambda d: d["jobs"]["publicar"]["steps"].pop(),
                      lambda d: paso(d["jobs"]["subir_r2"], "Web en R2 (T-430)")["env"].__setitem__("R2_BUCKET", "x")):
            d = copy.deepcopy(self.d)
            mutar(d)
            self.assertNotEqual(_t510.deshacer_p40(d), self.antes)
        d = copy.deepcopy(self.d)
        del d["jobs"]["subir_r2"]
        with self.assertRaises(AssertionError):
            _t510.deshacer_p40(d)


class JobSubirR2(Base):
    def test_condicion_dependencias_y_concurrencia(self):
        self.assertEqual(self.j["environment"], "publicacion")
        self.assertEqual(self.j["needs"], ["preparar", "publicar"])
        self.assertEqual(self.j["if"], "${{ !cancelled() && github.ref == 'refs/heads/main' && needs.publicar.outputs.registro_persistido == 'success' }}")
        self.assertEqual(self.d["jobs"]["publicar"]["outputs"]["registro_persistido"], "${{ steps.persistir.outcome }}")
        self.assertEqual(paso(self.d["jobs"]["publicar"], "Persistir registro sólo después del despliegue")["id"], "persistir")
        self.assertEqual(self.j["concurrency"], {"group": "ddd-r2-web-prod", "cancel-in-progress": False, "queue": "max"})
        self.assertNotEqual(self.j["concurrency"]["group"], self.d["jobs"]["publicar"]["concurrency"]["group"])  # no entra en la cola de Pages
        self.assertEqual(self.j["permissions"], {"contents": "read", "actions": "read"})

    def test_recibe_el_artefacto_de_pages_y_no_reconstruye(self):
        recibir = paso(self.j, "Recibir el sitio desplegado en Pages (T-510)")
        self.assertTrue(recibir["uses"].startswith("actions/download-artifact@"))
        self.assertEqual(recibir["with"]["name"], "${{ needs.publicar.outputs.artefacto_pages }}")
        self.assertEqual(self.d["jobs"]["publicar"]["outputs"]["artefacto_pages"], "github-pages-${{ github.run_attempt }}")
        sube = [s for s in self.d["jobs"]["publicar"]["steps"] if str(s.get("uses", "")).startswith("actions/upload-pages-artifact")]
        self.assertEqual(sube[0]["with"]["name"], self.d["jobs"]["publicar"]["outputs"]["artefacto_pages"])  # el mismo nombre
        texto = yaml.safe_dump(self.j)
        for prohibido in ("deploy-pages", "upload-pages-artifact", "materializar_registro", "preparar_visor", "preparar_portada", "git push", "git commit"):
            self.assertNotIn(prohibido, texto)
        usa = [s.get("uses", "").split("@")[0] for s in self.j["steps"] if s.get("uses")]
        self.assertEqual(usa, ["actions/checkout", "actions/download-artifact"])

    def test_los_fallos_no_paran_el_job(self):
        for n in ("Recibir el sitio desplegado en Pages (T-510)", "Desempaquetar el sitio (T-510)", "Datos de la web en R2 (T-430)", "Web en R2 (T-430)"):
            self.assertIs(paso(self.j, n).get("continue-on-error"), True, n)
        self.assertEqual(paso(self.j, "Resumen de la subida a R2 (T-510)")["if"], "${{ always() }}")
        self.assertEqual([s.get("name") for s in self.j["steps"]][-1], "Resumen de la subida a R2 (T-510)")


class ScriptsDeVerdad(Base):
    def correr(self, run, env):
        with tempfile.TemporaryDirectory() as t:
            resumen = Path(t) / "resumen.md"
            r = subprocess.run(["bash", "-eo", "pipefail", "-c", run], capture_output=True, text=True,
                               env={**os.environ, **env, "GITHUB_STEP_SUMMARY": str(resumen), "RUNNER_TEMP": t})
            return r, (resumen.read_text(encoding="utf-8") if resumen.exists() else "")

    def resumen(self, **estado):
        base = {"RECIBIR": "success", "SITIO": "success", "DATOS": "success", "WEB": "success", "HAY_BUCKET_DATOS": "true", "HAY_BUCKET_SITIO": "true"}
        return self.correr(paso(self.j, "Resumen de la subida a R2 (T-510)")["run"], {**base, **estado})

    def test_resumen_fallo_lo_dice_y_sale_0(self):
        for estado in ({"DATOS": "failure", "WEB": "skipped"}, {"RECIBIR": "failure", "SITIO": "skipped", "DATOS": "skipped", "WEB": "skipped"},
                       {"WEB": "failure"}, {"SITIO": "", "DATOS": "", "WEB": ""}):
            r, md = self.resumen(**estado)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("::error::R2_SUBIDA_FALLIDA", r.stdout)
            self.assertIn("R2_SUBIDA_FALLIDA", md)
            self.assertIn("Pages está publicada y NO se ve afectada", md)

    def test_resumen_correcto_y_sin_bucket(self):
        r, md = self.resumen()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("R2_SUBIDA_FALLIDA", r.stdout + md)
        self.assertIn("Subida a R2 completa", md)
        r, md = self.resumen(HAY_BUCKET_DATOS="false")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("::warning::R2_SIN_BUCKET", r.stdout)
        self.assertIn("R2_SIN_BUCKET", md)

    def test_desempaquetar_el_tar_de_pages(self):
        run = paso(self.j, "Desempaquetar el sitio (T-510)")["run"]
        with tempfile.TemporaryDirectory() as t:
            sitio, dest = Path(t) / "origen", Path(t) / "sitio"
            (sitio / "datos").mkdir(parents=True)
            (sitio / "index.html").write_text("<html>", encoding="utf-8")
            (sitio / "datos" / "INDEX.json").write_text("{}", encoding="utf-8")
            (Path(t) / "pages").mkdir()
            with tarfile.open(Path(t) / "pages" / "artifact.tar", "w") as tar:  # como upload-pages-artifact: tar de «.» del sitio
                tar.add(sitio, arcname=".")
            local = run.replace("/tmp/site-candidate", str(dest))
            self.assertNotEqual(local, run)
            r = subprocess.run(["bash", "-eo", "pipefail", "-c", local], capture_output=True, text=True, env={**os.environ, "RUNNER_TEMP": t})
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual((dest / "datos" / "INDEX.json").read_text(encoding="utf-8"), "{}")
            (sitio / "index.html").unlink()  # control negativo: sin portada, falla
            with tarfile.open(Path(t) / "pages" / "artifact.tar", "w") as tar:
                tar.add(sitio, arcname=".")
            r = subprocess.run(["bash", "-eo", "pipefail", "-c", local], capture_output=True, text=True, env={**os.environ, "RUNNER_TEMP": t})
            self.assertNotEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
