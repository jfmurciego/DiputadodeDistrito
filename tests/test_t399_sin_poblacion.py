# -*- coding: utf-8 -*-
"""T-399 (D-126/D-128): secciones del seccionado sin población en la tabla → rellenadas con el Atlas del año más cercano y ajuste municipal.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.3.0 · FECHA: 2026-11-23 · ESTADO: candidato
ANTERIOR: legacy/tests/test_t399_sin_poblacion_v1.2.0_20261123.py
CAMBIOS: 1.3.0: T-448 (D-200): Barcelona (08) LISTA: 0804703001 recibe los 270 hab. del Censo de 0804702003 (contenida al 100 %); Las Palmas (35):
  3501603042 recibe los 730 de 3501602060 en lugar del relleno (1.681); D-201 (b): sin ajuste al total municipal, declarado (67 y 951). 1.2.0: T-448 (D-197): Ceuta (51, un diputado) exenta del 1 % y LISTA; clase ExencionRelleno con controles negativos. 1.1.0: T-400 (D-185): total municipal del Censo 2011: residuo para la única sección sin dato de un municipio (36059: 0) y 36 pasa a LISTA. 1.0.0: fichero nuevo.
MOTIVO: T-399 (D-158 B'). Atlas, tabla y seccionado sintéticos (valores esperados escritos a mano, no recalculados); sin red.
"""
from __future__ import annotations

