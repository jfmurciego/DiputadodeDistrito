from __future__ import annotations

import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "herramientas/adaptador_siel_andalucia_2026.py"

PROVINCES = ("4", "11", "14", "18", "21", "23", "29", "41")
SECTIONS = 6044
GEOGRAPHIC_VOTES = 4_157_000
CERA_VOTES = 539


def load_adapter():
    spec = importlib.util.spec_from_file_location("ddd_siel_andalucia_adapter", ADAPTER)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class SielAndaluciaAdapterTests(unittest.TestCase):
    def setUp(self):
        self.adapter = load_adapter()

    def _snapshot(self, root: Path) -> Path:
        snap = root / "snapshot"
        snap.mkdir()
        sections_path = snap / "andalucia_2026_siel_secciones.csv"

        base, remainder = divmod(GEOGRAPHIC_VOTES, SECTIONS)
        province_geo = {p: 0 for p in PROVINCES}
        with sections_path.open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(
                fh,
                fieldnames=["province", "municipality", "district", "section", "party", "votes"],
            )
            w.writeheader()
            local_index = {p: 0 for p in PROVINCES}
            for i in range(SECTIONS):
                p = PROVINCES[i % len(PROVINCES)]
                j = local_index[p]
                local_index[p] += 1
                municipality = j // 100 + 1
                section = j % 100 + 1
                votes = base + (1 if i < remainder else 0)
                province_geo[p] += votes
                w.writerow({
                    "province": p,
                    "municipality": str(municipality),
                    "district": "1",
                    "section": str(section),
                    "party": "PP",
                    "votes": votes,
                })

        cera_path = snap / "andalucia_2026_siel_cera_provincias.csv"
        province_cera = {p: 0 for p in PROVINCES}
        province_cera[PROVINCES[0]] = CERA_VOTES
        with cera_path.open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["province", "party", "votes"])
            w.writeheader()
            w.writerow({"province": PROVINCES[0], "party": "PP", "votes": CERA_VOTES})

        controls = {}
        for p in PROVINCES:
            geo = province_geo[p]
            cera = province_cera[p]
            controls[p] = {
                "candidate_votes_total": geo + cera,
                "candidate_votes_cera": cera,
                "candidate_votes_geocodable_expected": geo,
                "candidate_votes_sections": geo,
                "candidate_votes_total_by_party": {"PP": geo + cera},
                "candidate_votes_cera_by_party": ({"PP": cera} if cera else {}),
                "candidate_votes_geocodable_by_party": {"PP": geo},
                "candidate_votes_sections_by_party": {"PP": geo},
                "reconciles": True,
            }

        meta = {
            "schema": "ddd-siel-andalucia-snapshot/1.0",
            "territory_id": "andalucia",
            "election_id": "andalucia_parlamento_2026",
            "election_date": "2026-05-17",
            "siel_election_key": 202605,
            "publisher": "Junta de Andalucía — Sistema de Información Electoral de Andalucía (SIEL)",
            "source_base": "https://ws040.juntadeandalucia.es/siel-api/v1",
            "candidate_votes_official": 4_157_539,
            "candidate_votes_sections": GEOGRAPHIC_VOTES,
            "candidate_votes_cera": CERA_VOTES,
            "sections": SECTIONS,
            "vote_rows": SECTIONS,
            "province_controls": controls,
            "sections_sha256": self.adapter.sha256(sections_path),
            "cera_sha256": self.adapter.sha256(cera_path),
            "official_reference": "https://www.juntadeandalucia.es/boja/2026/115/1",
            "section_locator": {
                "role": "SECTION_LOCATOR_ONLY",
                "source_class": "PROVISIONAL",
                "publisher": "Minsait / EleccionesDB mirror",
                "url": "https://pub-36ce9aa148a348ae8d9b6686b7edf0c4.r2.dev/eleccionesdb-etl/data-raw/hechos/minsait/01-andalucia.csv",
                "sha256": "13ffb00bbba4403b9e8d072e766e3979c29ac63cfb5cdcdb7b5e91348484ac21",
                "sections": SECTIONS,
                "votes_consumed": False,
            },
        }
        (snap / "manifest.json").write_text(json.dumps(meta), encoding="utf-8")
        return snap

    def test_builds_verified_package_and_excludes_cera_from_geography(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            snap = self._snapshot(root)
            out = root / "package"
            m = self.adapter.build(snap, out)
            self.assertEqual(m["schema"], "ddd-electoral-package/1.0")
            self.assertEqual(m["decision"], "ACQUIRE")
            self.assertEqual(m["edition"], "2025")
            self.assertEqual(m["source_status"], "VERIFIED_OFFICIAL_FINAL")
            self.assertEqual(m["selected_source"]["path"], "data/resultados_electorales_normalizados.csv")
            self.assertEqual(m["selected_source"]["source_class"], "official_primary")
            self.assertEqual(m["embedded_contract"]["election_contract"], "contract/election_contract.json")
            self.assertEqual(m["official_candidate_votes"], 4_157_539)
            self.assertEqual(m["geographic_candidate_votes"], GEOGRAPHIC_VOTES)
            self.assertEqual(m["cera_candidate_votes"], CERA_VOTES)
            self.assertEqual(m["sections"], SECTIONS)
            self.assertEqual(m["snapshot"]["siel_election_key"], 202605)
            self.assertEqual(
                m["snapshot"]["source_base"],
                "https://ws040.juntadeandalucia.es/siel-api/v1",
            )
            self.assertEqual(
                m["snapshot"]["official_reference"],
                "https://www.juntadeandalucia.es/boja/2026/115/1",
            )
            self.assertFalse(m["snapshot"]["section_locator"]["votes_consumed"])
            rows = list(csv.DictReader(
                (out / "data/resultados_electorales_normalizados.csv").open(encoding="utf-8"),
                delimiter=";",
            ))
            self.assertEqual(len({r["CUSEC_KEY"] for r in rows}), SECTIONS)
            contract = json.loads((out / "contract/election_contract.json").read_text(encoding="utf-8"))
            self.assertEqual(contract["source_verification"]["status"], "VERIFIED_EXACT")
            self.assertTrue(contract["source_verification"]["province_party_controls_match"])
            self.assertEqual(contract["non_geocodable_votes"]["candidate_votes"], CERA_VOTES)
            upstream = contract["sources"][0]["upstream_snapshot"]
            self.assertEqual(upstream["siel_election_key"], 202605)
            self.assertFalse(upstream["section_locator"]["votes_consumed"])

    def test_changed_snapshot_is_rejected_by_pinned_hash(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            snap = self._snapshot(root)
            with self.assertRaisesRegex(ValueError, "Huella gobernada"):
                self.adapter.build(snap, root / "package", expected_sections_sha256="0" * 64)

    def test_wrong_snapshot_identity_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            snap = self._snapshot(root)
            manifest_path = snap / "manifest.json"
            meta = json.loads(manifest_path.read_text(encoding="utf-8"))
            meta["election_id"] = "otra_eleccion"
            manifest_path.write_text(json.dumps(meta), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Identidad SIEL incorrecta election_id"):
                self.adapter.build(snap, root / "package")

    def test_locator_cannot_claim_votes_consumed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            snap = self._snapshot(root)
            manifest_path = snap / "manifest.json"
            meta = json.loads(manifest_path.read_text(encoding="utf-8"))
            meta["section_locator"]["votes_consumed"] = True
            manifest_path.write_text(json.dumps(meta), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Índice SIEL incorrecto votes_consumed"):
                self.adapter.build(snap, root / "package")

    def test_party_redistribution_with_same_total_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            snap = self._snapshot(root)
            sections_path = snap / "andalucia_2026_siel_secciones.csv"
            rows = list(csv.DictReader(sections_path.open(encoding="utf-8", newline="")))
            rows[0]["party"] = "PSOE-A"
            with sections_path.open("w", encoding="utf-8", newline="") as fh:
                writer = csv.DictWriter(
                    fh,
                    fieldnames=["province","municipality","district","section","party","votes"],
                )
                writer.writeheader()
                writer.writerows(rows)
            manifest_path = snap / "manifest.json"
            meta = json.loads(manifest_path.read_text(encoding="utf-8"))
            meta["sections_sha256"] = self.adapter.sha256(sections_path)
            manifest_path.write_text(json.dumps(meta), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "distribución geográfica por candidatura"):
                self.adapter.build(snap, root / "package")


    def test_false_province_reconciliation_flag_is_not_enough(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            snap = self._snapshot(root)
            manifest_path = snap / "manifest.json"
            meta = json.loads(manifest_path.read_text(encoding="utf-8"))
            first = PROVINCES[0]
            meta["province_controls"][first]["candidate_votes_sections"] += 1
            meta["province_controls"][first]["candidate_votes_geocodable_expected"] += 1
            meta["province_controls"][first]["candidate_votes_total"] += 1
            meta["province_controls"][first]["reconciles"] = True
            manifest_path.write_text(json.dumps(meta), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "votos geográficos"):
                self.adapter.build(snap, root / "package")


    def test_broken_global_reconciliation_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            snap = self._snapshot(root)
            cera_path = snap / "andalucia_2026_siel_cera_provincias.csv"
            rows = list(csv.DictReader(cera_path.open(encoding="utf-8", newline="")))
            rows[0]["votes"] = str(CERA_VOTES - 1)
            with cera_path.open("w", encoding="utf-8", newline="") as fh:
                writer = csv.DictWriter(fh, fieldnames=["province", "party", "votes"])
                writer.writeheader()
                writer.writerows(rows)
            manifest_path = snap / "manifest.json"
            meta = json.loads(manifest_path.read_text(encoding="utf-8"))
            meta["cera_sha256"] = self.adapter.sha256(cera_path)
            meta["candidate_votes_cera"] = CERA_VOTES - 1
            manifest_path.write_text(json.dumps(meta), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Reconciliación SIEL/BOJA"):
                self.adapter.build(snap, root / "package")


if __name__ == "__main__":
    unittest.main()
