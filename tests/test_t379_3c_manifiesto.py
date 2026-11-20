"""T-379 3c-i (Planificador 20-11): puerta 04 en la cadena de P00 Campaña y huellas para el manifiesto por territorio.

Lee los ficheros reales; cada regla con su control negativo:
- `puerta_04` (fase electoral_product) tras P30, obligatoria en «Cerrar P30», con el M08 del espacio del territorio, y la
  puerta real (validar_puerta_ejecucion 1.0.2) acepta ese nombre; sin espacio, solo el canónico (como antes).
- Las HUELLAS de «Cerrar P10/P20/P30», evaluadas como lo hace GitHub (`format`, `toJSON`), dan JSON con lo que el cierre
  necesita (campana_registro.argumentos_manifiesto) y conservan las claves de la 1.0.0.
- Equivalencia: quitando lo que añade la 1.1.0, p00-cadena.yml es la 1.0.0 (legacy); p00-campana.yml solo cambia la
  llamada a `cerrar` (`--source-sha`).
"""
import copy
import json
import re
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / ".github" / "workflows"
LEGACY = ROOT / "legacy" / "workflows"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "herramientas"))
from herramientas.validar_puerta_ejecucion import _artifact_name_is_consistent as nombre_ok  # noqa: E402

NS = "campaign-900-1--01--aut11"


def leer(ruta):
    return yaml.safe_load(Path(ruta).read_text(encoding="utf-8"))


def paso(job, id_):
    return next(p for p in job["steps"] if p.get("id") == id_)


def evaluar(expr, valores):
    """`${{ format('plantilla', a, b, …) }}` de GitHub: {N} por el argumento, {{ y }} literales. `valores` da, para cada
    argumento (texto de la expresión), su valor ya evaluado."""
    m = re.fullmatch(r"\$\{\{ format\('(.*?)', (.*)\) \}\}", expr.strip())
    plantilla, args = m.group(1), [a.strip() for a in m.group(2).split(", ")]
    # «steps.optim.outputs.json || '{}'» lleva una coma dentro de comillas: no la hay; cada argumento es simple.
    return plantilla.format(*[valores[a] for a in args])


PUERTA = {"decision": "VALIDADO", "artifact_digest": "abc", "phase_decision": "PASS", "run_id": "900", "artifact_name": "x"}


class Puerta04(unittest.TestCase):
    def setUp(self):
        self.jobs = leer(WF / "p00-cadena.yml")["jobs"]

    def test_puerta_04_tras_p30_con_el_m08_del_territorio(self):
        j = self.jobs["puerta_04"]
        self.assertEqual(j["uses"], "./.github/workflows/_reutilizable-puerta-validacion.yml")
        self.assertEqual(j["needs"], ["plan", "p30"])
        self.assertIn("!cancelled()", j["if"])
        self.assertIn("needs.p30.result == 'success'", j["if"])
        w = j["with"]
        self.assertEqual(w["phase"], "electoral_product")
        self.assertEqual(w["artifact_name"], "${{ format('ddd-state-{0}-M08-{1}', github.run_id, needs.plan.outputs.ns) }}")
        self.assertEqual(w["artifact_namespace"], "${{ needs.plan.outputs.ns }}")
        self.assertEqual(w["source_ref"], "${{ github.sha }}")

    def test_obligatoria_al_cerrar_p30(self):
        j = self.jobs["cerrar_p30"]
        self.assertIn("puerta_04", j["needs"])
        env = paso(j, "cerrar")["env"]
        self.assertEqual(env["OBLIGATORIOS"].split(), ["puerta_03", "p30", "puerta_04"])
        self.assertIn('"puerta_04":"{2}"', env["RESULTADOS"])

    def test_la_puerta_real_acepta_el_m08_con_espacio(self):
        self.assertTrue(nombre_ok("electoral_product", "aut11", "2025", "900", f"ddd-state-900-M08-{NS}", NS))
        self.assertTrue(nombre_ok("electoral_product", "aut11", "2025", "900", "ddd-state-900-M08"))  # como antes
        # controles negativos: espacio a secas, de otro territorio, de otro run, hueco 00 y espacio sin declarar
        self.assertFalse(nombre_ok("electoral_product", "aut11", "2025", "900", "ddd-state-900-M08-aut11", "aut11"))
        self.assertFalse(nombre_ok("electoral_product", "nac22", "2025", "900", f"ddd-state-900-M08-{NS}", NS))
        self.assertFalse(nombre_ok("electoral_product", "aut11", "2025", "901", f"ddd-state-901-M08-{NS}", NS))
        ns00 = "campaign-900-1--00--aut11"
        self.assertFalse(nombre_ok("electoral_product", "aut11", "2025", "900", f"ddd-state-900-M08-{ns00}", ns00))
        self.assertFalse(nombre_ok("electoral_product", "aut11", "2025", "900", f"ddd-state-900-M08-{NS}"))
        # el M06 no cambia
        self.assertTrue(nombre_ok("territorial_product", "aut11", "2025", "900", f"ddd-state-900-M06-{NS}", NS))
        self.assertFalse(nombre_ok("territorial_product", "aut11", "2025", "900", f"ddd-state-900-M08-{NS}", NS))


