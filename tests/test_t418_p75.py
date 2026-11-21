#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: P75 Doble vuelta desde R2 (T-418) con R2 simulado y un repositorio sintético
VERSIÓN: 1.0.0 · FECHA: 2026-11-19 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
FUNCIÓN: valores esperados a mano (distrito de DISENO T-409 §7 adaptado): éxito con salida determinista, sha256 distinto, paquete sin el CSV de M07,
  sin paquete, cobertura baja (elección distinta), selección de territorios y subida a R2 de los ZIP.
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
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "herramientas"))
import p75_doble_vuelta_r2 as p75  # noqa: E402

from ddd_core import territorio_ids  # noqa: E402

RUN = "1001"
LEG = territorio_ids.id_legacy("nac01")  # id legacy del registro del visor y carpeta del archivista en R2
VOTOS = ("district_id,party,votes,bloc\n"
         "0,PP-EU,60,\n0,SUMAR,40,\n"
         "1,PP-EU,30,\n1,SUMAR,28,\n1,PSE-EE (PSOE),22,\n1,VOX,15,\n1,XX,5,\n")
BLOQUES = ("eleccion,siglas,denominacion,bloque_propuesto,motivo\n2023-07,PP,PP,Patriotas,x\n2023-07,VOX,VOX,Patriotas,x\n"
           "2023-07,Podemos–Sumar,x,Izquierdas,x\n2023-07,PSOE,PSOE,Izquierdas,x\n2023-07,XX,XX,,x\n")
ALIAS = ("eleccion,id_fuente,partido_homologado,origen,fuente\n202307,PP-EU,PP,H,x\n202307,SUMAR,Podemos–Sumar,H,x\n"
         "202307,PSE-EE (PSOE),PSOE,H,x\n202307,VOX,VOX,H,x\n202307,XX,XX,H,x\n")


def paquete(con_csv=True, votos=VOTOS) -> bytes:
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        z.writestr("estado/cache/run_m08_distritos.geojson", "{}")
        if con_csv:
            z.writestr("estado/cache/run_m07_resultados_partido.csv", votos)
    return b.getvalue()


def montar(td: Path, paquetes: dict, territorios=(("nac01", RUN), (LEG, RUN), ("nac02", "1002"), ("aut01", "1003"))) -> Path:
    (td / "orchestracion").mkdir()
    (td / "configuracion").mkdir()
    prods = [{"kind": "canonical_m08", "territory_id": t, "run_id": r} for t, r in territorios]
    prods += [{"kind": "canonical_m08", "territory_id": "nac01", "run_id": "9999", "election_date": "2026-11-29"},  # run mayor de OTRA elección: se ignora
              {"kind": "canonical_m06", "territory_id": "nac03", "run_id": "5"}]
    (td / "orchestracion/publicaciones_visor.json").write_text(json.dumps({"products": prods}), encoding="utf-8")
    arts = {f"{LEG}/{r}/ddd-minimo-{r}-M08.zip": {"run_id": r, "artefacto": f"ddd-minimo-{r}-M08", "sha256": hashlib.sha256(b).hexdigest()}
            for r, b in paquetes.items()}
    (td / "orchestracion/archivo_r2.json").write_text(json.dumps({"schema": "ddd.archivo-r2/1.0", "artefactos": arts}), encoding="utf-8")
    (td / "configuracion/bloques_partidos_2026-11-17.csv").write_text(BLOQUES, encoding="utf-8")
    (td / "configuracion/alias_partidos_generales.csv").write_text(ALIAS, encoding="utf-8")
    return td


def cp_de(paquetes: dict):
    def cp(origen, destino, extra=None):
        run = origen.split("/")[-1].split("-")[2]
        if run not in paquetes:
            raise OSError("NoSuchKey")
        Path(destino).write_bytes(paquetes[run])
    return cp


ENV = {"R2_BUCKET": "b", "R2_ACCOUNT_ID": "a"}


