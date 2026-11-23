"""
PROYECTO: Diputado de Distrito
PRUEBA: archivista R2 (T-47) con catálogo sintético y R2 simulado
VERSIÓN: 1.1.0
FECHA: 2026-11-07
CAMBIOS: 1.1.0 (T-72): solo productos finales M06/M08 y auditorías; M06 omitido si vive su M08.
ANTERIOR: ninguna (fichero nuevo; 1.0.0 sin copia en legacy)
"""
import importlib.util
import json
import tempfile
import unittest
import urllib.error
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("arc", ROOT / "herramientas/archivar_artefactos_r2.py")
arc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(arc)


def art(i, nombre, expira, expired=False):
    return {"id": i, "name": nombre, "expired": expired, "expires_at": expira, "size_in_bytes": 3,
            "workflow_run": {"id": int(nombre.split("-")[2]) if nombre.split("-")[2].isdigit() else 0}}


class R2Falso:
    def __init__(self):
        self.objs = {}
        self.runs = {}
        self.condiciones = []
        self.subidas = 0

    def sha(self, k):
        return self.objs.get(k)

    def subir(self, k, ruta, h, run=None, condicion=None):
        if condicion == "*" and k in self.objs:
            raise RuntimeError("R2_ESCRITURA_CONCURRENTE")
        if condicion not in (None, "*") and condicion != self.etag(k):
            raise RuntimeError("R2_ESCRITURA_CONCURRENTE")
        self.subidas += 1
        self.objs[k] = h
        self.runs[k] = run
        self.condiciones.append(condicion)

    def etag(self, k):
        return f'"{self.objs[k][:8]}-{self.runs.get(k)}"' if k in self.objs else None

    def cab(self, k):
        return {"sha256": self.objs[k], "run": self.runs.get(k), "bytes": 3, "etag": self.etag(k)} if k in self.objs else None


