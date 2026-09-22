from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from unittest.mock import patch
from email.message import Message
from pathlib import Path

import yaml

from herramientas.comprobar_fuente_electoral_oficial import check_declaration
from herramientas.materializar_contrato_electoral_runtime import materialize
from herramientas.resolver_eleccion_vigente import resolve
from herramientas.validar_paquete_electoral import validate_package
from herramientas.preparar_fuente_electoral import prepare, validate_previous

ROOT = Path(__file__).resolve().parents[1]


class FakeResponse:
    def __init__(self, data: bytes):
        self._data = data
        self.status = 200
        self.headers = Message()
        self.headers["Content-Type"] = "text/csv"

    def read(self, n=-1):
        return self._data if n < 0 else self._data[:n]

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class ResolverIndustrialTests(unittest.TestCase):
    def test_asturias_resolves_without_manual_current_election_row(self):
        catalog = yaml.safe_load((ROOT / "configuracion/elecciones_vigentes.yaml").read_text(encoding="utf-8"))
        self.assertNotIn("principado_de_asturias", [r["territory_id"] for r in catalog["territories"]])
        row = resolve("Principado de Asturias", root_dir=ROOT, edition="2025")
        self.assertEqual(row["territory_id"], "principado_de_asturias")
        self.assertEqual(row["territorial_edition"], "2025")
        self.assertEqual(row["election_id"], "asturias_jgpa_2023")
        self.assertEqual(row["election_date"], "2023-05-28")
        self.assertEqual(row["resolution_mode"], "auto_discovered_declaration")

    def test_aragon_resolves_from_materialized_contract_without_source_declaration(self):
        catalog = yaml.safe_load((ROOT / "configuracion/catalogo_preparacion.yaml").read_text(encoding="utf-8"))
        aragon = next(r for r in catalog["territories"] if r["territory_id"] == "aragon")
        self.assertIsNone(aragon["editions"]["2025"]["electoral_source_declaration"])
        row = resolve("Aragón", root_dir=ROOT, edition="2025")
        self.assertEqual(row["territory_id"], "aragon")
        self.assertEqual(row["election_id"], "aragon_cortes_2026-02-08")
        self.assertEqual(row["election_date"], "2026-02-08")
        self.assertEqual(row["declaration"], "")
        self.assertEqual(row["resolution_mode"], "materialized_election_contract")
        self.assertEqual(
            row["election_contract"],
            "territorios/aragon/config/elecciones/aragon_cortes_2026.json",
        )

    def test_galicia_governed_override_is_preserved(self):
        row = resolve("Galicia", root_dir=ROOT, edition="2025")
        self.assertEqual(row["election_id"], "galicia_parlamento_2024")
        self.assertEqual(row["resolution_mode"], "governed_override")


