import csv,json,tempfile,unittest
from pathlib import Path
from herramientas.preparar_fuente_electoral import transform_gencat_polling_csv

class TestCatalunaElectoralVigente(unittest.TestCase):
    def test_transforma_mesas_y_exige_reconciliacion_exacta(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); src=root/"epc.csv"; out=root/"out"
            fields=["Nivell","Codi circumscripció","Codi municipi","Nom municipi","Districte","Secció","Mesa","Votants","Vots a candidatures","Vots PSC","Vots ERC"]
            with src.open("w",encoding="utf-8",newline="") as f:
                w=csv.DictWriter(f,fieldnames=fields,delimiter=";"); w.writeheader()
                w.writerow({"Nivell":"ME","Codi circumscripció":"08","Codi municipi":"001","Nom municipi":"X","Districte":"01","Secció":"001","Mesa":"A","Votants":"10","Vots a candidatures":"9","Vots PSC":"5","Vots ERC":"4"})
                w.writerow({"Nivell":"ME","Codi circumscripció":"08","Codi municipi":"001","Nom municipi":"X","Districte":"01","Secció":"001","Mesa":"B","Votants":"12","Vots a candidatures":"11","Vots PSC":"6","Vots ERC":"5"})
                w.writerow({"Nivell":"ME","Codi circumscripció":"08","Codi municipi":"998","Nom municipi":"Residents Absents-Barcelona","Districte":"99","Secció":"001","Mesa":"U","Votants":"3","Vots a candidatures":"3","Vots PSC":"2","Vots ERC":"1"})
            declaration={"territory_id":"cataluna","election_id":"cataluna_parlament_2024","election_date":"2024-05-12","verification":{"official_voters":25,"official_candidate_votes":23,"expected_polling_stations":2,"expected_sections":1,"expected_cera_rows":1,"expected_cera_candidate_votes":3,"official_party_totals":{"PSC":13,"ERC":10}}}
            source_decl={"publisher":"Generalitat / mirror","url":"https://example.invalid/epc.csv"}
            result=transform_gencat_polling_csv(src,out,declaration,source_decl,root)
            self.assertEqual(result["sections"],1)
            self.assertEqual(result["polling_stations"],2)
            self.assertEqual(result["official_candidate_votes"],23)
            self.assertEqual(result["geographic_candidate_votes"],20)
            self.assertEqual(result["cera_candidate_votes"],3)
            contract=json.loads(result["contract"].read_text(encoding="utf-8"))
            self.assertEqual(contract["source_verification"]["status"],"VERIFIED_EXACT")
            self.assertEqual(contract["non_geocodable_votes"]["candidate_votes"],3)
            rows=list(csv.DictReader(result["source"].open(encoding="utf-8"),delimiter=";"))
            self.assertEqual({(r["party"],int(r["votes"])) for r in rows},{("PSC",11),("ERC",9)})

if __name__=="__main__": unittest.main()
