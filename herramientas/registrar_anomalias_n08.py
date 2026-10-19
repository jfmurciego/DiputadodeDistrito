"""Versión 1.0.0; 2026-10-13; exportación nominal de incidencias N08.

Nombre: registro nominal derivado de incidencias topológicas N08.
Alcance: extraer del producto acreditado solapamientos y CUSEC sin población
         por parte; no repara geometrías, clasifica causas ni crea adyacencias.
Estado: candidato diagnóstico.
Cambio/motivo: hacer inspeccionables los 498 pares solapados y las 115 CUSEC
               multipartes sin atribución, conservando identidad y SHA.
Origen: nuevo; no sustituye ni modifica fuentes/productos originales.
Anterior: no aplicable; herramienta nueva.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path


FIELDS = (
    "case_id", "CPRO", "case_type", "classification", "status", "CUSEC_1",
    "CUSEC_2", "section_geometry_1_sha256", "section_geometry_2_sha256",
    "municipality", "physical_component_1", "physical_component_2",
    "section_part_ids_by_cusec_json", "section_population_2025", "part_population_status",
    "part_population_by_part_json",
    "overlap_area_m2", "shared_border_m", "contact_sha256", "graph_linear_edge_present",
    "graph_edge_contact_sha256", "source_edition", "product_path",
    "product_sha256", "source_geometry_sha256", "evidence", "proposal",
    "owner_decision", "expiry_condition",
)


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def extract(product_dir: Path, components_csv: Path) -> list[dict[str, str]]:
    manifest_path = product_dir / "manifest.json"
    delivery_path = product_dir.parent / "MANIFEST_ENTREGA.json"
    if not delivery_path.is_file():
        raise ValueError("DELIVERY_MANIFEST_MISSING")
    delivery = json.loads(delivery_path.read_text(encoding="utf-8"))
    delivery_hashes = delivery.get("files_sha256", {})
    if delivery_hashes.get("producto/manifest.json") != _sha(manifest_path):
        raise ValueError("DELIVERY_TOPOLOGY_MANIFEST_SHA_MISMATCH")
    if delivery_hashes.get("COMPONENTES_POBLACION.csv") != _sha(components_csv):
        raise ValueError("DELIVERY_COMPONENT_POPULATION_SHA_MISMATCH")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema") != "ddd.congress-topology-diagnostic/1.0":
        raise ValueError("TOPOLOGY_MANIFEST_SCHEMA_INVALID")
    if manifest.get("generation_authorized") is not False:
        raise ValueError("GENERATION_AUTHORIZATION_MUST_REMAIN_FALSE")

    uncredited: set[str] = set()
    with components_csv.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            uncredited.update(code for code in row["CUSEC_sin_desagregacion"].split(",") if code)

    result: list[dict[str, str]] = []
    all_nodes: dict[str, dict] = {}
    all_parts_by_cusec: dict[str, list[str]] = {}
    for number in range(1, 53):
        cpro = f"{number:02d}"
        rel = f"unidades/{cpro}.json.gz"
        path = product_dir / rel
        declared = manifest.get("artifacts", {}).get(rel, {}).get("sha256")
        digest = _sha(path)
        if not declared or digest != declared:
            raise ValueError(f"PRODUCT_ARTIFACT_SHA_MISMATCH:{rel}")
        with gzip.open(path, "rt", encoding="utf-8") as stream:
            product = json.load(stream)
        if product.get("generation_authorized") is True:
            raise ValueError(f"UNIT_GENERATION_AUTHORIZATION_MUST_REMAIN_FALSE:{cpro}")
        nodes = {node["id"]: node for node in product["nodes"]}
        all_nodes.update(nodes)
        part_ids_by_cusec: dict[str, list[str]] = {ident: [] for ident in nodes}
        for component in product["polygon_part_components"]:
            for part_id in component["parts"]:
                ident, separator, _part = part_id.partition(":p")
                if not separator or ident not in part_ids_by_cusec:
                    raise ValueError(f"PHYSICAL_PART_IDENTITY_INVALID:{cpro}:{part_id}")
                part_ids_by_cusec[ident].append(part_id)
        if any(not parts for parts in part_ids_by_cusec.values()):
            raise ValueError(f"PHYSICAL_PART_COVERAGE_INCOMPLETE:{cpro}")
        all_parts_by_cusec.update({ident: sorted(parts) for ident, parts in part_ids_by_cusec.items()})
        edges = {tuple(sorted((edge["u"], edge["v"]))): edge for edge in product["edges"]}

        for overlap in product["overlaps"]:
            u, v = sorted((overlap["u"], overlap["v"]))
            if u not in nodes or v not in nodes:
                raise ValueError(f"OVERLAP_ENDPOINT_MISSING:{cpro}:{u}:{v}")
            edge = edges.get((u, v))
            if edge is not None:
                raise ValueError(f"OVERLAP_PAIR_PRESENT_AS_ACCEPTED_EDGE:{cpro}:{u}:{v}")
            result.append({
                "case_id": f"OVERLAP:{cpro}:{u}:{v}", "CPRO": cpro,
                "case_type": "OVERLAP_PAIR", "classification": "OVERLAP_CAUSE_UNCLASSIFIED",
                "status": "OPEN_DIAGNOSTIC", "CUSEC_1": u, "CUSEC_2": v,
                "section_geometry_1_sha256": nodes[u].get("geometry_sha256", ""),
                "section_geometry_2_sha256": nodes[v].get("geometry_sha256", ""),
                "municipality": f"{nodes[u].get('CUMUN','')}|{nodes[v].get('CUMUN','')}",
                "physical_component_1": nodes[u].get("physical_component", ""),
                "physical_component_2": nodes[v].get("physical_component", ""),
                "section_part_ids_by_cusec_json": json.dumps({u: sorted(part_ids_by_cusec[u]),
                                                    v: sorted(part_ids_by_cusec[v])},
                                                   ensure_ascii=False, sort_keys=True, separators=(",", ":")),
                "section_population_2025": f"{nodes[u].get('POB_2025','')}|{nodes[v].get('POB_2025','')}",
                "part_population_status": "NOT_APPLICABLE",
                "part_population_by_part_json": "",
                "overlap_area_m2": str(overlap.get("overlap_m2", "")),
                "shared_border_m": str(overlap.get("shared_border_m", "")),
                "contact_sha256": overlap.get("contact_sha256", ""),
                "graph_linear_edge_present": "false",
                "graph_edge_contact_sha256": "",
                "source_edition": "2025", "product_path": rel, "product_sha256": digest,
                "source_geometry_sha256": manifest.get("evidence", {}).get("geometry_identity_sha256", ""),
                "evidence": "archived section-level overlap record; part lists are complete endpoint inventories and do not attribute a touching part pair; overlap alone is not accepted as an edge",
                "proposal": "compare original geometry and independent administrative domain; retain or exclude only by evidence",
                "owner_decision": "NONE; no nominal exception approved",
                "expiry_condition": "re-evaluate if source edition/hash changes",
            })

        for contact in product["point_contacts"]:
            u, v = sorted((contact["u"], contact["v"]))
            if u not in nodes or v not in nodes:
                raise ValueError(f"POINT_CONTACT_ENDPOINT_MISSING:{cpro}:{u}:{v}")
            if (u, v) in edges:
                raise ValueError(f"POINT_ONLY_CONTACT_PRESENT_AS_GRAPH_EDGE:{cpro}:{u}:{v}")
            result.append({
                "case_id": f"POINT:{cpro}:{u}:{v}", "CPRO": cpro,
                "case_type": "POINT_ONLY_CONTACT", "classification": "POINT_CONTACT_NOT_CONTIGUITY",
                "status": "EXCLUDED_FROM_PHYSICAL_GRAPH", "CUSEC_1": u, "CUSEC_2": v,
                "section_geometry_1_sha256": nodes[u].get("geometry_sha256", ""),
                "section_geometry_2_sha256": nodes[v].get("geometry_sha256", ""),
                "municipality": f"{nodes[u].get('CUMUN','')}|{nodes[v].get('CUMUN','')}",
                "physical_component_1": nodes[u].get("physical_component", ""),
                "physical_component_2": nodes[v].get("physical_component", ""),
                "section_part_ids_by_cusec_json": json.dumps({u: sorted(part_ids_by_cusec[u]),
                                                    v: sorted(part_ids_by_cusec[v])},
                                                   ensure_ascii=False, sort_keys=True, separators=(",", ":")),
                "section_population_2025": f"{nodes[u].get('POB_2025','')}|{nodes[v].get('POB_2025','')}",
                "part_population_status": "NOT_APPLICABLE", "overlap_area_m2": "",
                "part_population_by_part_json": "",
                "shared_border_m": "0", "contact_sha256": contact.get("contact_sha256", ""),
                "graph_linear_edge_present": str((u, v) in edges).lower(),
                "graph_edge_contact_sha256": "", "source_edition": "2025",
                "product_path": rel, "product_sha256": digest,
                "source_geometry_sha256": manifest.get("evidence", {}).get("geometry_identity_sha256", ""),
                "evidence": "archived section-level point-only contact record; part lists are complete endpoint inventories and do not attribute a touching part pair; point contact is excluded from physical adjacency",
                "proposal": "retain as point-only evidence; do not create an edge",
                "owner_decision": "NONE; no nominal exception approved",
                "expiry_condition": "re-evaluate if source edition/hash changes",
            })

        for ident in sorted(uncredited.intersection(nodes)):
            node = nodes[ident]
            parts = sorted(part_ids_by_cusec[ident])
            result.append({
                "case_id": f"MULTIPART-POP:{ident}", "CPRO": cpro,
                "case_type": "MULTIPART_POPULATION_UNATTRIBUTED",
                "classification": "PHYSICAL_PART_POPULATION_NOT_EVIDENCED",
                "status": "INSUFFICIENT_EVIDENCE", "CUSEC_1": ident, "CUSEC_2": "",
                "section_geometry_1_sha256": node.get("geometry_sha256", ""),
                "section_geometry_2_sha256": "",
                "municipality": node.get("CUMUN", ""),
                "physical_component_1": node.get("physical_component", ""),
                "physical_component_2": "",
                "section_part_ids_by_cusec_json": json.dumps(parts, ensure_ascii=False, separators=(",", ":")),
                "section_population_2025": str(node.get("POB_2025", node.get("pop", ""))),
                "part_population_status": "UNKNOWN_BY_PART; SECTION_TOTAL_PRESERVED",
                "part_population_by_part_json": json.dumps(
                    {part: "NOT_EVIDENCED" for part in parts}, sort_keys=True, separators=(",", ":")),
                "overlap_area_m2": "", "shared_border_m": "", "contact_sha256": "",
                "graph_linear_edge_present": "", "graph_edge_contact_sha256": "",
                "source_edition": "2025", "product_path": rel, "product_sha256": digest,
                "source_geometry_sha256": manifest.get("evidence", {}).get("geometry_identity_sha256", ""),
                "evidence": "component population table lists CUSEC under CUSEC_sin_desagregacion",
                "proposal": "seek official population at part-level resolution; never apportion by area or proximity",
                "owner_decision": "NONE; no nominal exception approved",
                "expiry_condition": "re-evaluate if source edition/hash or CUSEC geometry changes",
            })

    interprov_path = product_dir / "contactos_interprovinciales.json.gz"
    declared = manifest.get("artifacts", {}).get("contactos_interprovinciales.json.gz", {}).get("sha256")
    interprov_digest = _sha(interprov_path)
    if not declared or interprov_digest != declared:
        raise ValueError("PRODUCT_ARTIFACT_SHA_MISMATCH:contactos_interprovinciales.json.gz")
    with gzip.open(interprov_path, "rt", encoding="utf-8") as stream:
        interprov = json.load(stream)
    for contact in interprov:
        if float(contact.get("overlap_m2", 0.0)) <= 0:
            continue
        u, v = sorted((contact["u"], contact["v"]))
        result.append({
            "case_id": f"INTERPROV-OVERLAP:{contact['CPRO_u']}:{contact['CPRO_v']}:{u}:{v}",
            "CPRO": f"{contact['CPRO_u']}-{contact['CPRO_v']}",
            "case_type": "INTERPROVINCIAL_OVERLAP_PAIR", "classification": "OVERLAP_CAUSE_UNCLASSIFIED",
            "status": "EXCLUDED_FROM_GRAPH; OPEN_DIAGNOSTIC", "CUSEC_1": u, "CUSEC_2": v,
            "section_geometry_1_sha256": all_nodes.get(u, {}).get("geometry_sha256", ""),
            "section_geometry_2_sha256": all_nodes.get(v, {}).get("geometry_sha256", ""),
            "municipality": f"{all_nodes.get(u,{}).get('CUMUN','')}|{all_nodes.get(v,{}).get('CUMUN','')}",
            "physical_component_1": all_nodes.get(u, {}).get("physical_component", ""),
            "physical_component_2": all_nodes.get(v, {}).get("physical_component", ""),
            "section_part_ids_by_cusec_json": json.dumps({u: sorted(all_parts_by_cusec[u]),
                                                v: sorted(all_parts_by_cusec[v])},
                                               ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            "section_population_2025": f"{all_nodes.get(u,{}).get('POB_2025','')}|{all_nodes.get(v,{}).get('POB_2025','')}",
            "part_population_status": "NOT_APPLICABLE", "overlap_area_m2": str(contact["overlap_m2"]),
            "part_population_by_part_json": "",
            "shared_border_m": str(contact.get("shared_border_m", "")),
            "contact_sha256": contact.get("contact_sha256", ""),
            "graph_linear_edge_present": "false", "graph_edge_contact_sha256": "",
            "source_edition": "2025", "product_path": "contactos_interprovinciales.json.gz",
            "product_sha256": interprov_digest,
            "source_geometry_sha256": manifest.get("evidence", {}).get("geometry_identity_sha256", ""),
            "evidence": "archived interprovincial section-contact record; listed parts are the endpoint sections' full part inventories, not an attribution of which parts touched; cross-province relation excluded from graph",
            "proposal": "compare source geometries and administrative boundary evidence; never add cross-province edge",
            "owner_decision": "NONE; no nominal exception approved",
            "expiry_condition": "re-evaluate if source edition/hash changes",
        })
    return sorted(result, key=lambda row: (row["CPRO"], row["case_id"]))


def write_csv(rows: list[dict[str, str]], target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--product", type=Path, required=True)
    parser.add_argument("--components", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = extract(args.product, args.components)
    write_csv(rows, args.output)
    print(json.dumps({
        "rows": len(rows),
        "overlap_pairs": sum(row["case_type"] == "OVERLAP_PAIR" for row in rows),
        "point_contacts": sum(row["case_type"] == "POINT_ONLY_CONTACT" for row in rows),
        "interprovincial_overlap_pairs": sum(row["case_type"] == "INTERPROVINCIAL_OVERLAP_PAIR" for row in rows),
        "unattributed_multipart_cusec": sum(row["case_type"] == "MULTIPART_POPULATION_UNATTRIBUTED" for row in rows),
        "generation_authorized": False,
        "output_sha256": _sha(args.output),
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
