"""Versión 1.2.0; preflight provincial Congreso M01-M06; fecha 2026-10-13.
Alcance: inspección reproducible sin partición real ni ejecución productiva.
Estado: candidato; límites M04/M05 contractuales; resultado parcial por provincia.
Motivo: admitir diagnósticos nacionales por CPRO y seguir fail-closed ante bloqueos.
Anterior: legacy/n08_caceres_20261012/preflight_caceres_n08_v1.py.
"""
from __future__ import annotations
import argparse
import csv
import gzip
import hashlib
import importlib.util
import json
import os
import platform
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
PRODUCT = ROOT / 'docs/ESTUDIOS/N08_TOPOLOGIA_NACIONAL_20251012/producto'
CONTRACT = ROOT / 'territorios/congreso/contrato_congreso_2026.json'
SOURCES = ROOT / 'territorios/congreso/fuentes/ine_2025_2025'
PROVINCE = '10'
def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(obj) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def read_json(path: Path):
    return json.loads(path.read_bytes())


def verify_manifest(root: Path, manifest: dict) -> None:
    identity = manifest.get('identity_sha256')
    body = dict(manifest)
    body.pop('identity_sha256', None)
    if identity != sha(canonical(body)):
        raise ValueError('TOPOLOGY_MANIFEST_IDENTITY')
    for rel, record in manifest.get('artifacts', {}).items():
        path = root / rel
        data = path.read_bytes()
        if sha(data) != record.get('sha256') or len(data) != record.get('bytes'):
            raise ValueError('TOPOLOGY_ARTIFACT_HASH:' + rel)
        raw = gzip.decompress(data)
        value = json.loads(raw)
        if sha(raw) != record.get('canonical_json_sha256') or raw != canonical(value) + b'\n':
            raise ValueError('TOPOLOGY_ARTIFACT_CONTENT:' + rel)
        if data != gzip.compress(raw, mtime=0):
            raise ValueError('TOPOLOGY_ARTIFACT_GZIP:' + rel)


