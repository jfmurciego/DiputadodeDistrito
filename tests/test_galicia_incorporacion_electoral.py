from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

import pandas as pd
import yaml

from ddd_core.electoral_contract import PartyDictionary

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "territorios/galicia/config/galicia_2025.yaml"
CONTRACT = ROOT / "territorios/galicia/config/elecciones/galicia_parlamento_2024.json"


def load_m07():
    spec = importlib.util.spec_from_file_location("ddd_m07_galicia", ROOT / "modulos/07_agregar_resultados_electorales.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class GaliciaElectoralApplication(unittest.TestCase):
    def test_contract_and_config_close_m07_m08(self):
        cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
        m07 = cfg["modulos"]["modulo_07_agregar_resultados_electorales"]
        m08 = cfg["modulos"]["modulo_08_integrar_resultados"]
        self.assertEqual(m07["election_contract"], str(CONTRACT.relative_to(ROOT)))
        self.assertEqual(m07["section_id_field"], "CUSEC_KEY")
        self.assertIn("out_district_summary_csv", m07)
        self.assertIn("out_districts_with_results_geojson", m08)

        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        self.assertEqual(contract["territory_id"], "galicia")
        self.assertEqual(contract["sources"][0]["sha256"], "7f9db16181962a1ef543fe0768c6822d19166e91b97e0a9d48b7c449c24aba96")
        adapter = contract["sources"][0]["adapter"]
        self.assertEqual(adapter["kind"], "wide_polling_station_csv")
        classification = adapter["record_classification"]
        self.assertEqual(
            classification["polling_station"]["mode"],
            "locator_contract",
        )
        self.assertTrue(
            classification["require_aggregate_for_each_block"]
        )
        self.assertEqual(
            classification["aggregates"][0]["id"],
            "provincial_total",
        )
        self.assertEqual(
            classification["aggregates"][0]["match"]["equals"],
            "Total",
        )
        self.assertEqual(
            classification["aggregates"][0]["vote_reconciliation"],
            {
                "kind": "party_columns_exact_sum",
                "empty_aggregate_value": "reject",
            },
        )
        applicability = adapter["party_applicability"]
        self.assertEqual(set(applicability), {"DO"})
        self.assertEqual(applicability["DO"]["field"], "Cód Cir")
        self.assertEqual(applicability["DO"]["equals"], ["32"])
        self.assertTrue(str(applicability["DO"]["reason"]).strip())
        provenance = adapter["structural_provenance"]
        self.assertEqual(
            provenance["path"],
            "territorios/galicia/config/elecciones/galicia_parlamento_2024.structural_provenance.json",
        )
        self.assertEqual(
            provenance["sha256"],
            "9839cd45ed28404d31010bcb4ff0a79cb40efc640540dfdee6f13ceedf53ca68",
        )
        exceptions = contract["reconciliation"]["allowed_result_only_sections"]
        self.assertEqual(len(exceptions), 48)
        self.assertEqual(sum(int(x["expected_votes"]) for x in exceptions), 25086)

        dictionary = ROOT / contract["party_dictionary"]["path"]
        self.assertEqual(hashlib.sha256(dictionary.read_bytes()).hexdigest(), contract["party_dictionary"]["sha256"])
        PartyDictionary(json.loads(dictionary.read_text(encoding="utf-8")))

    def test_structural_provenance_is_hash_bound_to_galicia_contract(self):
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        source = contract["sources"][0]
        declaration = source["adapter"]["structural_provenance"]
        sidecar = ROOT / declaration["path"]
        self.assertTrue(sidecar.is_file())
        self.assertEqual(
            hashlib.sha256(sidecar.read_bytes()).hexdigest(),
            declaration["sha256"],
        )
        document = json.loads(sidecar.read_text(encoding="utf-8"))
        self.assertEqual(
            document["merged_source"]["sha256"],
            source["sha256"],
        )
        self.assertEqual(document["merged_source"]["records"], 3996)
        self.assertEqual(
            sum(int(row["records"]) for row in document["sources"]),
            3996,
        )
        self.assertEqual(
            [row["source_id"] for row in document["sources"]],
            [
                "a_coruna_mesas",
                "lugo_mesas",
                "ourense_mesas",
                "pontevedra_mesas",
            ],
        )
        self.assertEqual(
            [
                row["source_id"]
                for row in document["sources"]
                if "DO" in row["original_columns"]
            ],
            ["ourense_mesas"],
        )
        self.assertEqual(
            source["adapter"]["party_applicability"]["DO"]["equals"],
            ["32"],
        )

    def test_electoral_schema_requires_sidecar_for_party_applicability(self):
        schema_path = ROOT / "configuracion/esquemas/contrato_electoral.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        adapter = schema["properties"]["sources"]["items"][
            "properties"
        ]["adapter"]
        self.assertEqual(
            adapter["properties"]["structural_provenance"][
                "required"
            ],
            ["path", "sha256"],
        )
        applicability_rule = next(
            rule
            for rule in adapter["allOf"]
            if (
                "party_applicability"
                in rule.get("if", {}).get("required", [])
            )
        )
        self.assertIn(
            "structural_provenance",
            applicability_rule["then"]["required"],
        )
        self.assertEqual(
            applicability_rule["then"]["properties"]["kind"]["const"],
            "wide_polling_station_csv",
        )

    def test_wide_polling_station_adapter_builds_cusec_and_aggregates_tables(self):
        m07 = load_m07()
        parties = PartyDictionary({
            "schema_family": "ddd-party-dictionary",
            "schema_version": "1.0.0",
            "unknown_party_policy": "reject",
            "parties": [
                {"canonical_id": "BNG", "display_name": "BNG"},
                {"canonical_id": "PP", "display_name": "PP"},
            ],
        })
        adapter = {
            "kind": "wide_polling_station_csv",
            "separator": ";",
            "province_field": "Cód Cir",
            "municipality_field": "Cód Con",
            "polling_station_field": "Mesa",
            "polling_station_regex": r"^(?P<district>\d{2})-(?P<section>\d{3})-[A-Z0-9]+$",
            "party_columns": ["BNG", "PP"],
        }
        with tempfile.TemporaryDirectory() as raw:
            source = Path(raw) / "mesas.csv"
            source.write_text(
                "Cód Cir;Cód Con;Mesa;BNG;PP\n"
                "15;007;01-001-A;10;20\n"
                "15;007;01-001-B;5;7\n",
                encoding="utf-8",
            )
            frame, sections = m07.read_results(source, adapter, "CUSEC_KEY", parties)
        self.assertEqual(sections, {"1500701001"})
        grouped = frame.groupby(["CUSEC_KEY", "party"], as_index=False)["votes"].sum()
        observed = {(r.CUSEC_KEY, r.party): int(r.votes) for r in grouped.itertuples()}
        self.assertEqual(observed[("1500701001", "BNG")], 15)
        self.assertEqual(observed[("1500701001", "PP")], 27)

    def test_wide_polling_station_adapter_rejects_total_row_without_locator(self):
        m07 = load_m07()
        parties = PartyDictionary({
            "schema_family": "ddd-party-dictionary",
            "schema_version": "1.0.0",
            "unknown_party_policy": "reject",
            "parties": [
                {"canonical_id": "BNG", "display_name": "BNG"},
                {"canonical_id": "PP", "display_name": "PP"},
            ],
        })
        adapter = {
            "kind": "wide_polling_station_csv",
            "separator": ";",
            "province_field": "Cód Cir",
            "municipality_field": "Cód Con",
            "polling_station_field": "Mesa",
            "polling_station_regex": r"^(?P<district>\d{2})-(?P<section>\d{3})-[A-Z0-9]+$",
            "party_columns": ["BNG", "PP"],
        }
        with tempfile.TemporaryDirectory() as raw:
            source = Path(raw) / "mesas.csv"
            source.write_text(
                "Cód Cir;Cód Con;Mesa;BNG;PP\n"
                "15;007;01-001-A;10;20\n"
                "15;007;01-001-B;5;7\n"
                "Total;;;15;27\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                ValueError,
                r"ELECTORAL_INPUT_INVALID.*row=csv\[4\].*field=Mesa.*cause=POLLING_STATION_LOCATOR_INVALID",
            ):
                m07.read_results(source, adapter, "CUSEC_KEY", parties)

    def test_contract_reconciliation_has_no_map_only_shortcut(self):
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        reconciliation = contract["reconciliation"]
        self.assertEqual(reconciliation["policy"], "fail_unless_declared")
        self.assertEqual(reconciliation["allowed_map_only_sections"], [])
        self.assertTrue(all(str(x.get("reason", "")).strip() for x in reconciliation["allowed_result_only_sections"]))


if __name__ == "__main__":
    unittest.main()
