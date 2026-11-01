"""T-10: todo job que registra en main empuja con la credencial de registro (app propia o github.token)."""
from pathlib import Path
import re
import subprocess
import unittest

import yaml

WF = Path(__file__).resolve().parents[1] / ".github/workflows"
PUSHERS = re.compile(r"promover_catalogo_tras_preparacion|promover_catalogo_operacional|registrar_par_fuentes_legislatura|"
                     r"persistir_estado_operativo_compartido|persistir_producto_electoral_operacional|git push")
# Solo los llama este reutilizable sin llamadores activos.
UNREACHABLE = {"_reutilizable-operacion-territorial.yml", "producir-territorio-por-contrato.yml"}


class CredencialRegistro(unittest.TestCase):
    def jobs(self):
        for p in sorted(WF.glob("*.yml")):
            if p.name in UNREACHABLE:
                continue
            for name, job in ((yaml.safe_load(p.read_text(encoding="utf-8")) or {}).get("jobs") or {}).items():
                steps = job.get("steps") or []
                if any(PUSHERS.search(str(s.get("run", "")) + str(s.get("with", ""))) for s in steps):
                    yield p.name, name, steps

    def test_cada_job_que_registra_usa_la_credencial_tras_el_checkout(self):
        found = list(self.jobs())
        self.assertGreaterEqual(len(found), 14)
        for wf, job, steps in found:
            with self.subTest(workflow=wf, job=job):
                checkout = next(i for i, s in enumerate(steps) if str(s.get("uses", "")).startswith("actions/checkout@"))
                cred = steps[checkout + 1]
                self.assertEqual(cred.get("name"), "Credencial de registro")
                self.assertEqual(cred["env"]["APP_ID"], "${{ secrets.DDD_REGISTRO_APP_ID }}")
                self.assertEqual(cred["env"]["APP_KEY"], "${{ secrets.DDD_REGISTRO_APP_KEY }}")
                self.assertIn("exit 0", cred["run"].split("\n")[1])  # sin secretos sigue con github.token
                self.assertIn("::add-mask::", cred["run"])
                # actions/checkout v6 guarda su credencial en un include: hay que quitarlo o van dos Authorization.
                self.assertIn("^includeIf\\.gitdir:", cred["run"])
                self.assertLess(cred["run"].index("includeIf"), cred["run"].index('extraheader "AUTHORIZATION'))
                subprocess.run(["bash", "-n"], input=cred["run"], text=True, check=True)


if __name__ == "__main__":
    unittest.main()
