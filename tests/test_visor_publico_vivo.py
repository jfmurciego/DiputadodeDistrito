"""Regresiones del visor público vivo: persistencia multi-territorio y UI funcional."""
from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

import yaml

from herramientas.sincronizar_visor_publico import sync_territory_from_artifact_roots


ROOT = Path(__file__).resolve().parents[1]


def write_geojson_zip(path: Path, *, electoral: bool = False) -> None:
    features = []
    for district_id in (1, 2):
        props = {
            "district_id": district_id,
            "population": 1000 + district_id,
            "target_population": 1000,
            "relative_deviation": district_id / 100,
        }
        if electoral:
            props.update({
                "winner_party": "A" if district_id == 1 else "B",
                "winner_votes": 400,
                "winner_share": 0.4,
                "total_votes": 1000,
            })
        features.append({
            "type": "Feature",
            "properties": props,
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-8.0 + district_id, 42.0],
                    [-7.9 + district_id, 42.0],
                    [-7.9 + district_id, 42.1],
                    [-8.0 + district_id, 42.0],
                ]],
            },
        })
    payload = {"type": "FeatureCollection", "features": features}
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(path.stem.replace(".geojson", "") + ".geojson", json.dumps(payload))


class LiveViewerCatalogTests(unittest.TestCase):
    def test_sync_uses_stable_paths_and_preserves_other_territories(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            declaration = root / "territorios/demo/config/elecciones/current.yaml"
            declaration.parent.mkdir(parents=True)
            declaration.write_text(yaml.safe_dump({
                "election_id": "demo_parlamento_2026",
                "election_date": "2026-02-08",
            }), encoding="utf-8")

            state = {
                "edition": "2025",
                "generated_at": "2026-09-22T10:00:00+00:00",
                "territories": [{
                    "territory_id": "demo",
                    "name": "Demo",
                    "edition": "2025",
                    "phase_evidence": {
                        "territorial_product": {
                            "run_id": 100,
                            "artifact_name": "ddd-state-100-M06",
                        },
                        "electoral_source": {
                            "election_id": "demo_parlamento_2026",
                            "declaration": "territorios/demo/config/elecciones/current.yaml",
                        },
                        "electoral_product": {
                            "run_id": 101,
                            "artifact_name": "ddd-state-101-M08",
                        },
                    },
                }],
            }
            catalog_path = root / "publicado/visor/catalogo.json"
            catalog_path.parent.mkdir(parents=True)
            catalog_path.write_text(json.dumps({
                "schema": "ddd.public-viewer-catalog/1.0",
                "territories": [{
                    "territory_id": "otro",
                    "name": "Otro",
                    "edition": "2025",
                    "products": [{"kind": "territorial", "source_path": "publicado/visor/data/otro/territorial.geojson", "districts": 1, "source_run_id": 9}],
                }],
            }), encoding="utf-8")

            m06 = root / "artifact-m06"
            m08 = root / "artifact-m08"
            write_geojson_zip(m06 / "demo_2025_m06_distritos.geojson.zip")
            write_geojson_zip(m08 / "demo_2025_m08_distritos_resultados.geojson.zip", electoral=True)

            catalog = sync_territory_from_artifact_roots(
                root=root,
                state=state,
                territory_id="demo",
                m06_root=m06,
                m08_root=m08,
                catalog_path=catalog_path,
                output_root=root / "publicado/visor/data",
            )

            self.assertEqual({row["territory_id"] for row in catalog["territories"]}, {"demo", "otro"})
            demo = next(row for row in catalog["territories"] if row["territory_id"] == "demo")
            products = {product["kind"]: product for product in demo["products"]}
            self.assertEqual(products["territorial"]["source_path"], "publicado/visor/data/demo/territorial.geojson")
            self.assertEqual(products["electoral"]["source_path"], "publicado/visor/data/demo/electoral.geojson")
            self.assertEqual(products["electoral"]["election_id"], "demo_parlamento_2026")
            self.assertEqual(products["electoral"]["election_date"], "2026-02-08")
            self.assertNotIn("100", products["territorial"]["source_path"])
            self.assertNotIn("101", products["electoral"]["source_path"])
            self.assertTrue((root / products["territorial"]["source_path"]).is_file())
            self.assertTrue((root / products["electoral"]["source_path"]).is_file())

    def test_public_ui_reads_live_json_and_hides_internal_run_language(self):
        app = (ROOT / "visor/app.js").read_text(encoding="utf-8")
        html = (ROOT / "visor/index.html").read_text(encoding="utf-8")
        self.assertIn("raw.githubusercontent.com/jfmurciego/DiputadodeDistrito/main/", app)
        self.assertIn("publicado/visor/catalogo.json", app)
        self.assertIn("orchestracion/estado_operativo.json", app)
        self.assertIn('cache:"no-store"', app)
        self.assertNotIn("technical_status", app)
        self.assertNotIn("publication_status", app)
        self.assertNotIn("run_id", app)
        self.assertIn("Territorial y censal", app)
        self.assertIn("Resultados electorales nunca intervienen", html)

    def test_existing_workflows_refresh_live_data_without_redeploy_dependency(self):
        full = (ROOT / ".github/workflows/ejecucion-completa-proyecto.yml").read_text(encoding="utf-8")
        publish = (ROOT / ".github/workflows/desplegar-visor-publico.yml").read_text(encoding="utf-8")
        reusable = (ROOT / ".github/workflows/_reutilizable-publicar-sitio.yml").read_text(encoding="utf-8")
        self.assertIn("sincronizar_visor_publico", full)
        self.assertIn("--territory-id", full)
        self.assertIn("publicado/visor", full)
        self.assertIn("sincronizar_visor_publico", publish)
        self.assertIn("--all", publish)
        self.assertIn("site/data/catalogo.json", reusable)
        self.assertIn("site/data/estado-operativo.json", reusable)


if __name__ == "__main__":
    unittest.main()
