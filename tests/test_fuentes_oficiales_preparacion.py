#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: pruebas de fuentes oficiales y preparación territorial
VERSIÓN: 1.2.0
NOMBRE DE VERSIÓN: Inmutabilidad nacional y aislamiento territorial
FECHA: 2026-09-17
ESTADO: candidato
FUNCIÓN: demostrar que las copias oficiales nacionales son inmutables y los recortes territoriales quedan aislados y consumibles.
CAMBIOS: añade regresiones origen/destino, huellas nacionales, preparación consecutiva Aragón-Extremadura y consumo desde ddd-official-inputs.
MOTIVO: impedir que preparar un territorio mutile la fuente nacional compartida o contamine la preparación del siguiente.
ANTERIOR: legacy/tests/test_fuentes_oficiales_preparacion_v1.1.0.py
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import yaml

from herramientas.adquirir_fuentes_oficiales import acquire, _filter_population, _write_shapefile_zip, _zip_single
from herramientas.evaluar_preparacion_territorial import evaluate, readable_report

ROOT = Path(__file__).resolve().parents[1]
CATALOG = yaml.safe_load((ROOT / "fuentes/catalogo_oficial.yaml").read_text(encoding="utf-8"))

SYNTHETIC_EXPECTED_SECTIONS = {
    "aragon": 1463,
    "extremadura": 964,
}


