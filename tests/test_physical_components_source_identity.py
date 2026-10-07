from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import yaml

from herramientas._resolver_ejecucion_completa_core import _hard_partition_spec
from herramientas.preparar_particiones_fisicas_m04 import prepare


ROOT = Path(__file__).resolve().parents[1]
LOOKUP = ROOT / "configuracion/particiones_insulares_2025.json"

EXPECTED = {
    "illes_balears": {
        2023: {
            "sectioning_sha256": "d548b2ed2cb180ab16e520f56751bb9b36f1bba5a77283ef70be15037d9eda1e",
            "territorial_identity_sha256": "dc2fa1ab23ced23fee4e52ed7069ed8ab8662e112db455e9ddac74adbbddaa61",
            "universe": 670,
            "universe_hash": "9360343a8c2a5d7b1e6fa167155d001a652bbab42df66c70be405052f52bbd2a",
            "components": {"07-C01": 532, "07-C02": 56, "07-C03": 6, "07-C04": 76},
            "hashes": {
                "07-C01": "c0398f331f91e66336cb3da29088e6d93a5f3e160d78f46b1a04fac4d9865558",
                "07-C02": "7d0f1842fc102e74aa795ef8e0e6d7235bc3c2a218402988422706da088374a8",
                "07-C03": "c390167612a821cb9112cfe5c5ef0a93627ed5821b1fae9d19411c711050c497",
                "07-C04": "ede71e3a5eaafa5d19911b67fb76c1feab6199ec2b9dfff035092e4436b33a91",
            },
        },
        2025: {
            "sectioning_sha256": "0a18c80304985b5819bc29854d745c3cbb5ffb79a9c3723f5a31d61dc5aec8a1",
            "territorial_identity_sha256": "7c47dd7f3d94a70bad560b33205cb33a07b25b65cc758d7c85b908fe75b3ee91",
            "universe": 674,
            "universe_hash": "9840bcfa657cbd05b0e04fefa99316c7fb8f9d085d030eea6060796b22ef9f8c",
            "components": {"07-C01": 536, "07-C02": 56, "07-C03": 6, "07-C04": 76},
            "hashes": {
                "07-C01": "92d618a6b53523078fd6e6b2aa1beeb35068c0a428c47b286ca619028e6758b3",
                "07-C02": "7d0f1842fc102e74aa795ef8e0e6d7235bc3c2a218402988422706da088374a8",
                "07-C03": "c390167612a821cb9112cfe5c5ef0a93627ed5821b1fae9d19411c711050c497",
                "07-C04": "ede71e3a5eaafa5d19911b67fb76c1feab6199ec2b9dfff035092e4436b33a91",
            },
        },
    },
    "canarias": {
        2023: {
            "sectioning_sha256": "eadf400e05922fe7116c384a227ed06e7f80769e30e3aceb626d46ce602cafc5",
            "territorial_identity_sha256": "77f8f22c63638601550e705b739260dfdd293afd109fdf20939c302f84f2918f",
            "universe": 1396,
            "universe_hash": "742f40b58ebe2c704aa839c3f6579dc0916e721d09f3d9d8c8ddb50e4d06f755",
            "components": {
                "35-C01": 585, "35-C02": 55, "35-C03": 74, "35-C04": 1,
                "38-C01": 599, "38-C02": 15, "38-C03": 61, "38-C04": 6,
            },
            "hashes": {
                "35-C01": "a4f61a58f817e95f8f64d6f91ef010d8e24b03647632de01be603e70c5fff4b9",
                "35-C02": "57378924a829dcb9b22f58f6ba32c2767b74e3a1a27cd036846d7b19e5cf2008",
                "35-C03": "07e47b7019692dd5f0dc02a1380092df133d1c696a7e6eddd7e9e5b44cff7386",
                "35-C04": "a72512d9a41eba4a25987f5bd4441ec5f632c4ac4ed11440b5083a75a887691d",
                "38-C01": "764660e1935a2bc50b71083baa054d3b18938c8476405fe5c749ebbda2b463ce",
                "38-C02": "8d7ca174e6f462ce0e3164b86aeb5d566c73f1bc68ab1861623c6a032df56488",
                "38-C03": "53cb1cad0d8d7e326f1c2bc780c97efc6c396652d3a281e9b62a82095dffd1a9",
                "38-C04": "d402bde485452cc28088e70a05c883c06647479186b6a26016a42b29704babd1",
            },
        },
        2025: {
            "sectioning_sha256": "13685e7fedaf80f74f162c06703b5367c61dc310fc9436c6ca28afffe3fb10fd",
            "territorial_identity_sha256": "b6e86da2c9708d4ea58a915c0021859cc2a260d7ba179a34a945a10368d13120",
            "universe": 1407,
            "universe_hash": "067cfe5845d23e81261bf41f69dae694d33bb815e4b77d8bb1a4c3c69688189c",
            "components": {
                "35-C01": 589, "35-C02": 56, "35-C03": 77, "35-C04": 1,
                "38-C01": 602, "38-C02": 15, "38-C03": 61, "38-C04": 6,
            },
            "hashes": {
                "35-C01": "2436fc07a477a660d004210fabc006078b2db373692920a8bdf0c8846d972f5a",
                "35-C02": "277c1ab0c60744986c3c21c9e32e534cfca4499e2de9f791d5fa3ab074ec1773",
                "35-C03": "ff2667f16ad33950a073f84bcd18fba4f5018495c36381957823f9027b405b32",
                "35-C04": "a72512d9a41eba4a25987f5bd4441ec5f632c4ac4ed11440b5083a75a887691d",
                "38-C01": "8b9c4001e19b457228b824aa41481d6beaa0e84de989d445e6fca66879ddc9f2",
                "38-C02": "8d7ca174e6f462ce0e3164b86aeb5d566c73f1bc68ab1861623c6a032df56488",
                "38-C03": "53cb1cad0d8d7e326f1c2bc780c97efc6c396652d3a281e9b62a82095dffd1a9",
                "38-C04": "d402bde485452cc28088e70a05c883c06647479186b6a26016a42b29704babd1",
            },
        },
    },
}


