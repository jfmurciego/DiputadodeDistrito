#!/usr/bin/env python3
"""Verificación F10 v1.0.0; 2026-10-10; candidato local.

Alcance: bytes y receipts existentes de cinco territorios; sin escritura productiva.
Cambios: expediente reproducible; motivo: distinguir linaje real de derivación local.
Origen: c83f6e3f5b9d25ec12c0124e42b372e7d838031e / #179; predecesor: ninguno.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from herramientas.almacen_fuentes_local import inspect_zip, require
from herramientas.compatibilidad_poblacion_seccionado import REPORT_NAME, validate_compatibility_package
from herramientas.consumir_par_fuentes_legislatura import PreparedPairExecutionBlock, validate_territorial_receipt
from herramientas.identidad_fuentes_legislatura import territorial_identity

PRIOR = Path('docs/AUDITORIAS/F04_F10_20261009')
HERE = Path('docs/AUDITORIAS/F10_20261010')
TERRITORIES = ('andalucia', 'comunidad_valenciana', 'extremadura', 'aragon', 'castilla_y_leon')


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def read(path: Path) -> dict:
    return json.loads((ROOT / path).read_text())


def verify() -> dict:
    metadata = {r['territory']: r for r in read(PRIOR / 'artifact-metadata.json')}
    snapshots = {r['run_id']: r for r in read(HERE / 'remote-artifacts.json')['runs']}
    rows = []
    for territory in TERRITORIES:
        recovery_path = PRIOR / territory / 'recovery-receipt.json'
        recovery = read(recovery_path)
        historical = metadata[territory]
        snapshot = snapshots[recovery['run_id']]
        response = snapshot['response']
        artifacts = response['artifacts']
        require(response['total_count'] == len(artifacts), 'inventario remoto incompleto')
        matches = [a for a in artifacts if a['name'] == recovery['artifact_name']]
        require(len(matches) == 1, 'identidad de artefacto ambigua o ausente')
        remote = matches[0]
        for key in ('id', 'name', 'size_in_bytes', 'digest', 'workflow_run'):
            require(remote[key] == historical[key], f'metadata histórica contradictoria: {key}')
        require(remote['id'] == recovery['artifact_id'], "F10: evidencia contradictoria: remote['id'] == recovery['artifact_id']")
        require(remote['workflow_run']['id'] == recovery['run_id'], "F10: evidencia contradictoria: remote['workflow_run']['id'] == recovery['run_id']")
        require(remote['workflow_run']['head_sha'] == recovery['source_commit'], "F10: evidencia contradictoria: remote['workflow_run']['head_sha'] == recovery['source_commit']")
        artifact_path = PRIOR / 'originales' / f"artifact-{remote['id']}.zip"
        artifact_raw = (ROOT / artifact_path).read_bytes()
        require(len(artifact_raw) == remote['size_in_bytes'], "F10: evidencia contradictoria: len(artifact_raw) == remote['size_in_bytes']")
        require(sha(artifact_raw) == recovery['artifact_sha256'] == remote['digest'].removeprefix('sha256:'), "F10: evidencia contradictoria: sha(artifact_raw) == recovery['artifact_sha256'] == remote['digest'].removeprefix('sha256:')")
        with zipfile.ZipFile(io.BytesIO(artifact_raw)) as outer:
            inspect_zip(outer)
            require(set(outer.namelist()) == {'manifest.json', 'prepared_sources.zip'}, "F10: evidencia contradictoria: set(outer.namelist()) == {'manifest.json', 'prepared_sources.zip'}")
            manifest_raw = outer.read('manifest.json')
            manifest = json.loads(manifest_raw)
            package_raw = outer.read('prepared_sources.zip')
        require(sha(package_raw) == manifest['sha256'] == recovery['package_sha256'], "F10: evidencia contradictoria: sha(package_raw) == manifest['sha256'] == recovery['package_sha256']")
        require(manifest['territory_id'] == territory, "F10: evidencia contradictoria: manifest['territory_id'] == territory")
        require(str(manifest['edition']) == recovery['edition'], "F10: evidencia contradictoria: str(manifest['edition']) == recovery['edition']")
        require(manifest['path'] == 'prepared_sources.zip', "F10: evidencia contradictoria: manifest['path'] == 'prepared_sources.zip'")
        # El directorio previamente extraído debe contener exactamente los mismos bytes.
        original = PRIOR / territory / 'original'
        require((ROOT / original / 'manifest.json').read_bytes() == manifest_raw, "F10: evidencia contradictoria: (ROOT / original / 'manifest.json').read_bytes() == manifest_raw")
        require((ROOT / original / 'prepared_sources.zip').read_bytes() == package_raw, "F10: evidencia contradictoria: (ROOT / original / 'prepared_sources.zip').read_bytes() == package_raw")
        with zipfile.ZipFile(io.BytesIO(package_raw)) as inner:
            inspect_zip(inner)
            members = inner.namelist()
            has_report = REPORT_NAME in members
        report, report_sha, compatibility_reasons = validate_compatibility_package(
            ROOT / original, territory_id=territory, edition=recovery['edition'],
            population_year=recovery['population_year'], section_year=recovery['section_year'])
        historical_identity = territorial_identity(**{k: recovery[k] for k in (
            'territory_id', 'edition', 'population_year', 'section_year', 'package_sha256')})
        require(historical_identity['territorial_identity_sha256'] == recovery['territorial_identity_sha256'], "F10: evidencia contradictoria: historical_identity['territorial_identity_sha256'] == recovery['territorial_identity_sha256']")
        candidate_path = PRIOR / territory / 'derived-receipt-v3.json'
        candidate = read(candidate_path)
        candidate_package_path = PRIOR / territory / 'candidato-v3/prepared_sources.zip'
        candidate_raw = (ROOT / candidate_package_path).read_bytes()
        require(sha(candidate_raw) == candidate['package_sha256'], "F10: evidencia contradictoria: sha(candidate_raw) == candidate['package_sha256']")
        require(candidate['package_sha256'] != recovery['package_sha256'], "F10: evidencia contradictoria: candidate['package_sha256'] != recovery['package_sha256']")
        with zipfile.ZipFile(io.BytesIO(candidate_raw)) as inner:
            report_raw = inner.read(REPORT_NAME)
        candidate_report = json.loads(report_raw)
        require(sha(report_raw) == candidate['compatibility_report_sha256'], "F10: evidencia contradictoria: sha(report_raw) == candidate['compatibility_report_sha256']")
        require(candidate_report['compatibility_identity_sha256'] == candidate['compatibility_identity_sha256'], "F10: evidencia contradictoria: candidate_report['compatibility_identity_sha256'] == candidate['compatibility_identity_sha256']")
        identity = territorial_identity(**{k: candidate[k] for k in (
            'territory_id', 'edition', 'population_year', 'section_year',
            'package_sha256', 'compatibility_identity_sha256')})
        require(identity['territorial_identity_sha256'] == candidate['territorial_identity_sha256'], "F10: evidencia contradictoria: identity['territorial_identity_sha256'] == candidate['territorial_identity_sha256']")
        try:
            _, receipt = validate_territorial_receipt(root_dir=ROOT, territory=territory, edition='2025')
            durable = {'decision': 'READY', 'identity': receipt['territorial_identity_sha256']}
        except PreparedPairExecutionBlock as exc:
            durable = {'decision': 'BLOCKED', 'reason': str(exc)}
        require(not has_report and not report and not report_sha and compatibility_reasons, 'F10: evidencia contradictoria: not has_report and not report and not report_sha and compatibility_reasons')
        require(durable['decision'] == 'BLOCKED', "F10: evidencia contradictoria: durable['decision'] == 'BLOCKED'")
        rows.append({
            'territory_id': territory, 'decision': 'BLOCKED',
            'run_id': recovery['run_id'], 'source_commit': recovery['source_commit'],
            'run_url': f"https://github.com/jfmurciego/DiputadodeDistrito/actions/runs/{recovery['run_id']}",
            'remote_snapshot': (HERE / 'remote-artifacts.json').as_posix(),
            'remote_inventory_count': response['total_count'], 'remote_inventory_complete': True,
            'artifact_id': remote['id'], 'artifact_name': remote['name'],
            'artifact_path': artifact_path.as_posix(), 'artifact_sha256': sha(artifact_raw),
            'artifact_bytes': len(artifact_raw), 'package_sha256': sha(package_raw),
            'original_members': members, 'compatibility_report_present': has_report,
            'original_compatibility_rejection': compatibility_reasons,
            'historical_identity_sha256_without_compatibility': historical_identity['territorial_identity_sha256'],
            'canonical_receipt_path': recovery['historical_receipt'], 'durable_consumer': durable,
            'local_candidate_receipt': candidate_path.as_posix(),
            'local_candidate_package_sha256': sha(candidate_raw),
            'local_candidate_report_sha256': sha(report_raw),
            'local_candidate_compatibility_identity_sha256': candidate['compatibility_identity_sha256'],
            'local_candidate_territorial_identity_sha256': identity['territorial_identity_sha256'],
            'candidate_run_accreditation': 'ABSENT: no receipt/run/artifact binding for these derived bytes',
            'other_source_named_artifacts_not_accredited': [
                {'id': a['id'], 'name': a['name'], 'digest': a['digest']}
                for a in artifacts if a['name'].startswith('ddd-source-package') and a['id'] != remote['id']],
            'required_producer_action': {
                'operation': '01 · Preparación de Datos Territoriales',
                'territory_id': territory, 'data_edition': '2025',
                'population_year': '2025', 'section_year': '2025',
                'reuse_historical_artifact': False,
                'requirements': [
                    'Reproducir la materialización/derivación territorial en una ejecución autorizada del productor, con linaje de inputs y commit verificable.',
                    'Congelar informe #179 READY en el nuevo paquete y verificar bindings, CRS, roles, conservación y digests.',
                    'Emitir artefacto del nuevo run; calcular SHA exterior, interior, informe e identidad desde sus bytes.',
                    'Acreditar receipt nuevo ligado al run productor real y declaración versionada; registro durable y promoción son actuaciones posteriores separadas.'],
            },
        })
    return {'version': '1.0.0', 'date': '2026-10-10', 'scope': 'F10 únicamente',
            'origin': 'c83f6e3f5b9d25ec12c0124e42b372e7d838031e', 'predecessor': None,
            'changes': 'inventario comprobado y bloqueos F10', 'reason': 'contrato #179',
            'decision': 'BLOCKED', 'rows': rows,
            'limits': ['Sólo los cinco runs registrados y los bytes conservados se verifican exhaustivamente.',
                       'No se afirma inexistencia global de otros runs/artefactos.',
                       'Los dos artifacts de nombre genérico de Comunidad Valenciana sólo tienen metadata; bytes no examinados y nombre ambiguo.',
                       'Las identidades v3 se recalculan para distinguir bytes; no se repite F05–F09 ni se certifica su preparación productiva.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compare', type=Path, help='Comparar con resultado conservado sin escribir')
    args = parser.parse_args()
    result = verify()
    if args.compare:
        require(result == json.loads(args.compare.read_text()), 'resultado no reproducible')
        print('PASS: evidencia F10 reproducida; cinco candidatos BLOCKED')
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
