import csv
import io
import json
from pathlib import Path

import pytest

from herramientas import registrar_anomalias_n08 as registry


ROOT = Path(__file__).resolve().parents[1]
PRODUCT = ROOT / "docs/ESTUDIOS/N08_TOPOLOGIA_NACIONAL_20251012/producto"
COMPONENTS = ROOT / "docs/ESTUDIOS/N08_TOPOLOGIA_NACIONAL_20251012/COMPONENTES_POBLACION.csv"


def test_registry_extracts_all_archived_anomalies_without_creating_edges(tmp_path):
    rows = registry.extract(PRODUCT, COMPONENTS)
    counts = {}
    for row in rows:
        counts[row["case_type"]] = counts.get(row["case_type"], 0) + 1
    assert counts == {
        "OVERLAP_PAIR": 498,
        "POINT_ONLY_CONTACT": 5750,
        "MULTIPART_POPULATION_UNATTRIBUTED": 115,
        "INTERPROVINCIAL_OVERLAP_PAIR": 7,
    }
    assert all(row["classification"].endswith("UNCLASSIFIED") for row in rows if "OVERLAP" in row["case_type"])
    cross_component = [row for row in rows if row["case_type"] == "OVERLAP_PAIR"
                       and row["physical_component_1"] != row["physical_component_2"]]
    assert len(cross_component) == 9
    assert all(row["section_geometry_1_sha256"] and row["section_geometry_2_sha256"]
               and row["section_part_ids_by_cusec_json"] for row in rows if row["case_type"] != "MULTIPART_POPULATION_UNATTRIBUTED")
    for row in rows:
        parts = json.loads(row["section_part_ids_by_cusec_json"])
        if row["case_type"] == "MULTIPART_POPULATION_UNATTRIBUTED":
            assert all(part.startswith(row["CUSEC_1"] + ":p") for part in parts)
            assert json.loads(row["part_population_by_part_json"]) == {
                part: "NOT_EVIDENCED" for part in parts
            }
        else:
            assert all(part.startswith(ident + ":p")
                       for ident, section_parts in parts.items() for part in section_parts)
    sample = next(row for row in rows if row["case_id"] == "OVERLAP:02:0200302024:0200308001")
    assert json.loads(sample["section_part_ids_by_cusec_json"]) == {
        "0200302024": ["0200302024:p0000"],
        "0200308001": ["0200308001:p0000", "0200308001:p0001"],
    }
    assert all(row["graph_linear_edge_present"] == "false" for row in rows if row["case_type"] in {"OVERLAP_PAIR", "POINT_ONLY_CONTACT", "INTERPROVINCIAL_OVERLAP_PAIR"})
    assert all(row["status"] == "EXCLUDED_FROM_PHYSICAL_GRAPH" for row in rows if row["case_type"] == "POINT_ONLY_CONTACT")
    assert all(row["part_population_status"] == "UNKNOWN_BY_PART; SECTION_TOTAL_PRESERVED" for row in rows if row["case_type"] == "MULTIPART_POPULATION_UNATTRIBUTED")
    first = tmp_path / "first.csv"
    second = tmp_path / "second.csv"
    registry.write_csv(rows, first)
    registry.write_csv(registry.extract(PRODUCT, COMPONENTS), second)
    assert first.read_bytes() == second.read_bytes()
    with first.open(encoding="utf-8", newline="") as handle:
        output = list(csv.DictReader(handle))
    assert len(output) == len(rows)


def test_registry_rejects_tampered_outer_inputs(tmp_path):
    changed_components = tmp_path / "COMPONENTES_POBLACION.csv"
    rows = COMPONENTS.read_text(encoding="utf-8")
    changed_components.write_text(rows.replace("0301408014", "0301408015"), encoding="utf-8")
    with pytest.raises(ValueError, match="DELIVERY_COMPONENT_POPULATION_SHA_MISMATCH"):
        registry.extract(PRODUCT, changed_components)

    delivery_root = tmp_path / "delivery"
    altered_product = delivery_root / "producto"
    altered_product.mkdir(parents=True)
    original = json.loads((PRODUCT / "manifest.json").read_text(encoding="utf-8"))
    original["evidence"]["geometry_identity_sha256"] = "0" * 64
    (altered_product / "manifest.json").write_text(json.dumps(original), encoding="utf-8")
    (delivery_root / "MANIFEST_ENTREGA.json").write_bytes(
        (PRODUCT.parent / "MANIFEST_ENTREGA.json").read_bytes())
    with pytest.raises(ValueError, match="DELIVERY_TOPOLOGY_MANIFEST_SHA_MISMATCH"):
        registry.extract(altered_product, COMPONENTS)


def test_registry_rejects_modified_archived_artifact_hash(monkeypatch):
    original = registry._sha

    def mismatched(path):
        if path.name == "01.json.gz":
            return "0" * 64
        return original(path)

    monkeypatch.setattr(registry, "_sha", mismatched)
    with pytest.raises(ValueError, match="PRODUCT_ARTIFACT_SHA_MISMATCH:unidades/01.json.gz"):
        registry.extract(PRODUCT, COMPONENTS)


def test_registry_rejects_overlap_pair_also_present_as_accepted_edge(monkeypatch):
    original_open = registry.gzip.open

    def contradictory_open(path, mode="rb", *args, **kwargs):
        if str(path).endswith("unidades/02.json.gz"):
            with original_open(path, "rt", encoding="utf-8") as stream:
                unit = json.load(stream)
            overlap = unit["overlaps"][0]
            unit["edges"].append({
                "u": overlap["u"], "v": overlap["v"], "shared_border_m": 1.0,
                "overlap_m2": 0.0, "edge_type": "geometric", "contact_sha256": "a" * 64,
            })
            return io.StringIO(json.dumps(unit))
        return original_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(registry.gzip, "open", contradictory_open)
    with pytest.raises(ValueError, match="OVERLAP_PAIR_PRESENT_AS_ACCEPTED_EDGE:02:"):
        registry.extract(PRODUCT, COMPONENTS)
