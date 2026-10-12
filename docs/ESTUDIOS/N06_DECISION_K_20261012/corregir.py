#!/usr/bin/env python3
"""Versión 1.0.0; Corrección institucional N06; 2026-10-12.
Alcance: reparto analítico 2025; WAIT_OWNER; origen: nuevo.
Cambios/motivo: primacía de mónada, mínimo uno y excepciones declarativas.
"""
import csv
import hashlib
import json
from fractions import Fraction as F
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = ROOT / 'docs/ESTUDIOS/modelo_nacional_2025_120000/fuente_poblacion.json'

def allocate(populations):
    if set(populations) != {f'{i:02d}' for i in range(1, 53)}:
        raise ValueError('COVERAGE_INVALID')
    if any(type(p) is not int or p <= 0 for p in populations.values()):
        raise ValueError('POPULATION_INVALID')
    return {c: max(1, (p + 60000) // 120000) for c, p in sorted(populations.items())}

def build():
    source = json.loads(SOURCE.read_text())
    if source['population_year'] != 2025 or source['reference_date'] != '2025-01-01':
        raise ValueError('EDITION_INVALID')
    populations = {r['province_code']: r['population'] for r in source['rows']}
    if len(source['rows']) != 52:
        raise ValueError('DUPLICATE_OR_MISSING')
    assignment = allocate(populations)
    total = sum(assignment.values())
    rows = []
    for r in sorted(source['rows'], key=lambda r: r['province_code']):
        c, p = r['province_code'], r['population']
        k = assignment[c]
        mean = F(p, k)
        rows.append(dict(province_code=c, name='Islas Baleares' if c=='07' else r['name'],
                         population_2025=p, quota=str(F(p, 120000)), k_province=k,
                         mean=str(mean), deviation=str(mean-120000),
                         deviation_percent=str((mean-120000)/1200),
                         national_deviation=str(mean-F(sum(populations.values()), total)),
                         exception='SMALL_WHOLE_CIRCUMSCRIPTION' if p < 100000 else 'NONE'))
    summary = dict(metadata=dict(version='1.0.0', name='Recomendación DDD N06 corregida',
                   date='2026-10-12', scope='aritmética 2025, sin generación', status='WAIT_OWNER',
                   changes='mínimo uno, half-up provincial', reason='mandato del propietario', origin='nuevo'),
                   population_total=sum(populations.values()), k_total=total,
                   formula='max(1, (P + 60000) // 120000)', target=120000,
                   national_mean=str(F(sum(populations.values()), total)),
                   mae=str(sum(abs(F(r['deviation']))*r['k_province'] for r in rows)/total),
                   exceptions=[r for r in rows if r['exception'] != 'NONE'],
                   source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                   legal_k_constraint=None, rounding='nearest_half_up',
                   geographical_exceptions_status='PREDECLARED_POLICY_PENDING_ACCREDITED_REGISTER',
                   rows=rows)
    return rows, summary

if __name__ == '__main__':
    rows, summary = build()
    (HERE/'resultados/correccion_ddd.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n')
    with (HERE/'resultados/reparto_ddd_52.csv').open('w', newline='') as stream:
        writer=csv.DictWriter(stream, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    print(f"K={summary['k_total']}; 52 circunscripciones; WAIT_OWNER")
