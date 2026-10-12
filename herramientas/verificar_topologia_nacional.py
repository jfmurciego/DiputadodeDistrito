#!/usr/bin/env python3
"""VERSIÓN 1.0.0; NOMBRE auditoría independiente N08; FECHA 2026-10-12.
ALCANCE: auditoría original escalar e integridad de artefactos; no generación.
ESTADO: candidato; CAMBIOS/MOTIVO: reproducción independiente de contactos.
ORIGEN: nuevo, sin reutilizar contacts ni componentes del constructor.
"""
from __future__ import annotations
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from shapely import STRtree
from herramientas.preflight_topologico_nacional import load_inputs


def sha(data): return hashlib.sha256(data).hexdigest()
def canonical(value): return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()
def require(condition, message):
    if not condition: raise ValueError(message)


def contacts(geoms, ids):
    """Scalar geometry predicates over bounding-box candidates, independent of builder."""
    index = STRtree(geoms)
    records = []
    for i, geom in enumerate(geoms):
        for j in sorted(int(j) for j in index.query(geom) if int(j) > i):
            other = geoms[j]
            if not geom.intersects(other): continue
            border = geom.boundary.intersection(other.boundary)
            area = geom.intersection(other).area
            length = border.length
            records.append({'u': ids[i], 'v': ids[j], 'shared_border_m': float(length),
                            'overlap_m2': float(area), 'contact_sha256': sha(border.wkb),
                            'kind': 'overlap' if area > 0 else 'linear' if length > 0 else 'point'})
    return records


def components(ids, edges):
    adjacency = {uid: set() for uid in ids}
    for edge in edges:
        u, v = edge['u'], edge['v']
        require(u != v and u in adjacency and v in adjacency, 'INVALID_EDGE')
        adjacency[u].add(v); adjacency[v].add(u)
    unseen = set(ids); result = []
    while unseen:
        seed = min(unseen); todo = [seed]; members = []
        unseen.remove(seed)
        while todo:
            uid = todo.pop(); members.append(uid)
            for neighbor in sorted(adjacency[uid]):
                if neighbor in unseen: unseen.remove(neighbor); todo.append(neighbor)
        result.append(sorted(members))
    return sorted(result)


