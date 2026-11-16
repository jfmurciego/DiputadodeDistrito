# -*- coding: utf-8 -*-
"""T-370 (D-133, paso 4): P50 Publicación académica sustituye a `publicar-version-mapa.yml` sin cambiar paquete, SHA256SUMS, atestación ni entorno.

PROYECTO: Diputado de Distrito · VERSIÓN: 1.0.0 · FECHA: 2026-11-16 · ESTADO: candidato · ANTERIOR: ninguna (fichero nuevo)
La equivalencia se calcula contra una COPIA CONGELADA (`tests/fixtures/t370_workflows/`, con sha256; en CI no hay `legacy/`). Si falta o cambia su
huella el test FALLA (no se salta). Controles negativos: un permiso, entorno, acción, comando o `needs` cambiados se detectan.
"""
import copy
import hashlib
import json
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

from tests._uses_sin_version import cargar as cargar_sin_version

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / ".github" / "workflows"
FIX = ROOT / "tests" / "fixtures" / "t370_workflows" / "publicar-version-mapa_1.1.2.yml"
SHA = "722943e760bc4fe83b41893c79712a75d198b79fe133e501751b88e01dab750b"
TAR = "tar --sort=name --mtime='1980-01-01 00:00Z' --owner=0 --group=0 --numeric-owner"
FIND = "find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS"


def on(d):
    return d.get("on") or d.get(True)


def paso(job, nombre):
    return next(s for s in job["steps"] if s.get("name") == nombre)


def usos(job):
    return [s["uses"] for s in job["steps"] if "uses" in s]


def diferencias(viejo, nuevo):
    """Diferencias NO permitidas en el job de publicación (vacía = equivalente)."""
    a, b = viejo["jobs"]["publicar"], nuevo["jobs"]["publicar"]
    d = []
    if a.get("environment") != b.get("environment"):
        d.append("entorno")
    if a.get("permissions") != b.get("permissions"):
        d.append("permisos")
    if a.get("runs-on") != b.get("runs-on"):
        d.append("runs-on")
    if not set(a["permissions"]) <= set(b.get("permissions", {})):
        d.append("permiso perdido")
    cb = paso(b, "Empaquetar de forma determinista")["run"]
    if TAR not in cb or "-czf" not in cb or "-C" not in cb:
        d.append("empaquetado")
    if FIND not in paso(b, "Manifiesto SHA-256")["run"]:
        d.append("manifiesto")
    att = [s for s in b["steps"] if str(s.get("uses", "")).startswith("actions/attest-build-provenance")]
    ate = [s for s in a["steps"] if str(s.get("uses", "")).startswith("actions/attest-build-provenance")]
    if len(att) != 1 or att[0]["uses"] != ate[0]["uses"]:
        d.append("atestación")
    for u in usos(a):
        if u.split("@")[0] in ("actions/checkout", "actions/download-artifact") and u not in usos(b):
            d.append(f"acción {u}")
    return d


