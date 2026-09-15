"""
PRUEBAS: Contrato electoral común R039
VERSIÓN: 1.0.2
NOMBRE DE VERSIÓN: Verificación coherente y normalización de district_id
FECHA: 2026-09-15
ESTADO: vigente — R039
CAMBIOS: añade regresión para IDs de distrito leídos por pandas como float entero (1.0) frente a IDs geométricos textuales ("1").
MOTIVO: impedir que una representación de tipo convierta una cobertura electoral completa en un falso faltante 67/67.
ANTERIOR: legacy/tests/test_r039_electoral_contract_v1.0.1.py
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

import pandas as pd
import yaml

from ddd_core.electoral_contract import PartyDictionary, load_election_contract


ROOT = Path(__file__).resolve().parents[1]


def load_module(relative_path: str, name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


M07 = load_module("modulos/07_agregar_resultados_electorales.py", "ddd_m07_r039")
M08 = load_module("modulos/08_integrar_resultados.py", "ddd_m08_r039")


class R039ElectoralContract(unittest.TestCase):
    def test_contrato_aragon_verifica_hash_y_todas_las_siglas(self):
        config_path = ROOT / "territorios/aragon/config/aragon_2025.yaml"
        config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        m07 = config["modulos"]["modulo_07_agregar_resultados_electorales"]
        self.assertEqual(
            set(m07),
            {
                "in_geojson", "section_id_field", "district_field",
                "election_contract", "out_district_party_csv",
                "out_district_summary_csv", "out_reconciliation_report",
                "out_sections_enriched_geojson",
            },
        )
        contract_path = ROOT / m07["election_contract"]
        declared = json.loads(contract_path.read_text(encoding="utf-8"))
        source_record = declared["sources"][0]
        source_path = ROOT / source_record["path"]
        if source_path.is_file():
            contract, parties = load_election_contract(
                contract_path,
                project_root=ROOT,
                expected_territory_id="aragon",
            )
            frames = [
                M07.read_results(source["resolved_path"], source["adapter"], "CUSEC_KEY", parties)
                for source in contract["sources"]
            ]
            observed = set(pd.concat([item[0] for item in frames])["party"])
            self.assertEqual(len(observed), 15)
            self.assertIn("IU_MOVIMIENTO_SUMAR", observed)
        else:
            manifest = (ROOT / "territorios/aragon/inputs/MANIFEST.sha256").read_text(encoding="utf-8")
            self.assertIn(
                f"{source_record['sha256']}  {source_record['path']}",
                manifest,
            )
            dictionary_record = declared["party_dictionary"]
            dictionary_path = ROOT / dictionary_record["path"]
            self.assertEqual(
                hashlib.sha256(dictionary_path.read_bytes()).hexdigest(),
                dictionary_record["sha256"],
            )
            dictionary_data = json.loads(dictionary_path.read_text(encoding="utf-8"))
            PartyDictionary(dictionary_data)
            canonical_ids = {item["canonical_id"] for item in dictionary_data["parties"]}
            self.assertEqual(len(canonical_ids), 15)
            self.assertIn("IU_MOVIMIENTO_SUMAR", canonical_ids)

    def test_checksum_alterado_bloquea_antes_de_leer_votos(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "votes.csv"
            source.write_text("section,party,votes\n1,P,10\n", encoding="utf-8")
            dictionary = root / "parties.json"
            dictionary.write_text(json.dumps({
                "schema_family": "ddd-party-dictionary",
                "schema_version": "1.0.0",
                "unknown_party_policy": "reject",
                "parties": [{"canonical_id": "P", "display_name": "P"}],
            }), encoding="utf-8")
            digest = hashlib.sha256(dictionary.read_bytes()).hexdigest()
            contract = root / "election.json"
            contract.write_text(json.dumps({
                "schema_family": "ddd-election",
                "schema_version": "1.0.0",
                "election_id": "synthetic-1",
                "territory_id": "synthetic",
                "title": "Elección sintética",
                "election_date": "2026-01-01",
                "input_mode": "verifiable_file",
                "boundary_independence": True,
                "sources": [{
                    "path": "votes.csv", "sha256": "0" * 64,
                    "publisher": "fixture", "source_url": "https://example.invalid",
                    "retrieved_at": "2026-01-01",
                    "adapter": {"kind": "long_csv", "section_field": "section", "party_field": "party", "votes_field": "votes"},
                }],
                "party_dictionary": {"path": "parties.json", "sha256": digest},
                "reconciliation": {"policy": "fail_unless_declared"},
            }), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "checksum incorrecto"):
                load_election_contract(contract, project_root=root)

    def test_alias_ambiguo_y_partido_desconocido_se_rechazan(self):
        with self.assertRaisesRegex(ValueError, "alias ambiguo"):
            PartyDictionary({
                "schema_family": "ddd-party-dictionary",
                "schema_version": "1.0.0",
                "unknown_party_policy": "reject",
                "parties": [
                    {"canonical_id": "A", "display_name": "Partido"},
                    {"canonical_id": "B", "display_name": " partido  "},
                ],
            })
        dictionary = PartyDictionary({
            "schema_family": "ddd-party-dictionary",
            "schema_version": "1.0.0",
            "unknown_party_policy": "reject",
            "parties": [{"canonical_id": "A", "display_name": "Árbol", "aliases": [" A "]}],
        })
        self.assertEqual(dictionary.canonicalize("  a "), "A")
        with self.assertRaisesRegex(ValueError, "no declarado"):
            dictionary.canonicalize("B")

    def test_m08_exige_cobertura_exacta_y_sin_duplicados(self):
        geometry = pd.DataFrame({"district_id": ["1", "2"], "population": [10, 20]})
        complete = pd.DataFrame({"district_id": [1.0, 2.0], "total_votes": [7, 15]})
        merged = M08.integrate_results(geometry, complete)
        self.assertEqual(list(merged["district_id"]), ["1", "2"])
        self.assertEqual(list(merged["total_votes"]), [7, 15])
        with self.assertRaisesRegex(ValueError, "sin_resultados"):
            M08.integrate_results(geometry, complete.iloc[:1])
        with self.assertRaisesRegex(ValueError, "duplicados"):
            M08.integrate_results(geometry, pd.concat([complete, complete.iloc[:1]]))

    def test_modulos_no_contienen_tablas_ni_nombres_territoriales(self):
        m07_text = (ROOT / "modulos/07_agregar_resultados_electorales.py").read_text(encoding="utf-8")
        m08_text = (ROOT / "modulos/08_integrar_resultados.py").read_text(encoding="utf-8")
        for forbidden in ("RTVE", "aragon", "PP", "PSOE", "PODEMOS"):
            self.assertNotIn(forbidden, m07_text + m08_text)


if __name__ == "__main__":
    unittest.main()
