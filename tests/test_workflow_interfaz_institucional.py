from pathlib import Path
import unittest,yaml
from herramientas.catalogo_preparacion import rows_for
ROOT=Path(__file__).resolve().parents[1]
WORKFLOWS=ROOT/".github/workflows"
PRODUCTION=WORKFLOWS/"produccion-distritos.yml"
PREPARATION=WORKFLOWS/"preparacion-fuentes.yml"
CATALOG=ROOT/"configuracion/catalogo_preparacion.yaml"

def load(path):
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
def dispatch_inputs(path):
    d=load(path); t=d.get("on") or d.get(True)
    return t["workflow_dispatch"]["inputs"]

class WorkflowInterfaceInstitutional(unittest.TestCase):
    def test_tres_interfaces_visibles(self):
        self.assertEqual({load(p)["name"] for p in WORKFLOWS.glob("*.yml")},{"Preparación de fuentes oficiales","Producción de distritos","Pruebas de la plataforma"})

    def test_formulario_productivo_tiene_exactamente_cuatro_controles(self):
        inputs=dispatch_inputs(PRODUCTION)
        self.assertEqual(list(inputs),["territory_id","data_edition","publish_result","confirmar_ejecucion"])
        self.assertEqual(inputs["territory_id"]["options"],[r["name"] for r in rows_for("production",CATALOG)])
        self.assertEqual(inputs["data_edition"]["options"],["2025"])

    def test_preparacion_y_produccion_comparten_catalogo(self):
        self.assertEqual(dispatch_inputs(PREPARATION)["territory_id"]["options"],[r["name"] for r in rows_for("preparation",CATALOG)])
        text=PRODUCTION.read_text(encoding="utf-8")
        self.assertIn("herramientas/catalogo_preparacion.py resolve --mode production",text)
        self.assertIn("python -m herramientas.seleccionar_checkpoint_productivo",text)

    def test_secuencia_productiva_conserva_m01_m08(self):
        jobs=load(PRODUCTION)["jobs"]
        for stage in range(1,9): self.assertIn(f"m{stage:02d}",jobs)
        for name in ("official_sources","auditoria","electoral_source","visor","informe_ejecucion"): self.assertIn(name,jobs)

if __name__=="__main__": unittest.main()
