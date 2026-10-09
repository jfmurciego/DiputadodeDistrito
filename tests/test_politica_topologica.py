#!/usr/bin/env python3
"""
PROYECTO: Diputado de Distrito
COMPONENTE: Política topológica R037
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Bloqueo y componentes insulares
FECHA: 2026-09-13
ESTADO: vigente — R037
FUNCIÓN: prueba la correspondencia con R023, el bloqueo de anomalías y la prohibición de enlaces marítimos.
CAMBIOS: primera versión.
MOTIVO: impedir promociones topológicas silenciosas antes de M04.
ANTERIOR: ninguno — prueba nueva.
"""
from pathlib import Path
import tempfile, unittest, yaml
from herramientas.validar_politica_topologica import validate
ROOT=Path(__file__).resolve().parents[1]; POLICY=ROOT/"configuracion/politica_topologia_territorial_2025.yaml"

def mutated(change):
    data=yaml.safe_load(POLICY.read_text(encoding="utf-8")); change(data)
    with tempfile.NamedTemporaryFile("w",suffix=".yaml",encoding="utf-8",delete=False) as f: yaml.safe_dump(data,f,sort_keys=False,allow_unicode=True); path=Path(f.name)
    try:return validate(path,ROOT)
    finally:path.unlink(missing_ok=True)

class TopologyPolicy(unittest.TestCase):
    def test_registro_vigente_pasa(self):
        self.assertEqual(validate(POLICY,ROOT)["status"],"PASS")

    def test_no_admite_anomalia_como_inexistente(self):
        report=mutated(lambda d:d["territories"][0].__setitem__("decision","ADMITTED_NO_ANOMALIES"))
        self.assertEqual(report["status"],"FAIL")

    def test_no_inventa_puente_marino(self):
        report=mutated(lambda d:d["policies"]["archipelago_components"].__setitem__("inter_component_edges","allowed"))
        self.assertEqual(report["status"],"FAIL")

    def test_no_admite_reparacion_sin_expediente(self):
        report=mutated(lambda d:d["territories"][0].update({"decision":"ADMITTED_WITH_DECLARED_REPAIRS","repairs":[{"u":"a","v":"b"}]}))
        self.assertEqual(report["status"],"FAIL")

if __name__=="__main__": unittest.main()