def _set_hash(values: list[str]) -> str:
    return hashlib.sha256(("\n".join(sorted(values)) + "\n").encode("utf-8")).hexdigest()


def _identity(*, territory_id: str, population_year: int, section_year: int,
              package_sha256: str, compatibility_identity_sha256: str | None = None) -> str:
    payload = {
        "territory_id": territory_id,
        "edition": "2025",
        "population_year": population_year,
        "section_year": section_year,
        "package_sha256": package_sha256,
    }
    if compatibility_identity_sha256:
        payload["compatibility_identity_sha256"] = compatibility_identity_sha256
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _contract_for_inventory(territory_id: str, year: int) -> dict:
    contract_path = ROOT / f"territorios/{territory_id}/config/{territory_id}_2025.yaml"
    contract = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
    lookup = json.loads(LOOKUP.read_text(encoding="utf-8"))
    inventory = next(
        row for row in lookup["territories"][territory_id]["inventories"]
        if int(row["section_year"]) == year
    )
    meta = contract["meta"]
    meta["source_population_year"] = int(inventory["population_year"])
    meta["source_section_year"] = int(inventory["section_year"])
    baseline = contract["validation"].setdefault("source_baseline", {})
    baseline.update({
        "schema": "ddd.source-baseline/1.0",
        "edition": "2025",
        "population_year": int(inventory["population_year"]),
        "section_year": int(inventory["section_year"]),
        "target_section_count": int(inventory["universe_section_count"]),
        "package_sha256": inventory["source_package_sha256"],
    })
    if inventory.get("compatibility_identity_sha256"):
        baseline["compatibility_identity_sha256"] = inventory["compatibility_identity_sha256"]
    else:
        baseline.pop("compatibility_identity_sha256", None)
    state = contract.setdefault("generation_state", {})
    state["package_sha256"] = inventory["source_package_sha256"]
    if inventory.get("compatibility_identity_sha256"):
        state["compatibility_identity_sha256"] = inventory["compatibility_identity_sha256"]
    else:
        state.pop("compatibility_identity_sha256", None)
    state["source_inputs"] = [{
        "path": f"inputs/seccionado_{year}.zip",
        "sha256": inventory["sectioning_sha256"],
        "role": "target_sectioning",
        "source_id": "secciones_censales",
    }]
    return contract


