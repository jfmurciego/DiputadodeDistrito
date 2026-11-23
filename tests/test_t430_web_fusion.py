"""T-430 paso 3c (D-194, P7): `herramientas/web_fusion_r2.py` monta el sitio de R2 vigente con la V4 de `main` (sin datos ni P40) y
`publicar_sitio_r2.py` lo publica; el job `publicar_web` de P90 solo corre en push a main de una fusión solo de la web."""
import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

from herramientas import publicar_sitio_r2 as s
from herramientas import web_fusion_r2 as w
from herramientas.publicar_datos_web import DatosWebError

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / ".github" / "workflows" / "p90-automatico.yml"
PORTADA = b"<html><head><title>Diputado de Distrito | Portada</title></head>"

# Sitio publicado por P40 (sin datos): la V4 en la raiz y redirecciones en v4/, lo demas de otras versiones.
SITIO = {"index.html": PORTADA + b"vieja", "comprender.html": b"<html>c", "app.js": b"1", "styles.css": b"a{}", "viejo.html": b"<html>v",
         "mapa/index.html": b"<html>m", "mapa/explorar.js": b"2", "v4/index.html": b"r", "v4/viejo.html": b"r",
         "v1/index.html": b'<html><base href="../"><script src="v1/app.js">', "v1/app.js": b"v1", "v2/index.html": b"<html>v2", "v2/vendor/maplibre.js": b"m",
         "v3/index.html": b"<html>v3", "docs/index.html": b"<html>d", "dashboard/index.html": b"<html>db", "robots.txt": b"x"}
# V4 de main tras la fusion: cambia la portada, quita viejo.html, anade nueva.html; lo de NO_PUBLICAR no sale.
V4 = {"index.html": PORTADA + b"nueva", "comprender.html": b"<html>c", "app.js": b"1", "styles.css": b"a{}", "nueva.html": b"<html>n",
      "mapa/index.html": b"<html>m", "mapa/explorar.js": b"2", "cabecera.html": b"interno",
      "NO_PUBLICAR.txt": b"# comentario\nNO_PUBLICAR.txt\ncabecera.html\n"}


PREVIOS = {"index.html", "viejo.html", "mapa", "app.js", "styles.css", "comprender.html", "NO_PUBLICAR.txt", "cabecera.html"}


class R2Falso:
    def __init__(self, obj):
        self.obj, self.escritos, self.borrados = dict(obj), [], []

    def leer(self, clave):
        return self.obj.get(clave)

    def bajar(self, destino):
        for k, b in self.obj.items():
            if not k.startswith("_sitio/"):
                (destino / k).parent.mkdir(parents=True, exist_ok=True)
                (destino / k).write_bytes(b)

    def escribir(self, clave, origen, cache):
        self.obj[clave] = Path(origen).read_bytes()
        self.escritos.append(clave)

    def borrar(self, clave):
        self.borrados.append(clave)
        self.obj.pop(clave, None)


def bucket(sitio, extra=None):
    obj = dict(sitio)
    obj["_sitio/actual.json"] = json.dumps({"ficheros": {k: hashlib.sha256(b).hexdigest() for k, b in sitio.items()}}).encode()
    obj.update(extra or {})
    return R2Falso(obj)


