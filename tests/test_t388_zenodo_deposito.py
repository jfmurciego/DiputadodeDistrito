# -*- coding: utf-8 -*-
"""T-388 (D-146): depósito de mapas en Zenodo por API contra un servidor local SIMULADO (sin red, sin token real).

PROYECTO: Diputado de Distrito · VERSIÓN: 1.0.0 · FECHA: 2026-11-16 · ESTADO: candidato · ANTERIOR: ninguna (fichero nuevo)
"""
import hashlib
import io
import json
import subprocess
import sys
import tarfile
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import zenodo_deposito as z  # noqa: E402

TOKEN = "TOKEN-FALSO-DE-PRUEBA-123"


class Sim:
    """Estado de la API simulada de Zenodo."""

    def __init__(self):
        self.deps, self.sig = {}, 1000
        self.rechaza_tipo, self.corrompe_md5, self.log, self.fallo_subida = False, False, [], False
        self.error_put_meta, self.fallo_publish, self.sin_latest, self.fallo_delete_fichero = None, None, False, False
        self.get_5xx = 0

    def nuevo(self, concepto=None, ficheros=None):
        self.sig += 1
        d = {"id": self.sig, "state": "unsubmitted", "metadata": {}, "files": dict(ficheros or {}), "concepto": concepto}
        self.deps[d["id"]] = d
        return d


def hacer_servidor(sim: Sim):
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _base(self):
            return f"http://127.0.0.1:{self.server.server_port}"

        def _json(self, code, obj):
            b = json.dumps(obj).encode()
            self.send_response(code)
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)

        def _links(self, d):
            b, i = self._base(), d["id"]
            return {"self": f"{b}/api/deposit/depositions/{i}", "files": f"{b}/api/deposit/depositions/{i}/files",
                    "bucket": f"{b}/files/{i}", "publish": f"{b}/api/deposit/depositions/{i}/actions/publish",
                    "html": f"{b}/deposit/{i}"}

        def _vista(self, d):
            return {"id": d["id"], "state": d["state"], "metadata": d["metadata"], "links": self._links(d)}

        def _auth(self):
            if self.headers.get("Authorization") != f"Bearer {TOKEN}":
                self._json(401, {"message": f"token inválido {self.headers.get('Authorization')}"})
                return False
            return True

        def _cuerpo(self):
            return self.rfile.read(int(self.headers.get("Content-Length") or 0))

        def do_GET(self):
            if not self._auth():
                return
            sim.log.append(("GET", self.path))
            p = self.path.split("?")[0].strip("/").split("/")
            if p[:3] == ["api", "deposit", "depositions"] and len(p) == 3:
                if sim.get_5xx:
                    sim.get_5xx -= 1
                    return self._json(503, {"message": "ocupado"})
                q = dict(x.split("=") for x in self.path.split("?")[1].split("&"))
                todos = [self._vista(d) for d in sim.deps.values()]
                n, pg = int(q["size"]), int(q["page"])
                return self._json(200, todos[(pg - 1) * n: pg * n])
            d = sim.deps.get(int(p[3]))
            if len(p) == 4:
                return self._json(200, self._vista(d))
            if len(p) == 5 and p[4] == "files":
                return self._json(200, [{"id": f"f{k}", "filename": n, "checksum": "x" if sim.corrompe_md5 else m,
                                         "links": {"self": f"{self._base()}/api/deposit/depositions/{d['id']}/files/f{k}"}}
                                        for k, (n, m) in enumerate(d["files"].items())])
            self._json(404, {})

        def do_POST(self):
            if not self._auth():
                return
            sim.log.append(("POST", self.path))
            self._cuerpo()
            p = self.path.strip("/").split("/")
            if len(p) == 3:
                return self._json(201, self._vista(sim.nuevo()))
            d = sim.deps[int(p[3])]
            if p[-1] == "newversion":
                if sim.sin_latest:
                    return self._json(201, {"id": d["id"], "links": {}})
                n = sim.nuevo(concepto=d["concepto"] or "C1", ficheros={"codigo.zip": "m"})
                return self._json(201, {"links": {"latest_draft": self._links(n)["self"]}})
            if p[-1] == "publish":
                if sim.fallo_publish:
                    return self._json(sim.fallo_publish, {"message": "no se puede publicar"})
                d["state"] = "done"
                return self._json(202, {"doi": f"10.5281/zenodo.{d['id']}", "conceptdoi": "10.5281/zenodo.C1",
                                        "links": {"html": f"{self._base()}/records/{d['id']}"}})
            self._json(404, {})

        def do_PUT(self):
            if not self._auth():
                return
            sim.log.append(("PUT", self.path))
            p = self.path.strip("/").split("/")
            cuerpo = self._cuerpo()
            if p[0] == "files":
                if sim.fallo_subida:
                    return self._json(500, {"message": "boom"})
                sim.deps[int(p[1])]["files"][p[2]] = hashlib.md5(cuerpo).hexdigest()
                return self._json(201, {"key": p[2]})
            d = sim.deps[int(p[3])]
            meta = json.loads(cuerpo)["metadata"]
            if sim.error_put_meta is not None and d["concepto"]:
                return self._json(400, sim.error_put_meta)
            if sim.rechaza_tipo and d["concepto"]:
                return self._json(400, {"status": 400, "message": "Validation error.",
                                        "errors": [{"field": "metadata.upload_type", "message": "no se puede cambiar"}]})
            d["metadata"] = meta
            self._json(200, self._vista(d))

        def do_DELETE(self):
            if not self._auth():
                return
            sim.log.append(("DELETE", self.path))
            p = self.path.strip("/").split("/")
            if len(p) == 4:
                sim.deps.pop(int(p[3]))
            elif sim.fallo_delete_fichero:
                return self._json(500, {"message": "no borra"})
            else:
                d = sim.deps[int(p[3])]
                d["files"].pop(list(d["files"])[int(p[5][1:])], None)
            self._json(204, {})

    s = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s


