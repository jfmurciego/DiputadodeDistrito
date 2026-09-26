import sqlite3,tempfile,unittest
from pathlib import Path
from herramientas.adaptador_eleccionesdb import build

class TestAdaptadorEleccionesDB(unittest.TestCase):
 def db(self,ccaa='06',with_votes=True):
  td=tempfile.TemporaryDirectory(); p=Path(td.name)/'x.sqlite'; c=sqlite3.connect(p)
  c.executescript('''CREATE TABLE elecciones(id INTEGER,fecha TEXT); CREATE TABLE elecciones_fuentes(eleccion_id INTEGER,fuente TEXT,url_fuente TEXT,observaciones TEXT); CREATE TABLE territorios(id INTEGER,tipo TEXT,codigo_ccaa TEXT,codigo_provincia TEXT,codigo_municipio TEXT,codigo_distrito TEXT,codigo_seccion TEXT); CREATE TABLE resumen_territorial(eleccion_id INTEGER,territorio_id INTEGER); CREATE TABLE partidos(id INTEGER,siglas TEXT,denominacion TEXT); CREATE TABLE votos_territoriales(eleccion_id INTEGER,territorio_id INTEGER,partido_id INTEGER,votos INTEGER);''')
  c.execute("INSERT INTO elecciones VALUES(237,'2023-05-28')"); c.execute("INSERT INTO elecciones_fuentes VALUES(237,'Gobierno','https://example.test','')"); c.execute("INSERT INTO territorios VALUES(1,'seccion',?,'39','075','01','1')",(ccaa,)); c.execute('INSERT INTO resumen_territorial VALUES(237,1)'); c.execute("INSERT INTO partidos VALUES(1,'P','Partido')")
  if with_votes:c.execute('INSERT INTO votos_territoriales VALUES(237,1,1,10)')
  c.commit();c.close(); return td,p
 def test_territorio_equivocado_bloquea(self):
  td,p=self.db('05'); self.addCleanup(td.cleanup)
  with self.assertRaisesRegex(ValueError,'Territorio equivocado'): build(p,'cantabria_parlamento_2023',Path(td.name)/'o')
 def test_cero_votos_bloquea(self):
  td,p=self.db(with_votes=False); self.addCleanup(td.cleanup)
  with self.assertRaisesRegex(ValueError,'cero votos'): build(p,'cantabria_parlamento_2023',Path(td.name)/'o')
 def test_huella_incorrecta_bloquea(self):
  td,p=self.db(); self.addCleanup(td.cleanup)
  with self.assertRaisesRegex(ValueError,'Huella'): build(p,'cantabria_parlamento_2023',Path(td.name)/'o','0'*64)
if __name__=='__main__': unittest.main()
