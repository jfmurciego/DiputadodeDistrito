#!/usr/bin/env python3
"""Cierre de Fuentes Oficiales v1.0.0, 2026-10-11; evidencia local.

Alcance: reconciliar F04 y validar 19 consumidores sin red ni promoción.
Cambios: nuevo verificador; motivo: cierre del Plan Maestro existente.
Origen: main@5216a1b25da7726dd73296723f22754dcf7451e1; predecesor: ninguno.
No escribe receipts ni cambia catálogos, contratos o estados del Plan Maestro.
"""
from __future__ import annotations

import argparse
import json
import re
import socket
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PRIOR = ROOT / 'docs/AUDITORIAS/F04_F10_20261009'
sys.path.insert(0, str(ROOT))
from herramientas.almacen_fuentes_local import consume, require, sha256
from herramientas.catalogo_preparacion import lookup
from herramientas.compatibilidad_poblacion_seccionado import validate_compatibility_package
from herramientas.consumir_par_fuentes_legislatura import (
    PreparedPairExecutionBlock, validate_effective_territorial_package,
    validate_territorial_receipt,
)
from herramientas.identidad_fuentes_legislatura import territorial_identity
from herramientas.resolver_preparacion_legislatura import resolve
from herramientas.seleccionar_paquete_fuentes import validate_prepared_package
from herramientas._resolver_ejecucion_completa_core import generation_enablement

RUNS = {
    'andalucia': 38082966768, 'aragon': 38093067883,
    'castilla_y_leon': 38091055890, 'comunidad_valenciana': 38091132175,
    'extremadura': 38091144559,
}


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def verify_files(manifest: dict) -> int:
    paths = [entry['path'] for entry in manifest['files']]
    require(len(paths) == len(set(paths)), 'manifiesto con rutas duplicadas')
    for entry in manifest['files']:
        path = ROOT / entry['path']
        require(path.is_file() and path.stat().st_size == entry['bytes'],
                'tamaño/archivo contradictorio: ' + entry['path'])
        require(sha256(path) == entry['sha256'], 'SHA contradictorio: ' + entry['path'])
    return len(paths)


def verify_actions(snapshot: dict) -> list[dict]:
    rows = snapshot['rows']
    require(len(rows) == 5 and {r['run']['id'] for r in rows} == set(RUNS.values()),
            'colección distinta de los cinco runs autorizados')
    result = []
    for tid, run_id in RUNS.items():
        row = next(r for r in rows if r['run']['id'] == run_id)
        run, inventory, artifact = row['run'], row['artifacts'], row['selected']
        require(run['status'] == 'completed' and run['conclusion'] == 'success',
                'run no SUCCESS')
        require(inventory['total_count'] == len(inventory['artifacts']), 'inventario incompleto')
        require(len({a['id'] for a in inventory['artifacts']}) == len(inventory['artifacts']),
                'IDs de artefacto duplicados')
        matches = [a for a in inventory['artifacts'] if a['id'] == artifact['id']]
        require(matches == [artifact], 'artefacto ausente o contradictorio')
        require(artifact['name'] == f'ddd-source-package-{tid}-2025-{run_id}',
                'nombre de artefacto contradictorio; no acredita contenido')
        require(artifact['workflow_run']['id'] == run_id
                and artifact['workflow_run']['head_sha'] == run['head_sha'],
                'run/commit contradictorio')
        require(bool(re.fullmatch(r'sha256:[0-9a-f]{64}', artifact['digest'])),
                'digest remoto inválido')
        require(not artifact['expired'] and artifact['size_in_bytes'] > 0, 'artefacto no disponible')
        jobs = row['jobs']
        require(jobs['total_count'] == len(jobs['jobs']), 'inventario de jobs incompleto')
        preparation = [j for j in jobs['jobs'] if j['name'].endswith('/ Preparar fuentes territoriales')]
        require(len(preparation) == 1 and preparation[0]['conclusion'] == 'success',
                'preparación no SUCCESS')
        registration = [j for j in jobs['jobs'] if j['name'].endswith('/ Registrar fuentes territoriales preparadas')]
        require(len(registration) == 1 and registration[0]['conclusion'] == 'skipped',
                'registro durable inesperado')
        result.append({'territory_id': tid, 'run_id': run_id, 'artifact_id': artifact['id'],
                       'artifact_name': artifact['name'], 'source_commit': run['head_sha'],
                       'remote_sha256': artifact['digest'].removeprefix('sha256:'),
                       'remote_bytes': artifact['size_in_bytes'], 'expires_at': artifact['expires_at'],
                       'run_metadata': 'PASS', 'preparation_reported': 'SUCCESS',
                       'artifact_bytes_validation': 'BLOCKED', 'durable_conservation': 'BLOCKED',
                       'canonical_receipt': 'BLOCKED_NOT_CREATED',
                       'cause': 'ZIP local ausente; transporte DNS bloqueado; conservación Drive rechazada',
                       'missing': ['manifest y edición/años comprobados desde bytes',
                                   'CRC exterior/interior y SHA interior recalculados',
                                   'compatibility_report_member', 'compatibility_report_sha256',
                                   'compatibility_identity_sha256', 'territorial_identity_sha256',
                                   'conservación durable y receipt #179 del paquete exacto']})
    return result


