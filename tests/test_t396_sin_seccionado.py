# -*- coding: utf-8 -*-
"""T-396 (D-153): secciones con población sin geometría en el seccionado del año → asignada / excluida / APARTADA.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.2.0 · FECHA: 2026-11-23 · ESTADO: candidato
ANTERIOR: legacy/tests/test_t396_sin_seccionado_v1.1.0_20261123.py
CAMBIOS: 1.2.0: T-448 (D-200): sucesora sin fila que contiene la sección al 100 % con el centroide y en el mismo municipio → asignada y
  la sucesora nace `reasignada`; controles negativos (contención parcial, otro municipio, punto representativo). 1.1.0: T-402: `materializar` normaliza la geometría; con zip falso se parchea `_normalizar_seccionado`. 1.0.0: fichero nuevo.
MOTIVO: T-396. Geometrías y tabla sintéticas (valores esperados escritos a mano, no recalculados); sin red.
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

A, B, C = "2200101001", "2200101002", "2300101001"  # A y B: provincia 22; C: provincia 23
AÑO = {A: None, B: None, C: None}


def _geo_anio():
    return {A: box(0, 0, 10, 10), B: box(10, 0, 20, 10), C: box(20, 0, 30, 10)}


@unittest.skipIf(box is None, "sin shapely")
class AsignarSinSeccionado(unittest.TestCase):
    def test_asignada_excluida_y_otra_provincia_apartada(self):
        donante_cerca = {"2200101009": box(1, 1, 3, 3),            # centroide (2,2) dentro de A → asignada
                         "2200101010": box(21, 1, 23, 3),          # centroide dentro de C (provincia 23) → apartada
                         "2200101011": box(100, 100, 102, 102)}    # fuera de todo el seccionado → excluida
        donante_lejos = {"2200101009": box(11, 1, 13, 3),          # NO se usa: manda el donante más cercano
                         "2200101012": box(11, 1, 13, 3)}          # solo aquí: asignada a B
        pob = {"2200101009": 7, "2200101010": 5, "2200101011": 3, "2200101012": 9, "2200101013": 4}
        r = che.asignar_sin_seccionado(sorted(pob), pob, _geo_anio(),
                                       [(2019, lambda: donante_cerca), (2015, lambda: donante_lejos)])
        self.assertEqual((r["2200101009"]["destino"], r["2200101009"]["sucesora"], r["2200101009"]["donante_anio"]), ("asignada", A, 2019))
        self.assertTrue(r["2200101009"]["mismo_municipio"])
        self.assertEqual((r["2200101010"]["destino"], r["2200101010"]["sucesora"]), ("apartada", C))
        self.assertEqual((r["2200101011"]["destino"], r["2200101011"]["poblacion"]), ("excluida", 3))
        self.assertEqual((r["2200101012"]["destino"], r["2200101012"]["sucesora"], r["2200101012"]["donante_anio"]), ("asignada", B, 2015))
        self.assertEqual((r["2200101013"]["destino"], r["2200101013"]["motivo"]), ("excluida", "sin geometría en ningún seccionado"))

    def test_centroide_fuera_usa_punto_representativo(self):
        from shapely.geometry import Polygon
        # Sección donante en L: su centroide (42,87; 2,87) cae en el hueco y su punto representativo (40,5; 5,5) en el brazo vertical.
        ele = Polygon([(40, 0), (50, 0), (50, 1), (41, 1), (41, 10), (40, 10)])
        self.assertFalse(ele.contains(ele.centroid))
        self.assertTrue(ele.contains(ele.representative_point()))
        # La sección del año solo cubre una franja del brazo: contiene el punto representativo y NO el centroide.
        geo = {A: box(39, 3, 41.5, 11), B: box(10, 0, 20, 10)}
        self.assertFalse(geo[A].contains(ele.centroid))
        r = che.asignar_sin_seccionado(["2200101009"], {"2200101009": 1}, geo, [(2019, lambda: {"2200101009": ele})])
        self.assertEqual((r["2200101009"]["destino"], r["2200101009"]["sucesora"], r["2200101009"]["punto"]),
                         ("asignada", A, "punto_representativo"))
        # Control negativo: con el centroide dentro de la sección (donante en caja) no hace falta el respaldo
        r = che.asignar_sin_seccionado(["2200101009"], {"2200101009": 1}, geo, [(2019, lambda: {"2200101009": box(40, 4, 41, 6)})])
        self.assertEqual((r["2200101009"]["destino"], r["2200101009"]["punto"]), ("asignada", "centroide"))
        # Ni centroide ni punto representativo en el seccionado → excluida
        r = che.asignar_sin_seccionado(["2200101009"], {"2200101009": 1}, {B: box(10, 0, 20, 10)}, [(2019, lambda: {"2200101009": ele})])
        self.assertEqual(r["2200101009"]["destino"], "excluida")

    def test_sucesora_sin_fila_en_la_tabla_se_excluye(self):
        # contenida solo en 5/6 (box 5..11 sobre A = 0..10): sigue excluida aunque el centroide (8,2) caiga en A
        r = che.asignar_sin_seccionado(["2200101009"], {"2200101009": 7}, _geo_anio(), [(2019, lambda: {"2200101009": box(5, 1, 11, 3)})],
                                       con_fila={B})
        self.assertEqual((r["2200101009"]["destino"], r["2200101009"]["poblacion"]), ("excluida", 7))
        self.assertIn(A, r["2200101009"]["motivo"])

    def test_d200_sucesora_sin_fila_que_la_contiene_entera_la_recibe(self):
        r = che.asignar_sin_seccionado(["2200101009"], {"2200101009": 7}, _geo_anio(), [(2019, lambda: {"2200101009": box(1, 1, 3, 3)})],
                                       con_fila={B})
        self.assertEqual((r["2200101009"]["destino"], r["2200101009"]["sucesora"], r["2200101009"]["sucesora_sin_fila"],
                          r["2200101009"]["contencion"]), ("asignada", A, True, "1.0000"))
        # otro municipio (22002 dentro de A, que es 22001): excluida
        r = che.asignar_sin_seccionado(["2200201009"], {"2200201009": 7}, _geo_anio(), [(2019, lambda: {"2200201009": box(1, 1, 3, 3)})],
                                       con_fila={B})
        self.assertEqual(r["2200201009"]["destino"], "excluida")
        # con sucesora con fila no cambia nada (regla D-153 de siempre, sin marca)
        r = che.asignar_sin_seccionado(["2200101009"], {"2200101009": 7}, _geo_anio(), [(2019, lambda: {"2200101009": box(1, 1, 3, 3)})],
                                       con_fila={A, B})
        self.assertEqual((r["2200101009"]["destino"], "sucesora_sin_fila" in r["2200101009"]), ("asignada", False))

    def test_d200_solo_con_centroide_no_con_punto_representativo(self):
        from shapely.geometry import Polygon
        ele = Polygon([(1, 1), (9, 1), (9, 2), (2, 2), (2, 9), (1, 9)])  # en L dentro de A; su centroide cae en el hueco, también dentro de A
        self.assertTrue(box(0, 0, 10, 10).contains(ele.centroid))
        r = che.asignar_sin_seccionado(["2200101009"], {"2200101009": 7}, _geo_anio(), [(2019, lambda: {"2200101009": ele})], con_fila={B})
        self.assertEqual((r["2200101009"]["destino"], r["2200101009"]["punto"]), ("asignada", "centroide"))
        geo = {A: box(0.5, 0.5, 2.5, 9.5), B: box(10, 0, 20, 10)}  # A contiene solo el brazo vertical: no la contiene entera
        r = che.asignar_sin_seccionado(["2200101009"], {"2200101009": 7}, geo, [(2019, lambda: {"2200101009": ele})], con_fila={B})
        self.assertEqual(r["2200101009"]["destino"], "excluida")
        # contenida entera (≥ 0,999) pero el centroide cae en el hueco de la L, fuera de todo el seccionado: solo la encuentra el punto
        # representativo → excluida (aísla la condición «centroide dentro» de D-200)
        geo = {A: ele.buffer(0.1), B: box(10, 0, 20, 10)}
        self.assertFalse(any(g.contains(ele.centroid) for g in geo.values()))
        self.assertGreaterEqual(ele.intersection(geo[A]).area / ele.area, che.CONTENCION_SUCESORA)
        r = che.asignar_sin_seccionado(["2200101009"], {"2200101009": 7}, geo, [(2019, lambda: {"2200101009": ele})], con_fila={B})
        self.assertEqual(r["2200101009"]["destino"], "excluida")
        self.assertIn(A, r["2200101009"]["motivo"])

    def test_donante_con_huella_distinta_falla_cerrado(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "seccionado_2015.zip").write_bytes(b"no es el zip del INE")
            with self.assertRaises(SystemExit) as cm:
                che._donantes({"seccionado": 2012}, {}, Path(d), ROOT)
            self.assertIn("DONANTE_HUELLA_DISTINTA", str(cm.exception))


class AplicarAsignacion(unittest.TestCase):
    def test_suma_en_la_sucesora_y_excluye(self):
        pob = {A: {"poblacion": 10, "origen": "dato"}, B: {"poblacion": 20, "origen": "dato"},
               "2200101009": {"poblacion": 7, "origen": "dato"}, "2200101011": {"poblacion": 3, "origen": "dato"}}
        out = che.aplicar_asignacion(pob, [{"seccion": "2200101009", "sucesora": A, "poblacion": 7}],
                                     [{"seccion": "2200101011", "poblacion": 3}])
        self.assertEqual(out, {A: {"poblacion": 17, "origen": "dato"}, B: {"poblacion": 20, "origen": "dato"}})  # dato + dato = dato
        pob["2200101009"]["origen"] = "interpolada"
        out = che.aplicar_asignacion(pob, [{"seccion": "2200101009", "sucesora": A, "poblacion": 7}], [])
        self.assertEqual(out[A], {"poblacion": 17, "origen": "reasignada"})  # con una estimada, cuenta como estimada
        self.assertEqual(pob["2200101009"]["poblacion"], 7)  # la entrada no se muta

    def test_d200_la_sucesora_sin_fila_nace_reasignada(self):
        pob = {B: {"poblacion": 20, "origen": "dato"}, "2200101009": {"poblacion": 270, "origen": "dato"}}
        out = che.aplicar_asignacion(pob, [{"seccion": "2200101009", "sucesora": A, "poblacion": 270, "sucesora_sin_fila": True}], [])
        self.assertEqual(out, {A: {"poblacion": 270, "origen": "reasignada"}, B: {"poblacion": 20, "origen": "dato"}})
        with self.assertRaises(SystemExit) as cm:  # marcada sin fila pero la tiene: falla cerrado
            che.aplicar_asignacion(pob, [{"seccion": "2200101009", "sucesora": B, "poblacion": 270, "sucesora_sin_fila": True}], [])
        self.assertIn("SUCESORA_CON_FILA", str(cm.exception))
        with self.assertRaises(SystemExit) as cm:  # sin marca y sin fila: como antes
            che.aplicar_asignacion(pob, [{"seccion": "2200101009", "sucesora": A, "poblacion": 270}], [])
        self.assertIn("SUCESORA_SIN_FILA", str(cm.exception))

    def test_poblacion_declarada_distinta_falla(self):
        pob = {A: {"poblacion": 10, "origen": "dato"}, "2200101009": {"poblacion": 7, "origen": "dato"}}
        with self.assertRaises(SystemExit) as cm:
            che.aplicar_asignacion(pob, [{"seccion": "2200101009", "sucesora": A, "poblacion": 8}], [])
        self.assertIn("SIN_SECCIONADO_POBLACION_DISTINTA", str(cm.exception))


class MaterializarConSinSeccionado(unittest.TestCase):
    def _arbol(self, d: Path, resuelto: dict | None, sin_resolver: list, estado: str = "LISTA"):
        import yaml
        root, fuentes = d / "root", d / "fuentes"
        (root / "territorios/nac22/config").mkdir(parents=True)
        fuentes.mkdir()
        base = root / "territorios/nac22/config/nac22_2025.yaml"
        base.write_text(yaml.safe_dump(BASE), encoding="utf-8")
        (fuentes / "seccionado_2020.zip").write_bytes(b"zip")
        (fuentes / "tabla.csv").write_text(
            "elección,sección,población,origen,año_fuente_relleno\n2019-11,2200101001,10,dato,\n2019-11,2200101002,20,dato,\n"
            "2019-11,2200101009,7,dato,\n2019-11,2200101011,3,dato,\n", encoding="utf-8")
        c = _contrato_sintetico(_sha(fuentes / "tabla.csv"), _sha(base), _sha(fuentes / "seccionado_2020.zip"), "d" * 64)
        p = c["provincias"]["22"]
        p["estado"] = estado
        p["poblacion"].update({"secciones_sin_seccionado": sin_resolver, "secciones": 2, "total": 30})
        if resuelto:
            p["poblacion"]["sin_seccionado_resuelto"] = resuelto
        cpath = root / "contrato.json"
        cpath.write_text(json.dumps(c), encoding="utf-8")
        def falso(secc, cpro, cache, sha):  # zip de mentira: la normalización real se prueba en test_t365 (MaterializarZipReal)
            dest = cache / "seccionado_normalizado.zip"
            dest.write_bytes(secc.read_bytes())
            return dest, {"normalizado_sha256": hashlib.sha256(dest.read_bytes()).hexdigest(), "corregidas": []}
        return root, fuentes, cpath, mock.patch.multiple(che, _secciones_seccionado=mock.Mock(return_value={A, B}),
                                                         _normalizar_seccionado=falso)

    RES = {"asignadas": [{"seccion": "2200101009", "sucesora": A, "donante_anio": 2019, "poblacion": 7}],
           "excluidas": [{"seccion": "2200101011", "poblacion": 3, "motivo": "x"}], "apartadas": []}

    def test_asignada_y_excluida_materializa_y_suma(self):
        with tempfile.TemporaryDirectory() as d:
            root, fuentes, cpath, parche = self._arbol(Path(d), self.RES, [])
            with parche:
                out = che.materializar("2019-11", "nac22", fuentes, root, cpath)
            import yaml
            cfg = yaml.safe_load(out.read_text(encoding="utf-8"))
            pob = root / cfg["io"]["input"]["population_cip"]["paths"][0]
            self.assertEqual(pob.read_text(encoding="utf-8").splitlines()[1:],
                             ["2020,2200101001,17,dato", "2020,2200101002,20,dato"])

    def test_sin_declarar_sigue_fallando_cerrado(self):
        with tempfile.TemporaryDirectory() as d:
            root, fuentes, cpath, parche = self._arbol(Path(d), None, [])
            with parche, self.assertRaises(SystemExit) as cm:
                che.materializar("2019-11", "nac22", fuentes, root, cpath)
            self.assertIn("SIN_SECCIONADO_DISTINTO_DEL_CONTRATO", str(cm.exception))

    def test_provincia_apartada_no_se_materializa(self):
        with tempfile.TemporaryDirectory() as d:
            res = {"asignadas": [], "excluidas": [self.RES["excluidas"][0]],
                   "apartadas": [{"seccion": "2200101009", "poblacion": 7, "motivo": "otra provincia"}]}
            root, fuentes, cpath, parche = self._arbol(Path(d), res, ["2200101009"], estado="APARTADA")
            with parche, self.assertRaises(SystemExit) as cm:
                che.materializar("2019-11", "nac22", fuentes, root, cpath)
            self.assertIn("PROVINCIA_NO_LISTA", str(cm.exception))


class ContratosVersionados(unittest.TestCase):
    """Los cinco contratos de `main`: ninguna provincia LISTA con secciones sin resolver; el informe se deriva del contrato."""

    ELEC = ("2011-11", "2015-12", "2016-06", "2019-04", "2019-11")

    def test_coherencia_de_cada_contrato(self):
        for e in self.ELEC:
            c = json.loads(che.ruta_contrato(e).read_text(encoding="utf-8"))
            for cpro, p in c["provincias"].items():
                pb, r = p["poblacion"], p["poblacion"].get("sin_seccionado_resuelto")
                with self.subTest(e=e, cpro=cpro):
                    if p["estado"] == "LISTA":
                        self.assertEqual(pb["secciones_sin_seccionado"], [])
                    if r:
                        self.assertEqual(r["poblacion_asignada"], sum(x["poblacion"] for x in r["asignadas"]))
                        self.assertEqual(r["poblacion_excluida"], sum(x["poblacion"] for x in r["excluidas"]))
                        self.assertEqual(sorted(pb["secciones_sin_seccionado"]), sorted(x["seccion"] for x in r["apartadas"]))
                        self.assertEqual(p["estado"] == "APARTADA", bool(r["apartadas"]) and p["estado"] != "BLOQUEADA_SIN_DATO")
                        self.assertTrue(all(x["sucesora"][:2] == x["seccion"][:2] == cpro for x in r["asignadas"]))

    def test_informe_coincide_con_los_contratos(self):
        filas = che.informe_sin_seccionado()
        n = 0
        for e in self.ELEC:
            c = json.loads(che.ruta_contrato(e).read_text(encoding="utf-8"))
            n += sum(len((p["poblacion"].get("sin_seccionado_resuelto") or {}).get("asignadas", [])) for p in c["provincias"].values())
        self.assertEqual(sum(f["asignadas"] for f in filas), n)


if __name__ == "__main__":
    unittest.main()