def paquete(d: Path, t="aut01", v="1.0.0") -> Path:
    p = d / f"ddd-{t}-v{v}.tar.gz"
    with tarfile.open(p, "w:gz") as tf:
        datos = json.dumps({"territory_id": t, "version": v, "oficial": False}).encode()
        ti = tarfile.TarInfo("./LINAJE.json")
        ti.size = len(datos)
        tf.addfile(ti, io.BytesIO(datos))
    return p


class Base(unittest.TestCase):
    def setUp(self):
        self._espera, self._timeout = z._ESPERA_GET, z._TIMEOUT
        z._ESPERA_GET = (0, 0)
        self.sim = Sim()
        self.srv = hacer_servidor(self.sim)
        self.base = f"http://127.0.0.1:{self.srv.server_port}"
        self.tmp = tempfile.TemporaryDirectory()
        d = Path(self.tmp.name)
        self.rutas = [paquete(d)]
        for n, c in (("SHA256SUMS", "abc  x\n"), ("LINAJE.json", "[]"), ("LICENCIA_CC-BY-4.0.txt", "CC BY 4.0"), ("NOTA_FUENTES.md", "INE, Interior")):
            (d / n).write_text(c, encoding="utf-8")
            self.rutas.append(d / n)

    def tearDown(self):
        z._ESPERA_GET, z._TIMEOUT = self._espera, self._timeout
        self.srv.shutdown()
        self.srv.server_close()
        self.tmp.cleanup()

    def dep(self, **kw):
        a = dict(destino="prueba", token=TOKEN, version="1.0.0", tag="mapas-v1.0.0", repo="o/r", rutas=self.rutas,
                 concepto_id=None, api_base=self.base, fecha="2026-11-16")
        a.update(kw)
        return z.depositar(**a)