import hashlib
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

    def test_sin_dato_en_ningun_anio_y_sin_total_municipal_no_se_inventa(self):
        r = che.rellenar_sin_poblacion([N1, S], self.POB, ATLAS, 2011, {"22001": 450})  # sin total de 22002
        self.assertEqual(r["sin_dato"], [S])
        self.assertEqual([x["seccion"] for x in r["rellenadas"]], [N1])   # S no aparece con 0
        self.assertEqual({x["municipio"]: x["estado"] for x in r["cuadre"]}["22002"], "aviso_sin_dato")

    def test_unica_seccion_sin_dato_recibe_el_residuo_del_total_municipal(self):
        pob = {**self.POB, "2200201002": {"poblacion": 15, "origen": "dato"}}
        r = che.rellenar_sin_poblacion([S], pob, ATLAS, 2011, {"22002": 40})   # 40 − 15 = 25 (a mano)
        self.assertEqual(r["sin_dato"], [])
        self.assertEqual([(x["seccion"], x["poblacion"], x["ajuste"]) for x in r["rellenadas"]], [(S, 25, "residuo_municipal_censo")])
        r = che.rellenar_sin_poblacion([S], pob, ATLAS, 2011, {"22002": 10})   # residuo −5: mínimo 0
        self.assertEqual([(x["poblacion"], x["ajuste"]) for x in r["rellenadas"]], [(0, "residuo_municipal_censo")])
        self.assertEqual(r["cuadre"][0]["exceso_sobre_censo"], 5)

    def test_dos_secciones_sin_dato_en_un_municipio_siguen_sin_dato(self):
        S2 = "2200201003"
        r = che.rellenar_sin_poblacion([S, S2], self.POB, {**ATLAS, 2015: {**ATLAS[2015], S2: "."}}, 2011, {"22002": 40})
        self.assertEqual(sorted(r["sin_dato"]), [S, S2])


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
        def falso(secc, cpro, cache, sha):  # zip de mentira: la normalización real se prueba en test_t365 (MaterializarZipReal)
            dest = cache / "seccionado_normalizado.zip"
            dest.write_bytes(secc.read_bytes())
            return dest, {"normalizado_sha256": hashlib.sha256(dest.read_bytes()).hexdigest(), "corregidas": []}
        return root, fuentes, cpath, mock.patch.multiple(che, _secciones_seccionado=mock.Mock(return_value={A, B, N1}), _normalizar_seccionado=falso)

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

    def test_reparto_madre_hija_declarado_materializa_y_conserva_el_total(self):
        with tempfile.TemporaryDirectory() as d:
            root, fuentes, cpath, parche = self._arbol(Path(d), False)
            c = json.loads(cpath.read_text(encoding="utf-8"))
            c["provincias"]["22"]["poblacion"]["sin_poblacion_resuelto"] = {"repartidas": [{
                "madre": B, "poblacion_censo_madre": 200,
                "miembros": [{"seccion": B, "rol": "madre", "poblacion": 120}, {"seccion": N1, "rol": "hija", "solape": 0.9, "poblacion": 80}]}],
                "rellenadas": []}
            cpath.write_text(json.dumps(c), encoding="utf-8")
            with parche:
                out = che.materializar("2019-11", "nac22", fuentes, root, cpath)
            import yaml
            cfg = yaml.safe_load(out.read_text(encoding="utf-8"))
            filas = (root / cfg["io"]["input"]["population_cip"]["paths"][0]).read_text(encoding="utf-8").splitlines()[1:]
            self.assertEqual(filas, ["2020,2200101001,100,dato", "2020,2200101002,120,repartida_madre", "2020,2200101003,80,repartida_hija"])
            self.assertEqual(120 + 80, 200)  # el total de la madre (200) se conserva
            # control negativo: si la tabla ya no trae esa población en la madre, falla cerrado
            c["provincias"]["22"]["poblacion"]["sin_poblacion_resuelto"]["repartidas"][0]["poblacion_censo_madre"] = 199
            cpath.write_text(json.dumps(c), encoding="utf-8")
            with parche, self.assertRaises(SystemExit) as cm:
                che.materializar("2019-11", "nac22", fuentes, root, cpath)
            self.assertIn("REPARTO_MADRE_POBLACION_DISTINTA", str(cm.exception))

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

    def test_la_madre_es_del_mismo_municipio(self):
        # otra sección con población de OTRO municipio (22002) solapa igual: no puede ser madre; la del mismo municipio (22001) sí
        otro = "2200201001"
        censo = {self.M: box(0, 0, 10, 10), otro: box(10, 0, 20, 10)}
        pob = {self.M: self.POB[self.M], otro: {"poblacion": 700, "origen": "dato"}}
        atlas = {2015: {self.M: 600, self.H1: 400}}
        r = che.repartir_madres([self.H1], pob, {self.H1: box(5, 0, 15, 10)}, censo, atlas, 2011)  # 50 % en cada una
        self.assertEqual([x["madre"] for x in r["repartos"]], [self.M])
        # control negativo: si solo hay madre candidata en otro municipio, la hija queda sin madre
        r = che.repartir_madres([self.H1], {otro: pob[otro]}, {self.H1: box(10, 0, 14, 10)}, censo, atlas, 2011)
        self.assertEqual((r["repartos"], r["sin_madre"]), ([], [self.H1]))

    def test_restos_mayores_exactos_y_suma_siempre_igual_a_la_madre(self):
        # valores a mano (no con el código): 100 en 1:1:1 → base 33/33/33 y los restos son iguales: el sobrante va a la primera (madre)
        geo = {self.H1: box(0, 0, 5, 10), self.H2: box(5, 0, 10, 10)}
        r = che.repartir_madres([self.H1, self.H2], {self.M: {"poblacion": 100, "origen": "dato"}}, geo, self.CENSO,
                                {2015: {self.M: 1, self.H1: 1, self.H2: 1}}, 2011)
        self.assertEqual([y["poblacion"] for y in r["repartos"][0]["miembros"]], [34, 33, 33])
        # 101 en 5:3:2 → base 50/30/20, restos 5/3/2: el uno que falta va al resto mayor (la madre)
        r = che.repartir_madres([self.H1, self.H2], {self.M: {"poblacion": 101, "origen": "dato"}}, geo, self.CENSO,
                                {2015: {self.M: 5, self.H1: 3, self.H2: 2}}, 2011)
        self.assertEqual([y["poblacion"] for y in r["repartos"][0]["miembros"]], [51, 30, 20])
        # 7 en 1:2:4: exactos 1, 2, 4
        r = che.repartir_madres([self.H1, self.H2], {self.M: {"poblacion": 7, "origen": "dato"}}, geo, self.CENSO,
                                {2015: {self.M: 1, self.H1: 2, self.H2: 4}}, 2011)
        self.assertEqual([y["poblacion"] for y in r["repartos"][0]["miembros"]], [1, 2, 4])
        # propiedad independiente: para cualquier total y pesos, la suma es el total y cada parte difiere < 1 de la proporción exacta
        import itertools
        for total, pesos in itertools.product((1, 2, 99, 1000, 123457), ((1, 1), (1, 7, 3), (13, 1, 1), (5, 5, 5, 5), (1000, 1))):
            vals = {f"22001010{i:02d}": v for i, v in enumerate(pesos, 1)}
            claves = list(vals)
            geo_i = {k: box(0, 0, 10, 10) for k in claves[1:]}
            r = che.repartir_madres(claves[1:], {claves[0]: {"poblacion": total, "origen": "dato"}}, geo_i, {claves[0]: box(0, 0, 10, 10)},
                                    {2015: vals}, 2011)
            partes = [y["poblacion"] for y in r["repartos"][0]["miembros"]]
            self.assertEqual(sum(partes), total)
            for parte, peso in zip(partes, pesos):
                self.assertLess(abs(parte - total * peso / sum(pesos)), 1)

    def test_madres_contra_el_censo_acreditado(self):
        rep = [{"madre": self.M, "poblacion_censo_madre": 1000, "miembros": []}]
        che.verificar_madres_censo(rep, {self.M: 1000})  # coincide: sin error
        for censo in ({self.M: 995}, {}, {self.M: "."}):
            with self.assertRaises(SystemExit) as cm:
                che.verificar_madres_censo(rep, censo)
            self.assertIn("REPARTO_MADRE_DISTINTA_DEL_CENSO", str(cm.exception))

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


