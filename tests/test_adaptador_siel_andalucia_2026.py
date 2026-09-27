from __future__ import annotations

import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "herramientas/adaptador_siel_andalucia_2026.py"


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
        sections = snap / "andalucia_2026_siel_secciones.csv"
        with sections.open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["province","municipality","district","section","party","votes"])
            w.writeheader()
            w.writerow({"province":"4","municipality":"29","district":"1","section":"6","party":"PP","votes":4_000_000})
            w.writerow({"province":"4","municipality":"29","district":"1","section":"6","party":"PSOE-A","votes":157_000})
        cera = snap / "andalucia_2026_siel_cera_provincias.csv"
        with cera.open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["province","party","votes"])
            w.writeheader()
            w.writerow({"province":"4","party":"PP","votes":300})
            w.writerow({"province":"4","party":"PSOE-A","votes":239})
        controls = {}
        for p in ("4","11","14","18","21","23","29","41"):
            controls[p] = {
                "candidate_votes_total": 0,
                "candidate_votes_cera": 0,
                "candidate_votes_geocodable_expected": 0,
                "candidate_votes_sections": 0,
                "reconciles": True,
            }
        controls["4"].update(
            candidate_votes_total=4_157_539,
            candidate_votes_cera=539,
            candidate_votes_geocodable_expected=4_157_000,
            candidate_votes_sections=4_157_000,
        )
        meta = {
            "schema":"ddd-siel-andalucia-snapshot/1.0",
            "territory_id":"andalucia",
            "election_id":"andalucia_parlamento_2026",
            "election_date":"2026-05-17",
            "siel_election_key":202605,
            "source_base":"https://ws040.juntadeandalucia.es/siel-api/v1",
            "candidate_votes_official":4_157_539,
            "candidate_votes_sections":4_157_000,
            "candidate_votes_cera":539,
            "sections":6044,
            "vote_rows":2,
            "province_controls":controls,
            "sections_sha256":self.adapter.sha256(sections),
            "cera_sha256":self.adapter.sha256(cera),
            "official_reference":"https://www.juntadeandalucia.es/boja/2026/115/1",
            "section_locator":{
                "role":"SECTION_LOCATOR_ONLY",
                "source_class":"PROVISIONAL",
                "publisher":"Minsait / EleccionesDB mirror",
                "url":"https://pub-36ce9aa148a348ae8d9b6686b7edf0c4.r2.dev/eleccionesdb-etl/data-raw/hechos/minsait/01-andalucia.csv",
                "sha256":"13ffb00bbba4403b9e8d072e766e3979c29ac63cfb5cdcdb7b5e91348484ac21",
                "sections":6044,
                "votes_consumed":False,
            },
        }
        (snap / "manifest.json").write_text(json.dumps(meta), encoding="utf-8")
        return snap

    def test_builds_verified_package_and_excludes_cera_from_geography(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            snap = self._snapshot(root)
            out = root / "package"
            with self.assertRaisesRegex(ValueError, "Secciones SIEL"):
                self.adapter.build(snap, out)
            meta_path = snap / "manifest.json"
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            meta["sections"] = 1
            meta_path.write_text(json.dumps(meta), encoding="utf-8")
            m = self.adapter.build(snap, out)
            self.assertEqual(m["schema"], "ddd-electoral-package/1.0")
            self.assertEqual(m["decision"], "ACQUIRE")
            self.assertEqual(m["edition"], "2025")
            self.assertEqual(m["source_status"], "VERIFIED_OFFICIAL_FINAL")
            self.assertEqual(m["selected_source"]["path"], "data/resultados_electorales_normalizados.csv")
            self.assertEqual(m["selected_source"]["source_class"], "official_primary")
            self.assertEqual(m["embedded_contract"]["election_contract"], "contract/election_contract.json")
            self.assertEqual(m["official_candidate_votes"], 4_157_539)
            self.assertEqual(m["geographic_candidate_votes"], 4_157_000)
            self.assertEqual(m["cera_candidate_votes"], 539)
            rows = list(csv.DictReader((out / "data/resultados_electorales_normalizados.csv").open(encoding="utf-8"), delimiter=";"))
            self.assertEqual({r["CUSEC_KEY"] for r in rows}, {"0402901006"})
            contract = json.loads((out / "contract/election_contract.json").read_text(encoding="utf-8"))
            self.assertEqual(contract["source_verification"]["status"], "VERIFIED_EXACT")
            self.assertEqual(contract["non_geocodable_votes"]["candidate_votes"], 539)

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

    def test_broken_global_reconciliation_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            snap = self._snapshot(root)
            cera_path = snap / "andalucia_2026_siel_cera_provincias.csv"
            rows = list(csv.DictReader(cera_path.open(encoding="utf-8", newline="")))
            rows[0]["votes"] = "299"
            with cera_path.open("w", encoding="utf-8", newline="") as fh:
                writer = csv.DictWriter(fh, fieldnames=["province","party","votes"])
                writer.writeheader()
                writer.writerows(rows)
            manifest_path = snap / "manifest.json"
            meta = json.loads(manifest_path.read_text(encoding="utf-8"))
            meta["cera_sha256"] = self.adapter.sha256(cera_path)
            meta["candidate_votes_cera"] = 538
            manifest_path.write_text(json.dumps(meta), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Reconciliación SIEL/BOJA"):
                self.adapter.build(snap, root / "package")


if __name__ == "__main__":
    unittest.main()
