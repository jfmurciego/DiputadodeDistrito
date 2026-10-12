"""VERSIÓN 1.0.0; FECHA 2026-10-12; factibilidad necesaria Congreso.
ALCANCE diagnóstico; ESTADO propuesta no aprobada; ORIGEN nuevo.
CAMBIOS/MOTIVO: cuantificar opciones sin adoptar límites autonómicos.
"""
from fractions import Fraction


def ceil_fraction(value): return -(-value.numerator // value.denominator)


def evaluate_option(product, tolerance, *, basis="provincial_mean"):
    """Necessary arithmetic bounds only, never construction or sufficiency.

    Units remain original sections; population is never allocated to polygon
    parts. Municipal atomicity is examined separately as a hypothetical rule.
    """
    s = product['summary']; k = s['k']; total = s['population']
    target = Fraction(total, k) if basis == 'provincial_mean' else Fraction(120000)
    t = Fraction(tolerance); lower, upper = target * (1-t), target * (1+t)
    # Express population exception is provincial; does not waive geography.
    exceptional = s['CPRO'] in ('42', '51', '52')
    records = []
    for component in product['physical_components']:
        population = component['population']; section_count = len(component['sections'])
        minimum = max(1, ceil_fraction(Fraction(population, 1) / upper))
        maximum = min(section_count, int(Fraction(population, 1) / lower))
        if exceptional and len(product['physical_components']) == 1:
            minimum = maximum = 1
        records.append({'component': component['id'], 'population': population,
                        'minimum_districts': minimum, 'maximum_districts': maximum,
                        'interval_nonempty': minimum <= maximum})
    min_total = sum(r['minimum_districts'] for r in records)
    max_total = sum(r['maximum_districts'] for r in records)
    impossible = (not all(r['interval_nonempty'] for r in records) or not min_total <= k <= max_total)
    large_municipalities = [r for r in product['municipalities'] if Fraction(r['population']) > upper]
    too_large_sections = [n['id'] for n in product['nodes'] if Fraction(n['pop']) > upper]
    if exceptional: large_municipalities = []; too_large_sections = []
    indivisible_impossible = bool(large_municipalities) or k > len(product['municipalities'])
    if exceptional: indivisible_impossible = False
    return {'CPRO': s['CPRO'], 'basis': basis, 'tolerance': str(t), 'target': str(target),
            'lower': str(lower), 'upper': str(upper), 'exception': exceptional,
            'ordinary_mean_within_limits': exceptional or lower <= Fraction(total,k) <= upper,
            'necessary_component_intervals': records, 'minimum_total': min_total, 'maximum_total': max_total,
            'arithmetic_impossibility_section_graph': impossible,
            'municipal_indivisibility_impossibility_by_size_or_count': indivisible_impossible,
            'municipalities_above_upper': [{'CUMUN': r['CUMUN'], 'population': r['population'],
                                          'minimum_districts_by_population': ceil_fraction(Fraction(r['population']) / upper)}
                                         for r in large_municipalities],
            'sections_above_upper': too_large_sections,
            'physical_parts_population_unallocated': bool(s['multipart_sections_spanning_physical_components']),
            'feasibility_proven': False, 'institutionally_approved': False, 'generation_authorized': False}


def evaluate_national(products):
    result = []
    for basis in ('reference_120000', 'provincial_mean'):
        for tolerance in ('1/10', '3/20', '1/5'):
            rows = [evaluate_option(p, tolerance, basis=basis) for p in products]
            result.append({'basis': basis, 'tolerance': tolerance,
                           'mean_outside_limits': [r['CPRO'] for r in rows if not r['ordinary_mean_within_limits']],
                           'component_arithmetic_blocked': [r['CPRO'] for r in rows if r['arithmetic_impossibility_section_graph']],
                           'municipal_indivisibility_blocked': [r['CPRO'] for r in rows if r['municipal_indivisibility_impossibility_by_size_or_count']],
                           'municipalities_requiring_split': sum(len(r['municipalities_above_upper']) for r in rows),
                           'sections_above_upper': sum(len(r['sections_above_upper']) for r in rows), 'units': rows})
    return {'schema': 'ddd.congress-population-proposal/1.0', 'reference': 120000,
            'recommendation': {'basis': 'provincial_mean', 'tolerance': '3/20',
                               'municipal_policy': 'preserve connected municipalities when compatible; allow necessary subdivision by official sections, no invented connections',
                               'approved': False}, 'options': result, 'generation_authorized': False}