class CriterioDelUnoPorCiento(unittest.TestCase):
    """D-161: del reparto madre/hijas cuenta solo lo movido a las hijas más lo rellenado; la madre no cuenta."""

    FILAS = [{"poblacion": 100, "origen": "dato"}, {"poblacion": 600, "origen": "repartida_madre"}, {"poblacion": 300, "origen": "repartida_hija"},
             {"poblacion": 50, "origen": "rellenada_año_cercano"}, {"poblacion": 10, "origen": "reasignada"}]

    def test_cuenta_hijas_y_rellenadas_no_la_madre(self):
        est = che.filas_estimadas(self.FILAS)
        self.assertEqual(sorted(x["origen"] for x in est), ["reasignada", "rellenada_año_cercano", "repartida_hija"])
        self.assertEqual(sum(x["poblacion"] for x in est), 360)  # 300 + 50 + 10 (a mano); con la madre enteras serían 960

    def test_contrato_2011_11_con_el_criterio_nuevo(self):
        c = json.loads(che.ruta_contrato("2011-11").read_text(encoding="utf-8"))
        self.assertIn("D-161", c["poblacion"]["regla_publicacion"])
        # 51 (1,70 %) supera el 1 %; 36 (2,64 %) bajó a 0,65 % con el total municipal del Censo (D-185); 15, 22, 29, 34 y 47 (con el criterio de madre+hijas enteras superaban el 1 %) ya no
        pct = {k: float(c["provincias"][k]["poblacion"]["pct_no_dato"]) for k in ("15", "22", "29", "34", "47", "36", "51")}
        self.assertTrue(pct["51"] > 1 and pct["36"] <= 1)
        self.assertTrue(all(pct[k] <= 1 for k in ("15", "22", "29", "34", "47")), pct)
        self.assertEqual(c["provincias"]["51"]["estado"], "LISTA")  # D-197: un diputado, exenta del 1 % (declarada)
        self.assertEqual(c["provincias"]["51"]["exencion_relleno"]["decision"], "D-197 (propietario, 23-11)")
        self.assertEqual(c["provincias"]["36"]["estado"], "LISTA")  # D-185: su única sección sin dato recibe el residuo municipal del Censo
        for k in ("15", "22", "29", "34", "47"):
            self.assertEqual(c["provincias"][k]["estado"], "LISTA", k)
        estados = {k: p["estado"] for k, p in c["provincias"].items()}
        self.assertEqual({e: sum(v == e for v in estados.values()) for e in set(estados.values())},
                         {"LISTA": 47, "APARTADA_VOTOS": 5})  # D-185: 36 pasa a LISTA; D-197: 51; D-200: 08

    def test_las_otras_elecciones_no_cambian_de_criterio(self):
        for e in ("2015-12", "2016-06", "2019-04", "2019-11"):  # sin reparto madre/hijas: mismo cómputo que con D-126
            c = json.loads(che.ruta_contrato(e).read_text(encoding="utf-8"))
            for p in c["provincias"].values():
                self.assertNotIn("repartida_madre", json.dumps(p["poblacion"]))


