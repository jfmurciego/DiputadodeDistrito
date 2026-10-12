"""Versión 0.1.0; Adaptador diagnóstico Congreso; fecha 2026-10-12.
Alcance: interfaces M01–M06 sin ejecución. Estado: candidato N08.
Cambios: validación nacional aislada. Motivo: evitar herencia autonómica.
Origen: nuevo, sin predecesor. Nunca autoriza generación.
"""
from __future__ import annotations

import math
import re
from collections import defaultdict
from ddd_core.congreso_contract import validate_congress_identity, production_blockers

SHA = re.compile(r"[0-9a-f]{64}\Z")


def _require(condition, reason):
    if not condition:
        raise ValueError(reason)


def physical_components(nodes, edges):
    """Componentes deterministas, incluyendo nodos aislados; aristas no dirigidas."""
    adjacency = {n['id']: set() for n in nodes}
    for e in edges:
        adjacency[e['u']].add(e['v'])
        adjacency[e['v']].add(e['u'])
    unseen = set(adjacency)
    result = []
    while unseen:
        first = min(unseen)
        stack, component = [first], set()
        unseen.remove(first)
        while stack:
            node = stack.pop()
            component.add(node)
            for neighbor in sorted(adjacency[node] & unseen):
                unseen.remove(neighbor)
                stack.append(neighbor)
        result.append(sorted(component))
    return result