class Montaje(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.raiz = Path(self.t.name) / "repo"
        for r, b in V4.items():
            p = self.raiz / "visor" / "v4" / r
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(b)
        self.dest = Path(self.t.name) / "sitio"

    def tearDown(self):
        self.t.cleanup()

    def test_sustituye_la_v4_y_conserva_lo_demas(self):
        r2 = bucket(SITIO, {"huerfano.html": b"x"})  # en el bucket pero no en el indice: no entra
        w.montar(self.dest, r2, self.raiz, PREVIOS)
        hay = {p.relative_to(self.dest).as_posix() for p in self.dest.rglob("*") if p.is_file()}
        self.assertEqual(hay, {"index.html", "comprender.html", "app.js", "styles.css", "nueva.html", "mapa/index.html", "mapa/explorar.js",
                               "v4/index.html", "v4/comprender.html", "v4/nueva.html", "v4/mapa/index.html",
                               "v1/index.html", "v1/app.js", "v2/index.html", "v2/vendor/maplibre.js", "v3/index.html", "docs/index.html",
                               "dashboard/index.html", "robots.txt"})
        self.assertEqual((self.dest / "index.html").read_bytes(), PORTADA + b"nueva")
        self.assertIn('url=../../mapa/"', (self.dest / "v4/mapa/index.html").read_text())
        # y el publicador sube solo lo cambiado y borra lo que salio, con su indice al final
        s.publicar(self.dest, r2, "9")
        self.assertEqual(sorted(r2.borrados), ["v4/viejo.html", "viejo.html"])
        self.assertEqual(r2.escritos[-1], "_sitio/actual.json")
        self.assertEqual(set(r2.escritos[:-1]), {"index.html", "nueva.html", "v4/index.html", "v4/comprender.html", "v4/nueva.html",
                                                 "v4/mapa/index.html"})

    def test_sin_indice_no_monta_nada(self):
        self.assertEqual(w.montar(self.dest, R2Falso({}), self.raiz), 0)
        self.assertFalse(self.dest.exists())

    def test_sitio_que_no_casa_con_su_indice_aborta(self):
        r2 = bucket(SITIO)
        r2.obj["v2/index.html"] = b"alterado"
        with self.assertRaisesRegex(DatosWebError, "SITIO_R2_NO_CASA"):
            w.montar(self.dest, r2, self.raiz, PREVIOS)

    def test_nombre_de_la_v4_que_pisaria_el_sitio_aborta(self):
        for previos, fichero in (({"docs"}, None), (set(), "v2/x.js")):
            with self.subTest(previos=previos, fichero=fichero):
                if fichero:
                    (self.raiz / "visor/v4" / fichero).parent.mkdir(parents=True, exist_ok=True)
                    (self.raiz / "visor/v4" / fichero).write_text("x")
                with self.assertRaisesRegex(DatosWebError, "V4_PISA_EL_SITIO"):
                    w.montar(self.dest, bucket(SITIO), self.raiz, previos)

    def test_nombre_nuevo_de_la_v4_que_ya_esta_en_el_sitio_aborta(self):
        # guarda de choques de preparar_portada_v4.py: robots.txt es del sitio, no de la V4; un robots.txt nuevo en la V4 no lo machaca
        (self.raiz / "visor/v4/robots.txt").write_text("nuevo")
        with self.assertRaisesRegex(DatosWebError, "V4_PISA_EL_SITIO: robots.txt"):
            w.montar(self.dest, bucket(SITIO), self.raiz, PREVIOS)
        self.assertFalse(self.dest.exists())

    def test_sin_previos_todo_es_nuevo_y_no_se_publica(self):
        with self.assertRaisesRegex(DatosWebError, "V4_PISA_EL_SITIO: comprender.html, mapa"):
            w.montar(self.dest, bucket(SITIO), self.raiz, set())

    def test_enlace_simbolico_en_la_v4_aborta(self):
        (self.raiz / "visor/v4/secreto.txt").symlink_to("/etc/hostname")
        with self.assertRaisesRegex(DatosWebError, "V4_CON_ENLACE: visor/v4/secreto.txt"):
            w.montar(self.dest, bucket(SITIO), self.raiz, PREVIOS)

    def test_sitio_sin_otras_versiones_no_se_publica(self):
        sitio = {k: v for k, v in SITIO.items() if not k.startswith("v3/")}
        with self.assertRaisesRegex(DatosWebError, "SITIO_INCOMPLETO: faltan v3/index.html"):
            w.montar(self.dest, bucket(sitio), self.raiz, PREVIOS)

    def test_main_inerte_sin_bucket(self):
        self.assertEqual(w.main(["--destino", str(self.dest), "--bucket", ""]), 0)
        self.assertFalse(self.dest.exists())


def paso_cambios():
    return next(x for x in yaml.safe_load(WF.read_text(encoding="utf-8"))["jobs"]["cambios"]["steps"] if x.get("id") == "f")


class JobPublicarWeb(unittest.TestCase):
    def clasificar(self, evento, ficheros):
        paso = paso_cambios()
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            run = lambda *a: subprocess.run(a, cwd=repo, check=True, capture_output=True, text=True)
            run("git", "init", "-q"); run("git", "config", "user.email", "a@b"); run("git", "config", "user.name", "a")
            (repo / "base.txt").write_text("0"); run("git", "add", "-A"); run("git", "commit", "-qm", "0")
            for f in ficheros:
                p = repo / f; p.parent.mkdir(parents=True, exist_ok=True); p.write_text("1")
            run("git", "add", "-A"); run("git", "commit", "-qm", "1", "--allow-empty")
            out = repo / "salida.txt"; out.write_text("")
            env = {**{k: str(v) for k, v in (paso.get("env") or {}).items() if "${{" not in str(v)}, "PATH": "/usr/bin:/bin",
                   "EVENTO": evento, "ACTOR": "persona", "BASE": "HEAD~1", "GITHUB_SHA": "HEAD", "GITHUB_OUTPUT": str(out)}
            r = subprocess.run(["bash", "-eo", "pipefail", "-c", paso["run"]], cwd=repo, env=env, capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            return dict(l.split("=", 1) for l in out.read_text().splitlines() if "=" in l)

    def test_publicar_web_solo_en_push_solo_de_la_web(self):
        for ficheros in (["visor/v4/index.html"], ["visor/v4/mapa/explorar.js", "tests/test_visor_v4_mapa.py", "docs/registro/2026-11-23_x.md"]):
            c = self.clasificar("push", ficheros)
            self.assertEqual((c["publicar_web"], c["web"]), ("true", "false"), ficheros)  # en main, batería completa igualmente
        for nombre, (evento, ficheros) in {
            "PR solo web": ("pull_request", ["visor/v4/index.html"]),
            "web + código": ("push", ["visor/v4/index.html", "herramientas/x.py"]),
            "web + workflow": ("push", ["visor/v4/index.html", ".github/workflows/p90-automatico.yml"]),
            "solo registro": ("push", ["docs/registro/2026-11-23_x.md"]),
            "visor v3": ("push", ["visor/v3/v3.js"]),
        }.items():
            with self.subTest(nombre):
                self.assertEqual(self.clasificar(evento, ficheros)["publicar_web"], "false")

    def test_job_solo_main_sin_escritura_y_serializado_con_p40(self):
        j = yaml.safe_load(WF.read_text(encoding="utf-8"))["jobs"]["publicar_web"]
        self.assertEqual(j["needs"], ["cambios", "guardian", "suite"])
        self.assertEqual(j["if"], "${{ !cancelled() && github.event_name == 'push' && github.ref == 'refs/heads/main' && needs.cambios.outputs.publicar_web == 'true'"
                                  " && needs.guardian.result == 'success' && needs.suite.result == 'success' }}")
        self.assertEqual(j["permissions"], {"contents": "read"})
        self.assertEqual(j["concurrency"], {"group": "ddd-pages-prod", "cancel-in-progress": False, "queue": "max"})  # mismo grupo que P40 `publicar`
        p40 = yaml.safe_load((ROOT / ".github/workflows/p40-publicacion.yml").read_text(encoding="utf-8"))["jobs"]["publicar"]["concurrency"]
        self.assertEqual(p40["group"], j["concurrency"]["group"])
        self.assertFalse(any(s.get("with", {}).get("persist-credentials", False) for s in j["steps"] if "uses" in s))
        paso = j["steps"][-1]
        self.assertTrue(paso["env"]["AWS_ACCESS_KEY_ID"].startswith("${{ secrets.R2_SITIO_"))
        self.assertIn('if [[ -z "${R2_SITIO_BUCKET:-}" ]]', paso["run"])
        self.assertIn("herramientas/web_fusion_r2.py", paso["run"])
        self.assertIn("herramientas/publicar_sitio_r2.py", paso["run"])
        self.assertNotIn("--permitir-borrado", paso["run"])
        self.assertIn("node --check", paso["run"])
        # orden: la comprobación de una V4 posterior en main va justo antes de publicar
        self.assertLess(paso["run"].index("compare/$GITHUB_SHA...main"), paso["run"].index("publicar_sitio_r2.py"))
        self.assertNotIn("publicar_web", yaml.safe_load(WF.read_text(encoding="utf-8"))["jobs"]["pruebas"]["needs"])
        subprocess.run(["bash", "-n"], input=paso["run"], text=True, check=True)

    def test_push_con_la_v4_y_otros_ficheros_avisa(self):
        # menor (b) del revisor de #989: la web en R2 se queda atrás hasta la siguiente P40, con aviso visible
        paso = paso_cambios()
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            run = lambda *a: subprocess.run(a, cwd=repo, check=True, capture_output=True, text=True)
            run("git", "init", "-q"); run("git", "config", "user.email", "a@b"); run("git", "config", "user.name", "a")
            (repo / "base.txt").write_text("0"); run("git", "add", "-A"); run("git", "commit", "-qm", "0")
            for f in ("visor/v4/index.html", "herramientas/x.py"):
                (repo / f).parent.mkdir(parents=True, exist_ok=True); (repo / f).write_text("1")
            run("git", "add", "-A"); run("git", "commit", "-qm", "1")
            out = repo / "salida.txt"; out.write_text("")
            env = {**{k: str(v) for k, v in (paso.get("env") or {}).items() if "${{" not in str(v)}, "PATH": "/usr/bin:/bin",
                   "EVENTO": "push", "ACTOR": "persona", "BASE": "HEAD~1", "GITHUB_SHA": "HEAD", "GITHUB_OUTPUT": str(out)}
            r = subprocess.run(["bash", "-eo", "pipefail", "-c", paso["run"]], cwd=repo, env=env, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("publicar_web=false", r.stdout)
        self.assertIn("::warning::El push toca visor/v4/ junto con otros ficheros", r.stdout)

    def test_orden_no_depende_de_la_lista_de_compare(self):
        # menor (a) del revisor de #989: `compare` lista como mucho 300 ficheros
        import re as _re
        paso = yaml.safe_load(WF.read_text(encoding="utf-8"))["jobs"]["publicar_web"]["steps"][-1]["run"]
        filtro = _re.search(r"compare/\$GITHUB_SHA\.\.\.main\" --jq '([^']+)'", paso).group(1)
        casos = {
            "igual a main": ({"ahead_by": 0, "files": []}, "0"),
            "robot posterior": ({"ahead_by": 1, "files": [{"filename": "docs/REGISTRO_DE_CAMBIOS.md"}]}, "0"),
            "V4 posterior": ({"ahead_by": 2, "files": [{"filename": "visor/v4/index.html"}, {"filename": "docs/x.md"}]}, "1"),
            "300 ficheros sin V4 en la lista": ({"ahead_by": 40, "files": [{"filename": f"datos/{i}.json"} for i in range(300)]}, "muchos"),
        }
        for nombre, (entrada, esperado) in casos.items():
            with self.subTest(nombre):
                r = subprocess.run(["jq", "-r", filtro], input=json.dumps(entrada), capture_output=True, text=True, check=True)
                self.assertEqual(r.stdout.strip(), esperado)

    def test_push_de_varios_commits_o_sin_before_no_publica(self):
        paso = yaml.safe_load(WF.read_text(encoding="utf-8"))["jobs"]["publicar_web"]["steps"][-1]
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            run = lambda *a: subprocess.run(a, cwd=repo, check=True, capture_output=True, text=True).stdout.strip()
            run("git", "init", "-q"); run("git", "config", "user.email", "a@b"); run("git", "config", "user.name", "a")
            for i in range(3):
                run("git", "commit", "-q", "--allow-empty", "-m", str(i))
            abuelo = run("git", "rev-parse", "HEAD~2")
            for antes in ("", "0" * 40, abuelo):
                with self.subTest(antes=antes):
                    r = subprocess.run(["bash", "-eo", "pipefail", "-c", paso["run"]], cwd=repo, capture_output=True, text=True,
                                       env={"PATH": "/usr/bin:/bin", "R2_SITIO_BUCKET": "ddd-web-sitio", "ANTES": antes, "RUNNER_TEMP": raw})
                    self.assertEqual(r.returncode, 0, r.stderr)
                    self.assertIn("no se publica la web", r.stdout)
                    self.assertFalse((repo / "sitio-web").exists())

    def test_paso_inerte_sin_bucket_bajo_pipefail(self):
        paso = yaml.safe_load(WF.read_text(encoding="utf-8"))["jobs"]["publicar_web"]["steps"][-1]
        r = subprocess.run(["bash", "-eo", "pipefail", "-c", paso["run"]], cwd=ROOT, env={"PATH": "/usr/bin:/bin", "R2_SITIO_BUCKET": ""},
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Sin R2_SITIO_BUCKET", r.stdout)


if __name__ == "__main__":
    unittest.main()
