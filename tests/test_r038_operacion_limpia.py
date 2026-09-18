"""Trinquetes de interfaz tras Diseño A."""
import os,subprocess,unittest
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[1]
WORKFLOWS=ROOT/".github/workflows"

class R038OperacionLimpia(unittest.TestCase):
    def test_exactamente_tres_workflows(self):
        self.assertEqual(sorted(p.name for p in WORKFLOWS.glob("*.yml")),["preparacion-fuentes.yml","produccion-distritos.yml","pruebas-plataforma.yml"])

    def test_interfaz_productiva_tiene_cuatro_controles(self):
        data=yaml.safe_load((WORKFLOWS/"produccion-distritos.yml").read_text(encoding="utf-8"))
        raw=(data.get("on") or data.get(True))["workflow_dispatch"]["inputs"]
        self.assertEqual(list(raw),["territory_id","data_edition","publish_result","confirmar_ejecucion"])
        self.assertNotIn("checkpoint_run_id",raw)
        self.assertNotIn("from_stage",raw)
        self.assertNotIn("to_stage",raw)

    def test_lanzador_shell_compila(self):
        r=subprocess.run(["bash","-n",str(ROOT/"procedimiento.sh")],text=True,capture_output=True)
        self.assertEqual(r.returncode,0,r.stderr)

    def test_linea_comun_publica_productos_del_run(self):
        text=(WORKFLOWS/"produccion-distritos.yml").read_text(encoding="utf-8")
        self.assertIn("steps.resolve.outputs.runs_dir",text)
        self.assertIn("--run-id \"$DDD_RUN_ID\"",text)
        self.assertIn("bash -n procedimiento.sh",text)
        self.assertIn("actions/deploy-pages@v4",text)
        self.assertIn("ddd-state-",text)

    def test_no_quedan_workflows_territoriales_o_g10_visibles(self):
        names={p.name for p in WORKFLOWS.glob("*.yml")}
        for name in ("g10-ejecutar-tramo-certificado.yml","aragon-ejecucion-integral.yml","procedimiento-ddd.yml"):
            self.assertNotIn(name,names)

if __name__=="__main__": unittest.main()