def verify_f04() -> dict:
    count = verify_files(read(PRIOR / 'MANIFEST-v3.json'))
    require(count == 242, 'lote F04 distinto')
    overlay_count = verify_files(read(PRIOR / 'subsanacion/manifest.json'))
    matrix = read(PRIOR / 'continuacion/matriz-19-final.json')['rows']
    require(len(matrix) == 19 and len({r['territory_id'] for r in matrix}) == 19,
            'matriz F04 distinta de 19')
    results = []
    for row in read(PRIOR / 'candidate-results-v3.json')['rows']:
        tid = row['territory_id']
        require(tid in RUNS, 'candidato F04 desconocido')
        package = (ROOT / row['package']).parent
        receipt = read(ROOT / row['receipt'])
        require(receipt['schema'] == 'ddd.local-derived-source-receipt/1.0',
                'no confundir receipt local con canónico')
        args = dict(territory_id=tid, edition='2025', population_year=2025, section_year=2025)
        valid, reasons = validate_prepared_package(package, **args)
        require(valid, '; '.join(reasons))
        report, report_sha, reasons = validate_compatibility_package(package, **args, require_ready=True)
        require(not reasons, '; '.join(reasons))
        require(sha256(package / 'prepared_sources.zip') == row['package_sha256']
                == receipt['package_sha256'], 'SHA F04 distinto')
        require(report_sha == receipt['compatibility_report_sha256'], 'informe F04 distinto')
        identity = territorial_identity(**{k: receipt[k] for k in (
            'territory_id', 'edition', 'population_year', 'section_year', 'package_sha256',
            'compatibility_identity_sha256')})
        require(identity == row['identity'], 'identidad F04 distinta')
        results.append({'territory_id': tid, 'decision': 'PASS_LOCAL',
                        'package_sha256': row['package_sha256'],
                        'territorial_identity_sha256': identity['territorial_identity_sha256'],
                        'compatibility_report_sha256': report_sha, 'report_decision': report['decision']})
    require(len(results) == 5 and {r['territory_id'] for r in results} == set(RUNS),
            'lote F04 incompleto')
    return {'criterion': 'Matriz de 19 con gaps y pruebas', 'technical_criterion': 'SATISFIED',
            'formal_status': 'PENDING', 'transition_proposed': 'PASS_REQUIRES_WORK_APPROVAL',
            'approval_recorded': False, 'manifest_files_verified': count,
            'accepted_reference_overlay_files_verified': overlay_count,
            'matrix_rows': len(matrix), 'prior_review': 'GO_ACOTADO, sesión separada', 'rows': results}