class Flujo(Base):
    def test_concepto_nuevo_publica_con_metadatos_y_huellas(self):
        r = self.dep()
        self.assertTrue(r["publicado"] and r["concepto_nuevo"])
        self.assertEqual(r["doi"], f"10.5281/zenodo.{r['deposito_id']}")
        m = self.sim.deps[r["deposito_id"]]["metadata"]
        self.assertEqual((m["upload_type"], m["license"], m["version"]), ("dataset", "cc-by-4.0", "1.0.0"))
        self.assertEqual(m["creators"], [{"name": "Murciego, Jesus", "affiliation": "Independent researcher", "orcid": "0009-0002-4434-959X"}])
        self.assertIn("sin valor oficial", m["description"].lower())
        rel = {x["identifier"] for x in m["related_identifiers"]}
        self.assertEqual(rel, {"https://github.com/o/r/releases/tag/mapas-v1.0.0", z.VISOR})
        self.assertEqual(set(self.sim.deps[r["deposito_id"]]["files"]), {p.name for p in self.rutas})
        esperado = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in self.rutas}
        self.assertEqual({f["nombre"]: f["sha256"] for f in r["ficheros"]}, esperado)

    def test_nueva_version_del_concepto_borra_ficheros_heredados(self):
        previo = self.sim.nuevo(concepto="C1", ficheros={"codigo.zip": "m"})
        previo["state"], previo["metadata"] = "done", {"version": "mapa-congreso_huesca-v1.0.0"}
        r = self.dep(concepto_id=str(previo["id"]))
        self.assertFalse(r["concepto_nuevo"])
        files = self.sim.deps[r["deposito_id"]]["files"]
        self.assertNotIn("codigo.zip", files)
        self.assertEqual(set(files), {p.name for p in self.rutas})

    def test_zenodo_rechaza_el_tipo_concepto_nuevo_sin_dejar_borrador_ni_duplicado(self):
        self.sim.rechaza_tipo = True
        previo = self.sim.nuevo(concepto="C1")
        previo["state"] = "done"
        avisos = []
        r = self.dep(concepto_id=str(previo["id"]), avisar=avisos.append, permitir_concepto_nuevo=True)
        self.assertTrue(r["concepto_nuevo"] and r["publicado"])
        self.assertTrue(avisos)
        borradores = [d for d in self.sim.deps.values() if d["state"] == "unsubmitted"]
        self.assertEqual(borradores, [])
        self.assertEqual(sum(1 for d in self.sim.deps.values() if d["metadata"].get("version") == "1.0.0"), 1)

    def test_cambio_de_tipo_sin_permiso_falla_cerrado_y_documenta_el_borrador(self):
        self.sim.rechaza_tipo = True
        previo = self.sim.nuevo(concepto="C1")
        previo["state"] = "done"
        with self.assertRaises(z.ErrorDeposito) as c:
            self.dep(concepto_id=str(previo["id"]))
        self.assertIn("ZENODO_CONCEPTO_NUEVO_NO_PERMITIDO", str(c.exception))
        self.assertIn("BORRADOR sin publicar", str(c.exception))
        self.assertEqual(len([d for d in self.sim.deps.values() if d["state"] == "unsubmitted"]), 1)  # solo el borrador; sin serie nueva
        self.assertFalse([x for x in self.sim.log if x[0] == "POST" and x[1] == "/api/deposit/depositions"])

    def test_otros_400_422_nunca_abren_serie_nueva_ni_con_permiso(self):
        previo = self.sim.nuevo(concepto="C1")
        previo["state"] = "done"
        for cuerpo in ({"message": "Validation error.", "errors": [{"field": "metadata.title", "message": "falta"}]},
                       {"message": "Validation error.", "errors": [{"field": "metadata.upload_type", "message": "x"},
                                                                    {"field": "metadata.license", "message": "y"}]},
                       {"message": "upload_type no se puede cambiar"}, {"errors": []}, {}):
            self.sim.error_put_meta = cuerpo
            with self.subTest(cuerpo), self.assertRaises(z.ErrorDeposito) as c:
                self.dep(concepto_id=str(previo["id"]), permitir_concepto_nuevo=True)
            self.assertIn("ZENODO_HTTP_400", str(c.exception))
            self.assertIn("BORRADOR sin publicar", str(c.exception))
        self.assertFalse([x for x in self.sim.log if x[0] == "POST" and x[1] == "/api/deposit/depositions"])

    def test_sin_publicar_deja_borrador_validado(self):
        r = self.dep(publicar=False)
        self.assertFalse(r["publicado"])
        self.assertEqual(self.sim.deps[r["deposito_id"]]["state"], "unsubmitted")
        self.assertNotIn(("POST", f"/api/deposit/depositions/{r['deposito_id']}/actions/publish"), self.sim.log)


