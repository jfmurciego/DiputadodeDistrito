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

    # T-443 (D-188/D-198): P75 escribe en interno/doble-vuelta/ (mapas/ solo lo escribe la publicación), ruta fija sin run en la clave, guarda por
    # el run del M08 en R2 y sha256 comprobado. Sustituye a los tests de T-418 «nunca sobrescribe» (claves `<carpeta>/<run>/…-p75-<run_p75>.zip`).
    CLAVE = "interno/doble-vuelta/nacionales/congreso-2023/alava/doble-vuelta.zip"
    MANIF = "interno/doble-vuelta/nacionales/congreso-2023/alava/manifiesto.json"

    def _r2(self):
        r2, runs = {}, {}  # clave → bytes, clave → metadato run

        def subir(k, ruta, h, run=None):
            r2[k] = Path(ruta).read_bytes()
            runs[k] = run
        sha_r2 = lambda k: hashlib.sha256(r2[k]).hexdigest() if k in r2 else None  # noqa: E731
        cab = lambda k: {"sha256": sha_r2(k), "run": runs.get(k), "bytes": len(r2[k])} if k in r2 else None  # noqa: E731
        return r2, runs, subir, sha_r2, cab

    def _ejecutar(self, subir, sha_r2, cab, run_p75="77"):
        with tempfile.TemporaryDirectory() as t, tempfile.TemporaryDirectory() as w, mock.patch.dict(os.environ, ENV):
            r = montar(Path(t), {RUN: paquete()})
            return p75.ejecutar(r, "nac01", "2023-07", Path(w), cp_de({RUN: paquete()}), subir, run_p75, existe=lambda k: True,
                                sha_r2=sha_r2, bucket="b", r2_cab=cab)

    def test_sube_el_zip_a_interno_con_run_y_manifiesto(self):
        r2, runs, subir, sha_r2, cab = self._r2()
        inf = self._ejecutar(subir, sha_r2, cab)
        f = inf["territorios"][0]
        self.assertEqual((f["estado"], f["clave_r2"], f["manifiesto_r2"], f["run_p75"]), ("OK", self.CLAVE, self.MANIF, "77"))
        self.assertEqual((hashlib.sha256(r2[self.CLAVE]).hexdigest(), runs[self.CLAVE]), (f["sha256_salida"], RUN))
        m = json.loads(r2[self.MANIF])
        self.assertEqual((m["run"], sorted(m["ficheros"])), (RUN, ["doble-vuelta.zip"]))
        self.assertEqual(m["ficheros"]["doble-vuelta.zip"]["sha256"], f["sha256_salida"])
        self.assertFalse(any(k.startswith("mapas/") for k in r2))  # D-198: mapas/ no lo escribe P75

    def test_mismo_run_sustituye_y_un_run_mayor_no_se_pisa(self):
        r2, runs, subir, sha_r2, cab = self._r2()
        r2[self.CLAVE], runs[self.CLAVE] = b"anterior", RUN
        self.assertEqual(self._ejecutar(subir, sha_r2, cab)["territorios"][0]["estado"], "OK")  # mismo M08: se recalcula
        self.assertNotEqual(r2[self.CLAVE], b"anterior")
        r2[self.CLAVE], runs[self.CLAVE] = b"de un M08 posterior", "999999"
        f = self._ejecutar(subir, sha_r2, cab)["territorios"][0]
        self.assertEqual(f["estado"], "SUPERADO")
        self.assertEqual(r2[self.CLAVE], b"de un M08 posterior")

    def test_sha_en_r2_distinto_tras_subir_falla(self):
        r2, runs, subir, _, cab = self._r2()
        f = self._ejecutar(subir, lambda k: "00" * 32, cab)["territorios"][0]  # control negativo: R2 no queda con el sha256 subido
        self.assertEqual(f["estado"], "SHA_R2_DISTINTO")
        self.assertNotIn("clave_r2", f)

    def test_informe_se_fusiona_por_territorio(self):
        ent = {"bloques": {"sha256": "b"}, "alias": {"sha256": "a"}}
        ant = {"eleccion": "2023-07", "run_p75": "1-1", "entradas": ent, "territorios": [
            {"territorio": "nac01", "estado": "OK", "run_p75": "1-1"}, {"territorio": "nac02", "estado": "OK", "run_p75": "1-1"}]}
        nue = {"eleccion": "2023-07", "run_p75": "2-1", "entradas": ent, "territorios": [
            {"territorio": "nac01", "estado": "OK", "run_p75": "2-1"}, {"territorio": "nac03", "estado": "COBERTURA_BAJA", "run_p75": "2-1"}]}
        f = p75.fusionar_informe(ant, nue)
        self.assertEqual([(x["territorio"], x["run_p75"]) for x in f["territorios"]], [("nac01", "2-1"), ("nac02", "1-1"), ("nac03", "2-1")])
        self.assertEqual((f["ok"], f["total"], f["run_p75"]), (2, 3, "2-1"))
        mal = dict(nue, territorios=[{"territorio": "nac02", "estado": "SIN_CSV_M07", "run_p75": "2-1"}])
        self.assertEqual(p75.fusionar_informe(ant, mal)["territorios"][1]["run_p75"], "1-1")  # un fallo no sustituye a una fila OK
        otro = dict(nue, entradas={"bloques": {"sha256": "x"}, "alias": {"sha256": "a"}})
        self.assertEqual([x["territorio"] for x in p75.fusionar_informe(ant, otro)["territorios"]], ["nac01", "nac03"])  # otros bloques: de nuevo

    def test_fila_ok_previa_con_zip_distinto_en_r2_no_se_conserva(self):
        ent = {"bloques": {"sha256": "b"}, "alias": {"sha256": "a"}}
        ant = {"eleccion": "2023-07", "entradas": ent, "territorios": [
            {"territorio": "nac01", "estado": "OK", "run_p75": "1-1", "clave_r2": "k1", "sha256_salida": "s1"}]}
        nue = {"eleccion": "2023-07", "run_p75": "2-1", "entradas": ent, "territorios": [{"territorio": "nac01", "estado": "SUPERADO", "run_p75": "2-1"}]}
        self.assertEqual(p75.fusionar_informe(ant, nue, lambda k: "s1")["territorios"][0]["run_p75"], "1-1")  # el ZIP sigue: se conserva
        self.assertEqual(p75.fusionar_informe(ant, nue, lambda k: "otro")["territorios"][0]["estado"], "SUPERADO")  # ya no casa: gana la nueva
        otro = dict(nue, entradas={"bloques": {"sha256": "x"}, "alias": {"sha256": "a"}}, territorios=[{"territorio": "nac02", "estado": "OK"}])
        self.assertEqual(p75.fusionar_informe(ant, otro)["huerfanos"], ["k1"])

    def test_el_codigo_de_salida_es_el_de_esta_ejecucion(self):
        """Revisión de 57f1f11 (2): un fallo nuevo no se esconde tras una fila OK anterior del informe fusionado."""
        ent = {"bloques": {"ruta": "b", "sha256": "b"}, "alias": {"ruta": "a", "sha256": "a"}}
        previo = {"eleccion": "2023-07", "run_p75": "1-1", "entradas": ent, "ok": 1, "total": 1, "territorios": [
            {"territorio": "nac01", "run": RUN, "estado": "OK", "run_p75": "1-1", "clave_r2": self.CLAVE, "sha256_salida": "s1"}]}
        nuevo = {"eleccion": "2023-07", "run_p75": "2-1", "entradas": ent, "ok": 0, "total": 1, "territorios": [
            {"territorio": "nac01", "run": RUN, "estado": "SIN_PAQUETE_EN_R2", "run_p75": "2-1", "sha256_salida": None}]}
        k_inf = "interno/doble-vuelta/nacionales/congreso-2023/informe-doble-vuelta.json"
        subidas = {}

        def subir(k, ruta, h, run=None):
            subidas[k] = Path(ruta).read_bytes()
        with mock.patch.dict(os.environ, {**ENV, "GITHUB_RUN_ID": "2", "GITHUB_RUN_ATTEMPT": "1"}), \
                mock.patch.object(p75, "ejecutar", lambda *a, **k: json.loads(json.dumps(nuevo))), \
                mock.patch.object(p75.ar, "r2_cliente", lambda b, c: (lambda k: "s1" if k == self.CLAVE else (hashlib.sha256(subidas[k]).hexdigest() if k in subidas else None), subir)), \
                mock.patch.object(p75.ar, "r2_cabecera", lambda b, c: (lambda k: {"run": "1"} if k == k_inf else None)), \
                mock.patch.object(p75, "r2_existe", lambda b, c: (lambda k: False)), \
                mock.patch.object(p75.fuente_r2, "_cp", lambda o, d, e=None: Path(d).write_text(json.dumps(previo))), \
                tempfile.TemporaryDirectory() as w:
            rc = p75.main(["--territorios", "nac01", "--salida", w])
        self.assertEqual(rc, 1)
        fusion = json.loads(subidas[k_inf])
        self.assertEqual((fusion["territorios"][0]["estado"], fusion["territorios"][0]["run_p75"]), ("OK", "1-1"))  # el ZIP previo sigue

    def test_carpeta_de_entrada_con_claves_nuevas_y_viejas(self):
        self.assertEqual(p75.carpeta_de_entrada(f"{LEG}/{RUN}/ddd-minimo-{RUN}-M08.zip", {}), LEG)
        self.assertEqual(p75.carpeta_de_entrada("interno/estados/nacionales/alava/ultimo/minimo-m08.zip", {"territorio": "nac01"}), "nac01")
        self.assertEqual(p75.clave_informe({"eleccion": "2023-07"}, "9-1"), "interno/doble-vuelta/nacionales/congreso-2023/informe-doble-vuelta.json")
        self.assertEqual(p75.clave_informe({"eleccion": "autonomicas"}, "9-1"), "interno/doble-vuelta/autonomicas/informe-doble-vuelta.json")

    def test_el_resumen_de_p70_imprime_la_clave_que_sube_p75(self):
        """Bloqueante 1 de la revisión de #988: el resumen del job no compone la clave por su cuenta; usa `clave_informe` de P75."""
        import yaml
        wf = yaml.safe_load((ROOT / ".github/workflows/p70-archivo.yml").read_text(encoding="utf-8"))
        run = next(x for x in wf["jobs"]["doble_vuelta_r2"]["steps"] if x.get("name", "").startswith("Calcular"))["run"]
        self.assertIn("clave_informe(", run)
        self.assertNotIn("INFORME_CLAVE=doble_vuelta/", run)

    def test_archivista_en_el_arbol_nuevo_sigue_valiendo(self):
        """El M08 archivado en `interno/estados/…` (archivista 1.2.0) se localiza por run y su territorio sale de la entrada."""
        with tempfile.TemporaryDirectory() as t, tempfile.TemporaryDirectory() as w, mock.patch.dict(os.environ, ENV):
            r = montar(Path(t), {})
            k = "interno/estados/nacionales/alava/ultimo/minimo-m08.zip"
            arts = {k: {"run_id": RUN, "artefacto": f"ddd-minimo-{RUN}-M08", "sha256": hashlib.sha256(paquete()).hexdigest(), "territorio": "nac01"}}
            (r / "orchestracion/archivo_r2.json").write_text(json.dumps({"artefactos": arts}), encoding="utf-8")

            def cp(origen, destino, extra=None):
                self.assertTrue(origen.endswith(k))
                Path(destino).write_bytes(paquete())
            inf = p75.ejecutar(r, "nac01", "2023-07", Path(w), cp)
        self.assertEqual(inf["territorios"][0]["estado"], "OK")

    def test_log_con_el_sha_del_informe_y_de_cada_zip(self):
        inf = {"territorios": [{"territorio": "nac01", "run": "1001", "sha256_salida": "ab" * 32, "clave_r2": "c/1001/z.zip"}]}
        self.assertEqual(p75.lineas_para_log(inf, "cd" * 32, "doble_vuelta/2023-07/9-1/INFORME.json"),
                         ["INFORME_CLAVE=doble_vuelta/2023-07/9-1/INFORME.json", "INFORME_SHA256=" + "cd" * 32,
                          "P75_ZIP territorio=nac01 run=1001 sha256=" + "ab" * 32 + " clave=c/1001/z.zip"])

    def test_log_imprime_las_cifras_por_territorio_con_votos_total(self):
        inf = {"territorios": [{"territorio": "aut08", "run": "7", "sha256_salida": "ab" * 32, "clave_r2": "k", "votos_total": 1070325,
                                "sin_casar_pct": 0.0, "sin_bloque_pct": 2.6}, {"territorio": "aut09", "run": "8", "estado": "NO_APLICA"}]}
        lineas = p75.lineas_para_log(inf, "cd" * 32, "k")
        self.assertIn("P75_CIFRAS territorio=aut08 votos_total=1070325 sin_casar_pct=0.0 sin_bloque_pct=2.6", lineas)
        self.assertEqual(sum(l.startswith("P75_CIFRAS") for l in lineas), 1)

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
        from tests._t379_2a import deshacer as sin_2a  # T-379 PR 2a: sin el entorno `registro`
        cls.wf = sin_2a("p70-archivo", yaml.safe_load((ROOT / ".github/workflows/p70-archivo.yml").read_text(encoding="utf-8")))
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
