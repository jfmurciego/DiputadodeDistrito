from __future__ import annotations

import csv
import hashlib
import importlib.util
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon, box

from ddd_core.territorial_validation import (
    TerritorialDataError,
    parse_population_value,
    validate_geodataframe,
)
from herramientas.compatibilidad_poblacion_seccionado import (
    REPORT_NAME,
    assert_materialized_territorial_gate,
)
from herramientas.ejecutar_fuentes_workflow import (
    _manifest_from_acquisition,
    validate_materialized_evidence,
)
from herramientas.politica_reutilizacion_fuentes import validate_frozen_copy
from herramientas.seleccionar_paquete_fuentes import validate_prepared_package

ROOT = Path(__file__).resolve().parents[1]
M01_PATH = ROOT / "modulos/01_preparar_base_territorial.py"
spec = importlib.util.spec_from_file_location("m01_strict_boundaries", M01_PATH)
m01 = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(m01)


def _population_zip(path: Path, rows: list[tuple[str, object]]) -> bytes:
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=["Secciones", "Total"], delimiter=";")
    writer.writeheader()
    for section, population in rows:
        writer.writerow({"Secciones": section, "Total": population})
    payload = stream.getvalue().encode("utf-8")
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("population.csv", payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(out.getvalue())
    return out.getvalue()


def _section_zip(
    path: Path,
    *,
    section_ids: list[str],
    geometries: list,
    crs: str | None = "EPSG:4326",
    include_prj: bool = True,
) -> bytes:
    with tempfile.TemporaryDirectory(prefix="ddd-real-section-package-") as td:
        root = Path(td)
        shp = root / "seccionado.shp"
        gdf = gpd.GeoDataFrame({"CUSEC": section_ids}, geometry=geometries, crs=crs)
        gdf.to_file(shp, driver="ESRI Shapefile", index=False)
        out = io.BytesIO()
        with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for member in sorted(root.glob("seccionado.*")):
                if not include_prj and member.suffix.lower() == ".prj":
                    continue
                archive.writestr(member.name, member.read_bytes())
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(out.getvalue())
    return out.getvalue()


def _write_evidence(
    root: Path,
    *,
    population_rows: list[tuple[str, object]],
    section_ids: list[str] | None = None,
    geometries: list | None = None,
    crs: str | None = "EPSG:4326",
    include_prj: bool = True,
) -> tuple[Path, dict]:
    evidence = root / "evidence"
    materialized = evidence / "materialized" / "inputs"
    section_ids = section_ids or ["0100101001"]
    geometries = geometries or [box(-3.8, 40.3, -3.7, 40.4)]
    pop_payload = _population_zip(materialized / "population.zip", population_rows)
    sec_payload = _section_zip(
        materialized / "sections.zip",
        section_ids=section_ids,
        geometries=geometries,
        crs=crs,
        include_prj=include_prj,
    )
    inventory = {
        "territory_id": "demo",
        "edition": 2025,
        "population_year": 2025,
        "section_year": 2025,
        "sources": [
            {
                "source_id": "population",
                "role": "population",
                "path": "inputs/population.zip",
                "bytes": len(pop_payload),
                "sha256": hashlib.sha256(pop_payload).hexdigest(),
                "edition": 2025,
            },
            {
                "source_id": "sections",
                "role": "target_sectioning",
                "path": "inputs/sections.zip",
                "bytes": len(sec_payload),
                "sha256": hashlib.sha256(sec_payload).hexdigest(),
                "edition": 2025,
            },
        ],
    }
    provenance = {
        "territory_id": "demo",
        "edition": 2025,
        "population_year": 2025,
        "section_year": 2025,
        "sources": [
            {"source_id": "population", "acquired_at_utc": "2026-09-30T12:00:00+00:00"},
            {"source_id": "sections", "acquired_at_utc": "2026-09-30T12:01:00+00:00"},
        ],
    }
    decision = {
        "territory_id": "demo",
        "edition": 2025,
        "population_year": 2025,
        "section_year": 2025,
        "decision": "READY",
    }
    declaration = {
        "territory_id": "demo",
        "edition": 2025,
        "population_year": 2025,
        "section_year": 2025,
    }
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / "inventario_fuentes.json").write_text(json.dumps(inventory), encoding="utf-8")
    (evidence / "manifiesto_procedencia.json").write_text(json.dumps(provenance), encoding="utf-8")
    (evidence / "decision_adquisicion.json").write_text(json.dumps(decision), encoding="utf-8")
    (evidence / "declaracion_materializacion.json").write_text(json.dumps(declaration), encoding="utf-8")
    return evidence, inventory


