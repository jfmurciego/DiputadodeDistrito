"""T-454: P40 espera a que el artefacto github-pages sea visible antes de deploy-pages (carrera de visibilidad)."""
import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
NOMBRE = "Esperar a que el artefacto github-pages sea visible (T-454)"


class Espera(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        wf = yaml.safe_load((ROOT / ".github/workflows/p40-publicacion.yml").read_text(encoding="utf-8"))
        cls.pasos = wf["jobs"]["publicar"]["steps"]
        cls.paso = next(s for s in cls.pasos if s.get("name") == NOMBRE)

    def test_entre_la_subida_y_el_despliegue(self):
        usos = [(s.get("uses") or "").split("@")[0] for s in self.pasos]
        i = self.pasos.index(self.paso)
        self.assertEqual(usos[i - 1], "actions/upload-pages-artifact")
        self.assertEqual(usos[i + 1], "actions/deploy-pages")
        self.assertEqual(self.pasos[i + 1].get("id"), "deployment")

    def test_no_bloquea_ni_toca_secretos(self):
        self.assertNotIn("if", self.paso)
        self.assertNotIn("env", self.paso)
        self.assertNotIn("exit 1", self.paso["run"])

    def _ejecutar(self, artefactos, intento="2026-11-24T10:00:00Z", antes=0):
        """`artefactos`: función de la cuenta de consulta -> lista de (created_at) del artefacto github-pages; `antes`: consultas sin él."""
        guion = (
            "#!/usr/bin/env bash\n"
            'if [[ "$*" == *attempts* ]]; then echo "$INTENTO"; exit 0; fi\n'
            'if [[ -n "$FALLA" ]]; then echo boom >&2; exit 1; fi\n'
            'echo x >> "$CUENTA"; c=$(wc -l < "$CUENTA")\n'
            'if (( c > ANTES )); then echo "{\\"artifacts\\":[{\\"name\\":\\"github-pages\\",\\"expired\\":false,\\"created_at\\":\\"$CREADO\\"}]}"; else echo \'{"artifacts":[]}\'; fi\n'
        )
        with tempfile.TemporaryDirectory() as d:
            gh = Path(d) / "gh"
            gh.write_text(guion, encoding="utf-8")
            gh.chmod(gh.stat().st_mode | stat.S_IEXEC)
            env = {**os.environ, "PATH": f"{d}:{os.environ['PATH']}", "GITHUB_REPOSITORY": "o/r", "GITHUB_RUN_ID": "1", "GITHUB_RUN_ATTEMPT": "2",
                   "DDD_REINTENTO_BASE": "0", "CUENTA": str(Path(d) / "cuenta"), "INTENTO": intento, "ANTES": str(antes), **artefactos}
            return subprocess.run(["bash", "-eo", "pipefail", "-c", self.paso["run"]], env=env, capture_output=True, text=True)

    def test_visible_a_la_tercera_consulta_con_margen(self):
        r = self._ejecutar({"CREADO": "2026-11-24T10:05:00Z"}, antes=2)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Artefacto github-pages visible; margen de 10 s", r.stdout)
        self.assertEqual(r.stdout.count("aún no es visible"), 2)

    def test_margen_tras_visible_en_el_texto(self):
        self.assertRegex(self.paso["run"], r"sleep \$\(\( 10 \* \$\{DDD_REINTENTO_BASE:-1\} \)\)")

    def test_artefacto_del_intento_anterior_no_cuenta(self):
        r = self._ejecutar({"CREADO": "2026-11-24T09:00:00Z"})  # creado ANTES de run_started_at de este intento
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("::warning::T-454", r.stdout)
        self.assertNotIn("margen de 10 s", r.stdout)

    def test_nunca_visible_avisa_y_sale_0(self):
        r = self._ejecutar({"CREADO": "2026-11-24T10:05:00Z"}, antes=99)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("::warning::T-454", r.stdout)

    def test_consulta_que_falla_degrada(self):
        r = self._ejecutar({"CREADO": "2026-11-24T10:05:00Z", "FALLA": "1"})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("::warning::T-454", r.stdout)

    def test_control_negativo_deshacer(self):
        from tests import _t454
        pasos = _t454.deshacer_p40_pasos(self.pasos)
        self.assertNotIn(NOMBRE, [s.get("name") for s in pasos])
        with self.assertRaises(AssertionError):
            _t454.deshacer_p40_pasos(pasos)


if __name__ == "__main__":
    unittest.main()