class P75(unittest.TestCase):
    def correr(self, paquetes, pedidos="nac01", subir=None, eleccion="2023-07", manifiesto_extra=None, run_p75="77"):
        with tempfile.TemporaryDirectory() as t, tempfile.TemporaryDirectory() as w, mock.patch.dict(os.environ, ENV):
            r = montar(Path(t), manifiesto_extra if manifiesto_extra is not None else paquetes)
            inf = p75.ejecutar(r, pedidos, eleccion, Path(w), cp_de(paquetes), subir, run_p75)
            zips = {p.name: p.read_bytes() for p in Path(w).rglob("*.zip") if p.name.startswith("ddd-doble-vuelta")}
            return inf, zips

    def test_exito_con_valores_a_mano(self):
        inf, zips = self.correr({RUN: paquete()})
        f = inf["territorios"][0]
        self.assertEqual((f["estado"], f["trae_m07"], f["sin_casar_pct"], f["sin_bloque_pct"]), ("OK", True, 0.0, 2.5))  # XX: 5 de 200
        z = zipfile.ZipFile(io.BytesIO(zips[f"ddd-doble-vuelta-{RUN}.zip"]))
        self.assertEqual(sorted(z.namelist()), ["cobertura.json", "detalle.csv", "doble_vuelta.csv", "manifiesto.json"])
        filas = {(r["district_id"], r["escenario"]): r for r in csv.DictReader(io.StringIO(z.read("doble_vuelta.csv").decode()))}
        self.assertEqual(filas[("0", "dv_base")]["candidatura_ganadora"], "PP")  # 60 % en primera vuelta
        self.assertEqual(filas[("0", "dv_base")]["vuelta_decisiva"], "1")
        b = filas[("1", "dv_base")]  # PP 30 y SUMAR 28 finalistas; PSOE→SUMAR (50); VOX→PP (45); XX sin bloque: abstención
        self.assertEqual((b["candidatura_ganadora"], b["votos_a_2v"], b["votos_b_2v"], b["votos_abstencion"]), ("Podemos–Sumar", "45", "50", "5"))
        a = filas[("1", "dv_A")]  # Izquierdas 50 y Patriotas 45 (50 % no gana en primera)
        self.assertEqual((a["candidatura_ganadora"], a["vuelta_decisiva"], a["votos_abstencion"]), ("bloque:Izquierdas", "2", "5"))
        man = json.loads(z.read("manifiesto.json"))
        self.assertEqual(man["alias"]["ruta"], "alias_partidos_generales.csv")  # rutas relativas y estables

    def test_salida_determinista(self):
        a = self.correr({RUN: paquete()})[1]
        b = self.correr({RUN: paquete()})[1]
        self.assertEqual(a, b)

    def test_sha256_distinto(self):
        inf, _ = self.correr({RUN: paquete()}, manifiesto_extra={RUN: paquete(votos="otra cosa")})
        self.assertEqual(inf["territorios"][0]["estado"], "SHA_DISTINTO")

    def test_paquete_sin_el_csv_de_m07(self):
        inf, zips = self.correr({RUN: paquete(con_csv=False)})
        f = inf["territorios"][0]
        self.assertEqual((f["estado"], f["trae_m07"]), ("SIN_CSV_M07", False))
        self.assertEqual(zips, {})

    def test_sin_paquete_en_el_manifiesto(self):
        inf, _ = self.correr({RUN: paquete()}, manifiesto_extra={})
        self.assertEqual(inf["territorios"][0]["estado"], "SIN_PAQUETE_EN_R2")

    def test_cobertura_baja_no_calcula(self):
        inf, zips = self.correr({RUN: paquete(votos=VOTOS.replace("PP-EU", "OTRO").replace("SUMAR", "OTRO2"))})
        f = inf["territorios"][0]
        self.assertEqual(f["estado"], "COBERTURA_BAJA")
        self.assertGreater(f["sin_casar_pct"], p75.UMBRAL_SIN_CASAR)
        self.assertEqual(zips, {})

    def test_seleccion_de_territorios(self):
        with tempfile.TemporaryDirectory() as t:
            r = montar(Path(t), {})
            # solo Congreso (ámbito NAC), id nuevo, sin duplicar por el legacy, sin M06 y con el run de LA ELECCIÓN (no el 9999 de 2026)
            self.assertEqual(p75.territorios_con_m08(r), [("nac01", RUN), ("nac02", "1002")])
            self.assertEqual(p75.territorios_con_m08(r, LEG), [("nac01", RUN)])  # el id legacy vale
            for malo, causa in (("aut01", "P75_FUERA_DE_ALCANCE"), ("andalucia", "P75_FUERA_DE_ALCANCE"), ("nac99", "P75_TERRITORIO_INVALIDO"), ("nac03", "P75_SIN_M08_VIGENTE")):
                with self.assertRaisesRegex(ValueError, causa):
                    p75.territorios_con_m08(r, malo)

    def test_sube_el_zip_a_la_carpeta_del_paquete_de_entrada(self):
        subidas = []
        inf, _ = self.correr({RUN: paquete()}, subir=lambda k, ruta, h: subidas.append((k, Path(ruta).name, h)))
        # carpeta y run: los del archivista (legacy); el run de P75 entra en el nombre: objetos nuevos, nunca se sobrescribe
        self.assertEqual(subidas, [(f"{LEG}/{RUN}/ddd-doble-vuelta-{RUN}-p75-77.zip", f"ddd-doble-vuelta-{RUN}.zip", inf["territorios"][0]["sha256_salida"])])
        self.assertEqual(inf["run_p75"], "77")

    def test_nunca_sobrescribe_si_la_clave_ya_existe(self):
        subidas = []
        subir = lambda k, ruta, h: subidas.append(k)  # noqa: E731
        with tempfile.TemporaryDirectory() as t, tempfile.TemporaryDirectory() as w, mock.patch.dict(os.environ, ENV):
            r = montar(Path(t), {RUN: paquete()})
            inf = p75.ejecutar(r, "nac01", "2023-07", Path(w), cp_de({RUN: paquete()}), subir, "77", existe=lambda k: True)  # control negativo
            self.assertEqual((inf["territorios"][0]["estado"], subidas), ("CLAVE_YA_EXISTE", []))
            inf = p75.ejecutar(r, "nac01", "2023-07", Path(w), cp_de({RUN: paquete()}), subir, "77", existe=lambda k: False)
            self.assertEqual((inf["territorios"][0]["estado"], len(subidas)), ("OK", 1))

    def test_un_rerun_con_el_mismo_run_id_no_sobrescribe(self):
        r2 = {}  # R2 simulado: clave → ruta subida
        subir = lambda k, ruta, h: r2.update({k: h})  # noqa: E731
        for intento, esperado in (("1", "OK"), ("1", "CLAVE_YA_EXISTE"), ("2", "OK")):  # mismo run y mismo intento = clave repetida
            run_p75 = p75.run_p75_de_entorno({"GITHUB_RUN_ID": "500", "GITHUB_RUN_ATTEMPT": intento})
            with tempfile.TemporaryDirectory() as t, tempfile.TemporaryDirectory() as w, mock.patch.dict(os.environ, ENV):
                r = montar(Path(t), {RUN: paquete()})
                inf = p75.ejecutar(r, "nac01", "2023-07", Path(w), cp_de({RUN: paquete()}), subir, run_p75, existe=lambda k: k in r2)
            self.assertEqual(inf["territorios"][0]["estado"], esperado, intento)
        self.assertEqual(sorted(r2), [f"{LEG}/{RUN}/ddd-doble-vuelta-{RUN}-p75-500-1.zip", f"{LEG}/{RUN}/ddd-doble-vuelta-{RUN}-p75-500-2.zip"])

    def test_log_con_el_sha_del_informe_y_de_cada_zip(self):
        inf = {"territorios": [{"territorio": "nac01", "run": "1001", "sha256_salida": "ab" * 32, "clave_r2": "c/1001/z.zip"}]}
        self.assertEqual(p75.lineas_para_log(inf, "cd" * 32, "doble_vuelta/2023-07/9-1/INFORME.json"),
                         ["INFORME_CLAVE=doble_vuelta/2023-07/9-1/INFORME.json", "INFORME_SHA256=" + "cd" * 32,
                          "P75_ZIP territorio=nac01 run=1001 sha256=" + "ab" * 32 + " clave=c/1001/z.zip"])

    def test_resumen_del_workflow_imprime_el_sha_del_informe(self):
        import yaml
        wf = yaml.safe_load((ROOT / ".github/workflows/p70-archivo.yml").read_text(encoding="utf-8"))
        run = next(s for s in wf["jobs"]["doble_vuelta_r2"]["steps"] if s.get("name", "").startswith("Calcular"))["run"]
        self.assertIn("INFORME_SHA256=", run)
        self.assertIn("INFORME_CLAVE=", run)

    def test_run_p75_lleva_el_intento(self):
        self.assertEqual(p75.run_p75_de_entorno({"GITHUB_RUN_ID": "9", "GITHUB_RUN_ATTEMPT": "3"}), "9-3")
        self.assertEqual(p75.run_p75_de_entorno({"GITHUB_RUN_ID": "9"}), "9-1")
        self.assertRegex(p75.run_p75_de_entorno({}), r"^\d{8}T\d{6}Z$")

    def test_subir_nuevo_y_r2_existe(self):
        subidas = []
        with self.assertRaisesRegex(FileExistsError, "P75_CLAVE_YA_EXISTE"):
            p75.subir_nuevo(lambda *a: subidas.append(a), lambda k: True, "k", Path("x"), "h")
        self.assertEqual(subidas, [])
        p75.subir_nuevo(lambda *a: subidas.append(a), lambda k: False, "k", Path("x"), "h")
        self.assertEqual(len(subidas), 1)

        def head(rc, err):
            return mock.Mock(returncode=rc, stdout="{}", stderr=err)
        for rc, err, esperado in ((0, "", True), (254, "An error occurred (404) when calling the HeadObject operation: Not Found", False)):
            with mock.patch("p75_doble_vuelta_r2.subprocess.run", return_value=head(rc, err)):
                self.assertIs(p75.r2_existe("b", "a")("clave"), esperado)
        # control negativo: «404» dentro de un id de cuenta + fallo de conexión NO es «no existe»: debe propagar, nunca devolver False
        conexion = "Could not connect to the endpoint URL: \"https://a1b2404c3d4e5f60.r2.cloudflarestorage.com/bucket/clave\""
        with mock.patch("p75_doble_vuelta_r2.subprocess.run", return_value=head(255, conexion)), \
                mock.patch("p75_doble_vuelta_r2.ar._dormir", lambda s: None):
            with self.assertRaises(Exception):
                p75.r2_existe("b", "a")("clave")
        with mock.patch("p75_doble_vuelta_r2.subprocess.run", return_value=head(254, "An error occurred (NoSuchKey) when calling the HeadObject operation")):
            self.assertIs(p75.r2_existe("b", "a")("clave"), False)
        with mock.patch("p75_doble_vuelta_r2.subprocess.run", return_value=head(255, "AccessDenied")), \
                mock.patch("p75_doble_vuelta_r2.ar._dormir", lambda s: None):
            with self.assertRaises(Exception):  # otro fallo: nunca se asume que no existe
                p75.r2_existe("b", "a")("clave")

    def test_la_carpeta_de_r2_debe_ser_la_del_territorio(self):
        with tempfile.TemporaryDirectory() as t, tempfile.TemporaryDirectory() as w, mock.patch.dict(os.environ, ENV):
            r = montar(Path(t), {RUN: paquete()})
            m = json.loads((r / "orchestracion/archivo_r2.json").read_text())
            m["artefactos"] = {k.replace(LEG, "otro_territorio"): v for k, v in m["artefactos"].items()}
            (r / "orchestracion/archivo_r2.json").write_text(json.dumps(m), encoding="utf-8")
            inf = p75.ejecutar(r, "nac01", "2023-07", Path(w), cp_de({RUN: paquete()}))
            self.assertEqual(inf["territorios"][0]["estado"], "CARPETA_NO_ES_DEL_TERRITORIO")

    def test_un_territorio_malo_no_para_a_los_demas(self):
        inf, _ = self.correr({RUN: paquete()}, pedidos="nac01,nac02")
        self.assertEqual([f["estado"] for f in inf["territorios"]], ["OK", "SIN_PAQUETE_EN_R2"])  # M08 vigente que no está en R2: falla y se informa
        self.assertEqual((inf["ok"], inf["total"]), (1, 2))


