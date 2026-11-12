from __future__ import annotations
import json
import shutil
import subprocess
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"dashboard"/"alternativa"
PUBLISHED=ROOT/"publicado"/"dashboard"/"alternativa"
class ActivationDashboardAlternativeTests(unittest.TestCase):
    def test_alternative_is_parallel_and_does_not_replace_current_dashboard(self):
        self.assertTrue((ROOT/"dashboard"/"index.html").exists())
        self.assertTrue((SOURCE/"index.html").exists())
        html=(SOURCE/"index.html").read_text(encoding="utf-8")
        self.assertIn("Estado nacional de fuentes",html)
        self.assertIn('href="../"',html)
    def test_source_and_published_alternative_assets_are_identical(self):
        for name in ("index.html","styles.css","app.js","spain-autonomies.geojson","GEODATA.md","LICENSE-GEODATA.txt"):
            self.assertEqual((SOURCE/name).read_text(encoding="utf-8"),(PUBLISHED/name).read_text(encoding="utf-8"),name)
    def test_real_map_contains_exactly_the_19_ddd_territories(self):
        geo=json.loads((SOURCE/"spain-autonomies.geojson").read_text(encoding="utf-8"))
        ids={f["properties"]["territory_id"] for f in geo["features"]}
        self.assertEqual(len(geo["features"]),19)
        self.assertEqual(ids,{"andalucia","aragon","principado_de_asturias","illes_balears","canarias","cantabria","castilla_y_leon","castilla_la_mancha","cataluna","comunidad_valenciana","extremadura","galicia","madrid","region_de_murcia","comunidad_foral_de_navarra","pais_vasco","la_rioja","ceuta","melilla"})
        self.assertTrue(all(f["geometry"]["type"]=="MultiPolygon" for f in geo["features"]))
    def test_alternative_has_only_four_primary_kpi_states(self):
        js=(SOURCE/"app.js").read_text(encoding="utf-8")
        for label in ("Activadas","Activables","Pendientes","Bloqueadas"): self.assertIn(label,js)
        self.assertNotIn("Actividad reciente",js)
        self.assertNotIn("Sustitución temporal acreditada",js)
    def test_table_is_compact_and_activation_only(self):
        html=(SOURCE/"index.html").read_text(encoding="utf-8")
        for label in ("Territorio","Población","Secciones","Electoral","Estado","Falta"): self.assertIn(label,html)
        for forbidden in ("M04","M06","Generación territorial","Publicación opcional","run_id","receipt"): self.assertNotIn(forbidden,html)
    def test_frontend_consumes_backend_activation_state(self):
        js=(SOURCE/"app.js").read_text(encoding="utf-8")
        self.assertIn("activation?.state",js)
        self.assertIn("source_readiness",js)
        self.assertNotIn("population_year_required ===",js)
        self.assertNotIn("section_year_required ===",js)
    def test_ceuta_and_melilla_have_minimum_28px_hit_targets(self):
        js=(SOURCE/"app.js").read_text(encoding="utf-8")
        css=(SOURCE/"styles.css").read_text(encoding="utf-8")
        self.assertIn('["ceuta","melilla"]',js)
        self.assertIn('setAttribute("r","14")',js)
        self.assertIn('"city-hit "',js)
        self.assertIn(".city-hit{fill:transparent;stroke:transparent;pointer-events:all;cursor:pointer}",css)
        self.assertIn(".city-hit:focus-visible{stroke:currentColor;stroke-width:2;outline:none}",css)

    def test_published_geodata_contains_complete_mit_notice(self):
        geodata=(PUBLISHED/"GEODATA.md").read_text(encoding="utf-8")
        license_text=(PUBLISHED/"LICENSE-GEODATA.txt").read_text(encoding="utf-8")
        self.assertIn("Click That ’Hood",geodata)
        self.assertIn("Copyright (c) 2013-2021 Code for America",geodata)
        self.assertIn("MIT License",license_text)
        self.assertIn("Copyright (c) 2013-2021 Code for America",license_text)
        self.assertIn("Permission is hereby granted, free of charge",license_text)
        self.assertIn('The above copyright notice and this permission notice shall be included',license_text)

    def test_alternative_javascript_is_syntax_valid_when_node_is_available(self):
        node=shutil.which("node")
        if node is None:
            self.skipTest("node no forma parte del contenedor de unittest")
        result=subprocess.run(
            [node,"--check",str(SOURCE/"app.js")],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode,0,result.stderr)
if __name__=="__main__": unittest.main()