class _FakeM04:
    def __init__(self, contract: dict, source: Path, output: Path, input_df: pd.DataFrame, *, mode: str = "ok"):
        self.contract = contract
        self.source = source
        self.output = output
        self.input_df = input_df.copy()
        self.output_df: pd.DataFrame | None = None
        self.mode = mode

    def load_params_yaml(self, _path: str) -> dict:
        return self.contract

    def load_geo(self, path: Path) -> pd.DataFrame:
        return (self.input_df if Path(path) == self.source else self.output_df).copy()

    def prepare_hard_partitions(self, _path: str) -> None:
        out = self.input_df.copy()
        out["DDD_PARTITION"] = out["CUMUN"].map({"07001": "A", "07002": "B"})
        if self.mode == "loss":
            out = out.iloc[:-1].copy()
        elif self.mode == "wrong_component":
            out.loc[out["CUSEC_KEY"] == "0700101001", "DDD_PARTITION"] = "B"
        out["DDD_MUNICIPALITY_PARTITION"] = out["CUMUN"] + ":" + out["DDD_PARTITION"]
        self.output_df = out
        self.output.touch()


def _demo_contract(root: Path, ids: list[str]) -> tuple[dict, Path, Path]:
    source = root / "source.geojson.zip"
    output = root / "partitions.geojson.zip"
    source.touch()
    package_sha = "a" * 64
    compatibility_sha = "b" * 64
    sectioning_sha = "c" * 64
    identity = _identity(
        territory_id="demo",
        population_year=2023,
        section_year=2023,
        package_sha256=package_sha,
        compatibility_identity_sha256=compatibility_sha,
    )
    by_component = {
        "A": [section for section in ids if section[:5] == "07001"],
        "B": [section for section in ids if section[:5] == "07002"],
    }
    lookup = root / "particiones.json"
    lookup.write_text(json.dumps({
        "schema": "ddd-archipelago-partitions/1.2",
        "territories": {
            "demo": {
                "partition_mode": "physical_components",
                "physical_component_count": 2,
                "components": {
                    "A": {"province_code": "07", "name": "A"},
                    "B": {"province_code": "07", "name": "B"},
                },
                "municipality_to_partition": {"07001": "A", "07002": "B"},
                "section_overrides": {},
                "inventories": [{
                    "inventory_id": "secciones_2023",
                    "section_year": 2023,
                    "population_year": 2023,
                    "sectioning_sha256": sectioning_sha,
                    "territorial_identity_sha256": identity,
                    "compatibility_identity_sha256": compatibility_sha,
                    "source_package_sha256": package_sha,
                    "universe_section_count": 3,
                    "universe_cusec_set_sha256": _set_hash([
                        "0700101001", "0700201001", "0700201002"
                    ]),
                    "component_sections": {"A": 1, "B": 2},
                    "component_cusec_set_sha256": {
                        "A": _set_hash(["0700101001"]),
                        "B": _set_hash(["0700201001", "0700201002"]),
                    },
                }],
            }
        },
    }, indent=2) + "\n", encoding="utf-8")
    contract = {
        "meta": {
            "territory_id": "demo", "run_name": "demo_2025", "year": 2025,
            "source_population_year": 2023, "source_section_year": 2023,
        },
        "territory_contract": {"k_districts": 2},
        "modulos": {
            "modulo_01_preparar_base_territorial": {"out_geojson": str(source)},
            "modulo_02_construir_adyacencias": {"topology_bridges": []},
            "modulo_04_generar_semillas": {
                "source_geojson": str(source),
                "in_geojson": str(output),
                "id_field": "CUSEC_KEY",
                "source_municipality_field": "CUMUN",
                "province_field": "DDD_PARTITION",
                "municipality_field": "DDD_MUNICIPALITY_PARTITION",
                "district_apportionment": "hamilton_components",
                "hard_partition_lookup": str(lookup),
                "hard_partition_territory_id": "demo",
            },
        },
        "validation": {
            "hard_partition_mode": "physical_components",
            "hard_partition_lookup": str(lookup),
            "province_apportionment": "hamilton_components",
            "province_field": "DDD_PARTITION",
            "municipality_field": "DDD_MUNICIPALITY_PARTITION",
            "province_districts": {"A": 1, "B": 1},
            "partition_populations": {"A": 100, "B": 200},
            "partition_apportionment_audit": {
                "A": {"population": 100, "districts": 1, "floor_exception_required": False, "floor_exception_governed": True},
                "B": {"population": 200, "districts": 1, "floor_exception_required": False, "floor_exception_governed": True},
            },
            "population_floor_exempt_partitions": [],
            "source_baseline": {
                "schema": "ddd.source-baseline/1.0",
                "edition": "2025",
                "population_year": 2023,
                "section_year": 2023,
                "target_section_count": 3,
                "package_sha256": package_sha,
                "compatibility_identity_sha256": compatibility_sha,
            },
        },
        "generation_state": {
            "package_sha256": package_sha,
            "compatibility_identity_sha256": compatibility_sha,
            "source_inputs": [{
                "path": "inputs/seccionado_2023.zip",
                "sha256": sectioning_sha,
                "role": "target_sectioning",
                "source_id": "secciones_censales",
            }],
        },
    }
    return contract, source, output


