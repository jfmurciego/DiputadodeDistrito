from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from herramientas.preparar_visor_ejecucion import build_from_publication_registry
from herramientas.registro_publicaciones_visor import (
    SCHEMA,
    make_candidate,
    sha256_file,
    validate_registry,
    verify_materialized_registry,
)

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
PUBLISHER = WORKFLOWS / "_reutilizable-publicar-sitio.yml"
ENSEMBLE = WORKFLOWS / "generar-alternativas-territoriales.yml"
FULL = WORKFLOWS / "ejecucion-completa-proyecto.yml"
REGISTRY = ROOT / "orchestracion/publicaciones_visor.json"
REPOSITORY = "jfmurciego/DiputadodeDistrito"


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


def release_product(root: Path, territory: str, run_id: str, marker: str, *, electoral: bool = False) -> dict:
    stage = "m08" if electoral else "m06"
    kind = "canonical_m08" if electoral else "canonical_m06"
    asset_type = "electoral_product" if electoral else "territorial_product"
    entry_id = f"{stage}-{territory}-{run_id}"
    asset = root / entry_id / "asset"
    write_zip(asset, geojson(marker=marker, electoral=electoral), f"{territory}_{stage}.geojson")
    digest = sha256_file(asset)
    asset_id = int(run_id) * 10 + (8 if electoral else 6)
    return {
        "id": entry_id,
        "asset_type": asset_type,
        "source_type": "release_asset",
        "immutable_location": f"github-release-asset://{REPOSITORY}/{asset_id}",
        "repository": REPOSITORY,
        "asset_id": asset_id,
        "asset_name": f"{territory}-{run_id}-{stage}.geojson.zip",
        "release_tag": f"viewer-{territory}-{run_id}-{stage}-{digest[:12]}",
        "sha256": digest,
        "kind": kind,
        "territory_id": territory,
        "territory_label": territory.title(),
        "label": f"{stage.upper()} · run {run_id}",
        "run_id": run_id,
        "expected_districts": 1,
        "technical_status": "PASS",
        "certification_status": "CERTIFIED",
        "territorial_certification_status": "CERTIFIED",
        "publication_status": "PUBLICABLE",
        "geometric_status": "PASS",
    }


