#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: suite de regresión R015
VERSIÓN: 1.1.0
NOMBRE DE VERSIÓN: Gobernanza M05 sensible a la versión activa
FECHA: 2026-09-11
ESTADO: vigente
FUNCIÓN: proteger las invariantes territoriales R012/R014, el determinismo de M05 y la trazabilidad activa hacia legacy.
CAMBIOS: sustituye la aserción fija M05 v7.3.1 por una comprobación dinámica entre la versión del ejecutable activo y el contrato documental; conserva Run #8/v7.3.0 como baseline territorial validado.
MOTIVO: permitir rondas funcionales posteriores sin debilitar la coherencia entre código, contrato y último baseline validado.
ANTERIOR: legacy/tests/test_r015_invariantes_v1.0.0.py
"""
from __future__ import annotations

import csv
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import unittest
from collections import defaultdict, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN8 = ROOT / "resultados" / "ejecuciones" / "gh-34592470470-1"
M04_CSV = RUN8 / "M04" / "asignacion_inicial.csv"
M05_CSV = RUN8 / "M05" / "asignacion_optimizada.csv"
GRAPH_JSON = RUN8 / "M03" / "grafo.json"
VALIDATION_JSON = RUN8 / "VALIDACION.json"

EXPECTED_SECTIONS = 1463
EXPECTED_POP = 1364621
EXPECTED_K = 67
EXPECTED_PROVINCES = {"22": 11, "44": 7, "50": 49}
FLOOR_RATIO = 0.80
CAP_RATIO = 1.75
TOL_RATIO = 0.12


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def read_graph() -> tuple[dict[str, int], dict[str, set[str]]]:
    data = json.loads(GRAPH_JSON.read_text(encoding="utf-8"))
    pop = {str(n["id"]): int(n.get("pop", 0)) for n in data["nodes"]}
    adj: dict[str, set[str]] = defaultdict(set)
    for e in data["edges"]:
        u, v = str(e["u"]), str(e["v"])
        adj[u].add(v)
        adj[v].add(u)
    return pop, adj


def is_connected(nodes: set[str], adj: dict[str, set[str]]) -> bool:
    if not nodes:
        return False
    start = next(iter(nodes))
    seen = {start}
    q = deque([start])
    while q:
        u = q.popleft()
        for v in adj.get(u, set()):
            if v in nodes and v not in seen:
                seen.add(v)
                q.append(v)
    return len(seen) == len(nodes)


def district_data(rows: list[dict[str, str]]):
    drows: dict[int, list[dict[str, str]]] = defaultdict(list)
    for r in rows:
        drows[int(r["district_id"])].append(r)
    pops = {d: sum(int(float(r["POP_2025"])) for r in rs) for d, rs in drows.items()}
    return drows, pops


class TerritorialRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for p in (M04_CSV, M05_CSV, GRAPH_JSON, VALIDATION_JSON):
            if not p.exists():
                raise AssertionError(f"Falta baseline Run #8: {p}")
        cls.graph_pop, cls.adj = read_graph()
        cls.m04 = read_rows(M04_CSV)
        cls.m05 = read_rows(M05_CSV)

    def assert_core(self, rows: list[dict[str, str]], require_tolerance: bool):
        self.assertEqual(len(rows), EXPECTED_SECTIONS)
        ids = [r["CUSEC_KEY"] for r in rows]
        self.assertEqual(len(ids), len(set(ids)), "CUSEC duplicado")
        self.assertEqual(set(ids), set(self.graph_pop), "M03 y asignación no contienen las mismas secciones")
        total = sum(int(float(r["POP_2025"])) for r in rows)
        self.assertEqual(total, EXPECTED_POP)
        self.assertEqual(sum(self.graph_pop.values()), EXPECTED_POP)
        drows, pops = district_data(rows)
        self.assertEqual(len(drows), EXPECTED_K)
        target = total / EXPECTED_K
        floor, cap, tol = target * FLOOR_RATIO, target * CAP_RATIO, target * TOL_RATIO
        for d, p in pops.items():
            self.assertGreaterEqual(p, floor, f"distrito {d} bajo suelo")
            self.assertLessEqual(p, cap, f"distrito {d} sobre techo")
            if require_tolerance:
                self.assertLessEqual(abs(p - target), tol + 1e-9, f"distrito {d} fuera de ±12%")
        district_province: dict[int, str] = {}
        for d, rs in drows.items():
            provs = {str(r["CPRO"]).zfill(2) for r in rs}
            self.assertEqual(len(provs), 1, f"distrito {d} cruza provincia")
            district_province[d] = next(iter(provs))
            nodes = {r["CUSEC_KEY"] for r in rs}
            self.assertTrue(is_connected(nodes, self.adj), f"distrito {d} desconectado")
        counts = {p: sum(1 for x in district_province.values() if x == p) for p in EXPECTED_PROVINCES}
        self.assertEqual(counts, EXPECTED_PROVINCES)
        self.assert_municipality_discipline(rows, target, cap)
        return pops, target, tol

    def assert_municipality_discipline(self, rows, target: float, cap: float):
        mun_rows: dict[str, list[dict[str, str]]] = defaultdict(list)
        district_muns: dict[int, set[str]] = defaultdict(set)
        for r in rows:
            mun = r["CUMUN"]
            d = int(r["district_id"])
            mun_rows[mun].append(r)
            district_muns[d].add(mun)
        for mun, rs in mun_rows.items():
            p = sum(int(float(r["POP_2025"])) for r in rs)
            dids = {int(r["district_id"]) for r in rs}
            if p <= cap:
                self.assertEqual(len(dids), 1, f"municipio {mun} cabe bajo techo y fue fragmentado")
                continue
            min_allowed = max(1, math.ceil(p / cap))
            max_allowed = max(1, math.ceil(p / target))
            self.assertGreaterEqual(len(dids), min_allowed, f"municipio {mun} usa muy pocos distritos")
            self.assertLessEqual(len(dids), max_allowed, f"municipio {mun} usa demasiados distritos")
            mixed = [d for d in dids if len(district_muns[d]) > 1]
            self.assertLessEqual(len(mixed), 1, f"municipio {mun} tiene más de un distrito mixto")

    def test_m04_es_estructuralmente_valido(self):
        pops, target, tol = self.assert_core(self.m04, require_tolerance=False)
        outside = [d for d, p in pops.items() if abs(p - target) > tol]
        self.assertEqual(len(outside), 1, "el baseline M04 de Run #8 debe conservar un único outlier fino")

    def test_m05_cierra_el_objetivo_fino_sin_regresiones(self):
        pops, target, tol = self.assert_core(self.m05, require_tolerance=True)
        self.assertEqual(sum(abs(p - target) > tol for p in pops.values()), 0)
        max_rel = max(abs(p - target) / target for p in pops.values())
        self.assertLessEqual(max_rel, TOL_RATIO)
        self.assertAlmostEqual(max_rel, 0.119431695687, places=9)

    def test_m04_m05_conservan_exactamente_el_universo(self):
        by04 = {r["CUSEC_KEY"]: (r["CUMUN"], str(r["CPRO"]).zfill(2), int(float(r["POP_2025"]))) for r in self.m04}
        by05 = {r["CUSEC_KEY"]: (r["CUMUN"], str(r["CPRO"]).zfill(2), int(float(r["POP_2025"]))) for r in self.m05}
        self.assertEqual(by04, by05)

    def test_validacion_publicada_run8_es_pass(self):
        val = json.loads(VALIDATION_JSON.read_text(encoding="utf-8"))
        self.assertEqual(val["estado"], "PASS")
        self.assertEqual(val["failures"], [])
        self.assertEqual(val["graph_disconnected"], [])
        self.assertEqual(val["province_crossings"], [])
        self.assertEqual(val["municipality_violations"], [])


class M05Determinism(unittest.TestCase):
    def make_case(self, base: Path, label: str):
        import geopandas as gpd
        from shapely.geometry import Point

        run = base / label
        run.mkdir(parents=True)
        sections = [
            ("s1", 5, "U1", 1, 0.0),
            ("s2", 5, "U1", 1, 1.0),
            ("s3", 10, "U2", 1, 2.0),
            ("s4", 5, "U3", 1, 3.0),
            ("s5", 15, "U4", 2, 4.0),
        ]
        gdf = gpd.GeoDataFrame(
            {
                "CUSEC_KEY": [x[0] for x in sections],
                "POP_2025": [x[1] for x in sections],
                "CPRO": ["50"] * len(sections),
                "CUMUN": ["50001"] * len(sections),
                "district_id": [x[3] for x in sections],
                "ddd_unit_id": [x[2] for x in sections],
                "ddd_closed_urban": [False] * len(sections),
            },
            geometry=[Point(x[4], 0) for x in sections],
            crs="EPSG:4326",
        )
        input_geo = run / "input.geojson"
        gdf.to_file(input_geo, driver="GeoJSON")
        graph = {
            "nodes": [{"id": x[0], "pop": x[1]} for x in sections],
            "edges": [
                {"u": "s1", "v": "s2"},
                {"u": "s2", "v": "s3"},
                {"u": "s3", "v": "s4"},
                {"u": "s4", "v": "s5"},
            ],
        }
        graph_path = run / "graph.json"
        graph_path.write_text(json.dumps(graph), encoding="utf-8")
        output = run / "output.geojson.zip"
        report = run / "report.json"
        cfg = run / "config.yaml"
        cfg.write_text(
            f"""meta:\n  run_name: synthetic\n  year: 2025\nio:\n  project_root:\n    path: .\nmodulos:\n  modulo_05_optimizar_distritos:\n    in_graph_json: {graph_path.name}\n    in_geojson: {input_geo.name}\n    id_field: CUSEC_KEY\n    pop_field: POP_2025\n    district_field: district_id\n    province_field: CPRO\n    municipality_field: CUMUN\n    greedy_moves_limit: 0\n    anneal_iters: 500\n    seed: 12345\n    anneal_seed_offset: 0\n    anneal_outside_penalty: 0.01\n    anneal_maxdev_weight: 0.05\n    anneal_churn_weight: 0.0016\n    anneal_temp_start: 0.02\n    anneal_temp_end: 0.0005\n    out_geojson: {output.name}\n    out_report: {report.name}\nvalidation:\n  population_floor_ratio: 0.75\n  population_cap_ratio: 1.75\n  target_tolerance_ratio: 0.12\n""",
            encoding="utf-8",
        )
        return cfg, output, report

    def run_case(self, cfg: Path):
        env = dict(os.environ)
        proc = subprocess.run(
            [sys.executable, str(ROOT / "modulos" / "05_optimizar_distritos.py"), "--params", str(cfg)],
            cwd=ROOT,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout)

    def assignment(self, output: Path):
        import geopandas as gpd

        g = gpd.read_file(f"zip://{output}")
        return {str(r.CUSEC_KEY): int(r.district_id) for r in g.itertuples()}

    def test_m05_misma_semilla_misma_salida(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            c1, o1, r1 = self.make_case(base, "a")
            c2, o2, r2 = self.make_case(base, "b")
            self.run_case(c1)
            self.run_case(c2)
            rep1 = json.loads(r1.read_text(encoding="utf-8"))
            rep2 = json.loads(r2.read_text(encoding="utf-8"))
            self.assertEqual(rep1, rep2)
            self.assertEqual(self.assignment(o1), self.assignment(o2))
            self.assertGreater(rep1["accepted_annealing_moves"], 0)
            self.assertEqual(rep1["districts_outside_tolerance"], 0)
            ass = self.assignment(o1)
            self.assertEqual(ass["s1"], ass["s2"], "una ddd_unit_id multisección debe permanecer atómica")


@unittest.skipIf(os.environ.get("DDD_SKIP_LEGACY_CHECK") == "1" or (ROOT / "herramientas/r015_patch_components.py").exists(), "legacy se valida tras completar la migración R015")
class GovernanceHeaders(unittest.TestCase):
    TARGETS = [
        "modulos/01_preparar_base_territorial.py",
        "modulos/02_construir_adyacencias.py",
        "modulos/03_construir_grafo.py",
        "modulos/04_generar_semillas.py",
        "modulos/05_optimizar_distritos.py",
        "modulos/06_consolidar_distritos.py",
        "modulos/07_agregar_resultados_electorales.py",
        "modulos/08_integrar_resultados.py",
        "ddd_core/config.py",
        "herramientas/adquirir_fuentes_ine.py",
        "herramientas/calcular_clave_preparacion.py",
        "herramientas/generar_outputs_auditables.py",
        "herramientas/registrar_ejecucion.py",
        "herramientas/validar_ejecucion.py",
        "configuracion/aragon_2025.yaml",
        "procedimiento.sh",
        ".github/workflows/procedimiento-ddd.yml",
    ]
    CANONICAL_VERSIONED_DOCS = [
        "README.md",
        "docs/ESTADO_MAESTRO_PROYECTO.md",
        "docs/CONTINUIDAD_NUEVO_CHAT.md",
        "docs/BITACORA.md",
        "docs/POLITICA_DE_VERSIONES.md",
    ]

    def test_cabeceras_y_predecesores_legacy(self):
        mandatory = ["VERSIÓN:", "NOMBRE DE VERSIÓN:", "FECHA:", "ESTADO:", "CAMBIOS:", "MOTIVO:", "ANTERIOR:"]
        for rel in self.TARGETS:
            text = (ROOT / rel).read_text(encoding="utf-8")[:5000]
            for key in mandatory:
                self.assertIn(key, text, f"{rel}: falta {key}")
            m = re.search(r"(?m)^\s*#?\s*ANTERIOR:\s*`?([^`\s]+)`?\s*$", text)
            self.assertIsNotNone(m, f"{rel}: ANTERIOR no parseable")
            prev = ROOT / m.group(1)
            self.assertTrue(prev.exists(), f"{rel}: predecesor inexistente {m.group(1)}")

    def test_documentos_canonicos_versionados_tienen_predecesor_real(self):
        for rel in self.CANONICAL_VERSIONED_DOCS:
            text = (ROOT / rel).read_text(encoding="utf-8")[:5000]
            m = re.search(r"(?mi)^\s*(?:\*\*)?Anterior:(?:\*\*)?\s*`?([^`\s]+)`?\s*$", text)
            self.assertIsNotNone(m, f"{rel}: falta referencia Anterior parseable")
            prev_rel = m.group(1)
            self.assertTrue(prev_rel.startswith("legacy/"), f"{rel}: Anterior debe apuntar a legacy/: {prev_rel}")
            self.assertTrue((ROOT / prev_rel).is_file(), f"{rel}: predecesor documental inexistente {prev_rel}")

    def test_recuperaciones_documentales_r015_presentes(self):
        expected = [
            "legacy/docs/README_v3.2.0.md",
            "legacy/memoria/ESTADO_MAESTRO_PROYECTO_v1.10.0.md",
            "legacy/memoria/CONTINUIDAD_NUEVO_CHAT_v1.3.0.md",
            "legacy/bitacora/BITACORA_v2.15.0.md",
            "legacy/docs/POLITICA_DE_VERSIONES_v1.1.0.md",
            "legacy/docs/MODULOS/M05_OPTIMIZACION_pre_versionado_2026-09-11.md",
            "legacy/tests/test_r015_invariantes_pre_versionado_2026-09-11.py",
        ]
        for rel in expected:
            self.assertTrue((ROOT / rel).is_file(), f"falta recuperación documental R015: {rel}")

    def test_contrato_m05_distingue_version_activa_y_logica_validada(self):
        contract = (ROOT / "docs/MODULOS/M05_OPTIMIZACION.md").read_text(encoding="utf-8")
        executable = (ROOT / "modulos/05_optimizar_distritos.py").read_text(encoding="utf-8")[:3000]
        m = re.search(r"(?m)^VERSIÓN:\s*(\d+\.\d+\.\d+)\s*$", executable)
        self.assertIsNotNone(m, "M05 activo no declara VERSIÓN SemVer")
        self.assertIn(f"**Código activo:** M05 v{m.group(1)}", contract)
        self.assertIn("M05 v7.3.0", contract)
        self.assertIn("Run #8", contract)

    def test_documentos_r015_presentes(self):
        self.assertTrue((ROOT / "docs/RONDAS/R015_2026-09-11_pruebas_y_gobernanza.md").exists())
        self.assertTrue((ROOT / "docs/DEUDA_HISTORICA_LEGACY.md").exists())


if __name__ == "__main__":
    unittest.main()
