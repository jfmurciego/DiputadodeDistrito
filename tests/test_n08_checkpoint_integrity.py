"""VERSIÓN1.0.0; FECHA2026-10-12; checkpoint N08 fail closed; origen nuevo.
Alcance corrupción y continuidad, sin producción; motivo hallazgo independiente P1.
"""
import copy
import gzip
import json
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
from herramientas.preflight_topologico_nacional import bytes_hash, json_bytes, read_checkpoint, read_unit_checkpoint, run


class CheckpointIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.output=Path(self.tmp.name);(self.output/'unidades').mkdir()
        self.artifact=self.output/'unidades/39.json.gz'
        self.binding='a'*64;self.payload={'run_binding':self.binding,'nodes':[{'id':'3910101001','pop':249}]}
        raw=json_bytes(self.payload);data=gzip.compress(raw,mtime=0);self.artifact.write_bytes(data)
        self.record={'sha256':bytes_hash(data),'bytes':len(data),'canonical_json_sha256':bytes_hash(raw)}
        self.ledger={'schema':'ddd.congress-topology-checkpoint/1.1','run_binding':self.binding,
                     'completed_codes':['39'],'artifacts':{'unidades/39.json.gz':self.record},'generation_authorized':False}
        self.save()

    def save(self): (self.output/'checkpoint.json').write_bytes(json_bytes(self.ledger))

    def test_intact_checkpoint_reused(self):
        self.assertEqual(read_checkpoint(self.output,self.binding),self.ledger)
        self.assertEqual(read_unit_checkpoint(self.artifact,self.record,self.binding),self.payload)

    def test_altered_population_with_same_binding_is_rejected(self):
        changed=copy.deepcopy(self.payload);changed['nodes'][0]['pop']=0
        self.artifact.write_bytes(gzip.compress(json_bytes(changed),mtime=0))
        with self.assertRaisesRegex(ValueError,'ARTIFACT_HASH_MISMATCH'):read_checkpoint(self.output,self.binding)

    def test_orphan_without_ledger_rejected(self):
        (self.output/'checkpoint.json').unlink()
        with self.assertRaisesRegex(ValueError,'LEDGER_MISSING'):read_checkpoint(self.output,self.binding)

    def test_record_omission_and_missing_artifact_rejected(self):
        self.ledger['artifacts']={};self.save()
        with self.assertRaisesRegex(ValueError,'LEDGER_INVALID'):read_checkpoint(self.output,self.binding)
        self.ledger['artifacts']={'unidades/39.json.gz':self.record};self.save();self.artifact.unlink()
        with self.assertRaisesRegex(ValueError,'ARTIFACT_MISSING'):read_checkpoint(self.output,self.binding)

    def test_stale_binding_and_legacy_checkpoint_rejected(self):
        with self.assertRaisesRegex(ValueError,'STALE_CHECKPOINT_LEDGER'):read_checkpoint(self.output,'b'*64)
        self.ledger.pop('schema');self.save()
        with self.assertRaisesRegex(ValueError,'HASH_LEDGER_REQUIRED'):read_checkpoint(self.output,self.binding)

    def test_canonical_content_hash_verified_before_use(self):
        record=copy.deepcopy(self.record);record['canonical_json_sha256']='c'*64
        with self.assertRaisesRegex(ValueError,'CONTENT_HASH_MISMATCH'):read_unit_checkpoint(self.artifact,record,self.binding)

    def test_empty_new_checkpoint_allowed(self):
        (self.output/'checkpoint.json').unlink();self.artifact.unlink()
        ledger=read_checkpoint(self.output,self.binding)
        self.assertEqual(ledger['completed_codes'],[]);self.assertFalse(ledger['generation_authorized'])


class CheckpointResumeFlowTests(unittest.TestCase):
    """Exercise resume control flow on two toy units; no real territorial run."""
    def setUp(self):
        import geopandas as gpd
        from shapely.geometry import box
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.output=Path(self.tmp.name)
        self.frame=gpd.GeoDataFrame({'CPRO':['01','02'],'CUSEC':['0100101001','0200101001']},
                                    geometry=[box(0,0,1,1),box(2,0,3,1)],crs=25830)
        self.contract={'quotas_by_origin_unit':[{'code':'01','k':1},{'code':'02','k':1}]}
        self.evidence={'source_binding':{'geometry':{'sha256':'a'*64}}}
        def analyze(frame,k,source_hash):
            code=frame.CPRO.iloc[0]
            return {'summary':{'CPRO':code,'sections':1,'population':100,'k':1,'edges':0,
                               'section_graph_components':1,'physical_part_components':1,'overlap_pairs':0},
                    'run_binding':None}
        self.analyzer=analyze

    def execute(self,resume=False):
        with patch('herramientas.preflight_topologico_nacional.load_inputs',return_value=(self.frame,self.contract,self.evidence)), \
             patch('herramientas.preflight_topologico_nacional.analyze_unit',side_effect=self.analyzer) as calculate, \
             patch('herramientas.preflight_topologico_nacional.cross_province_contacts',return_value=[]):
            result=run(Path('unused_toy_source'),self.output,resume=resume)
            return result,calculate.call_count

    def test_complete_resume_retains_future_records_and_identical_bytes(self):
        first,calls=self.execute();self.assertEqual(calls,2)
        before={str(p.relative_to(self.output)):p.read_bytes() for p in self.output.rglob('*') if p.is_file()}
        second,calls=self.execute(resume=True);self.assertEqual(calls,0)
        after={str(p.relative_to(self.output)):p.read_bytes() for p in self.output.rglob('*') if p.is_file()}
        self.assertEqual(first,second);self.assertEqual(before,after)

    def test_complete_resume_cannot_bless_corrupt_artifact(self):
        self.execute();artifact=self.output/'unidades/02.json.gz'
        value=json.loads(gzip.decompress(artifact.read_bytes()));value['summary']['population']=0
        artifact.write_bytes(gzip.compress(json_bytes(value),mtime=0))
        with self.assertRaisesRegex(ValueError,'ARTIFACT_HASH_MISMATCH'):self.execute(resume=True)

    def test_existing_unit_without_record_cannot_be_reused(self):
        self.execute();path=self.output/'checkpoint.json';ledger=json.loads(path.read_bytes())
        ledger['completed_codes']=['01'];ledger['artifacts'].pop('unidades/02.json.gz');path.write_bytes(json_bytes(ledger))
        with self.assertRaisesRegex(ValueError,'UNIT_WITHOUT_CHECKPOINT_RECORD'):self.execute(resume=True)


if __name__=='__main__':unittest.main()
