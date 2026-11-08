"""T-113: «histórico: generales 2019-11» del Gestor 2.0 planifica el paso A de T-83 por provincia.

VERSIÓN: 1.0.0 · FECHA: 2026-11-08
ANTERIOR: ninguna (fichero nuevo)
Valores esperados de fuentes independientes: códigos INE de provincia (Huesca 22, Teruel 44, Zaragoza 50) y las tres
provincias sin M06 publicado a 08-11 (Alicante, Barcelona, Málaga: 49 de 52 en datos_abiertos/INDEX.json).
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import gestor_campanas_2 as g  # noqa: E402
import historico_campana as hc  # noqa: E402

H = {"eleccion": "histórico: generales 2019-11", "tipo": "nacional", "territorios": "todos",
     "inicio": "reutilizar progreso", "publicar": "no", "ensemble": "ninguno", "mapa": "407"}


class Plan(unittest.TestCase):
    def test_todos_omite_las_tres_sin_m06(self):
        h = g.build(H, {}, ROOT)["historico"]
        self.assertEqual(h["clave"], "201911")
        self.assertEqual(len(h["include"]), 49)
        self.assertEqual(sorted(h["omitidos"]), ["congreso_alicante", "congreso_barcelona", "congreso_malaga"])

    def test_comunidad_da_sus_provincias_con_codigo_ine(self):
        h = g.build({**H, "territorios": "Aragón"}, {}, ROOT)["historico"]
        self.assertEqual(h["include"], [{"territorio": "congreso_huesca", "provincia": "22"},
                                        {"territorio": "congreso_teruel", "provincia": "44"},
                                        {"territorio": "congreso_zaragoza", "provincia": "50"}])

    def test_no_soportado_falla_con_mensaje(self):
        casos = [({"territorios": "Huesca,Barcelona"}, "congreso_barcelona: sin M06"),
                 ({"eleccion": "histórico: generales 2011"}, "empieza por 2019-11"),
                 ({"publicar": "sí"}, "puerta 04"), ({"tipo": "autonómico"}, "nacional"),
                 ({"mapa": "350"}, "350"), ({"ensemble": "10"}, "ensemble")]
        for kw, msg in casos:
            with self.subTest(kw=kw), self.assertRaisesRegex(g.NoDisponible, msg):
                g.resolve({**H, **kw}, ROOT)

    def test_markdown_y_lanzar_rechazado(self):
        plan = g.build(H, {}, ROOT)
        md = g.markdown(plan, True)
        self.assertIn("Omitidos", md)
        self.assertIn("| congreso_huesca | 22 |", md)
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "plan.json"
            p.write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")
            r = subprocess.run([sys.executable, "herramientas/gestor_campanas_2.py", "lanzar", "--plan", str(p)],
                               cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)
        self.assertIn("jobs «histórico»", r.stderr)


class Fuentes(unittest.TestCase):
    def test_huellas_de_seccionados_historicos_son_las_de_t83(self):
        man = json.loads((ROOT / "datos/resultados/historico/MANIFEST.json").read_text(encoding="utf-8"))
        for t, e in man["territorios"].items():
            with self.subTest(t=t):
                self.assertEqual(e["fuentes"]["historicos"], hc.HISTORICOS)

    def test_reagregacion_rechaza_eleccion_desconocida(self):
        r = subprocess.run([sys.executable, "herramientas/reagregacion_historico.py", "--espejo", ".", "--historicos",
                            ".", "--seccionado", "x", "--padron", "x", "--territorio", "congreso_huesca",
                            "--provincia", "22", "--distritos", "x", "--elecciones", "209901"],
                           cwd=ROOT, capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("ELECCION_DESCONOCIDA", r.stderr)


class Workflow(unittest.TestCase):
    def test_job_historico_tras_el_plan_aprobado(self):
        import yaml
        wf = yaml.safe_load((ROOT / ".github/workflows/gestor-campanas.yml").read_text(encoding="utf-8"))
        job = wf["jobs"]["historico"]
        self.assertEqual(job["needs"], "legislatura")
        self.assertIn("!inputs.solo_plan", job["if"])
        self.assertIn("historico_campana.py ejecutar", json.dumps(job["steps"], ensure_ascii=False))
        self.assertIn("historico", wf["jobs"]["legislatura"]["outputs"])


if __name__ == "__main__":
    unittest.main()
