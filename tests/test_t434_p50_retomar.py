# -*- coding: utf-8 -*-
"""T-434: P50 1.2.0 — paquete de Deslinde fuera del lote, «Retomar el depósito en Zenodo» y prueba sin Release pública.

PROYECTO: Diputado de Distrito · VERSIÓN: 1.0.0 · FECHA: 2026-11-20 · ESTADO: candidato · ANTERIOR: ninguna (fichero nuevo)
Hecho de partida (run 44748912809, main@622bc97f): la 1.1.0 empaquetaba con `for d in paquetes/*/`, que recoge el directorio
versionado `paquetes/deslinde` (código del motor) y lo subió a la Release mapas-v1.0.0 como ddd-deslinde-v1.0.0.tar.gz, sin
LINAJE.json; el job `zenodo` falló con ZENODO_SIN_LINAJE. Los pasos de shell se EJECUTAN aquí (no se buscan cadenas): la copia
congelada de la 1.1.0 (`tests/fixtures/t434_workflows/`, con sha256) reproduce el fallo y la 1.2.0 no.
"""
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

import yaml

from tests._uses_sin_version import cargar as cargar_sin_version

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
sys.path.insert(0, str(ROOT))
import p50_resolver as res  # noqa: E402
import zenodo_deposito as z  # noqa: E402

WF = ROOT / ".github" / "workflows" / "p50-publicacion-academica.yml"
FIX = ROOT / "tests" / "fixtures" / "t434_workflows" / "p50-publicacion-academica_1.1.0.yml"
SHA_FIX = "4d5ae8374e18b6b459234f86604fce2da1b3dc1c1e295987e6399fcc9bd8d1b0"
RETOMAR = "Retomar el depósito en Zenodo de la última versión"
NUEVA = "Publicar una versión nueva"
H = {t: hashlib.sha256(t.encode()).hexdigest() for t in ("aut01", "aut02", "nac42")}


def on(d):
    return d.get("on") or d.get(True)


def paso(job, nombre):
    return next(s for s in job["steps"] if s.get("name") == nombre)


def evaluar(expr, modo, destino, r_publicar="success", r_resolver="success"):
    """Evalúa una condición `if:` de GitHub con el subconjunto que usa P50 (traducción literal a Python)."""
    e = expr.strip()
    e = re.sub(r"^\$\{\{|\}\}$", "", e).strip()
    e = e.replace("!cancelled()", "True").replace("&&", " and ").replace("||", " or ")
    e = e.replace("needs.resolver.outputs.modo", repr(modo)).replace("inputs.destino", repr(destino))
    e = e.replace("needs.publicar.result", repr(r_publicar)).replace("needs.resolver.result", repr(r_resolver))
    assert re.fullmatch(r"[\s()'\w=áéíóú.-]+", e.replace("!=", "==")), e  # nada sin traducir
    return eval(e, {"__builtins__": {}}, {"True": True})  # noqa: S307 (expresión cerrada del propio workflow)


def ejecuta(job, modo, destino, r_publicar="success"):
    return evaluar(job.get("if", "true == true"), modo, destino, r_publicar)


def paquete(d: Path, t: str, v: str, sha: str) -> Path:
    p = d / f"ddd-{t}-v{v}.tar.gz"
    with tarfile.open(p, "w:gz") as tf:
        datos = json.dumps({"territory_id": t, "version": v, "sha256": sha, "oficial": False}).encode()
        ti = tarfile.TarInfo("./LINAJE.json")
        ti.size = len(datos)
        tf.addfile(ti, io.BytesIO(datos))
    return p


def codigo_deslinde(d: Path, v: str) -> Path:
    """Como el ddd-deslinde-v1.0.0.tar.gz de la Release: código, sin LINAJE.json."""
    p = d / f"ddd-deslinde-v{v}.tar.gz"
    with tarfile.open(p, "w:gz") as tf:
        datos = b"print('motor')\n"
        ti = tarfile.TarInfo("./src/deslinde/api.py")
        ti.size = len(datos)
        tf.addfile(ti, io.BytesIO(datos))
    return p


