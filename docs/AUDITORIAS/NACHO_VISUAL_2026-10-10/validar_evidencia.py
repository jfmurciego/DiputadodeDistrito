#!/usr/bin/env python3
"""1.0.0 · 2026-10-10 · Cotejo estático visual aislado, sin motores.
Estado: evidencia auxiliar; no acredita navegador. Origen: nuevo encargo Work.
"""
import csv
import hashlib
import json
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
SOURCE = ROOT / 'docs/AUDITORIAS/NACHO_VALIDACION_2026-10-10'
VIS = SOURCE / 'visualizacion'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Diagnostic(HTMLParser):
    def __init__(self):
        super().__init__()
        self.candidate = None
        self.cell = None
        self.row = []
        self.rows = defaultdict(list)
        self.rects = defaultdict(dict)
        self.links = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'article':
            self.candidate = a['id']
        if tag == 'section' and a.get('id') == 'invalid':
            self.candidate = 'C_hard_invalid'
        if tag == 'rect':
            self.rects[self.candidate][a['data-section']] = a
        if tag == 'tr':
            self.row = []
        if tag == 'td':
            self.cell = ''
        if tag == 'a':
            self.links.append(a['href'])

    def handle_data(self, data):
        if self.cell is not None:
            self.cell += data

    def handle_endtag(self, tag):
        if tag == 'td':
            self.row.append(self.cell)
            self.cell = None
        if tag == 'tr' and self.row:
            self.rows[self.candidate].append(self.row)
        if tag == 'article' or tag == 'section':
            self.candidate = None


def run():
    manifest = json.loads((SOURCE / 'MANIFIESTO.json').read_text())
    for relative, expected in manifest['files'].items():
        assert sha(SOURCE / relative) == expected, relative
    provenance = json.loads((VIS / 'provenance.json').read_text())
    for path, expected in provenance['source_sha256'].items():
        assert sha(Path(path)) == expected, path
    ranking = json.loads((VIS / 'frozen_results.json').read_text())['ranking']
    summary = json.loads((VIS / 'gallery/data/summary.json').read_text())
    doc = Diagnostic()
    html = (VIS / 'diagnostico.html').read_text()
    doc.feed(html)
    csv_rows = list(csv.DictReader((VIS / 'comparison.csv').open()))
    assert len(csv_rows) == 12
    results = {}
    for candidate, frozen in ranking['candidates'].items():
        asset = json.loads((VIS / 'assets_metric' / (candidate + '.geojson')).read_text())
        populations = defaultdict(int)
        assignment = {}
        municipal_districts = defaultdict(set)
        assert len(asset['features']) == 16
        for feature in asset['features']:
            p = feature['properties']
            section = p['section_id']
            district = int(p['district_id'])
            assert section not in assignment
            assignment[section] = district
            populations[district] += p['population']
            municipal_districts[p['municipality']].add(district)
            assert p['population'] == ranking['cell_population_matrix'][int(section)//4][int(section)%4]
            if candidate != 'C_hard_invalid':
                rect = doc.rects[candidate][section]
                assert int(rect['data-district']) == district
                assert int(rect['x']) == (int(section) % 4) * 80
                assert int(rect['y']) == (int(section) // 4) * 80
        assert set(assignment) == {str(i) for i in range(16)}
        ordered_assignment = [assignment[str(i)] for i in range(16)]
        assert hashlib.sha256(json.dumps(ordered_assignment, sort_keys=True).encode()).hexdigest() == frozen['assignment_sha256']
        assert all(len(d) == 1 for d in municipal_districts.values())
        assert [populations[d] for d in range(4)] == frozen['population']
        assert sum(populations.values()) == 4000
        rows = [r for r in csv_rows if r['candidate'] == candidate]
        all_violations = []
        for district, population in populations.items():
            r = next(r for r in rows if int(r['district']) == district)
            violations = []
            if population > 1750:
                violations.append('population_cap:' + str(district))
            if population < 800:
                violations.append('population_floor:' + str(district))
            if not 800 <= population <= 1200:
                violations.append('population_tolerance:' + str(district))
            all_violations.extend(violations)
            assert int(r['population']) == population
            assert [int(r[k]) for k in ('floor', 'cap', 'tolerance_min', 'tolerance_max')] == [800,1750,800,1200]
            assert (r['outlier'] == 'True') == bool(violations)
            assert r['municipality_splits'] == '0'
            assert set(filter(None,r['violations'].split(';'))) == set(violations)
            rendered = next(r for r in doc.rows[candidate] if int(r[0]) == district)
            assert rendered[:5] == [str(district),str(population),'800','1750','800–1200']
            assert float(rendered[5].rstrip('%')) == abs(population-1000)/10
            assert rendered[6:8] == [str(bool(violations)).lower(),'0']
            assert set(rendered[8].split('; ')) == set(violations or ['Ninguno'])
        original = json.loads((VIS / 'copied_reports' / candidate / 'report.json').read_text())
        assert set(all_violations) == set(original['diagnostic']['violations'])
        assert set(all_violations) == set(ranking['actual_DDD_engine_results'][candidate]['violations'])
        assert original['hard_constraints']['all_pass'] == (not all_violations)
        results[candidate] = {'population':frozen['population'],'assignment_sha256':frozen['assignment_sha256'],'violations':all_violations,'municipality_splits':0}
    assert {c['candidate_id'] for c in summary['candidates']} == {'A_lower_L1','B_lower_max'}
    assert summary['invalid_candidates'] == ['C_hard_invalid']
    assert summary['pareto_candidates'] == summary['shortlist'] == ['B_lower_max']
    assert summary['selection_status'] == 'PENDING_FIELD_REVIEW'
    for c in summary['candidates']:
        assert sha(VIS / 'gallery' / c['asset']) == sha(VIS / 'assets_web' / (c['candidate_id']+'.geojson'))
        assert c['metrics']['population']['max_deviation'] == ranking['candidates'][c['candidate_id']]['max_relative']
        copied = json.loads((VIS / 'copied_reports' / c['candidate_id'] / 'report.json').read_text())
        assert c['metrics'] == copied['metrics']
        assert c['profile'] == 'controlled' and c['seed'] == 0
    assert all((VIS / href).is_file() for href in doc.links)
    result = {'version':'1.0.0','status':'PASS_STATIC_ONLY','prior_manifest_files':len(manifest['files']),'candidates':results,'html_csv_rows':12,'svg_sections':32,'links_exist':doc.links,'render_browser':False,'console_checked':False,'exceptions_exercised':False,'scope':'Frozen input/HTML/CSV/GeoJSON consistency; no engines, no browser simulation'}
    (OUT / 'DATOS_RESULTADO.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(result,ensure_ascii=False))


if __name__ == '__main__':
    run()
