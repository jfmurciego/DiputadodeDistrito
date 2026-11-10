"""T-221: con motor=motor2 la certificación lee el plan ganador del P30, no el informe M05 canónico."""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "herramientas/estado_produccion.py"
WORKFLOW = ROOT / ".github/workflows/_reutilizable-generacion-territorial.yml"

# Informe M05 canónico: 0 fuera de tolerancia (lo que se certificaba antes con motor2).
M05 = {"objective_start": [0, 0.0, 2, 0.20, 0.3], "objective_final": [0, 0.0, 0, 0.11, 0.2],
       "population_repair": {"enabled": False}}
GEO = {"schema": "ddd.geometric-components-audit/2.0", "decision": "PASS", "governed_exceptions": 0,
       "blocked_districts": 0, "policy_mismatches": 0, "contract_blockers": [], "districts": []}
COMPOSICION = "section_code,district_id\n2600101001,1\n2600101002,2\n"


def p30_la_rioja(composicion_sha256):
    """Cifras del P30.json real de La Rioja (00 simulada en local, T-221, huella_resultado 7bb9b44b…): gana
    ponderado-s2009387672, 78 secciones cambiadas, fuera_tolerancia=1 y desvío máximo igual al del canónico."""
    return {"schema": "ddd.motor2-p30/1.0", "territorio": "la_rioja", "ganador": "ponderado-s2009387672",
            "valido": True, "estado_ganador": "VALIDO", "estado": "P30_GANA_OTRO_PLAN", "rehacer_m06": True,
            "secciones_cambiadas": 78,
            "huella_resultado": "7bb9b44b3a51690d47632914979669ca8339566ef9229f1663d91dc59eee4675",
            "metricas": {"ganador": {"fuera_tolerancia": 1, "desvio_max": 0.4177583606903271},
                         "canonico": {"fuera_tolerancia": 1, "desvio_max": 0.4177583606903271}},
            "verificacion_m06": {"igual_al_ganador": True, "composicion_sha256": composicion_sha256},
            "m05_restaurada": True}


class Motor2Certificacion(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = Path(self.tmp.name)
        self.d = d
        self.params = d / "contrato.yaml"
        self.params.write_text(yaml.safe_dump({
            "meta": {"run_name": "fixture", "year": 2025},
            "modulos": {"modulo_05_optimizar_distritos": {"out_report": "runs/{run_id}/m05.json"},
                        "modulo_06_consolidar_distritos": {"out_composition_csv": "runs/{run_id}/composicion.csv"}},
        }), encoding="utf-8")
        self.runs = d / "runs" / "r1"
        (self.runs / "p30_motor2").mkdir(parents=True)
        (self.runs / "m05.json").write_text(json.dumps(M05), encoding="utf-8")
        (self.runs / "composicion.csv").write_text(COMPOSICION, encoding="utf-8")
        self.sha = hashlib.sha256(COMPOSICION.encode()).hexdigest()
        (d / "geo.json").write_text(json.dumps(GEO), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def escribir_p30(self, payload):
        (self.runs / "p30_motor2" / "P30.json").write_text(json.dumps(payload), encoding="utf-8")

    def run_status(self, *extra, name="status.json"):
        out = self.d / "out" / name
        subprocess.run([sys.executable, str(SCRIPT), "--params", str(self.params), "--territory-id", "la_rioja",
                        "--run-id", "r1", "--from-stage", "M01", "--to-stage", "M06",
                        "--geometric-outcome", "success", "--geometric-decision", "PASS",
                        "--geometric-audit", str(self.d / "geo.json"), "--output", str(out), *extra],
                       check=True, cwd=ROOT, capture_output=True, text=True)
        return out.read_bytes(), json.loads(out.read_text(encoding="utf-8"))

    def test_motor2_certifica_con_el_ganador_de_la_rioja(self):
        self.escribir_p30(p30_la_rioja(self.sha))
        _, s = self.run_status("--motor", "motor2", "--runs-dir", str(self.runs))
        self.assertEqual(s["population_evidence_source"], "MOTOR2_P30")
        self.assertEqual(s["population_outliers_after"], 1)  # el M05 canónico decía 0
        self.assertEqual(s["population_max_deviation_after"], 0.4177583606903271)
        self.assertEqual(s["population_outliers_before"], 1)
        self.assertEqual(s["motor2_ganador"], "ponderado-s2009387672")
        self.assertEqual(s["motor2_secciones_cambiadas"], 78)
        self.assertEqual(s["population_decision"], "TARGET_NOT_MET")
        self.assertEqual(s["decision"], "PASS")

    def test_m05_identico_aunque_haya_un_p30(self):
        base, s = self.run_status(name="a.json")
        self.escribir_p30(p30_la_rioja(self.sha))
        con_p30, _ = self.run_status("--motor", "m05", "--runs-dir", str(self.runs), name="b.json")
        self.assertEqual(base, con_p30)
        self.assertEqual(s["population_outliers_after"], 0)
        self.assertEqual(s["population_evidence_source"], "BASE_M05")

    def assert_bloquea(self, causa, *extra):
        _, s = self.run_status("--motor", "motor2", "--runs-dir", str(self.runs), *extra)
        self.assertEqual(s["decision"], "BLOCK")
        self.assertEqual(s["block_cause"], causa)
        return s

    def test_motor2_sin_p30_falla_cerrado_sin_caer_al_m05(self):
        s = self.assert_bloquea("P30_POPULATION_EVIDENCE_MISSING")
        self.assertIsNone(s["population_outliers_after"])

    def test_motor2_p30_no_valido_o_no_verificado_bloquea(self):
        casos = {
            "sin ganador": {"valido": False, "estado": "P30_SIN_GANADOR_VALIDO"},
            "M06 no verificado": {"verificacion_m06": {"igual_al_ganador": False, "composicion_sha256": self.sha}},
            "M05 no restaurada": {"m05_restaurada": False},
            "composición distinta": {"verificacion_m06": {"igual_al_ganador": True, "composicion_sha256": "0" * 64}},
            "sin métricas": {"metricas": {"ganador": {"fuera_tolerancia": 1}}},
        }
        for nombre, cambio in casos.items():
            with self.subTest(nombre):
                self.escribir_p30(p30_la_rioja(self.sha) | cambio)
                self.assert_bloquea("P30_POPULATION_EVIDENCE_INVALID")

    def test_gana_canonico_no_exige_m06_rehecho(self):
        p30 = p30_la_rioja(self.sha) | {"estado": "P30_GANA_CANONICO", "rehacer_m06": False, "secciones_cambiadas": 0,
                                       "metricas": {"ganador": {"fuera_tolerancia": 0, "desvio_max": 0.1},
                                                    "canonico": {"fuera_tolerancia": 0, "desvio_max": 0.1}}}
        del p30["verificacion_m06"], p30["m05_restaurada"]
        self.escribir_p30(p30)
        _, s = self.run_status("--motor", "motor2", "--runs-dir", str(self.runs))
        self.assertEqual((s["decision"], s["population_decision"]), ("PASS", "TARGET_MET"))

    def test_workflow_pasa_motor_y_runs_dir(self):
        texto = WORKFLOW.read_text(encoding="utf-8")
        bloque = texto[texto.index("python herramientas/estado_produccion.py"):]
        bloque = bloque[:bloque.index("--output .ddd-audit/production_status.json")]
        self.assertIn('--motor "${{ inputs.motor }}" --runs-dir "$RUNS_DIR"', bloque)


if __name__ == "__main__":
    unittest.main()