class FalloCerrado(Base):
    def test_idempotencia_no_crea_segundo_deposito(self):
        self.dep()
        n = len(self.sim.deps)
        with self.assertRaisesRegex(z.ErrorDeposito, "ZENODO_YA_EXISTE"):
            self.dep()
        self.assertEqual(len(self.sim.deps), n)
        self.assertEqual([x for x in self.sim.log if x[0] == "POST" and x[1].endswith("depositions")].__len__(), 1)

    def test_borrador_previo_tambien_cuenta(self):
        self.dep(publicar=False)
        with self.assertRaisesRegex(z.ErrorDeposito, "ZENODO_YA_EXISTE"):
            self.dep()

    def test_huella_distinta_no_publica_y_documenta_el_borrador(self):
        self.sim.corrompe_md5 = True
        with self.assertRaises(z.ErrorDeposito) as c:
            self.dep()
        self.assertIn("ZENODO_BORRADOR_NO_VALIDA", str(c.exception))
        self.assertIn("BORRADOR sin publicar", str(c.exception))
        self.assertFalse([x for x in self.sim.log if x[1].endswith("/actions/publish")])

    def test_fallo_de_subida_sin_reintento_y_con_borrador_documentado(self):
        self.sim.fallo_subida = True
        with self.assertRaises(z.ErrorDeposito) as c:
            self.dep()
        self.assertIn("ZENODO_HTTP_500", str(c.exception))
        self.assertIn("BORRADOR", str(c.exception))
        self.assertEqual(len([x for x in self.sim.log if x[0] == "PUT" and x[1].startswith("/files/")]), 1)  # un solo intento
        self.assertFalse([x for x in self.sim.log if x[1].endswith("/actions/publish")])

    def test_red_caida_error_claro_y_token_nunca_en_el_mensaje(self):
        self.srv.shutdown()
        self.srv.server_close()
        with self.assertRaises(z.ErrorDeposito) as c:
            self.dep()
        self.assertIn("ZENODO_RED", str(c.exception))
        self.assertNotIn(TOKEN, str(c.exception))
        self.srv = hacer_servidor(Sim())  # para tearDown

    def test_token_equivocado_no_se_filtra(self):
        with self.assertRaises(z.ErrorDeposito) as c:
            self.dep(token="OTRO-TOKEN-SECRETO")
        self.assertIn("ZENODO_HTTP_401", str(c.exception))
        self.assertNotIn("OTRO-TOKEN-SECRETO", str(c.exception))

    def test_get_5xx_se_reintenta_y_acaba_bien(self):
        self.sim.get_5xx = 2
        self.assertTrue(self.dep()["publicado"])

    def test_get_5xx_persistente_falla_claro(self):
        self.sim.get_5xx = 99
        with self.assertRaisesRegex(z.ErrorDeposito, "ZENODO_HTTP_503"):
            self.dep()
        self.assertEqual(self.sim.deps, {})

    def test_publish_con_5xx_y_4xx_no_reintenta_y_documenta_el_borrador(self):
        for codigo, v in ((500, "1.0.0"), (400, "1.1.0")):
            self.sim.fallo_publish = codigo
            with self.subTest(codigo), self.assertRaises(z.ErrorDeposito) as c:
                self.dep(version=v, tag=f"mapas-v{v}")
            self.assertIn(f"ZENODO_HTTP_{codigo}", str(c.exception))
            self.assertIn("BORRADOR sin publicar", str(c.exception))
        self.assertEqual(len([x for x in self.sim.log if x[1].endswith("/actions/publish")]), 2)  # uno por intento, sin reintentos

    def test_newversion_sin_latest_draft_falla_cerrado_con_aviso(self):
        self.sim.sin_latest = True
        previo = self.sim.nuevo(concepto="C1")
        previo["state"] = "done"
        with self.assertRaisesRegex(z.ErrorDeposito, f"ZENODO_NEWVERSION_INESPERADA.*{previo['id']}"):
            self.dep(concepto_id=str(previo["id"]))

    def test_fallo_al_borrar_fichero_heredado_documenta_el_borrador(self):
        self.sim.fallo_delete_fichero = True
        previo = self.sim.nuevo(concepto="C1", ficheros={"codigo.zip": "m"})
        previo["state"] = "done"
        with self.assertRaises(z.ErrorDeposito) as c:
            self.dep(concepto_id=str(previo["id"]))
        self.assertIn("ZENODO_HTTP_500", str(c.exception))
        self.assertIn("BORRADOR sin publicar", str(c.exception))
        self.assertFalse([x for x in self.sim.log if x[1].endswith("/actions/publish")])

    def test_timeout_error_claro(self):
        import socket
        z._TIMEOUT = 0.3
        sock = socket.socket()
        sock.bind(("127.0.0.1", 0))
        sock.listen(5)  # acepta conexiones y nunca responde
        try:
            with self.assertRaisesRegex(z.ErrorDeposito, "ZENODO_RED"):
                self.dep(api_base=f"http://127.0.0.1:{sock.getsockname()[1]}")
        finally:
            sock.close()

    def test_paginacion_de_100_encuentra_el_deposito_de_la_segunda_pagina(self):
        for i in range(120):
            self.sim.nuevo()
        ya = self.sim.nuevo()
        ya["metadata"] = {"version": "1.0.0", "title": z.TITULO + "1.0.0"}
        with self.assertRaisesRegex(z.ErrorDeposito, "ZENODO_YA_EXISTE"):
            self.dep()

    def test_registro_historico_con_otro_titulo_no_bloquea(self):
        h = self.sim.nuevo(concepto="C1")
        h["state"], h["metadata"] = "done", {"version": "1.0.0", "title": "Diputado de Distrito: motor reproducible"}
        self.assertTrue(self.dep()["publicado"])

    def test_entradas_invalidas(self):
        for kw, msg in (({"token": ""}, "ZENODO_SIN_TOKEN"), ({"destino": "otro"}, "ZENODO_DESTINO_INVALIDO"),
                        ({"tag": "mapas-v9.9.9"}, "ZENODO_VERSION_INVALIDA"), ({"version": "1.0"}, "ZENODO_VERSION_INVALIDA"),
                        ({"repo": "o/r;x"}, "ZENODO_REPO_INVALIDO"), ({"api_base": "https://evil.example"}, "ZENODO_API_BASE_NO_LOCAL")):
            with self.subTest(kw), self.assertRaisesRegex(z.ErrorDeposito, msg):
                self.dep(**kw)
        self.assertEqual(self.sim.deps, {})  # nada creado

    def test_sin_codigo_ni_ficheros_ajenos(self):
        d = Path(self.tmp.name)
        for n in ("motor.py", "codigo.zip", "fuente.tar.gz"):
            (d / n).write_text("x")
            with self.subTest(n), self.assertRaisesRegex(z.ErrorDeposito, "ZENODO_FICHERO_NO_PERMITIDO"):
                self.dep(rutas=self.rutas + [d / n])
        with self.assertRaisesRegex(z.ErrorDeposito, "ZENODO_FALTAN_FICHEROS"):
            self.dep(rutas=[p for p in self.rutas if p.name != "NOTA_FUENTES.md"])
        with self.assertRaisesRegex(z.ErrorDeposito, "ZENODO_SIN_PAQUETE"):
            self.dep(rutas=self.rutas[1:])
        with self.assertRaisesRegex(z.ErrorDeposito, "ZENODO_FICHERO_AUSENTE"):
            self.dep(rutas=self.rutas + [d / "no_existe.tar.gz"])
        self.assertEqual(self.sim.deps, {})

    def test_enlace_de_otro_servidor_no_recibe_el_token(self):
        c = z.Cliente(self.base, TOKEN)
        with self.assertRaisesRegex(z.ErrorDeposito, "ZENODO_URL_AJENA"):
            c.get("https://otro.example/api/x")


