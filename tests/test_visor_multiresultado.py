"""Contratos del visor unificado: baseline, metadatos y alternativas GerryChain."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class VisorMultiresultado(unittest.TestCase):
    def test_interfaz_tiene_selector_de_resultado(self):
        html=(ROOT/'visor/index.html').read_text(encoding='utf-8')
        self.assertIn('id="territory-select"',html)
        self.assertIn('id="result-select"',html)
        self.assertIn('id="ensemble-link"',html)

    def test_app_lee_metadatos_y_catalogo_ensemble(self):
        js=(ROOT/'visor/app.js').read_text(encoding='utf-8')
        self.assertIn('data/ensemble-index.json',js)
        self.assertIn('metadata.json',js)
        self.assertIn('geometric_audit',js)
        self.assertIn('candidate_id',js)
        self.assertIn('resultSelect',js)

    def test_publicacion_m06_audita_geometria_antes_de_visualizar(self):
        wf=(ROOT/'.github/workflows/_reutilizable-publicar-evidencia-m06.yml').read_text(encoding='utf-8')
        self.assertIn('auditar_componentes_geometricos.py',wf)
        self.assertIn('actions/download-artifact@v6',wf)
        self.assertIn('contiguedad_geometrica.json',wf)
        self.assertIn('metadata.json',wf)
        self.assertIn('actions/deploy-pages@v4',wf)

    def test_ensemble_despliega_un_solo_visor_con_combo(self):
        wf=(ROOT/'.github/workflows/generar-alternativas-territoriales.yml').read_text(encoding='utf-8')
        self.assertIn('ensemble-index.json',wf)
        self.assertIn('cp visor/index.html visor/app.js visor/styles.css site/',wf)
        self.assertIn('cp -R work/ensemble/site/. site/ensemble/',wf)
        self.assertIn('path: site',wf)


if __name__=='__main__':
    unittest.main()