class SemaforoNoLeeContratosHistoricos(unittest.TestCase):
    """`campana_estado` aún no lee el estado de los contratos históricos (T-378 lo hará): cuando lo haga, `APARTADA_VOTOS` debe ser rojo (no LISTA → no declarable, D-154)."""

    def test_campana_estado_no_lee_estados_de_contratos_historicos(self):
        src = (ROOT / "herramientas/campana_estado.py").read_text(encoding="utf-8")
        for palabra in ("historico_epoca", "APARTADA_VOTOS", "BLOQUEADA_RELLENO"):
            self.assertNotIn(palabra, src, "campana_estado ya lee contratos históricos: añade APARTADA_VOTOS como causa roja")


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
        v = c["poblacion"]["madres_verificadas_contra_censo"]  # las madres se verificaron contra el Censo acreditado (sha256 de T-357)
        self.assertEqual(v["sha256"], che._sumas_t357(ROOT)["indicadores_seccion_censal_csv.zip"])
        for e in ("2015-12", "2016-06", "2019-04", "2019-11"):
            self.assertNotIn("madres_verificadas_contra_censo", json.loads(che.ruta_contrato(e).read_text(encoding="utf-8"))["poblacion"])
        self.assertEqual(c["provincias"]["08"]["poblacion"]["secciones_sin_dato"], [])  # D-200: 0804703001 recibe la sección del Censo que contiene
        self.assertEqual(c["provincias"]["08"]["estado"], "LISTA")
        self.assertEqual(c["provincias"]["36"]["poblacion"]["secciones_sin_dato"], [])  # D-185: residuo del total municipal (6.073 − 6.075 < 0 → 0)
        r36 = {x["seccion"]: x for x in c["provincias"]["36"]["poblacion"]["sin_poblacion_resuelto"]["rellenadas"]}["3605901003"]
        self.assertEqual((r36["poblacion"], r36["ajuste"]), (0, "residuo_municipal_censo"))
        decl = json.loads((ROOT / "configuracion/historico_epoca/total_municipal_censo_2011.json").read_text(encoding="utf-8"))
        self.assertEqual(c["poblacion"]["total_municipal_oficial"]["sha256"], decl["fuente"]["sha256"])
        self.assertEqual(sum(len(p["poblacion"].get("sin_poblacion_resuelto", {}).get("rellenadas", [])) for p in c["provincias"].values()), 42)  # 41 con Atlas + 3605901003 con el residuo municipal (D-200: 3501603042 ya no se rellena)


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
                    self.assertEqual(r["habitantes_atlas"], sum(x["poblacion_atlas"] or 0 for x in r["rellenadas"]))
                    self.assertTrue(all(x["poblacion"] >= 0 and x["seccion"][:2] == cpro for x in r["rellenadas"]))
                    self.assertTrue(set(r["sin_dato"]) <= set(pb["secciones_sin_dato"]))
                    if r["sin_dato"]:
                        self.assertEqual(p["estado"], "BLOQUEADA_SIN_DATO")  # sin dato en ningún año: no se inventa
                    # el relleno cuenta como estimado: si pasa del 1 % la provincia no es LISTA (D-126)
                    if r["habitantes_rellenados"] * 100 > pb["total"] and "exencion_relleno" not in p:
                        self.assertNotEqual(p["estado"], "LISTA")

    def test_informe_coincide_con_los_contratos(self):
        prov, mun = che.informe_sin_poblacion()
        n = 0
        for e in self.ELEC:
            c = json.loads(che.ruta_contrato(e).read_text(encoding="utf-8"))
            n += sum(len((p["poblacion"].get("sin_poblacion_resuelto") or {}).get("rellenadas", [])) for p in c["provincias"].values())
        self.assertEqual(sum(f["secciones_rellenadas"] for f in prov), n)
        self.assertEqual(sum(f["secciones_rellenadas"] for f in mun), n)


