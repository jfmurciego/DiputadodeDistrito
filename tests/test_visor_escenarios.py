"""Versión 1.0.0; 2026-11-02; candidato. T-27 fase (b): selector del visor con optgroups y conmutador Territorial/Electoral."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NODE = shutil.which("node")

RESULTS = [
    {"id": "m06-c", "kind": "canonical_m06", "label": "M06 territorial · run 1", "territory_id": "t"},
    {"id": "m08-c", "kind": "canonical_m08", "label": "M08 electoral · run 1", "territory_id": "t"},
    {"id": "s6", "kind": "scenario_m06", "label": "M06 · GerryChain 50", "scenario_id": "gc50-9", "strategy": "GerryChain 50", "territory_id": "t"},
    {"id": "s8", "kind": "scenario_m08", "label": "M08 · GerryChain 50", "scenario_id": "gc50-9", "strategy": "GerryChain 50", "territory_id": "t"},
    {"id": "z6", "kind": "scenario_m06", "label": "M06 · GerryChain", "scenario_id": "gc-3", "strategy": "GerryChain", "territory_id": "t"},
    {"id": "e1", "kind": "ensemble_candidate", "label": "Ensemble c1", "ensemble_release_tag": "ensemble-abc", "territory_id": "t"},
    {"id": "st", "kind": "static", "label": "histórico", "territory_id": "t"},
]


def js(expression: str):
    script = f"const e=require({json.dumps(str(ROOT / 'visor/escenarios.js'))});const R={json.dumps(RESULTS)};console.log(JSON.stringify({expression}))"
    return json.loads(subprocess.run([NODE, "-e", script], check=True, capture_output=True, text=True).stdout)


@unittest.skipIf(NODE is None, "node requerido")
class VisorEscenariosTests(unittest.TestCase):
    def test_grupos_ordenados_canonico_escenarios_ensembles(self):
        groups = js("e.groupResults(R).map(g=>[g.key,g.label,g.items.map(i=>i.id)])")
        self.assertEqual([g[0] for g in groups], ["canonical", "scenario:gc-3", "scenario:gc50-9", "ensemble:ensemble-abc"])
        self.assertEqual(groups[0][2], ["m06-c", "m08-c", "st"])
        self.assertEqual(groups[2][1], "GerryChain 50 · gc50-9")
        self.assertEqual(groups[3][1], "Ensemble · ensemble-abc")

    def test_conmutador_territorial_y_electoral(self):
        electoral = js('e.groupsForStage(R,"electoral").map(g=>[g.key,g.items.map(i=>i.id)])')
        self.assertEqual(electoral, [["canonical", ["m08-c"]], ["scenario:gc50-9", ["s8"]]])
        territorial = js('e.groupsForStage(R,"territorial").map(g=>[g.key,g.items.map(i=>i.id)])')
        self.assertEqual([g[0] for g in territorial], ["canonical", "scenario:gc-3", "scenario:gc50-9", "ensemble:ensemble-abc"])
        self.assertEqual(js("e.availableStages(R)"), {"territorial": True, "electoral": True})
        self.assertEqual(js('e.availableStages(R.filter(r=>r.kind.endsWith("m06")))'), {"territorial": True, "electoral": False})

    def test_nada_se_pierde_ni_se_mezcla(self):
        ids = js("e.groupResults(R).flatMap(g=>g.items.map(i=>i.id))")
        self.assertEqual(sorted(ids), sorted(r["id"] for r in RESULTS))

    def test_cableado_en_index_app_y_publicador(self):
        html = (ROOT / "visor/index.html").read_text(encoding="utf-8")
        app = (ROOT / "visor/app.js").read_text(encoding="utf-8")
        wf = (ROOT / ".github/workflows/_reutilizable-publicar-sitio.yml").read_text(encoding="utf-8")
        self.assertLess(html.index("escenarios.js"), html.index('src="app.js"'))
        self.assertIn('id="stage-toggle"', html)
        self.assertIn("DDDEscenarios.groupsForStage", app)
        self.assertIn("optgroup", app)
        self.assertRegex(wf, r"cp visor/index\.html visor/app\.js visor/escenarios\.js visor/styles\.css")
        self.assertIn("node --check visor/escenarios.js", wf)


if __name__ == "__main__":
    unittest.main()
