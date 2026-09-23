from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from herramientas.preparar_visor_ejecucion import build_from_publication_registry
from herramientas.registro_publicaciones_visor import SCHEMA, upsert

ROOT = Path(__file__).resolve().parents[1]
PUBLISHER = ROOT / ".github/workflows/_reutilizable-publicar-sitio.yml"
ENSEMBLE = ROOT / ".github/workflows/generar-alternativas-territoriales.yml"
FULL = ROOT / ".github/workflows/ejecucion-completa-proyecto.yml"
REGISTRY = ROOT / "orchestracion/publicaciones_visor.json"


def geojson(*, marker: str, electoral: bool = False) -> dict:
    properties = {"district_id": "1", "population": 1000, "marker": marker}
    if electoral:
        properties.update({"winner_party": "X", "winner_votes": 10})
    return {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "properties": properties,
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[-3.0, 40.0], [-2.9, 40.0], [-2.9, 40.1], [-3.0, 40.0]]],
            },
        }],
    }


def write_zip(path: Path, payload: dict, member: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(member, json.dumps(payload))


def product(territory: str, run_id: str) -> dict:
    return {
        "id": f"m06-{territory}-{run_id}",
        "source_type": "workflow_artifact",
        "kind": "canonical_m06",
        "territory_id": territory,
        "territory_label": territory.title(),
        "label": f"M06 territorial · run {run_id}",
        "run_id": run_id,
        "artifact_name": f"ddd-state-{run_id}-M06",
        "expected_districts": 1,
        "technical_status": "PASS",
        "certification_status": "CERTIFIED",
        "territorial_certification_status": "CERTIFIED",
        "publication_status": "PUBLICABLE",
        "geometric_status": "PASS",
    }


def ensemble_entry(territory: str, ensemble_id: str) -> dict:
    return {
        "id": f"ensemble-{territory}-{ensemble_id}",
        "source_type": "release",
        "kind": "ensemble",
        "territory_id": territory,
        "territory_label": territory.title(),
        "ensemble_id": ensemble_id,
        "release_tag": ensemble_id,
        "candidate_count_expected": 1,
        "candidate_count_valid": 1,
        "publication_status": "PUBLICABLE",
    }


def materialize_product(root: Path, entry: dict, marker: str) -> None:
    target = root / entry["id"] / f"{entry['territory_id']}_2025_m06_distritos.geojson.zip"
    write_zip(target, geojson(marker=marker), f"{entry['territory_id']}_m06.geojson")


def materialize_ensemble(root: Path, entry: dict, candidate_id: str = "candidate-01") -> None:
    base = root / entry["id"] / "site"
    asset = base / "assets" / f"{candidate_id}.geojson"
    asset.parent.mkdir(parents=True, exist_ok=True)
    asset.write_text(json.dumps(geojson(marker=entry["territory_id"])), encoding="utf-8")
    summary = base / "data" / "summary.json"
    summary.parent.mkdir(parents=True, exist_ok=True)
    summary.write_text(json.dumps({
        "territory_id": entry["territory_id"],
        "territory_label": entry["territory_label"],
        "complete": True,
        "candidate_count_expected": 1,
        "candidate_count_valid": 1,
        "candidates": [{
            "candidate_id": candidate_id,
            "profile": "balanced",
            "seed": 1,
            "asset": f"assets/{candidate_id}.geojson",
            "metrics": {"population": {"district_count": 1}},
        }],
    }), encoding="utf-8")


class MultiterritoryPublicationTests(unittest.TestCase):
    def test_publish_a_then_b_and_republish_a_preserve_b(self):
        registry = {"schema": SCHEMA, "products": [], "ensembles": []}
        a = product("territorio_a", "101")
        b = product("territorio_b", "202")
        self.assertTrue(upsert(registry["products"], a))
        self.assertTrue(upsert(registry["products"], b))
        self.assertEqual({row["id"] for row in registry["products"]}, {a["id"], b["id"]})

        updated_a = dict(a, label="A republicado")
        self.assertTrue(upsert(registry["products"], updated_a))
        self.assertEqual(len(registry["products"]), 2)
        self.assertEqual(next(row for row in registry["products"] if row["id"] == b["id"]), b)

    def test_complete_registry_materializes_both_territories_and_m06_has_no_fake_electoral_fields(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            materialized = root / "materialized"
            site = root / "site"
            a = product("territorio_a", "101")
            b = product("territorio_b", "202")
            registry = {"schema": SCHEMA, "products": [a, b], "ensembles": []}
            registry_path = root / "registry.json"
            registry_path.write_text(json.dumps(registry), encoding="utf-8")
            materialize_product(materialized, a, "A")
            materialize_product(materialized, b, "B")

            results = build_from_publication_registry(registry_path, ROOT, materialized, site)

            self.assertEqual({row["territory_id"] for row in results}, {"territorio_a", "territorio_b"})
            a_path = site / "data/results/territorio_a/101/m06.geojson"
            b_path = site / "data/results/territorio_b/202/m06.geojson"
            self.assertTrue(a_path.is_file())
            self.assertTrue(b_path.is_file())
            props = json.loads(a_path.read_text(encoding="utf-8"))["features"][0]["properties"]
            self.assertNotIn("winner_party", props)
            self.assertNotIn("winner_votes", props)
            self.assertEqual(next(row for row in results if row["territory_id"] == "territorio_a")["kind"], "canonical_m06")

    def test_same_candidate_id_in_different_territories_does_not_collide_and_gallery_keeps_general_viewer(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            materialized = root / "materialized"
            site = root / "site"
            p = product("territorio_a", "101")
            e1 = ensemble_entry("territorio_a", "ensemble-one")
            e2 = ensemble_entry("territorio_b", "ensemble-two")
            registry = {"schema": SCHEMA, "products": [p], "ensembles": [e1, e2]}
            registry_path = root / "registry.json"
            registry_path.write_text(json.dumps(registry), encoding="utf-8")
            materialize_product(materialized, p, "A")
            materialize_ensemble(materialized, e1, candidate_id="shared")
            materialize_ensemble(materialized, e2, candidate_id="shared")

            results = build_from_publication_registry(registry_path, ROOT, materialized, site)

            first = site / "data/ensemble/territorio_a/ensemble-one/shared.geojson"
            second = site / "data/ensemble/territorio_b/ensemble-two/shared.geojson"
            self.assertTrue(first.is_file())
            self.assertTrue(second.is_file())
            self.assertNotEqual(first, second)
            self.assertTrue((site / "galleries/territorio_a/ensemble-one/index.html").is_file())
            self.assertTrue((site / "galleries/territorio_b/ensemble-two/index.html").is_file())
            self.assertIn("canonical_m06", {row["kind"] for row in results})
            self.assertEqual(sum(row["kind"] == "ensemble_candidate" for row in results), 2)

    def test_pages_has_one_deployer_and_one_global_mutex(self):
        publisher = PUBLISHER.read_text(encoding="utf-8")
        ensemble = ENSEMBLE.read_text(encoding="utf-8")
        self.assertIn("group: ddd-pages-prod", publisher)
        self.assertIn("actions/deploy-pages@d6db90164ac5ed86f2b6aed7e0febac5b3c0c03e", publisher)
        self.assertNotIn("actions/deploy-pages@d6db90164ac5ed86f2b6aed7e0febac5b3c0c03e", ensemble)
        self.assertNotIn("actions/upload-pages-artifact@7b1f4a764d45c48632c6b24a0339c27f5614fb0b", ensemble)
        self.assertIn("uses: ./.github/workflows/_reutilizable-publicar-sitio.yml", ensemble)

    def test_existing_aragon_and_castilla_y_leon_are_preserved(self):
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        products = {row["id"]: row for row in registry["products"]}
        self.assertIn("static-aragon", products)
        self.assertIn("static-castilla_y_leon", products)
        for key in ("static-aragon", "static-castilla_y_leon"):
            self.assertTrue((ROOT / products[key]["source_path"]).is_file())

    def test_full_orchestrator_can_publish_certified_m06_without_electoral_gate(self):
        workflow = FULL.read_text(encoding="utf-8")
        self.assertIn("needs: [planificar, puerta_02, puerta_04]", workflow)
        self.assertIn("needs.puerta_02.result == 'success'", workflow)
        self.assertIn("needs.puerta_04.result == 'success' && needs.puerta_04.outputs.run_id || needs.puerta_02.outputs.run_id", workflow)


if __name__ == "__main__":
    unittest.main()