class SucesoraSinFila(unittest.TestCase):
    """D-200 (propietario, 23-11) en el contrato 2011-11: valores del Censo 2011 por sección (indicadores_seccion_censal_csv.zip, sha256 305a19f1…)."""

    def test_cardona_y_las_palmas(self):
        c = json.loads(che.ruta_contrato("2011-11").read_text(encoding="utf-8"))
        for cpro, sec, suc, censo in (("08", "0804702003", "0804703001", 270), ("35", "3501602060", "3501603042", 730)):
            with self.subTest(cpro=cpro):
                p = c["provincias"][cpro]
                r = p["poblacion"]["sin_seccionado_resuelto"]
                a = [x for x in r["asignadas"] if x["seccion"] == sec]
                self.assertEqual([(x["sucesora"], x["poblacion"], x["sucesora_sin_fila"], x["contencion"], x["decision"]) for x in a],
                                 [(suc, censo, True, "1.0000", "D-200")])
                self.assertEqual(r["excluidas"], [])
                self.assertEqual(p["estado"], "LISTA")
                sp = p["poblacion"].get("sin_poblacion_resuelto") or {}
                self.assertNotIn(suc, [x["seccion"] for x in sp.get("rellenadas", [])])  # no se rellena con el Atlas
                self.assertNotIn(suc, [m["seccion"] for x in sp.get("repartidas", []) for m in x["miembros"]])  # ni es hija
        self.assertEqual(c["provincias"]["08"]["poblacion"]["secciones_sin_dato"], [])
        self.assertEqual(c["provincias"]["08"]["poblacion"]["total"], 5487390 + 270)  # 1.5.0 + la sección del Censo

    def test_d201_sin_cuadre_municipal_declarado(self):
        # totales de 1mun00 (sha256 ad95479c…): Cardona 5.057, Las Palmas de Gran Canaria 381.271; secciones del Censo: 4.990 y 380.320
        c = json.loads(che.ruta_contrato("2011-11").read_text(encoding="utf-8"))
        got = {cpro: [(x["municipio"], x["total_municipal_censo"], x["suma_secciones"], x["diferencia"], x["decision"])
                      for x in p["poblacion"].get("sin_cuadre_municipal", [])] for cpro, p in c["provincias"].items()}
        self.assertEqual({k: v for k, v in got.items() if v},
                         {"08": [("08047", 5057, 4990, 67, "D-201 (b)")], "35": [("35016", 381271, 380320, 951, "D-201 (b)")]})

    def test_cuadre_sucesoras_sin_fila(self):
        final = {"0804701001": {"poblacion": 100}, "0804703001": {"poblacion": 20}, "0804801001": {"poblacion": 50}}
        asig = [{"sucesora": "0804703001", "sucesora_sin_fila": True}, {"sucesora": "0804801001"}]
        self.assertEqual([(x["municipio"], x["diferencia"]) for x in che.cuadre_sucesoras_sin_fila(final, asig, {"08047": 125, "08048": 60})],
                         [("08047", 5)])  # 08048 no tiene sucesora sin fila: no se declara
        self.assertEqual(che.cuadre_sucesoras_sin_fila(final, asig, {"08047": 120}), [])  # cuadra
        self.assertEqual(che.cuadre_sucesoras_sin_fila(final, asig, {}), [])  # sin total municipal