def verify_national(store: Path) -> list[dict]:
    historical = read(PRIOR / 'continuacion/evidencia-previa-reutilizada.json')
    previous = {r['territory_id']: r for r in historical['rows']}
    require(len(previous) == 14, 'históricos distintos de 14')
    manifest_path = store / 'recovery-manifest.json'
    before = sha256(manifest_path)
    rows = []
    plans = resolve(ROOT, 'Todos')['plans']
    require(len(plans) == 19, 'plan temporal distinto de 19')
    with tempfile.TemporaryDirectory(prefix='ddd-cierre-consumo-', dir='/private/tmp') as tmp:
        for plan in plans:
            tid = plan['territory_id']
            state = lookup(tid, '2025', ROOT / 'configuracion/catalogo_preparacion.yaml')
            row = {'territory_id': tid, 'name': plan['name'], 'election_id': plan['election_id'],
                   'selected_population_year': plan['population_year_selected'],
                   'selected_section_year': plan['section_year_selected'],
                   'electoral_source': {'metadata_admissibility': plan['electoral_admissibility'],
                                        'reason': plan['electoral_reason'],
                                        'identity': plan['electoral_candidate'],
                                        'bytes_revalidated': False},
                   'production_executed': False, 'canonical_promotion': False}
            try:
                _, receipt = validate_territorial_receipt(root_dir=ROOT, territory=tid, edition='2025')
                require(tid in previous, 'receipt nuevo inesperado: revisar antes de continuar')
                prior = previous[tid]
                require(receipt == prior['details']['F03_consumer_receipt'], 'receipt histórico cambiado')
                prepared = consume(store, destination=Path(tmp) / tid, **{k: receipt[k] for k in (
                    'territory_id', 'edition', 'territorial_identity_sha256', 'package_sha256')})
                effective = validate_effective_territorial_package(
                    root_dir=ROOT, territorial_receipt_path=Path(prior['receipt_path']),
                    territorial_package=prepared)
                require(effective == prior['details']['F03_effective_consumer'],
                        'validación histórica distinta')
                row['territorial_consumer'] = {'decision': 'PASS', 'mode': 'ACTUAL_OFFLINE_BYTES',
                                              'receipt_path': prior['receipt_path'], 'receipt': receipt,
                                              'effective_validation': effective}
                years = (receipt['population_year'], receipt['section_year'])
                row['temporal_compatibility'] = 'PASS' if years == (
                    plan['population_year_selected'], plan['section_year_selected']) else 'BLOCKED_WRONG_YEAR'
                evidence_path = ROOT / f'territorios/{tid}/evidencia/catalogo/generation_preflight_2025.json'
                gate = generation_enablement(root_dir=ROOT, contract_path=state.get('contract_path'),
                    territory_id=tid, first_generation_evidence=read(evidence_path) if evidence_path.exists() else {},
                    preparation_evidence=state['preparation_evidence'], require_source=True)
                row['generation_source_gate'] = gate
                row['productivity'] = 'SOURCE_GATE_ONLY_NO_EXECUTION_AUTHORIZATION' if gate['allowed'] else 'BLOCKED_GENERATION_GATE'
            except (PreparedPairExecutionBlock, ValueError, OSError, KeyError) as exc:
                row['territorial_consumer'] = {'decision': 'BLOCKED', 'reason': str(exc)}
                row['temporal_compatibility'] = 'BLOCKED_UNACCREDITED_BYTES'
                row['productivity'] = 'BLOCKED_UNACCREDITED_TERRITORIAL_SOURCE'
            if tid in RUNS:
                requested = (plan['population_year_selected'], plan['section_year_selected'])
                row['new_package_temporal_contract'] = {
                    'producer_years_reported': [2025, 2025], 'selected_years_required': list(requested),
                    'decision': 'MATCH_REPORTED_NOT_BYTE_VERIFIED' if requested == (2025, 2025) else 'BLOCKED_YEAR_MISMATCH',
                    'source': 'caller y log del nuevo productor; no manifiesto local'}
            rows.append(row)
    require(before == sha256(manifest_path), 'almacén histórico alterado')
    return rows


def verify(store: Path) -> dict:
    with patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
         patch.object(socket, 'create_connection', side_effect=AssertionError('network forbidden')), \
         patch.object(socket, 'getaddrinfo', side_effect=AssertionError('network forbidden')):
        return {'schema': 'ddd.official-sources-closure/1.0', 'version': '1.0.0',
                'date': '2026-10-11', 'origin': '5216a1b25da7726dd73296723f22754dcf7451e1',
                'predecessor': None, 'scope': 'Fuentes Oficiales; Plan Maestro vigente',
                'changes': 'reconciliación F04 y consumo nacional offline',
                'reason': 'propuesta de cierre F10 sin aprobación ni promoción',
                'decision': 'BLOCKED', 'network': 'FORBIDDEN', 'F04': verify_f04(),
                'new_runs': verify_actions(read(HERE / 'actions.json')),
                'consumers': verify_national(store)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--store', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--compare', type=Path)
    args = parser.parse_args()
    require(not (args.output and args.compare), 'usar output o compare')
    if args.output:
        require(not args.output.exists(), 'conservar salida existente')
        require(args.output.resolve().is_relative_to(HERE) or
                args.output.resolve().is_relative_to(Path('/private/tmp')), 'salida fuera del expediente/tmp')
        require(not args.output.resolve().is_relative_to(args.store.resolve()), 'salida en almacén prohibida')
    result = verify(args.store)
    if args.compare:
        require(result == read(args.compare), 'resultado no reproducible')
    if args.output:
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'F04': result['F04']['technical_criterion'],
                      'consumers_PASS': sum(r['territorial_consumer']['decision'] == 'PASS' for r in result['consumers']),
                      'consumers_BLOCKED': sum(r['territorial_consumer']['decision'] == 'BLOCKED' for r in result['consumers']),
                      'new_receipts_created': 0, 'decision': result['decision']}))