class Workflow(unittest.TestCase):
    def setUp(self):
        import yaml
        self.txt = (ROOT / ".github/workflows/p50-publicacion-academica.yml").read_text(encoding="utf-8")
        self.w = yaml.safe_load(self.txt)

    def test_un_paso_por_destino_sin_respaldo_cruzado(self):
        pasos = {s.get("name", ""): s for s in self.w["jobs"]["zenodo"]["steps"] if "Depositar" in s.get("name", "")}
        self.assertEqual(len(pasos), 2)
        p, r = pasos["Depositar en Zenodo (prueba)"], pasos["Depositar en Zenodo (real)"]
        self.assertEqual(p["env"]["ZENODO_TOKEN"], "${{ secrets.ZENODO_SANDBOX_TOKEN }}")
        self.assertEqual(r["env"]["ZENODO_TOKEN"], "${{ secrets.ZENODO_TOKEN }}")
        self.assertIn("'prueba'", p["if"])
        self.assertIn("'Zenodo'", r["if"])
        for linea in self.txt.splitlines():
            if "secrets." in linea and not linea.lstrip().startswith("#"):
                self.assertNotIn("||", linea)
                self.assertNotIn("&&", linea)

    def test_secretos_solo_en_los_pasos_de_deposito(self):
        j = self.w["jobs"]["zenodo"]
        self.assertNotIn("secrets.", json.dumps({k: v for k, v in j.items() if k != "steps"}))
        for s in j["steps"]:
            if "Depositar" not in s.get("name", ""):
                self.assertNotIn("secrets.", json.dumps(s))
        self.assertEqual(j["permissions"], {"contents": "read"})
        self.assertEqual(j["environment"], "publicacion")

    def test_concepto_nuevo_desmarcado_por_defecto_y_solo_en_el_real(self):
        e = (self.w.get("on") or self.w.get(True))["workflow_dispatch"]["inputs"]
        self.assertEqual((e["concepto_nuevo"]["type"], e["concepto_nuevo"]["default"]), ("boolean", False))
        self.assertEqual(e["destino"]["default"], "prueba")
        self.assertEqual(e["destino"]["options"], ["prueba", "Zenodo"])
        pasos = {s.get("name", ""): s for s in self.w["jobs"]["zenodo"]["steps"]}
        self.assertNotIn("permitir-concepto-nuevo", pasos["Depositar en Zenodo (prueba)"]["run"])
        self.assertIn("permitir-concepto-nuevo", pasos["Depositar en Zenodo (real)"]["run"])

    def test_bash_n_de_los_pasos(self):
        for s in self.w["jobs"]["zenodo"]["steps"]:
            if "run" in s:
                r = subprocess.run(["bash", "-n"], input=s["run"], text=True, capture_output=True)
                self.assertEqual(r.returncode, 0, r.stderr)


