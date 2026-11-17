"""T-10: todo job que registra en main empuja con la credencial de registro (app propia o github.token)."""
from pathlib import Path
import re
import subprocess
import unittest

import yaml

WF = Path(__file__).resolve().parents[1] / ".github/workflows"
PUSHERS = re.compile(r"promover_catalogo_tras_preparacion|promover_catalogo_operacional|registrar_par_fuentes_legislatura|"
                     r"persistir_estado_operativo_compartido|persistir_producto_electoral_operacional|persistir_evidencia_pre_m04_operacional|git push")
# Solo los llama este reutilizable sin llamadores activos.
UNREACHABLE = set()
# T-379 2b (D-163): P10-P30 tienen GITHUB_TOKEN de solo lectura; su credencial no cae en github.token.
SIN_RESPALDO = {"p10-fuentes.yml", "p20-distritos.yml", "p30-resultados-electorales.yml"}


class CredencialRegistro(unittest.TestCase):
    def jobs(self):
        for p in sorted(WF.glob("*.yml")):
            if p.name in UNREACHABLE:
                continue
            for name, job in ((yaml.safe_load(p.read_text(encoding="utf-8")) or {}).get("jobs") or {}).items():
                steps = job.get("steps") or []
                if any(PUSHERS.search(str(s.get("run", "")) + str(s.get("with", ""))) for s in steps):
                    yield p.name, name, steps

    @staticmethod
    def checkout_que_alimenta_el_push(steps):
        """Índice del ÚLTIMO `actions/checkout` anterior al primer paso que empuja (T-376: en P30 el código se descarga primero y el
        persistidor de `main` —el que empuja— en `persistidor/` justo antes de la credencial; en el resto hay un solo checkout)."""
        push = next(i for i, s in enumerate(steps) if PUSHERS.search(str(s.get("run", "")) + str(s.get("with", ""))))
        return max(i for i, s in enumerate(steps[:push]) if str(s.get("uses", "")).startswith("actions/checkout@"))

    @classmethod
    def directorios_incoherentes(cls, steps):
        """Con más de un checkout, la credencial y los pasos que empujan (desde el checkout elegido) deben trabajar en SU directorio:
        `with.path` del checkout == `working-directory` de cada uno (ambos ausentes = raíz). Devuelve los pasos incoherentes."""
        if sum(1 for s in steps if str(s.get("uses", "")).startswith("actions/checkout@")) < 2:
            return []
        i = cls.checkout_que_alimenta_el_push(steps)
        directorio = (steps[i].get("with") or {}).get("path") or None
        empuja = re.compile(PUSHERS.pattern + r"|registrar_en_main|archivo_origen")
        malos = []
        for s in steps[i + 1:]:
            if s.get("name") == "Credencial de registro" or empuja.search(str(s.get("run", ""))):
                if (s.get("working-directory") or None) != directorio:
                    malos.append(s.get("name"))
        return malos

    def test_varios_checkouts_comparten_directorio_con_el_push(self):
        casos = 0
        for wf, job, steps in self.jobs():
            with self.subTest(workflow=wf, job=job):
                self.assertEqual(self.directorios_incoherentes(steps), [])
            casos += sum(1 for s in steps if str(s.get("uses", "")).startswith("actions/checkout@")) > 1
        self.assertGreaterEqual(casos, 1)  # P30 (T-376) tiene dos checkouts

    def test_control_negativo_directorio_cambiado_en_p30(self):
        import copy
        job = yaml.safe_load((WF / "p30-resultados-electorales.yml").read_text(encoding="utf-8"))["jobs"]["incorporar"]
        self.assertEqual(self.directorios_incoherentes(job["steps"]), [])
        for nombre in ("Credencial de registro", "Archivo en origen — M08 a R2 y votos por partido a git", "Registrar disponibilidad del producto electoral"):
            malo = copy.deepcopy(job["steps"])
            next(s for s in malo if s.get("name") == nombre)["working-directory"] = "otro"
            self.assertEqual(self.directorios_incoherentes(malo), [nombre])
        sin_path = copy.deepcopy(job["steps"])
        next(s for s in sin_path if s.get("name") == "Cargar persistidor vigente compatible con main")["with"].pop("path")
        self.assertTrue(self.directorios_incoherentes(sin_path))

    def test_control_negativo_credencial_no_pegada_al_checkout_del_push(self):
        co = {"uses": "actions/checkout@abc"}
        cred = {"name": "Credencial de registro"}
        otro = {"name": "Otro", "run": "true"}
        push = {"name": "Push", "run": "git push"}
        self.assertEqual(self.checkout_que_alimenta_el_push([co, otro, co, cred, push]), 2)  # el de antes del push
        self.assertEqual(self.checkout_que_alimenta_el_push([co, cred, push]), 0)
        steps = [co, otro, co, otro, cred, push]  # credencial separada del checkout que alimenta el push: debe detectarse
        self.assertNotEqual(steps[self.checkout_que_alimenta_el_push(steps) + 1].get("name"), "Credencial de registro")

    def test_cada_job_que_registra_usa_la_credencial_tras_el_checkout(self):
        found = list(self.jobs())
        self.assertGreaterEqual(len(found), 14)
        for wf, job, steps in found:
            with self.subTest(workflow=wf, job=job):
                checkout = self.checkout_que_alimenta_el_push(steps)
                cred = steps[checkout + 1]
                self.assertEqual(cred.get("name"), "Credencial de registro")
                self.assertEqual(cred["env"]["APP_ID"], "${{ secrets.DDD_REGISTRO_APP_ID }}")
                self.assertEqual(cred["env"]["APP_KEY"], "${{ secrets.DDD_REGISTRO_APP_KEY }}")
                if wf in SIN_RESPALDO:  # T-379 2b (D-163): GITHUB_TOKEN de solo lectura: sin la app, falla
                    self.assertIn("exit 1", cred["run"].split("\n")[1])
                    self.assertIn("::error::", cred["run"].split("\n")[1])
                else:
                    self.assertIn("exit 0", cred["run"].split("\n")[1])  # sin secretos sigue con github.token
                self.assertIn("::add-mask::", cred["run"])
                # actions/checkout v6 guarda su credencial en un include: hay que quitarlo o van dos Authorization.
                self.assertIn("^includeIf\\.gitdir:", cred["run"])
                self.assertLess(cred["run"].index("includeIf"), cred["run"].index('extraheader "AUTHORIZATION'))
                subprocess.run(["bash", "-n"], input=cred["run"], text=True, check=True)


if __name__ == "__main__":
    unittest.main()