class Congelado(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assert FIX.is_file(), f"falta la copia congelada {FIX}"  # nunca se salta
        datos = FIX.read_bytes()
        assert hashlib.sha256(datos).hexdigest() == SHA, "la copia congelada cambió"
        cls.v = cargar_sin_version(datos.decode("utf-8"))
        cls.p = cargar_sin_version((WF / "p50-publicacion-academica.yml").read_text(encoding="utf-8"))


class Disparadores(Congelado):
    def test_fichero_viejo_borrado_y_boton_unico(self):
        self.assertFalse((WF / "publicar-version-mapa.yml").exists())
        self.assertEqual(self.p["name"], "P50 Publicación académica")
        self.assertEqual(set(on(self.p)), {"workflow_dispatch"})  # sin workflow_call: la 05 ya no lo lanza
        entradas = on(self.p)["workflow_dispatch"]["inputs"]
        self.assertEqual(set(entradas), {"territorios", "destino", "concepto_nuevo"})  # T-388: destino añadido
        self.assertEqual(entradas["territorios"]["type"], "string")
        self.assertEqual(entradas["territorios"]["default"], "todos")
        self.assertNotIn("version", entradas)  # versión automática

    def test_sin_tildes_en_los_inputs(self):
        for k, v in on(self.p)["workflow_dispatch"]["inputs"].items():
            self.assertTrue(k.isascii(), k)
            self.assertTrue(k.isidentifier(), k)

    def test_concurrencia_en_cola(self):
        self.assertEqual(self.p["concurrency"]["queue"], "max")
        self.assertFalse(self.p["concurrency"]["cancel-in-progress"])


class Equivalencia(Congelado):
    def test_entorno_permisos_empaquetado_y_atestacion_identicos(self):
        self.assertEqual(diferencias(self.v, self.p), [])

    def test_entorno_y_permisos_literales(self):
        j = self.p["jobs"]["publicar"]
        self.assertEqual(j["environment"], "publicacion")
        self.assertEqual(j["permissions"], {"contents": "write", "actions": "read", "id-token": "write", "attestations": "write"})
        self.assertEqual(self.p["permissions"], {"contents": "read"})

    def test_ningun_job_gana_permisos(self):
        r = self.p["jobs"]["resolver"]
        self.assertEqual(r["permissions"], {"contents": "read"})
        self.assertNotIn("environment", r)
        self.assertEqual(self.p["jobs"]["publicar"]["needs"], "resolver")

    def test_paquete_mismo_contenido(self):
        run = paso(self.p["jobs"]["publicar"], "Añadir contexto de linaje")["run"]
        for frag in ('cp -r "territorios/$T/config"', "configuracion/controles_obligatorios.yaml", "CITATION.cff",
                     '"schema": "ddd.version-mapa/1.0"', '"oficial": False', '"source_commit"', "LINAJE.json"):
            self.assertIn(frag, run)
        self.assertIn("ddd-${T}-v${V}.tar.gz", paso(self.p["jobs"]["publicar"], "Empaquetar de forma determinista")["run"])

    def test_linaje_lleva_blob_sha256_run_y_commit_del_registro_del_visor(self):
        run = paso(self.p["jobs"]["publicar"], "Añadir contexto de linaje")["run"]
        for frag in ('"blob_sha": os.environ["BLOB"]', '"sha256": os.environ["SHA"]', '"production_run_id": os.environ["RUN"]',
                     '"source_run_id": os.environ["RUN"]', '"source_commit": os.environ["SRC_SHA"]'):
            self.assertIn(frag, run)
        self.assertNotIn('"production_run_id": None', run)
        # blob_sha, sha256 y run salen del plan, que sale del registro del visor
        import sys
        sys.path.insert(0, str(ROOT / "herramientas"))
        sys.path.insert(0, str(ROOT))
        import p50_resolver as r
        for t, p in r.vigentes(ROOT).items():
            self.assertTrue(p["blob_sha"] and p["sha256"] and str(p["run_id"]).isdigit(), t)

    def test_release_una_por_lote_con_todos_los_territorios(self):
        run = paso(self.p["jobs"]["publicar"], "Crear Release")["run"]
        self.assertEqual(len(re.findall(r"gh release create", run)), 1)
        self.assertIn('"$TAG"', run)
        self.assertIn("MAPAS.json", run)
        self.assertEqual(self.p["jobs"]["publicar"]["env"]["TAG"], "${{ needs.resolver.outputs.tag }}")

    def test_m06_del_visor_no_de_artefacto_de_actions(self):
        j = self.p["jobs"]["publicar"]
        self.assertTrue(any(u.startswith("actions/download-artifact") for u in usos(j)))  # solo el plan
        for s in j["steps"]:
            if str(s.get("uses", "")).startswith("actions/download-artifact"):
                self.assertEqual(s["with"]["name"], "p50-plan")
                self.assertNotIn("run-id", s["with"])
        self.assertIn("p50_resolver.py blob", paso(j, "Descargar M06 del visor (sha256 verificado)")["run"])

    def test_cadena_ya_no_lanza_p50(self):
        self.assertFalse((WF / "cadena-publicacion.yml").exists())  # T-372: la cadena se funde en P40
        p40 = (WF / "p40-publicacion.yml").read_text(encoding="utf-8")
        self.assertNotIn("p50-publicacion-academica", p40.replace("legacy/", ""))
        self.assertNotIn("version_mapa", p40)


class Negativos(Congelado):
    def test_permiso_ganado_o_perdido_se_detecta(self):
        n = copy.deepcopy(self.p)
        n["jobs"]["publicar"]["permissions"]["packages"] = "write"
        self.assertIn("permisos", diferencias(self.v, n))
        n = copy.deepcopy(self.p)
        del n["jobs"]["publicar"]["permissions"]["attestations"]
        self.assertIn("permiso perdido", diferencias(self.v, n))

    def test_entorno_cambiado_se_detecta(self):
        n = copy.deepcopy(self.p)
        n["jobs"]["publicar"]["environment"] = "produccion"
        self.assertIn("entorno", diferencias(self.v, n))
        del n["jobs"]["publicar"]["environment"]
        self.assertIn("entorno", diferencias(self.v, n))

    def test_empaquetado_o_manifiesto_alterado_se_detecta(self):
        n = copy.deepcopy(self.p)
        paso(n["jobs"]["publicar"], "Empaquetar de forma determinista")["run"] = "tar -czf x.tar.gz ."
        self.assertIn("empaquetado", diferencias(self.v, n))
        n = copy.deepcopy(self.p)
        paso(n["jobs"]["publicar"], "Manifiesto SHA-256")["run"] = "sha256sum * > SHA256SUMS"
        self.assertIn("manifiesto", diferencias(self.v, n))

    def test_atestacion_quitada_o_cambiada_se_detecta(self):
        n = copy.deepcopy(self.p)
        n["jobs"]["publicar"]["steps"] = [s for s in n["jobs"]["publicar"]["steps"]
                                          if not str(s.get("uses", "")).startswith("actions/attest-build-provenance")]
        self.assertIn("atestación", diferencias(self.v, n))
        n = copy.deepcopy(self.p)
        for s in n["jobs"]["publicar"]["steps"]:
            if str(s.get("uses", "")).startswith("actions/attest-build-provenance"):
                s["uses"] = "actions/attest-build-provenance@v1"
        self.assertIn("atestación", diferencias(self.v, n))

    def test_huella_de_la_copia_congelada(self):
        self.assertNotEqual(hashlib.sha256(FIX.read_bytes() + b"x").hexdigest(), SHA)


class Resolutor(unittest.TestCase):
    def setUp(self):
        import sys
        sys.path.insert(0, str(ROOT / "herramientas"))
        sys.path.insert(0, str(ROOT))
        import p50_resolver as r
        self.r = r

    def test_primera_version_es_1_0_0(self):
        self.assertEqual(self.r.version("", None, {"aut01": "a"}), "1.0.0")
        self.assertEqual(self.r.version("otra-etiqueta\n", None, {"aut01": "a"}), "1.0.0")

    def test_sube_la_menor_si_cambia_el_mapa(self):
        self.assertEqual(self.r.version("mapas-v1.0.0\n", {"aut01": "a"}, {"aut01": "b"}), "1.1.0")
        self.assertEqual(self.r.version("mapas-v1.2.0\nmapas-v1.10.0\nmapas-v1.9.0\n", {"a": "1"}, {"a": "2"}), "1.11.0")

    def test_se_niega_si_no_cambia_o_falta_el_previo(self):
        with self.assertRaisesRegex(ValueError, "P50_MAPA_SIN_CAMBIOS"):
            self.r.version("mapas-v1.0.0\n", {"aut01": "a"}, {"aut01": "a"})
        with self.assertRaisesRegex(ValueError, "P50_SIN_MAPAS_PREVIO"):
            self.r.version("mapas-v1.0.0\n", None, {"aut01": "a"})

    def test_ultima(self):
        self.assertEqual(self.r.ultima("x\nmapas-v1.2.0\nmapas-v1.10.0\n"), "mapas-v1.10.0")
        self.assertEqual(self.r.ultima(""), "")

    def test_territorios(self):
        todos = self.r.elegir(ROOT, "todos")
        self.assertTrue(todos)
        un = sorted(todos)[0]
        self.assertEqual(list(self.r.elegir(ROOT, f" {un.upper()} ")), [un])
        for malo in ("", "  ", "xx9", "aut01;rm", "congreso350_valladolid"):
            with self.assertRaises(ValueError, msg=malo):
                self.r.elegir(ROOT, malo)

    def test_cli_errores_a_stderr_y_rc_1(self):
        with tempfile.TemporaryDirectory() as d:
            t = Path(d) / "t.txt"
            t.write_text("", encoding="utf-8")
            p = subprocess.run(["python3", str(ROOT / "herramientas" / "p50_resolver.py"), "plan", "--territorios", "xx9", "--tags", str(t)],
                               capture_output=True, text=True)
            self.assertEqual(p.returncode, 1)
            self.assertEqual(p.stdout, "")
            self.assertIn("P50_TERRITORIO_DESCONOCIDO", p.stderr)
            ok = subprocess.run(["python3", str(ROOT / "herramientas" / "p50_resolver.py"), "plan", "--territorios", "todos", "--tags", str(t)],
                                capture_output=True, text=True)
            self.assertEqual(ok.returncode, 0)
            self.assertEqual(json.loads(ok.stdout)["version"], "1.0.0")

    def test_tag_existente_se_niega(self):
        original = self.r.version
        self.r.version = lambda *a, **k: "1.0.0"  # versión candidata ya presente como etiqueta (Release borrada/archivada)
        try:
            with tempfile.TemporaryDirectory() as d:
                (Path(d) / "visor").mkdir()
                with self.assertRaisesRegex(ValueError, "P50_TAG_EXISTE"):
                    self.r.plan(ROOT, "todos", "mapas-v1.0.0\n", None)
        finally:
            self.r.version = original

    def _bajar(self, rc, out=b"", err=b"", sha=None):
        import unittest.mock as m
        blob = "a" * 40
        h = sha or hashlib.sha256(out).hexdigest()
        with tempfile.TemporaryDirectory() as d, m.patch.object(
                self.r.subprocess, "run", return_value=subprocess.CompletedProcess([], rc, out, err)):
            destino = Path(d) / "x" / "m06.zip"
            try:
                self.r.bajar(blob, h, destino, "o/r")
            finally:
                escrito = destino.is_file()
        return escrito

    def test_bajar_ok_y_fallos_cerrados(self):
        self.assertTrue(self._bajar(0, b"zip"))
        with self.assertRaisesRegex(ValueError, "P50_SHA256_NO_CUADRA"):
            self._bajar(0, b"zip", sha="0" * 64)
        with self.assertRaisesRegex(ValueError, "P50_BLOB_NO_BAJA"):
            self._bajar(1, b"", b"HTTP 404")

    def test_sha256_no_cuadra_no_deja_fichero(self):
        import unittest.mock as m
        with tempfile.TemporaryDirectory() as d, m.patch.object(
                self.r.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, b"zip", b"")):
            destino = Path(d) / "m06.zip"
            with self.assertRaises(ValueError):
                self.r.bajar("a" * 40, "0" * 64, destino, "o/r")
            self.assertFalse(destino.exists())

    def test_blob_mal_formado_falla_cerrado(self):
        with self.assertRaisesRegex(ValueError, "P50_BLOB_INVALIDO"):
            self.r.bajar("zz", "yy", Path("/nonexistent/x"), "o/r")


class PasosBash(Congelado):
    def test_pasos_de_shell_bash_n_y_eo_pipefail(self):
        for job in self.p["jobs"].values():
            for s in job["steps"]:
                if "run" in s and "<<PY" not in s["run"]:
                    r = subprocess.run(["bash", "-n"], input=s["run"], text=True, capture_output=True)
                    self.assertEqual(r.returncode, 0, r.stderr)
        # la secuencia del resolver con tags vacíos (sin Release previa) no aborta bajo `bash -eo pipefail`
        with tempfile.TemporaryDirectory() as d:
            sh = (f'cd {d}; : > tags.txt; ult="$(python3 {ROOT}/herramientas/p50_resolver.py ultima --tags tags.txt)"; '
                  f'python3 {ROOT}/herramientas/p50_resolver.py plan --territorios todos --tags tags.txt --previo "" > plan.json; '
                  f'test -z "$ult"; jq -r .version plan.json')
            r = subprocess.run(["bash", "-eo", "pipefail", "-c", sh], capture_output=True, text=True)
            self.assertEqual((r.returncode, r.stdout.strip()), (0, "1.0.0"), r.stderr)


if __name__ == "__main__":
    unittest.main()