def validate_physical_product(contract, nodes, edges, source_binding, *, require_national=True):
    """Validate diagnostic input/output identity, not geometry or authorization.

    Border/hash evidence must additionally be recomputed by the topology builder.
    This validator intentionally cannot certify an edge from its asserted length.
    Partial synthetic products require explicit require_national=False.
    """
    validate_congress_identity(contract)
    _require(contract['accreditation'].get('generation_authorized') is False,
             'GENERATION_MUST_REMAIN_FALSE')
    for kind in ('geometry', 'population'):
        expected = contract['sources'][kind]
        actual = source_binding.get(kind, {})
        _require(actual.get('edition') == expected['edition'] == 2025 and
                 actual.get('sha256') == expected['sha256'], 'SOURCE_BINDING:' + kind)
    by_id = {}
    population = defaultdict(int)
    for n in nodes:
        ident = n.get('id', '')
        _require(isinstance(ident, str) and len(ident) == 10 and ident.isdecimal(), 'CUSEC_INVALID')
        _require(ident not in by_id, 'CUSEC_DUPLICATE')
        province, municipality = n.get('CPRO'), n.get('CUMUN')
        _require(province in {f'{i:02d}' for i in range(1, 53)} and
                 ident[:2] == province and ident[:5] == municipality, 'ADMIN_IDENTITY')
        _require(type(n.get('pop')) is int and n['pop'] >= 0, 'POPULATION_INVALID')
        _require(SHA.fullmatch(n.get('geometry_sha256', '')) is not None, 'GEOMETRY_HASH_INVALID')
        _require(n.get('source_geometry_sha256') == source_binding['geometry']['sha256'], 'NODE_SOURCE_HASH')
        _require(isinstance(n.get('physical_component'), str) and n['physical_component'], 'COMPONENT_MISSING')
        population[province] += n['pop']
        by_id[ident] = n
    pairs = set()
    for e in edges:
        u, v = e.get('u'), e.get('v')
        _require(u in by_id and v in by_id and u != v, 'EDGE_ENDPOINT')
        pair = tuple(sorted((u, v)))
        _require(pair not in pairs, 'EDGE_DUPLICATE')
        pairs.add(pair)
        _require(by_id[u]['CPRO'] == by_id[v]['CPRO'], 'CROSS_PROVINCE')
        border = e.get('shared_border_m')
        _require(type(border) in (float, int) and math.isfinite(border) and border > 0,
                 'POINT_OR_INVALID_CONTACT')
        _require(e.get('edge_type') == 'geometric' and e.get('overlap_m2') == 0,
                 'NON_PHYSICAL_OR_OVERLAPPING_EDGE')
        _require(SHA.fullmatch(e.get('contact_sha256', '')) is not None, 'CONTACT_HASH_INVALID')
    components = physical_components(nodes, edges)
    labels = set()
    for component in components:
        component_labels = {by_id[ident]['physical_component'] for ident in component}
        _require(len(component_labels) == 1, 'COMPONENT_LABEL_CONTRADICTION')
        label = next(iter(component_labels))
        _require(label not in labels, 'COMPONENT_LABEL_REUSED')
        labels.add(label)
    _require(contract['k_decision'].get('total') == 407 and
             contract['k_decision'].get('status') == 'APPROVED_BY_OWNER' and
             contract['k_decision'].get('quota_method', '').startswith('max(1,(P_i+60000)//120000)'),
             'N06_DECISION_INVALID')
    rows = contract['quotas_by_origin_unit']
    quotas = {q['code']: q['k'] for q in rows}
    _require(len(rows) == 52 and set(quotas) == {f'{i:02d}' for i in range(1, 53)} and
             all(type(k) is int and k > 0 for k in quotas.values()), 'N06_QUOTAS_INVALID')
    _require(len(quotas) == 52 and sum(quotas.values()) == 407, 'N06_QUOTAS_INVALID')
    for province, total in population.items():
        _require(quotas[province] == max(1, (total + 60000) // 120000), 'N06_QUOTA_POPULATION')
    if require_national:
        _require(len(by_id) == 36554 and len(population) == 52, 'NATIONAL_COVERAGE')
        _require(sum(population.values()) == 49128297, 'NATIONAL_POPULATION')
    return {'scope': 'congreso', 'diagnostic_only': True, 'generation_authorized': False,
            'nodes': len(nodes), 'edges': len(edges), 'section_graph_components': len(components),
            'physical_land_connectivity': 'NOT_EVIDENCED_BY_SECTION_GRAPH',
            'population': sum(population.values()), 'quotas': quotas,
            'production_blockers': production_blockers(contract)}


def structural_component_bound(component_populations, k):
    """Necessary bound under strict physical contiguity; not a feasibility proof.

    Even zero-population components contain sections requiring coverage.
    """
    _require(type(k) is int and k > 0, 'K_INVALID')
    _require(all(type(p) is int and p >= 0 for p in component_populations), 'COMPONENT_POPULATION_INVALID')
    return {'necessary_condition': len(component_populations) <= k,
            'reason': 'PHYSICAL_COMPONENTS_EXCEED_K' if len(component_populations) > k
                      else 'NO_IMPOSSIBILITY_FROM_COMPONENT_COUNT',
            'feasibility_proven': False}


def engine_input_contract():
    """Field mapping only; not a runnable config or defaults for pending policies."""
    return {'M01': {'id_field': 'CUSEC', 'pop_field': 'POB_2025', 'year': 2025},
            'M02': {'id_field': 'CUSEC', 'province_field': 'CPRO', 'municipality_field': 'CUMUN',
                    'buffer_m': 0, 'simplify_m': 0, 'bridges': []},
            'M03': {'node_fields': ['id', 'pop', 'CPRO', 'CUMUN'], 'edge_fields': ['u', 'v']},
            'M04': {'status': 'BLOCKED', 'required': ['minimum_unit', 'population_limits',
                    'municipal_indivisibility', 'physical_discontinuities']},
            'M05': {'status': 'BLOCKED', 'required_input_fields': ['district_id', 'ddd_unit_id', 'CPRO']},
            'M06': {'status': 'BLOCKED', 'required_input_fields': ['CUSEC', 'district_id', 'POB_2025']}}


def audit_synthetic_partition(contract, nodes, edges, source_binding, output_rows, policy, *, synthetic_fixture=False):
    """Audit only a declared synthetic output against externally approved quotas.

    Pending institutional decisions remain pending. This is not admission and
    never returns a runnable configuration. No real partition is generated.
    Limits are explicit absolute counts for fixtures; no regional defaults.
    Multi-part physical connectivity cannot be inferred from the section graph.
    """
    _require(synthetic_fixture is True, 'SYNTHETIC_FIXTURE_REQUIRED')
    _require(bool(nodes), 'PARTITION_EMPTY_UNIVERSE')
    validate_physical_product(contract, nodes, edges, source_binding, require_national=False)
    _require(isinstance(policy, dict) and set(policy) == {
        'minimum_unit', 'municipal_policy', 'population_floor', 'population_cap'}, 'EXPLICIT_POLICY_REQUIRED')
    _require(policy['minimum_unit'] == 'section', 'MINIMUM_UNIT_UNSUPPORTED')
    _require(policy['municipal_policy'] in ('indivisible', 'splittable'), 'MUNICIPAL_POLICY_REQUIRED')
    floor, cap = policy['population_floor'], policy['population_cap']
    _require(type(floor) in (float, int) and type(cap) in (float, int) and
             math.isfinite(floor) and math.isfinite(cap) and 0 < floor <= cap, 'POPULATION_LIMITS_INVALID')
    by_id = {n['id']: n for n in nodes}
    for n in nodes:
        parts = n.get('physical_part_components')
        _require(isinstance(parts, list) and len(parts) == 1 and
                 isinstance(parts[0], str) and bool(parts[0]), 'PHYSICAL_PART_CONNECTIVITY_NOT_EVIDENCED')
    by_output = {}
    districts = defaultdict(list)
    for row in output_rows:
        _require(isinstance(row, dict) and set(row) == {'id', 'district_id', 'pop'}, 'PARTITION_ROW_INVALID')
        ident = row['id']
        _require(ident in by_id and ident not in by_output, 'PARTITION_COVERAGE')
        _require(type(row['pop']) is int and row['pop'] == by_id[ident]['pop'], 'PARTITION_POPULATION_NOT_CONSERVED')
        label = row['district_id']
        _require(isinstance(label, str) and bool(label.strip()), 'DISTRICT_ID_INVALID')
        by_output[ident] = row
        districts[label].append(ident)
    _require(set(by_output) == set(by_id), 'PARTITION_COVERAGE')
    province_districts = defaultdict(set)
    district_populations = {}
    for label, owned in districts.items():
        provinces = {by_id[ident]['CPRO'] for ident in owned}
        _require(len(provinces) == 1, 'PARTITION_CROSS_PROVINCE')
        province = next(iter(provinces))
        province_districts[province].add(label)
        local_edges = [e for e in edges if e['u'] in owned and e['v'] in owned]
        _require(len(physical_components([by_id[ident] for ident in owned], local_edges)) == 1,
                 'PARTITION_DISTRICT_CONTIGUITY')
        # A section's membership in one land component must agree for the district;
        # connectivity through a MultiPolygon atom is never accepted implicitly.
        land = {by_id[ident]['physical_part_components'][0] for ident in owned}
        _require(len(land) == 1, 'PARTITION_PHYSICAL_LAND_DISCONTINUITY')
        total = sum(by_id[ident]['pop'] for ident in owned)
        _require(floor <= total <= cap, 'PARTITION_HARD_POPULATION_LIMITS')
        district_populations[label] = total
    quotas = {row['code']: row['k'] for row in contract['quotas_by_origin_unit']}
    for province in {n['CPRO'] for n in nodes}:
        _require(len(province_districts[province]) == quotas[province], 'PARTITION_EXTERNAL_QUOTA_MISMATCH')
    if policy['municipal_policy'] == 'indivisible':
        municipalities = defaultdict(set)
        for ident, row in by_output.items():
            municipalities[by_id[ident]['CUMUN']].add(row['district_id'])
        _require(all(len(labels) == 1 for labels in municipalities.values()), 'PARTITION_MUNICIPAL_INTEGRITY')
    return {'status': 'SYNTHETIC_OUTPUT_AUDIT_PASS', 'diagnostic_only': True,
            'generation_authorized': False, 'institutional_policy_approved': False,
            'production_blockers': production_blockers(contract),
            'nodes': len(nodes), 'population': sum(n['pop'] for n in nodes),
            'district_populations': district_populations}
