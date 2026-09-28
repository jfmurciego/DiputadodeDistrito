import json,sqlite3,tempfile,unittest
from pathlib import Path
from herramientas.adaptador_eleccionesdb import build
from herramientas.validar_paquete_electoral import validate_package

RETRIEVED_AT='2026-09-28T12:34:56Z'

class TestAdaptadorEleccionesDB(unittest.TestCase):
 def db(self,ccaa='06',with_votes=True):
  td=tempfile.TemporaryDirectory(); p=Path(td.name)/'x.sqlite'; c=sqlite3.connect(p)
  c.executescript('''CREATE TABLE elecciones(id INTEGER,fecha TEXT); CREATE TABLE elecciones_fuentes(eleccion_id INTEGER,fuente TEXT,url_fuente TEXT,observaciones TEXT); CREATE TABLE territorios(id INTEGER,tipo TEXT,codigo_ccaa TEXT,codigo_provincia TEXT,codigo_municipio TEXT,codigo_distrito TEXT,codigo_seccion TEXT); CREATE TABLE resumen_territorial(eleccion_id INTEGER,territorio_id INTEGER); CREATE TABLE partidos(id INTEGER,siglas TEXT,denominacion TEXT); CREATE TABLE votos_territoriales(eleccion_id INTEGER,territorio_id INTEGER,partido_id INTEGER,votos INTEGER);''')
  c.execute("INSERT INTO elecciones VALUES(237,'2023-05-28')"); c.execute("INSERT INTO elecciones_fuentes VALUES(237,'Gobierno','https://example.test','')"); c.execute("INSERT INTO territorios VALUES(1,'seccion',?,'39','075','01','1')",(ccaa,)); c.execute('INSERT INTO resumen_territorial VALUES(237,1)'); c.execute("INSERT INTO partidos VALUES(1,'P','Partido')")
  if with_votes:c.execute('INSERT INTO votos_territoriales VALUES(237,1,1,10)')
  c.commit();c.close(); return td,p
 def test_territorio_equivocado_bloquea(self):
  td,p=self.db('05'); self.addCleanup(td.cleanup)
  with self.assertRaisesRegex(ValueError,'Territorio equivocado'): build(p,'cantabria_parlamento_2023',Path(td.name)/'o',retrieved_at=RETRIEVED_AT)
 def test_cero_votos_bloquea(self):
  td,p=self.db(with_votes=False); self.addCleanup(td.cleanup)
  with self.assertRaisesRegex(ValueError,'cero votos'): build(p,'cantabria_parlamento_2023',Path(td.name)/'o')
 def test_ceuta_y_melilla_separan_eleccion_fisica_247_por_ccaa(self):
  td=tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup)
  p=Path(td.name)/'shared.sqlite'; con=sqlite3.connect(p)
  con.executescript("""CREATE TABLE elecciones(id INTEGER,fecha TEXT); CREATE TABLE elecciones_fuentes(eleccion_id INTEGER,fuente TEXT,url_fuente TEXT,observaciones TEXT); CREATE TABLE territorios(id INTEGER,tipo TEXT,codigo_ccaa TEXT,codigo_provincia TEXT,codigo_municipio TEXT,codigo_distrito TEXT,codigo_seccion TEXT); CREATE TABLE resumen_territorial(eleccion_id INTEGER,territorio_id INTEGER); CREATE TABLE partidos(id INTEGER,siglas TEXT,denominacion TEXT); CREATE TABLE votos_territoriales(eleccion_id INTEGER,territorio_id INTEGER,partido_id INTEGER,votos INTEGER);""")
  con.execute("INSERT INTO elecciones VALUES(247,'2023-05-28')")
  con.execute("INSERT INTO elecciones_fuentes VALUES(247,'Ministerio','https://example.test','')")
  con.executemany("INSERT INTO territorios VALUES(?,?,?,?,?,?,?)",[
   (18,'seccion','18','51','001','01','1'),
   (19,'seccion','19','52','001','01','1'),
  ])
  con.executemany("INSERT INTO resumen_territorial VALUES(247,?)",[(18,),(19,)])
  con.execute("INSERT INTO partidos VALUES(1,'P','Partido')")
  con.executemany("INSERT INTO votos_territoriales VALUES(247,?,?,?)",[(18,1,10),(19,1,20)])
  con.commit(); con.close()
  ceuta=build(p,'ceuta_asamblea_local_2023',Path(td.name)/'ceuta',retrieved_at=RETRIEVED_AT)
  melilla=build(p,'melilla_asamblea_local_2023',Path(td.name)/'melilla',retrieved_at=RETRIEVED_AT)
  self.assertEqual((ceuta['territory_id'],ceuta['sections'],ceuta['candidate_votes']),('ceuta',1,10))
  self.assertEqual((melilla['territory_id'],melilla['sections'],melilla['candidate_votes']),('melilla',1,20))
  self.assertNotEqual(ceuta['selected_source']['sha256'],melilla['selected_source']['sha256'])
 def test_paquete_comun_es_consumible_por_incorporacion(self):
  td,p=self.db(); self.addCleanup(td.cleanup)
  out=Path(td.name)/'package'
  manifest=build(p,'cantabria_parlamento_2023',out,edition='2025',retrieved_at=RETRIEVED_AT)
  self.assertEqual(manifest['schema'],'ddd-electoral-package/1.0')
  self.assertEqual(manifest['decision'],'ACQUIRE')
  self.assertEqual(manifest['edition'],'2025')
  self.assertEqual(manifest['retrieved_at'],RETRIEVED_AT)
  contract=json.loads((out/'contract/election_contract.json').read_text(encoding='utf-8'))
  self.assertEqual(contract['sources'][0]['retrieved_at'],RETRIEVED_AT)
  self.assertEqual(contract['sources'][0]['upstream_snapshot']['retrieved_at'],RETRIEVED_AT)
  self.assertTrue((out/'contract/election_contract.json').is_file())
  self.assertTrue((out/'contract/party_dictionary.json').is_file())
  validation=validate_package(
   package=out,
   params=Path(__file__).resolve().parents[1]/'territorios/cantabria/config/cantabria_2025.yaml',
   territory_id='cantabria',
   edition='2025',
   root=Path(__file__).resolve().parents[1],
   materialize=False,
  )
  self.assertEqual(validation['decision'],'READY_PACKAGE')
  self.assertEqual(validation['mode'],'embedded_runtime_contract')
  self.assertEqual(validation['election_id'],'cantabria_parlamento_2023')
 def test_retrieved_at_verificable_es_obligatorio(self):
  td,p=self.db(); self.addCleanup(td.cleanup)
  with self.assertRaisesRegex(ValueError,'retrieved_at verificable ausente'):
   build(p,'cantabria_parlamento_2023',Path(td.name)/'o')
  with self.assertRaisesRegex(ValueError,'zona horaria'):
   build(p,'cantabria_parlamento_2023',Path(td.name)/'o2',retrieved_at='2026-09-28T12:34:56')
 def test_huella_incorrecta_bloquea(self):
  td,p=self.db(); self.addCleanup(td.cleanup)
  with self.assertRaisesRegex(ValueError,'Huella'): build(p,'cantabria_parlamento_2023',Path(td.name)/'o','0'*64,retrieved_at=RETRIEVED_AT)
if __name__=='__main__': unittest.main()