class StaticContractPreparationTests(unittest.TestCase):
    @staticmethod
    def sha(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def test_static_contract_package_records_election_identity_and_rejects_stale_reuse(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            source=root/"results.json"
            source.write_text(json.dumps({"mapa":{"zonas":[]}}),encoding="utf-8")
            contract=root/"election.json"
            contract.write_text(json.dumps({
                "schema_family":"ddd-election",
                "schema_version":"1.0.0",
                "election_id":"demo_2026",
                "territory_id":"demo",
                "election_date":"2026-02-08",
                "sources":[{
                    "path":"results.json",
                    "sha256":self.sha(source),
                    "publisher":"Demo",
                    "source_url":"https://example.invalid/results",
                    "retrieved_at":"2026-09-22",
                }],
            }),encoding="utf-8")
            params=root/"params.yaml"
            params.write_text(yaml.safe_dump({
                "meta":{"territory_id":"demo","year":2025},
                "modulos":{"modulo_07_agregar_resultados_electorales":{"election_contract":"election.json"}},
            },sort_keys=False),encoding="utf-8")
            out=root/"package"
            manifest=prepare(
                territory_id="demo",edition="2025",package_out=out,root=root,params=params
            )
            self.assertEqual(manifest["election_id"],"demo_2026")
            self.assertEqual(manifest["election_date"],"2026-02-08")
            self.assertIsNotNone(validate_previous(
                out,"demo","2025",
                expected_election_id="demo_2026",
                expected_election_date="2026-02-08",
            ))
            self.assertIsNone(validate_previous(
                out,"demo","2025",
                expected_election_id="demo_2027",
                expected_election_date="2027-02-08",
            ))

    def test_new_declaration_wins_over_stale_static_contract(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            old_source=root/"old.json"
            old_source.write_text(json.dumps({"mapa":{"zonas":[{"old":1}]}}),encoding="utf-8")
            contract=root/"election_old.json"
            contract.write_text(json.dumps({
                "schema_family":"ddd-election",
                "schema_version":"1.0.0",
                "election_id":"demo_2024",
                "territory_id":"demo",
                "election_date":"2024-01-01",
                "sources":[{
                    "path":"old.json",
                    "sha256":self.sha(old_source),
                    "publisher":"Old",
                    "source_url":"https://old.example/results",
                    "retrieved_at":"2024-01-02",
                }],
            }),encoding="utf-8")
            declaration=root/"current.yaml"
            declaration.write_text(yaml.safe_dump({
                "schema":"ddd-election-official-source-declaration/1.0",
                "territory_id":"demo",
                "election_id":"demo_2026",
                "election_date":"2026-02-08",
                "minimum_resolution":"section",
                "allowed_official_hosts":["official.example"],
                "sources":[{
                    "id":"current","publisher":"Official",
                    "url":"https://official.example/current.json",
                    "required":True,"declared_resolution":"section",
                    "granularity_markers":["seccion"],
                }],
            },sort_keys=False),encoding="utf-8")
            params=root/"params.yaml"
            params.write_text(yaml.safe_dump({
                "meta":{"territory_id":"demo","year":2025},
                "modulos":{"modulo_07_agregar_resultados_electorales":{"election_contract":"election_old.json"}},
            },sort_keys=False),encoding="utf-8")
            def fake_check(data,tmp):
                tmp=Path(tmp); tmp.mkdir(parents=True,exist_ok=True)
                current=tmp/"current.json"
                current.write_text(json.dumps({"mapa":{"zonas":[{"new":1}]}}),encoding="utf-8")
                return {
                    "decision":"READY",
                    "selected_source":{
                        "id":"current","artifact_path":"current.json",
                        "url":"https://official.example/current.json",
                        "publisher":"Official",
                        "sha256":self.sha(current),"bytes":current.stat().st_size,
                    },
                    "selected_sources":[],
                    "checks":[],
                }
            out=root/"package"
            with patch("herramientas.preparar_fuente_electoral.check_declaration",side_effect=fake_check):
                manifest=prepare(
                    territory_id="demo",edition="2025",package_out=out,root=root,
                    params=params,declaration=declaration,
                )
            self.assertEqual(manifest["election_id"],"demo_2026")
            self.assertEqual(manifest["election_date"],"2026-02-08")
            self.assertEqual(manifest["decision"],"ACQUIRE")
            self.assertNotEqual(manifest["selected_source"]["sha256"],self.sha(old_source))

class VerifiedMirrorPolicyTests(unittest.TestCase):
    def base_declaration(self):
        return {
            "schema": "ddd-election-official-source-declaration/1.0",
            "territory_id": "demo",
            "election_id": "demo_2023",
            "election_date": "2023-05-28",
            "minimum_resolution": "polling_station",
            "allowed_source_hosts": ["mirror.example"],
            "sources": [{
                "id": "mirror",
                "publisher": "Verified mirror",
                "url": "https://mirror.example/results.csv",
                "source_class": "verified_mirror",
                "declared_resolution": "polling_station",
                "access": "public",
                "required": True,
                "granularity_markers": ["mesa"],
            }],
        }

    def test_verified_mirror_requires_official_reference(self):
        with tempfile.TemporaryDirectory() as td:
            result = check_declaration(
                self.base_declaration(),
                td,
                opener=lambda request, timeout=0: FakeResponse(b"mesa;votos\nA;10\n"),
            )
            self.assertEqual(result["decision"], "BLOCK")
            self.assertEqual(result["checks"][0]["status"], "BLOCK_MISSING_OFFICIAL_REFERENCE")

    def test_verified_mirror_with_official_reference_can_be_acquired(self):
        declaration = self.base_declaration()
        declaration["official_reference_urls"] = ["https://official.example/election"]
        with tempfile.TemporaryDirectory() as td:
            result = check_declaration(
                declaration,
                td,
                opener=lambda request, timeout=0: FakeResponse(b"mesa;votos\nA;10\n"),
            )
            self.assertEqual(result["decision"], "READY")
            self.assertEqual(result["selected_source"]["source_class"], "verified_mirror")


class EmbeddedContractTests(unittest.TestCase):
    @staticmethod
    def sha(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def test_package_materializes_generic_m07_m08_overlay(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            package = root / "package"
            (package / "data").mkdir(parents=True)
            (package / "contract").mkdir(parents=True)
            source = package / "data/results.csv"
            source.write_text("CUSEC_KEY;party;votes\n3300101001;A;10\n", encoding="utf-8")
            dictionary = package / "contract/party_dictionary.json"
            dictionary.write_text(json.dumps({
                "schema_family": "ddd-party-dictionary",
                "schema_version": "1.0.0",
                "unknown_party_policy": "reject",
                "parties": [{"canonical_id": "A", "display_name": "A", "aliases": [], "classification": ""}],
            }), encoding="utf-8")
            contract = package / "contract/election_contract.json"
            contract.write_text(json.dumps({
                "schema_family": "ddd-election",
                "schema_version": "1.0.0",
                "election_id": "demo_2023",
                "territory_id": "demo",
                "title": "Demo",
                "election_date": "2023-05-28",
                "input_mode": "verifiable_file",
                "boundary_independence": True,
                "sources": [{
                    "path": "data/results.csv",
                    "sha256": self.sha(source),
                    "publisher": "Mirror",
                    "source_url": "https://mirror.example",
                    "retrieved_at": "2026-09-21",
                    "adapter": {"kind": "long_csv", "separator": ";", "section_field": "CUSEC_KEY", "party_field": "party", "votes_field": "votes"},
                }],
                "party_dictionary": {"path": "contract/party_dictionary.json", "sha256": self.sha(dictionary)},
                "reconciliation": {"policy": "fail_unless_declared", "allowed_result_only_sections": [], "allowed_map_only_sections": []},
            }), encoding="utf-8")
            manifest = {
                "schema": "ddd-electoral-package/1.0",
                "decision": "ACQUIRE",
                "territory_id": "demo",
                "edition": "2025",
                "election_id": "demo_2023",
                "selected_source": {
                    "path": "data/results.csv",
                    "sha256": self.sha(source),
                    "bytes": source.stat().st_size,
                },
                "embedded_contract": {
                    "election_contract": "contract/election_contract.json",
                    "party_dictionary": "contract/party_dictionary.json",
                    "contract_sha256": self.sha(contract),
                    "party_dictionary_sha256": self.sha(dictionary),
                },
            }
            (package / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            params = root / "params.yaml"
            params.write_text(yaml.safe_dump({
                "meta": {"territory_id": "demo", "year": 2025, "run_name": "demo_2025"},
                "io": {"cache": {"dir": "territorios/demo/.cache/{run_name}"}},
                "modulos": {
                    "modulo_06_consolidar_distritos": {
                        "out_geojson": "territorios/demo/.cache/{run_name}/{run_name}_m06_secciones.geojson.zip",
                        "out_district_geojson": "territorios/demo/.cache/{run_name}/{run_name}_m06_distritos.geojson.zip",
                        "id_field": "CUSEC_KEY",
                        "district_field": "district_id",
                    }
                },
            }, sort_keys=False), encoding="utf-8")
            validation_path = root / "validation.json"
            payload = validate_package(
                package=package, params=params, territory_id="demo", edition="2025",
                root=root, materialize=True,
            )
            validation_path.write_text(json.dumps(payload), encoding="utf-8")
            self.assertEqual(payload["mode"], "embedded_runtime_contract")
            self.assertTrue((root / payload["runtime_contract_path"]).is_file())

            overlay = root / "runtime_params.yaml"
            result = materialize(params, validation_path, overlay)
            self.assertEqual(result, overlay)
            cfg = yaml.safe_load(overlay.read_text(encoding="utf-8"))
            m07 = cfg["modulos"]["modulo_07_agregar_resultados_electorales"]
            m08 = cfg["modulos"]["modulo_08_integrar_resultados"]
            self.assertEqual(m07["election_contract"], payload["runtime_contract_path"])
            self.assertEqual(m07["in_geojson"], cfg["modulos"]["modulo_06_consolidar_distritos"]["out_geojson"])
            self.assertEqual(m08["in_district_geojson"], cfg["modulos"]["modulo_06_consolidar_distritos"]["out_district_geojson"])


class WorkflowContractTests(unittest.TestCase):
    def test_preparation_installs_xlsx_runtime_and_incorporation_materializes_overlay(self):
        prepare = (ROOT / ".github/workflows/preparacion-resultados-electorales.yml").read_text(encoding="utf-8")
        incorporate = (ROOT / ".github/workflows/_reutilizable-incorporacion-electoral.yml").read_text(encoding="utf-8")
        self.assertIn("openpyxl==3.1.5", prepare)
        self.assertIn("materializar_contrato_electoral_runtime.py", incorporate)
        self.assertIn('echo "PARAMS=$runtime_params" >> "$GITHUB_ENV"', incorporate)


if __name__ == "__main__":
    unittest.main()
