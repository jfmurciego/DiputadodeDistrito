#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: prueba de la poda de R2 (T-145)
VERSIÓN: 1.1.0 · FECHA: 2026-11-23 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo; 1.1.0, T-443: árbol nuevo protegido y paquetes P10 de arc-e/ con su copia por edición)
FUNCIÓN: la poda verifica antes de borrar, no borra nada ante un desajuste, simula por defecto y se detiene al primer error.
"""
import csv
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import podar_r2 as pr  # noqa: E402

CAB = ["clave", "territorio", "run_id", "etapa", "tamano_bytes", "sha256", "motivo", "copia_que_conserva", "copia_clave", "copia_sha256"]
K1, K2, TOP = "x/1/ddd-state-1-M01.zip", "x/1/ddd-state-1-M07.zip", "x/1/ddd-state-1-M08.zip"


class Base(unittest.TestCase):
    def setUp(self):
        self.td = Path(tempfile.mkdtemp())
        self.lista = self.td / "l.csv"
        with self.lista.open("w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(CAB)
            w.writerow([K1, "x", "1", "M01", 10, "a1", "m", "c", TOP, "t8"])
            w.writerow([K2, "x", "1", "M07", 20, "a7", "m", "c", TOP, "t8"])
        self.man = self.td / "m.json"
        self.arts = {K1: {"sha256": "a1"}, K2: {"sha256": "a7"}, TOP: {"sha256": "t8"}}
        self.man.write_text(json.dumps({"schema": "s", "artefactos": self.arts}))
        self.r2 = {K1: "a1", K2: "a7", TOP: "t8"}
        self.borradas = []
        self.filas = pr.leer_lista(self.lista, hashlib.sha256(self.lista.read_bytes()).hexdigest())

    def borrar(self, k):
        self.borradas.append(k)
        self.r2.pop(k, None)

    def run_(self, ejecutar, entrada=True, borrar=None):
        return pr.podar(self.filas, self.man, self.r2.get, lambda t: entrada, borrar or self.borrar, ejecutar)


class Poda(Base):
    def test_lista_con_otro_sha_se_rechaza(self):
        with self.assertRaises(ValueError):
            pr.leer_lista(self.lista, "0" * 64)

    def test_clave_que_no_es_estado_se_rechaza(self):
        txt = self.lista.read_text().replace(K1, "x/1/ddd-minimo-1-M08.zip")
        self.lista.write_text(txt)
        with self.assertRaises(ValueError):
            pr.leer_lista(self.lista, hashlib.sha256(self.lista.read_bytes()).hexdigest())

    def test_simulacion_no_borra(self):
        inf = self.run_(False)
        self.assertEqual((inf["desajustes"], self.borradas), ([], []))
        self.assertEqual(set(json.loads(self.man.read_text())["artefactos"]), {K1, K2, TOP})

    def test_ejecutar_borra_y_actualiza_manifiesto(self):
        inf = self.run_(True)
        self.assertEqual(self.borradas, [K1, K2])
        self.assertEqual(inf["bytes_borrados"], 30)
        self.assertEqual(set(json.loads(self.man.read_text())["artefactos"]), {TOP})
        self.assertIn(TOP, self.r2)

    def test_un_desajuste_no_borra_nada(self):
        for mal in ({K2: "otro"}, {TOP: "otro"}):
            with self.subTest(mal=mal):
                self.setUp()
                self.r2.update(mal)
                inf = self.run_(True)
                self.assertEqual(self.borradas, [])
                self.assertTrue(inf["desajustes"])

    def test_copia_ausente_no_borra(self):
        del self.r2[TOP]
        inf = self.run_(True)
        self.assertEqual((self.borradas, {d["error"] for d in inf["desajustes"]}), ([], {"COPIA_SHA_R2_DISTINTO"}))

    def test_etapa_de_bateria_exige_entrada_minima(self):
        inf = self.run_(True, entrada=False)
        # K1 es M01 (exige entrada), K2 es M07 (no la exige): hay un desajuste y no se borra nada
        self.assertEqual(self.borradas, [])
        self.assertEqual([d["clave"] for d in inf["desajustes"]], [K1])

    def test_se_detiene_al_primer_error(self):
        def malo(k):
            raise RuntimeError("R2 caído")
        inf = self.run_(True, borrar=malo)
        self.assertIn("R2 caído", inf["error"])
        self.assertEqual(inf["borradas"], [])
        self.assertEqual(set(json.loads(self.man.read_text())["artefactos"]), {K1, K2, TOP})

    def test_borrado_no_efectivo_detiene(self):
        inf = self.run_(True, borrar=lambda k: None)
        self.assertIn("BORRADO_NO_EFECTIVO", inf["error"])
        self.assertEqual(inf["borradas"], [])


class Principal(Base):
    def test_main_sale_con_error_ante_desajuste_y_sin_borrar(self):
        import os
        from unittest import mock
        (self.td / "docs/ESTUDIOS/T145_PODA_R2").mkdir(parents=True)
        (self.td / pr.LISTA).write_bytes(self.lista.read_bytes())
        (self.td / "orchestracion").mkdir()
        (self.td / pr.ar.MANIFIESTO).write_bytes(self.man.read_bytes())
        self.r2[TOP] = "otro"
        sha = hashlib.sha256(self.lista.read_bytes()).hexdigest()
        env = {"R2_BUCKET": "b", "R2_ACCOUNT_ID": "a"}
        with mock.patch.dict(os.environ, env), mock.patch.object(
                pr, "clientes_r2", return_value=(self.r2.get, lambda t: True, self.borrar, lambda k: None)):
            rc = pr.main(["--root-dir", str(self.td), "--sha256-lista", sha, "--ejecutar"])
        self.assertEqual((rc, self.borradas), (1, []))

    def test_copia_de_otro_territorio_no_borra(self):
        for f in self.filas:
            f["copia_clave"] = "y/1/ddd-state-1-M08.zip"
        self.arts["y/1/ddd-state-1-M08.zip"] = {"sha256": "t8"}
        self.man.write_text(json.dumps({"schema": "s", "artefactos": self.arts}))
        self.r2["y/1/ddd-state-1-M08.zip"] = "t8"
        inf = self.run_(True)
        self.assertEqual(({d["error"] for d in inf["desajustes"]}, self.borradas), ({"COPIA_DE_OTRO_TERRITORIO"}, []))


PKG_A, PKG_B = "a" * 64, "b" * 64
P10_A, P10_B = f"arc-e/paquetes-p10/{PKG_A}.zip", f"arc-e/paquetes-p10/{PKG_B}.zip"
ED_A = "fuentes/por-territorio/nacionales/soria/2025/paquete.zip"
CITADOS = [{"territorio": "nac42", "edicion": "2025", "package_sha256": PKG_A, "clave": ED_A}]


class ArbolNuevo(unittest.TestCase):
    """T-443 (D-198): fuentes/, interno/ y mapas/ no se podan; arc-e/paquetes-p10/ solo con la copia por edición de cada paquete citado."""

    def lista(self, filas):
        td = Path(tempfile.mkdtemp())
        ruta = td / "l.csv"
        with ruta.open("w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(CAB)
            w.writerows(filas)
        return pr.leer_lista(ruta, hashlib.sha256(ruta.read_bytes()).hexdigest()), td

    def r2_con_copia(self):
        r2 = {P10_A: "za", P10_B: "zb", ED_A: "ea"}
        manifiestos = {"fuentes/por-territorio/nacionales/soria/2025/manifiesto.json": {"huella": PKG_A, "ficheros": {"paquete.zip": {"sha256": "ea"}}}}
        return r2, manifiestos

    def podar(self, filas, r2, manifiestos, citados=CITADOS):
        f, td = self.lista(filas)
        man = td / "m.json"
        man.write_text(json.dumps({"schema": "s", "artefactos": {}}))
        borradas = []
        inf = pr.podar(f, man, r2.get, lambda t: True, lambda k: (borradas.append(k), r2.pop(k)), True, citados, manifiestos.get)
        return inf, borradas

    def test_claves_del_arbol_nuevo_protegidas(self):
        for k in ("fuentes/ine/2023/seccionado.zip", "interno/estados/nacionales/soria/ultimo/minimo-m08.zip",
                  "mapas/nacionales/congreso-2023/soria/doble-vuelta.zip", "arc-e/fuentes/ine/seccionado_2023_abc.zip"):
            with self.subTest(k=k), self.assertRaisesRegex(ValueError, "CLAVE_PROTEGIDA|LISTA_INVALIDA"):
                self.lista([[k, "x", "1", "M01", 1, "h", "m", "c", "", ""]])

    def test_p10_citado_y_no_citado_se_borran_con_la_copia_por_edicion(self):
        r2, mans = self.r2_con_copia()
        inf, borradas = self.podar([[P10_A, "nac42", "", "P10", 5, "za", "m", "c", ED_A, "ea"],
                                    [P10_B, "", "", "P10", 5, "zb", "no citado (D-178)", "", "", ""]], r2, mans)
        self.assertEqual((inf["desajustes"], borradas), ([], [P10_A, P10_B]))
        self.assertIn(ED_A, r2)  # la copia por edición sigue

    def test_falta_una_copia_por_edicion_y_no_se_borra_ningun_paquete(self):
        r2, mans = self.r2_con_copia()
        citados = CITADOS + [{"territorio": "aut01", "edicion": "2025", "package_sha256": "c" * 64,
                              "clave": "fuentes/por-territorio/autonomicas/andalucia/2025/paquete.zip"}]
        inf, borradas = self.podar([[P10_B, "", "", "P10", 5, "zb", "m", "", "", ""]], r2, mans, citados)
        self.assertEqual(({d["error"] for d in inf["desajustes"]}, borradas), ({"ARC_E_P10_SIN_COPIA_POR_EDICION"}, []))

    def test_copia_por_edicion_de_otro_paquete_no_vale(self):
        r2, mans = self.r2_con_copia()
        mans["fuentes/por-territorio/nacionales/soria/2025/manifiesto.json"]["huella"] = "d" * 64
        inf, borradas = self.podar([[P10_B, "", "", "P10", 5, "zb", "m", "", "", ""]], r2, mans)
        self.assertEqual(({d["error"] for d in inf["desajustes"]}, borradas), ({"ARC_E_P10_SIN_COPIA_POR_EDICION"}, []))

    def test_zip_de_la_copia_con_otro_sha_no_vale(self):
        r2, mans = self.r2_con_copia()
        r2[ED_A] = "otro"
        inf, borradas = self.podar([[P10_B, "", "", "P10", 5, "zb", "m", "", "", ""]], r2, mans)
        self.assertEqual(({d["error"] for d in inf["desajustes"]}, borradas), ({"ARC_E_P10_SIN_COPIA_POR_EDICION"}, []))

    def test_p10_citado_sin_su_copia_en_la_fila(self):
        r2, mans = self.r2_con_copia()
        inf, borradas = self.podar([[P10_A, "nac42", "", "P10", 5, "za", "m", "", "", ""]], r2, mans)
        self.assertEqual(({d["error"] for d in inf["desajustes"]}, borradas), ({"P10_CITADO_SIN_SU_COPIA"}, []))

    def test_sin_citados_no_se_borra_ningun_paquete(self):
        r2, mans = self.r2_con_copia()
        inf, borradas = self.podar([[P10_B, "", "", "P10", 5, "zb", "m", "", "", ""]], r2, mans, citados=None)
        self.assertEqual(({d["error"] for d in inf["desajustes"]}, borradas), ({"ARC_E_P10_SIN_COPIA_POR_EDICION"}, []))

    def test_copia_en_interno_estados_del_mismo_territorio(self):
        k, ck = "soria/9/ddd-state-9-M07.zip", "interno/estados/nacionales/soria/ultimo/minimo-m08.zip"
        f, td = self.lista([[k, "soria", "9", "M07", 5, "s7", "m", "c", ck, "c8"]])
        man = td / "m.json"
        for territorio, esperado in (("soria", []), ("teruel", ["COPIA_DE_OTRO_TERRITORIO"])):
            man.write_text(json.dumps({"schema": "s", "artefactos": {k: {"sha256": "s7"}, ck: {"sha256": "c8", "territorio": territorio}}}))
            inf = pr.podar(f, man, {k: "s7", ck: "c8"}.get, lambda t: True, lambda x: None, False)
            self.assertEqual([d["error"] for d in inf["desajustes"]], esperado, territorio)

    def test_catalogo_real_cita_un_paquete_por_territorio_y_edicion(self):
        c = pr.paquetes_citados()
        self.assertTrue(c)
        self.assertEqual(len({(x["territorio"], x["edicion"]) for x in c}), len(c))
        self.assertTrue(all(x["clave"] and x["clave"].endswith("/paquete.zip") for x in c))
        aut01 = next(x for x in c if x["territorio"] == "aut01")
        self.assertEqual(aut01["clave"], "fuentes/por-territorio/autonomicas/andalucia/2025/paquete.zip")

    def test_entrada_minima_vale_en_la_ruta_por_edicion(self):
        ks = pr.claves_paquete_p10("aut01")
        self.assertEqual(ks[0], "fuentes/por-territorio/autonomicas/andalucia/2025/paquete.zip")
        self.assertTrue(ks[1].startswith("arc-e/paquetes-p10/"))


class ListaReal(unittest.TestCase):
    def test_lista_aprobada_es_coherente(self):
        filas = list(csv.DictReader((ROOT / pr.LISTA).open(encoding="utf-8", newline="")))
        self.assertEqual(len(filas), 234)
        self.assertEqual(sum(int(f["tamano_bytes"]) for f in filas), 26085405682)
        claves = {f["clave"] for f in filas}
        for f in filas:
            self.assertRegex(f["clave"], pr._ESTADO)
            self.assertNotIn(f["copia_clave"], claves)


if __name__ == "__main__":
    unittest.main()
