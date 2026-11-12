"""T-113: «histórico: generales 2019-11» del Gestor 2.0 planifica el paso A de T-83 por provincia.

VERSIÓN: 1.1.0 · FECHA: 2026-11-11
CAMBIOS: 1.1.0 (T-247): el plan se evalúa sobre una raíz con el INDEX de M06 publicados congelado (52 circunscripciones,
  tests/fixtures/t247_m06_publicados_52.json) y composiciones presentes; antes leía datos_abiertos/INDEX.json vivo, que
  reescribe la 05 del bot (9c0cab12 lo dejó en 17 territorios, sin Huesca) y ponía main en rojo sin tocar este código.
ANTERIOR: legacy/tests/test_t113_gestor_historico_v1.0.0_20261111.py
Valores esperados de fuentes independientes: códigos INE de provincia (Huesca 22, Teruel 44, Zaragoza 50) y las 52
circunscripciones del Congreso. No se fija cuántas tienen M06 publicado (cambia con cada 00): lo no soportado se prueba
con un territorio inexistente.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import gestor_campanas_2 as g  # noqa: E402
import historico_campana as hc  # noqa: E402

H = {"eleccion": "histórico: generales 2019-11", "tipo": "nacional", "territorios": "todos",
     "inicio": "reutilizar progreso", "publicar": "no", "ensemble": "ninguno", "mapa": "407"}


M06_PUBLICADOS = json.loads((REPO / "tests/fixtures/t247_m06_publicados_52.json").read_text(encoding="utf-8"))["territorios"]


def raiz_congelada(m06: list[str], tmp: Path) -> Path:
    """Raíz enlazada al repositorio con el estado que lee el plan fijado: INDEX con ``m06`` y su composición."""
    for e in REPO.iterdir():
        if e.name not in {".git", "datos_abiertos", "datos"}:
            (tmp / e.name).symlink_to(e)
    for sub in ("datos", "datos_abiertos"):
        (tmp / sub).mkdir()
        for e in (REPO / sub).iterdir():
            if e.name not in {"composicion", "INDEX.json"}:
                (tmp / sub / e.name).symlink_to(e)
    (tmp / "datos_abiertos/INDEX.json").write_text(json.dumps({"territorios": {t: {} for t in m06}}), encoding="utf-8")
    (tmp / "datos/composicion").mkdir()
    for t in m06:
        (tmp / f"datos/composicion/{t}.csv").write_text("seccion,distrito,poblacion\n", encoding="utf-8")
    return tmp


class Plan(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.addCleanup(self._td.cleanup)
        self.root = raiz_congelada(M06_PUBLICADOS, Path(self._td.name))

    def test_fixture_son_las_52_circunscripciones(self):
        self.assertEqual(len(set(M06_PUBLICADOS)), 52)
        self.assertTrue(all(t.startswith("congreso_") for t in M06_PUBLICADOS))

    def test_sin_m06_en_el_index_se_omite(self):
        # Invariante: un territorio fuera de datos_abiertos/INDEX.json no entra en el plan aunque tenga composición.
        with tempfile.TemporaryDirectory() as td:
            root = raiz_congelada([t for t in M06_PUBLICADOS if t != "nac22"], Path(td))
            (root / "datos/composicion/congreso_huesca.csv").write_text("x\n", encoding="utf-8")
            h = hc.plan(H["eleccion"], [{"territory_id": "nac22", "codigo": "22"},
                                        {"territory_id": "nac44", "codigo": "44"}], False, root)
            self.assertEqual(h["include"], [{"territorio": "nac44", "provincia": "44"}])
            self.assertIn("sin M06 publicado", h["omitidos"]["nac22"])

    def test_todos_cubre_las_52(self):
        h = g.build(H, {}, self.root)["historico"]
        self.assertEqual(h["clave"], "201911")
        self.assertEqual(len(h["include"]) + len(h["omitidos"]), 52)

    def test_sin_m06_se_omite_con_todos_y_falla_si_se_pide(self):
        filas = [{"territory_id": "nac22", "codigo": "22"}, {"territory_id": "congreso_narnia", "codigo": "99"}]
        h = hc.plan(H["eleccion"], filas, False, self.root)
        self.assertEqual(h["include"], [{"territorio": "nac22", "provincia": "22"}])
        self.assertIn("sin M06 publicado", h["omitidos"]["congreso_narnia"])
        with self.assertRaisesRegex(hc.NoDisponible, "congreso_narnia: sin M06"):
            hc.plan(H["eleccion"], filas, True, self.root)

    def test_comunidad_da_sus_provincias_con_codigo_ine(self):
        h = g.build({**H, "territorios": "Aragón"}, {}, self.root)["historico"]
        self.assertEqual(h["include"], [{"territorio": "nac22", "provincia": "22"},
                                        {"territorio": "nac44", "provincia": "44"},
                                        {"territorio": "nac50", "provincia": "50"}])

    def test_no_soportado_falla_con_mensaje(self):
        casos = [({"publicar": "sí"}, "puerta 04"), ({"tipo": "autonómico"}, "nacional"),
                 ({"mapa": "350"}, "350"), ({"ensemble": "10"}, "ensemble")]
        for kw, msg in casos:
            with self.subTest(kw=kw), self.assertRaisesRegex(g.NoDisponible, msg):
                g.resolve({**H, **kw}, self.root)

    def test_las_cinco_generales_se_planifican(self):
        # Claves del espejo T-89 (fuente independiente: nazioenbehatokia, 52 provincias por elección).
        esperado = {"2011": "201111", "2015": "201512", "2016": "201606", "2019-04": "201904", "2019-11": "201911"}
        for nombre, clave in esperado.items():
            with self.subTest(e=nombre):
                h = g.build({**H, "eleccion": f"histórico: generales {nombre}", "territorios": "Aragón"}, {}, self.root)["historico"]
                self.assertEqual(h["clave"], clave)
                self.assertEqual(h["prueba"], {"territorio": "nac22", "provincia": "22"})
                self.assertEqual(len(h["include"]), 3)
                self.assertIn("Lote de prueba: nac22", hc.plan_markdown(h))

    def test_markdown_y_lanzar_rechazado(self):
        plan = g.build(H, {}, self.root)
        md = g.markdown(plan, True)
        self.assertIn("| nac22 | 22 |", md)
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "plan.json"
            p.write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")
            r = subprocess.run([sys.executable, "herramientas/gestor_campanas_2.py", "lanzar", "--plan", str(p)],
                               cwd=REPO, capture_output=True, text=True)
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
                            ".", "--seccionado", "x", "--padron", "x", "--territorio", "nac22",
                            "--provincia", "22", "--distritos", "x", "--elecciones", "209901"],
                           cwd=ROOT, capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("ELECCION_DESCONOCIDA", r.stderr)


class Workflow(unittest.TestCase):
    def test_job_historico_tras_el_plan_aprobado(self):
        import yaml
        wf = yaml.safe_load((ROOT / ".github/workflows/gestor-campanas.yml").read_text(encoding="utf-8"))
        job = wf["jobs"]["historico"]
        self.assertEqual(job["needs"], ["legislatura", "historico_prueba"])
        self.assertIn("success()", job["if"])
        self.assertIn("max_paralelo", job["strategy"]["max-parallel"])
        prueba = wf["jobs"]["historico_prueba"]
        self.assertEqual(prueba["needs"], "legislatura")
        self.assertNotIn("max-parallel", prueba["strategy"])
        self.assertIn("!inputs.solo_plan", job["if"])
        self.assertIn("historico_campana.py ejecutar", json.dumps(job["steps"], ensure_ascii=False))
        self.assertIn("historico", wf["jobs"]["legislatura"]["outputs"])


if __name__ == "__main__":
    unittest.main()
