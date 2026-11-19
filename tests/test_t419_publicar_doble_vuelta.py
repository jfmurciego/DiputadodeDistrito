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


class Montaje:
    def __init__(self, td: Path, zips: dict, estado_ok=True, informe_total=None):
        self.td, self.objetos = td, {}
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
    def correr(self, mod=None, zips=None, **kw):
        with tempfile.TemporaryDirectory() as t, tempfile.TemporaryDirectory() as d:
            m = Montaje(Path(t), zips or zips_buenos(), **kw)
            if mod:
                mod(m)
            try:
                ind = pdv.publicar(Path(t), Path(d), m.cp, "b", "2026-11-19")
            except pdv.DobleVueltaError as exc:
                return None, str(exc), {}
            salida = {str(p.relative_to(d)): p.read_bytes() for p in Path(d).rglob("*") if p.is_file()}
            return ind, "", salida

    def test_exito_con_valores_a_mano(self):
        ind, err, s = self.correr()
        self.assertEqual(err, "")
        self.assertEqual(sorted(s), ["INDEX.json", "nac01/detalle.csv", "nac01/resultados_doble_vuelta.csv", "nac02/detalle.csv", "nac02/resultados_doble_vuelta.csv"])
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
        _, err, s = self.correr(zips={"1001": zip_de(res, det), "1002": zip_de(res, det)})
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
        self.assertIn("--destino /tmp/site-candidate/v4/mapa/datos", run)
        for prohibido in ("git push", "git add", "registrar_en_main", "gh api", "inputs."):
            self.assertNotIn(prohibido, run)

    def test_va_antes_de_validar_el_sitio_y_sin_entradas_nuevas(self):
        n = [s.get("name") for s in self.wf["jobs"]["publicar"]["steps"]]
        self.assertLess(n.index(self.paso["name"]), n.index("Validar sitio candidato completo"))
        ent = (self.wf.get("on") or self.wf.get(True))["workflow_dispatch"]["inputs"]
        self.assertEqual(sorted(ent), ["que_publicar", "simular", "territorios"])


if __name__ == "__main__":
    unittest.main()
