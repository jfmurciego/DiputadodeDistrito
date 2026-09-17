#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: pruebas de fuentes oficiales y preparación territorial
VERSIÓN: 1.1.0
NOMBRE DE VERSIÓN: Modos reales, negativos y consumo M01
FECHA: 2026-09-17
ESTADO: candidato
FUNCIÓN: demostrar trazabilidad estricta, bloqueo fail-closed y preparación sintética consumible.
CAMBIOS: cubre HTML, edición, provincias, territorio, checksum, no-red, igualdad de evidencia e integración Extremadura.
MOTIVO: asegurar que ninguna fuente incoherente habilita la generación de distritos.
ANTERIOR: legacy/tests/test_fuentes_oficiales_preparacion_v1.0.0.py
"""
from __future__ import annotations

import copy
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import yaml

from herramientas.adquirir_fuentes_oficiales import acquire
from herramientas.evaluar_preparacion_territorial import evaluate, readable_report

ROOT = Path(__file__).resolve().parents[1]
CATALOG = yaml.safe_load((ROOT / "fuentes/catalogo_oficial.yaml").read_text(encoding="utf-8"))


def declaration(territory: str) -> dict:
    return yaml.safe_load((ROOT / "territorios" / territory / "config" / "fuentes_oficiales.yaml").read_text(encoding="utf-8"))


class SimulatedINE:
    def __init__(self, declaration_data: dict, *, edition: int | None = None, omit_population_province: str | None = None, unexpected_section_province: str | None = None, html_population: bool = False):
        self.declaration = declaration_data
        self.edition = edition if edition is not None else int(declaration_data["territory"]["edition"])
        self.omit_population_province = omit_population_province
        self.unexpected_section_province = unexpected_section_province
        self.html_population = html_population
        expected = int(declaration_data["coverage_checks"]["expected_sections"])
        divisions = declaration_data["territory"]["territorial_codes"]
        base, remainder = divmod(expected, len(divisions))
        self.counts = {str(row["code"]).zfill(2): base + (1 if index < remainder else 0) for index, row in enumerate(divisions)}

    def section_ids(self):
        for code, count in self.counts.items():
            for index in range(count):
                yield code, f"{code}{index:08d}"

    def __call__(self, url: str) -> bytes:
        if "65034.csv" in url:
            if self.html_population:
                return b"<!doctype html><html><body>error</body></html>"
            out = io.StringIO()
            out.write("Periodo\tSexo\tEdad\tSecciones\tTotal\n")
            for code, section in self.section_ids():
                if code == self.omit_population_province:
                    continue
                out.write(f"{self.edition}\tTotal\tTodas las edades\t{section}\t100\n")
            return ("\ufeff" + out.getvalue()).encode("utf-8")
        query = parse_qs(urlparse(url).query)
        filter_text = query["filter"][0]
        requested = next(code for code in self.counts if f"CPRO='{code}'" in filter_text)
        actual = self.unexpected_section_province if self.unexpected_section_province and requested == sorted(self.counts)[0] else requested
        features = []
        for index in range(self.counts[requested]):
            section = f"{requested}{index:08d}"
            features.append({"type": "Feature", "properties": {"CPRO": actual, "TIPO": "SECCION", "CUSEC": section}, "geometry": {"type": "Point", "coordinates": [-6.0 + index * 0.00001, 39.0]}})
        return json.dumps({"type": "FeatureCollection", "features": features}).encode("utf-8")


class OfficialSourcesTests(unittest.TestCase):
    def materialize(self, territory: str, fetcher=None):
        dec = copy.deepcopy(declaration(territory))
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        evidence = root / "evidence"
        for source_id, binding in dec["source_bindings"].items():
            original = Path(binding["materialized_path"])
            binding["materialized_path"] = str(root / original)
        fetcher = fetcher or SimulatedINE(dec)
        resolved, inventory, provenance, acquisition = acquire(catalog=CATALOG, declaration=dec, evidence_dir=evidence, environment="test", acquisition_mode="simulated", fetcher=fetcher, root_dir=root)
        return td, root, evidence, dec, resolved, inventory, provenance, acquisition

    def evaluate_materialized(self, dec, root, resolved, inventory, provenance, acquisition):
        return evaluate(catalog=CATALOG, declaration=dec, resolved_declaration=resolved, inventory=inventory, provenance=provenance, environment="test", root_dir=root, acquisition_decision=acquisition)

    def test_aragon_remains_declarative_regression(self):
        dec = declaration("aragon")
        self.assertEqual(dec["territory"]["id"], "aragon")
        self.assertEqual([row["code"] for row in dec["territory"]["territorial_codes"]], ["22", "44", "50"])
        self.assertEqual(dec["coverage_checks"]["expected_sections"], 1463)

    def test_simulation_is_rejected_outside_test(self):
        dec = declaration("extremadura")
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(RuntimeError):
                acquire(catalog=CATALOG, declaration=dec, evidence_dir=Path(td), environment="production", acquisition_mode="simulated", fetcher=SimulatedINE(dec), root_dir=Path(td))

    def test_html_instead_of_csv_blocks_and_preserves_evidence(self):
        dec0 = declaration("extremadura")
        fetcher = SimulatedINE(dec0, html_population=True)
        td, root, evidence, dec, resolved, inventory, provenance, acquisition = self.materialize("extremadura", fetcher=fetcher)
        self.addCleanup(td.cleanup)
        self.assertEqual(acquisition["decision"], "BLOCKED")
        self.assertTrue((evidence / "inventario_fuentes.json").is_file())
        self.assertTrue((evidence / "decision_adquisicion.json").is_file())
        self.assertIn("HTML", json.dumps(acquisition, ensure_ascii=False))

    def test_wrong_edition_blocks(self):
        dec0 = declaration("extremadura")
        fetcher = SimulatedINE(dec0, edition=2024)
        td, root, evidence, dec, resolved, inventory, provenance, acquisition = self.materialize("extremadura", fetcher=fetcher)
        self.addCleanup(td.cleanup)
        self.assertEqual(acquisition["decision"], "BLOCKED")
        self.assertIn("edición 2025", json.dumps(acquisition, ensure_ascii=False).lower())

    def test_missing_province_blocks(self):
        dec0 = declaration("extremadura")
        fetcher = SimulatedINE(dec0, omit_population_province="10")
        td, root, evidence, dec, resolved, inventory, provenance, acquisition = self.materialize("extremadura", fetcher=fetcher)
        self.addCleanup(td.cleanup)
        self.assertEqual(acquisition["decision"], "BLOCKED")
        self.assertIn("cobertura provincial", json.dumps(acquisition, ensure_ascii=False).lower())

    def test_unexpected_province_blocks(self):
        dec0 = declaration("extremadura")
        fetcher = SimulatedINE(dec0, unexpected_section_province="99")
        td, root, evidence, dec, resolved, inventory, provenance, acquisition = self.materialize("extremadura", fetcher=fetcher)
        self.addCleanup(td.cleanup)
        self.assertEqual(acquisition["decision"], "BLOCKED")
        self.assertIn("provincia inesperada", json.dumps(acquisition, ensure_ascii=False).lower())

    def test_inventory_from_other_territory_blocks(self):
        td, root, evidence, dec, resolved, inventory, provenance, acquisition = self.materialize("extremadura")
        self.addCleanup(td.cleanup)
        inventory = copy.deepcopy(inventory)
        inventory["territory_id"] = "aragon"
        decision = self.evaluate_materialized(dec, root, resolved, inventory, provenance, acquisition)
        self.assertEqual(decision["decision"], "BLOCKED")
        self.assertTrue(any("territory_id" in reason for reason in decision["reasons"]))

    def test_exact_source_fields_must_match(self):
        td, root, evidence, dec, resolved, inventory, provenance, acquisition = self.materialize("extremadura")
        self.addCleanup(td.cleanup)
        for field, replacement in (("path", "otra/ruta.zip"), ("sha256", "0" * 64), ("bytes", 7), ("urls", ["https://example.invalid"]), ("edition", 2024), ("source_id", "otra_fuente")):
            mutated = copy.deepcopy(inventory)
            mutated["sources"][0][field] = replacement
            decision = self.evaluate_materialized(dec, root, resolved, mutated, provenance, acquisition)
            self.assertEqual(decision["decision"], "BLOCKED", field)

    def test_wrong_snapshot_hash_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            raw = b"Periodo\tSexo\tEdad\tSecciones\tTotal\n2025\tTotal\tTodas las edades\t0600000001\t1\n"
            snapshot = root / "snapshot.csv"
            snapshot.write_bytes(raw)
            dec = {
                "territory": {"id": "x", "business_name": "X", "edition": 2025, "territorial_codes": [{"code": "06", "business_name": "Badajoz"}]},
                "required_sources": ["poblacion_por_sexo_y_edad"],
                "source_bindings": {"poblacion_por_sexo_y_edad": {"materialized_path": str(root / "out.zip"), "archive_member": "65034.csv", "snapshot": {"path": str(snapshot), "expected_sha256": "0" * 64, "official_origin_url": CATALOG["sources"]["poblacion_por_sexo_y_edad"]["url"], "edition": 2025, "acquired_at": "2026-09-17"}}},
                "population_validation": {"required_columns": ["Periodo", "Sexo", "Edad", "Secciones", "Total"]},
                "environment_policy": {"production": ["verified_snapshot"]},
                "default_mode": {"production": "verified_snapshot"},
            }
            _, _, _, acquisition = acquire(catalog=CATALOG, declaration=dec, evidence_dir=root / "evidence", environment="production", acquisition_mode="verified_snapshot", root_dir=root)
            self.assertEqual(acquisition["decision"], "BLOCKED")
            self.assertIn("Huella", json.dumps(acquisition, ensure_ascii=False))

    def test_verified_snapshot_never_falls_back_to_network(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            dec = copy.deepcopy(declaration("extremadura"))
            dec["required_sources"] = ["poblacion_por_sexo_y_edad"]
            binding = dec["source_bindings"]["poblacion_por_sexo_y_edad"]
            binding["materialized_path"] = str(root / "out.zip")
            del binding["snapshot"]["path"]
            calls = []
            def forbidden(url: str) -> bytes:
                calls.append(url)
                raise AssertionError("la copia verificada no puede usar red")
            _, _, _, acquisition = acquire(catalog=CATALOG, declaration=dec, evidence_dir=root / "evidence", environment="production", acquisition_mode="verified_snapshot", fetcher=forbidden, root_dir=root)
            self.assertEqual(acquisition["decision"], "BLOCKED")
            self.assertEqual(calls, [])
            self.assertIn("path", json.dumps(acquisition, ensure_ascii=False))

    def test_source_unavailable_preserves_blocking_inventory(self):
        dec0 = declaration("extremadura")
        normal = SimulatedINE(dec0)
        def unavailable(url: str) -> bytes:
            if "65034.csv" in url:
                raise RuntimeError("fuente no disponible")
            return normal(url)
        td, root, evidence, dec, resolved, inventory, provenance, acquisition = self.materialize("extremadura", fetcher=unavailable)
        self.addCleanup(td.cleanup)
        self.assertEqual(acquisition["decision"], "BLOCKED")
        row = next(row for row in inventory["sources"] if row["source_id"] == "poblacion_por_sexo_y_edad")
        self.assertEqual(row["availability"], "BLOCKED")
        self.assertTrue((evidence / "inventario_fuentes.json").is_file())

    def test_extremadura_simulation_ready_and_inputs_are_consumable_by_m01(self):
        td, root, evidence, dec, resolved, inventory, provenance, acquisition = self.materialize("extremadura")
        self.addCleanup(td.cleanup)
        decision = self.evaluate_materialized(dec, root, resolved, inventory, provenance, acquisition)
        self.assertEqual(acquisition["decision"], "READY")
        self.assertEqual(decision["decision"], "READY")
        self.assertEqual(decision["territory_id"], "extremadura")
        self.assertEqual(inventory["territorial_coverage"], ["06", "10"])
        for name in ("inventario_fuentes.json", "manifiesto_procedencia.json", "decision_adquisicion.json", "declaracion_materializacion.json"):
            self.assertTrue((evidence / name).is_file(), name)
        (evidence / "decision_preparacion.json").write_text(json.dumps(decision, ensure_ascii=False, indent=2), encoding="utf-8")
        (evidence / "informe_preparacion.md").write_text(readable_report(decision), encoding="utf-8")
        self.assertTrue((evidence / "informe_preparacion.md").is_file())

        spec = importlib.util.spec_from_file_location("ddd_m01_test", ROOT / "modulos/01_preparar_base_territorial.py")
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)
        section_path = Path(dec["source_bindings"]["secciones_censales"]["materialized_path"])
        population_path = Path(dec["source_bindings"]["poblacion_por_sexo_y_edad"]["materialized_path"])
        gdf = module.load_seccionado(str(section_path), "", ["06", "10"])
        cip = module.load_cip([str(population_path)], "Secciones", "Total", 2025, "auto", {"year_col": "Periodo", "sexo_col": "Sexo", "edad_col": "Edad", "sexo_total_values": ["Total"], "edad_total_values": ["Todas las edades"], "year_value": 2025}, ["06", "10"])
        self.assertEqual(len(gdf), 964)
        self.assertEqual(len(cip), 964)


if __name__ == "__main__":
    unittest.main()
