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

    def _previo_con(self, r2, extra):
        idx = w.publicar(self.s, r2, "1")
        idx["mapas"]["nac01"]["ficheros"].update({k: "0" * 64 for k in extra})
        r2.obj["web/actual/actual.json"] = json.dumps(idx).encode()
        return r2.obj["web/actual/actual.json"]

    def test_candidato_sin_territorios_no_publica_ni_borra(self):
        r2 = R2Falso()
        w.publicar(self.s, r2, "1")
        antes = dict(r2.obj)
        (self.s / "datos/INDEX.json").write_text('{"territorios": {}}')
        import shutil
        for d in ("nac01", "aut14"):
            shutil.rmtree(self.s / "mapa/datos" / d)
        with self.assertRaises(w.DatosWebError):
            w.publicar(self.s, r2, "2")
        self.assertEqual(r2.obj, antes)

    def test_candidato_truncado_no_borra(self):
        r2 = R2Falso()
        w.publicar(self.s, r2, "1")
        antes = dict(r2.obj)
        idx = json.loads((self.s / "datos/INDEX.json").read_text())
        del idx["territorios"]["nac02"]
        (self.s / "datos/INDEX.json").write_text(json.dumps(idx))
        import shutil
        shutil.rmtree(self.s / "datos/nac02")
        with self.assertRaises(w.DatosWebError) as e:
            w.publicar(self.s, r2, "2")
        self.assertIn("TERRITORIOS_DESAPARECEN", str(e.exception))
        self.assertEqual(r2.obj, antes)
        w.publicar(self.s, r2, "3", permitir_borrado=True)  # anulación explícita
        self.assertNotIn("web/actual/datos/nac02/distritos.geojson", r2.obj)

    def test_borrado_masivo_aborta(self):
        r2 = R2Falso()
        previo = self._previo_con(r2, [f"datos/nac01/viejo{i}.csv" for i in range(60)])
        with self.assertRaises(w.DatosWebError) as e:
            w.publicar(self.s, r2, "2")
        self.assertIn("BORRADO_MASIVO", str(e.exception))
        self.assertEqual(r2.obj["web/actual/actual.json"], previo)

    def test_borrado_por_porcentaje_aborta(self):
        r2 = R2Falso()
        previo = self._previo_con(r2, [f"datos/nac01/viejo{i}.csv" for i in range(6)])  # 6 de 15 > 10 %, por debajo de 50
        with self.assertRaises(w.DatosWebError):
            w.publicar(self.s, r2, "2")
        self.assertEqual(r2.obj["web/actual/actual.json"], previo)

    def test_clave_fuera_de_los_arboles_no_se_borra(self):
        for mala in ("../x", "datos/../../otro", "/datos/x", "", "interno/x", "web/actual/actual.json", "datos//x"):
            self.assertFalse(w.clave_valida(mala), mala)
        r2 = R2Falso()
        previo = self._previo_con(r2, ["fuentes/ine.zip"])
        with self.assertRaises(w.DatosWebError) as e:
            w.publicar(self.s, r2, "2", permitir_borrado=True)  # ni con anulación
        self.assertIn("CLAVE_NO_BORRABLE", str(e.exception))
        self.assertEqual(r2.obj["web/actual/actual.json"], previo)

    def test_ninguna_clave_borrada_fuera_de_web_actual(self):
        r2 = R2Falso()
        self._previo_con(r2, ["datos/nac01/viejo.csv"])
        borradas = []
        r2.borrar = lambda k: borradas.append(k)
        w.publicar(self.s, r2, "2")
        self.assertEqual(borradas, ["web/actual/datos/nac01/viejo.csv"])

    def test_fallo_tras_subir_o_del_indice_no_borra(self):
        for corromper in ("web/actual/datos/nac02/distritos.geojson", "web/actual/actual.json"):
            r2 = R2Falso()
            self._previo_con(r2, ["datos/nac01/viejo.csv"])
            (self.s / "datos/nac02/distritos.geojson").write_bytes(b'{"b":3}')
            borradas = []
            r2.borrar, r2.corromper = (lambda k: borradas.append(k)), corromper
            with self.assertRaises(w.DatosWebError):
                w.publicar(self.s, r2, "2")
            self.assertEqual(borradas, [], corromper)

    def test_simular_con_sobrantes_no_borra(self):
        r2 = R2Falso()
        self._previo_con(r2, ["datos/nac01/viejo.csv"])
        n = len(r2.escritos)
        borradas = []
        r2.borrar = lambda k: borradas.append(k)
        w.publicar(self.s, r2, "2", simular=True)
        self.assertEqual((borradas, len(r2.escritos)), ([], n))

    def test_bucket_de_trabajo_rechazado(self):
        import os
        from unittest import mock
        with mock.patch.dict(os.environ, {"R2_BUCKET": "trabajo"}):
            self.assertEqual(w.main(["--sitio", str(self.s), "--bucket", "trabajo"]), 1)

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
        # T-510 (P40 1.8.0): el paso vive en el job `subir_r2` (entorno publicacion); «solo main» va en la condición del job
        pasos = [(j, s) for j, job in wf["jobs"].items() for s in job["steps"] if s.get("name") == "Datos de la web en R2 (T-430)"]
        self.assertEqual(len(pasos), 1)
        j, p = pasos[0]
        self.assertEqual(j, "subir_r2")
        self.assertIn("github.ref == 'refs/heads/main'", wf["jobs"][j]["if"])  # otra rama no reescribe actual.json de producción
        self.assertEqual(p.get("if"), "${{ steps.sitio.outcome == 'success' }}")
        self.assertEqual(p["env"]["R2_WEB_BUCKET"], "${{ vars.R2_WEB_BUCKET }}")
        self.assertEqual(p["env"]["R2_BUCKET"], "${{ vars.R2_BUCKET }}")  # para rechazar el bucket de trabajo
        self.assertNotIn("--permitir-borrado", p["run"])  # la anulación del tope nunca va en el workflow
        self.assertIn("publicar_datos_web.py --sitio /tmp/site-candidate", p["run"])


if __name__ == "__main__":
    unittest.main()
