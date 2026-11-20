"""T-430 fase 1 (D-186): `herramientas/publicar_datos_web.py` sube a R2 los datos de la web y reescribe `actual.json` solo al final."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from herramientas import publicar_datos_web as w


class R2Falso:
    def __init__(self, corromper=None):
        self.obj, self.escritos, self.corromper = {}, [], corromper

    def leer(self, clave):
        return self.obj.get(clave)

    def borrar(self, clave):
        self.obj.pop(clave, None)

    def escribir(self, clave, origen, cache):
        b = Path(origen).read_bytes()
        self.obj[clave] = b"X" if clave == self.corromper else b
        self.escritos.append((clave, cache))


def sitio(raiz: Path, geo01=b'{"a":1}'):
    f = {"datos/INDEX.json": json.dumps({"territorios": {"nac01": {"run_id": "111"}, "nac02": {"run_id": "222"}}}).encode(),
         "datos/catalogo_procedencia.json": b"{}", "datos/nac01/distritos.geojson": geo01,
         "datos/nac02/distritos.geojson": b'{"b":2}', "mapa/datos/INDEX.json": b"{}",
         "mapa/datos/nac01/detalle.csv": b"d\n1\n", "mapa/datos/aut14/resultados_doble_vuelta.csv": b"r\n",
         "v2/datos/provincias.json": b"[]", "data/viewer-results.json": b"{}", "index.html": b"<html>"}
    for r, b in f.items():
        (raiz / r).parent.mkdir(parents=True, exist_ok=True)
        (raiz / r).write_bytes(b)


class DatosWeb(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory()
        self.s = Path(self.d.name)
        sitio(self.s)

    def tearDown(self):
        self.d.cleanup()

    def test_reparto_por_territorio_y_comunes(self):
        g = w.plan(self.s)
        self.assertEqual(set(g), {"comunes", "mapas/nac01", "mapas/nac02", "mapas/aut14"})
        self.assertEqual(set(g["mapas/nac01"]), {"datos/nac01/distritos.geojson", "mapa/datos/nac01/detalle.csv"})
        self.assertEqual(set(g["comunes"]), {"datos/INDEX.json", "datos/catalogo_procedencia.json", "mapa/datos/INDEX.json",
                                              "v2/datos/provincias.json", "data/viewer-results.json"})  # index.html no es dato

    def test_publica_y_actual_al_final_con_sha256(self):
        r2 = R2Falso()
        idx = w.publicar(self.s, r2, "999", ahora="2026-11-20T00:00:00Z")
        self.assertEqual(r2.escritos[-1], ("web/actual/actual.json", "public, max-age=60"))
        self.assertTrue(all(c == "public, max-age=60" and k.startswith("web/actual/") for k, c in r2.escritos))
        self.assertEqual(idx["mapas"]["nac01"]["run"], "111")
        self.assertEqual(r2.obj["web/actual/datos/nac01/distritos.geojson"], b'{"a":1}')  # ruta de hoy, sin códigos ni runs
        self.assertEqual(json.loads(r2.obj["web/actual/actual.json"]), idx)
        self.assertEqual(idx["mapas"]["nac01"]["ficheros"]["datos/nac01/distritos.geojson"], hashlib.sha256(b'{"a":1}').hexdigest())
        self.assertEqual(idx["comunes"]["run"], "999")

    def test_regenerar_un_territorio_solo_sube_lo_suyo(self):
        r2 = R2Falso()
        a = w.publicar(self.s, r2, "1")
        n = len(r2.escritos)
        self.assertEqual(w.publicar(self.s, r2, "2")["mapas"], a["mapas"])
        self.assertEqual(r2.escritos[n:], [("web/actual/actual.json", "public, max-age=60")])  # nada nuevo: solo el índice
        n = len(r2.escritos)
        (self.s / "datos/nac01/distritos.geojson").write_bytes(b'{"a":2}')
        b = w.publicar(self.s, r2, "3")
        self.assertEqual([k for k, _ in r2.escritos[n:]], ["web/actual/datos/nac01/distritos.geojson", "web/actual/actual.json"])
        self.assertEqual({t: b["mapas"][t] for t in ("nac02", "aut14")}, {t: a["mapas"][t] for t in ("nac02", "aut14")})

    def test_solo_la_vigente_borra_lo_que_sale_del_indice_despues(self):
        r2 = R2Falso()
        w.publicar(self.s, r2, "1")
        (self.s / "mapa/datos/nac01/detalle.csv").unlink()
        orden = []
        r2.borrar = lambda k: (orden.append(("borrar", k, "web/actual/actual.json" in r2.obj)), r2.obj.pop(k))
        w.publicar(self.s, r2, "2")
        self.assertEqual(orden, [("borrar", "web/actual/mapa/datos/nac01/detalle.csv", True)])
        self.assertNotIn("mapa/datos/nac01/detalle.csv", json.dumps(json.loads(r2.obj["web/actual/actual.json"])))

    def test_sha256_distinto_tras_subir_no_toca_actual(self):
        r2 = R2Falso(corromper="web/actual/datos/nac02/distritos.geojson")
        r2.obj["web/actual/actual.json"] = b'{"previo": true}'
        with self.assertRaises(w.DatosWebError):
            w.publicar(self.s, r2, "1")
        self.assertEqual(r2.obj["web/actual/actual.json"], b'{"previo": true}')

    def test_simular_no_escribe(self):
        r2 = R2Falso()
        w.publicar(self.s, r2, "1", simular=True)
        self.assertEqual(r2.escritos, [])

    def test_sin_bucket_no_hace_nada(self):
        self.assertEqual(w.main(["--sitio", str(self.s), "--bucket", ""]), 0)

    def test_sin_indice_falla(self):
        (self.s / "datos/INDEX.json").unlink()
        with self.assertRaises(w.DatosWebError):
            w.plan(self.s)


class PasoP40(unittest.TestCase):
    def test_solo_desde_main_y_secretos_en_el_paso(self):
        import yaml
        wf = yaml.safe_load((Path(__file__).resolve().parents[1] / ".github/workflows/p40-publicacion.yml").read_text(encoding="utf-8"))
        pasos = [s for s in wf["jobs"]["publicar"]["steps"] if s.get("name") == "Datos de la web en R2 (T-430)"]
        self.assertEqual(len(pasos), 1)
        p = pasos[0]
        self.assertEqual(p.get("if"), "${{ github.ref == 'refs/heads/main' }}")  # otra rama no reescribe actual.json de producción
        self.assertEqual(p["env"]["R2_WEB_BUCKET"], "${{ vars.R2_WEB_BUCKET }}")
        self.assertIn("publicar_datos_web.py --sitio /tmp/site-candidate", p["run"])


if __name__ == "__main__":
    unittest.main()
