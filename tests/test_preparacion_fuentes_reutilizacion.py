from __future__ import annotations

import hashlib
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

import geopandas as gpd
import yaml
from pyproj import CRS
from shapely.geometry import box

from herramientas.compatibilidad_poblacion_seccionado import REPORT_NAME, SCHEMA
from herramientas.seleccionar_paquete_fuentes import select_first_valid, validate_prepared_package

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/preparacion-fuentes.yml"
ELECTORAL_WORKFLOW = ROOT / ".github/workflows/preparacion-resultados-electorales.yml"


def _section_zip(*, crs: str = "EPSG:4326") -> bytes:
    with tempfile.TemporaryDirectory(prefix="ddd_test_sections_") as td:
        root = Path(td)
        shp = root / "seccionado.shp"
        gdf = gpd.GeoDataFrame(
            {"CUSEC": ["0100101001"]},
            geometry=[box(-3.8, 40.3, -3.7, 40.4)],
            crs=crs,
        )
        gdf.to_file(shp, driver="ESRI Shapefile", index=False)
        out = io.BytesIO()
        with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(root.glob("seccionado.*")):
                archive.writestr(path.name, path.read_bytes())
        return out.getvalue()


def _canonical_report_identity(report: dict) -> str:
    canonical = {
        key: value
        for key, value in report.items()
        if key not in {"schema", "compatibility_identity_sha256", "decision"}
    }
    return hashlib.sha256(
        json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def build_package(
    root: Path,
    *,
    territory="la_rioja",
    edition=2025,
    source_year=None,
    population_year=None,
    section_year=None,
    corrupt=False,
    include_compatibility=True,
) -> Path:
    package = root
    package.mkdir(parents=True, exist_ok=True)
    source_year = edition if source_year is None else source_year
    population_year = source_year if population_year is None else population_year
    section_year = source_year if section_year is None else section_year

    target_sectioning = _section_zip(crs="EPSG:4326")
    origin_sectioning = _section_zip(crs="EPSG:4326")
    payloads = {
        "population": ("inputs/population.zip", b"official-population-bytes", population_year, "population"),
        "target_sectioning": ("inputs/sections.zip", target_sectioning, section_year, "sections"),
    }
    if population_year != section_year:
        payloads["population_sectioning_origin"] = (
            "inputs/sections-origin.zip",
            origin_sectioning,
            population_year,
            "sections_origin",
        )

    inventory_sources = []
    for role, (path, payload, year, source_id) in payloads.items():
        inventory_sources.append({
            "source_id": source_id,
            "role": role,
            "path": path,
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "edition": year,
        })

    docs = {
        "declaracion_materializacion.json": {
            "territory_id": territory,
            "territory": "La Rioja",
            "edition": edition,
            "population_year": population_year,
            "section_year": section_year,
            "sources": [{"source_id": row["source_id"], "role": row["role"]} for row in inventory_sources],
        },
        "inventario_fuentes.json": {
            "territory_id": territory,
            "territory": "La Rioja",
            "edition": edition,
            "population_year": population_year,
            "section_year": section_year,
            "sources": inventory_sources,
        },
        "manifiesto_procedencia.json": {
            "territory_id": territory,
            "territory": "La Rioja",
            "edition": edition,
            "population_year": population_year,
            "section_year": section_year,
            "sources": [{"source_id": row["source_id"], "role": row["role"]} for row in inventory_sources],
        },
        "decision_adquisicion.json": {
            "territory_id": territory,
            "territory": "La Rioja",
            "edition": edition,
            "population_year": population_year,
            "section_year": section_year,
            "decision": "READY",
        },
    }

    inputs = {}
    for role, (path, payload, _year, source_id) in payloads.items():
        inputs[role] = {
            "role": role,
            "source_id": source_id,
            "path": path,
            "member": "materialized/" + path,
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
        }

    crs_wkt = CRS.from_epsg(4326).to_wkt()
    compatibility = {
        "schema": SCHEMA,
        "territory_id": territory,
        "edition": str(edition),
        "population_year": population_year,
        "section_year": section_year,
        "inputs": inputs,
        "crs": {
            "target": {"original": "EPSG:4326", "original_wkt": crs_wkt},
            "origin": (
                {"original": "EPSG:4326", "original_wkt": crs_wkt}
                if population_year != section_year
                else None
            ),
            "effective": {
                "crs": "EPSG:4326",
                "wkt": crs_wkt,
                "policy": "target_sectioning_crs",
                "origin_reprojected": False,
            },
        },
        "correspondences": [],
        "geometric_changes": [],
        "duplicates": {"population": [], "target_geometry": [], "origin_geometry": []},
        "population_without_geometry": [],
        "geometry_without_population": [],
        "population_without_destination": [],
        "population": {"input_total": 1, "assigned_total": 1, "exact_conservation": True},
        "causes": [],
        "decision": "READY",
    }
    compatibility["compatibility_identity_sha256"] = _canonical_report_identity(compatibility)

    bundle = package / "prepared_sources.zip"
    with zipfile.ZipFile(bundle, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, data in docs.items():
            zf.writestr(name, json.dumps(data))
        for role, (path, payload, _year, _source_id) in payloads.items():
            if corrupt and role == "population":
                payload = payload + b"corrupt"
            zf.writestr("materialized/" + path, payload)
        if include_compatibility:
            zf.writestr(REPORT_NAME, json.dumps(compatibility))

    manifest = {
        "source_id": "prepared-territorial-sources:" + ",".join(sorted(row["source_id"] for row in inventory_sources)),
        "territory_id": territory,
        "edition": edition,
        "population_year": population_year,
        "section_year": section_year,
        "origin": "https://official.example/sources",
        "path": "prepared_sources.zip",
        "bytes": bundle.stat().st_size,
        "sha256": hashlib.sha256(bundle.read_bytes()).hexdigest(),
        "records": 1,
        "acquired_at": "2026-09-19T00:00:00Z",
    }
    (package / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return package


def rewrite_bundle(package: Path, mutator) -> None:
    manifest_path = package / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    bundle = package / manifest["path"]
    with zipfile.ZipFile(bundle) as zf:
        members = {name: zf.read(name) for name in zf.namelist()}
    mutator(members)
    with zipfile.ZipFile(bundle, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in sorted(members):
            zf.writestr(name, members[name])
    manifest["bytes"] = bundle.stat().st_size
    manifest["sha256"] = hashlib.sha256(bundle.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")


class PreparedSourceReuseTests(unittest.TestCase):
    def test_valid_previous_package_is_reused(self):
        with tempfile.TemporaryDirectory() as td:
            package = build_package(Path(td) / "valid")
            selected, diagnostics = select_first_valid(
                [package], territory_id="la_rioja", edition=2025, reuse_enabled=True
            )
            self.assertEqual(selected, package)
            self.assertTrue(diagnostics[0]["valid"])
            self.assertEqual(
                validate_prepared_package(package, territory_id="la_rioja", edition=2025),
                (True, []),
            )

    def test_population_or_section_year_mismatch_is_not_reusable(self):
        with tempfile.TemporaryDirectory() as td:
            package = build_package(
                Path(td) / "valid",
                edition=2025,
                population_year=2025,
                section_year=2026,
            )
            valid, reasons = validate_prepared_package(
                package,
                territory_id="la_rioja",
                edition=2025,
                population_year=2025,
                section_year=2025,
            )
            self.assertFalse(valid)
            self.assertTrue(any("año de seccionado distinto" in reason for reason in reasons))

    def test_legacy_cross_year_package_without_geometry_admissibility_is_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            package = build_package(
                Path(td) / "legacy-cross-year",
                edition=2025,
                population_year=2025,
                section_year=2026,
            )
            valid, reasons = validate_prepared_package(
                package,
                territory_id="la_rioja",
                edition=2025,
                population_year=2025,
                section_year=2026,
            )
            self.assertFalse(valid)
            self.assertTrue(
                any(
                    "GEOMETRY_ADMISSIBILITY_EVIDENCE_MISSING" in reason
                    for reason in reasons
                ),
                reasons,
            )

    def test_legacy_package_without_compatibility_report_is_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            package = build_package(Path(td) / "legacy", include_compatibility=False)
            valid, reasons = validate_prepared_package(
                package, territory_id="la_rioja", edition=2025
            )
            self.assertFalse(valid)
            self.assertTrue(any("paquete histórico no reutilizable" in reason for reason in reasons))

    def test_replaced_population_or_sectioning_with_updated_inventory_invalidates_old_report(self):
        for role, member in (
            ("population", "materialized/inputs/population.zip"),
            ("target_sectioning", "materialized/inputs/sections.zip"),
        ):
            with self.subTest(role=role), tempfile.TemporaryDirectory() as td:
                package = build_package(Path(td) / "tampered")

                def mutate(members):
                    replacement = f"replacement-{role}".encode()
                    members[member] = replacement
                    inventory = json.loads(members["inventario_fuentes.json"].decode())
                    row = next(x for x in inventory["sources"] if x["role"] == role)
                    row["bytes"] = len(replacement)
                    row["sha256"] = hashlib.sha256(replacement).hexdigest()
                    members["inventario_fuentes.json"] = json.dumps(inventory).encode()

                rewrite_bundle(package, mutate)
                valid, reasons = validate_prepared_package(
                    package, territory_id="la_rioja", edition=2025
                )
                self.assertFalse(valid)
                self.assertTrue(any(f"INPUT_REPORT_SHA_MISMATCH: {role}" in r for r in reasons), reasons)

    def test_self_consistent_report_whose_inputs_do_not_match_package_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            package = build_package(Path(td) / "report-mismatch")

            def mutate(members):
                report = json.loads(members[REPORT_NAME].decode())
                report["inputs"]["population"]["sha256"] = "f" * 64
                report["compatibility_identity_sha256"] = _canonical_report_identity(report)
                members[REPORT_NAME] = json.dumps(report).encode()

            rewrite_bundle(package, mutate)
            valid, reasons = validate_prepared_package(
                package, territory_id="la_rioja", edition=2025
            )
            self.assertFalse(valid)
            self.assertTrue(any("INPUT_REPORT_SHA_MISMATCH: population" in r for r in reasons), reasons)

    def test_missing_or_duplicate_roles_are_rejected(self):
        cases = ("missing", "duplicate")
        for case in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as td:
                package = build_package(Path(td) / case)

                def mutate(members):
                    inventory = json.loads(members["inventario_fuentes.json"].decode())
                    if case == "missing":
                        inventory["sources"] = [
                            row for row in inventory["sources"]
                            if row["role"] != "target_sectioning"
                        ]
                    else:
                        population = next(row for row in inventory["sources"] if row["role"] == "population")
                        inventory["sources"].append(dict(population))
                    members["inventario_fuentes.json"] = json.dumps(inventory).encode()

                rewrite_bundle(package, mutate)
                valid, reasons = validate_prepared_package(
                    package, territory_id="la_rioja", edition=2025
                )
                self.assertFalse(valid)
                expected = "INPUT_ROLE_MISSING" if case == "missing" else "INPUT_ROLE_DUPLICATE"
                self.assertTrue(any(expected in r for r in reasons), reasons)

    def test_reuse_disabled_selects_nothing(self):
        with tempfile.TemporaryDirectory() as td:
            package = build_package(Path(td) / "valid")
            selected, diagnostics = select_first_valid(
                [package], territory_id="la_rioja", edition=2025, reuse_enabled=False
            )
            self.assertIsNone(selected)
            self.assertEqual(diagnostics, [])

    def test_corrupt_newest_falls_back_to_older_valid_package(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            newest = build_package(root / "newest", corrupt=True)
            older = build_package(root / "older")
            selected, diagnostics = select_first_valid(
                [newest, older], territory_id="la_rioja", edition=2025, reuse_enabled=True
            )
            self.assertEqual(selected, older)
            self.assertFalse(diagnostics[0]["valid"])
            self.assertTrue(diagnostics[1]["valid"])
            self.assertTrue(any(
                "tamaño incorrecto" in r
                or "checksum incorrecto" in r
                or "INPUT_" in r
                for r in diagnostics[0]["reasons"]
            ))

    def test_workflows_share_contract_and_recover_only_registered_artifact(self):
        territorial = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
        electoral = yaml.safe_load(ELECTORAL_WORKFLOW.read_text(encoding="utf-8"))
        territorial_trigger = territorial.get("on") or territorial.get(True)
        electoral_trigger = electoral.get("on") or electoral.get(True)

        self.assertEqual(
            list(territorial_trigger["workflow_dispatch"]["inputs"]),
            ["territory_id"],
        )
        self.assertEqual(
            list(electoral_trigger["workflow_dispatch"]["inputs"]),
            ["territory_id", "data_edition", "reutilizar_si_ya_preparada"],
        )
        self.assertEqual(
            list(territorial_trigger["workflow_call"]["inputs"]),
            ["territory_id", "data_edition", "source_year", "population_year", "section_year", "reutilizar_si_ya_preparada", "source_ref", "persist_state", "recover_run_id", "recover_artifact_sha256"],
        )
        resolver_run = territorial["jobs"]["resolver"]["steps"][-1]["run"]
        self.assertIn("resolver_preparacion_legislatura.py", resolver_run)
        self.assertIn("population_year_selected", resolver_run)
        self.assertIn("section_year_selected", resolver_run)
        self.assertNotIn("population_current_year", resolver_run)
        self.assertNotIn("section_current_year", resolver_run)
        self.assertNotIn("EVENT_NAME", resolver_run)
        self.assertIn('if [[ -z "$EDITION_INPUT" ]]; then', resolver_run)
        self.assertIn("reuse_enabled=true", resolver_run)
        self.assertIn("persist_requested=true", resolver_run)
        self.assertIn("EDITION_INPUT", territorial["jobs"]["resolver"]["steps"][-1]["env"])
        activacion = yaml.safe_load((ROOT / ".github/workflows/preparacion-legislatura-vigente.yml").read_text(encoding="utf-8"))
        territorial_call = activacion["jobs"]["territorial"]["with"]
        self.assertEqual(territorial_call["population_year"], "${{ needs.planificar.outputs.population_year }}")
        self.assertEqual(territorial_call["section_year"], "${{ needs.planificar.outputs.section_year }}")
        self.assertFalse(territorial_call["reutilizar_si_ya_preparada"])
        self.assertEqual(
            list(electoral_trigger["workflow_call"]["inputs"]),
            ["territory_id", "data_edition", "reutilizar_si_ya_preparada", "source_ref", "persist_state", "allow_source_gap_success"],
        )
        self.assertFalse(
            electoral_trigger["workflow_call"]["inputs"]["allow_source_gap_success"]["default"]
        )

        territorial_steps = territorial["jobs"]["territoriales"]["steps"]
        electoral_steps = electoral["jobs"]["electorales"]["steps"]
        territorial_previous = next(s for s in territorial_steps if s.get("id") == "previous")
        electoral_previous = next(s for s in electoral_steps if s.get("id") == "previous")

        for previous in (territorial_previous, electoral_previous):
            self.assertIn("registered_run_id != ''", previous["if"])
            self.assertIn("REGISTERED_RUN_ID", previous["run"])
            self.assertIn("REGISTERED_ARTIFACT_NAME", previous["run"])
            self.assertIn("REGISTERED_ARTIFACT_SHA256", previous["run"])
            self.assertNotIn("actions/runs?status=completed", previous["run"])

        acquire = next(s for s in territorial_steps if s.get("name") == "Adquirir y congelar fuentes")
        self.assertEqual(acquire["id"], "acquire")
        self.assertEqual(acquire["if"], "${{ steps.previous.outputs.reused_candidate != 'true' }}")
        diagnostics = next(
            s for s in territorial_steps
            if s.get("name") == "Publicar diagnóstico de adquisición fallida"
        )
        self.assertEqual(
            diagnostics["if"],
            "${{ failure() && steps.acquire.outcome == 'failure' }}",
        )
        self.assertIn("ddd-source-diagnostics-", diagnostics["with"]["name"])
        self.assertEqual(diagnostics["with"]["path"], "${{ env.EVIDENCE_DIR }}")
        reuse_install = next(
            s for s in territorial_steps
            if s.get("name") == "Instalar entorno geoespacial para reutilización"
        )
        self.assertEqual(reuse_install["if"], territorial_previous["if"])
        self.assertIn("-r requirements.lock", reuse_install["run"])
        reuse_verify = next(
            s for s in territorial_steps
            if s.get("name") == "Verificar entorno geoespacial para reutilización"
        )
        self.assertEqual(reuse_verify["if"], territorial_previous["if"])
        self.assertIn("import geopandas", reuse_verify["run"])
        self.assertIn("herramientas.seleccionar_paquete_fuentes", territorial_previous["run"])

        electoral_prepare = next(s for s in electoral_steps if s.get("id") == "prepare")
        self.assertIn("--previous-package .ddd-electoral-previous", electoral_prepare["run"])
        self.assertNotIn("electorales", territorial["jobs"])
        self.assertNotIn("territoriales", electoral["jobs"])


if __name__ == "__main__":
    unittest.main()