def declaration(territory: str) -> dict:
    return yaml.safe_load((ROOT / "territorios" / territory / "config" / "fuentes_oficiales.yaml").read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class SimulatedINE:
    def __init__(self, declaration_data: dict, *, expected_sections: int | None = None, edition: int | None = None, omit_population_province: str | None = None, unexpected_section_province: str | None = None, html_population: bool = False):
        self.declaration = declaration_data
        self.edition = edition if edition is not None else int(declaration_data["territory"]["edition"])
        self.omit_population_province = omit_population_province
        self.unexpected_section_province = unexpected_section_province
        self.html_population = html_population
        territory_id = str(declaration_data["territory"]["id"])
        expected = expected_sections if expected_sections is not None else SYNTHETIC_EXPECTED_SECTIONS[territory_id]
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
        test_modes = list((dec.setdefault("environment_policy", {}).get("test") or []))
        if "simulated" not in test_modes:
            test_modes.append("simulated")
        dec["environment_policy"]["test"] = test_modes
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        evidence = root / "evidence"
        fetcher = fetcher or SimulatedINE(dec)
        resolved, inventory, provenance, acquisition = acquire(catalog=CATALOG, declaration=dec, evidence_dir=evidence, environment="test", acquisition_mode="simulated", fetcher=fetcher, root_dir=root)
        return td, root, evidence, dec, resolved, inventory, provenance, acquisition

    def evaluate_materialized(self, dec, root, evidence, resolved, inventory, provenance, acquisition, environment="test"):
        return evaluate(catalog=CATALOG, declaration=dec, resolved_declaration=resolved, inventory=inventory, provenance=provenance, environment=environment, root_dir=root, evidence_dir=evidence, acquisition_decision=acquisition)

    def make_shared_national_snapshots(self, root: Path) -> dict[str, Path]:
        counts: dict[str, int] = {}
        for territory in ("aragon", "extremadura"):
            dec = declaration(territory)
            expected = SYNTHETIC_EXPECTED_SECTIONS[territory]
            divisions = dec["territory"]["territorial_codes"]
            base, remainder = divmod(expected, len(divisions))
            for index, row in enumerate(divisions):
                counts[str(row["code"]).zfill(2)] = base + (1 if index < remainder else 0)

        population = io.StringIO()
        population.write("Periodo\tSexo\tEdad\tSecciones\tTotal\n")
        features = []
        ordinal = 0
        for code, count in sorted(counts.items()):
            for index in range(count):
                sid = f"{code}{index:08d}"
                population.write(f"2025\tTotal\tTodas las edades\t{sid}\t100\n")
                features.append({"type": "Feature", "properties": {"CPRO": code, "TIPO": "SECCION", "CUSEC": sid}, "geometry": {"type": "Point", "coordinates": [-7.0 + ordinal * 0.00001, 40.0]}})
                ordinal += 1

        national = root / "national"
        national.mkdir(parents=True)
        pop_path = national / "65034.csv.zip"
        sec_path = national / "seccionado_2025.zip"
        pop_path.write_bytes(_zip_single("65034.csv", ("\ufeff" + population.getvalue()).encode("utf-8")))
        sec_path.write_bytes(_write_shapefile_zip(features, crs="EPSG:4326"))
        return {"poblacion_por_sexo_y_edad": pop_path, "secciones_censales": sec_path}

    def verified_declaration(self, territory: str, snapshots: dict[str, Path]) -> dict:
        dec = copy.deepcopy(declaration(territory))
        edition = int(dec["territory"]["edition"])
        for source_id, binding in dec["source_bindings"].items():
            path = snapshots[source_id]
            source = CATALOG["sources"][source_id]
            official_origin_url = source.get("url") or str(source["endpoint_template"]).format(edition=edition)
            binding["snapshot"] = {
                "path": str(path),
                "expected_sha256": sha256(path),
                "official_origin_url": official_origin_url,
                "edition": edition,
                "acquired_at": "2026-09-17",
            }
        dec["environment_policy"]["production"] = ["verified_snapshot"]
        dec["default_mode"]["production"] = "verified_snapshot"
        return dec

    def test_aragon_remains_declarative_regression(self):
        dec = declaration("aragon")
        self.assertEqual(dec["territory"]["id"], "aragon")
        self.assertEqual([row["code"] for row in dec["territory"]["territorial_codes"]], ["22", "44", "50"])
        self.assertEqual(dec["coverage_checks"]["required_territorial_codes"], ["22", "44", "50"])

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

    def test_population_explicit_aggregate_rows_do_not_hide_valid_sections(self):
        dec = declaration("cantabria")
        payload = (
            "Total Nacional;Provincias;Municipios;Secciones;Sexo;Edad;Periodo;Total\n"
            "Total Nacional;;;;Total;Todas las edades;2023;48619620\n"
            ";Cantabria;;;Total;Todas las edades;2023;591151\n"
            ";Cantabria;39001;;Total;Todas las edades;2023;1000\n"
            ";Cantabria;39001;3900101001;Total;Todas las edades;2023;123\n"
        ).encode("utf-8")
        filtered, checks = _filter_population(payload, dec, 2023, ["39"])
        text = filtered.decode("utf-8-sig")
        self.assertIn("3900101001", text)
        self.assertNotIn("48619620", text)
        self.assertNotIn("591151", text)
        self.assertEqual(checks["rows"], 1)
        self.assertEqual(checks["provinces"], ["39"])
        self.assertEqual(checks["pertinent_rows_examined"], 4)
        self.assertEqual(checks["aggregate_exclusions"]["total"], 3)
        self.assertEqual(
            checks["aggregate_exclusions"]["by_level"],
            {"national": 1, "provincial": 1, "municipal": 1},
        )
        self.assertEqual(
            checks["aggregate_exclusions"]["causes"],
            {
                "national": "TOTAL_NACIONAL_WITHOUT_LOWER_LEVELS",
                "provincial": "PROVINCIA_WITHOUT_MUNICIPIO_OR_SECCION",
                "municipal": "MUNICIPIO_WITHOUT_SECCION",
            },
        )
        self.assertEqual(checks["territorial_exclusions"]["count"], 0)
        self.assertEqual(
            checks["row_reconciliation"],
            {
                "pertinent": 4,
                "classified_aggregates": 3,
                "accepted_sections": 1,
                "territorial_exclusions": 0,
                "balanced": True,
            },
        )
        self.assertEqual(checks["selected_section_population_total"], 123)

    def test_population_missing_value_preserves_source_row_context(self):
        dec = {"population_validation": {}}
        payload = (
            "Periodo\tSexo\tEdad\tTotal Nacional\tProvincias\tMunicipios\tSecciones\tTotal\n"
            "2023\tTotal\tTodas las edades\tTotal Nacional\t39 Cantabria\t39059 Santander\t3905902003\t\n"
        ).encode("utf-8")
        with self.assertRaisesRegex(ValueError, "POPULATION_MISSING") as caught:
            _filter_population(payload, dec, 2023, ["39"])
        message = str(caught.exception)
        self.assertIn("POPULATION_SOURCE_ROWS_INVALID", message)
        self.assertIn("count=1", message)
        self.assertIn('"Secciones": "3905902003"', message)
        self.assertIn('"Periodo": "2023"', message)
        self.assertIn('"Sexo": "Total"', message)
        self.assertIn('"Edad": "Todas las edades"', message)
        self.assertIn('"Total": ""', message)
        self.assertIn('"Provincias": "39 Cantabria"', message)
        self.assertIn('"Municipios": "39059 Santander"', message)

    def test_population_reports_all_row_defects_in_one_pass(self):
        dec = {"population_validation": {}}
        payload = (
            "Periodo\tSexo\tEdad\tTotal Nacional\tProvincias\tMunicipios\tSecciones\tTotal\n"
            "2023\tTotal\tTodas las edades\tTotal Nacional\t39 Cantabria\t39059 Santander\t3905902003\t\n"
            "2023\tTotal\tTodas las edades\tTotal Nacional\t39 Cantabria\t39059 Santander\t3905902004\tn.d.\n"
            "2023\tTotal\tTodas las edades\tTotal Nacional\t39 Cantabria\t39059 Santander\t3905902005\t-1\n"
            "2023\tTotal\tTodas las edades\tTotal Nacional\t\t39059 Santander\t\t100\n"
            "2023\tTotal\tTodas las edades\tTotal Nacional\t39 Cantabria\t39059 Santander\t3905902006\t0\n"
        ).encode("utf-8")
        with self.assertRaisesRegex(ValueError, "POPULATION_SOURCE_ROWS_INVALID") as caught:
            _filter_population(payload, dec, 2023, ["39"])
        message = str(caught.exception)
        self.assertIn("count=4", message)
        self.assertIn("POPULATION_MISSING", message)
        self.assertIn("POPULATION_NON_NUMERIC", message)
        self.assertIn("POPULATION_NEGATIVE", message)
        self.assertIn("contradictoria: municipio sin provincia", message)
        self.assertIn('"Secciones": "3905902003"', message)
        self.assertIn('"Secciones": "3905902004"', message)
        self.assertIn('"Secciones": "3905902005"', message)
        self.assertIn('"Secciones": "3905902006"', message)

    def test_population_zero_and_grouped_integers_remain_valid(self):
        dec = {"population_validation": {}}
        payload = (
            "Periodo;Sexo;Edad;Total Nacional;Provincias;Municipios;Secciones;Total\n"
            "2023;Total;Todas las edades;Total Nacional;39 Cantabria;39059 Santander;3905902001;0\n"
            "2023;Total;Todas las edades;Total Nacional;39 Cantabria;39059 Santander;3905902002;1.234\n"
            "2023;Total;Todas las edades;Total Nacional;39 Cantabria;39059 Santander;3905902003;2 345\n"
        ).encode("utf-8")
        _, checks = _filter_population(payload, dec, 2023, ["39"])
        self.assertEqual(checks["rows"], 3)
        self.assertEqual(checks["selected_section_population_total"], 3579)

    def test_population_section_row_with_wrong_province_blocks(self):
        dec = {"population_validation": {}}
        payload = (
            "Periodo;Sexo;Edad;Total Nacional;Provincias;Municipios;Secciones;Total\n"
            "2023;Total;Todas las edades;Total Nacional;01 Araba/Álava;39059 Santander;3905902003;123\n"
        ).encode("utf-8")
        with self.assertRaisesRegex(ValueError, "SECTION_HIERARCHY_MISMATCH"):
            _filter_population(payload, dec, 2023, ["39"])

    def test_population_section_row_with_wrong_municipality_blocks(self):
        dec = {"population_validation": {}}
        payload = (
            "Periodo;Sexo;Edad;Total Nacional;Provincias;Municipios;Secciones;Total\n"
            "2023;Total;Todas las edades;Total Nacional;39 Cantabria;39001 Alfoz;3905902003;123\n"
        ).encode("utf-8")
        with self.assertRaisesRegex(ValueError, "SECTION_HIERARCHY_MISMATCH"):
            _filter_population(payload, dec, 2023, ["39"])

    def test_population_overlong_section_identifier_does_not_get_silently_truncated(self):
        dec = {"population_validation": {}}
        payload = (
            "Periodo;Sexo;Edad;Total Nacional;Provincias;Municipios;Secciones;Total\n"
            "2023;Total;Todas las edades;Total Nacional;39 Cantabria;39059 Santander;39059020030;123\n"
        ).encode("utf-8")
        with self.assertRaisesRegex(ValueError, "SECTION_ID_INVALID"):
            _filter_population(payload, dec, 2023, ["39"])

    def test_population_invalid_nonempty_section_still_blocks(self):
        dec = declaration("cantabria")
        payload = (
            "Total Nacional;Provincias;Municipios;Secciones;Sexo;Edad;Periodo;Total\n"
            ";Cantabria;39001;seccion-invalida;Total;Todas las edades;2023;123\n"
        ).encode("utf-8")
        with self.assertRaisesRegex(ValueError, "SECTION_ID_INVALID"):
            _filter_population(payload, dec, 2023, ["39"])

    def test_population_blank_section_without_explicit_aggregate_level_blocks(self):
        dec = declaration("cantabria")
        payload = (
            "Total Nacional;Provincias;Municipios;Secciones;Sexo;Edad;Periodo;Total\n"
            ";;;;Total;Todas las edades;2023;123\n"
        ).encode("utf-8")
        with self.assertRaisesRegex(ValueError, "SECTION_ID_INVALID"):
            _filter_population(payload, dec, 2023, ["39"])

    def test_population_missing_section_with_repeated_ancestors_is_municipal_aggregate(self):
        dec = declaration("cantabria")
        payload = (
            "Total Nacional;Provincias;Municipios;Secciones;Sexo;Edad;Periodo;Total\n"
            "Total Nacional;Cantabria;39001;;Total;Todas las edades;2023;123\n"
            "Total Nacional;Cantabria;39001;3900101001;Total;Todas las edades;2023;0\n"
        ).encode("utf-8")
        _, checks = _filter_population(payload, dec, 2023, ["39"])
        self.assertEqual(checks["aggregate_exclusions"]["by_level"]["municipal"], 1)
        self.assertEqual(checks["selected_section_population_total"], 0)
        self.assertTrue(checks["row_reconciliation"]["balanced"])

    def test_population_reconciles_out_of_scope_sections_without_counting_them_in_population(self):
        dec = declaration("cantabria")
        payload = (
            "Total Nacional;Provincias;Municipios;Secciones;Sexo;Edad;Periodo;Total\n"
            ";Cantabria;39001;3900101001;Total;Todas las edades;2023;0\n"
            ";Asturias;33001;3300101001;Total;Todas las edades;2023;999\n"
        ).encode("utf-8")
        filtered, checks = _filter_population(payload, dec, 2023, ["39"])
        text = filtered.decode("utf-8-sig")
        self.assertIn("3900101001", text)
        self.assertNotIn("3300101001", text)
        self.assertEqual(checks["pertinent_rows_examined"], 2)
        self.assertEqual(checks["rows"], 1)
        self.assertEqual(checks["territorial_exclusions"]["count"], 1)
        self.assertEqual(checks["selected_section_population_total"], 0)
        self.assertTrue(checks["row_reconciliation"]["balanced"])

    def test_population_repeated_ancestors_classify_by_most_specific_level(self):
        dec = declaration("cantabria")
        payload = (
            "Total Nacional;Provincias;Municipios;Secciones;Sexo;Edad;Periodo;Total\n"
            "Total Nacional;01 Araba/Álava;;;Total;Todas las edades;2023;333746\n"
            "Total Nacional;01 Araba/Álava;01001;;Total;Todas las edades;2023;25000\n"
            "Total Nacional;Cantabria;39001;3900101001;Total;Todas las edades;2023;0\n"
        ).encode("utf-8")
        filtered, checks = _filter_population(payload, dec, 2023, ["39"])
        text = filtered.decode("utf-8-sig")
        self.assertIn("3900101001", text)
        self.assertNotIn("333746", text)
        self.assertNotIn("25000", text)
        self.assertEqual(checks["aggregate_exclusions"]["by_level"], {
            "national": 0, "provincial": 1, "municipal": 1,
        })
        self.assertEqual(checks["pertinent_rows_examined"], 3)
        self.assertEqual(checks["territorial_exclusions"]["count"], 0)
        self.assertEqual(checks["rows"], 1)
        self.assertEqual(checks["selected_section_population_total"], 0)
        self.assertEqual(checks["row_reconciliation"], {
            "pertinent": 3,
            "classified_aggregates": 2,
            "accepted_sections": 1,
            "territorial_exclusions": 0,
            "balanced": True,
        })

    def test_population_repeated_ancestor_row_from_other_territory_is_aggregate_not_section_exclusion(self):
        dec = declaration("cantabria")
        payload = (
            "Total Nacional;Provincias;Municipios;Secciones;Sexo;Edad;Periodo;Total\n"
            "Total Nacional;01 Araba/Álava;;;Total;Todas las edades;2023;333746\n"
            "Total Nacional;Cantabria;39001;3900101001;Total;Todas las edades;2023;123\n"
        ).encode("utf-8")
        _, checks = _filter_population(payload, dec, 2023, ["39"])
        self.assertEqual(checks["aggregate_exclusions"]["by_level"]["provincial"], 1)
        self.assertEqual(checks["territorial_exclusions"]["count"], 0)
        self.assertTrue(checks["row_reconciliation"]["balanced"])

    def test_population_true_hierarchy_contradiction_still_blocks(self):
        dec = declaration("cantabria")
        payload = (
            "Total Nacional;Provincias;Municipios;Secciones;Sexo;Edad;Periodo;Total\n"
            "Total Nacional;;01001;;Total;Todas las edades;2023;123\n"
        ).encode("utf-8")
        with self.assertRaisesRegex(ValueError, "contradictoria: municipio sin provincia"):
            _filter_population(payload, dec, 2023, ["39"])

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
        decision = self.evaluate_materialized(dec, root, evidence, resolved, inventory, provenance, acquisition)
        self.assertEqual(decision["decision"], "BLOCKED")
        self.assertTrue(any("territory_id" in reason for reason in decision["reasons"]))

    def test_exact_source_fields_must_match(self):
        td, root, evidence, dec, resolved, inventory, provenance, acquisition = self.materialize("extremadura")
        self.addCleanup(td.cleanup)
        for field, replacement in (("path", "otra/ruta.zip"), ("sha256", "0" * 64), ("bytes", 7), ("urls", ["https://example.invalid"]), ("edition", 2024), ("source_id", "otra_fuente")):
            mutated = copy.deepcopy(inventory)
            mutated["sources"][0][field] = replacement
            decision = self.evaluate_materialized(dec, root, evidence, resolved, mutated, provenance, acquisition)
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
                "source_bindings": {"poblacion_por_sexo_y_edad": {"materialized_path": "inputs/out.zip", "archive_member": "65034.csv", "snapshot": {"path": str(snapshot), "expected_sha256": "0" * 64, "official_origin_url": CATALOG["sources"]["poblacion_por_sexo_y_edad"]["url"], "edition": 2025, "acquired_at": "2026-09-17"}}},
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
            snapshots = self.make_shared_national_snapshots(root)
            dec = self.verified_declaration("extremadura", snapshots)
            dec["required_sources"] = ["poblacion_por_sexo_y_edad"]
            binding = dec["source_bindings"]["poblacion_por_sexo_y_edad"]
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

    def test_national_snapshot_hashes_do_not_change(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            snapshots = self.make_shared_national_snapshots(root)
            before = {sid: sha256(path) for sid, path in snapshots.items()}
            dec = self.verified_declaration("extremadura", snapshots)
            evidence = root / "extremadura-evidence"
            resolved, inventory, provenance, acquisition = acquire(catalog=CATALOG, declaration=dec, evidence_dir=evidence, environment="production", acquisition_mode="verified_snapshot", root_dir=root)
            decision = self.evaluate_materialized(dec, root, evidence, resolved, inventory, provenance, acquisition, environment="production")
            self.assertEqual(acquisition["decision"], "READY")
            self.assertEqual(decision["decision"], "READY")
            self.assertEqual(before, {sid: sha256(path) for sid, path in snapshots.items()})
            self.assertTrue(decision["checks"]["official_copies_immutable"])

    def test_aragon_and_extremadura_can_share_same_national_snapshots_consecutively(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            snapshots = self.make_shared_national_snapshots(root)
            baseline = {sid: sha256(path) for sid, path in snapshots.items()}
            results = {}
            for territory in ("aragon", "extremadura"):
                dec = self.verified_declaration(territory, snapshots)
                evidence = root / f"{territory}-evidence"
                resolved, inventory, provenance, acquisition = acquire(catalog=CATALOG, declaration=dec, evidence_dir=evidence, environment="production", acquisition_mode="verified_snapshot", root_dir=root)
                decision = self.evaluate_materialized(dec, root, evidence, resolved, inventory, provenance, acquisition, environment="production")
                results[territory] = decision["decision"]
                self.assertEqual(baseline, {sid: sha256(path) for sid, path in snapshots.items()})
                for binding in dec["source_bindings"].values():
                    self.assertTrue((evidence / "materialized" / binding["materialized_path"]).is_file())
            self.assertEqual(results, {"aragon": "READY", "extremadura": "READY"})

    def test_origin_equal_destination_is_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            evidence = root / "evidence"
            destination = evidence / "materialized" / "inputs" / "65034.csv.zip"
            destination.parent.mkdir(parents=True)
            payload = _zip_single("65034.csv", b"\xef\xbb\xbfPeriodo\tSexo\tEdad\tSecciones\tTotal\n2025\tTotal\tTodas las edades\t0600000001\t1\n")
            destination.write_bytes(payload)
            dec = {
                "territory": {"id": "x", "business_name": "X", "edition": 2025, "territorial_codes": [{"code": "06", "business_name": "Badajoz"}]},
                "required_sources": ["poblacion_por_sexo_y_edad"],
                "source_bindings": {"poblacion_por_sexo_y_edad": {"materialized_path": "inputs/65034.csv.zip", "archive_member": "65034.csv", "snapshot": {"path": str(destination), "expected_sha256": sha256(destination), "official_origin_url": CATALOG["sources"]["poblacion_por_sexo_y_edad"]["url"], "edition": 2025, "acquired_at": "2026-09-17"}}},
                "population_validation": {"required_columns": ["Periodo", "Sexo", "Edad", "Secciones", "Total"]},
                "environment_policy": {"production": ["verified_snapshot"]},
                "default_mode": {"production": "verified_snapshot"},
            }
            _, _, _, acquisition = acquire(catalog=CATALOG, declaration=dec, evidence_dir=evidence, environment="production", acquisition_mode="verified_snapshot", root_dir=root)
            self.assertEqual(acquisition["decision"], "BLOCKED")
            self.assertIn("mismo fichero", json.dumps(acquisition, ensure_ascii=False).lower())

    def test_extremadura_simulation_ready_and_inputs_are_consumable_by_m01(self):
        td, root, evidence, dec, resolved, inventory, provenance, acquisition = self.materialize("extremadura")
        self.addCleanup(td.cleanup)
        decision = self.evaluate_materialized(dec, root, evidence, resolved, inventory, provenance, acquisition)
        self.assertEqual(acquisition["decision"], "READY")
        self.assertEqual(decision["decision"], "READY")
        self.assertEqual(decision["territory_id"], "extremadura")
        self.assertEqual(inventory["territorial_coverage"], ["06", "10"])
        for name in ("inventario_fuentes.json", "manifiesto_procedencia.json", "decision_adquisicion.json", "declaracion_materializacion.json"):
            self.assertTrue((evidence / name).is_file(), name)
        (evidence / "decision_preparacion.json").write_text(json.dumps(decision, ensure_ascii=False, indent=2), encoding="utf-8")
        (evidence / "informe_preparacion.md").write_text(readable_report(decision), encoding="utf-8")

        spec = importlib.util.spec_from_file_location("ddd_m01_test", ROOT / "modulos/01_preparar_base_territorial.py")
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)
        section_path = evidence / "materialized" / dec["source_bindings"]["secciones_censales"]["materialized_path"]
        population_path = evidence / "materialized" / dec["source_bindings"]["poblacion_por_sexo_y_edad"]["materialized_path"]
        gdf = module.load_seccionado(str(section_path), "", ["06", "10"])
        cip = module.load_cip([str(population_path)], "Secciones", "Total", 2025, "auto", {"year_col": "Periodo", "sexo_col": "Sexo", "edad_col": "Edad", "sexo_total_values": ["Total"], "edad_total_values": ["Todas las edades"], "year_value": 2025}, ["06", "10"])
        self.assertEqual(len(gdf), 964)
        self.assertEqual(len(cip), 964)
        self.assertFalse((root / "inputs" / "65034.csv.zip").exists())
        self.assertFalse((root / "inputs" / "seccionado_2025.zip").exists())


if __name__ == "__main__":
    unittest.main()
