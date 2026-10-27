#!/usr/bin/env python3
"""Versión 1.0.0; nombre acreditación Cantabria N08; fecha 2026-10-12.
Alcance: diagnóstico aislado; estado candidato. Cambio: contraste independiente.
Motivo: enclave, multipartes y vacíos; origen: N08 #251, INE2025, IGN/RCC.
No cambia fuentes, población, grafo, K ni autorización. Sin predecesor.
"""
from __future__ import annotations
import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import shapely
from shapely.geometry import shape
from shapely.ops import transform
from pyproj import Transformer
from herramientas.preflight_topologico_nacional import load_inputs

DOSSIER = ROOT / 'docs/ESTUDIOS/N08_CANTABRIA_ACREDITACION_20261012'
PRODUCT = ROOT / 'docs/ESTUDIOS/N08_TOPOLOGIA_NACIONAL_20251012/producto/unidades/39.json.gz'
TARGETS = {'3910101001', '3903503001', '3906101003', '3907504011'}
GRIDS = (.0001, .001, .01, .1, 1.)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encoded(obj):
    return (json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def checked(path, expected):
    data = path.read_bytes()
    if sha(data) != expected:
        raise ValueError(f'SHA-256 incompatible: {path}')
    return data


def validate_sections(sections, product):
    nodes = {n['CUSEC']: n for n in product['nodes']}
    if len(sections) != 458 or len({s['CUSEC'] for s in sections}) != 458:
        raise ValueError('Cobertura Cantabria incompatible')
    if set(nodes) != {s['CUSEC'] for s in sections}:
        raise ValueError('Identidad CUSEC incompatible')
    for s in sections:
        n = nodes[s['CUSEC']]
        if s['CUMUN'] != n['CUMUN'] or s['pop'] != n['pop']:
            raise ValueError('Identidad administrativa o población incompatible')
    for s in sections:
        if sha(bytes.fromhex(s['wkb_hex'])) != nodes[s['CUSEC']]['geometry_sha256']:
            raise ValueError('Geometría incompatible')
    if sum(s['pop'] for s in sections) != 593623:
        raise ValueError('Población Cantabria incompatible')


def extract(parts_dir):
    frame, _, evidence = load_inputs(parts_dir)
    f = frame.loc[frame.CPRO == '39'].sort_values('CUSEC')
    sections = [{'CUSEC': r.CUSEC, 'CUMUN': r.CUMUN, 'NMUN': r.NMUN,
                 'pop': int(r.POB_2025), 'wkb_hex': r.geometry.wkb_hex} for r in f.itertuples()]
    return sections, evidence


def classify_void(h):
    # Nominal decisions from the independent evidence dossier, bound to full original hashes.
    known = {v['boundary_sha256'] for v in json.loads(gzip.decompress(PRODUCT.read_bytes()))['enclosed_voids']}
    if h not in known:
        raise ValueError('Vacío no acreditado en producto #251')
    if h == '1ea675806a11cc3a5a5bf78b9c3587f66c8034ae10e252bf27cefd1035e33504':
        return 'TERRITORIO_COMUNAL_CAMPOO_CABUERNIGA', 'PASS_NATURALEZA_NO_IDENTIDAD_EXACTA_2025'
    if h in {'473a25113f91abeacbb0e08c1d2c769abedc6e113fa2dfbeea2e21e207afb13f', 'e8e4bbf4269d759e8729f4ef3ceb8c5c7ee1f67867b9cc6db14f5d212c1deaba'}:
        return 'ENCLAVE_PALENTINO_POMAR_DE_VALDIVIA', 'PASS_NATURALEZA_NO_IDENTIDAD_EXACTA_2025'
    return 'MICROVACIO_ANALISIS_PRECISION', 'DIAGNOSTIC_ORIGEN_NO_ACREDITADO'


def run(parts_dir, output, sources=DOSSIER / 'fuentes_cartograficas'):
    # The immutable #251 ledger binds every original geometry and population.
    product_bytes = PRODUCT.read_bytes()
    product = json.loads(gzip.decompress(product_bytes))
    manifest = json.loads((PRODUCT.parents[1] / 'manifest.json').read_bytes())
    # Manifest format differs from this focused product; verify its file ledger.
    ledger = manifest['artifacts']
    rel = 'unidades/39.json.gz'
    expected = ledger[rel]['sha256'] if isinstance(ledger, dict) else next(r['sha256'] for r in ledger if r['path'] == rel)
    checked(PRODUCT, expected)
    expected_summary = {'sections': 458, 'municipalities': 102, 'population': 593623, 'k': 5, 'edges': 1208, 'physical_part_components': 5, 'generation_authorized': False}
    if any(product['summary'][k] != v for k, v in expected_summary.items()) or len(product['edges']) != 1208 or len(product['polygon_part_components']) != 5:
        raise ValueError('Resumen Cantabria incompatible')
    if manifest['k'] != 407 or manifest['generation_authorized'] is not False:
        raise ValueError('Contrato nacional incompatible')
    sections, evidence = extract(parts_dir)
    validate_sections(sections, product)
    if evidence['source_binding']['geometry']['edition'] != 2025 or evidence['source_binding']['population']['edition'] != 2025:
        raise ValueError('Edición incompatible')
    geoms = {s['CUSEC']: shapely.from_wkb(bytes.fromhex(s['wkb_hex'])) for s in sections}
    lonlat = Transformer.from_crs(25830, 4326, always_xy=True).transform
    project = Transformer.from_crs(4326, 25830, always_xy=True).transform
    external, names, receipts = {}, [], []
    for rp in sorted(sources.glob('*.receipt.json')):
        receipt = json.loads(rp.read_bytes())
        filename = receipt.get('file') or rp.name.replace('.receipt.json', '.json')
        source = sources / filename
        raw = checked(source, receipt['sha256'])
        receipts.append({'file': filename, 'sha256': sha(raw), 'url': receipt['url']})
        if source.suffix != '.json':
            continue
        obj = json.loads(raw)
        for f in obj.get('features', []):
            if not f.get('geometry'):
                continue
            props = f['properties']; g = transform(project, shape(f['geometry']))
            if 'nationalcode' in props:
                external[props['nationalcode']] = (g, props, filename)
            elif 'etiqueta' in props:
                names.append((g, props, filename))
    province = external['34063900000'][0]
    parts = []
    for s in sections:
        if s['CUSEC'] not in TARGETS:
            continue
        gs = sorted(list(geoms[s['CUSEC']].geoms) if geoms[s['CUSEC']].geom_type == 'MultiPolygon' else [geoms[s['CUSEC']]], key=lambda g: g.wkb)
        for i, g in enumerate(gs):
            point = g.representative_point(); xy = lonlat(point.x, point.y)
            contacts = []
            for uid, other in geoms.items():
                if uid == s['CUSEC'] or not g.intersects(other):
                    continue
                overlap = g.intersection(other).area
                linear = g.boundary.intersection(other.boundary).length
                contacts.append({'CUSEC': uid, 'overlap_m2': overlap, 'shared_border_m': linear,
                                 'kind': 'overlap' if overlap > 0 else 'linear' if linear > 0 else 'point'})
            mun = external['340639' + s['CUMUN']][0]
            munparts = list(mun.geoms) if mun.geom_type == 'MultiPolygon' else [mun]
            external_part_matches = [{'external_part_wkb_sha256': sha(mp.wkb), 'coverage_ratio_raw': g.intersection(mp).area / g.area,
                                      'names_inside_external_part': [np['etiqueta'] for ng, np, fn in names if mp.covers(ng)]}
                                     for mp in munparts if g.intersection(mp).area > 0]
            matching_names = [{'name': p['etiqueta'], 'type': p.get('tipo'), 'properties': p, 'source': fn} for ng, p, fn in names if g.covers(ng)]
            parts.append({'part_id': f"{s['CUSEC']}:p{i:04d}", 'CUSEC': s['CUSEC'], 'CUMUN': s['CUMUN'],
                          'municipality': s['NMUN'], 'population_section': s['pop'],
                          'population_part': s['pop'] if len(gs) == 1 else None,
                          'population_part_status': 'PASS' if len(gs) == 1 else 'NOT_EVIDENCED',
                          'area_m2': g.area, 'bounds': list(g.bounds), 'lon': xy[0], 'lat': xy[1],
                          'wkb_sha256': sha(g.wkb), 'wkb_hex': g.wkb_hex, 'contacts': contacts,
                          'distance_to_other_same_section_parts_m': min((g.distance(o) for o in gs if o is not g), default=None),
                          'ign_municipal_coverage_ratio_raw': g.intersection(mun).area / g.area,
                          'official_named_points_inside': matching_names, 'external_part_matches': external_part_matches})
    union = shapely.union_all(list(geoms.values()))
    polygons = list(union.geoms) if union.geom_type == 'MultiPolygon' else [union]
    holes = sorted([shapely.Polygon(r) for p in polygons for r in p.interiors], key=lambda g: sha(g.wkb))
    if {sha(g.wkb) for g in holes} != {v['boundary_sha256'] for v in product['enclosed_voids']}:
        raise ValueError('Vacíos no reproducen #251')
    rounded = {str(grid): shapely.union_all(shapely.set_precision(list(geoms.values()), grid)) for grid in GRIDS}
    voids = []
    for g in holes:
        h = sha(g.wkb); point = g.representative_point(); xy = lonlat(point.x, point.y)
        matches = []
        for code, (e, props, fn) in sorted(external.items()):
            if props.get('nationallevelname') != 'Municipio' or not e.intersects(g):
                continue
            a = e.intersection(g).area
            if a > 0:
                matches.append({'nationalcode': code, 'name': props['nameunit'], 'coverage_ratio_raw': a / g.area, 'source': fn})
        classification, status = classify_void(h)
        bordering = [s['CUSEC'] for s in sections if g.boundary.intersects(geoms[s['CUSEC']])]
        voids.append({'id': 'V39-' + h[:16], 'wkb_sha256': h, 'wkb_hex': g.wkb_hex, 'area_m2': g.area,
                      'lon': xy[0], 'lat': xy[1], 'bounds': list(g.bounds), 'classification': classification, 'status': status,
                      'population': None, 'population_status': 'NOT_EVIDENCED',
                      'ign_cantabria_coverage_ratio_raw': g.intersection(province).area / g.area,
                      'official_municipal_matches': matches, 'bordering_CUSEC': bordering,
                      'bordering_CUMUN': sorted({u[:5] for u in bordering}),
                      'official_named_points_inside': [p['etiqueta'] for ng, p, fn in names if g.covers(ng)],
                      'uncovered_original_area_by_grid_m2': {grid: g.difference(u).area for grid, u in rounded.items()}})
    overlaps = []
    for row in product['overlaps']:
        a, b = geoms[row['u']], geoms[row['v']]; overlap = a.intersection(b)
        if overlap.area != row['overlap_m2']:
            raise ValueError('Solapamiento no reproduce #251')
        nearest = min(voids, key=lambda v: overlap.distance(shapely.from_wkb(bytes.fromhex(v['wkb_hex']))))
        overlaps.append({**row, 'geometry_sha256': sha(overlap.wkb), 'nearest_void': nearest['id'],
                         'distance_to_nearest_void_m': overlap.distance(shapely.from_wkb(bytes.fromhex(nearest['wkb_hex']))),
                         'area_by_grid_m2': {str(grid): shapely.set_precision(a, grid).intersection(shapely.set_precision(b, grid)).area for grid in GRIDS}})
    sensitivity = []
    for grid, u in rounded.items():
        ps = list(u.geoms) if u.geom_type == 'MultiPolygon' else [u]
        hs = [shapely.Polygon(r) for p in ps for r in p.interiors]
        sensitivity.append({'grid_m': float(grid), 'holes': len(hs), 'hole_area_m2': sum(g.area for g in hs)})
    valley = geoms['3910101001']; ign_valley = external['34063939101'][0]
    result = {'version': '1.0.0', 'mode': 'DIAGNOSTIC_ONLY', 'source_evidence': evidence,
              'product_39_sha256': sha(product_bytes), 'external_sources': receipts,
              'external_crs': 'CRS84 longitude/latitude -> EPSG:25830, always_xy',
              'external_edition': 'IGN/RCC metadata revision2026-02-12, metadata2026-02-23; snapshot not identity2025',
              'external_accuracy': 'RCC heterogeneous; general uncertainty about40m, scale1:25000; not an electoral tolerance',
              'invariants': {'sections': 458, 'municipalities': 102, 'population': 593623, 'K': 5, 'K_national': 407,
                             'edges': 1208, 'part_components': 5, 'generation_authorized': False, 'physical_edges_created': 0},
              'parts': [{k: v for k, v in p.items() if k != 'wkb_hex'} for p in parts],
              'voids': [{k: v for k, v in p.items() if k != 'wkb_hex'} for p in voids],
              'overlaps': overlaps, 'sensitivity': sensitivity,
              'precision_policy': 'NOT_APPROVED; analytic grids span original4decimal coordinates to1m; never used for physical graph',
              'valley': {'original_ign_symmetric_difference_m2': valley.symmetric_difference(ign_valley).area,
                         'ign_own_valley_bizkaia_overlap_m2': ign_valley.intersection(external['34164800000'][0]).area,
                         'original_distance_to_main_cantabria_m': valley.distance(shapely.union_all([g for uid, g in geoms.items() if uid != '3910101001']))},
              'factibility': 'BLOCKED_NO_PARTITION_EXECUTED', 'districts_created': 0}
    output.mkdir(parents=True, exist_ok=True)
    (output / 'RESULTADOS.json').write_bytes(encoded(result))
    (output / 'GEOMETRIAS.json.gz').write_bytes(gzip.compress(encoded({'crs': 'EPSG:25830', 'parts': parts, 'voids': voids}), mtime=0))
    with (output / 'VACIOS_28.csv').open('w', newline='') as f:
        fields = ['id', 'wkb_sha256', 'area_m2', 'lon', 'lat', 'classification', 'status', 'ign_cantabria_coverage_ratio_raw', 'bordering_CUMUN', 'official_municipal_matches', 'official_named_points_inside', 'uncovered_original_area_by_grid_m2']
        writer = csv.DictWriter(f, fields); writer.writeheader()
        for v in voids:
            writer.writerow({k: json.dumps(v[k], ensure_ascii=False, sort_keys=True) if isinstance(v[k], (list, dict)) else v[k] for k in fields})
    with (output / 'SOLAPAMIENTOS_30.csv').open('w', newline='') as f:
        fields = list(overlaps[0]); writer = csv.DictWriter(f, fields); writer.writeheader()
        for row in overlaps:
            writer.writerow({k: json.dumps(v, sort_keys=True) if isinstance(v, dict) else v for k, v in row.items()})
    return result


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--parts-dir', type=Path, required=True)
    ap.add_argument('--output', type=Path, default=DOSSIER)
    args = ap.parse_args()
    res = run(args.parts_dir, args.output)
    print(json.dumps({'parts': len(res['parts']), 'voids': len(res['voids']), 'overlaps': len(res['overlaps']), 'invariants': res['invariants']}, sort_keys=True))
