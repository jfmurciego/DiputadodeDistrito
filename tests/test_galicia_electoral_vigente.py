from __future__ import annotations
import json,tempfile,unittest
from email.message import Message
from pathlib import Path
import yaml

from herramientas.comprobar_fuente_electoral_oficial import check_declaration
from herramientas.preparar_fuente_electoral import merge_delimited_sources
from herramientas.resolver_eleccion_vigente import resolve

ROOT=Path(__file__).resolve().parents[1]
WF=ROOT/".github/workflows/preparacion-resultados-electorales.yml"
DECL=ROOT/"territorios/galicia/config/elecciones/galicia_parlamento_vigente.yaml"

class FakeResponse:
    def __init__(self,data:bytes):
        self._data=data; self.status=200; self.headers=Message(); self.headers["Content-Type"]="text/csv"
    def read(self,n=-1): return self._data if n<0 else self._data[:n]
    def __enter__(self): return self
    def __exit__(self,*args): return False

class GaliciaElectoralVigente(unittest.TestCase):
    def test_galicia_2025_resolves_2024_without_user_year(self):
        row=resolve("Galicia",root_dir=ROOT)
        self.assertEqual(row["territory_id"],"galicia")
        self.assertEqual(row["territorial_edition"],"2025")
        self.assertEqual(row["election_id"],"galicia_parlamento_2024")
        self.assertEqual(row["election_date"],"2024-02-18")
        d=yaml.safe_load(DECL.read_text(encoding="utf-8"))
        self.assertEqual(d["selection_mode"],"all_required")
        self.assertEqual(len(d["sources"]),4)
        self.assertTrue(all(s["required"] for s in d["sources"]))

    def test_workflow_hides_year_and_uses_current_election_resolver(self):
        d=yaml.safe_load(WF.read_text(encoding="utf-8"))
        trigger=d.get("on") or d.get(True)
        inputs=trigger["workflow_dispatch"]["inputs"]
        self.assertEqual(list(inputs),["territory_id","reutilizar_si_ya_preparada"])\n        self.assertNotIn("confirmar_preparacion",inputs)
        text=WF.read_text(encoding="utf-8")
        self.assertIn("resolver_eleccion_vigente.py",text)
        self.assertIn("needs.resolver.outputs.edition",text)
        self.assertNotIn("inputs.data_edition",text)

    def test_all_required_files_must_be_ready(self):
        declaration={
            "schema":"ddd-election-official-source-declaration/1.0",
            "territory_id":"galicia",
            "election_id":"galicia_parlamento_2024",
            "election_date":"2024-02-18",
            "selection_mode":"all_required",
            "minimum_resolution":"polling_station",
            "allowed_official_hosts":["official.example"],
            "sources":[
                {"id":"p1","publisher":"Official","url":"https://official.example/p1.csv","required":True,"declared_resolution":"polling_station","granularity_markers":["mesa"]},
                {"id":"p2","publisher":"Official","url":"https://official.example/p2.csv","required":True,"declared_resolution":"polling_station","granularity_markers":["mesa"]},
            ],
        }
        def opener(request,timeout=0):
            return FakeResponse(b"mesa;censo;votos\n01;100;50\n")
        with tempfile.TemporaryDirectory() as td:
            result=check_declaration(declaration,td,opener=opener)
            self.assertEqual(result["decision"],"READY")
            self.assertIsNone(result["selected_source"])
            self.assertEqual(len(result["selected_sources"]),2)
            self.assertTrue(all(x["status"]=="READY" for x in result["selected_sources"]))

    def test_multifile_merge_preserves_union_of_columns(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            a=root/"a.csv"; b=root/"b.csv"; out=root/"merged.csv"
            a.write_text("mesa;censo;A\n01;100;10\n",encoding="utf-8")
            b.write_text("mesa;censo;B\n02;120;20\n",encoding="utf-8")
            info=merge_delimited_sources([a,b],out)
            self.assertEqual(info["records"],2)
            self.assertEqual(info["columns"],["mesa","censo","A","B"])
            text=out.read_text(encoding="utf-8")
            self.assertIn("01;100;10;",text)
            self.assertIn("02;120;;20",text)

if __name__=="__main__":
    unittest.main()
