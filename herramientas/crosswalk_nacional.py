#!/usr/bin/env python3
"""Versión 1.0.0; nombre: crosswalk censal nacional; fecha: 2026-10-11.
Alcance: N07, correspondencia administrativa de la edición INE 2025.
Estado: candidato local, CI_PENDIENTE. Cambios: validador y materialización.
Motivo: acreditar cobertura 52 sin extrapolar ediciones. Origen: nuevo.
"""
from __future__ import annotations
import argparse
from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from herramientas.inventariar_cartografia_historica import (
    SECTIONING_2025_BASELINE_SHA256, sectioning_reference,
)
PROVINCES = {f'{i:02d}' for i in range(1, 53)}
FIELDS = ('CUSEC', 'CUMUN', 'CPRO', 'CMUN', 'CDIS', 'CSEC')


def validate_rows(universe, crosswalk, expected_counts):
    """Exige igualdad de conjuntos y asignaciones, además de recuentos y claves."""
    def index(rows):
        result = {}
        counts = Counter()
        for row in rows:
            if any(not isinstance(row.get(k), str) for k in FIELDS):
                raise ValueError('IDENTITY_TYPE')
            sizes = dict(CUSEC=10, CUMUN=5, CPRO=2, CMUN=3, CDIS=2, CSEC=3)
            if any(len(row[k]) != n or not row[k].isascii() or not row[k].isdigit()
                   for k, n in sizes.items()):
                raise ValueError('IDENTITY_FORMAT')
            if row['CPRO'] not in PROVINCES:
                raise ValueError('PROVINCE_INVALID')
            if row['CUMUN'] != row['CPRO'] + row['CMUN'] or row['CUSEC'] != row['CUMUN'] + row['CDIS'] + row['CSEC']:
                raise ValueError('IDENTITY_CONTRADICTION')
            if row['CPRO'] in {'51', '52'} and row['CMUN'] != '001':
                raise ValueError('CITY_MUNICIPALITY_INVALID')
            if row['CUSEC'] in result:
                raise ValueError('DUPLICATE_SECTION')
            result[row['CUSEC']] = tuple(row[k] for k in FIELDS)
            counts[row['CPRO']] += 1
        if set(counts) != PROVINCES or dict(counts) != expected_counts:
            raise ValueError('COVERAGE_OR_COUNTS')
        return result
    source = index(universe)
    target = index(crosswalk)
    if source != target:
        raise ValueError('LOSS_EXTRA_OR_REASSIGNMENT')
    return {'status': 'PASS', 'unit_count': len(source), 'unique_ids': len(target),
            'province_counts': expected_counts, 'losses': 0, 'extras': 0, 'duplicates': 0,
            'assignment': 'CPRO corroborated by CUMUN and CUSEC in same source edition',
            'ceuta': expected_counts['51'], 'melilla': expected_counts['52']}


def materialize(source, output):
    import geopandas as gpd
    import shapely
    from shapely.validation import explain_validity
    reference = sectioning_reference(source, SECTIONING_2025_BASELINE_SHA256)
    protected = json.loads((ROOT/'docs/ESTUDIOS/cartografia_nacional_20261008/referencia_seccionado_2025.json').read_text())
    if reference['province_counts'] != protected['province_counts'] or reference['unit_count'] != protected['unit_count']:
        raise ValueError('BASELINE_COUNTS_MISMATCH')
    with zipfile.ZipFile(source) as archive:
        shapes = [n for n in archive.namelist() if n.lower().endswith('.shp')]
        if len(shapes) != 1:
            raise ValueError('SINGLE_SECTION_LAYER_REQUIRED')
    # GDAL ZIP lookup varies for the accented directory; use verified members.
    with tempfile.TemporaryDirectory(prefix='ddd-n07-') as directory:
        with zipfile.ZipFile(source) as archive:
            stem = shapes[0].rsplit('.', 1)[0]
            for name in archive.namelist():
                if name.rsplit('.', 1)[0] == stem:
                    suffix = name.rsplit('.', 1)[1].lower()
                    Path(directory, 'sections.' + suffix).write_bytes(archive.read(name))
        frame = gpd.read_file(Path(directory, 'sections.shp'))
    if frame.crs is None or frame.crs.to_epsg() != 25830:
        raise ValueError('CRS_MISMATCH')
    rows = frame[list(FIELDS)].to_dict('records')
    rows.sort(key=lambda r: r['CUSEC'])
    report = validate_rows(rows, rows, protected['province_counts'])
    issues = []
    geometry_hashes = {}
    for _, row in frame.iterrows():
        geom = row.geometry
        if geom is None or geom.is_empty:
            raise ValueError('GEOMETRY_MISSING')
        geometry_hashes[row.CUSEC] = hashlib.sha256(geom.wkb).hexdigest()
        if not geom.is_valid:
            issues.append({'CUSEC': row.CUSEC, 'reason': explain_validity(geom)})
    report.update(schema='ddd.national-crosswalk/1.0', edition=2025,
                  source_sha256=reference['file_sha256'], crs=reference['crs'],
                  geometry_invalid=issues, geometry_repaired=False,
                  topology_scope='Administrative membership only; no provincial overlay or adjacency certification',
                  generation_authorized=False, historical_edition_equivalence=False,
                  software={'geopandas': gpd.__version__, 'shapely': shapely.__version__, 'geos': shapely.geos_version_string})
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator='\n')
    writer.writeheader(); writer.writerows(rows)
    payload = stream.getvalue().encode()
    # Re-read the exported artifact and verify against the original universe.
    validate_rows(frame[list(FIELDS)].to_dict('records'), list(csv.DictReader(io.StringIO(payload.decode()))), protected['province_counts'])
    report['crosswalk_sha256'] = hashlib.sha256(payload).hexdigest()
    report['geometry_identity_sha256'] = hashlib.sha256(json.dumps(geometry_hashes, sort_keys=True).encode()).hexdigest()
    with zipfile.ZipFile(source) as archive:
        report['source_members'] = {n: hashlib.sha256(archive.read(n)).hexdigest() for n in sorted(archive.namelist()) if not n.endswith('/')}
    output = Path(output); output.mkdir(parents=True, exist_ok=False)
    (output/'crosswalk.csv').write_bytes(payload)
    (output/'evidence.json').write_text(json.dumps(report, sort_keys=True, indent=2)+'\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path); parser.add_argument('output', type=Path)
    args = parser.parse_args()
    report = materialize(args.source, args.output)
    print(json.dumps({k: report[k] for k in ('status', 'unit_count', 'ceuta', 'melilla', 'crosswalk_sha256')}))
