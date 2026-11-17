# -*- coding: utf-8 -*-
"""T-399 (D-126/D-128): secciones del seccionado sin población en la tabla → rellenadas con el Atlas del año más cercano y ajuste municipal.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-17 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
CAMBIOS: 1.0.0: fichero nuevo.
MOTIVO: T-399 (D-156). Atlas, tabla y seccionado sintéticos (valores esperados escritos a mano, no recalculados); sin red.
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "herramientas"))
sys.path.insert(0, str(ROOT / "tests"))
import contrato_historico_epoca as che  # noqa: E402
from test_t365_historico_epoca import BASE, _contrato_sintetico, _sha  # noqa: E402

A, B = "2200101001", "2200101002"      # con población (dato), municipio 22001
N1, N2 = "2200101003", "2200101004"    # del seccionado, sin población en la tabla
S = "2200201001"                       # municipio 22002: sin ningún dato en el Atlas
ATLAS = {2015: {N1: 60, N2: 40, S: "."}, 2016: {N1: 70, N2: "", S: ""}, 2020: {N2: 45}}


class ValorAnioCercano(unittest.TestCase):
    def test_mas_cercano_empate_el_anterior_y_sin_dato(self):
        self.assertEqual(che.valor_anio_cercano(N1, 2011, ATLAS), (60, 2015))   # 2015 es el más cercano a 2011
        self.assertEqual(che.valor_anio_cercano(N1, 2018, {2016: {N1: 5}, 2020: {N1: 9}}), (5, 2016))  # empate 2016/2020: el anterior
        self.assertEqual(che.valor_anio_cercano(N2, 2019, ATLAS), (45, 2020))   # «» de 2016 no es dato
        self.assertEqual(che.valor_anio_cercano(S, 2011, ATLAS), (None, None))  # «.» y «» no son dato: nunca 0


class RellenarSinPoblacion(unittest.TestCase):
    POB = {A: {"poblacion": 100, "origen": "dato"}, B: {"poblacion": 200, "origen": "dato"}}  # suma con dato: 300

    def _r(self, total):
        return che.rellenar_sin_poblacion([N1, N2], self.POB, ATLAS, 2011, {"22001": total})

    def test_ajuste_proporcional_al_total_municipal(self):
        r = self._r(450)   # residuo 150; Atlas 60+40 = 100 → ×1,5
        self.assertEqual([(x["seccion"], x["poblacion"], x["poblacion_atlas"], x["anio_atlas"], x["ajuste"]) for x in r["rellenadas"]],
                         [(N1, 90, 60, 2015, "ajustada"), (N2, 60, 40, 2015, "ajustada")])
        c = r["cuadre"][0]
        self.assertEqual((c["estado"], c["residuo"], c["rellenado_final"], c["suma_municipio"], c["exceso_sobre_censo"]), ("ajustado", 150, 150, 450, 0))

    def test_control_negativo_sin_ajuste(self):
        r = self._r(400)   # residuo 100 = Atlas: cuadra, sin tocar
        self.assertEqual([(x["poblacion"], x["ajuste"]) for x in r["rellenadas"]], [(60, "cuadra"), (40, "cuadra")])
        r = self._r(300)   # residuo 0: conserva el valor del Atlas (nunca 0) y declara el exceso
        self.assertEqual([(x["poblacion"], x["ajuste"]) for x in r["rellenadas"]], [(60, "sin_ajuste_municipal"), (40, "sin_ajuste_municipal")])
        self.assertEqual((r["cuadre"][0]["estado"], r["cuadre"][0]["exceso_sobre_censo"]), ("aviso_residuo_no_positivo", 100))
        r = self._r(250)   # residuo negativo: igual
        self.assertEqual([x["poblacion"] for x in r["rellenadas"]], [60, 40])
        r = che.rellenar_sin_poblacion([N1], self.POB, ATLAS, 2011, {})  # municipio sin total oficial
        self.assertEqual((r["rellenadas"][0]["poblacion"], r["cuadre"][0]["estado"]), (60, "aviso_sin_total_municipal"))

    def test_sin_dato_en_ningun_anio_no_se_inventa(self):
        r = che.rellenar_sin_poblacion([N1, S], self.POB, ATLAS, 2011, {"22001": 450, "22002": 10})
        self.assertEqual(r["sin_dato"], [S])
        self.assertEqual([x["seccion"] for x in r["rellenadas"]], [N1])   # S no aparece con 0
        self.assertEqual({x["municipio"]: x["estado"] for x in r["cuadre"]}["22002"], "aviso_sin_dato")


class AplicarRelleno(unittest.TestCase):
    def test_anade_con_origen_y_no_pisa_filas(self):
        pob = {A: {"poblacion": 100, "origen": "dato"}}
        out = che.aplicar_relleno(pob, [{"seccion": N1, "poblacion": 90}])
        self.assertEqual(out[N1], {"poblacion": 90, "origen": "rellenada_año_cercano"})
        self.assertNotIn(N1, pob)
        with self.assertRaises(SystemExit) as cm:
            che.aplicar_relleno(pob, [{"seccion": A, "poblacion": 1}])
        self.assertIn("RELLENADA_CON_FILA", str(cm.exception))


class MaterializarConRelleno(unittest.TestCase):
    def _arbol(self, d: Path, declarar: bool, estado: str = "LISTA"):
        import yaml
        root, fuentes = d / "root", d / "fuentes"
        (root / "territorios/nac22/config").mkdir(parents=True)
        fuentes.mkdir()
        base = root / "territorios/nac22/config/nac22_2025.yaml"
        base.write_text(yaml.safe_dump(BASE), encoding="utf-8")
        (fuentes / "seccionado_2020.zip").write_bytes(b"zip")
        (fuentes / "tabla.csv").write_text("elección,sección,población,origen,año_fuente_relleno\n"
                                           "2019-11,2200101001,100,dato,\n2019-11,2200101002,200,dato,\n", encoding="utf-8")
        c = _contrato_sintetico(_sha(fuentes / "tabla.csv"), _sha(base), _sha(fuentes / "seccionado_2020.zip"), "d" * 64)
        p = c["provincias"]["22"]
        p["estado"] = estado
        p["poblacion"].update({"secciones_sin_seccionado": [], "secciones": 3, "total": 390})
        if declarar:
            p["poblacion"]["sin_poblacion_resuelto"] = {"rellenadas": [{"seccion": N1, "poblacion": 90, "poblacion_atlas": 60, "anio_atlas": 2015,
                                                                       "ajuste": "ajustada"}]}
        cpath = root / "contrato.json"
        cpath.write_text(json.dumps(c), encoding="utf-8")
        return root, fuentes, cpath, mock.patch.object(che, "_secciones_seccionado", return_value={A, B, N1})

    def test_rellenada_declarada_materializa_con_su_origen(self):
        with tempfile.TemporaryDirectory() as d:
            root, fuentes, cpath, parche = self._arbol(Path(d), True)
            with parche:
                out = che.materializar("2019-11", "nac22", fuentes, root, cpath)
            import yaml
            cfg = yaml.safe_load(out.read_text(encoding="utf-8"))
            pob = root / cfg["io"]["input"]["population_cip"]["paths"][0]
            self.assertEqual(pob.read_text(encoding="utf-8").splitlines()[1:],
                             ["2020,2200101001,100,dato", "2020,2200101002,200,dato", "2020,2200101003,90,rellenada_año_cercano"])

    def test_control_negativo_sin_declarar_sigue_fallando(self):
        with tempfile.TemporaryDirectory() as d:
            root, fuentes, cpath, parche = self._arbol(Path(d), False)
            with parche, self.assertRaises(SystemExit) as cm:
                che.materializar("2019-11", "nac22", fuentes, root, cpath)
            self.assertIn("CASADO_POBLACION_SECCIONADO", str(cm.exception))
            self.assertIn("sin población 1", str(cm.exception))

    def test_provincia_bloqueada_por_relleno_no_materializa(self):
        with tempfile.TemporaryDirectory() as d:
            root, fuentes, cpath, parche = self._arbol(Path(d), True, estado="BLOQUEADA_RELLENO")
            with parche, self.assertRaises(SystemExit) as cm:
                che.materializar("2019-11", "nac22", fuentes, root, cpath)
            self.assertIn("PROVINCIA_NO_LISTA", str(cm.exception))


class SeccionadoDe2011(unittest.TestCase):
    """D-156: 2011-11 usa la cartografía del Censo 2011; el resto de elecciones, el seccionado INE de su año."""

    CENSO_SHA = "d0151e0cc126695933bc30a922c803ab09af03fdfb622238b22f769c7a883acc"  # SHA256SUMS de T-357 (literal, no recalculado)

    def test_eleccion_2011_propia_y_control_negativo(self):
        e = che._eleccion("2011-11")
        self.assertEqual((e["seccionado"], e["seccionado_fichero"]), (2011, "cartografia_censo2011_nacional.zip"))
        self.assertTrue(e["seccionado_propio"]["origen_url"].endswith("/censos2011_datos/cartografia_censo2011_nacional.zip"))
        for el, anio in (("2015-12", 2015), ("2016-06", 2016), ("2019-04", 2019), ("2019-11", 2020)):
            x = che._eleccion(el)
            self.assertEqual((x["seccionado"], x["seccionado_fichero"], x["seccionado_propio"]), (anio, f"seccionado_{anio}.zip", None))

    def test_contrato_2011_11(self):
        c = json.loads(che.ruta_contrato("2011-11").read_text(encoding="utf-8"))
        self.assertEqual((c["seccionado"]["fichero"], c["seccionado"]["anio"], c["seccionado"]["sha256"], c["seccionado"]["r2_clave"]),
                         ("cartografia_censo2011_nacional.zip", 2011, self.CENSO_SHA, None))
        self.assertIn("D-156", c["seccionado"]["decision"])
        self.assertIsNone(c["poblacion"]["total_municipal_oficial"]["fuente"])  # sin tabla oficial: no se ajusta y queda declarado
        for cpro, p in c["provincias"].items():
            with self.subTest(cpro=cpro):
                self.assertNotIn("sin_seccionado_resuelto", p["poblacion"])  # con el seccionado del Censo toda sección de la tabla tiene geometría
                self.assertEqual(p["poblacion"]["secciones_sin_seccionado"], [])
                r = p["poblacion"].get("sin_poblacion_resuelto")
                if r:  # ningún total oficial: todas sin ajuste municipal
                    self.assertTrue(all(x["ajuste"] == "sin_ajuste_municipal" and x["poblacion"] == x["poblacion_atlas"] for x in r["rellenadas"]))
        self.assertEqual(sum(len(p["poblacion"].get("sin_poblacion_resuelto", {}).get("rellenadas", [])) for p in c["provincias"].values()), 41)
        self.assertEqual(c["provincias"]["22"]["estado"], "LISTA")
        self.assertEqual({k for k, p in c["provincias"].items() if p["estado"] != "LISTA"}, {"27", "36"})  # sin dato en ningún año (declarado)

    def test_otros_contratos_sin_relleno(self):
        for e in ("2015-12", "2016-06", "2019-04", "2019-11"):
            c = json.loads(che.ruta_contrato(e).read_text(encoding="utf-8"))
            self.assertNotEqual(c["seccionado"]["fichero"], "cartografia_censo2011_nacional.zip")
            self.assertFalse(any("sin_poblacion_resuelto" in p["poblacion"] for p in c["provincias"].values()), e)


class ExcepcionesVotosD156(unittest.TestCase):
    """D-156 (A): topes absolutos de votos sin asignar en 13 provincias de 2011-11; control negativo (un voto más falla; otra provincia no entra)."""

    TOPES = {"15": 3008, "21": 489, "22": 418, "29": 1831, "31": 620, "32": 473, "34": 607, "35": 477, "37": 533, "41": 2184, "43": 838,
             "45": 457, "47": 499}  # literal: votos fuera del seccionado del Censo 2011 medidos con el Observatorio (votos_fuera_del_seccionado.csv)

    def _c(self):
        return json.loads(che.ruta_contrato("2011-11").read_text(encoding="utf-8"))

    def test_contrato_declara_las_13_con_su_fuente(self):
        ex = self._c()["puerta"]["excepciones_votos_sin_asignar"]
        self.assertEqual(ex["topes"], self.TOPES)
        self.assertEqual(ex["fuente_sha256"], _sha(ROOT / ex["fuente"]))
        self.assertIn("no se asignan a su sección", ex["decision"])
        for e in ("2015-12", "2016-06", "2019-04", "2019-11"):  # solo 2011-11
            self.assertNotIn("excepciones_votos_sin_asignar", json.loads(che.ruta_contrato(e).read_text(encoding="utf-8"))["puerta"])
        self.assertEqual(che.excepciones_votos("2019-11"), None)

    def test_excepciones_salen_del_csv_y_solo_superan_el_tope_general(self):
        import csv
        with open(ROOT / che.VOTOS_FUERA_CSV, encoding="utf-8", newline="") as f:
            filas = list(csv.DictReader(f))
        self.assertEqual(len(filas), 52)
        sup = {x["provincia"] for x in filas if int(x["perdidos_con_censo2011"]) * 1000 > int(x["votos_validos_observatorio"])}
        self.assertEqual(sup, set(self.TOPES))
        self.assertEqual(che.excepciones_votos("2011-11")["topes"], self.TOPES)

    def test_puerta_tope_exacto_pasa_un_voto_mas_falla_y_otra_provincia_no_entra(self):
        c = self._c()
        for cpro, tope in self.TOPES.items():
            k = c["provincias"][cpro]["K"]
            rec = {"status": "PASS_WITH_DECLARED_EXCEPTIONS", "ddd_unassigned_votes": tope, "source_votes": 10_000_000}
            self.assertEqual(che.puerta(c, cpro, rec, {"ok": True}, k)["estado"], "PASS", cpro)
            self.assertEqual(che.puerta(c, cpro, {**rec, "ddd_unassigned_votes": tope + 1}, {"ok": True}, k)["estado"], "FAIL", cpro)
        # una provincia sin excepción (28) sigue con el tope general del 0,1 %: 2.082 votos de 3.326.413 (0,063 %) pasan, 3.400 (0,102 %) no
        k28 = c["provincias"]["28"]["K"]
        rec = {"status": "PASS", "ddd_unassigned_votes": 2082, "source_votes": 3326413}
        self.assertEqual(che.puerta(c, "28", rec, {"ok": True}, k28)["estado"], "PASS")
        self.assertEqual(che.puerta(c, "28", {**rec, "ddd_unassigned_votes": 3400}, {"ok": True}, k28)["estado"], "FAIL")
        # las D-70 antiguas (hc.D70, medidas con el seccionado 2012) ya no valen en 2011-11: 03 con 1.877 votos de 876.076 (0,214 %) falla
        rec = {"status": "PASS_WITH_DECLARED_EXCEPTIONS", "ddd_unassigned_votes": 1877, "source_votes": 876076}
        self.assertEqual(che.puerta(c, "03", rec, {"ok": True}, c["provincias"]["03"]["K"])["estado"], "FAIL")
        # control: sin la declaración del contrato (comportamiento anterior) 03 pasaba por hc.D70
        sin = {**c, "puerta": {k: v for k, v in c["puerta"].items() if k != "excepciones_votos_sin_asignar"}}
        self.assertEqual(che.puerta(sin, "03", rec, {"ok": True}, c["provincias"]["03"]["K"])["estado"], "PASS")


class ContratosVersionados(unittest.TestCase):
    ELEC = ("2011-11", "2015-12", "2016-06", "2019-04", "2019-11")

    def test_coherencia_del_relleno_en_cada_contrato(self):
        for e in self.ELEC:
            c = json.loads(che.ruta_contrato(e).read_text(encoding="utf-8"))
            self.assertEqual(c["poblacion"]["regla_sin_poblacion"], che.METODO_SIN_POBLACION)
            for cpro, p in c["provincias"].items():
                pb, r = p["poblacion"], p["poblacion"].get("sin_poblacion_resuelto")
                with self.subTest(e=e, cpro=cpro):
                    if not r:
                        continue
                    self.assertEqual(r["habitantes_rellenados"], sum(x["poblacion"] for x in r["rellenadas"]))
                    self.assertEqual(r["habitantes_atlas"], sum(x["poblacion_atlas"] for x in r["rellenadas"]))
                    self.assertTrue(all(x["poblacion"] > 0 and x["seccion"][:2] == cpro for x in r["rellenadas"]))
                    self.assertTrue(set(r["sin_dato"]) <= set(pb["secciones_sin_dato"]))
                    if r["sin_dato"]:
                        self.assertEqual(p["estado"], "BLOQUEADA_SIN_DATO")  # sin dato en ningún año: no se inventa
                    # el relleno cuenta como estimado: si pasa del 1 % la provincia no es LISTA (D-126)
                    if r["habitantes_rellenados"] * 100 > pb["total"]:
                        self.assertNotEqual(p["estado"], "LISTA")

    def test_informe_coincide_con_los_contratos(self):
        prov, mun = che.informe_sin_poblacion()
        n = 0
        for e in self.ELEC:
            c = json.loads(che.ruta_contrato(e).read_text(encoding="utf-8"))
            n += sum(len((p["poblacion"].get("sin_poblacion_resuelto") or {}).get("rellenadas", [])) for p in c["provincias"].values())
        self.assertEqual(sum(f["secciones_rellenadas"] for f in prov), n)
        self.assertEqual(sum(f["secciones_rellenadas"] for f in mun), n)


if __name__ == "__main__":
    unittest.main()