def lote_release(d: Path, v="1.0.0", con_deslinde=True) -> Path:
    """Réplica del contenido de la Release: paquetes de territorios, (el de Deslinde), SHA256SUMS y MAPAS.json."""
    d.mkdir(parents=True, exist_ok=True)
    ps = [paquete(d, t, v, H[t]) for t in ("aut01", "aut02")]
    if con_deslinde:
        ps.append(codigo_deslinde(d, v))
    (d / "SHA256SUMS").write_text("".join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n" for p in sorted(ps)))
    (d / "MAPAS.json").write_text(json.dumps({"aut01": H["aut01"], "aut02": H["aut02"]}))
    return d


class Congelado(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assert FIX.is_file(), f"falta la copia congelada {FIX}"  # nunca se salta
        datos = FIX.read_bytes()
        assert hashlib.sha256(datos).hexdigest() == SHA_FIX, "la copia congelada cambió"
        cls.viejo = yaml.safe_load(datos.decode("utf-8"))
        cls.nuevo = yaml.safe_load(WF.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- (1) el paquete de Deslinde no entra
class PasosDePublicar(Congelado):
    """Ejecuta «Añadir contexto de linaje», «Manifiesto» y «Empaquetar» de cada versión sobre un árbol con `paquetes/deslinde`."""

    def _arbol(self, d: Path, ts):
        for n in ("territorios", "configuracion", "CITATION.cff"):
            (d / n).symlink_to(ROOT / n)
        (d / "paquetes" / "deslinde" / "src").mkdir(parents=True)  # el directorio versionado del repo (código)
        (d / "paquetes" / "deslinde" / "README.md").write_text("Deslinde\n")
        plan = {"modo": "nueva", "version": "9.9.0", "tag": "mapas-v9.9.0", "mapa": {t: H.get(t, "0" * 64) for t in ts},
                "territorios": [{"territory_id": t, "run_id": "1", "blob_sha": "a" * 40, "sha256": H.get(t, "0" * 64)} for t in ts]}
        (d / "plan.json").write_text(json.dumps(plan))
        g = ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false"]
        subprocess.run(["git", "init", "-q", str(d)], check=True)
        subprocess.run(g + ["-C", str(d), "commit", "-q", "--allow-empty", "-m", "x"], check=True)

    def _publicar(self, wf, d: Path, tmp: Path, base: str):
        for t in json.loads((d / "plan.json").read_text())["mapa"]:
            m06 = Path(base.replace("$RUNNER_TEMP", str(tmp))) / t / "productos" / f"{t}_m06_1.zip"
            m06.parent.mkdir(parents=True, exist_ok=True)
            m06.write_bytes(b"m06 " + t.encode())
        env = {**os.environ, "V": "9.9.0", "RUNNER_TEMP": str(tmp)}
        for nombre in ("Añadir contexto de linaje", "Manifiesto SHA-256", "Empaquetar de forma determinista"):
            r = subprocess.run(["bash", "-eo", "pipefail", "-c", paso(wf["jobs"]["publicar"], nombre)["run"]],
                               cwd=d, env=env, capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, f"{nombre}: {r.stderr}")
        return sorted(p.name for p in (d / "salida").glob("ddd-*.tar.gz"))

    def _miembros(self, p: Path):
        with tarfile.open(p) as tf:
            out = {}
            for m in tf.getmembers():
                if m.isfile():
                    b = tf.extractfile(m).read()
                    if m.name == "./LINAJE.json":
                        j = json.loads(b)
                        j.pop("published_at")
                        b = json.dumps(j, sort_keys=True).encode()
                    if m.name == "./SHA256SUMS":
                        b = b"".join(l + b"\n" for l in b.splitlines() if not l.endswith(b"LINAJE.json"))
                    out[m.name] = b
            return out

    def test_la_1_1_0_reproduce_el_fallo_y_la_1_2_0_no(self):
        ts = sorted(res.vigentes(ROOT))[:2]
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b, \
                tempfile.TemporaryDirectory() as ta, tempfile.TemporaryDirectory() as tb:
            da, db = Path(a), Path(b)
            self._arbol(da, ts)
            self._arbol(db, ts)
            # la 1.1.0 trabaja en `paquetes/` del árbol: el M06 se deja allí, como hacía su paso de descarga
            viejo = self._publicar(self.viejo, da, Path(ta), str(da / "paquetes"))
            nuevo = self._publicar(self.nuevo, db, Path(tb), "$RUNNER_TEMP/p50/paquetes")
            self.assertIn("ddd-deslinde-v9.9.0.tar.gz", viejo)  # el fallo de mapas-v1.0.0, reproducido
            self.assertEqual(nuevo, [f"ddd-{t}-v9.9.0.tar.gz" for t in ts])
            self.assertEqual(viejo, sorted(nuevo + ["ddd-deslinde-v9.9.0.tar.gz"]))
            # equivalencia: cada paquete de territorio tiene el mismo contenido (salvo la hora de published_at)
            for n in nuevo:
                self.assertEqual(self._miembros(da / "salida" / n), self._miembros(db / "salida" / n), n)
            self.assertFalse((db / "paquetes" / "deslinde" / "SHA256SUMS").exists())  # el código del repo no se toca
            # y el lote de la 1.2.0 pasa el `preparar` del depósito
            self.assertEqual(len(z.preparar(db / "salida", "9.9.0", db / "zen")), len(ts))

    def test_ningun_paso_usa_el_directorio_paquetes_del_repo(self):
        for s in self.nuevo["jobs"]["publicar"]["steps"]:
            run = s.get("run", "")
            self.assertNotRegex(run, r'(?<![/\w])paquetes/', s.get("name"))


class Preparar(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_excluye_deslinde_y_deja_sumas_y_linaje_solo_de_los_territorios(self):
        lote = lote_release(self.d / "lote")
        avisos = []
        lin = z.preparar(lote, "1.0.0", self.d / "zen", avisar=avisos.append)
        self.assertEqual([x["territory_id"] for x in lin], ["aut01", "aut02"])
        zen = sorted(p.name for p in (self.d / "zen").iterdir())
        self.assertEqual(zen, ["LINAJE.json", "SHA256SUMS", "ddd-aut01-v1.0.0.tar.gz", "ddd-aut02-v1.0.0.tar.gz"])
        sumas = (self.d / "zen" / "SHA256SUMS").read_text()
        self.assertNotIn("deslinde", sumas)
        for n in ("ddd-aut01-v1.0.0.tar.gz", "ddd-aut02-v1.0.0.tar.gz"):
            self.assertIn(f"{hashlib.sha256((lote / n).read_bytes()).hexdigest()}  {n}", sumas)
        self.assertEqual(avisos, ["excluido del depósito: ddd-deslinde-v1.0.0.tar.gz (no es un territorio del lote)"])
        # con los dos ficheros de acompañamiento, el conjunto pasa la validación del depósito
        for n in ("LICENCIA_CC-BY-4.0.txt", "NOTA_FUENTES.md"):
            (self.d / "zen" / n).write_text("x")
        self.assertEqual(len(z.validar_ficheros(sorted((self.d / "zen").iterdir()))), 6)

    def test_la_1_1_0_fallaba_con_el_mismo_lote(self):
        lote = lote_release(self.d / "lote")
        with self.assertRaisesRegex(z.ErrorDeposito, "ZENODO_SIN_LINAJE: ddd-deslinde-v1.0.0.tar.gz"):
            z.unir_linaje(lote)

    def test_paquete_alterado_falla_cerrado(self):
        lote = lote_release(self.d / "lote")
        paquete(lote, "aut02", "1.0.0", "f" * 64)  # contenido distinto del de SHA256SUMS
        with self.assertRaisesRegex(z.ErrorDeposito, "ZENODO_SHA256_NO_CUADRA: ddd-aut02"):
            z.preparar(lote, "1.0.0", self.d / "zen")

    def test_falta_un_territorio_falla_cerrado(self):
        lote = lote_release(self.d / "lote")
        (lote / "ddd-aut02-v1.0.0.tar.gz").unlink()
        with self.assertRaisesRegex(z.ErrorDeposito, "ZENODO_FICHERO_AUSENTE: ddd-aut02"):
            z.preparar(lote, "1.0.0", self.d / "zen")

    def test_linaje_de_otro_m06_o_version_falla_cerrado(self):
        lote = lote_release(self.d / "lote")
        (lote / "MAPAS.json").write_text(json.dumps({"aut01": H["aut01"], "aut02": H["nac42"]}))
        with self.assertRaisesRegex(z.ErrorDeposito, "ZENODO_LINAJE_NO_CUADRA: .*aut02"):
            z.preparar(lote, "1.0.0", self.d / "zen")

    def test_sin_mapas_o_sin_sumas_falla_cerrado(self):
        lote = lote_release(self.d / "lote")
        (lote / "MAPAS.json").unlink()
        with self.assertRaisesRegex(z.ErrorDeposito, "ZENODO_SIN_MAPAS"):
            z.preparar(lote, "1.0.0", self.d / "zen")
        lote = lote_release(self.d / "lote2")
        (lote / "SHA256SUMS").unlink()
        with self.assertRaisesRegex(z.ErrorDeposito, "ZENODO_FALTAN_FICHEROS"):
            z.preparar(lote, "1.0.0", self.d / "zen")

    def test_cli(self):
        lote = lote_release(self.d / "lote")
        p = subprocess.run([sys.executable, str(ROOT / "herramientas" / "zenodo_deposito.py"), "preparar", "--lote", str(lote),
                            "--version", "1.0.0", "--salida", str(self.d / "zen")], capture_output=True, text=True)
        self.assertEqual((p.returncode, p.stdout), (0, ""), p.stderr)
        self.assertIn("excluido del depósito: ddd-deslinde", p.stderr)


# ---------------------------------------------------------------- (2) retomar el depósito sobre la Release ya creada
class Retomar(Congelado):
    def test_resolutor_da_la_ultima_version_sin_crear_otra(self):
        r = res.retomar("mapas-v1.0.0\nmapas-v0.9.0\n", {"aut02": H["aut02"], "aut01": H["aut01"]})
        self.assertEqual(r, {"modo": "retomar", "version": "1.0.0", "tag": "mapas-v1.0.0",
                             "mapa": {"aut01": H["aut01"], "aut02": H["aut02"]},
                             "territorios": [{"territory_id": "aut01"}, {"territory_id": "aut02"}]})

    def test_resolutor_se_niega_sin_version_o_sin_mapas(self):
        with self.assertRaisesRegex(ValueError, "P50_SIN_VERSION_QUE_RETOMAR"):
            res.retomar("", {"aut01": H["aut01"]})
        with self.assertRaisesRegex(ValueError, "P50_SIN_MAPAS_PREVIO"):
            res.retomar("mapas-v1.0.0\n", None)
        with self.assertRaisesRegex(ValueError, "P50_MAPAS_INVALIDO"):
            res.retomar("mapas-v1.0.0\n", {"aut01;rm": H["aut01"]})

    def test_boton_en_espanol_sin_parametros_tecnicos(self):
        e = on(self.nuevo)["workflow_dispatch"]["inputs"]["accion"]
        self.assertEqual((e["type"], e["default"], e["options"]), ("choice", NUEVA, [NUEVA, RETOMAR]))
        texto = json.dumps(e, ensure_ascii=False)
        self.assertNotRegex(texto, r"run[_ ]?id|sha|\bv?\d+\.\d+\.\d+\b|mapas-v")

    def _resolver(self, accion, tags, mapas_previo):
        """Ejecuta el paso «Resolver» con un `gh` simulado que sirve la Release mapas-v1.0.0 y su MAPAS.json."""
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "herramientas").symlink_to(ROOT / "herramientas")
            for n in ("orchestracion", "ddd_core"):
                (d / n).symlink_to(ROOT / n)
            (d / "MAPAS_srv.json").write_text(json.dumps(mapas_previo))
            bin_ = d / "bin"
            bin_.mkdir()
            (bin_ / "gh").write_text(
                "#!/bin/bash\n"
                f'case "$*" in\n'
                f'  *"/releases --paginate"*) printf "%s\\n" {" ".join(tags) or "\"\""} | grep . || true ;;\n'
                f'  *"matching-refs"*) : ;;\n'
                f'  *"/releases/tags/"*) echo 77 ;;\n'
                f'  *"/releases/assets/77"*) cat "{d}/MAPAS_srv.json" ;;\n'
                f'  *) echo "gh inesperado: $*" >&2; exit 9 ;;\n'
                "esac\n")
            (bin_ / "gh").chmod(0o755)
            out, summ = d / "out", d / "summ"
            env = {**os.environ, "PATH": f"{bin_}:{os.environ['PATH']}", "GITHUB_REPOSITORY": "o/r", "GITHUB_OUTPUT": str(out),
                   "GITHUB_STEP_SUMMARY": str(summ), "TERRITORIOS": "todos", "ACCION": accion, "GH_TOKEN": "x"}
            r = subprocess.run(["bash", "-eo", "pipefail", "-c", paso(self.nuevo["jobs"]["resolver"], "Resolver")["run"]],
                               cwd=d, env=env, capture_output=True, text=True)
            salida = dict(l.split("=", 1) for l in out.read_text().splitlines()) if out.exists() else {}
            return r, salida

    def test_paso_resolver_retomar_sobre_mapas_v1_0_0(self):
        r, o = self._resolver(RETOMAR, ["mapas-v1.0.0"], {"aut01": H["aut01"], "aut02": H["aut02"]})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(o, {"version": "1.0.0", "tag": "mapas-v1.0.0", "modo": "retomar"})

    def test_paso_resolver_nueva_sigue_negandose_si_no_cambia(self):
        vig = {t: p["sha256"] for t, p in res.vigentes(ROOT).items()}
        r, _ = self._resolver(NUEVA, ["mapas-v1.0.0"], vig)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("P50_MAPA_SIN_CAMBIOS", r.stderr)
        r, o = self._resolver(NUEVA, ["mapas-v1.0.0"], {**vig, sorted(vig)[0]: "0" * 64})
        self.assertEqual((r.returncode, o.get("version"), o.get("modo")), (0, "1.1.0", "nueva"), r.stderr)

    def test_retomar_no_crea_paquete_ni_release_y_si_deposita(self):
        j = self.nuevo["jobs"]
        for destino in ("prueba", "Zenodo"):
            self.assertFalse(ejecuta(j["publicar"], "retomar", destino))
            self.assertTrue(ejecuta(j["zenodo"], "retomar", destino, r_publicar="skipped"))
            self.assertFalse(evaluar(paso(j["zenodo"], "Lote de prueba de este run (sin Release)")["if"], "retomar", destino))
        reunir = paso(j["zenodo"], "Reunir ficheros del depósito (solo mapas, sin código)")["run"]
        self.assertIn('[[ "$MODO" == "retomar" || "$DESTINO" == "Zenodo" ]]', reunir)
        self.assertIn("--pattern MAPAS.json", reunir)
        self.assertIn("zenodo_deposito.py preparar --lote lote", reunir)

    def test_nueva_deposita_solo_si_publicar_acaba_bien(self):
        j = self.nuevo["jobs"]
        for destino in ("prueba", "Zenodo"):
            self.assertTrue(ejecuta(j["publicar"], "nueva", destino))
            self.assertTrue(ejecuta(j["zenodo"], "nueva", destino, "success"))
            for malo in ("failure", "cancelled", "skipped"):
                self.assertFalse(ejecuta(j["zenodo"], "nueva", destino, malo), (destino, malo))
        self.assertFalse(evaluar(j["zenodo"]["if"], "retomar", "Zenodo", "success", r_resolver="failure"))

    def test_paso_reunir_con_la_release_real_simulada(self):
        """El paso «Reunir» con un `gh release download` simulado que sirve el lote de mapas-v1.0.0 (con Deslinde)."""
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            srv = lote_release(d / "srv")
            for n in ("herramientas", "docs"):
                (d / n).symlink_to(ROOT / n)
            bin_ = d / "bin"
            bin_.mkdir()
            (bin_ / "gh").write_text('#!/bin/bash\n[[ "$1 $2" == "release download" ]] || exit 9\n'
                                     'dir=$(sed -n "s/.*--dir \\([^ ]*\\).*/\\1/p" <<<"$*")\n'
                                     f'cp "{srv}"/* "$dir"/\n')
            (bin_ / "gh").chmod(0o755)
            env = {**os.environ, "PATH": f"{bin_}:{os.environ['PATH']}", "GITHUB_REPOSITORY": "o/r", "TAG": "mapas-v1.0.0",
                   "V": "1.0.0", "MODO": "retomar", "DESTINO": "prueba", "GH_TOKEN": "x"}
            run = paso(self.nuevo["jobs"]["zenodo"], "Reunir ficheros del depósito (solo mapas, sin código)")["run"]
            r = subprocess.run(["bash", "-eo", "pipefail", "-c", run], cwd=d, env=env, capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(sorted(p.name for p in (d / "zen").iterdir()),
                             ["LICENCIA_CC-BY-4.0.txt", "LINAJE.json", "NOTA_FUENTES.md", "SHA256SUMS",
                              "ddd-aut01-v1.0.0.tar.gz", "ddd-aut02-v1.0.0.tar.gz"])


# ---------------------------------------------------------------- (3) una prueba nunca crea una Release pública
class PruebaSinRelease(Congelado):
    def test_crear_release_solo_con_destino_zenodo(self):
        pub = self.nuevo["jobs"]["publicar"]
        cr = paso(pub, "Crear Release")
        self.assertFalse(evaluar(cr["if"], "nueva", "prueba"))
        self.assertTrue(evaluar(cr["if"], "nueva", "Zenodo"))
        self.assertNotIn("if", paso(self.viejo["jobs"]["publicar"], "Crear Release"))  # la 1.1.0 la creaba siempre

    def test_ningun_otro_paso_escribe_releases_ni_etiquetas(self):
        for jn, job in self.nuevo["jobs"].items():
            for s in job["steps"]:
                run = s.get("run", "")
                escribe = re.search(r"gh release (create|upload|edit)|releases\b.*-X\s*(POST|PATCH|PUT)|git (tag|push)", run)
                if escribe:
                    self.assertEqual((jn, s.get("name")), ("publicar", "Crear Release"))

    def test_prueba_guarda_el_lote_como_artefacto_y_el_deposito_lo_usa(self):
        pub, zen = self.nuevo["jobs"]["publicar"], self.nuevo["jobs"]["zenodo"]
        g = paso(pub, "Guardar el lote de prueba (sin Release)")
        self.assertTrue(evaluar(g["if"], "nueva", "prueba"))
        self.assertFalse(evaluar(g["if"], "nueva", "Zenodo"))
        self.assertTrue(g["uses"].startswith("actions/upload-artifact@"))
        self.assertEqual(g["with"]["name"], "p50-lote-prueba")
        b = paso(zen, "Lote de prueba de este run (sin Release)")
        self.assertTrue(evaluar(b["if"], "nueva", "prueba"))
        self.assertFalse(evaluar(b["if"], "nueva", "Zenodo"))
        self.assertEqual((b["with"]["name"], b["with"]["path"]), ("p50-lote-prueba", "lote"))
        self.assertNotIn("run-id", b["with"])  # solo el de este run

    def test_paso_reunir_en_prueba_nueva_no_baja_de_releases(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            lote_release(d / "lote", con_deslinde=False)
            for n in ("herramientas", "docs"):
                (d / n).symlink_to(ROOT / n)
            bin_ = d / "bin"
            bin_.mkdir()
            (bin_ / "gh").write_text("#!/bin/bash\necho 'gh no debe llamarse' >&2\nexit 9\n")
            (bin_ / "gh").chmod(0o755)
            env = {**os.environ, "PATH": f"{bin_}:{os.environ['PATH']}", "GITHUB_REPOSITORY": "o/r", "TAG": "mapas-v1.0.0",
                   "V": "1.0.0", "MODO": "nueva", "DESTINO": "prueba", "GH_TOKEN": "x"}
            run = paso(self.nuevo["jobs"]["zenodo"], "Reunir ficheros del depósito (solo mapas, sin código)")["run"]
            r = subprocess.run(["bash", "-eo", "pipefail", "-c", run], cwd=d, env=env, capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertTrue((d / "zen" / "LINAJE.json").is_file())


# ---------------------------------------------------------------- (4) el resto de P50, igual que en la 1.1.0
CAMBIADOS = {("resolver", "Resolver"), ("publicar", "Descargar M06 del visor (sha256 verificado)"),
             ("publicar", "Añadir contexto de linaje"), ("publicar", "Manifiesto SHA-256"),
             ("publicar", "Empaquetar de forma determinista"), ("publicar", "Crear Release"),
             ("zenodo", "Reunir ficheros del depósito (solo mapas, sin código)")}
NUEVOS = {("publicar", "Guardar el lote de prueba (sin Release)"), ("zenodo", "Lote de prueba de este run (sin Release)")}


class EquivalenciaResto(Congelado):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.v = cargar_sin_version(FIX.read_text(encoding="utf-8"))
        cls.n = cargar_sin_version(WF.read_text(encoding="utf-8"))

    def test_cabecera_de_workflow_igual(self):
        for k in ("name", "permissions", "concurrency"):
            self.assertEqual(self.v[k], self.n[k], k)
        self.assertEqual(set(on(self.n)), {"workflow_dispatch"})

    def test_entradas_previas_mismo_tipo_defecto_y_opciones(self):
        vi, ni = on(self.v)["workflow_dispatch"]["inputs"], on(self.n)["workflow_dispatch"]["inputs"]
        self.assertEqual(set(ni) - set(vi), {"accion"})
        for k, e in vi.items():
            for c in ("type", "default", "options", "required"):
                self.assertEqual(e.get(c), ni[k].get(c), (k, c))

    def test_jobs_mismo_entorno_permisos_runner_y_needs(self):
        self.assertEqual(set(self.v["jobs"]), set(self.n["jobs"]))
        for jn, jv in self.v["jobs"].items():
            jn_ = self.n["jobs"][jn]
            for c in ("runs-on", "environment", "permissions", "needs", "env", "outputs"):
                if c in ("env", "outputs"):
                    self.assertLessEqual(set((jv.get(c) or {}).items()), set((jn_.get(c) or {}).items()), (jn, c))
                else:
                    self.assertEqual(jv.get(c), jn_.get(c), (jn, c))

    def test_pasos_no_cambiados_identicos_y_en_el_mismo_orden(self):
        for jn, jv in self.v["jobs"].items():
            nombres_v = [s.get("name", s.get("uses")) for s in jv["steps"]]
            nombres_n = [s.get("name", s.get("uses")) for s in self.n["jobs"][jn]["steps"] if (jn, s.get("name")) not in NUEVOS]
            self.assertEqual(nombres_v, nombres_n, jn)
            for sv, sn in zip(jv["steps"], [s for s in self.n["jobs"][jn]["steps"] if (jn, s.get("name")) not in NUEVOS]):
                if (jn, sv.get("name")) in CAMBIADOS:
                    continue
                self.assertEqual(sv, sn, (jn, sv.get("name")))

    def test_pasos_cambiados_conservan_lo_esencial(self):
        pv, pn = self.v["jobs"]["publicar"], self.n["jobs"]["publicar"]
        for nombre in ("Crear Release", "Descargar M06 del visor (sha256 verificado)"):
            self.assertEqual(paso(pv, nombre)["run"].replace('"paquetes/$T', '"$RUNNER_TEMP/p50/paquetes/$T'),
                             paso(pn, nombre)["run"], nombre)
            self.assertEqual(paso(pv, nombre).get("env"), paso(pn, nombre).get("env"))
        lv, ln = paso(pv, "Añadir contexto de linaje")["run"], paso(pn, "Añadir contexto de linaje")["run"]
        py = lambda r: r[r.index("json.dump({"):r.index("}, open(")]  # noqa: E731
        self.assertEqual(py(lv), py(ln))  # mismo LINAJE.json
        r = paso(self.n["jobs"]["resolver"], "Resolver")["run"]
        rv = paso(self.v["jobs"]["resolver"], "Resolver")["run"]
        self.assertIn('python3 herramientas/p50_resolver.py plan --territorios "$TERRITORIOS" --tags tags.txt --previo "$previo" > plan.json', r)
        self.assertEqual(rv[:rv.index("python3 herramientas/p50_resolver.py plan")],
                         r[:r.index('if [[ "$ACCION"')])  # tags, última versión y MAPAS previo: igual

    def test_bash_n_y_sin_tildes_en_las_claves(self):
        for job in self.nuevo["jobs"].values():
            for s in job["steps"]:
                if "run" in s:
                    p = subprocess.run(["bash", "-n"], input=s["run"], text=True, capture_output=True)
                    self.assertEqual(p.returncode, 0, p.stderr)
        for k in on(self.nuevo)["workflow_dispatch"]["inputs"]:
            self.assertTrue(k.isascii() and k.isidentifier(), k)

    def test_huella_de_la_copia_congelada(self):
        self.assertNotEqual(hashlib.sha256(FIX.read_bytes() + b"x").hexdigest(), SHA_FIX)


if __name__ == "__main__":
    unittest.main()
