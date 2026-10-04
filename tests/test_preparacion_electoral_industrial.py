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
from herramientas.preparar_fuente_electoral import (
    _copy_raw_sources,
    merge_delimited_sources,
    prepare,
    validate_previous,
)
from ddd_core.electoral_contract import load_election_contract

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

    def test_aragon_materialized_contract_is_pinned_for_reuse(self):
        params = ROOT / "territorios/aragon/config/aragon_2025.yaml"
        cfg = yaml.safe_load(params.read_text(encoding="utf-8")) or {}
        m07 = (cfg.get("modulos") or {}).get("modulo_07_agregar_resultados_electorales") or {}
        self.assertEqual(
            m07.get("election_contract"),
            "territorios/aragon/config/elecciones/aragon_cortes_2026.json",
        )
        self.assertFalse((cfg.get("meta") or {}).get("electoral_sources_declaration"))
        contract_path = ROOT / m07["election_contract"]
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        self.assertEqual(contract["territory_id"], "aragon")
        self.assertEqual(contract["election_id"], "aragon_cortes_2026-02-08")
        self.assertEqual(contract["election_date"], "2026-02-08")
        source = contract["sources"][0]
        manifest = (ROOT / "inputs/MANIFEST.sha256").read_text(encoding="utf-8")
        self.assertIn(
            f'{source["sha256"]}  {source["path"]}',
            manifest,
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
            validated = validate_package(
                package=out,
                params=params,
                territory_id="demo",
                edition="2025",
                root=root,
                materialize=False,
            )
            self.assertEqual(validated["decision"], "READY_PACKAGE")
            self.assertEqual(validated["election_identity_mode"], "exact")
            legacy_contract = json.loads(contract.read_text(encoding="utf-8"))
            legacy_contract["election_id"] = "demo_2026-2026-02-08"
            contract.write_text(json.dumps(legacy_contract), encoding="utf-8")
            legacy_validated = validate_package(
                package=out,
                params=params,
                territory_id="demo",
                edition="2025",
                root=root,
                materialize=False,
            )
            self.assertEqual(legacy_validated["election_identity_mode"], "legacy_date_suffix_alias")
            manifest_path = out / "manifest.json"
            tampered = json.loads(manifest_path.read_text(encoding="utf-8"))
            tampered["election_id"] = "demo_2027"
            manifest_path.write_text(json.dumps(tampered), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "election_id del contrato electoral estático"):
                validate_package(
                    package=out,
                    params=params,
                    territory_id="demo",
                    edition="2025",
                    root=root,
                    materialize=False,
                )

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
                "election_date": "2023-05-28",
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

            manifest_path = package / "manifest.json"
            tampered = json.loads(manifest_path.read_text(encoding="utf-8"))
            tampered["election_date"] = "2024-01-01"
            manifest_path.write_text(json.dumps(tampered), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "election_date del contrato electoral embebido"):
                validate_package(
                    package=package,
                    params=params,
                    territory_id="demo",
                    edition="2025",
                    root=root,
                    materialize=False,
                )


class StructuralProvenancePackagingTests(unittest.TestCase):
    @staticmethod
    def sha(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    @staticmethod
    def wide_adapter(sidecar_path: str, sidecar_sha: str) -> dict:
        return {
            "kind":"wide_polling_station_csv",
            "separator":";",
            "province_field":"province",
            "municipality_field":"municipality",
            "polling_station_field":"polling",
            "polling_station_regex":(
                r"^(?P<district>\d+)-(?P<section>\d+)-[A-Z]$"
            ),
            "party_columns":["P","Q"],
            "party_applicability":{
                "Q":{
                    "field":"province",
                    "equals":["32"],
                    "reason":"fixture",
                }
            },
            "structural_provenance":{
                "path":sidecar_path,
                "sha256":sidecar_sha,
            },
            "record_classification":{
                "polling_station":{"mode":"locator_contract"},
                "aggregates":[{
                    "id":"total",
                    "match":{
                        "field":"province",
                        "equals":"SUM",
                        "required_empty_fields":[
                            "municipality","polling"
                        ],
                    },
                    "scope":{
                        "kind":"preceding_polling_station_block",
                        "partition_field":"province",
                    },
                    "vote_reconciliation":{
                        "kind":"party_columns_exact_sum",
                        "empty_aggregate_value":"reject",
                    },
                }],
                "require_aggregate_for_each_block":True,
            },
        }

    def _write_dictionary(self, path: Path) -> None:
        path.write_text(json.dumps({
            "schema_family":"ddd-party-dictionary",
            "schema_version":"1.0.0",
            "unknown_party_policy":"reject",
            "parties":[
                {"canonical_id":"P","display_name":"P"},
                {"canonical_id":"Q","display_name":"Q"},
            ],
        }),encoding="utf-8")

    def test_static_contract_package_embeds_sidecar_without_claiming_raws(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            raw=root/"raw.csv"
            raw.write_text(
                "province;municipality;polling;P;Q\n"
                "32;1;1-1-A;7;0\n"
                "SUM;;;7;0\n",
                encoding="utf-8",
            )
            merged=root/"results.csv"
            info=merge_delimited_sources(
                [raw],
                merged,
                source_ids=["p32"],
            )
            sidecar=Path(info["structural_provenance_path"])
            dictionary=root/"parties.json"
            self._write_dictionary(dictionary)
            contract=root/"election.json"
            contract.write_text(json.dumps({
                "schema_family":"ddd-election",
                "schema_version":"1.0.0",
                "election_id":"demo_2026",
                "territory_id":"demo",
                "title":"Demo",
                "election_date":"2026-01-01",
                "input_mode":"verifiable_file",
                "boundary_independence":True,
                "sources":[{
                    "path":"results.csv",
                    "sha256":self.sha(merged),
                    "publisher":"Official",
                    "source_url":"https://official.example/results",
                    "retrieved_at":"2026-01-02",
                    "adapter":self.wide_adapter(
                        sidecar.name,
                        self.sha(sidecar),
                    ),
                }],
                "party_dictionary":{
                    "path":"parties.json",
                    "sha256":self.sha(dictionary),
                },
                "reconciliation":{
                    "policy":"fail_unless_declared",
                    "allowed_result_only_sections":[],
                    "allowed_map_only_sections":[],
                },
            }),encoding="utf-8")
            params=root/"params.yaml"
            params.write_text(yaml.safe_dump({
                "meta":{"territory_id":"demo","year":2025},
                "modulos":{
                    "modulo_07_agregar_resultados_electorales":{
                        "election_contract":"election.json"
                    }
                },
            }),encoding="utf-8")

            out=root/"package"
            manifest=prepare(
                territory_id="demo",
                edition="2025",
                package_out=out,
                root=root,
                params=params,
            )
            self.assertEqual(manifest["decision"],"REUSE")
            structural=manifest["structural_provenance"]
            self.assertFalse(structural["raw_sources_embedded"])
            self.assertTrue((out/structural["path"]).is_file())
            self.assertEqual(
                structural["merged_source_sha256"],
                manifest["selected_source"]["sha256"],
            )
            embedded=manifest["embedded_contract"]
            portable=json.loads(
                (out/embedded["election_contract"]).read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(
                portable["sources"][0]["adapter"][
                    "structural_provenance"
                ]["path"],
                "evidence/structural_provenance.json",
            )
            self.assertIsNotNone(
                validate_previous(out,"demo","2025")
            )

    def test_embedded_runtime_contract_materializes_verified_sidecar(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            package=root/"package"
            (package/"data").mkdir(parents=True)
            (package/"contract").mkdir(parents=True)
            (package/"evidence").mkdir(parents=True)

            raw15=root/"p15.csv"
            raw15.write_text(
                "province;municipality;polling;P\n"
                "15;7;1-1-A;5\n"
                "SUM;;;5\n",
                encoding="utf-8",
            )
            raw32=root/"p32.csv"
            raw32.write_text(
                "province;municipality;polling;P;Q\n"
                "32;1;1-1-A;7;0\n"
                "SUM;;;7;0\n",
                encoding="utf-8",
            )
            generated=root/"merged.csv"
            info=merge_delimited_sources(
                [raw15,raw32],
                generated,
                source_ids=["p15","p32"],
            )
            source=package/"data/results.csv"
            source.write_bytes(generated.read_bytes())
            sidecar=package/"evidence/structural_provenance.json"
            sidecar.write_bytes(
                Path(info["structural_provenance_path"]).read_bytes()
            )

            dictionary=package/"contract/party_dictionary.json"
            self._write_dictionary(dictionary)
            contract=package/"contract/election_contract.json"
            adapter=self.wide_adapter(
                "evidence/structural_provenance.json",
                self.sha(sidecar),
            )
            contract.write_text(json.dumps({
                "schema_family":"ddd-election",
                "schema_version":"1.0.0",
                "election_id":"demo_2026",
                "territory_id":"demo",
                "title":"Demo",
                "election_date":"2026-01-01",
                "input_mode":"verifiable_file",
                "boundary_independence":True,
                "sources":[{
                    "path":"data/results.csv",
                    "sha256":self.sha(source),
                    "publisher":"Official",
                    "source_url":"https://official.example/results",
                    "retrieved_at":"2026-01-02",
                    "adapter":adapter,
                }],
                "party_dictionary":{
                    "path":"contract/party_dictionary.json",
                    "sha256":self.sha(dictionary),
                },
                "reconciliation":{
                    "policy":"fail_unless_declared",
                    "allowed_result_only_sections":[],
                    "allowed_map_only_sections":[],
                },
            }),encoding="utf-8")
            manifest={
                "schema":"ddd-electoral-package/1.0",
                "decision":"ACQUIRE",
                "territory_id":"demo",
                "edition":"2025",
                "election_id":"demo_2026",
                "election_date":"2026-01-01",
                "selected_source":{
                    "path":"data/results.csv",
                    "sha256":self.sha(source),
                    "bytes":source.stat().st_size,
                },
                "structural_provenance":{
                    "schema":"ddd-electoral-structural-provenance/1.0",
                    "path":"evidence/structural_provenance.json",
                    "sha256":self.sha(sidecar),
                    "merged_source_sha256":self.sha(source),
                    "raw_sources_embedded":False,
                },
                "embedded_contract":{
                    "election_contract":"contract/election_contract.json",
                    "party_dictionary":"contract/party_dictionary.json",
                    "contract_sha256":self.sha(contract),
                    "party_dictionary_sha256":self.sha(dictionary),
                    "structural_provenance":"evidence/structural_provenance.json",
                    "structural_provenance_sha256":self.sha(sidecar),
                },
            }
            (package/"manifest.json").write_text(
                json.dumps(manifest),encoding="utf-8"
            )
            params=root/"params.yaml"
            params.write_text(yaml.safe_dump({
                "meta":{
                    "territory_id":"demo",
                    "year":2025,
                    "run_name":"demo_2025",
                },
                "modulos":{},
            }),encoding="utf-8")

            payload=validate_package(
                package=package,
                params=params,
                territory_id="demo",
                edition="2025",
                root=root,
                materialize=True,
            )
            runtime_contract=root/payload["runtime_contract_path"]
            runtime=json.loads(
                runtime_contract.read_text(encoding="utf-8")
            )
            runtime_decl=runtime["sources"][0]["adapter"][
                "structural_provenance"
            ]
            runtime_sidecar=root/runtime_decl["path"]
            self.assertTrue(runtime_sidecar.is_file())
            self.assertEqual(
                payload["structural_provenance_sha256"],
                self.sha(runtime_sidecar),
            )
            loaded,_=load_election_contract(
                runtime_contract,
                project_root=root,
                expected_territory_id="demo",
            )
            self.assertEqual(
                loaded["sources"][0]["adapter"][
                    "structural_provenance"
                ]["resolved_path"],
                str(runtime_sidecar.resolve()),
            )

            tampered=json.loads(
                (package/"manifest.json").read_text(encoding="utf-8")
            )
            tampered["structural_provenance"]["sha256"]="0"*64
            (package/"manifest.json").write_text(
                json.dumps(tampered),encoding="utf-8"
            )
            with self.assertRaisesRegex(
                ValueError,
                r"declaración estructural del paquete no coincide",
            ):
                validate_package(
                    package=package,
                    params=params,
                    territory_id="demo",
                    edition="2025",
                    root=root,
                    materialize=False,
                )

    def test_reuse_preserves_structural_sidecar_and_embedded_raws(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            raw_a=root/"a"/"results.csv"
            raw_b=root/"b"/"results.csv"
            raw_a.parent.mkdir()
            raw_b.parent.mkdir()
            raw_a.write_text(
                "province;municipality;polling;P\n"
                "15;7;1-1-A;5\n"
                "SUM;;;5\n",
                encoding="utf-8",
            )
            raw_b.write_text(
                "province;municipality;polling;P;Q\n"
                "32;1;1-1-A;7;0\n"
                "SUM;;;7;0\n",
                encoding="utf-8",
            )
            previous=root/"previous"
            (previous/"data").mkdir(parents=True)
            generated=root/"merged.csv"
            info=merge_delimited_sources(
                [raw_a,raw_b],
                generated,
                source_ids=["p15","p32"],
            )
            source=previous/"data/results.csv"
            source.write_bytes(generated.read_bytes())
            selected=[
                {
                    "id":"p15",
                    "sha256":self.sha(raw_a),
                    "url":"https://official.example/p15",
                    "publisher":"Official",
                },
                {
                    "id":"p32",
                    "sha256":self.sha(raw_b),
                    "url":"https://official.example/p32",
                    "publisher":"Official",
                },
            ]
            raw_manifest=_copy_raw_sources(
                package_out=previous,
                selected_sources=selected,
                source_paths=[raw_a,raw_b],
            )
            (previous/"evidence").mkdir()
            sidecar=previous/"evidence/structural_provenance.json"
            sidecar.write_bytes(
                Path(info["structural_provenance_path"]).read_bytes()
            )
            manifest={
                "schema":"ddd-electoral-package/1.0",
                "decision":"ACQUIRE",
                "territory_id":"demo",
                "edition":"2025",
                "election_id":"demo_2026",
                "election_date":"2026-01-01",
                "selected_source":{
                    "path":"data/results.csv",
                    "sha256":self.sha(source),
                    "bytes":source.stat().st_size,
                    "records":4,
                    "record_count_method":"delimited_rows_excluding_header",
                },
                "raw_sources":raw_manifest,
                "structural_provenance":{
                    "schema":"ddd-electoral-structural-provenance/1.0",
                    "path":"evidence/structural_provenance.json",
                    "sha256":self.sha(sidecar),
                    "merged_source_sha256":self.sha(source),
                    "raw_sources_embedded":True,
                },
            }
            (previous/"manifest.json").write_text(
                json.dumps(manifest),encoding="utf-8"
            )

            out=root/"reused"
            result=prepare(
                territory_id="demo",
                edition="2025",
                package_out=out,
                root=root,
                previous=previous,
                previous_run_id="123",
                previous_artifact_name="fixture",
            )
            self.assertEqual(result["decision"],"REUSE")
            self.assertTrue(
                result["structural_provenance"]["raw_sources_embedded"]
            )
            self.assertEqual(len(result["raw_sources"]),2)
            self.assertNotEqual(
                result["raw_sources"][0]["path"],
                result["raw_sources"][1]["path"],
            )
            for raw in result["raw_sources"]:
                self.assertTrue((out/raw["path"]).is_file())
            self.assertIsNotNone(validate_previous(out,"demo","2025"))

    def test_copy_raw_sources_avoids_same_basename_collision(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            first=root/"a"/"results.csv"
            second=root/"b"/"results.csv"
            first.parent.mkdir()
            second.parent.mkdir()
            first.write_text("x\n1\n",encoding="utf-8")
            second.write_text("x\n2\n",encoding="utf-8")
            package=root/"package"
            package.mkdir()
            selected=[
                {"id":"a","sha256":self.sha(first)},
                {"id":"b","sha256":self.sha(second)},
            ]
            copied=_copy_raw_sources(
                package_out=package,
                selected_sources=selected,
                source_paths=[first,second],
            )
            self.assertEqual(len({row["path"] for row in copied}),2)
            self.assertEqual(
                [Path(row["path"]).name for row in copied],
                ["000_results.csv","001_results.csv"],
            )


class WorkflowContractTests(unittest.TestCase):
    def test_preparation_installs_xlsx_runtime_and_incorporation_materializes_overlay(self):
        prepare = (ROOT / ".github/workflows/preparacion-resultados-electorales.yml").read_text(encoding="utf-8")
        incorporate = (ROOT / ".github/workflows/_reutilizable-incorporacion-electoral.yml").read_text(encoding="utf-8")
        self.assertIn("openpyxl==3.1.5", prepare)
        self.assertIn("materializar_contrato_electoral_runtime.py", incorporate)
        self.assertIn('echo "PARAMS=$runtime_params" >> "$GITHUB_ENV"', incorporate)


if __name__ == "__main__":
    unittest.main()