class Workflow(unittest.TestCase):
    """P75 en p70-archivo.yml: solo lectura sobre git, un solo escritor en R2, sin entradas nuevas y el resto de acciones intactas."""

    @classmethod
    def setUpClass(cls):
        import yaml
        cls.wf = yaml.safe_load((ROOT / ".github/workflows/p70-archivo.yml").read_text(encoding="utf-8"))
        f = ROOT / "tests/fixtures/t418_workflows/p70-archivo_1.0.0.yml"  # copia congelada (en CI no hay legacy/)
        assert f.is_file(), f
        cls.antes = yaml.safe_load(f.read_text(encoding="utf-8"))

    def test_job_de_solo_lectura_con_un_escritor_en_r2(self):
        j = self.wf["jobs"]["doble_vuelta_r2"]
        self.assertEqual(j["permissions"], {"contents": "read"})
        self.assertEqual(j["concurrency"]["group"], "archivar-artefactos-r2")
        self.assertEqual(j["if"], "${{ inputs.accion == 'P75 Doble vuelta desde R2' }}")
        run = next(s for s in j["steps"] if s.get("name", "").startswith("Calcular"))["run"]
        for prohibido in ("git push", "registrar_en_main", "gh api", "inputs."):
            self.assertNotIn(prohibido, run)  # las entradas llegan por env, no interpoladas en el script
        self.assertIn("p75_doble_vuelta_r2.py", run)

    def test_sin_entradas_nuevas(self):
        ent = (self.wf.get("on") or self.wf.get(True))["workflow_dispatch"]["inputs"]
        self.assertEqual(sorted(ent), ["accion", "eleccion", "simular", "territorios"])
        self.assertEqual(ent["accion"]["options"][-1], "P75 Doble vuelta desde R2")
        for k in ("territorios", "eleccion"):
            self.assertIn("P75", ent[k]["description"])
        self.assertIn("todos los nac", ent["territorios"]["description"])

    def test_las_demas_acciones_no_cambian(self):
        import copy
        n = copy.deepcopy(self.wf)
        n["jobs"].pop("doble_vuelta_r2")
        (n.get("on") or n.get(True))["workflow_dispatch"]["inputs"]["accion"]["options"].remove("P75 Doble vuelta desde R2")
        # T-420b (P70 1.1.2): P74 `listar` cambia solo su llamada (--duplicados --json) y suma el paso de artefacto; todo lo demás, idéntico.
        # Su detalle lo fija tests/test_t420b_p74_duplicados.py.
        listar = n["jobs"].pop("listar")
        antes = copy.deepcopy(self.antes)
        antes_listar = antes["jobs"].pop("listar")
        self.assertEqual(n["jobs"], antes["jobs"])
        self.assertEqual({k: v for k, v in listar.items() if k != "steps"}, {k: v for k, v in antes_listar.items() if k != "steps"})
        self.assertEqual(listar["steps"][0], antes_listar["steps"][0])
        self.assertEqual(listar["steps"][1]["env"], antes_listar["steps"][1]["env"])
        # T-432 (P70 1.1.4) y T-437 (1.1.5): dos pasos más en total además de la subida de duplicados: subida del inventario CSV y su impresión en el log (+3).
        self.assertEqual(len(listar["steps"]), len(antes_listar["steps"]) + 3)
        self.assertEqual("Imprimir el inventario en el log", listar["steps"][-1]["name"])
        extra = [s for s in listar["steps"][2:] if str(s.get("uses", "")).startswith("actions/upload-artifact@")]
        self.assertEqual(["p74-duplicados-${{ github.run_id }}", "p74-inventario-${{ github.run_id }}"], [s["with"]["name"] for s in extra])


if __name__ == "__main__":
    unittest.main()