class ExencionRelleno(unittest.TestCase):
    """D-197 (propietario, 23-11): una provincia de un diputado declarada queda exenta del tope del 1 %; el resto, no."""
    SECC = "772ad76b84e1b3bb9293a5595d2ccafa06f21a3a58ccc96a9ec5dadd99e46c4a"

    def _c(self, k=1, estimada=1410, estado="BLOQUEADA_RELLENO", cpro="51"):
        return {"eleccion": "2011-11", "seccionado": {"sha256": self.SECC},
                "provincias": {cpro: {"K": k, "estado": estado,
                                      "poblacion": {"total": 83195, "poblacion_no_dato": estimada, "pct_no_dato": che.pct(estimada, 83195)}}}}

    def test_declarada_y_un_diputado_pasa_a_lista(self):
        c = che.aplicar_exenciones_relleno(self._c())
        self.assertEqual(c["provincias"]["51"]["estado"], "LISTA")
        self.assertEqual(c["provincias"]["51"]["exencion_relleno"]["pct_estimada"], "1.6948")  # 1.410 / 83.195, contrato 1.4.0

    def test_mas_de_un_diputado_falla_cerrado(self):
        with self.assertRaises(che.ErrorContrato) as cm:
            che.aplicar_exenciones_relleno(self._c(k=2))
        self.assertIn("EXENCION_RELLENO_SOLO_UN_DIPUTADO", str(cm.exception))

    def test_otra_medida_falla_cerrado(self):
        with self.assertRaises(che.ErrorContrato) as cm:
            che.aplicar_exenciones_relleno(self._c(estimada=1500))
        self.assertIn("EXENCION_RELLENO_MEDIDA_DISTINTA", str(cm.exception))

    def test_otro_seccionado_falla_cerrado(self):
        c = self._c()
        c["seccionado"]["sha256"] = "0" * 64
        with self.assertRaises(che.ErrorContrato) as cm:
            che.aplicar_exenciones_relleno(c)
        self.assertIn("EXENCION_RELLENO_DE_OTRO_SECCIONADO", str(cm.exception))

    def test_otra_eleccion_o_provincia_no_declarada_no_cambia(self):
        c = self._c()
        c["eleccion"] = "2019-11"
        self.assertEqual(che.aplicar_exenciones_relleno(c)["provincias"]["51"]["estado"], "BLOQUEADA_RELLENO")
        c = self._c(cpro="52")
        c["provincias"]["51"] = c["provincias"]["52"]
        with self.assertRaises(che.ErrorContrato):  # la declarada (51) debe existir; 52 no se toca
            che.aplicar_exenciones_relleno({**c, "provincias": {"52": c["provincias"]["52"]}})

    def test_contrato_materializable_para_ceuta(self):
        c = json.loads(che.ruta_contrato("2011-11").read_text(encoding="utf-8"))
        self.assertEqual((c["provincias"]["51"]["K"], c["provincias"]["51"]["estado"]), (1, "LISTA"))
        self.assertTrue(all(p["estado"] != "LISTA" or "exencion_relleno" not in p or p["K"] == 1 for p in c["provincias"].values()))


if __name__ == "__main__":
    unittest.main()
