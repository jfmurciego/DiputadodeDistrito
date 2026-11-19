#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: publicador de la doble vuelta (R2 → sitio, V4) con R2 simulado y un repositorio sintético
VERSIÓN: 1.0.0 · FECHA: 2026-11-19 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
FUNCIÓN: valores esperados a mano (un distrito de 100 votos: PP 30, Sumar 28, PSOE 22, VOX 15, XX 5); controles negativos: sha256 del informe distinto,
  clave ausente, sha256 del ZIP distinto, id de distrito fuera de rango, informe incompleto, primero incoherente, escenario desconocido; sin fijado = no-op.
"""
import csv
import hashlib
import io
import json
import os
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import publicar_doble_vuelta as pdv  # noqa: E402

ENC = ("district_id,escenario,vuelta_decisiva,candidatura_ganadora,bloque_ganador,votos_1v,cuota_1v,finalista_a,finalista_b,votos_a_2v,votos_b_2v,"
       "cuota_ganador_2v,votos_abstencion,empate\n")
ENC_D = "district_id,escenario,candidatura,partido,bloque,votos_1v,votos_candidatura\n"


def resultados(ids=(0, 1), extra=""):
    f = ""
    for i in ids:
        f += (f"{i},dv_base,2,Podemos–Sumar,Izquierdas,30,0.300000,PP,Podemos–Sumar,45,50,0.526316,5,false\n"
              f"{i},dv_A,2,bloque:Izquierdas,Izquierdas,50,0.500000,bloque:Izquierdas,bloque:Patriotas,50,45,0.526316,5,false\n"
              f"{i},dv_B,2,bloque:Izquierdas,Izquierdas,50,0.500000,bloque:Izquierdas,bloque:Patriotas,50,45,0.526316,5,false\n")
    return ENC + f + extra


def detalle(ids=(0, 1)):
    f = ""
    for i in ids:
        for p, b, v in (("PP", "Patriotas", 30), ("Podemos–Sumar", "Izquierdas", 28), ("PSOE", "Izquierdas", 22), ("VOX", "Patriotas", 15), ("XX", "", 5)):
            f += f"{i},dv_base,{p},{p},{b},{v},{v}\n"
    return ENC_D + f


def zip_de(res, det) -> bytes:
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        z.writestr("doble_vuelta.csv", res)
        z.writestr("detalle.csv", det)
        z.writestr("manifiesto.json", "{}")
    return b.getvalue()


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def cuadrado(n: int, extra_colineal=True) -> list:
    """Cuadrado de 0,01° en la columna n (distrito público n); un punto COLINEAL en medio del lado inferior (DP lo quita) y coordenadas con 7 decimales."""
    x0 = 0.01 * (n - 1)
    pts = [[x0, 40.0], ([x0 + 0.005, 40.0000001] if extra_colineal else [x0 + 0.01, 40.0]), [x0 + 0.01, 40.0], [x0 + 0.01, 40.01], [x0, 40.01], [x0, 40.0]]
    return [pts if extra_colineal else pts[:1] + pts[2:]]


def geojson_sitio(ids=(1, 2), sin=()) -> bytes:
    feats = [{"type": "Feature", "properties": {"distrito": n, "poblacion": 10}, "geometry": {"type": "Polygon", "coordinates": cuadrado(n)}} for n in ids if n not in sin]
    return json.dumps({"type": "FeatureCollection", "features": feats}).encode()


class Montaje:
    def __init__(self, td: Path, zips: dict, estado_ok=True, informe_total=None, geo=None):
        self.td, self.objetos = td, {}
        sitio = td / "sitio" / "datos"
        indice = {}
        for t in ("nac01", "nac02"):
            g = geo(t) if geo else geojson_sitio()
            if g is not None:
                (sitio / t).mkdir(parents=True, exist_ok=True)
                (sitio / t / "distritos.geojson").write_bytes(g)
                indice[t] = {"geojson": {"sha256": sha(g)}}
        sitio.mkdir(parents=True, exist_ok=True)
        (sitio / "INDEX.json").write_text(json.dumps({"territorios": indice}), encoding="utf-8")
        (td / "orchestracion").mkdir()
        (td / "configuracion").mkdir()
        (td / "orchestracion/publicaciones_visor.json").write_text(json.dumps({"products": [
            {"kind": "canonical_m08", "territory_id": t, "territory_label": f"Congreso {n}"} for t, n in (("nac01", "Álava"), ("nac02", "Albacete"))]}), encoding="utf-8")
        filas = []
        for t, (run, z) in zip(("nac01", "nac02"), zips.items()):
            clave = f"carpeta_{t}/{run}/ddd-doble-vuelta-{run}-p75-77-1.zip"
            self.objetos[clave] = z
            filas.append({"territorio": t, "run": run, "estado": "OK" if estado_ok else "COBERTURA_BAJA", "sin_casar_pct": 0.0,
                          "sha256_salida": sha(z), "clave_r2": clave})
        inf = {"schema": "ddd.p75-informe/1.0", "eleccion": "2023-07", "run_p75": "77-1",
               "entradas": {"bloques": {"sha256": "b" * 64}, "alias": {"sha256": "a" * 64}}, "territorios": filas,
               "ok": len(filas) if estado_ok else 0, "total": informe_total or len(filas)}
        self.informe = (json.dumps(inf) + "\n").encode()
        self.objetos["doble_vuelta/2023-07/77-1/INFORME.json"] = self.informe
        self.pin = {"eleccion": "2023-07", "run_p75": "77-1", "informe_clave": "doble_vuelta/2023-07/77-1/INFORME.json", "informe_sha256": sha(self.informe)}
        self.escribir_pin()

    def escribir_pin(self):
        (self.td / "configuracion/doble_vuelta_publicada.json").write_text(json.dumps(self.pin), encoding="utf-8")

    def cp(self, origen, destino, extra=None):
        clave = origen.split("/", 3)[3]
        if clave not in self.objetos:
            raise OSError("NoSuchKey")
        Path(destino).write_bytes(self.objetos[clave])


def zips_buenos():
    return {"1001": zip_de(resultados(), detalle()), "1002": zip_de(resultados(), detalle())}


class Publicar(unittest.TestCase):
    def setUp(self):
        p = mock.patch.object(pdv, "ESPERADOS", 2)  # el montaje tiene 2 territorios; en producción son 52
        p.start()
        self.addCleanup(p.stop)

    def correr(self, mod=None, zips=None, **kw):  # kw: estado_ok, informe_total, geo
        with tempfile.TemporaryDirectory() as t, tempfile.TemporaryDirectory() as d:
            m = Montaje(Path(t), zips or zips_buenos(), **kw)
            if mod:
                mod(m)
            try:
                ind = pdv.publicar(Path(t), Path(d), m.cp, "b", "2026-11-19", sitio=Path(t) / "sitio")
            except pdv.DobleVueltaError as exc:
                return None, str(exc), {}
            salida = {str(p.relative_to(d)): p.read_bytes() for p in Path(d).rglob("*") if p.is_file()}
            return ind, "", salida

    def test_exito_con_valores_a_mano(self):
        ind, err, s = self.correr()
        self.assertEqual(err, "")
        self.assertEqual(sorted(s), ["INDEX.json", "nac01/detalle.csv", "nac01/distritos.geojson", "nac01/resultados_doble_vuelta.csv",
                                  "nac02/detalle.csv", "nac02/distritos.geojson", "nac02/resultados_doble_vuelta.csv"])
        e = ind["territorios"][0]
        self.assertEqual((e["id"], e["nombre"], e["etiqueta"], e["distritos"]), ("nac01", "Álava", "Congreso Álava", 2))
        res = list(csv.DictReader(io.StringIO(s["nac01/resultados_doble_vuelta.csv"].decode())))
        self.assertEqual(sorted({r["district_id"] for r in res}), ["1", "2"])  # interno 0..1 → público 1..2
        self.assertEqual([r["escenario"] for r in res[:4]], ["dv_base", "dv_A", "dv_B", "primero"])
        p = res[3]  # primero del distrito 1: PP 30 de 100
        self.assertEqual((p["candidatura_ganadora"], p["bloque_ganador"], p["vuelta_decisiva"], p["cuota_1v"], p["empate"]), ("PP", "Patriotas", "1", "0.300000", "false"))
        det = list(csv.DictReader(io.StringIO(s["nac01/detalle.csv"].decode())))
        self.assertEqual(len([d for d in det if d["escenario"] == "primero"]), 10)  # 5 partidos × 2 distritos
        self.assertEqual(e["resultados"]["sha256"], sha(s["nac01/resultados_doble_vuelta.csv"]))
        self.assertEqual((ind["aviso"], ind["generado"], ind["p75_run"], ind["bloques_sha256"]), ("Simulación sin valor oficial", "2026-11-19", "77-1", "b" * 64))
        self.assertEqual(json.loads(s["INDEX.json"]), ind)

    def test_geometria_simplificada_con_district_id_publico(self):
        ind, err, s = self.correr()
        self.assertEqual(err, "")
        gj = json.loads(s["nac01/distritos.geojson"])
        self.assertEqual([f["properties"] for f in gj["features"]], [{"district_id": 1}, {"district_id": 2}])  # solo district_id, entero público
        anillo = gj["features"][0]["geometry"]["coordinates"][0]
        self.assertEqual(anillo, [[0.0, 40.0], [0.01, 40.0], [0.01, 40.01], [0.0, 40.01], [0.0, 40.0]])  # 7 decimales → 5; punto colineal fuera; esquinas dentro
        g = ind["territorios"][0]["geometria"]
        self.assertEqual(g["sha256"], sha(s["nac01/distritos.geojson"]))
        self.assertEqual(g["sha256_origen"], sha(geojson_sitio()))
        self.assertEqual(ind["simplificacion"]["tolerancia_grados"], pdv.TOLERANCIA_GRADOS)

    def test_douglas_peucker(self):
        tol = 0.001
        self.assertEqual(pdv.douglas_peucker([[0, 0], [1, 0.0005], [2, 0]], tol), [[0, 0], [2, 0]])  # desvío 0,0005 < tol: se quita
        self.assertEqual(pdv.douglas_peucker([[0, 0], [1, 0.002], [2, 0]], tol), [[0, 0], [1, 0.002], [2, 0]])  # 0,002 > tol: se conserva
        n = 30000  # sin recursión: un anillo grande no desborda la pila
        zig = [[i * 1e-6, (i % 2) * 1e-7] for i in range(n)]
        self.assertEqual(len(pdv.douglas_peucker(zig, tol)), 2)

    def test_distrito_sin_geometria_falla(self):  # control negativo obligatorio
        _, err, s = self.correr(geo=lambda t: geojson_sitio(sin=(2,)))
        self.assertIn("DATO_SIN_GEOMETRIA", err)
        self.assertEqual(s, {})  # o todo o nada

    def test_geometria_sin_dato_falla(self):
        _, err, s = self.correr(geo=lambda t: geojson_sitio(ids=(1, 2, 3)))
        self.assertIn("GEOMETRIA_SIN_DATO", err)
        self.assertEqual(s, {})

    def test_geometria_ausente_o_con_sha_distinto(self):
        _, err, _ = self.correr(geo=lambda t: None)
        self.assertIn("GEOMETRIA_AUSENTE", err)

        def mod(m):
            (m.td / "sitio/datos/nac01/distritos.geojson").write_bytes(geojson_sitio() + b" ")
        _, err, s = self.correr(mod)
        self.assertIn("GEOMETRIA_SHA256_DISTINTO", err)
        self.assertEqual(s, {})

    def test_geometria_sin_sitio(self):
        with tempfile.TemporaryDirectory() as t, tempfile.TemporaryDirectory() as d:
            m = Montaje(Path(t), zips_buenos())
            with self.assertRaisesRegex(pdv.DobleVueltaError, "GEOMETRIA_AUSENTE"):
                pdv.publicar(Path(t), Path(d), m.cp, "b", "2026-11-19")

    def test_primero_cubre_todos_los_distritos(self):
        det = detalle(ids=(0,))  # dv_base sin detalle del distrito 1
        z = zip_de(resultados(), det)
        _, err, s = self.correr(zips={"1001": z, "1002": z})
        self.assertIn("PRIMERO_INCOMPLETO", err)
        self.assertEqual(s, {})

    def test_id_de_territorio_invalido_o_duplicado_y_total(self):
        for nuevo, causa in (("../x", "TERRITORIO_INVALIDO"), ("nac1", "TERRITORIO_INVALIDO"), ("nac01", "TERRITORIO_DUPLICADO")):
            def mod(m, nuevo=nuevo):
                inf = json.loads(m.informe)
                inf["territorios"][1]["territorio"] = nuevo
                m.informe = (json.dumps(inf) + "\n").encode()
                m.objetos["doble_vuelta/2023-07/77-1/INFORME.json"] = m.informe
                m.pin["informe_sha256"] = sha(m.informe)
                m.escribir_pin()
            _, err, s = self.correr(mod)
            self.assertIn(causa, err, nuevo)
            self.assertEqual(s, {})

    def test_exige_los_52_no_solo_ok_igual_a_total(self):
        with mock.patch.object(pdv, "ESPERADOS", 52):  # control negativo con el valor real: un informe sano de 2 territorios no vale
            _, err, s = self.correr()
        self.assertIn("INFORME_INCOMPLETO", err)
        self.assertEqual(s, {})

    def test_informe_sin_entradas_da_error_con_codigo(self):
        def mod(m):
            inf = json.loads(m.informe)
            del inf["entradas"]["alias"]
            m.informe = (json.dumps(inf) + "\n").encode()
            m.objetos["doble_vuelta/2023-07/77-1/INFORME.json"] = m.informe
            m.pin["informe_sha256"] = sha(m.informe)
            m.escribir_pin()
        _, err, s = self.correr(mod)
        self.assertIn("INFORME_SIN_ENTRADAS", err)  # DobleVueltaError con código, no un KeyError con traceback
        self.assertEqual(s, {})

    def test_zip_demasiado_grande_descomprimido(self):
        with mock.patch.object(pdv, "MAX_DESCOMPRIMIDO", 100):
            _, err, s = self.correr()
        self.assertIn("ZIP_DEMASIADO_GRANDE", err)
        self.assertEqual(s, {})

    def test_salida_determinista(self):
        self.assertEqual(self.correr()[2], self.correr()[2])

    def test_sin_fijado_no_hace_nada(self):
        with tempfile.TemporaryDirectory() as t, tempfile.TemporaryDirectory() as d:
            Path(t, "configuracion").mkdir()
            self.assertIsNone(pdv.publicar(Path(t), Path(d), lambda *a: 1 / 0, "b"))
            self.assertEqual(list(Path(d).iterdir()), [])

    def test_informe_con_sha256_distinto(self):
        def mod(m):
            m.pin["informe_sha256"] = "0" * 64
            m.escribir_pin()
        ind, err, s = self.correr(mod)
        self.assertIn("INFORME_SHA256_DISTINTO", err)
        self.assertEqual(s, {})

    def test_clave_ausente(self):
        def mod(m):
            del m.objetos[next(k for k in m.objetos if k.endswith(".zip"))]
        _, err, s = self.correr(mod)
        self.assertIn("CLAVE_AUSENTE", err)
        self.assertEqual(s, {})  # o todo o nada

    def test_zip_con_sha256_distinto(self):
        def mod(m):
            k = next(k for k in m.objetos if k.endswith(".zip"))
            m.objetos[k] = m.objetos[k] + b"x"
        _, err, s = self.correr(mod)
        self.assertIn("ZIP_SHA256_DISTINTO", err)
        self.assertEqual(s, {})

    def test_t422_ids_como_real_o_con_espacios_se_normalizan(self):
        """T-422: M07 puede escribir «0.0» o « 1 »; el público sigue siendo 1..K y 52/52 intacto."""
        res = resultados(("0.0", " 1 "))
        det = detalle(("0.0", " 1 "))
        z = zip_de(res, det)
        _, err, s = self.correr(zips={"1001": z, "1002": z})
        self.assertNotIn("ID_FUERA_DE_RANGO", err)
        csv_pub = s["nac01/resultados_doble_vuelta.csv"].decode("utf-8")
        self.assertEqual({l.split(",")[0] for l in csv_pub.splitlines()[1:]}, {"1", "2"})

    def test_t422_id_no_numerico_da_diagnostico_por_territorio(self):
        malo = zip_de(resultados(("0", "nan")), detalle(("0", "nan")))
        _, err, s = self.correr(zips={"1001": malo, "1002": malo})
        self.assertIn("nac01/doble_vuelta.csv", err)
        self.assertIn("nac02/doble_vuelta.csv", err)  # informa de todos, no solo del primero
        self.assertIn("'nan'", err)
        self.assertEqual(s, {})

    def test_t422_barrido_52_ids_reales_de_datos_resultados(self):
        """Los 52 nac de `datos/resultados/` (ganador por distrito, fuente del M08 publicado) pasan por el publicador como 0..K-1, también escritos «N.0»."""
        for i in range(1, 53):
            t = f"nac{i:02d}"
            with open(ROOT / "datos" / "resultados" / f"{t}.csv", encoding="utf-8", newline="") as f:
                ids = [r["distrito"] for r in csv.DictReader(f)]
            for forma in (lambda x: x, lambda x: f"{x}.0"):
                filas = [{"district_id": forma(d)} for d in ids]
                norm = pdv._normalizar_ids(t, filas, "doble_vuelta.csv")
                self.assertEqual(sorted(int(r["district_id"]) for r in norm), list(range(len(ids))), t)
        # nac02 (Albacete, 3 distritos): caso real del fallo del run 44615106125
        z = zip_de(resultados(("0.0", "1.0", "2.0")), detalle(("0.0", "1.0", "2.0")))
        res, _, k = pdv.procesar_territorio({"territorio": "nac02"}, z)
        self.assertEqual(k, 3)
        self.assertEqual({l.split(",")[0] for l in res.decode("utf-8").splitlines()[1:]}, {"1", "2", "3"})

    def test_id_de_distrito_fuera_de_rango(self):
        for ids in ((1, 2), (0, 2)):  # empieza en 1 o con hueco
            z = zip_de(resultados(ids), detalle(ids))
            _, err, s = self.correr(zips={"1001": z, "1002": z})
            self.assertIn("ID_FUERA_DE_RANGO", err, ids)
            self.assertEqual(s, {})

    def test_informe_incompleto(self):
        _, err, _ = self.correr(estado_ok=False)
        self.assertIn("INFORME_INCOMPLETO", err)
        self.assertIn("COBERTURA_BAJA", err)

    def test_escenario_desconocido_y_primero_incoherente(self):
        z = zip_de(resultados(extra="0,dv_X,1,A,,1,1,,,,,,0,false\n"), detalle())
        _, err, _ = self.correr(zips={"1001": z, "1002": z})
        self.assertIn("ESCENARIO_DESCONOCIDO", err)
        malo = resultados().replace("dv_base,2,Podemos–Sumar,Izquierdas,30", "dv_base,2,Podemos–Sumar,Izquierdas,31")
        z = zip_de(malo, detalle())
        _, err, _ = self.correr(zips={"1001": z, "1002": z})
        self.assertIn("PRIMERO_INCOHERENTE", err)

    def test_empate_en_primero(self):
        det = ENC_D + "".join(f"0,dv_base,{p},{p},{b},30,30\n" for p, b in (("AAA", "Patriotas"), ("BBB", "Izquierdas")))
        res = ENC + "0,dv_base,2,AAA,Patriotas,30,0.500000,AAA,BBB,30,30,0.5,0,true\n0,dv_A,2,x,,1,1,,,,,,0,false\n0,dv_B,2,x,,1,1,,,,,,0,false\n"
        _, err, s = self.correr(zips={"1001": zip_de(res, det), "1002": zip_de(res, det)}, geo=lambda t: geojson_sitio(ids=(1,)))
        self.assertEqual(err, "")
        p = [r for r in csv.DictReader(io.StringIO(s["nac01/resultados_doble_vuelta.csv"].decode())) if r["escenario"] == "primero"][0]
        self.assertEqual((p["candidatura_ganadora"], p["empate"]), ("AAA", "true"))  # alfabético, marcado

    def test_zip_slip_no_se_extrae(self):
        b = io.BytesIO()
        with zipfile.ZipFile(b, "w") as z:
            z.writestr("../doble_vuelta.csv", resultados())
            z.writestr("detalle.csv", detalle())
        z = b.getvalue()
        _, err, _ = self.correr(zips={"1001": z, "1002": z})
        self.assertIn("ZIP_INCOMPLETO", err)

    def test_main_sin_credenciales_y_sin_fijado(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(pdv.main(["--destino", "/tmp/x", "--fijado", "configuracion/no_existe.json"]), 0)


class WorkflowP40(unittest.TestCase):
    """El paso de P40: mismas credenciales R2 que el resto, sin entradas nuevas, y sin escribir en git ni fuera del sitio."""

    @classmethod
    def setUpClass(cls):
        import yaml
        cls.wf = yaml.safe_load((ROOT / ".github/workflows/p40-publicacion.yml").read_text(encoding="utf-8"))
        cls.paso = next(s for s in cls.wf["jobs"]["publicar"]["steps"] if s.get("name", "").startswith("Doble vuelta de los territorios"))

    def test_credenciales_r2_ya_existentes_y_sin_secretos_nuevos(self):
        self.assertEqual(sorted(self.paso["env"]), ["AWS_ACCESS_KEY_ID", "AWS_DEFAULT_REGION", "AWS_SECRET_ACCESS_KEY", "R2_ACCOUNT_ID", "R2_BUCKET"])
        usados = {s for v in self.paso["env"].values() for s in __import__("re").findall(r"secrets\.(\w+)", str(v))}
        self.assertLessEqual(usados, {"R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_ACCOUNT_ID"})

    def test_solo_escribe_en_el_sitio_candidato(self):
        run = self.paso["run"]
        self.assertIn("--sitio /tmp/site-candidate --destino /tmp/site-candidate/v4/mapa/datos", run)
        for prohibido in ("git push", "git add", "registrar_en_main", "gh api", "inputs."):
            self.assertNotIn(prohibido, run)

    def test_p40_copia_visor_v4_completo_antes_del_paso_de_datos(self):
        n = [s.get("name") for s in self.wf["jobs"]["publicar"]["steps"]]
        construir = next(s for s in self.wf["jobs"]["publicar"]["steps"] if s.get("name") == "Construir sitio candidato completo")
        self.assertIn("cp -R visor/v4/. /tmp/site-candidate/v4/", construir["run"])
        self.assertLess(n.index("Construir sitio candidato completo"), n.index(self.paso["name"]))  # la copia va antes: el paso añade v4/mapa/datos/ encima
        for intacto in ("cp -R visor/v2/. /tmp/site-candidate/v2/", "cp visor/v3/index.html visor/v3/v3.css visor/v3/v3.js visor/v3/calendario.json /tmp/site-candidate/v3/"):
            self.assertIn(intacto, construir["run"])  # V2 y V3 siguen igual

    def test_v4_llega_al_sitio_con_sus_datos(self):
        """Ejecuta la línea de copia del workflow contra el visor real y el publicador contra un montaje sintético: el sitio queda con v4/ y v4/mapa/datos/."""
        import re
        import subprocess
        construir = next(s for s in self.wf["jobs"]["publicar"]["steps"] if s.get("name") == "Construir sitio candidato completo")
        lineas = [l.split("  #")[0].strip() for l in construir["run"].splitlines() if "visor/v4/" in l and "site-candidate/v4" in l]
        self.assertEqual(len(lineas), 2)  # copia + borrado de lo no público
        linea = " && ".join(lineas[:1]) + "\n" + lineas[1]
        with tempfile.TemporaryDirectory() as site, tempfile.TemporaryDirectory() as t:
            subprocess.run(["bash", "-c", linea.replace("/tmp/site-candidate", site)], cwd=ROOT, check=True)
            for f in ("index.html", "mapa/dv.js"):
                self.assertTrue((Path(site) / "v4" / f).is_file(), f)
            excluidas = [l for l in (ROOT / "visor/v4/NO_PUBLICAR.txt").read_text(encoding="utf-8").splitlines() if l and not l.startswith("#")]
            for e in excluidas:  # lo listado no llega al sitio
                self.assertFalse((Path(site) / "v4" / e).exists(), e)
            for f in ("index.html", "comprender.html", "styles.css", "tokens-bloques.css", "mapa/index.html", "mapa/dv.js", "mapa/geo.js", "mapa/mapa.js", "mapa/mapa.css"):
                self.assertTrue((Path(site) / "v4" / f).is_file(), f)  # lo demás sí
            publicados = {str(p.relative_to(Path(site) / "v4")) for p in (Path(site) / "v4").rglob("*") if p.is_file()}
            self.assertFalse({"NOTICE.md", "assets-manifest.json", "auditoria-registro.html", "NO_PUBLICAR.txt"} & publicados)
            self.assertFalse(any(x.startswith("mapa/ejemplo/") for x in publicados))
            m = Montaje(Path(t), zips_buenos())
            with mock.patch.object(pdv, "ESPERADOS", 2):
                pdv.publicar(Path(t), Path(site) / "v4/mapa/datos", m.cp, "b", "2026-11-19", sitio=Path(t) / "sitio")
            self.assertTrue((Path(site) / "v4/mapa/datos/INDEX.json").is_file())
            self.assertTrue((Path(site) / "v4/mapa/datos/nac01/distritos.geojson").is_file())
            self.assertTrue((Path(site) / "v4/mapa/dv.js").is_file())  # los datos no pisan el visor
            self.assertIsNone(re.search(r"\.\.", linea.replace("*..*", "")))

    def test_la_lista_de_no_publicar_es_segura(self):
        lista = (ROOT / "visor/v4/NO_PUBLICAR.txt").read_text(encoding="utf-8").splitlines()
        entradas = [l for l in lista if l and not l.startswith("#")]
        self.assertTrue(entradas)
        for e in entradas:
            self.assertFalse(e.startswith("/") or ".." in e, e)  # nada fuera de visor/v4/
            self.assertTrue((ROOT / "visor/v4" / e).exists(), f"{e} no existe en visor/v4/: lista desfasada")

    def test_va_antes_de_validar_el_sitio_y_sin_entradas_nuevas(self):
        n = [s.get("name") for s in self.wf["jobs"]["publicar"]["steps"]]
        self.assertLess(n.index(self.paso["name"]), n.index("Validar sitio candidato completo"))
        ent = (self.wf.get("on") or self.wf.get(True))["workflow_dispatch"]["inputs"]
        self.assertEqual(sorted(ent), ["que_publicar", "simular", "territorios"])


class Fijado(unittest.TestCase):
    """El fichero que fija en el repo el run de P75 que publica P40: formato y coherencia (la huella la verificó el Coordinador en el log del run)."""

    def setUp(self):
        self.pin = json.loads((ROOT / pdv.FIJADO).read_text(encoding="utf-8"))

    def test_formato(self):
        import re
        self.assertEqual(sorted(self.pin), ["eleccion", "informe_clave", "informe_sha256", "run_p75", "schema"])
        self.assertEqual(self.pin["schema"], "ddd.doble-vuelta-publicada/1.0")
        self.assertRegex(self.pin["eleccion"], r"^\d{4}-\d{2}$")
        self.assertRegex(self.pin["run_p75"], r"^\d+-\d+$")  # GITHUB_RUN_ID-GITHUB_RUN_ATTEMPT
        self.assertRegex(self.pin["informe_sha256"], r"^[0-9a-f]{64}$")

    def test_la_clave_es_la_del_run_fijado(self):
        self.assertEqual(self.pin["informe_clave"], f"doble_vuelta/{self.pin['eleccion']}/{self.pin['run_p75']}/INFORME.json")

    def test_valores_fijados(self):  # literales de la huella verificada en el log del job de P75 (run 44575597009, intento 1, 52/52 OK)
        self.assertEqual((self.pin["eleccion"], self.pin["run_p75"]), ("2023-07", "44575597009-1"))
        self.assertEqual(self.pin["informe_sha256"], "c127f66b074a37319b864a090c7585c6db4ccc923482e11342b147e69194711c")

    def test_el_publicador_lo_acepta_como_fijado_valido(self):
        # control: con un informe cuyo sha256 NO es el fijado, el publicador falla cerrado (no publica con otra huella)
        with tempfile.TemporaryDirectory() as t, tempfile.TemporaryDirectory() as d:
            m = Montaje(Path(t), zips_buenos())
            (Path(t) / "configuracion/doble_vuelta_publicada.json").write_text((ROOT / pdv.FIJADO).read_text(encoding="utf-8"), encoding="utf-8")
            m.objetos[self.pin["informe_clave"]] = m.informe  # sirve OTRO informe con ese nombre
            with self.assertRaisesRegex(pdv.DobleVueltaError, "INFORME_SHA256_DISTINTO"):
                pdv.publicar(Path(t), Path(d), m.cp, "b", "2026-11-19", sitio=Path(t) / "sitio")


if __name__ == "__main__":
    unittest.main()