def audit(parts_dir, product, output):
    frame, contract, evidence = load_inputs(parts_dir)
    raw_manifest = (product / 'manifest.json').read_bytes()
    manifest = json.loads(raw_manifest)
    identity = manifest.pop('identity_sha256')
    require(sha(canonical(manifest)) == identity, 'MANIFEST_IDENTITY')
    manifest['identity_sha256'] = identity
    require(manifest['evidence'] == evidence, 'SOURCE_OR_CONTRACT_BINDING_MISMATCH')
    require(manifest['generation_authorized'] is False, 'GENERATION_AUTHORIZATION')
    require(manifest['origin_units'] == 52 and manifest['sections'] == 36554 and manifest['population'] == 49128297 and manifest['k'] == 407, 'NATIONAL_COVERAGE')
    artifacts = {}
    for name, record in sorted(manifest['artifacts'].items()):
        data = (product / name).read_bytes()
        decoded = gzip.decompress(data)
        require(sha(data) == record['sha256'] and len(data) == record['bytes'], 'ARTIFACT_BYTES:' + name)
        require(sha(decoded) == record['canonical_json_sha256'], 'ARTIFACT_CONTENT:' + name)
        value = json.loads(decoded)
        require(decoded == canonical(value) + b'\n', 'ARTIFACT_CANONICAL:' + name)
        require(data == gzip.compress(decoded, mtime=0), 'ARTIFACT_GZIP:' + name)
        artifacts[name] = value
    units = []; all_ids = set(); all_edges = 0; all_parts = 0
    geometry_hash = evidence['source_binding']['geometry']['sha256']
    for code, group in frame.groupby('CPRO', sort=True):
        group = group.sort_values('CUSEC').reset_index(drop=True)
        original = {str(row.CUSEC): row for row in group.itertuples()}
        ids = group.CUSEC.tolist(); geoms = group.geometry.tolist()
        value = artifacts['unidades/' + str(code) + '.json.gz']
        require(value['summary']['generation_authorized'] is False, 'UNIT_GENERATION')
        require(value['run_binding'] == manifest['run_binding'], 'UNIT_RUN_BINDING')
        nodes = value['nodes']
        require([n['id'] for n in nodes] == ids, 'NODE_COVERAGE:' + code)
        for node in nodes:
            row = original[node['id']]
            require(node['id'] not in all_ids, 'DUPLICATE_NODE'); all_ids.add(node['id'])
            require(node['geometry_sha256'] == sha(row.geometry.wkb) and node['source_geometry_sha256'] == geometry_hash, 'NODE_GEOMETRY')
            require(node['pop'] == int(row.POB_2025), 'NODE_POPULATION')
            for field in group.columns:
                if field == 'geometry': continue
                expected = getattr(row, field)
                require(node[field] == expected, 'NODE_ADMIN:' + field)
        raw = contacts(geoms, ids)
        edges = [{**r, 'edge_type': 'geometric'} for r in raw if r['kind'] == 'linear']
        require(edges == value['edges'], 'EDGE_MISSING_OR_EXTRA:' + code)
        require([r for r in raw if r['kind'] == 'point'] == value['point_contacts'], 'POINT_CONTACTS:' + code)
        require([r for r in raw if r['kind'] == 'overlap'] == value['overlaps'], 'OVERLAP_CONTACTS:' + code)
        comps = components(ids, edges)
        expected_components = [{'id': members[0], 'sections': members, 'population': sum(int(original[u].POB_2025) for u in members)} for members in comps]
        require(expected_components == value['physical_components'], 'SECTION_COMPONENTS:' + code)
        comp_map = {u: members[0] for members in comps for u in members}
        part_ids = []; part_geoms = []; owners = {}
        for uid, geom in zip(ids, geoms):
            parts = sorted(list(geom.geoms) if geom.geom_type == 'MultiPolygon' else [geom], key=lambda p: p.wkb)
            for i, part in enumerate(parts):
                pid = f'{uid}:p{i:04d}'; part_ids.append(pid); part_geoms.append(part); owners[pid] = uid
        part_raw = contacts(part_geoms, part_ids)
        part_edges = [r for r in part_raw if r['kind'] == 'linear']
        part_comps = components(part_ids, part_edges)
        owner_components = {uid: set() for uid in ids}
        for members in part_comps:
            for pid in members: owner_components[owners[pid]].add(members[0])
        expected_parts = []
        for members in part_comps:
            sections = sorted({owners[p] for p in members})
            unresolved = [u for u in sections if len(owner_components[u]) > 1]
            known = sum(int(original[u].POB_2025) for u in sections if len(owner_components[u]) == 1)
            expected_parts.append({'id': members[0], 'parts': members, 'sections': sections, 'population_exact': None if unresolved else known, 'population_known': known, 'population_unallocatable_sections': unresolved})
        require(expected_parts == value['polygon_part_components'], 'PART_COMPONENTS:' + code)
        for node in nodes:
            require(node['physical_component'] == comp_map[node['id']] and node['physical_part_components'] == sorted(owner_components[node['id']]), 'NODE_COMPONENTS')
        require([m['CUMUN'] for m in value['municipalities']] == sorted(set(group.CUMUN)), 'MUNICIPAL_COVERAGE:' + code)
        for municipality in value['municipalities']:
            members = sorted(uid for uid in ids if original[uid].CUMUN == municipality['CUMUN'])
            subset = set(members)
            mc = components(members, [r for r in edges if r['u'] in subset and r['v'] in subset])
            pids = [p for p in part_ids if owners[p] in subset]; pset = set(pids)
            pc = components(pids, [r for r in part_edges if r['u'] in pset and r['v'] in pset])
            require(mc == municipality['component_members'] and pc == municipality['part_component_members'], 'MUNICIPAL_COMPONENTS:' + municipality['CUMUN'])
        require(all(e['u'][:2] == code == e['v'][:2] for e in edges), 'INTERPROVINCIAL_EDGE')
        require(len(edges) == len({(e['u'], e['v']) for e in edges}), 'DUPLICATE_EDGE')
        summary = value['summary']
        require(summary['sections'] == len(ids) and summary['population'] == int(group.POB_2025.sum()) and summary['k'] == max(1, (int(group.POB_2025.sum()) + 60000) // 120000), 'UNIT_QUOTA_POPULATION:' + code)
        require(summary['edges'] == len(edges) and summary['section_graph_components'] == len(comps) and summary['physical_part_components'] == len(part_comps), 'UNIT_SUMMARY_GRAPH:' + code)
        all_edges += len(edges); all_parts += len(part_comps)
        units.append({'CPRO': code, 'sections': len(ids), 'edges': len(edges), 'section_components': len(comps), 'physical_part_components': len(part_comps), 'status': 'PASS'})
        print('INDEPENDENT_AUDIT ' + code, flush=True)
    # Independent audit of excluded province-boundary contacts, without graph admission.
    geoms = frame.geometry.tolist(); ids = frame.CUSEC.tolist(); codes = frame.CPRO.tolist()
    index = STRtree(geoms); cross = []
    for i, geom in enumerate(geoms):
        for j in sorted(int(j) for j in index.query(geom) if int(j) > i and codes[int(j)] != codes[i]):
            other = geoms[j]
            if not geom.intersects(other): continue
            border = geom.boundary.intersection(other.boundary)
            cross.append({'u': ids[i], 'v': ids[j], 'CPRO_u': codes[i], 'CPRO_v': codes[j],
                          'shared_border_m': float(border.length), 'overlap_m2': float(geom.intersection(other).area),
                          'contact_sha256': sha(border.wkb), 'excluded_from_graph': True})
    require(cross == artifacts['contactos_interprovinciales.json.gz'], 'EXCLUDED_PROVINCE_CONTACTS')
    require(all_edges == manifest['edges'] and all_parts == manifest['physical_part_components'], 'TOTAL_GRAPH_MISMATCH')
    result = {'schema': 'ddd.congress-topology-independent-audit/1.0', 'manifest_sha256': sha(raw_manifest), 'manifest_identity_sha256': identity,
              'verifier_sha256': sha(Path(__file__).read_bytes()), 'source_binding': evidence['source_binding'], 'units': units,
              'sections': len(all_ids), 'edges': all_edges, 'physical_part_components': all_parts,
              'checks': {'all_scalar_original_contacts': 'PASS', 'part_components_population_not_invented': 'PASS', 'all_artifact_hashes_canonical_gzip': 'PASS', 'official_node_attributes': 'PASS', 'municipal_induced_components': 'PASS', 'excluded_province_boundary_contacts': 'PASS', 'no_extra_missing_or_point_edges': 'PASS', 'source_edition_hash_binding': 'PASS'},
              'generation_authorized': False, 'status': 'PASS'}
    output.parent.mkdir(parents=True, exist_ok=True); output.write_bytes(canonical(result) + b'\n')
    return result


def main():
    parser = argparse.ArgumentParser(description='Auditoría independiente original N08, sin generación')
    parser.add_argument('--parts-dir', type=Path, required=True)
    parser.add_argument('--product', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); audit(args.parts_dir, args.product, args.output)
if __name__ == '__main__': main()