class Huellas(unittest.TestCase):
    """Las huellas, evaluadas como en GitHub, llevan lo que el manifiesto necesita."""

    def setUp(self):
        self.jobs = leer(WF / "p00-cadena.yml")["jobs"]

    def huellas(self, job, valores):
        return json.loads(evaluar(paso(self.jobs[job], "cerrar")["env"]["HUELLAS"], valores))

    def test_p10_plan_y_puerta_01(self):
        h = self.huellas("cerrar_p10", {
            "needs.p11.outputs.artifact_digest": "d1", "needs.p12.outputs.artifact_digest": "d2",
            "needs.plan.outputs.territory_id": "aut11", "needs.plan.outputs.territory_name": "Extremadura",
            "needs.plan.outputs.edition": "2025", "needs.plan.outputs.modo": "catalog_source",
            "toJSON(needs.puerta_01.outputs)": json.dumps(PUERTA, indent=2)})
        self.assertEqual((h["paquete_territorial"], h["paquete_electoral"]), ("d1", "d2"))  # claves de la 1.0.0
        self.assertEqual(h["plan"], {"territory_id": "aut11", "territory_name": "Extremadura", "edition": "2025",
                                     "modo": "catalog_source"})
        self.assertEqual(h["puerta_01"], PUERTA)
        # el plan publica `modo` (execution_mode del manifiesto)
        self.assertEqual(self.jobs["plan"]["outputs"]["modo"], "${{ steps.plan.outputs.modo }}")
        self.assertIn('echo "modo=$modo"', paso(self.jobs["plan"], "plan")["run"])

    def test_p20_puerta_02_y_optimizacion(self):
        optim = '{"requested_algorithm":"Canónico","effective_algorithm":"Canónico","fallback":false,"fallback_reason":null}'
        h = self.huellas("cerrar_p20", {"needs.puerta_02.outputs.artifact_digest": "d6",
                                        "toJSON(needs.puerta_02.outputs)": json.dumps(PUERTA),
                                        "steps.optim.outputs.json || '{}'": optim})
        self.assertEqual(h["m06"], "d6")
        self.assertEqual(h["puerta_02"], PUERTA)
        self.assertEqual(h["optimizacion"]["effective_algorithm"], "Canónico")
        # sin puerta 02 (paso apartado): JSON válido igualmente
        h = self.huellas("cerrar_p20", {"needs.puerta_02.outputs.artifact_digest": "",
                                        "toJSON(needs.puerta_02.outputs)": "{}", "steps.optim.outputs.json || '{}'": "{}"})
        self.assertEqual(h["optimizacion"], {})

    def test_p20_lee_la_optimizacion_del_m06(self):
        j = self.jobs["cerrar_p20"]
        nombres = [p.get("id") or p.get("name") for p in j["steps"]]
        self.assertLess(nombres.index("optim"), nombres.index("cerrar"))
        bajar = next(p for p in j["steps"] if str(p.get("uses", "")).startswith("actions/download-artifact"))
        self.assertEqual(bajar["with"]["name"], "${{ needs.puerta_02.outputs.artifact_name }}")
        self.assertEqual(bajar["with"]["run-id"], "${{ github.run_id }}")
        self.assertIn("OPTIMIZATION_EXECUTION.json", paso(j, "optim")["run"])

    def test_p30_puertas_03_y_04(self):
        h = self.huellas("cerrar_p30", {"toJSON(needs.puerta_03.outputs)": json.dumps(PUERTA),
                                        "toJSON(needs.puerta_04.outputs)": json.dumps(PUERTA)})
        self.assertEqual(set(h), {"puerta_03", "puerta_04"})

    def test_bloque_optim_bajo_pipefail(self):
        import subprocess
        import tempfile
        run = paso(self.jobs["cerrar_p20"], "optim")["run"]
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "out"
            r = subprocess.run(["bash", "-eo", "pipefail", "-c", run], cwd=td, env={"GITHUB_OUTPUT": str(out), "PATH": "/usr/bin:/bin"},
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 51, r.stderr)  # sin evidencia: falla
            d = Path(td) / ".ddd-optimization-state" / "x"
            d.mkdir(parents=True)
            (d / "OPTIMIZATION_EXECUTION.json").write_text(
                '{"requested_algorithm":"Canónico","effective_algorithm":"Canónico","fallback":false,"otro":1}', encoding="utf-8")
            r = subprocess.run(["bash", "-eo", "pipefail", "-c", run], cwd=td, env={"GITHUB_OUTPUT": str(out), "PATH": "/usr/bin:/bin"},
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            linea = out.read_text(encoding="utf-8").strip()
            self.assertTrue(linea.startswith("json="))
            self.assertEqual(json.loads(linea[5:]), {"requested_algorithm": "Canónico", "effective_algorithm": "Canónico",
                                                     "fallback": False, "fallback_reason": None})


class Equivalencia(unittest.TestCase):
    """Sin lo que añade la 3c-i, los dos workflows son los de la 1.0.0 (legacy)."""

    def test_cadena(self):
        nuevo, viejo = leer(WF / "p00-cadena.yml"), leer(LEGACY / "p00-cadena_v1.0.0_20261120.yml")
        d = copy.deepcopy(nuevo)
        j = d["jobs"]
        del j["puerta_04"]
        del j["plan"]["outputs"]["modo"]
        p = paso(j["plan"], "plan")
        p["run"] = re.sub(r'(?m)^ *echo "modo=\$modo"\n', "", p["run"])
        j["cerrar_p20"]["steps"] = [s for s in j["cerrar_p20"]["steps"]
                                    if s.get("id") != "optim" and not str(s.get("uses", "")).startswith("actions/download-artifact")]
        j["cerrar_p30"]["needs"].remove("puerta_04")
        for nombre in ("cerrar_p10", "cerrar_p20", "cerrar_p30"):
            paso(j[nombre], "cerrar")["env"]["HUELLAS"] = paso(viejo["jobs"][nombre], "cerrar")["env"]["HUELLAS"]
        env = paso(j["cerrar_p30"], "cerrar")["env"]
        env["OBLIGATORIOS"], env["RESULTADOS"] = (paso(viejo["jobs"]["cerrar_p30"], "cerrar")["env"][k]
                                                  for k in ("OBLIGATORIOS", "RESULTADOS"))
        self.assertEqual(d, viejo)
        # control negativo: un cambio más no pasa
        d["jobs"]["p30"]["with"]["persist_state"] = False
        self.assertNotEqual(d, viejo)

    def test_campana(self):
        nuevo = (WF / "p00-campana.yml").read_text(encoding="utf-8")
        viejo = (LEGACY / "p00-campana_v1.0.0_20261120.yml").read_text(encoding="utf-8")
        cuerpo = lambda t: t.split("\nname: ", 1)[1]  # noqa: E731  (sin la cabecera de versión)
        self.assertEqual(cuerpo(nuevo).count('--source-sha "$GITHUB_SHA"'), 2)
        self.assertEqual(cuerpo(nuevo).replace(' --source-sha "$GITHUB_SHA"', ""), cuerpo(viejo))


if __name__ == "__main__":
    unittest.main()
