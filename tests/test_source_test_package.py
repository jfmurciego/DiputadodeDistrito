from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from herramientas.probar_fuentes_oficiales import (
    _with_limit,
    full_test,
    probe_ogc,
    probe_static_csv,
)
from herramientas.adquirir_fuentes_oficiales import _collect_live_sections, _source_urls
from herramientas.resolver_fuentes_territorio import build_declaration, matrix, territories

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/prueba-fuentes-oficiales.yml"


class FakeResponse:
    def __init__(self, payload: bytes, status: int = 200):
        self._bio = io.BytesIO(payload)
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def readline(self):
        return self._bio.readline()

    def read(self):
        return self._bio.read()


class SourceTestPackageTests(unittest.TestCase):
    def test_registry_covers_all_spanish_territories(self):
        rows = territories()
        self.assertEqual(len(rows), 19)
        self.assertEqual(matrix("Todos"), [r["name"] for r in rows])
        self.assertIn("La Rioja", matrix("Todos"))
        self.assertIn("Ceuta", matrix("Todos"))
        self.assertIn("Melilla", matrix("Todos"))

    def test_declaration_is_generated_without_prepared_snapshot(self):
        d = build_declaration("La Rioja", 2025)
        self.assertEqual(d["territory"]["id"], "la_rioja")
        self.assertEqual([x["code"] for x in d["territory"]["territorial_codes"]], ["26"])
        self.assertEqual(d["required_sources"], ["poblacion_por_sexo_y_edad", "secciones_censales"])
        self.assertNotIn("snapshot", d["source_bindings"]["poblacion_por_sexo_y_edad"])
        self.assertNotIn("snapshot", d["source_bindings"]["secciones_censales"])
        self.assertEqual(d["default_mode"]["production"], "official_live")

    def test_population_probe_reads_only_header_and_sample(self):
        source = {
            "id": "poblacion_por_sexo_y_edad",
            "kind": "static_csv",
            "url": "https://example.test/pop.csv",
        }
        payload = b"Periodo;Sexo;Edad;Secciones;Total\n" + b"2025;Total;Todas;2600101001;1\n" * 50
        with patch("herramientas.probar_fuentes_oficiales._request", return_value=FakeResponse(payload)):
            result = probe_static_csv(source, timeout=10, sample_size=10)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["sample_records"], 10)
        self.assertLess(result["sample_bytes"], len(payload))

    def test_ogc_remote_filter_is_only_province_and_sections_are_filtered_locally(self):
        d = build_declaration("La Rioja", 2025)
        source = yaml.safe_load((ROOT / "fuentes/catalogo_oficial.yaml").read_text(encoding="utf-8"))["sources"]["secciones_censales"]
        urls = _source_urls(source, 2025, d["territory"]["territorial_codes"])
        self.assertEqual(len(urls), 1)
        self.assertIn("CPRO%3D%2726%27", urls[0])
        self.assertNotIn("TIPO", urls[0])

        payload = json.dumps({"features": [
            {"properties": {"CPRO": "26", "CUSEC": "2600101000", "CSEC": "000", "TIPO": "DISTRITO"}},
            {"properties": {"CPRO": "26", "CUSEC": "2600101001", "CSEC": "001", "TIPO": "SECCIÓN"}},
            {"properties": {"CPRO": "26", "CUSEC": "2600101002", "CSEC": "002"}},
        ]}).encode()
        features, _, checks = _collect_live_sections(
            source, 2025, d["territory"]["territorial_codes"], lambda _url: payload
        )
        self.assertEqual([f["properties"]["CUSEC"] for f in features], ["2600101001", "2600101002"])
        self.assertEqual(checks["sections"], 2)

    def test_ogc_probe_limits_each_province(self):
        d = build_declaration("Canarias", 2025)
        source = yaml.safe_load((ROOT / "fuentes/catalogo_oficial.yaml").read_text(encoding="utf-8"))["sources"]["secciones_censales"]
        payload35 = json.dumps({"features": [{"properties": {"CPRO": "35", "CUSEC": "3500101001"}}]}).encode()
        payload38 = json.dumps({"features": [{"properties": {"CPRO": "38", "CUSEC": "3800101001"}}]}).encode()
        responses = [FakeResponse(payload35), FakeResponse(payload38)]
        with patch("herramientas.probar_fuentes_oficiales._request", side_effect=responses):
            result = probe_ogc(source, d, timeout=10, sample_size=10)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["sample_records"], 2)
        self.assertTrue(all("limit=10" in x["url"] for x in result["provinces"]))

    def test_limit_replaces_existing_ogc_limit(self):
        url = _with_limit("https://example.test/items?f=json&limit=10000", 10)
        self.assertIn("limit=10", url)
        self.assertNotIn("limit=10000", url)

    def test_full_mode_requires_acquire_then_reuse_then_block(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            declaration = build_declaration("La Rioja", 2025)
            declaration_path = root / "fuentes.yaml"
            declaration_path.write_text(yaml.safe_dump(declaration, allow_unicode=True), encoding="utf-8")
            out = root / "out"

            calls = {"n": 0}

            def fake_run(args, expect_success=True):
                calls["n"] += 1
                if calls["n"] == 1:
                    cp = out / "checkpoint-acquire"
                    (cp / "sources").mkdir(parents=True)
                    bundle = cp / "sources/prepared_sources.zip"
                    bundle.write_bytes(b"package")
                    digest = __import__("hashlib").sha256(bundle.read_bytes()).hexdigest()
                    (cp / "source_execution.json").write_text(json.dumps({
                        "decision": "ACQUIRE", "sha256": digest, "bytes": 7, "records": 343
                    }), encoding="utf-8")
                    return type("R", (), {"returncode": 0, "stdout": "ACQUIRE", "stderr": ""})()
                if calls["n"] == 2:
                    cp = out / "checkpoint-reuse"
                    cp.mkdir(parents=True)
                    first = json.loads((out / "checkpoint-acquire/source_execution.json").read_text())
                    (cp / "source_execution.json").write_text(json.dumps({
                        **first, "decision": "REUSE"
                    }), encoding="utf-8")
                    return type("R", (), {"returncode": 0, "stdout": "REUSE", "stderr": ""})()
                return type("R", (), {"returncode": 1, "stdout": "", "stderr": "BLOCK checksum incorrecto"})()

            with patch("herramientas.probar_fuentes_oficiales.unit_test", return_value={"decision": "PASS"}), \
                 patch("herramientas.probar_fuentes_oficiales.run_cmd", side_effect=fake_run):
                result = full_test(declaration_path, out, timeout=10)
            self.assertEqual(result["acquire"]["decision"], "ACQUIRE")
            self.assertEqual(result["reuse"]["decision"], "REUSE")
            self.assertEqual(result["corruption"]["decision"], "BLOCK")

    def test_workflow_exposes_only_functional_test_controls(self):
        d = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
        trigger = d.get("on") or d.get(True)
        inputs = trigger["workflow_dispatch"]["inputs"]
        self.assertEqual(set(inputs), {"territory", "data_edition", "mode"})
        self.assertEqual(inputs["mode"]["options"], ["Unit test", "Todo"])
        self.assertEqual(inputs["territory"]["options"][0], "Todos")
        self.assertIn("17 · La Rioja", inputs["territory"]["options"])
        self.assertIn("19 · Melilla", inputs["territory"]["options"])
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("max-parallel: 4", text)
        self.assertIn("--timeout-seconds 10", text)
        self.assertIn("budget=10m", text)
        self.assertIn("budget=120m", text)


if __name__ == "__main__":
    unittest.main()
