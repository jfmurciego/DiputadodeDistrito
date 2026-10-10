#!/usr/bin/env python3
"""Recuperación F10 v1.0.0; 2026-10-10; candidato local.

Alcance: artefactos originales, candidatos v3, inventarios completos y receipts.
Cambios: comprobación offline reproducible; motivo: distinguir bytes y metadata.
Origen: main@579ab82e84aadba778b0fe7d138ea96b66457e1e; predecesor: ninguno.
No adquiere fuentes ni registra/promueve productos; salida sólo si se solicita.
"""
import argparse
import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from herramientas.almacen_fuentes_local import inspect_zip
from herramientas.compatibilidad_poblacion_seccionado import REPORT_NAME, validate_compatibility_package
from herramientas.consumir_par_fuentes_legislatura import PreparedPairExecutionBlock, validate_territorial_receipt
from herramientas.identidad_fuentes_legislatura import territorial_identity

def load(path):
    return json.loads(path.read_text())

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def verify():
    inventories = load(HERE / 'inventarios-remotos.json')['runs']
    all_artifacts = {}
    for run in inventories:
        assert not run.get('error'), run['run_id']
        pages = run['pages']
        artifacts = [a for page in pages for a in page['artifacts']]
        assert pages[0]['total_count'] == len(artifacts), run['run_id']
        assert len({a['id'] for a in artifacts}) == len(artifacts), run['run_id']
        for a in artifacts:
            assert a['workflow_run']['id'] == run['run_id']
            all_artifacts[a['id']] = a
    selected = load(HERE / 'artefactos-seleccionados.json')['artifacts']
    downloads = load(HERE / 'descargas-conector.json')['downloads']
    assert {a['id'] for a in selected} == {d['artifact_id'] for d in downloads}
    for a in selected:
        assert a == all_artifacts[a['id']], a['id']
        assert not a['expired'], a['id']
    for d in downloads:
        assert d['backend_status'] == 'FILE_REFERENCE_RETURNED' and d['file_id']
        assert d['local_bytes_verified'] is False

    prior = ROOT / 'docs/AUDITORIAS/F04_F10_20261009'
    historical = load(prior / 'artifact-metadata.json')
    rows = []
    verified_artifacts = set()
    for original in historical:
        territory = original['territory']
        recovery = load(prior / territory / 'recovery-receipt.json')
        remote = all_artifacts[original['id']]
        assert remote['workflow_run']['head_sha'] == recovery['source_commit']
        assert remote['name'] == recovery['artifact_name']
        artifact_path = prior / 'originales' / f"artifact-{remote['id']}.zip"
        raw = artifact_path.read_bytes()
        assert sha(raw) == remote['digest'].removeprefix('sha256:') == recovery['artifact_sha256']
        assert len(raw) == remote['size_in_bytes']
        with zipfile.ZipFile(io.BytesIO(raw)) as outer:
            inspect_zip(outer)
            manifest = json.loads(outer.read('manifest.json'))
            package = outer.read('prepared_sources.zip')
        assert manifest['territory_id'] == territory
        assert str(manifest['edition']) == '2025'
        assert manifest['sha256'] == sha(package) == recovery['package_sha256']
        with zipfile.ZipFile(io.BytesIO(package)) as inner:
            inspect_zip(inner)
            assert REPORT_NAME not in inner.namelist()
        candidate = load(prior / territory / 'derived-receipt-v3.json')
        assert candidate['schema'] == 'ddd.local-derived-source-receipt/1.0'
        candidate_path = prior / territory / 'candidato-v3'
        candidate_raw = (candidate_path / 'prepared_sources.zip').read_bytes()
        assert sha(candidate_raw) == candidate['package_sha256'] != sha(package)
        report, report_sha, reasons = validate_compatibility_package(candidate_path,
            territory_id=territory, edition='2025', population_year=2025, section_year=2025)
        assert not reasons and report['decision'] == 'READY', (territory, reasons)
        assert report_sha == candidate['compatibility_report_sha256']
        identity = territorial_identity(**{k: candidate[k] for k in (
            'territory_id', 'edition', 'population_year', 'section_year',
            'package_sha256', 'compatibility_identity_sha256')})
        assert report['compatibility_identity_sha256'] == identity['compatibility_identity_sha256']
        assert identity['territorial_identity_sha256'] == candidate['territorial_identity_sha256']
        try:
            validate_territorial_receipt(root_dir=ROOT, territory=territory, edition='2025')
        except PreparedPairExecutionBlock as exc:
            cause = str(exc)
        else:
            raise AssertionError(f'Promoción inesperada: {territory}')
        verified_artifacts.add(remote['id'])
        rows.append({'territory_id': territory, 'state': 'BLOCKED', 'canonical_cause': cause,
            'run_id': remote['workflow_run']['id'], 'artifact_id': remote['id'],
            'source_commit': recovery['source_commit'], 'artifact_created_at': remote['created_at'],
            'artifact_sha256': sha(raw), 'artifact_bytes': len(raw),
            'original_package_sha256': sha(package), 'original_report_present': False,
            'candidate_package_sha256': sha(candidate_raw), 'candidate_report_sha256': report_sha,
            'compatibility_identity_sha256': identity['compatibility_identity_sha256'],
            'territorial_identity_sha256': identity['territorial_identity_sha256'],
            'candidate_run_accredited': False, 'production_promotion': 'NONE'})

    historical_pass = load(prior / 'continuacion/evidencia-previa-reutilizada.json')['rows']
    assert len(historical_pass) == 14
    for row in historical_pass:
        _, receipt = validate_territorial_receipt(root_dir=ROOT, territory=row['territory_id'], edition='2025')
        assert receipt['package_sha256'] == row['package_sha256']
        assert receipt['territorial_identity_sha256'] == row['territorial_identity_sha256']
        assert row['controls']['F03_effective_consumer'] == 'PASS'
    assert len(rows) == 5
    return {'version': '1.0.0', 'date': '2026-10-10', 'scope': 'recuperación verificable F10',
        'origin': '579ab82e84aadba778b0fe7d138ea96b66457e1e', 'predecessor': None,
        'changes': 'nueva verificación', 'reason': 'no acreditar metadata como bytes',
        'state': 'BLOCKED_CON_ACCION_EJECUTABLE', 'complete_remote_inventories': len(inventories),
        'selected_artifacts': len(selected), 'backend_download_references': len(downloads),
        'artifact_bytes_verified': len(verified_artifacts),
        'unverified_artifact_ids': sorted({a['id'] for a in selected} - verified_artifacts),
        'historical_PASS_preserved': 14, 'historical_products_reexecuted': False, 'rows': rows}

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', type=Path)
    ap.add_argument('--compare', type=Path)
    args = ap.parse_args()
    value = verify()
    if args.compare:
        assert value == load(args.compare), 'Resultado no reproducible'
    if args.output:
        args.output.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    print('PASS: inventarios completos; 5 artefactos auténticos; 14 PASS históricos y 5 BLOCKED preservados')