def release_ensemble(root: Path, territory: str, ensemble_id: str, candidate_id: str = "candidate-01") -> dict:
    entry_id = f"ensemble-{territory}-{ensemble_id}"
    staging = root / "_staging" / entry_id / "site"
    asset = staging / "assets" / f"{candidate_id}.geojson"
    asset.parent.mkdir(parents=True, exist_ok=True)
    asset.write_text(json.dumps(geojson(marker=territory)), encoding="utf-8")
    (staging / "index.html").write_text("<!doctype html><title>gallery</title>", encoding="utf-8")
    summary = staging / "data" / "summary.json"
    summary.parent.mkdir(parents=True, exist_ok=True)
    summary.write_text(json.dumps({
        "territory_id": territory,
        "territory_label": territory.title(),
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

    archive = root / entry_id / "asset"
    archive.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted((staging.parent).rglob("*")):
            if path.is_file():
                bundle.write(path, path.relative_to(staging.parent))
    digest = sha256_file(archive)
    asset_id = abs(hash((territory, ensemble_id))) % 1000000 + 1000
    return {
        "id": entry_id,
        "asset_type": "ensemble_archive",
        "source_type": "release_asset",
        "immutable_location": f"github-release-asset://{REPOSITORY}/{asset_id}",
        "repository": REPOSITORY,
        "asset_id": asset_id,
        "asset_name": f"{ensemble_id}.zip",
        "release_tag": ensemble_id,
        "sha256": digest,
        "kind": "ensemble",
        "territory_id": territory,
        "territory_label": territory.title(),
        "ensemble_id": ensemble_id,
        "candidate_count_expected": 1,
        "candidate_count_valid": 1,
        "publication_status": "PUBLICABLE",
    }


class MultiterritoryPublicationTests(unittest.TestCase):
    def test_workflow_artifact_can_never_be_definitive_registry_source(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            entry = release_product(root, "aragon", "101", "A")
            entry["source_type"] = "workflow_artifact"
            registry = {"schema": SCHEMA, "products": [entry], "ensembles": []}
            with self.assertRaisesRegex(ValueError, "workflow_artifact"):
                validate_registry(registry)

    def test_incorrect_hash_blocks_before_registry_change_and_keeps_previous_registry(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            materialized = root / "assets"
            good = release_product(materialized, "aragon", "101", "A")
            base = {"schema": SCHEMA, "products": [good], "ensembles": []}
            registry_path = root / "publicaciones_visor.json"
            registry_path.write_text(json.dumps(base, sort_keys=True), encoding="utf-8")
            before = registry_path.read_bytes()

            candidate_entry = release_product(materialized, "galicia", "202", "B")
            candidate_entry["sha256"] = "0" * 64
            candidate = make_candidate(base, [candidate_entry])
            with self.assertRaisesRegex(ValueError, "SHA-256 no coincide"):
                verify_materialized_registry(candidate, materialized)

            self.assertEqual(registry_path.read_bytes(), before)

    def test_missing_persistent_asset_blocks_before_registry_change(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            materialized = root / "assets"
            existing = release_product(materialized, "aragon", "101", "A")
            base = {"schema": SCHEMA, "products": [existing], "ensembles": []}
            registry_path = root / "publicaciones_visor.json"
            registry_path.write_text(json.dumps(base, sort_keys=True), encoding="utf-8")
            before = registry_path.read_bytes()

            missing = dict(existing)
            missing.update({
                "id": "m06-galicia-202",
                "territory_id": "galicia",
                "territory_label": "Galicia",
                "run_id": "202",
                "asset_id": 2026,
                "asset_name": "galicia-202-m06.geojson.zip",
                "release_tag": "viewer-galicia-202-m06-deadbeefdead",
                "immutable_location": f"github-release-asset://{REPOSITORY}/2026",
            })
            candidate = make_candidate(base, [missing])
            with self.assertRaises(FileNotFoundError):
                verify_materialized_registry(candidate, materialized)

            self.assertEqual(registry_path.read_bytes(), before)

    def test_two_persistent_products_reconstruct_together_without_fake_electoral_fields(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            materialized = root / "materialized"
            site = root / "site"
            a = release_product(materialized, "aragon", "101", "A")
            b = release_product(materialized, "galicia", "202", "B")
            registry = {"schema": SCHEMA, "products": [a, b], "ensembles": []}
            verify_materialized_registry(registry, materialized)
            registry_path = root / "registry.json"
            registry_path.write_text(json.dumps(registry), encoding="utf-8")

            results = build_from_publication_registry(registry_path, ROOT, materialized, site)

            self.assertEqual({row["territory_id"] for row in results}, {"aragon", "galicia"})
            a_path = site / "data/results/aragon/101/m06.geojson"
            b_path = site / "data/results/galicia/202/m06.geojson"
            self.assertTrue(a_path.is_file())
            self.assertTrue(b_path.is_file())
            props = json.loads(a_path.read_text(encoding="utf-8"))["features"][0]["properties"]
            self.assertNotIn("winner_party", props)
            self.assertNotIn("winner_votes", props)

    def test_republishing_same_identity_replaces_only_that_entry(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            assets = root / "assets"
            a = release_product(assets, "aragon", "101", "A")
            b = release_product(assets, "galicia", "202", "B")
            base = {"schema": SCHEMA, "products": [a, b], "ensembles": []}
            replacement = dict(a, label="A republicado")
            candidate = make_candidate(base, [replacement])
            self.assertEqual(len(candidate["products"]), 2)
            self.assertEqual(next(row for row in candidate["products"] if row["territory_id"] == "galicia"), b)
            self.assertEqual(next(row for row in candidate["products"] if row["territory_id"] == "aragon")["label"], "A republicado")

    def test_duplicate_publication_identity_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            entry = release_product(root, "aragon", "101", "A")
            duplicate = dict(entry, id="otro-id", asset_id=99999,
                             immutable_location=f"github-release-asset://{REPOSITORY}/99999")
            registry = {"schema": SCHEMA, "products": [entry, duplicate], "ensembles": []}
            with self.assertRaisesRegex(ValueError, "Identidad de publicación duplicada"):
                validate_registry(registry)

    def test_same_candidate_id_in_different_territories_does_not_collide(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            materialized = root / "materialized"
            site = root / "site"
            p = release_product(materialized, "aragon", "101", "A")
            e1 = release_ensemble(materialized, "aragon", "ensemble-one", candidate_id="shared")
            e2 = release_ensemble(materialized, "galicia", "ensemble-two", candidate_id="shared")
            registry = {"schema": SCHEMA, "products": [p], "ensembles": [e1, e2]}
            verify_materialized_registry(registry, materialized)
            registry_path = root / "registry.json"
            registry_path.write_text(json.dumps(registry), encoding="utf-8")

            results = build_from_publication_registry(registry_path, ROOT, materialized, site)

            first = site / "data/ensemble/aragon/ensemble-one/shared.geojson"
            second = site / "data/ensemble/galicia/ensemble-two/shared.geojson"
            self.assertTrue(first.is_file())
            self.assertTrue(second.is_file())
            self.assertTrue((site / "galleries/aragon/ensemble-one/index.html").is_file())
            self.assertTrue((site / "galleries/galicia/ensemble-two/index.html").is_file())
            self.assertIn("canonical_m06", {row["kind"] for row in results})
            self.assertEqual(sum(row["kind"] == "ensemble_candidate" for row in results), 2)

    def test_pages_has_exactly_one_deployer_and_one_global_mutex(self):
        active = sorted(WORKFLOWS.glob("*.yml"))
        deployers = []
        for path in active:
            text = path.read_text(encoding="utf-8")
            if "actions/deploy-pages@" in text:
                deployers.append(path.name)
        self.assertEqual(deployers, ["_reutilizable-publicar-sitio.yml"])
        publisher = PUBLISHER.read_text(encoding="utf-8")
        ensemble = ENSEMBLE.read_text(encoding="utf-8")
        self.assertEqual(publisher.count("actions/deploy-pages@"), 1)
        self.assertIn("group: ddd-pages-prod", publisher)
        self.assertNotIn("actions/upload-pages-artifact@", ensemble)
        self.assertIn("uses: ./.github/workflows/_reutilizable-publicar-sitio.yml", ensemble)

    def test_registry_pins_aragon_and_castilla_y_leon_by_blob_and_sha256(self):
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        validate_registry(registry)
        products = {row["id"]: row for row in registry["products"]}
        expected = {
            "static-aragon": "902f3b5d79f1cda8bf90c84589612342e393aa9561c572fa8ea8ef2fc9851512",
            "static-castilla_y_leon": "493f0d9c09ed2c41562469cb7ad8490667166c3a9d02745ce73fbcb865bccc2f",
        }
        for key, digest in expected.items():
            row = products[key]
            self.assertEqual(row["source_type"], "repository_blob")
            self.assertEqual(row["sha256"], digest)
            self.assertRegex(row["blob_sha"], r"^[0-9a-f]{40}$")
            path = ROOT / row["source_path"]
            self.assertTrue(path.is_file())
            observed = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(observed, digest)

    def test_full_orchestrator_can_publish_certified_m06_without_electoral_gate(self):
        workflow = FULL.read_text(encoding="utf-8")
        self.assertIn("needs: [planificar, puerta_02, puerta_04, actualizar_estado]", workflow)
        self.assertIn("needs.puerta_02.result == 'success'", workflow)
        self.assertIn("needs.actualizar_estado.result == 'success'", workflow)
        self.assertIn("needs.puerta_04.result == 'success' && needs.puerta_04.outputs.run_id || needs.puerta_02.outputs.run_id", workflow)

    def test_valid_geojson_with_wrong_district_count_blocks_candidate_and_preserves_registry_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            materialized = root / "materialized"
            site = root / "site-candidate"
            existing = release_product(materialized, "aragon", "101", "A")
            base = {"schema": SCHEMA, "products": [existing], "ensembles": []}
            registry_path = root / "publicaciones_visor.json"
            registry_path.write_bytes((json.dumps(base, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
            before = registry_path.read_bytes()

            mismatched = release_product(materialized, "galicia", "202", "B")
            mismatched["expected_districts"] = 2
            candidate = make_candidate(base, [mismatched])
            candidate_path = root / "publicaciones_visor.candidate.json"
            candidate_path.write_text(
                json.dumps(candidate, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            # El activo existe, su SHA es correcto y el GeoJSON es sintácticamente válido.
            verify_materialized_registry(candidate, materialized)
            self.assertEqual(
                json.loads(
                    zipfile.ZipFile(materialized / mismatched["id"] / "asset")
                    .read("galicia_m06.geojson")
                    .decode("utf-8")
                )["type"],
                "FeatureCollection",
            )

            commit_marker = root / "registry-committed"
            deploy_marker = root / "pages-deployed"
            with self.assertRaisesRegex(ValueError, "distritos observados 1 != 2"):
                build_from_publication_registry(candidate_path, ROOT, materialized, site)
                commit_marker.touch()
                deploy_marker.touch()

            self.assertEqual(registry_path.read_bytes(), before)
            self.assertFalse(commit_marker.exists())
            self.assertFalse(deploy_marker.exists())

    def test_publisher_order_is_preflight_build_validation_pages_deploy_then_persist(self):
        text = PUBLISHER.read_text(encoding="utf-8")
        preflight = text.index("Preflight completo del registro candidato")
        build = text.index("Construir sitio candidato completo")
        validate = text.index("Validar sitio candidato completo")
        pages_preflight = text.index("Verificar Pages habilitado para GitHub Actions")
        configure = text.index("actions/configure-pages@")
        upload = text.index("actions/upload-pages-artifact@")
        deploy = text.index("actions/deploy-pages@")
        persist = text.index("Persistir registro sólo después del despliegue")
        self.assertLess(preflight, build)
        self.assertLess(build, validate)
        self.assertLess(validate, pages_preflight)
        self.assertLess(pages_preflight, configure)
        self.assertLess(configure, upload)
        self.assertLess(upload, deploy)
        self.assertLess(deploy, persist)
        self.assertIn("with: {path: /tmp/site-candidate}", text)
        self.assertEqual(text.count("--site /tmp/site-candidate"), 1)
        self.assertNotIn("--site site ", text)

    def test_publisher_preflights_pages_and_never_self_enables_with_github_token(self):
        text = PUBLISHER.read_text(encoding="utf-8")
        current = text.index("Preflight completo del registro vigente")
        candidate = text.index("Preflight completo del registro candidato")
        pages = text.index("Verificar Pages habilitado para GitHub Actions")
        deploy = text.index("actions/deploy-pages@")
        persist = text.index("Persistir registro sólo después del despliegue")
        self.assertLess(current, candidate)
        self.assertLess(candidate, pages)
        self.assertLess(pages, deploy)
        self.assertLess(deploy, persist)
        self.assertIn('gh api "repos/$GITHUB_REPOSITORY/pages"', text)
        self.assertIn('build_type="$(jq -r', text)
        self.assertNotIn("enablement: true", text)
        self.assertIn("el GITHUB_TOKEN no puede crear el sitio", text)
        self.assertIn('steps.deployment.outcome', text)
        self.assertIn("release_asset", text)
        self.assertIn("repos/$GITHUB_REPOSITORY/releases/assets/$asset_id", text)

    def test_publication_workflow_and_job_names_remain_stable(self):
        wrapper = (WORKFLOWS / "desplegar-visor-publico.yml").read_text(encoding="utf-8")
        publisher = PUBLISHER.read_text(encoding="utf-8")
        self.assertIn("name: 05 · Publicación del Visor", wrapper)
        self.assertIn("name: Preparar promoción web", wrapper)
        self.assertIn("name: Desplegar página seleccionada", wrapper)
        self.assertIn("name: _Publicador Interno del Sitio", publisher)


if __name__ == "__main__":
    unittest.main()