class PhysicalComponentsSourceIdentityTests(unittest.TestCase):
    def test_real_four_accredited_inventories_are_selectable_and_exact(self):
        lookup = json.loads(LOOKUP.read_text(encoding="utf-8"))
        expected_names = {
            "illes_balears": {"07-C01": "Mallorca", "07-C02": "Menorca", "07-C03": "Formentera", "07-C04": "Ibiza/Eivissa"},
            "canarias": {
                "35-C01": "Gran Canaria", "35-C02": "Fuerteventura", "35-C03": "Lanzarote",
                "35-C04": "La Graciosa", "38-C01": "Tenerife", "38-C02": "La Gomera",
                "38-C03": "La Palma", "38-C04": "El Hierro",
            },
        }
        for territory_id, years in EXPECTED.items():
            territory = lookup["territories"][territory_id]
            self.assertEqual(expected_names[territory_id], {
                key: row["name"] for key, row in territory["components"].items()
            })
            self.assertEqual(len(expected_names[territory_id]), territory["physical_component_count"])
            for year, expected in years.items():
                with self.subTest(territory=territory_id, section_year=year):
                    hard = _hard_partition_spec(_contract_for_inventory(territory_id, year), ROOT)
                    self.assertEqual(f"secciones_{year}", hard["inventory_id"])
                    self.assertEqual(year, hard["source_identity"]["section_year"])
                    self.assertEqual(expected["sectioning_sha256"], hard["source_identity"]["sectioning_sha256"])
                    self.assertEqual(expected["territorial_identity_sha256"], hard["source_identity"]["territorial_identity_sha256"])
                    self.assertEqual(expected["universe"], hard["expected_graph_nodes"])
                    self.assertEqual(expected["universe_hash"], hard["universe_cusec_set_sha256"])
                    self.assertEqual(expected["components"], hard["component_sections"])
                    self.assertEqual(expected["hashes"], hard["component_cusec_set_sha256"])
                    self.assertEqual(len(expected["components"]), hard["expected_global_components"])
                    contract = _contract_for_inventory(territory_id, year)
                    self.assertEqual([], contract["modulos"]["modulo_02_construir_adyacencias"].get("topology_bridges"))

        self.assertEqual(
            "35-C04",
            lookup["territories"]["canarias"]["section_overrides"]["3502401010"],
        )

    def test_current_contracts_select_2023_not_product_edition_2025(self):
        for territory_id in ("illes_balears", "canarias"):
            contract = yaml.safe_load(
                (ROOT / f"territorios/{territory_id}/config/{territory_id}_2025.yaml").read_text(encoding="utf-8")
            )
            hard = _hard_partition_spec(contract, ROOT)
            self.assertEqual("secciones_2023", hard["inventory_id"], territory_id)
            self.assertEqual(2023, hard["source_identity"]["section_year"], territory_id)

    def test_unaccredited_source_identity_fails_closed(self):
        contract = _contract_for_inventory("illes_balears", 2023)
        contract["generation_state"]["source_inputs"][0]["sha256"] = "f" * 64
        with self.assertRaisesRegex(ValueError, "SOURCE_IDENTITY_MISMATCH"):
            _hard_partition_spec(contract, ROOT)

    def test_materializer_conserves_input_output_and_records_hashes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ids = ["0700101001", "0700201001", "0700201002"]
            contract, source, output = _demo_contract(root, ids)
            params = root / "demo.yaml"
            params.write_text(yaml.safe_dump(contract, sort_keys=False), encoding="utf-8")
            df = pd.DataFrame({"CUSEC_KEY": ids, "CUMUN": ["07001", "07002", "07002"]})
            fake = _FakeM04(contract, source, output, df)
            with patch("herramientas.preparar_particiones_fisicas_m04._load_m04", return_value=fake):
                result = prepare(params, "123", root_dir=root)
            self.assertTrue(result["input_output_cusec_equal"])
            self.assertEqual(3, result["input_section_count"])
            self.assertEqual(3, result["output_section_count"])
            self.assertEqual(_set_hash(ids), result["universe_cusec_set_sha256"])
            self.assertEqual({"A": 1, "B": 2}, result["component_sections"])

    def test_loss_after_source_fix_is_materialization_defect(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ids = ["0700101001", "0700201001", "0700201002"]
            contract, source, output = _demo_contract(root, ids)
            params = root / "demo.yaml"
            params.write_text(yaml.safe_dump(contract, sort_keys=False), encoding="utf-8")
            df = pd.DataFrame({"CUSEC_KEY": ids, "CUMUN": ["07001", "07002", "07002"]})
            fake = _FakeM04(contract, source, output, df, mode="loss")
            with patch("herramientas.preparar_particiones_fisicas_m04._load_m04", return_value=fake):
                with self.assertRaisesRegex(ValueError, "MATERIALIZATION_DEFECT"):
                    prepare(params, "123", root_dir=root)

    def test_same_count_wrong_cusec_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ids = ["0700101001", "0700201001", "0700201999"]
            contract, source, output = _demo_contract(root, ids)
            params = root / "demo.yaml"
            params.write_text(yaml.safe_dump(contract, sort_keys=False), encoding="utf-8")
            df = pd.DataFrame({"CUSEC_KEY": ids, "CUMUN": ["07001", "07002", "07002"]})
            fake = _FakeM04(contract, source, output, df)
            with patch("herramientas.preparar_particiones_fisicas_m04._load_m04", return_value=fake):
                with self.assertRaisesRegex(ValueError, "PHYSICAL_COMPONENT_INVENTORY_MISMATCH"):
                    prepare(params, "123", root_dir=root)

    def test_section_assigned_to_wrong_island_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ids = ["0700101001", "0700201001", "0700201002"]
            contract, source, output = _demo_contract(root, ids)
            params = root / "demo.yaml"
            params.write_text(yaml.safe_dump(contract, sort_keys=False), encoding="utf-8")
            df = pd.DataFrame({"CUSEC_KEY": ids, "CUMUN": ["07001", "07002", "07002"]})
            fake = _FakeM04(contract, source, output, df, mode="wrong_component")
            with patch("herramientas.preparar_particiones_fisicas_m04._load_m04", return_value=fake):
                with self.assertRaisesRegex(ValueError, "PHYSICAL_COMPONENT_INVENTORY_MISMATCH"):
                    prepare(params, "123", root_dir=root)


if __name__ == "__main__":
    unittest.main()