def _freeze_package(evidence: Path, package: Path, *, acquired_at: str = "2026-09-30T12:01:00+00:00") -> Path:
    package.mkdir(parents=True, exist_ok=True)
    bundle = package / "prepared_sources.zip"
    with zipfile.ZipFile(bundle, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(p for p in evidence.rglob("*") if p.is_file()):
            archive.writestr(path.relative_to(evidence).as_posix(), path.read_bytes())
    manifest = {
        "source_id": "prepared-territorial-sources:population,sections",
        "territory_id": "demo",
        "edition": 2025,
        "source_year": 2025,
        "population_year": 2025,
        "section_year": 2025,
        "origin": "https://official.example.test",
        "path": bundle.name,
        "bytes": bundle.stat().st_size,
        "sha256": hashlib.sha256(bundle.read_bytes()).hexdigest(),
        "records": 1,
        "acquired_at": acquired_at,
    }
    (package / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return package


class PopulationBoundaryTests(unittest.TestCase):
    def test_explicit_zero_is_valid_but_missing_non_numeric_and_negative_block(self):
        self.assertEqual(parse_population_value("0", section_id="0100101001"), 0)
        self.assertEqual(parse_population_value(0, section_id="0100101001"), 0)
        for bad, code in ((None, "POPULATION_MISSING"), ("", "POPULATION_MISSING"), ("abc", "POPULATION_NON_NUMERIC"), ("-1", "POPULATION_NEGATIVE")):
            with self.subTest(value=bad), self.assertRaisesRegex(TerritorialDataError, code):
                parse_population_value(bad, section_id="0100101001")

    def test_m01_does_not_drop_bad_population_or_sum_duplicate_normalized_keys(self):
        filters = {
            "year_col": "Periodo",
            "sexo_col": "Sexo",
            "edad_col": "Edad",
            "sexo_total_values": ["Total"],
            "edad_total_values": ["Todas las edades"],
            "year_value": 2025,
        }
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            good = root / "good.csv"
            good.write_text(
                "Periodo;Sexo;Edad;Secciones;Total\n2025;Total;Todas las edades;0100101001;0\n",
                encoding="utf-8",
            )
            result = m01.load_cip([str(good)], "Secciones", "Total", 2025, ";", filters, ["01"])
            self.assertEqual(result.to_dict("records"), [{"CUSEC_KEY": "0100101001", "POP": 0}])

            duplicate = root / "duplicate.csv"
            duplicate.write_text(
                "Periodo;Sexo;Edad;Secciones;Total\n"
                "2025;Total;Todas las edades;0100101001;10\n"
                "2025;Total;Todas las edades;01 001 01 001;20\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(TerritorialDataError, "DUPLICATE_AFTER_NORMALIZATION"):
                m01.load_cip([str(duplicate)], "Secciones", "Total", 2025, ";", filters, ["01"])

            missing = root / "missing.csv"
            missing.write_text(
                "Periodo;Sexo;Edad;Secciones;Total\n2025;Total;Todas las edades;0100101001;\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(TerritorialDataError, "POPULATION_MISSING"):
                m01.load_cip([str(missing)], "Secciones", "Total", 2025, ";", filters, ["01"])


class RealTerritorialPackageGateTests(unittest.TestCase):
    def test_real_local_package_passes_preparation_reuse_and_promotion_with_zero_population(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            evidence, inventory = _write_evidence(
                root,
                population_rows=[("0100101001", "0")],
            )
            prepared = assert_materialized_territorial_gate(
                evidence_dir=evidence,
                territory_id="demo",
                edition="2025",
                population_year=2025,
                section_year=2025,
                inventory=inventory,
            )
            self.assertEqual(prepared["decision"], "READY")
            self.assertEqual(prepared["population"]["input_total"], 0)

            reused = validate_materialized_evidence(
                evidence,
                territory_id="demo",
                edition=2025,
                population_year=2025,
                section_year=2025,
            )
            self.assertEqual(reused["compatibility_identity_sha256"], prepared["compatibility_identity_sha256"])

            package = _freeze_package(evidence, root / "package")
            valid, reasons = validate_prepared_package(
                package,
                territory_id="demo",
                edition=2025,
                population_year=2025,
                section_year=2025,
            )
            self.assertTrue(valid, reasons)

    def test_real_local_population_errors_block_before_package_can_be_promoted_or_reused(self):
        cases = [
            ([("0100101001", "")], "POPULATION_MISSING"),
            ([("0100101001", "abc")], "POPULATION_NON_NUMERIC"),
            ([("0100101001", "-1")], "POPULATION_NEGATIVE"),
            ([("0100101001", "10"), ("01 001 01 001", "20")], "DUPLICATE_POPULATION_KEYS"),
        ]
        for rows, expected in cases:
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                evidence, inventory = _write_evidence(root, population_rows=rows)
                with self.assertRaisesRegex(ValueError, expected):
                    assert_materialized_territorial_gate(
                        evidence_dir=evidence,
                        territory_id="demo",
                        edition="2025",
                        population_year=2025,
                        section_year=2025,
                        inventory=inventory,
                    )
                with self.assertRaisesRegex(ValueError, expected):
                    validate_materialized_evidence(
                        evidence,
                        territory_id="demo",
                        edition=2025,
                        population_year=2025,
                        section_year=2025,
                    )

    def test_real_local_missing_correspondence_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            evidence, inventory = _write_evidence(
                root,
                population_rows=[("0100101001", "10")],
                section_ids=["0100101002"],
            )
            with self.assertRaisesRegex(ValueError, "POPULATION_WITHOUT_GEOMETRY|GEOMETRY_WITHOUT_POPULATION"):
                assert_materialized_territorial_gate(
                    evidence_dir=evidence,
                    territory_id="demo",
                    edition="2025",
                    population_year=2025,
                    section_year=2025,
                    inventory=inventory,
                )

    def test_real_local_same_year_missing_crs_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            evidence, inventory = _write_evidence(
                root,
                population_rows=[("0100101001", "10")],
                include_prj=False,
            )
            with self.assertRaisesRegex(ValueError, "CRS_MISSING"):
                assert_materialized_territorial_gate(
                    evidence_dir=evidence,
                    territory_id="demo",
                    edition="2025",
                    population_year=2025,
                    section_year=2025,
                    inventory=inventory,
                )

    def test_real_local_same_year_invalid_geometry_blocks(self):
        bowtie = Polygon([(0, 0), (1, 1), (1, 0), (0, 1), (0, 0)])
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            evidence, inventory = _write_evidence(
                root,
                population_rows=[("0100101001", "10")],
                geometries=[bowtie],
            )
            with self.assertRaisesRegex(ValueError, "GEOMETRY_INVALID"):
                assert_materialized_territorial_gate(
                    evidence_dir=evidence,
                    territory_id="demo",
                    edition="2025",
                    population_year=2025,
                    section_year=2025,
                    inventory=inventory,
                )

    def test_null_empty_and_invalid_geometry_never_repaired(self):
        cases = [
            ([None], "GEOMETRY_NULL"),
            ([Polygon()], "GEOMETRY_EMPTY"),
            ([Polygon([(0, 0), (1, 1), (1, 0), (0, 1), (0, 0)])], "GEOMETRY_INVALID"),
        ]
        for geometries, expected in cases:
            with self.subTest(expected=expected):
                gdf = gpd.GeoDataFrame(
                    {"CUSEC": ["0100101001"]},
                    geometry=geometries,
                    crs="EPSG:4326",
                )
                with self.assertRaisesRegex(TerritorialDataError, expected):
                    validate_geodataframe(gdf, label="test")

    def test_historical_unknown_date_is_blocked_not_rewritten(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            frozen = root / "prepared_sources.zip"
            frozen.write_bytes(b"historical")
            manifest = {
                "source_id": "historical",
                "edition": 2025,
                "origin": "historical",
                "path": frozen.name,
                "bytes": frozen.stat().st_size,
                "sha256": hashlib.sha256(frozen.read_bytes()).hexdigest(),
                "records": 1,
                "acquired_at": "unknown-acquisition-date",
            }
            valid, reasons = validate_frozen_copy(manifest, root, expected_edition=2025)
            self.assertFalse(valid)
            self.assertTrue(any("fecha de adquisición" in reason for reason in reasons))
            self.assertEqual(manifest["acquired_at"], "unknown-acquisition-date")

    def test_new_manifest_reads_real_acquired_at_utc_and_rejects_missing_date(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            evidence, _ = _write_evidence(root, population_rows=[("0100101001", "10")])
            working = root / "working"
            working.mkdir()
            manifest = _manifest_from_acquisition(
                evidence, working, "demo", 2025, 2025, 2025, 1
            )
            self.assertEqual(manifest["acquired_at"], "2026-09-30T12:01:00+00:00")

            provenance = json.loads((evidence / "manifiesto_procedencia.json").read_text(encoding="utf-8"))
            for row in provenance["sources"]:
                row.pop("acquired_at_utc", None)
            (evidence / "manifiesto_procedencia.json").write_text(json.dumps(provenance), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "sin fecha de adquisición interpretable"):
                _manifest_from_acquisition(
                    evidence, root / "working2", "demo", 2025, 2025, 2025, 1
                )


if __name__ == "__main__":
    unittest.main()
