#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: pruebas de fuentes oficiales y preparación territorial
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Simulación INE multi-territorio
FECHA: 2026-09-17
ESTADO: candidato
FUNCIÓN: probar adquisición, cobertura, procedencia y preparación sin acceder a servicios externos.
CAMBIOS: añade regresión declarativa de Aragón y alta declarativa de Extremadura.
MOTIVO: validar la industrialización de fuentes sin ejecutar ningún territorio ni conjunto de alternativas.
ANTERIOR: tests/test_estado_produccion_poblacion.py
"""
from __future__ import annotations

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
    def __init__(self, declaration_data: dict):
        self.declaration = declaration_data
        expected = int(declaration_data["coverage_checks"]["expected_sections"])
        divisions = declaration_data["territory"]["territorial_codes"]
        base, remainder = divmod(expected, len(divisions))
        self.counts = {
            str(row["code"]): base + (1 if index < remainder else 0)
            for index, row in enumerate(divisions)
        }

    def __call__(self, url: str) -> bytes:
        if "65034.csv" in url:
            return b"Periodo;Sexo;Edad;Secciones;Total\n2025;Total;Todas las edades;0000000000;1\n"
        query = parse_qs(urlparse(url).query)
        filter_text = query["filter"][0]
        code = next(code for code in self.counts if f"CPRO='{code}'" in filter_text)
        features = []
        for index in range(self.counts[code]):
            section = f"{code}{index:08d}"
            features.append({"type": "Feature", "properties": {"CPRO": code, "TIPO": "SECCION", "CUSEC": section}, "geometry": None})
        return json.dumps({"type": "FeatureCollection", "features": features}).encode("utf-8")


class OfficialSourcesTests(unittest.TestCase):
    def materialize(self, territory: str):
        dec = declaration(territory)
        td = tempfile.TemporaryDirectory()
        out = Path(td.name)
        inventory, provenance = acquire(
            catalog=CATALOG,
            declaration=dec,
            out_dir=out,
            environment="test",
            acquisition_mode="simulated",
            fetcher=SimulatedINE(dec),
        )
        return td, dec, out, inventory, provenance

    def test_aragon_regression_is_declarative(self):
        dec = declaration("aragon")
        self.assertEqual([row["code"] for row in dec["territory"]["territorial_codes"]], ["22", "44", "50"])
        self.assertEqual(dec["coverage_checks"]["expected_sections"], 1463)
        td, dec, out, inventory, provenance = self.materialize("aragon")
        self.addCleanup(td.cleanup)
        self.assertEqual(inventory["territory"], "Aragón")
        self.assertEqual(next(row for row in inventory["sources"] if row["business_name"].startswith("Secciones censales"))["sections"], 1463)
        decision = evaluate(catalog=CATALOG, declaration=dec, inventory=inventory, provenance=provenance, environment="test")
        self.assertEqual(decision["decision"], "READY")

    def test_extremadura_uses_only_declarative_codes(self):
        dec = declaration("extremadura")
        self.assertEqual([(row["code"], row["business_name"]) for row in dec["territory"]["territorial_codes"]], [("06", "Badajoz"), ("10", "Cáceres")])
        td, dec, out, inventory, provenance = self.materialize("extremadura")
        self.addCleanup(td.cleanup)
        self.assertEqual(inventory["territory"], "Extremadura")
        self.assertEqual(next(row for row in inventory["sources"] if row["business_name"].startswith("Secciones censales"))["sections"], 964)
        self.assertEqual(inventory["territorial_coverage"], ["Badajoz", "Cáceres"])

    def test_outputs_include_inventory_provenance_decision_and_report(self):
        td, dec, out, inventory, provenance = self.materialize("extremadura")
        self.addCleanup(td.cleanup)
        decision = evaluate(catalog=CATALOG, declaration=dec, inventory=inventory, provenance=provenance, environment="test")
        (out / "decision_preparacion.json").write_text(json.dumps(decision, ensure_ascii=False, indent=2), encoding="utf-8")
        (out / "informe_preparacion.md").write_text(readable_report(decision), encoding="utf-8")
        for name in ("inventario_fuentes.json", "manifiesto_procedencia.json", "decision_preparacion.json", "informe_preparacion.md"):
            self.assertTrue((out / name).is_file(), name)
        visible = (out / "informe_preparacion.md").read_text(encoding="utf-8")
        self.assertIn("Extremadura", visible)
        self.assertNotIn("territory_id", visible)
        self.assertNotIn("CPRO", visible)

    def test_missing_evidence_blocks_cleanly(self):
        dec = declaration("extremadura")
        decision = evaluate(catalog=CATALOG, declaration=dec, inventory=None, provenance=None, environment="production")
        self.assertEqual(decision["decision"], "BLOCKED")
        self.assertIn("Falta evidencia materializada de fuentes oficiales", decision["reasons"])

    def test_wrong_environment_policy_blocks(self):
        td, dec, out, inventory, provenance = self.materialize("aragon")
        self.addCleanup(td.cleanup)
        inventory = dict(inventory)
        inventory["acquisition_mode"] = "simulated"
        decision = evaluate(catalog=CATALOG, declaration=dec, inventory=inventory, provenance=provenance, environment="production")
        self.assertEqual(decision["decision"], "BLOCKED")
        self.assertIn("La procedencia materializada no está permitida en este entorno", decision["reasons"])

    def test_acquisition_tool_contains_no_aragon_specific_constants(self):
        text = (ROOT / "herramientas/adquirir_fuentes_oficiales.py").read_text(encoding="utf-8")
        for literal in ("('22','44','50')", '("22", "44", "50")', "1463", "seccionado_2025_aragon"):
            self.assertNotIn(literal, text)


if __name__ == "__main__":
    unittest.main()
