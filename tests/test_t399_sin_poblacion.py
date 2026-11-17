# -*- coding: utf-8 -*-
"""T-399 (D-126/D-128): secciones del seccionado sin población en la tabla → rellenadas con el Atlas del año más cercano y ajuste municipal.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-17 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
CAMBIOS: 1.0.0: fichero nuevo.
MOTIVO: T-399 (D-158 B'). Atlas, tabla y seccionado sintéticos (valores esperados escritos a mano, no recalculados); sin red.
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

try:
    from shapely.geometry import box
except ImportError:  # pragma: no cover
    box = None

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


@unittest.skipIf(box is None, "sin shapely")
class RepartirMadres(unittest.TestCase):
    """D-158 (B'): la población de la madre se reparte entre madre e hijas con el Atlas; se conservan los totales."""

    M, H1, H2 = "2200101001", "2200101003", "2200101004"
    CENSO = {M: box(0, 0, 10, 10), "2200101002": box(10, 0, 20, 10)} if box else {}
    POB = {M: {"poblacion": 1000, "origen": "dato"}, "2200101002": {"poblacion": 500, "origen": "dato"}}
    ATLAS = {2015: {M: 600, "2200101003": 300, "2200101004": 100, "2200101002": 500}}

    def test_reparto_conserva_el_total_y_marca_madre_e_hijas(self):
        geo = {self.H1: box(0, 0, 5, 10), self.H2: box(5, 0, 10, 10)}  # hijas dentro de la madre
        r = che.repartir_madres([self.H1, self.H2], self.POB, geo, self.CENSO, self.ATLAS, 2011)
        self.assertEqual(r["sin_madre"], []) 
        self.assertEqual(r["sin_dato"], [])
        (x,) = r["repartos"]
        self.assertEqual((x["madre"], x["poblacion_censo_madre"]), (self.M, 1000))
        # 600:300:100 sobre 1.000 = 600, 300, 100 (valores escritos a mano)
        self.assertEqual([(y["seccion"], y["rol"], y["poblacion"]) for y in x["miembros"]],
                         [(self.M, "madre", 600), (self.H1, "hija", 300), (self.H2, "hija", 100)])
        self.assertEqual(sum(y["poblacion"] for y in x["miembros"]), 1000)
        # el reparto reescala: Atlas 60/30/10 sobre 1.000 → 600/300/100 con restos mayores
        atlas = {2015: {self.M: 61, self.H1: 30, self.H2: 9}}
        r = che.repartir_madres([self.H1, self.H2], self.POB, geo, self.CENSO, atlas, 2011)
        self.assertEqual([y["poblacion"] for y in r["repartos"][0]["miembros"]], [610, 300, 90])

    def test_solape_minimo_y_control_negativo(self):
        # hija con el 60 % de su área en la madre → madre; con el 40 % → sin madre (se rellenará con el Atlas); fuera de todo → sin madre
        geo = {self.H1: box(4, 0, 14, 10), "2200101005": box(6, 0, 16, 10), "2200101006": box(100, 0, 110, 10)}
        atlas = {2015: {self.M: 600, self.H1: 300, "2200101005": 100, "2200101006": 50}}
        solo_m = {self.M: self.POB[self.M]}  # la otra sección del Censo no tiene fila: no puede ser madre
        r = che.repartir_madres(sorted(geo), solo_m, geo, self.CENSO, atlas, 2011)
        self.assertEqual([x["madre"] for x in r["repartos"]], [self.M])
        self.assertEqual([y["seccion"] for y in r["repartos"][0]["miembros"]], [self.M, self.H1])
        self.assertEqual(r["sin_madre"], ["2200101005", "2200101006"])
        # la madre debe ser de la misma provincia y con población: una sección del Censo sin fila en la tabla no cuenta
        r = che.repartir_madres([self.H1], {"2200101002": self.POB["2200101002"]}, {self.H1: box(0, 0, 5, 10)}, self.CENSO, atlas, 2011)
        self.assertEqual((r["repartos"], r["sin_madre"]), ([], [self.H1]))

    def test_miembro_sin_dato_deja_las_hijas_sin_dato(self):
        geo = {self.H1: box(0, 0, 5, 10)}
        atlas = {2015: {self.M: 600, self.H1: "."}}
        r = che.repartir_madres([self.H1], self.POB, geo, self.CENSO, atlas, 2011)
        self.assertEqual((r["repartos"], r["sin_dato"]), ([], [self.H1]))  # nunca 0 ni inventado

    def test_aplicar_reparto_y_fallos_cerrados(self):
        x = {"madre": self.M, "poblacion_censo_madre": 1000,
             "miembros": [{"seccion": self.M, "rol": "madre", "poblacion": 700}, {"seccion": self.H1, "rol": "hija", "poblacion": 300}]}
        out = che.aplicar_reparto(self.POB, [x])
        self.assertEqual((out[self.M], out[self.H1]), ({"poblacion": 700, "origen": "repartida_madre"}, {"poblacion": 300, "origen": "repartida_hija"}))
        self.assertEqual(self.POB[self.M]["poblacion"], 1000)  # no muta la entrada
        for malo, msg in (({**x, "poblacion_censo_madre": 999}, "REPARTO_MADRE_POBLACION_DISTINTA"),
                          ({**x, "miembros": [{**x["miembros"][0], "poblacion": 701}, x["miembros"][1]]}, "REPARTO_SUMA_DISTINTA")):
            with self.assertRaises(SystemExit) as cm:
                che.aplicar_reparto(self.POB, [malo])
            self.assertIn(msg, str(cm.exception))
        con_fila = {**self.POB, self.H1: {"poblacion": 1, "origen": "dato"}}
        with self.assertRaises(SystemExit) as cm:
            che.aplicar_reparto(con_fila, [x])
        self.assertIn("REPARTO_HIJA_CON_FILA", str(cm.exception))


class ApartadasPorVotos(unittest.TestCase):
    """D-158: provincias de 2011-11 con votos sin asignar > 0,1 % quedan APARTADA_VOTOS; D-70 no se toca y no hay excepciones nuevas en la puerta."""

    APARTADAS = {"03": 1877, "24": 807, "27": 1128, "32": 399, "33": 1541}  # literal: votos fuera del seccionado 2012 (suma 5.752; máx. 0,54 % en 27)

    def test_contrato_2011_11_declara_las_5(self):
        c = json.loads(che.ruta_contrato("2011-11").read_text(encoding="utf-8"))
        ap = {k: p["poblacion"]["votos_sin_asignar"] for k, p in c["provincias"].items() if "votos_sin_asignar" in p["poblacion"]}
        self.assertEqual({k: v["votos_fuera_del_seccionado"] for k, v in ap.items()}, self.APARTADAS)
        self.assertEqual(sum(self.APARTADAS.values()), 5752)
        for k, v in ap.items():
            self.assertEqual(v["fuente_sha256"], _sha(ROOT / v["fuente"]))
            self.assertEqual(c["provincias"][k]["estado"], "APARTADA_VOTOS")
        self.assertEqual(max(float(v["pct"]) for v in ap.values()), 0.5369)
        self.assertEqual({k for k, p in c["provincias"].items() if p["estado"] == "APARTADA_VOTOS"}, set(self.APARTADAS))
        self.assertNotIn("excepciones_votos_sin_asignar", c["puerta"])  # sin excepciones nuevas en la puerta

    def test_control_negativo_otras_elecciones_y_d70_intacto(self):
        self.assertEqual(che.apartadas_por_votos("2019-11"), {})
        self.assertEqual(sorted(che.apartadas_por_votos("2011-11")), sorted(self.APARTADAS))
        import historico_campana as hc
        self.assertEqual(hc.D70["201111"], {"03": 1877, "24": 807, "27": 1128, "32": 399, "33": 1541})  # D-70 sin tocar
        for e in ("2015-12", "2016-06", "2019-04", "2019-11"):
            c = json.loads(che.ruta_contrato(e).read_text(encoding="utf-8"))
            self.assertFalse(any("votos_sin_asignar" in p["poblacion"] for p in c["provincias"].values()), e)

    def test_provincia_apartada_no_se_materializa(self):
        with self.assertRaises(SystemExit) as cm:
            che._exigir_lista({"estado": "APARTADA_VOTOS"}, "nac03", "2011-11")
        self.assertIn("PROVINCIA_NO_LISTA", str(cm.exception))


class ContratoDe2011(unittest.TestCase):
    def test_reparto_conserva_totales_y_declara_los_casos(self):
        c = json.loads(che.ruta_contrato("2011-11").read_text(encoding="utf-8"))
        self.assertEqual(c["seccionado"]["fichero"], "seccionado_2012.zip")
        madres = hijas = 0
        for cpro, p in c["provincias"].items():
            r = p["poblacion"].get("sin_poblacion_resuelto")
            if not r:
                continue
            for x in r["repartidas"]:
                madres += 1
                hijas += sum(y["rol"] == "hija" for y in x["miembros"])
                self.assertEqual(sum(y["poblacion"] for y in x["miembros"]), x["poblacion_censo_madre"])  # se conservan los totales del Censo
                self.assertTrue(all(y["solape"] >= 0.5 for y in x["miembros"] if y["rol"] == "hija"))
        self.assertEqual((madres, hijas), (58, 61))
        self.assertEqual(c["provincias"]["08"]["poblacion"]["secciones_sin_dato"], ["0804703001"])  # sin dato en ningún año: no se inventa
        self.assertEqual(c["provincias"]["08"]["estado"], "BLOQUEADA_SIN_DATO")
        self.assertEqual(c["provincias"]["36"]["poblacion"]["secciones_sin_dato"], ["3605901003"])
        self.assertIsNone(c["poblacion"]["total_municipal_oficial"]["fuente"])  # sin tabla oficial: sin ajuste, declarado
        self.assertEqual(sum(len(p["poblacion"].get("sin_poblacion_resuelto", {}).get("rellenadas", [])) for p in c["provincias"].values()), 42)


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
