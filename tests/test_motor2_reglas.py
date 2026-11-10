#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T-160 · núcleo de reglas del motor 2: un test por divergencia del inventario
(docs/ESTUDIOS/T137_NUCLEO_REGLAS/INVENTARIO_DIVERGENCIAS.md) y por cada decisión de criterio parametrizada.
Planes sintéticos; valores esperados literales. Solo stdlib."""
from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ddd_motor2.reglas import (  # noqa: E402
    Criterio, ErrorContrato, ErrorDatos, Problema, Reglas, Unidad, comparar_criterios, elegir_metodo, evaluar,
    resumen_por_opcion, variantes_criterio,
)


def contrato(**val):
    base = {
        "expected_districts": 2, "population_floor_ratio": 0.85, "population_cap_ratio": 1.15,
        "target_tolerance_ratio": 0.12, "require_single_province_per_district": True,
        "require_municipality_discipline": False, "province_districts": {},
    }
    base.update(val)
    return {"validation": {k: v for k, v in base.items() if v is not None}}


def cadena(pops, **campos):
    """Unidades u0..un en línea (u0-u1-u2-…), con campos por posición (listas) o comunes (escalar)."""
    us = []
    for i, p in enumerate(pops):
        kw = {k: (v[i] if isinstance(v, list) else v) for k, v in campos.items()}
        kw.setdefault("provincia", "30")
        kw.setdefault("municipio", f"30{i:03d}")
        us.append(Unidad(f"u{i}", p, **kw))
    return Problema(tuple(us), tuple((f"u{i}", f"u{i + 1}") for i in range(len(pops) - 1)))


def plan(*tamanos):
    out, i = {}, 0
    for d, n in enumerate(tamanos):
        for _ in range(n):
            out[f"u{i}"] = f"D{d}"
            i += 1
    return out


def codigos(problema, cfg, asig, **crit):
    return evaluar(problema, Reglas.desde_contrato(cfg, Criterio(**crit)), asig).codigos()


class Divergencias(unittest.TestCase):
    def test_1_tolerancia_metrica_o_dura(self):
        p = cadena([113, 87])  # objetivo 100, tolerancia 12: ambos fuera; suelo 85 y techo 115 se cumplen
        r = Reglas.desde_contrato(contrato(), Criterio(tolerancia="metrica"))
        inf = evaluar(p, r, plan(1, 1))
        self.assertTrue(inf.valido)
        self.assertEqual(inf.metricas["fuera_tolerancia"], ["D0", "D1"])
        self.assertEqual(codigos(p, contrato(), plan(1, 1), tolerancia="dura"), {"R-TOL"})

    def test_1b_tolerancia_dura_exime_por_debajo_a_distrito_exento(self):
        p = cadena([150, 50], municipio=["30001", "30002"])
        cfg = contrato(population_cap_ratio=1.5, population_floor_exempt_municipalities=["30002"])
        self.assertEqual(codigos(p, cfg, plan(1, 1), tolerancia="dura"), {"R-TOL"})  # solo D0 (+50 %)
        inf = evaluar(p, Reglas.desde_contrato(cfg, Criterio(tolerancia="dura")), plan(1, 1))
        self.assertEqual([v.ambito for v in inf.violaciones], ["D0"])

    def test_2_provincia_unica_por_defecto(self):
        p = cadena([130, 70, 70, 130], provincia=["01", "01", "20", "20"])
        cfg = contrato(require_single_province_per_district=None)
        with self.assertRaises(ErrorContrato):
            Reglas.desde_contrato(cfg)  # obligatoria: falla si falta
        self.assertTrue(evaluar(p, Reglas.desde_contrato(cfg, Criterio(provincia_defecto="si")), plan(2, 2)).valido)
        asig_inter = {"u0": "A", "u1": "B", "u2": "B", "u3": "C"}  # B = 01+20
        cfg3 = contrato(require_single_province_per_district=None, expected_districts=3)
        self.assertEqual(codigos(p, cfg3, asig_inter, provincia_defecto="si"), {"R-PROV"})
        self.assertEqual(codigos(p, cfg3, asig_inter, provincia_defecto="no"), set())

    def test_3_campo_r012_ausente_falla(self):
        p = cadena([100, 100], municipio=[None, "30001"])
        with self.assertRaisesRegex(ErrorDatos, "municipio"):
            evaluar(p, Reglas.desde_contrato(contrato(require_municipality_discipline=True)), plan(1, 1))
        cfg = contrato(require_municipality_discipline=True)
        cfg["partitioning"] = {"enabled": True, "strategy": "connected_internal_units"}
        with self.assertRaisesRegex(ErrorDatos, "unidad_r012"):
            evaluar(cadena([100, 100]), Reglas.desde_contrato(cfg), plan(1, 1))

    def test_4_exencion_municipal_por_campo_no_por_id(self):
        cfg = contrato(population_cap_ratio=1.5, population_floor_exempt_municipalities=["30009"])
        # Id renombrado sin formato {prov}:{mun}:…; el campo manda.
        us = (Unidad("renombrada-A", 150, municipio="30001", provincia="30"),
              Unidad("renombrada-B", 50, municipio="30009", provincia="30"))
        p = Problema(us, (("renombrada-A", "renombrada-B"),))
        self.assertTrue(evaluar(p, Reglas.desde_contrato(cfg), {"renombrada-A": 1, "renombrada-B": 2}).valido)
        # Id con formato que «diría» 30009, campo 30010: no exime (no se parsea el id).
        us = (Unidad("30:30001:M", 150, municipio="30001", provincia="30"),
              Unidad("30:30009:M", 50, municipio="30010", provincia="30"))
        p = Problema(us, (("30:30001:M", "30:30009:M"),))
        self.assertEqual(codigos(p, cfg, {"30:30001:M": 1, "30:30009:M": 2}), {"R-POB-SUELO"})

    def test_5_particion_exenta_normalizada_y_modo(self):
        # «7» en el contrato casa con «07» en la unidad.
        p = cadena([150, 50], particion=["01", "7"])
        cfg = contrato(population_cap_ratio=1.5, population_floor_exempt_partitions=["07"])
        self.assertTrue(evaluar(p, Reglas.desde_contrato(cfg), plan(1, 1)).valido)
        # Distrito D1 con dos particiones {07, 08}: 25+25 bajo suelo.
        p = cadena([75, 75, 25, 25], particion=["01", "01", "07", "08"])
        cfg = contrato(population_cap_ratio=1.6, expected_districts=3, population_floor_exempt_partitions=["7"])
        asig = {"u0": "A", "u1": "B", "u2": "C", "u3": "C"}
        self.assertEqual(codigos(p, cfg, asig, exencion_particion="todas"), {"R-POB-SUELO"})
        self.assertEqual(codigos(p, cfg, asig, exencion_particion="alguna"), set())
        self.assertEqual(codigos(p, cfg, asig, exencion_particion="primera"), set())
        cfg8 = contrato(population_cap_ratio=1.6, expected_districts=3, population_floor_exempt_partitions=["08"])
        self.assertEqual(codigos(p, cfg8, asig, exencion_particion="primera"), {"R-POB-SUELO"})
        self.assertEqual(codigos(p, cfg8, asig, exencion_particion="alguna"), set())

    def test_6_cuotas_por_provincia_normalizadas(self):
        p = cadena([100, 100], provincia="08")
        self.assertTrue(evaluar(p, Reglas.desde_contrato(contrato(province_districts={8: 2})), plan(1, 1)).valido)
        self.assertEqual(codigos(p, contrato(province_districts={"8": 1}), plan(1, 1)), {"R-CUOTA"})
        with self.assertRaises(ErrorContrato):
            Reglas.desde_contrato(contrato(province_districts={"8": 1, "08": 1}))

    def test_7_margen_numerico_exacto(self):
        # 100 * 1.15 en coma flotante es 114.99999999999999: con fracciones, 115 está justo en el techo.
        p = cadena([115, 100, 85])
        cfg = contrato(expected_districts=3)
        self.assertTrue(evaluar(p, Reglas.desde_contrato(cfg), plan(1, 1, 1)).valido)
        p = cadena([116, 100, 84])
        self.assertEqual(codigos(p, cfg, plan(1, 1, 1)), {"R-POB-TECHO", "R-POB-SUELO"})

    def test_8_mixtos_contrato_o_fijo(self):
        # Municipio M (u1,u2: 150) partido en D0={u0,u1} y D1={u2,u3}: dos distritos mixtos.
        p = cadena([50, 75, 75, 50], municipio=["30001", "30002", "30002", "30003"])
        cfg = contrato(require_municipality_discipline=True, max_mixed_districts_per_split_municipality=2)
        self.assertEqual(codigos(p, cfg, plan(2, 2), max_mixtos="contrato"), set())
        self.assertEqual(codigos(p, cfg, plan(2, 2), max_mixtos="fijo_1"), {"R-MUN-MIXTOS"})
        cfg_sin = contrato(require_municipality_discipline=True)  # sin clave: 1 por política
        self.assertEqual(codigos(p, cfg_sin, plan(2, 2)), {"R-MUN-MIXTOS"})

    def test_8b_r012_min_y_max(self):
        cfg = contrato(require_municipality_discipline=True, expected_districts=3, population_cap_ratio=1.5)
        # Municipio pequeño (u1+u2 = 60 < objetivo 100) partido en dos: máx 1.
        p = cadena([100, 30, 30, 140], municipio=["30001", "30002", "30002", "30003"])
        self.assertIn("R-MUN-MAX", codigos(p, cfg, {"u0": "A", "u1": "A", "u2": "B", "u3": "C"}))
        # Municipio de 160 > techo 150 en un solo distrito: mín 2.
        p = cadena([80, 80, 70, 70], municipio=["30001", "30001", "30002", "30003"])
        self.assertIn("R-MUN-MIN", codigos(p, cfg, {"u0": "A", "u1": "A", "u2": "B", "u3": "C"}))


class OtrasReglas(unittest.TestCase):
    def test_razones_obligatorias_sin_defecto(self):
        for clave in ("population_floor_ratio", "population_cap_ratio", "target_tolerance_ratio",
                      "expected_districts"):
            cfg = contrato()
            del cfg["validation"][clave]
            with self.assertRaisesRegex(ErrorContrato, clave):
                Reglas.desde_contrato(cfg)

    def test_k_y_atomicidad(self):
        p = cadena([100, 100])
        self.assertEqual(codigos(p, contrato(), {"u0": "A", "u1": "A"}), {"R-K", "R-POB-TECHO"})
        self.assertIn("R-ATOM", codigos(p, contrato(), {"u0": "A", "u1": "B", "x": "B"}))
        self.assertIn("R-ATOM", codigos(p, contrato(), {"u0": "A"}))

    def test_contiguidad_con_y_sin_puentes(self):
        us = tuple(Unidad(f"u{i}", 50, municipio=f"3000{i}", provincia="30") for i in range(4))
        p = Problema(us, (("u0", "u1"), ("u2", "u3")), puentes=(("u1", "u2"),))
        asig = {"u0": "A", "u3": "A", "u1": "B", "u2": "B"}  # A = u0+u3 no conexo
        self.assertEqual(codigos(p, contrato(), asig), {"R-CONTIG"})
        asig = {"u0": "A", "u1": "A", "u2": "B", "u3": "B"}
        self.assertTrue(evaluar(p, Reglas.desde_contrato(contrato()), asig).valido)
        asig = {"u0": "A", "u1": "B", "u2": "B", "u3": "A"}  # B = u1-u2 solo por puente
        cfg = contrato(population_cap_ratio=1.6)
        self.assertIn("R-CONTIG", codigos(p, cfg, asig, contiguidad_con_puentes=True))  # A no conexo
        self.assertEqual(
            sorted(v.ambito for v in evaluar(p, Reglas.desde_contrato(cfg, Criterio(contiguidad_con_puentes=False)),
                                             asig).violaciones), ["A", "B"])

    def test_nucleo_cerrado(self):
        p = cadena([100, 50, 50], nucleo_cerrado=["N1", None, None])
        cfg = contrato()
        self.assertTrue(evaluar(p, Reglas.desde_contrato(cfg), plan(1, 2)).valido)
        p = cadena([60, 40, 100], nucleo_cerrado=["N1", None, None])
        self.assertEqual(codigos(p, cfg, plan(2, 1)), {"R-NUCLEO"})
        self.assertEqual(codigos(p, contrato(preserve_closed_urban=False), plan(2, 1)), set())

    def test_huella_estable_y_sensible_al_criterio(self):
        a = Reglas.desde_contrato(contrato()).huella()
        self.assertEqual(a, Reglas.desde_contrato(copy.deepcopy(contrato())).huella())
        self.assertNotEqual(a, Reglas.desde_contrato(contrato(), Criterio(tolerancia="dura")).huella())
        self.assertNotEqual(a, Reglas.desde_contrato(contrato(population_cap_ratio=1.16)).huella())

    def test_criterio_rechaza_opcion_desconocida(self):
        with self.assertRaises(ValueError):
            Criterio(tolerancia="blanda")


class VaraComun(unittest.TestCase):
    def test_variantes_y_resumen_por_opcion(self):
        self.assertEqual(len(variantes_criterio()), 36)
        p = cadena([113, 87])
        cfg = contrato(require_single_province_per_district=None)
        filas = comparar_criterios(p, cfg, plan(1, 1))
        self.assertEqual(len(filas), 36)
        base = [f for f in filas if f["criterio"] == {"tolerancia": "metrica", "max_mixtos": "contrato",
                                                     "provincia_defecto": "obligatoria",
                                                     "exencion_particion": "todas"}]
        self.assertEqual(base[0]["veredicto"], "ERROR_CONTRATO")
        res = {"T1": filas, "T2": comparar_criterios(cadena([100, 100]), contrato(), plan(1, 1))}
        resumen = resumen_por_opcion(res)
        # T1: ERROR_CONTRATO en la base; cambia con provincia_defecto=si/no. T2 no cambia con nada.
        self.assertEqual(resumen["provincia_defecto=si"], 1)
        self.assertEqual(resumen["provincia_defecto=no"], 1)
        self.assertEqual(resumen["tolerancia=dura"], 0)


class Metodo(unittest.TestCase):
    def test_presupuesto_por_defecto_y_comprobacion_posterior(self):
        r = Reglas.desde_contrato(contrato())
        p = cadena([100, 100])
        self.assertEqual(elegir_metodo(p, r, recuento={"completo": True, "nodos": 10}).metodo, "enumeracion")
        d = elegir_metodo(p, r, recuento={"completo": False, "nodos": 200_000},
                          diagnostico={"unique_state_ratio": 0.05, "self_loop_rate": 0.5})
        self.assertEqual((d.metodo, d.revisar), ("cadena", True))
        with self.assertRaises(ValueError):
            elegir_metodo(p, r)

    def test_tamano_y_diagnostico(self):
        p = cadena([100] * 50)
        r = Reglas.desde_contrato(contrato(expected_districts=5), Criterio(metodo="tamano"))
        self.assertEqual(elegir_metodo(p, r).metodo, "cadena")
        r = Reglas.desde_contrato(contrato(expected_districts=5), Criterio(metodo="diagnostico"))
        self.assertEqual(elegir_metodo(p, r, diagnostico={"unique_state_ratio": 0.5,
                                                          "self_loop_rate": 0.95}).metodo, "enumeracion")


class Aislamiento(unittest.TestCase):
    def test_produccion_no_importa_motor2(self):
        culpables = [str(f.relative_to(ROOT)) for d in ("modulos", "ddd_core", "ddd_ensemble")
                     for f in (ROOT / d).rglob("*.py") if "ddd_motor2" in f.read_text(encoding="utf-8", errors="ignore")]
        self.assertEqual(culpables, [])


if __name__ == "__main__":
    unittest.main()


# --------------------------------------------------------------------------- paso 2: estado, poda, enumeración
import random  # noqa: E402

from ddd_motor2.reglas import Estado, enumerar, podar  # noqa: E402


def _rejilla(rng, filas=2, cols=4, nucleos=False):
    us, ids = [], {}
    for f in range(filas):
        for c in range(cols):
            i = f * cols + c
            ids[(f, c)] = f"s{i}"
            us.append(Unidad(f"s{i}", rng.randint(20, 120), municipio=f"3000{rng.randint(1, 3)}",
                             provincia=rng.choice(["30", "30", "03"]), particion=rng.choice(["01", "02"]),
                             nucleo_cerrado=("N" if nucleos and i in (0, 1) else None)))
    aristas = [(ids[(f, c)], ids[(f, c + 1)]) for f in range(filas) for c in range(cols - 1)]
    aristas += [(ids[(f, c)], ids[(f + 1, c)]) for f in range(filas - 1) for c in range(cols)]
    return Problema(tuple(us), tuple(aristas))


def _contrato_aleatorio(rng, k, permisivo=False):
    return contrato(expected_districts=k, population_floor_ratio=0.3 if permisivo else rng.choice([0.5, 0.7]),
                    population_cap_ratio=1.9 if permisivo else rng.choice([1.3, 1.6]), target_tolerance_ratio=0.2,
                    require_single_province_per_district=rng.choice([True, False]),
                    require_municipality_discipline=rng.choice([True, False]),
                    population_floor_exempt_municipalities=rng.choice([[], ["30002"]]),
                    population_floor_exempt_partitions=rng.choice([[], ["02"]]),
                    preserve_closed_urban=True)


def _todas_las_particiones(ids, k):
    """Cadenas de crecimiento restringido: cada partición en ≤k bloques una sola vez (fuerza bruta independiente)."""
    def rec(i, usadas, actual):
        if i == len(ids):
            yield dict(zip(ids, actual))
            return
        for d in range(min(usadas + 1, k)):
            yield from rec(i + 1, max(usadas, d + 1), actual + [f"B{d}"])
    yield from rec(0, 0, [])


def _canon(asig):
    bloques = {}
    for u, d in asig.items():
        bloques.setdefault(d, set()).add(u)
    return frozenset(frozenset(b) for b in bloques.values())


class EstadoIncremental(unittest.TestCase):
    def test_invariante_estado_igual_a_evaluar(self):
        rng = random.Random(160)
        for caso in range(30):
            p = _rejilla(rng, nucleos=caso % 3 == 0)
            k = rng.choice([2, 3])
            for crit in (Criterio(), Criterio(tolerancia="dura", exencion_particion="alguna")):
                r = Reglas.desde_contrato(_contrato_aleatorio(rng, k), crit)
                asig = {u.id: f"D{rng.randrange(k)}" for u in p.unidades}
                e = Estado(p, r, asig)
                for _ in range(40):
                    u = rng.choice(p.unidades).id
                    d = f"D{rng.randrange(k + 1)}"
                    antes = e.violaciones()
                    valido = e.movimiento_valido(u, d)
                    self.assertEqual(e.violaciones(), antes)  # prueba y deshace sin efecto
                    e.aplicar(u, d)
                    asig[u] = d
                    esperado = evaluar(p, r, asig).violaciones
                    self.assertEqual(e.violaciones(), esperado)
                    nuevas = {(v.regla, v.ambito) for v in esperado} - {(v.regla, v.ambito) for v in antes}
                    self.assertEqual(valido, not nuevas)


class Enumeracion(unittest.TestCase):
    def test_enumerador_igual_a_fuerza_bruta(self):
        rng = random.Random(7)
        total_validos = 0
        for caso in range(25):
            p = _rejilla(rng, nucleos=caso % 4 == 0)
            k = rng.choice([2, 3])
            r = Reglas.desde_contrato(_contrato_aleatorio(rng, k))
            bruta = {_canon(a) for a in _todas_las_particiones([u.id for u in p.unidades], k)
                     if evaluar(p, r, a).valido}
            res = enumerar(p, r, presupuesto=10**6, max_planes=10**6)
            self.assertTrue(res["completo"])
            self.assertEqual({_canon(a) for a in res["planes"]}, bruta, f"caso {caso}")
            self.assertEqual(res["validos"], len(bruta))
            total_validos += len(bruta)
        self.assertGreater(total_validos, 0)  # el test no es vacuo

    def test_poda_monotona(self):
        """Si podar() marca un parcial, ninguna extensión completa es válida."""
        rng = random.Random(11)
        n_validos = n_podados = 0
        for caso in range(15):
            p = _rejilla(rng, cols=4, nucleos=caso % 4 == 0)
            k = rng.choice([2, 3])
            r = Reglas.desde_contrato(_contrato_aleatorio(rng, k, permisivo=caso % 3 != 0),
                                      Criterio(tolerancia=rng.choice(["metrica", "dura"])))
            ids = [u.id for u in p.unidades]
            validos = [a for a in _todas_las_particiones(ids, k) if evaluar(p, r, a).valido]
            n_validos += len(validos)
            for _ in range(60):
                fijas = rng.sample(ids, rng.randint(1, len(ids) - 1))
                parcial = {u: f"B{rng.randrange(k)}" for u in fijas}
                if podar(p, r, parcial):
                    n_podados += 1
                    for a in validos:  # ninguna partición válida extiende el parcial (salvo renombrar bloques)
                        mapa = {}
                        coincide = all(mapa.setdefault(parcial[u], a[u]) == a[u] for u in fijas)
                        coincide = coincide and len(set(mapa.values())) == len(mapa)
                        self.assertFalse(coincide, f"caso {caso}: poda {podar(p, r, parcial)} con extensión válida")
        self.assertGreater(n_validos, 30)  # no vacuo (39 con la semilla 11)
        self.assertGreater(n_podados, 100)

    def test_presupuesto_agotado_no_es_completo(self):
        p = _rejilla(random.Random(1), cols=4)
        r = Reglas.desde_contrato(contrato(expected_districts=2, population_floor_ratio=0.1,
                                           population_cap_ratio=1.9, require_single_province_per_district=False))
        res = enumerar(p, r, presupuesto=5)
        self.assertEqual((res["completo"], res["huella"]), (False, ""))
        d = elegir_metodo(p, r, recuento=res)
        self.assertEqual(d.metodo, "cadena")
        self.assertEqual(elegir_metodo(p, r, recuento=enumerar(p, r)).metodo, "enumeracion")

    def test_recuento_literal_cadena_de_cuatro(self):
        # u0-u1-u2-u3, todas 100, K=2, objetivo 200. Particiones contiguas de una cadena de 4 en 2 bloques: 3
        # ({u0}{u1u2u3}, {u0u1}{u2u3}, {u0u1u2}{u3}); con suelo 100 y techo 320 valen las 3.
        p = cadena([100, 100, 100, 100], provincia="30")
        r = Reglas.desde_contrato(contrato(population_floor_ratio=0.5, population_cap_ratio=1.6))
        self.assertEqual(enumerar(p, r)["validos"], 3)
        r = Reglas.desde_contrato(contrato(population_floor_ratio=0.9, population_cap_ratio=1.1))
        self.assertEqual(enumerar(p, r)["validos"], 1)  # solo {u0,u1}{u2,u3}
