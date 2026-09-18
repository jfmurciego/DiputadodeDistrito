import hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch

from herramientas.preparar_fuente_electoral import prepare,validate_previous

class ElectoralPreparation(unittest.TestCase):
    def _previous_package(self,root:Path):
        old=root/"old"; data=old/"data"; data.mkdir(parents=True)
        src=data/"votes.csv"; src.write_text("section,votes\n1,10\n2,20\n",encoding="utf-8")
        h=hashlib.sha256(src.read_bytes()).hexdigest()
        manifest={"schema":"ddd-electoral-package/1.0","decision":"ACQUIRE","territory_id":"x","edition":"2025","selected_source":{"path":"data/votes.csv","sha256":h,"bytes":src.stat().st_size,"records":2,"record_count_method":"delimited_rows_excluding_header","origin_url":"https://official.example/data.csv","publisher":"Official","acquired_at":"2026-01-01"}}
        (old/"manifest.json").write_text(json.dumps(manifest),encoding="utf-8")
        return old,src,h

    def test_reuse_preserves_frozen_metadata_and_durable_provenance(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); old,src,h=self._previous_package(root); out=root/"new"
            result=prepare(territory_id="x",edition="2025",package_out=out,root=root,previous=old,previous_run_id="12345",previous_artifact_name="ddd-electoral-package-x-2025-12345")
            self.assertEqual(result["decision"],"REUSE")
            self.assertEqual(result["selected_source"]["sha256"],h)
            self.assertEqual(result["selected_source"]["records"],2)
            self.assertEqual(result["reuse_provenance"]["run_id"],"12345")
            self.assertEqual(result["reuse_provenance"]["artifact_name"],"ddd-electoral-package-x-2025-12345")
            self.assertIsNotNone(validate_previous(out,"x","2025"))

    def test_corrupt_previous_package_is_not_reused(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); old,src,_=self._previous_package(root); src.write_text("corrupt",encoding="utf-8")
            result=prepare(territory_id="x",edition="2025",package_out=root/"out",root=root,previous=old,previous_run_id="12345",previous_artifact_name="artifact")
            self.assertEqual(result["decision"],"BLOCK")
            self.assertNotIn("reuse_provenance",result)

    def test_acquire_success_freezes_file_hash_size_and_records(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); decl=root/"decl.yaml"; decl.write_text("schema: synthetic\n",encoding="utf-8")
            def fake_check(_declaration,out_dir):
                out=Path(out_dir); (out/"downloads").mkdir(parents=True)
                src=out/"downloads"/"votes.csv"; src.write_text("section,votes\n1,10\n2,20\n",encoding="utf-8")
                return {"decision":"READY","selected_source":{"artifact_path":"downloads/votes.csv","url":"https://official.example/votes.csv","publisher":"Official"}}
            with patch("herramientas.preparar_fuente_electoral.load_declaration",return_value={"synthetic":True}), patch("herramientas.preparar_fuente_electoral.check_declaration",side_effect=fake_check):
                result=prepare(territory_id="x",edition="2025",package_out=root/"out",root=root,declaration=decl)
            self.assertEqual(result["decision"],"ACQUIRE")
            selected=result["selected_source"]
            frozen=root/"out"/selected["path"]
            self.assertTrue(frozen.is_file())
            self.assertEqual(selected["bytes"],frozen.stat().st_size)
            self.assertEqual(selected["sha256"],hashlib.sha256(frozen.read_bytes()).hexdigest())
            self.assertEqual(selected["records"],2)

    def test_block_preserves_checker_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); decl=root/"decl.yaml"; decl.write_text("schema: synthetic\n",encoding="utf-8")
            def fake_check(_declaration,out_dir):
                out=Path(out_dir); out.mkdir(parents=True,exist_ok=True)
                (out/"decision_fuente_electoral.json").write_text('{"decision":"BLOCK"}\n',encoding="utf-8")
                (out/"informe_fuente_electoral.md").write_text("# BLOCK\n",encoding="utf-8")
                return {"decision":"BLOCK","selected_source":None,"checks":[{"status":"BLOCK_UNAVAILABLE"}]}
            with patch("herramientas.preparar_fuente_electoral.load_declaration",return_value={"synthetic":True}), patch("herramientas.preparar_fuente_electoral.check_declaration",side_effect=fake_check):
                result=prepare(territory_id="x",edition="2025",package_out=root/"out",root=root,declaration=decl)
            self.assertEqual(result["decision"],"BLOCK")
            self.assertTrue((root/"out"/"checker"/"decision_fuente_electoral.json").is_file())
            self.assertTrue((root/"out"/"checker"/"informe_fuente_electoral.md").is_file())

    def test_block_without_reuse_contract_or_declaration(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); out=root/"out"
            result=prepare(territory_id="x",edition="2025",package_out=out,root=root)
            self.assertEqual(result["decision"],"BLOCK")
            self.assertTrue((out/"manifest.json").is_file())

if __name__=="__main__": unittest.main()
