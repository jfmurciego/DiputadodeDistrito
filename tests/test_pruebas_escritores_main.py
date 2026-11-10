"""Escritores de main dentro de «Pruebas de la Plataforma» (T-149): aislados de `pruebas`, solo push, con señal visible."""
import re
import subprocess
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / ".github" / "workflows" / "pruebas-plataforma.yml"
ESCRITORES = {
    "catalogo": ("ddd-catalogo-procedencia", "catalogo"),
    "resultados": ("ddd-resultados-ligeros", "resultados"),
    "numeracion": ("ddd-registro-numeracion", "numeracion"),
}


def cargar():
    return yaml.safe_load(WF.read_text(encoding="utf-8"))


class EscritoresDeMain(unittest.TestCase):
    def test_pruebas_no_depende_de_los_escritores(self):
        needs = cargar()["jobs"]["pruebas"]["needs"]
        for job in ESCRITORES:
            self.assertNotIn(job, needs)

    def test_solo_push_a_main_y_aislados(self):
        jobs = cargar()["jobs"]
        for job, (grupo, flag) in ESCRITORES.items():
            with self.subTest(job=job):
                j = jobs[job]
                self.assertIn("github.event_name == 'push'", j["if"])
                self.assertIn(f"needs.cambios.outputs.{flag} == 'true'", j["if"])
                self.assertIn("needs.cambios.result != 'success'", j["if"])  # si `cambios` falla, el escritor corre
                self.assertTrue(j["if"].lstrip("${{ ").startswith("always()"))
                self.assertIs(j["continue-on-error"], True)
                self.assertEqual(j["permissions"], {"contents": "write"})
                self.assertEqual(j["concurrency"], {"group": grupo, "cancel-in-progress": False, "queue": "max"})
                self.assertEqual(j["needs"], "cambios")

    def test_credencial_de_registro_tras_el_checkout_y_senal_visible(self):
        for job in ESCRITORES:
            with self.subTest(job=job):
                pasos = cargar()["jobs"][job]["steps"]
                self.assertIn("checkout", pasos[0]["uses"])
                self.assertEqual(pasos[1]["name"], "Credencial de registro")
                ultimo = pasos[-1]
                self.assertEqual(ultimo["if"], "${{ failure() }}")
                self.assertIn("::error", ultimo["run"])
                self.assertIn("GITHUB_STEP_SUMMARY", ultimo["run"])
                subprocess.run(["bash", "-n"], input=ultimo["run"], text=True, check=True)

    def test_rutas_de_cada_escritor_y_sin_base_corren_todos(self):
        paso = next(s for s in cargar()["jobs"]["cambios"]["steps"] if s.get("id") == "f")["run"]
        esperado = {
            "catalogo": ["orchestracion/publicaciones_visor", "orchestracion/(publicaciones_visor|archivo_r2|productos_publicos)",
                         "datos_abiertos/INDEX", "datos/(composicion|resultados)/MANIFEST"],
            "resultados": ["orchestracion/publicaciones_visor", "datos/composicion/MANIFEST"],
            "numeracion": ["docs/registro/"],
        }
        for nombre, trozos in esperado.items():
            linea = next(l for l in paso.splitlines() if l.strip().startswith(f"escribe {nombre} "))
            for trozo in trozos[1:] if nombre == "catalogo" else trozos:
                self.assertIn(trozo, linea)
        self.assertIn('[[ "$files" == "todo" ]]', paso)  # sin base comparable: corren todos (idempotentes)
        self.assertNotIn("pruebas-plataforma", " ".join(l for l in paso.splitlines() if l.strip().startswith("escribe ")))


if __name__ == "__main__":
    unittest.main()
