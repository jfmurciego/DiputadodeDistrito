from __future__ import annotations

import csv
import io
import json
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

import yaml

from herramientas.materializar_contrato_generacion import (
    component_hamilton,
    hamilton,
    materialize,
)

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "configuracion/politica_generacion_territorial_2025.yaml"
MASTER = ROOT / "configuracion/catalogo_territorios_espana_2025.yaml"
PARTITIONS = ROOT / "configuracion/particiones_insulares_2025.json"


def population_package(root: Path, rows: list[tuple[str, int]]) -> Path:
    package = root / "package"
    package.mkdir(parents=True)
    payload = io.StringIO()
    writer = csv.writer(payload, delimiter="\t", lineterminator="\n")
    writer.writerow(["Total Nacional","Provincias","Municipios","Secciones","Sexo","Edad","Periodo","Total"])
    for section, population in rows:
        writer.writerow([
            "Total Nacional", section[:2], section[:5], section,
            "Total", "Todas las edades", "2025", f"{population:,}".replace(",", "."),
        ])
    zpath = package / "65034.csv.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("65034.csv", payload.getvalue().encode("utf-8-sig"))
    return package


def temp_root(territory_id: str, name: str, provinces: list[str]) -> tempfile.TemporaryDirectory:
    td = tempfile.TemporaryDirectory()
    root = Path(td.name)
    (root / "configuracion").mkdir(parents=True)
    (root / "inputs").mkdir(parents=True)
    shutil.copy2(POLICY, root / "configuracion/politica_generacion_territorial_2025.yaml")
    shutil.copy2(PARTITIONS, root / "configuracion/particiones_insulares_2025.json")
    (root / "configuracion/catalogo_territorios_espana_2025.yaml").write_text(
        "territories:\n"
        f"  - {{territory_id: {territory_id}, name: {name}, province_codes: {provinces!r}, batch: test, status: bootstrap, contract_level: bootstrap_m01_m03}}\n",
        encoding="utf-8",
    )
    (root / "inputs/MANIFEST.sha256").write_text(
        "0"*64 + "  inputs/seccionado_2025.zip\n" +
        "1"*64 + "  inputs/65034.csv.zip\n",
        encoding="utf-8",
    )
    return td


class NationalGenerationMaterializationTests(unittest.TestCase):
    def test_policy_covers_exactly_the_national_registry(self):
        policy = yaml.safe_load(POLICY.read_text(encoding="utf-8"))
        master = yaml.safe_load(MASTER.read_text(encoding="utf-8"))
        self.assertEqual(
            set(policy["territories"]),
            {row["territory_id"] for row in master["territories"]},
        )
        self.assertTrue(all(int(v["k"]) > 0 for v in policy["territories"].values()))

    def test_archipelago_registry_is_explicit_and_has_no_marine_edges(self):
        data = json.loads(PARTITIONS.read_text(encoding="utf-8"))
        self.assertEqual(set(data["territories"]), {"illes_balears", "canarias"})
        self.assertEqual(len(data["territories"]["illes_balears"]["components"]), 4)
        self.assertEqual(len(data["territories"]["canarias"]["components"]), 8)
        self.assertEqual(
            data["territories"]["canarias"]["section_overrides"]["3502401010"],
            "35-C04",
        )

    def test_hamilton_conserves_k(self):
        self.assertEqual(hamilton({"22":230087,"44":136091,"50":998443},67), {"22":11,"44":7,"50":49})

    def test_component_hamilton_keeps_one_small_component_and_declares_exception(self):
        quota, exempt = component_hamilton(
            {"A":971068,"B":102821,"C":11690,"D":164265}, 59, 0.80
        )
        self.assertEqual(sum(quota.values()), 59)
        self.assertEqual(quota["C"], 1)
        self.assertEqual(exempt, ["C"])

    def test_materializes_asturias_without_manual_contract_work(self):
        td = temp_root("principado_de_asturias", "Principado de Asturias", ["33"])
        try:
            root = Path(td.name)
            package = population_package(root, [("3300101001", 1_015_128)])
            result = materialize(root, "principado_de_asturias", "2025", package)
            self.assertEqual(result["status"], "READY")
            self.assertEqual(result["k"], 45)
            cfg = yaml.safe_load((root / result["contract_path"]).read_text(encoding="utf-8"))
            self.assertEqual(cfg["meta"]["contract_level"], "production_m01_m06")
            self.assertEqual(cfg["meta"]["production_authorization"], "AUTHORIZED")
            self.assertEqual(cfg["validation"]["province_districts"], {"33":45})
            self.assertTrue(all(
                key in cfg["modulos"] for key in (
                    "modulo_01_preparar_base_territorial","modulo_02_construir_adyacencias",
                    "modulo_03_construir_grafo","modulo_04_generar_semillas",
                    "modulo_05_optimizar_distritos","modulo_06_consolidar_distritos",
                )
            ))
        finally:
            td.cleanup()

    def test_materializes_balearic_archipelago_with_explicit_partition_exception(self):
        td = temp_root("illes_balears", "Islas Baleares", ["07"])
        try:
            root = Path(td.name)
            package = population_package(root, [
                ("0700101001", 971068),
                ("0700201001", 102821),
                ("0702401001", 11690),
                ("0702601001", 164265),
            ])
            result = materialize(root, "illes_balears", "2025", package)
            self.assertEqual(result["status"], "READY")
            self.assertEqual(result["partition_mode"], "physical_components_hamilton")
            self.assertEqual(sum(result["partition_districts"].values()), 59)
            self.assertIn("07-C03", result["population_floor_exempt_partitions"])
            cfg = yaml.safe_load((root / result["contract_path"]).read_text(encoding="utf-8"))
            self.assertEqual(cfg["modulos"]["modulo_04_generar_semillas"]["province_field"], "DDD_PARTITION")
            self.assertEqual(cfg["validation"]["hard_partition_mode"], "physical_components")
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