def _module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError('MODULE_NOT_LOADABLE:' + str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _source_pair(parts_dir: Path, source_manifest: dict, contract: dict):
    # load_inputs verifies the 3+4 protected INE ZIP parts, original ZIPs,
    # editions, exact CUSEC joins, all 36,554 source geometries, population,
    # N07 attributes, 52 quotas and generation=false. It does not rebuild N08.
    from herramientas.preflight_topologico_nacional import load_inputs
    frame, loaded_contract, evidence = load_inputs(parts_dir, root=ROOT)
    if loaded_contract != contract:
        raise ValueError('CONTRACT_CHANGED_DURING_PREFLIGHT')
    return frame, evidence


def _m01_real_input(parts_dir: Path, source_manifest: dict, code: str,
                    expected_sections: int, expected_population: int):
    """Exercise the actual M01 geometry/CIP loaders on one protected province."""
    import pandas as pd
    m01 = _module(ROOT / 'modulos/01_preparar_base_territorial.py', 'ddd_m01_caceres_preflight')
    geometry_source = source_manifest['sources']['geometry']
    parts = []
    for name, expected in sorted(geometry_source['part_sha256'].items()):
        data = (parts_dir / name).read_bytes()
        if sha(data) != expected:
            raise ValueError('M01_PROTECTED_GEOMETRY_PART_HASH:' + name)
        parts.append(data)
    zip_bytes = b''.join(parts)
    if sha(zip_bytes) != geometry_source['sha256']:
        raise ValueError('M01_PROTECTED_GEOMETRY_ZIP_HASH')
    with tempfile.TemporaryDirectory(prefix='ddd_m01_caceres_') as temp:
        zpath = Path(temp) / 'seccionado_2025.zip'
        zpath.write_bytes(zip_bytes)
        source = m01.load_seccionado(zpath, province_codes=[code], container='zip', materialized_format='shapefile')
        source = source.copy()
        source['_CUSEC'] = source['CUSEC'].map(m01.normalize_section_key)
        source = source.loc[source['_CUSEC'].str[:2] == code].copy()
        if source.crs is None or source.crs.to_epsg() != 25830:
            raise ValueError('M01_GEOMETRY_CRS')
        if source['_CUSEC'].isna().any() or source['_CUSEC'].duplicated().any():
            raise ValueError('M01_CUSEC_INVALID_OR_DUPLICATE')
        if len(source) != expected_sections or not source.geometry.is_valid.all() or source.geometry.is_empty.any():
            raise ValueError('M01_GEOMETRY_COVERAGE_OR_VALIDITY')
        pop_path = SOURCES / 'poblacion_por_seccion_2025.csv'
        cip = m01.load_cip([pop_path], 'CUSEC', 'POB_2025', 2025, ',',
                           {'year_col': '_already_2025', 'sexo_col': '_already_total',
                            'edad_col': '_already_all_ages', 'year_value': 2025},
                           [code], container='file', materialized_format='csv')
        if cip['CUSEC_KEY'].duplicated().any():
            raise ValueError('M01_POPULATION_DUPLICATE_CUSEC')
        joined = source.merge(cip, left_on='_CUSEC', right_on='CUSEC_KEY', how='left', validate='one_to_one')
        if joined['POP'].isna().any() or len(joined) != expected_sections or int(joined['POP'].sum()) != expected_population:
            raise ValueError('M01_EXACT_POPULATION_JOIN')
        joined['POB_2025'] = joined['POP'].astype('int64')
        return joined.drop(columns=['POP', 'CUSEC_KEY'])


def _approved_policies(contract):
    """Return only explicit owner-approved policy values; never fill defaults."""
    required = ('minimum_unit', 'contiguity', 'population_limits',
                'municipal_indivisibility', 'islands', 'enclaves',
                'physical_discontinuities')
    decisions = contract.get('decisions', {})
    pending = {}
    for key in required:
        decision = decisions.get(key, {}) or {}
        if decision.get('status') != 'APPROVED' or decision.get('value') is None:
            pending[key] = decision.get('status', 'MISSING')
    population = decisions.get('population_limits', {}) or {}
    values = population.get('value') if population.get('status') == 'APPROVED' else None
    required_limits = ('population_floor_ratio', 'population_cap_ratio', 'target_tolerance_ratio')
    if not isinstance(values, dict) or any(k not in values for k in required_limits):
        pending['population_limits_values'] = 'MISSING_OR_INVALID'
    return pending, values if isinstance(values, dict) else None


def report_gate_ready(pending, hard_limit_blocker, synthetic_m05, synthetic_m06,
                      contract_production_blockers=()):
    """Contract admission requires local checks and the national contract gate."""
    return (not pending and hard_limit_blocker is None and
            not contract_production_blockers and
            synthetic_m05.get('status') == 'SYNTHETIC_CONTRACT_PASS_ONLY' and
            synthetic_m06.get('status') == 'SYNTHETIC_OUTPUT_AUDIT_PASS')


def _synthetic_m05_contract(contract, nodes, edges, *, province, floor=1, cap=None):
    """Exercise M05 final invariants on a synthetic chain, never optimize."""
    from ddd_core.congreso_preflight_adapter import congreso_m05_municipal_policy
    from ddd_core.m05_population_repair import verify_partition_constraints
    municipal_policy = congreso_m05_municipal_policy(contract)
    total = sum(n['pop'] for n in nodes)
    units = {n['id']: {'population': n['pop'], 'province': province,
                       'municipality_group': n['CUMUN'], 'CUMUN': n['CUMUN']} for n in nodes}
    adjacency = {n['id']: set() for n in nodes}
    for edge in edges:
        adjacency[edge['u']].add(edge['v'])
        adjacency[edge['v']].add(edge['u'])
    state = {n['id']: str(i + 1) for i, n in enumerate(nodes)}
    result = verify_partition_constraints(state, units, adjacency, floor=floor,
                                          cap=total if cap is None else cap,
                                          municipality_policy=municipal_policy)
    if not result.get('valid') or not result.get('hard_limits_met'):
        raise ValueError('M05_SYNTHETIC_CONTRACT')
    return {'status': 'SYNTHETIC_CONTRACT_PASS_ONLY', 'diagnostic_only': True,
            'optimizer_executed': False, 'units': len(nodes),
            'districts': len(set(state.values())), 'municipality_policy': municipal_policy}


def _approved_m05_bounds(contract, *, quota, population):
    """Read the exact approved lower/upper limits from the shared contract helper."""
    from ddd_core.config import hard_limits
    pending, ratios = _approved_policies(contract)
    if pending or ratios is None:
        raise ValueError('APPROVED_POPULATION_LIMITS_REQUIRED')
    numeric = {key: float(ratios[key]) for key in
               ('population_floor_ratio', 'population_cap_ratio', 'target_tolerance_ratio')}
    target, floor, cap, _tolerance = hard_limits(
        {'validation': numeric}, k=quota, total_pop=population)
    return floor, cap


def _m04_component_diagnostic(component_populations, quota):
    """Represent a failed necessary bound as a diagnostic gate, not an exception."""
    from ddd_core.congreso_preflight_adapter import structural_component_bound
    bound = structural_component_bound(component_populations, quota)
    if bound['feasibility_proven']:
        raise ValueError('M04_COMPONENT_BOUND_MUST_NOT_CLAIM_SUFFICIENCY')
    return bound


def _synthetic_m06_contract(contract, source_binding, *, province, quota, population):
    """Synthetic output contract fixture; never a real assignment."""
    from ddd_core.congreso_preflight_adapter import (
        audit_synthetic_partition, congreso_m05_municipal_policy,
    )
    if type(quota) is not int or quota < 1 or population < quota:
        raise ValueError('M06_FIXTURE_QUOTA_OR_POPULATION')
    quotient, remainder = divmod(population, quota)
    nodes = []
    for i in range(quota):
        mun = f'{province}{i + 1:03d}'
        ident = mun + f'{i + 1:05d}'
        pop = quotient + (1 if i < remainder else 0)
        nodes.append({'id': ident, 'pop': pop, 'CPRO': province, 'CUMUN': mun,
                      'geometry_sha256': 'a' * 64, 'source_geometry_sha256': source_binding['geometry']['sha256'],
                      'physical_component': '', 'physical_part_components': [ident + ':p0000']})
    for node in nodes:
        node['physical_component'] = nodes[0]['id']
    edges = [{'u': nodes[i]['id'], 'v': nodes[i + 1]['id'], 'shared_border_m': 1.0,
              'overlap_m2': 0.0, 'edge_type': 'geometric',
              'contact_sha256': f'{i + 1:064x}'} for i in range(quota - 1)]
    rows = [{'id': n['id'], 'district_id': str(i + 1), 'pop': n['pop']} for i, n in enumerate(nodes)]
    policy = {'minimum_unit': 'section',
              'municipal_policy': congreso_m05_municipal_policy(contract),
              'population_floor': 1, 'population_cap': population}
    result = audit_synthetic_partition(contract, nodes, edges, source_binding, rows, policy, synthetic_fixture=True)
    if result['status'] != 'SYNTHETIC_OUTPUT_AUDIT_PASS' or len(result['district_populations']) != quota or sum(result['district_populations'].values()) != population:
        raise ValueError('M06_SYNTHETIC_CONTRACT')
    # Assert the fields consumed by M06. These fixture values are not policy.
    out = [{'CUSEC': r['id'], 'district_id': int(r['district_id']), 'POB_2025': r['pop'], 'CPRO': province} for r in rows]
    if len({r['CUSEC'] for r in out}) != quota or sum(r['POB_2025'] for r in out) != population:
        raise ValueError('M06_SYNTHETIC_TRACEABILITY')
    import pandas as pd
    m06 = _module(ROOT / 'modulos/06_consolidar_distritos.py', 'ddd_m06_caceres_preflight')
    cusec_join = m06.joined_unique(pd.Series([r['CUSEC'] for r in out]))
    if cusec_join != ' | '.join(sorted(r['CUSEC'] for r in out)):
        raise ValueError('M06_CONSUMER_CUSEC_CONTRACT')
    return {'status': result['status'], 'diagnostic_only': True, 'policy_approved': False,
            'rows': len(out), 'districts': len(result['district_populations']),
            'fields': ['CUSEC', 'district_id', 'POB_2025', 'CPRO'],
            'consumer': 'modulos/06_consolidar_distritos.py:joined_unique',
            '_fixture_nodes': nodes, '_fixture_edges': edges}


def _verify_historical_transition(transition_path: Path, product_dir: Path,
                                topology_manifest: dict, current_contract_sha: str) -> dict:
    """Permit source-bound artifact reuse only as diagnostic revalidation.

    It does not rewrite the historical product binding or accredit its topology.
    """
    transition = read_json(transition_path)
    if transition.get('schema') != 'ddd.congress-artifact-transition/1.0' or transition.get('status') != 'CANDIDATE_DIAGNOSTIC_ONLY':
        raise ValueError('ARTIFACT_TRANSITION_NOT_DIAGNOSTIC_CANDIDATE')
    source_product = transition.get('source_product', {})
    manifest_path = product_dir / 'manifest.json'
    if source_product.get('manifest_entries') != 74 or source_product.get('manifest_verified') != 74:
        raise ValueError('ARTIFACT_TRANSITION_74_OF_74_REQUIRED')
    if source_product.get('product_manifest_sha256') != sha(manifest_path.read_bytes()):
        raise ValueError('ARTIFACT_TRANSITION_PRODUCT_MANIFEST_HASH')
    delivery_path = ROOT / 'docs/ESTUDIOS/N08_TOPOLOGIA_NACIONAL_20251012/MANIFEST_ENTREGA.json'
    delivery = read_json(delivery_path)
    if delivery.get('files_sha256', {}).get('producto/manifest.json') != sha(manifest_path.read_bytes()):
        raise ValueError('ARTIFACT_TRANSITION_OUTER_MANIFEST_HASH')
    if topology_manifest.get('evidence', {}).get('contract_sha256') == current_contract_sha:
        raise ValueError('ARTIFACT_TRANSITION_NOT_NEEDED')
    expected_source = topology_manifest.get('evidence', {}).get('source_binding', {})
    if transition.get('invariants', {}).get('source_edition') != 2025 or topology_manifest.get('generation_authorized') is not False:
        raise ValueError('ARTIFACT_TRANSITION_SOURCE_OR_AUTHORIZATION')
    return {
        'status': 'CANDIDATE_DIAGNOSTIC_ONLY',
        'reuse': 'ARTIFACT_REUSE_WITH_STRUCTURAL_REVALIDATION',
        'historical_contract_sha256': topology_manifest.get('evidence', {}).get('contract_sha256'),
        'current_contract_sha256': current_contract_sha,
        'source_binding': expected_source,
        'product_manifest_sha256': sha(manifest_path.read_bytes()),
        'product_certification': 'NOT_PERFORMED',
        'generation_authorized': False,
    }


def run(parts_dir: Path, output: Path, province: str = PROVINCE, product_dir: Path = PRODUCT,
        transition_path: Path | None = None):
    code = str(province).zfill(2)
    if not code.isdigit() or len(code) != 2 or not 1 <= int(code) <= 52:
        raise ValueError('PROVINCE_CODE_INVALID')
    source_manifest = read_json(SOURCES / 'manifest.json')
    contract = read_json(CONTRACT)
    contract_identity = sha(CONTRACT.read_bytes())
    topology_manifest_path = product_dir / 'manifest.json'
    topology_manifest = read_json(topology_manifest_path)
    ident = topology_manifest.get('identity_sha256')
    if ident != sha(canonical({k: v for k, v in topology_manifest.items() if k != 'identity_sha256'})):
        raise ValueError('TOPOLOGY_MANIFEST_IDENTITY')
    if topology_manifest.get('generation_authorized') is not False:
        raise ValueError('GENERATION_AUTHORIZATION')
    binding = topology_manifest.get('evidence', {}).get('source_binding', {})
    if topology_manifest.get('evidence', {}).get('source_manifest_sha256') != sha((SOURCES / 'manifest.json').read_bytes()):
        raise ValueError('TOPOLOGY_SOURCE_MANIFEST_HASH')
    transition_evidence = None
    if topology_manifest.get('evidence', {}).get('contract_sha256') != contract_identity:
        if transition_path is None:
            raise ValueError('TOPOLOGY_CONTRACT_HASH')
        transition_evidence = _verify_historical_transition(
            transition_path, product_dir, topology_manifest, contract_identity)
    for role in ('geometry', 'population'):
        expected = contract['sources'][role]
        if expected.get('edition') != 2025 or expected.get('sha256') != binding.get(role, {}).get('sha256'):
            raise ValueError('CONTRACT_TOPOLOGY_SOURCE:' + role)
    crosswalk = SOURCES / 'crosswalk_n07_2025.csv'
    crosswalk_meta = source_manifest['crosswalk']
    if sha(crosswalk.read_bytes()) != crosswalk_meta['sha256']:
        raise ValueError('N07_CROSSWALK_HASH')
    population_path = SOURCES / 'poblacion_por_seccion_2025.csv'
    population_meta = source_manifest['outputs']['poblacion_por_seccion_2025.csv']
    if sha(population_path.read_bytes()) != population_meta['sha256']:
        raise ValueError('INE_POPULATION_OUTPUT_HASH')
    product_path = product_dir / 'unidades' / (code + '.json.gz')
    artifact_record = topology_manifest['artifacts'].get('unidades/' + code + '.json.gz')
    if not artifact_record:
        raise ValueError('TOPOLOGY_UNIT_NOT_IN_MANIFEST')
    raw = product_path.read_bytes()
    if sha(raw) != artifact_record['sha256'] or len(raw) != artifact_record['bytes']:
        raise ValueError('TOPOLOGY_UNIT_HASH')
    decoded = gzip.decompress(raw)
    unit = json.loads(decoded)
    # The manifest pins the exact compressed bytes, while canonical_json_sha256
    # pins the decoded canonical JSON. Recompressing and comparing bytes is
    # not portable across zlib/Python builds (the gzip OS header may differ)
    # and adds no integrity beyond these two independent hashes.
    if sha(decoded) != artifact_record['canonical_json_sha256'] or decoded != canonical(unit) + b'\n':
        raise ValueError('TOPOLOGY_UNIT_CANONICAL')
    if unit.get('run_binding') != topology_manifest.get('run_binding'):
        raise ValueError('TOPOLOGY_UNIT_RUN_BINDING')
    summary = unit['summary']
    quota = {q['code']: q['k'] for q in contract['quotas_by_origin_unit']}.get(code)
    actual_quota = max(1, (int(summary['population']) + 60000) // 120000)
    if summary['CPRO'] != code or quota != actual_quota or summary['k'] != quota:
        raise ValueError('CONGRESS_PROVINCIAL_QUOTA')
    from ddd_core.congreso_preflight_adapter import validate_physical_product, structural_component_bound, engine_input_contract
    source_binding = {role: {'edition': 2025, 'sha256': contract['sources'][role]['sha256']} for role in ('geometry', 'population')}
    graph_admission = validate_physical_product(contract, unit['nodes'], unit['edges'], source_binding, require_national=False)
    if summary.get('generation_authorized') is not False or graph_admission['generation_authorized'] is not False:
        raise ValueError('GENERATION_AUTHORIZATION')
    frame, source_evidence = _source_pair(parts_dir, source_manifest, contract)
    province_frame = frame.loc[frame.CPRO == code].sort_values('CUSEC').reset_index(drop=True)
    actual = _m01_real_input(parts_dir, source_manifest, code,
                             len(province_frame), int(province_frame.POB_2025.sum()))
    if set(actual['_CUSEC']) != set(province_frame['CUSEC']) or len(actual) != len(province_frame):
        raise ValueError('M01_PROTECTED_SOURCE_COVERAGE')
    # Compare M01 and N07 outputs to every accredited graph node by exact CUSEC.
    actual_by_id = {source_id: row for source_id, row in actual.set_index('_CUSEC').iterrows()}
    nodes = {n['id']: n for n in unit['nodes']}
    if set(nodes) != set(actual_by_id):
        raise ValueError('M03_GRAPH_COVERAGE')
    for source_id, source_row in actual_by_id.items():
        node = nodes[source_id]
        if int(source_row['POB_2025']) != node['pop'] or str(source_row['CUMUN']).zfill(5) != node['CUMUN']:
            raise ValueError('M01_M03_ATTRIBUTE_JOIN:' + source_id)
        if sha(source_row.geometry.wkb) != node['geometry_sha256']:
            raise ValueError('M01_M03_GEOMETRY_IDENTITY:' + source_id)
    m02 = _module(ROOT / 'modulos/02_construir_adyacencias.py', 'ddd_m02_caceres_preflight')
    # Pure consumer call on this province's source geometries, with no buffer, simplify,
    # bridges, or coordinate change. This does not rebuild the national product.
    # M02's contact predicate accepts pure points when its lower bound is zero.
    # A 1 nm positive-length floor is only a zero-vs-positive discriminator;
    # it is far below source precision and cannot bridge a gap or create contact.
    m02_positive_length_floor_m = 1e-9
    calculated = set(m02.iter_edges(
        actual, '_CUSEC', 'contact', m02_positive_length_floor_m, 0.0,
        0.0, 0.0, 0, 0, 'EPSG:25830'))
    accredited = {(e['u'], e['v']) for e in unit['edges']}
    if calculated != accredited:
        raise ValueError('M02_EDGE_SET_DIFFERS_FROM_N08_PRODUCT')
    m03 = _module(ROOT / 'modulos/03_construir_grafo.py', 'ddd_m03_caceres_preflight')
    graph_nodes = m03.build_nodes(actual, '_CUSEC', 'POB_2025', ('CPRO', 'CUMUN'))
    graph_edges = [{'u': e['u'], 'v': e['v']} for e in unit['edges']]
    adjacency = {n['id']: set() for n in graph_nodes}
    for e in graph_edges:
        if e['u'][:2] != code or e['v'][:2] != code:
            raise ValueError('M03_CROSS_PROVINCE_EDGE')
        adjacency[e['u']].add(e['v']); adjacency[e['v']].add(e['u'])
    graph_components = m03.component_sets(set(adjacency), adjacency)
    product_components = [set(c['sections']) for c in unit['physical_components']]
    if {frozenset(c) for c in graph_components} != {frozenset(c) for c in product_components}:
        raise ValueError('M03_COMPONENTS_DIFFER')
    topo = _m04_component_diagnostic(
        [int(c['population']) for c in unit['physical_components']], int(quota))
    topology_blocker = None if topo['necessary_condition'] else topo['reason']
    input_map = engine_input_contract()
    pending, limit_values = _approved_policies(contract)
    from ddd_core.congreso_contract import production_blockers
    blockers = production_blockers(contract)
    m04_necessary = None
    from ddd_core.config import hard_limits
    if limit_values and not pending:
        from math import isfinite
        ratios = ('population_floor_ratio', 'population_cap_ratio', 'target_tolerance_ratio')
        try:
            numeric = {key: float(limit_values[key]) for key in ratios}
            if (not all(isfinite(value) for value in numeric.values()) or
                    numeric['population_floor_ratio'] <= 0 or
                    numeric['population_cap_ratio'] < numeric['population_floor_ratio'] or
                    numeric['target_tolerance_ratio'] < 0):
                raise ValueError('APPROVED_POPULATION_LIMITS_INVALID')
            limits = hard_limits({'validation': numeric}, k=int(quota),
                                 total_pop=int(summary['population']))
            from ddd_core.m04_seed_engine import _atomic_population_necessary_conditions
            weights = {str(row.CUSEC): int(row.POB_2025) for row in actual.itertuples()}
            m04_necessary = _atomic_population_necessary_conditions(
                set(weights), weights, k=int(quota), floor=limits[1], cap=limits[2])
            population_blocker = None if m04_necessary[0] else m04_necessary[1]
            hard_limit_blocker = topology_blocker or population_blocker
        except (Exception, SystemExit) as exc:
            hard_limit_blocker = topology_blocker or str(exc)
            m04_necessary = (False, hard_limit_blocker, {})
    else:
        try:
            from ddd_core.config import hard_limits
            hard_limits({}, k=int(quota), total_pop=int(summary['population']))
            hard_limit_blocker = topology_blocker
        except (Exception, SystemExit) as exc:
            hard_limit_blocker = str(exc)
            m04_necessary = {'status': 'NOT_RUN_PENDING_APPROVED_LIMITS'}
    synthetic_m06 = _synthetic_m06_contract(contract, source_binding, province=code, quota=int(quota), population=int(summary["population"]))
    fixture_nodes = synthetic_m06.pop('_fixture_nodes')
    fixture_edges = synthetic_m06.pop('_fixture_edges')
    if limit_values and not pending and hard_limit_blocker is None:
        m05_floor, m05_cap = _approved_m05_bounds(
            contract, quota=int(quota), population=int(summary['population']))
    else:
        m05_floor, m05_cap = 1, int(summary['population'])
    try:
        synthetic_m05 = _synthetic_m05_contract(contract, fixture_nodes, fixture_edges,
                                                province=code, floor=m05_floor, cap=m05_cap)
    except (Exception, SystemExit) as exc:
        synthetic_m05 = {'status': 'BLOCKED', 'reason': str(exc),
                         'optimizer_executed': False}
    module_status = {
        'M01': {'status': 'PASS', 'evidence': f'actual INE2025 ZIP and population CSV; consumer loaders; exact join; {len(actual)}/{len(province_frame)}'},
        'M02': {'status': 'PASS', 'evidence': f'actual consumer iter_edges; exact {len(calculated)}/{len(accredited)} match; minimum positive shared line={m02_positive_length_floor_m:g} m (point filter only); buffer/simplify/bridges=0'},
        'M03': {'status': 'PASS', 'evidence': f'actual graph builder; {len(graph_nodes)}/{len(nodes)} identities and attributes; component reconstruction agrees'},
        'M04': {'status': 'PASS_NECESSARY_ONLY' if hard_limit_blocker is None else 'BLOCKED', 'evidence': 'component bound=' + json.dumps(topo, sort_keys=True) + '; population atomic necessary check=' + json.dumps(m04_necessary, sort_keys=True) + '; feasibility is not proven; ' + str(hard_limit_blocker)},
        'M05': {'status': synthetic_m05['status'], 'evidence': 'actual M05 invariant checker on synthetic fixture; no real M04 partition or optimizer call; ' + json.dumps(synthetic_m05, sort_keys=True)},
        'M06': {'status': 'SYNTHETIC_CONTRACT_PASS_ONLY', 'evidence': f'{quota}-unit synthetic fixture audited through adapter and actual M06 joined_unique; no real partition/output; ' + ','.join(input_map['M06']['required_input_fields'])},
    }
    expected_count = int(summary['sections']); expected_population = int(summary['population'])
    if len(actual) != expected_count or int(actual.POB_2025.sum()) != expected_population:
        raise ValueError('M01_PROVINCIAL_TOTAL')
    report = {
        'version': '1.2.0', 'name': 'N08 Congreso provincial M01-M06 diagnostic preflight',
        'date': '2026-10-12', 'base': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'tool_sha256': sha(Path(__file__).read_bytes()),
        'scope': 'single province read-only gates; no real partition or production',
        'province': code, 'identity': 'congreso_' + code,
        'source_binding': source_binding, 'source_evidence': source_evidence,
        'crosswalk_sha256': crosswalk_meta['sha256'], 'population_output_sha256': population_meta['sha256'],
        'topology_manifest_identity_sha256': ident, 'topology_unit_sha256': sha(raw),
        'artifact_transition': transition_evidence or {'status': 'DIRECT_CURRENT_CONTRACT_BINDING'},
        'inputs': {'sections': len(actual), 'population': expected_population,
                   'physical_edges': len(calculated), 'section_graph_components': len(graph_components),
                   'physical_part_components': summary['physical_part_components'],
                   'discontinuous_municipalities': summary['discontinuous_municipalities'],
                   'overlaps': summary['overlap_pairs'], 'enclosed_voids': summary['enclosed_voids'],
                   'k_approved': quota, 'k_rule': 'max(1,(P_i+60000)//120000)'},
        'modules': module_status, 'pending_decisions': pending,
        'contract_production_blockers': blockers,
        'preflight_status': ('PASS_TECHNICAL_PREFLIGHT_PRODUCTION_DISABLED'
                             if report_gate_ready(pending, hard_limit_blocker, synthetic_m05, synthetic_m06, blockers)
                             else 'BLOCKED_CONTRACT_OR_OWNER_DECISIONS'),
        'generation_authorized': False, 'real_partition_created': False,
        'districts_generated': 0, 'published': False,
        'next_action': ('Request separate express authorization for a controlled pilot; this preflight never activates production.'
                        if report_gate_ready(pending, hard_limit_blocker, synthetic_m05, synthetic_m06, blockers) else
                        'Resolve listed owner decisions and national contract blockers; rerun this preflight before separately authorizing a controlled pilot.'),
        'future_command_after_approval': f'python herramientas/preflight_caceres_n08.py --province {code} --parts-dir inputs/partes --output docs/ESTUDIOS/N08_{code}_preflight'
    }
    out_data = (json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()
    output.mkdir(parents=True, exist_ok=True)
    (output / 'PREFLIGHT.json').write_bytes(out_data)
    checkpoint = {'version': '1.2.0', 'province': code, 'status': report['preflight_status'],
                  'source_binding': source_binding, 'topology_manifest_identity_sha256': ident,
                  'topology_unit_sha256': sha(raw), 'preflight_sha256': sha(out_data),
                  'tool_sha256': report['tool_sha256'],
                  'generation_authorized': False, 'districts_generated': 0}
    (output / 'CHECKPOINT.json').write_bytes((json.dumps(checkpoint, sort_keys=True, indent=2) + '\n').encode())
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--province', default='10')
    parser.add_argument('--parts-dir', required=True, type=Path)
    parser.add_argument('--product-dir', type=Path, default=PRODUCT)
    parser.add_argument('--transition-path', type=Path, default=None,
                        help='candidato de transición; permite solo revalidación diagnóstica del producto histórico')
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    report = run(args.parts_dir, args.output, args.province, args.product_dir, args.transition_path)
    print(json.dumps({'province': report['province'], 'status': report['preflight_status'],
                      'modules': {k: v['status'] for k, v in report['modules'].items()},
                      'generation_authorized': report['generation_authorized']}, sort_keys=True))


if __name__ == '__main__':
    main()
