import hashlib,json,tempfile,unittest
from pathlib import Path
from herramientas.preparar_fuente_electoral import prepare,validate_previous

class ElectoralPreparation(unittest.TestCase):
    def test_reuse_preserves_frozen_metadata(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); old=root/"old"; data=old/"data"; data.mkdir(parents=True)
            src=data/"votes.csv"; src.write_text("section,votes\n1,10\n2,20\n",encoding="utf-8")
            h=hashlib.sha256(src.read_bytes()).hexdigest()
            manifest={"schema":"ddd-electoral-package/1.0","decision":"ACQUIRE","territory_id":"x","edition":"2025","selected_source":{"path":"data/votes.csv","sha256":h,"bytes":src.stat().st_size,"records":2,"record_count_method":"fixture","origin_url":"https://official.example/data.csv","publisher":"Official","acquired_at":"2026-01-01"}}
            (old/"manifest.json").write_text(json.dumps(manifest),encoding="utf-8")
            out=root/"new"
            result=prepare(territory_id="x",edition="2025",package_out=out,root=root,previous=old)
            self.assertEqual(result["decision"],"REUSE")
            self.assertEqual(result["selected_source"]["sha256"],h)
            self.assertEqual(result["selected_source"]["records"],2)
            self.assertIsNotNone(validate_previous(out,"x","2025"))

    def test_block_without_reuse_contract_or_declaration(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); out=root/"out"
            result=prepare(territory_id="x",edition="2025",package_out=out,root=root)
            self.assertEqual(result["decision"],"BLOCK")
            self.assertTrue((out/"manifest.json").is_file())

if __name__=="__main__": unittest.main()