class Archivista(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = Path(self.td.name)
        (self.root / "orchestracion").mkdir()
        (self.root / arc.CATALOGO).write_text(json.dumps({"t": {"cantabria": {
            "territory_id": "cantabria",
            "x": {"artifact_name": "ddd-state-41037133327-M06"},
            "y": {"artifact_name": "ddd-audit-41037133327"}}}}))
        (self.root / arc.VISOR).write_text(json.dumps({"products": [
            {"id": "m", "run_id": "41037133327", "territory_id": "cantabria"},
            {"id": "s", "territory_id": "aragon"}]}))
        self.vivos = [
            art(2, "ddd-state-41037133327-M06", "2026-11-20T00:00:00Z"),
            art(1, "ddd-state-41037133327-M05", "2026-11-13T00:00:00Z"),
            art(3, "ddd-audit-41037133327", "2026-11-15T00:00:00Z"),
            art(4, "ddd-state-99999999999-M05", "2026-11-12T00:00:00Z"),  # no referenciado
            art(5, "ddd-state-41037133327-M08", "2026-11-01T00:00:00Z", expired=True),
        ]
        self.r2 = R2Falso()
        self.man = {"artefactos": {}}

    def tearDown(self):
        self.td.cleanup()

    def correr(self, **kw):
        n, r = arc.referencias(self.root)
        return arc.archivar(self.vivos, n, r, self.man, lambda a, p: p.write_bytes(b"zip" + str(a["id"]).encode()),
                            self.r2.sha, self.r2.subir, "bkt", ahora=lambda: "2026-11-07T00:00:00Z", **kw)

    def test_referencias_y_prioridad(self):
        n, r = arc.referencias(self.root)
        sel = arc.seleccionar(self.vivos, n, r)
        self.assertEqual([a["name"] for a in sel],
                         ["ddd-audit-41037133327", "ddd-state-41037133327-M06"])  # sin M05 (T-72)
        self.assertEqual(arc.clave(sel[1]), "cantabria/41037133327/ddd-state-41037133327-M06.zip")

    def test_archiva_y_manifiesto(self):
        res = self.correr()
        self.assertEqual(len(res["archivados"]), 2)
        e = self.man["artefactos"]["cantabria/41037133327/ddd-state-41037133327-M06.zip"]
        self.assertEqual(e["url"], "r2://bkt/cantabria/41037133327/ddd-state-41037133327-M06.zip")
        self.assertEqual(e["caducidad_original"], "2026-11-20T00:00:00Z")
        self.assertEqual(len(e["sha256"]), 64)
        self.assertEqual(e["tamano_bytes"], 4)
        # T-443: la auditoría va al árbol nuevo (sin run en la ruta) con el manifiesto de su carpeta; el estado completo, a la clave vieja
        self.assertIn("interno/estados/autonomicas/cantabria/ultimo/audit.zip", self.man["artefactos"])
        self.assertEqual(self.man["artefactos"]["interno/estados/autonomicas/cantabria/ultimo/audit.zip"]["run_id"], "41037133327")
        self.assertEqual(res["manifiestos"], ["interno/estados/autonomicas/cantabria/ultimo/manifiesto.json"])
        objs = {k: v for k, v in self.r2.objs.items() if not k.endswith("/manifiesto.json")}
        self.assertEqual(set(objs.values()), {x['sha256'] for x in self.man['artefactos'].values()})

    def test_idempotente(self):
        self.correr()
        res = self.correr()
        self.assertEqual(self.r2.subidas, 3)  # 2 objetos + manifiesto.json (T-443); el segundo pase no resube nada
        self.assertEqual(len(res["ya_archivados"]), 2)
        self.assertEqual(res["archivados"], [])

    def test_no_resube_mismo_sha(self):
        self.correr()
        self.man["artefactos"].clear()  # manifiesto perdido, R2 conserva los objetos
        res = self.correr()
        self.assertEqual(self.r2.subidas, 3)  # el manifiesto reconstruido es idéntico: no se resube
        self.assertEqual(len(res["sin_cambios_r2"]), 2)

    def test_caduca_antes_y_maximo(self):
        res = self.correr(caduca_antes="2026-11-16")
        self.assertEqual(len(res["archivados"]), 1)
        res = self.correr(maximo=1)
        self.assertEqual(len(res["archivados"]), 1)

    def test_error_no_registra_y_perdidos(self):
        n, r = arc.referencias(self.root)
        n["ddd-state-41037133327-M04"] = "cantabria"
        n["ddd-state-41037133328-M06"] = "cantabria"

        def falla(a, p):
            raise RuntimeError("red")

        res = arc.archivar(self.vivos, n, r, self.man, falla, self.r2.sha, self.r2.subir, "bkt")
        self.assertEqual(len(res["errores"]), 2)
        self.assertEqual(self.man["artefactos"], {})
        self.assertIn("ddd-state-41037133328-M06", res["perdidos"])
        self.assertNotIn("ddd-state-41037133327-M04", res["perdidos"])  # intermedio: no se archiva

    def test_m06_omitido_si_vive_su_m08(self):
        self.vivos[4] = art(5, "ddd-state-41037133327-M08", "2026-11-21T00:00:00Z")
        n, r = arc.referencias(self.root)
        self.assertEqual([a["name"] for a in arc.seleccionar(self.vivos, n, r)],
                         ["ddd-audit-41037133327", "ddd-state-41037133327-M08"])
        self.assertTrue(arc.cubierto_por_m08("ddd-state-41037133327-M06",
                                             {"k": {"artefacto": "ddd-state-41037133327-M08"}}))
        self.assertTrue(arc.cubierto_por_m08("ddd-state-1111111111-M06",
                                             {"k": {"artefacto": "ddd-state-41037133327-M08", "incluye_m06_run": "1111111111"}}))

    def test_guardar_manifiesto_solo_si_cambia(self):
        ruta = self.root / arc.MANIFIESTO
        self.correr()
        self.assertTrue(arc.guardar_manifiesto(ruta, self.man))
        self.man["actualizado_en"] = "otra"
        self.assertFalse(arc.guardar_manifiesto(ruta, self.man))


def estado_zip(ruta, n_secciones=2500):
    import zipfile
    dist = {"features": [{"properties": {"district_id": 0}}, {"properties": {"district_id": 1}}]}
    secc = {"features": [{"properties": {"CUSEC": i}} for i in range(n_secciones)]}
    with zipfile.ZipFile(ruta, "w") as z:
        z.writestr("cache/.cache/t_m06_distritos.geojson", json.dumps(dist))
        z.writestr("cache/t_m06_secciones.geojson", json.dumps(secc))
        z.writestr("cache/t_m06_composicion_distritos.csv", "CUSEC_KEY,district_id,section_pop\n1,0,5\n")
        z.writestr("cache/t_m05_informe.json", "{}")
        z.writestr("run/CHAIN_STATE.json", "{}")
        z.writestr("sources/paquete.zip", b"x" * 1000)
    return ruta


class PaqueteMinimo(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.d = Path(self.td.name)
        estado_zip(self.d / "e.zip")
        (self.d / "audit").mkdir()
        (self.d / "audit/production_status.json").write_text('{"decision":"PASS"}')
        self.a = {"id": 7, "name": "ddd-state-41037133327-M06", "run": "41037133327"}

    def tearDown(self):
        self.td.cleanup()

    def paquete(self, sub):
        import zipfile
        (self.d / sub).mkdir()
        z = arc.empaquetar_minimo((self.d / "audit",))(self.a, self.d / "e.zip", self.d / sub)
        return z, zipfile.ZipFile(z)

    def test_seleccion_y_manifiesto(self):
        z, zf = self.paquete("p1")
        self.assertEqual(z.name, "ddd-minimo-41037133327-M06.zip")
        self.assertEqual(sorted(zf.namelist()), [
            "MANIFEST_MINIMO.json", "estado/cache/.cache/t_m06_distritos.geojson",
            "estado/cache/t_m06_composicion_distritos.csv", "estado/run/CHAIN_STATE.json",
            "extra/audit/production_status.json"])
        man = json.loads(zf.read("MANIFEST_MINIMO.json"))
        self.assertEqual(man["sha256_estado_original"], arc.sha256_fichero(self.d / "e.zip"))
        self.assertEqual(man["ficheros"]["estado/run/CHAIN_STATE.json"], arc.hashlib.sha256(b"{}").hexdigest())

    def test_secciones_pequenas_excluidas(self):
        estado_zip(self.d / "e.zip", n_secciones=50)
        _, zf = self.paquete("p1")
        self.assertNotIn("estado/cache/t_m06_secciones.geojson", zf.namelist())

    def test_determinista(self):
        z1, _ = self.paquete("p1")
        z2, _ = self.paquete("p2")
        self.assertEqual(arc.sha256_fichero(z1), arc.sha256_fichero(z2))

    def test_sin_geojson_distrital_falla(self):
        import zipfile
        with zipfile.ZipFile(self.d / "e2.zip", "w") as z:
            z.writestr("cache/t_m06_secciones.geojson", json.dumps({"features": [{}] * 2500}))
        (self.d / "p").mkdir()
        with self.assertRaises(ValueError):
            arc.empaquetar_minimo()(self.a, self.d / "e2.zip", self.d / "p")

    def test_geojson_zip_del_estado_real(self):
        """T-90: los módulos escriben *.geojson.zip (sin .geojson suelto); el M08 de Barcelona falló así."""
        import io
        import zipfile

        def gz(nombre, gj):
            b = io.BytesIO()
            with zipfile.ZipFile(b, "w") as z:
                z.writestr(nombre, json.dumps(gj))
            return b.getvalue()
        dist = {"features": [{"properties": {"district_id": 0, "winner_party": "PP"}}]}
        secc = {"features": [{"properties": {"CUSEC": i}} for i in range(3)]}
        with zipfile.ZipFile(self.d / "e3.zip", "w") as z:
            z.writestr("cache/t_m08_distritos_resultados.geojson.zip", gz("t_m08_distritos_resultados.geojson", dist))
            z.writestr("cache/t_m06_secciones.geojson.zip", gz("t_m06_secciones.geojson", secc))
        (self.d / "p").mkdir()
        zf = zipfile.ZipFile(arc.empaquetar_minimo()(self.a, self.d / "e3.zip", self.d / "p"))
        self.assertIn("estado/cache/t_m08_distritos_resultados.geojson.zip", zf.namelist())
        self.assertNotIn("estado/cache/t_m06_secciones.geojson.zip", zf.namelist())

    def test_archivar_con_paquete(self):
        r2 = R2Falso()
        man = {"artefactos": {}}
        viv = [{**art(7, "ddd-state-41037133327-M06", "2026-11-20T00:00:00Z")}]
        res = arc.archivar(viv, {"ddd-state-41037133327-M06": "cantabria"}, {}, man,
                           lambda a, p: p.write_bytes((self.d / "e.zip").read_bytes()), r2.sha, r2.subir, "bkt",
                           empaquetar=arc.empaquetar_minimo())
        k = "interno/estados/autonomicas/cantabria/ultimo/minimo-m06.zip"  # T-443: árbol nuevo, sin run en la ruta
        self.assertEqual(res["archivados"], [k])
        e = man["artefactos"][k]
        self.assertEqual(e["artefacto"], "ddd-minimo-41037133327-M06")
        self.assertEqual(e["artefacto_origen"], "ddd-state-41037133327-M06")
        self.assertEqual(e["sha256_estado_original"], arc.sha256_fichero(self.d / "e.zip"))
        self.assertLess(e["tamano_bytes"], e["tamano_estado_original"])
        self.assertEqual(res["perdidos"], [])
        self.assertEqual(e["run_id"], "41037133327")

    def test_t443_un_run_anterior_no_pisa_al_ultimo(self):
        r2 = R2Falso()
        man = {"artefactos": {}}
        bajar = lambda a, p: p.write_bytes(a["name"].encode())  # noqa: E731
        nuevo = {**art(9, "ddd-audit-41037133399", "2026-11-25T00:00:00Z")}
        viejo = {**art(8, "ddd-audit-41037133327", "2026-11-20T00:00:00Z")}
        refs = {"ddd-audit-41037133399": "cantabria", "ddd-audit-41037133327": "cantabria"}
        arc.archivar([nuevo], refs, {}, man, bajar, r2.sha, r2.subir, "bkt")
        res = arc.archivar([viejo], refs, {}, man, bajar, r2.sha, r2.subir, "bkt")
        k = "interno/estados/autonomicas/cantabria/ultimo/audit.zip"
        self.assertEqual(res["superados"], [k])
        self.assertEqual(man["artefactos"][k]["run_id"], "41037133399")
        m = arc.manifiesto_carpeta(man["artefactos"], "interno/estados/autonomicas/cantabria/ultimo")
        self.assertEqual(m["ficheros"]["audit.zip"]["run"], "41037133399")

    def test_t443_publicado_y_ultimo(self):
        """D-198: el run publicado va a publicado/ y a ultimo/; uno más reciente sin publicar solo a ultimo/, sin tocar publicado/."""
        r2 = R2Falso()
        man = {"artefactos": {}}
        bajar = lambda a, p: p.write_bytes(a["name"].encode())  # noqa: E731
        refs = {"ddd-audit-41037133327": "cantabria", "ddd-audit-41037133399": "cantabria"}
        pub = {("aut06", "m06"): "41037133327", ("aut06", "m08"): "41037133327"}
        arc.archivar([art(8, "ddd-audit-41037133327", "2026-11-20T00:00:00Z")], refs, {}, man, bajar, r2.sha, r2.subir, "bkt",
                     publicado=pub, r2_cab=r2.cab)
        base = "interno/estados/autonomicas/cantabria"
        self.assertEqual((r2.runs[f"{base}/publicado/audit.zip"], r2.runs[f"{base}/ultimo/audit.zip"]), ("41037133327", "41037133327"))
        arc.archivar([art(9, "ddd-audit-41037133399", "2026-11-25T00:00:00Z")], refs, {}, man, bajar, r2.sha, r2.subir, "bkt",
                     publicado=pub, r2_cab=r2.cab)
        self.assertEqual((r2.runs[f"{base}/publicado/audit.zip"], r2.runs[f"{base}/ultimo/audit.zip"]), ("41037133327", "41037133399"))
        # restaurar y P75 encuentran los dos runs por run_id
        self.assertEqual(sorted(e["run_id"] for e in man["artefactos"].values()), ["41037133327", "41037133399"])
        self.assertEqual(arc.manifiesto_carpeta(man["artefactos"], f"{base}/publicado", r2.cab)["ficheros"]["audit.zip"]["run"], "41037133327")

    def test_t443_la_guarda_es_la_de_r2_no_la_del_indice(self):
        """Índice perdido o atrasado (fallo de push): R2 ya tiene un run mayor en ultimo/ → no se pisa."""
        r2 = R2Falso()
        k = "interno/estados/autonomicas/cantabria/ultimo/audit.zip"
        r2.objs[k], r2.runs[k] = "f" * 64, "41037133399"
        man = {"artefactos": {}}
        res = arc.archivar([art(8, "ddd-audit-41037133327", "2026-11-20T00:00:00Z")], {"ddd-audit-41037133327": "cantabria"}, {}, man,
                           lambda a, p: p.write_bytes(b"x"), r2.sha, r2.subir, "bkt", r2_cab=r2.cab)
        self.assertEqual((res["superados"], r2.subidas, r2.runs[k]), ([k], 0, "41037133399"))

    def test_t443_el_manifiesto_dice_lo_que_hay_en_r2(self):
        r2 = R2Falso()
        base = "interno/estados/autonomicas/cantabria/ultimo"
        r2.objs[f"{base}/audit.zip"], r2.runs[f"{base}/audit.zip"] = "a" * 64, "7"
        ent = {f"{base}/audit.zip": {"sha256": "b" * 64, "run_id": "6"}, f"{base}/minimo-m08.zip": {"sha256": "c" * 64, "run_id": "6"}}
        m = arc.manifiesto_carpeta(ent, base, r2.cab)
        self.assertEqual(sorted(m["ficheros"]), ["audit.zip"])  # el que no está en R2 sale
        self.assertEqual((m["ficheros"]["audit.zip"]["sha256"], m["ficheros"]["audit.zip"]["run"]), ("a" * 64, "7"))

    def test_t443_publicado_por_tipo(self):
        """Revisión de 57f1f11 (3): el run publicado se resuelve por territorio Y tipo (canonical_m06 / canonical_m08)."""
        pub = {("aut06", "m06"): "100", ("aut06", "m08"): "200"}
        self.assertTrue(arc.es_del_publicado("ddd-minimo-100-M06", "cantabria", "100", pub))
        self.assertFalse(arc.es_del_publicado("ddd-minimo-200-M06", "cantabria", "200", pub))
        self.assertTrue(arc.es_del_publicado("ddd-minimo-200-M08", "cantabria", "200", pub))
        self.assertTrue(arc.es_del_publicado("ddd-audit-100", "cantabria", "100", pub))
        self.assertFalse(arc.es_del_publicado("ddd-audit-300", "cantabria", "300", pub))
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "orchestracion").mkdir()
            (root / arc.VISOR).write_text(json.dumps({"products": [
                {"kind": "canonical_m06", "territory_id": "aut06", "run_id": "100"},
                {"kind": "canonical_m08", "territory_id": "aut06", "run_id": "200"},
                {"kind": "canonical_m08", "territory_id": "aut06", "run_id": "150"}]}))
            self.assertEqual(arc.publicados(root), pub)

    def test_t443_escritura_condicional_y_resubida_por_run(self):
        r2 = R2Falso()
        man = {"artefactos": {}}
        bajar = lambda a, p: p.write_bytes(b"mismo contenido")  # noqa: E731
        refs = {"ddd-audit-41037133327": "cantabria", "ddd-audit-41037133399": "cantabria"}
        arc.archivar([art(8, "ddd-audit-41037133327", "2026-11-20T00:00:00Z")], refs, {}, man, bajar, r2.sha, r2.subir, "bkt", r2_cab=r2.cab)
        k = "interno/estados/autonomicas/cantabria/ultimo/audit.zip"
        self.assertEqual(r2.condiciones[0], "*")  # no existía: If-None-Match
        etag = r2.etag(k)
        res = arc.archivar([art(9, "ddd-audit-41037133399", "2026-11-25T00:00:00Z")], refs, {}, man, bajar, r2.sha, r2.subir, "bkt", r2_cab=r2.cab)
        self.assertEqual((res["archivados"][0], r2.runs[k]), (k, "41037133399"))  # mismo sha256, otro run: se resube
        self.assertIn(etag, r2.condiciones)  # If-Match con lo leído (el manifiesto sube sin condición)

    def test_t443_escritura_concurrente_no_pisa(self):
        r2 = R2Falso()
        k = "interno/estados/autonomicas/cantabria/ultimo/audit.zip"
        cab_vieja = {"sha256": None, "run": None, "bytes": None, "etag": None}

        def cab(x):  # lee «no existe»; entre la lectura y la escritura otro proceso la crea
            if x == k:
                r2.objs[k], r2.runs[k] = "e" * 64, "41037133327"
                return None
            return r2.cab(x)
        res = arc.archivar([art(8, "ddd-audit-41037133327", "2026-11-20T00:00:00Z")], {"ddd-audit-41037133327": "cantabria"}, {},
                           {"artefactos": {}}, lambda a, p: p.write_bytes(b"x"), r2.sha, r2.subir, "bkt", r2_cab=cab)
        self.assertTrue(any("R2_ESCRITURA_CONCURRENTE" in e for e in res["errores"]), res)
        self.assertEqual(r2.objs[k], "e" * 64)
        self.assertIsNone(cab_vieja["etag"])

    def test_t443_412_en_el_segundo_destino_no_deja_al_primero_sin_entrada(self):
        """3.ª revisión de #988: ultimo/ sube; publicado/ da 412 (otro lo creó): ultimo/ queda en el índice y su manifiesto se rehace."""
        r2 = R2Falso()
        base = "interno/estados/autonomicas/cantabria"
        kp = f"{base}/publicado/audit.zip"

        def cab(x):  # publicado/ «no existe» al leer; otro proceso lo crea antes de escribir
            if x == kp and kp not in r2.objs:
                r2.objs[kp], r2.runs[kp] = "e" * 64, "41037133327"
                return None
            return r2.cab(x)
        man = {"artefactos": {}}
        pub = {("aut06", "m06"): "41037133327", ("aut06", "m08"): "41037133327"}
        res = arc.archivar([art(8, "ddd-audit-41037133327", "2026-11-20T00:00:00Z")], {"ddd-audit-41037133327": "cantabria"}, {}, man,
                           lambda a, p: p.write_bytes(b"x"), r2.sha, r2.subir, "bkt", publicado=pub, r2_cab=cab)
        self.assertTrue(any("R2_ESCRITURA_CONCURRENTE" in e for e in res["errores"]), res)
        self.assertIn(f"{base}/ultimo/audit.zip", man["artefactos"])
        self.assertNotIn(kp, man["artefactos"])
        self.assertIn(f"{base}/ultimo/manifiesto.json", r2.objs)
        self.assertEqual(r2.objs[kp], "e" * 64)  # lo de otro no se pisa

    def test_t443_territorio_sin_resolver_conserva_la_clave_vieja(self):
        a = {"name": "ddd-audit-1234567890", "territorio": "sin_territorio", "run": "1234567890"}
        self.assertEqual(arc.clave(a), "sin_territorio/1234567890/ddd-audit-1234567890.zip")


class Reintentos(unittest.TestCase):
    def setUp(self):
        self.esperas = []
        p = mock.patch.object(arc, "_dormir", self.esperas.append)
        p.start()
        self.addCleanup(p.stop)

    def e500(self):
        return urllib.error.HTTPError("u", 500, "Internal Server Error", {}, None)

    def test_500_transitorio_se_reintenta_con_backoff(self):
        llamadas = []

        def f():
            llamadas.append(1)
            if len(llamadas) < 4:
                raise self.e500()
            return "ok"

        self.assertEqual(arc.con_reintentos(f, "x"), "ok")
        self.assertEqual(self.esperas, [2, 4, 8])

    def test_agota_intentos(self):
        def f():
            raise self.e500()

        with self.assertRaises(urllib.error.HTTPError):
            arc.con_reintentos(f, "x")
        self.assertEqual(self.esperas, [2, 4, 8, 16, 32])

    def test_4xx_no_se_reintenta(self):
        def f():
            raise urllib.error.HTTPError("u", 404, "nf", {}, None)

        with self.assertRaises(urllib.error.HTTPError):
            arc.con_reintentos(f, "x")
        self.assertEqual(self.esperas, [])

    def test_listado_gh_sobrevive_a_un_500(self):
        respuestas = [self.e500(), mock.MagicMock()]
        resp = respuestas[1]
        resp.__enter__.return_value = resp
        resp.read.return_value = json.dumps({"artifacts": [{"id": 1}]}).encode()

        def abrir(req, timeout=0):
            r = respuestas.pop(0)
            if isinstance(r, Exception):
                raise r
            return r

        with mock.patch.object(arc.urllib.request, "urlopen", abrir):
            self.assertEqual(arc.listar_artefactos_gh("o/r", "t"), [{"id": 1}])
        self.assertEqual(self.esperas, [2])


if __name__ == "__main__":
    unittest.main()