class Herramienta(Base):
    def test_linaje_une_los_de_cada_paquete(self):
        d = Path(self.tmp.name)
        paquete(d, "aut02")
        out = d / "L.json"
        self.assertEqual(z.main(["linaje", "--dir", str(d), "--salida", str(out)]), 0)
        self.assertEqual([x["territory_id"] for x in json.loads(out.read_text())], ["aut01", "aut02"])

    def test_cli_help_y_error_a_stderr(self):
        h = subprocess.run([sys.executable, str(ROOT / "herramientas" / "zenodo_deposito.py"), "--help"], capture_output=True, text=True)
        self.assertEqual(h.returncode, 0)
        p = subprocess.run([sys.executable, str(ROOT / "herramientas" / "zenodo_deposito.py"), "depositar", "--destino", "prueba",
                            "--version", "1.0.0", "--tag", "mapas-v1.0.0", "--repo", "o/r", "--ficheros", "/no/existe"],
                           capture_output=True, text=True, env={"PATH": "/usr/bin:/bin"})
        self.assertEqual((p.returncode, p.stdout), (1, ""))
        self.assertIn("ZENODO_SIN_TOKEN", p.stderr)
        h2 = subprocess.run([sys.executable, str(ROOT / "herramientas" / "zenodo_deposito.py"), "depositar", "--help"], capture_output=True, text=True)
        self.assertIn("--permitir-concepto-nuevo", h2.stdout)

    def test_destinos_y_url_reales(self):
        self.assertEqual(z.BASES, {"prueba": "https://sandbox.zenodo.org", "Zenodo": "https://zenodo.org"})


if __name__ == "__main__":
    unittest.main()
