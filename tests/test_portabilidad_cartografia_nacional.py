"""VERSIÓN: 1.0.0; FECHA: 2026-10-10; NOMBRE: regresión stat portable.
ALCANCE: incorporación C3 sin st_flags y protección BSD; ESTADO: revisión pendiente.
CAMBIOS: negativos y reproducción de defecto Linux; MOTIVO: REVIEW_NO_GO; ORIGEN: nuevo.
"""
import gzip,json,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from herramientas.inventariar_cartografia_historica import incorporate
ROOT=Path(__file__).resolve().parents[1]
FOLDER=ROOT/'docs/ESTUDIOS/cartografia_nacional_20261008'
class WithoutFlags:
    def __init__(self,wrapped):self.wrapped=wrapped
    def __getattr__(self,name):
        if name=='st_flags':raise AttributeError(name)
        return getattr(self.wrapped,name)
class PortableInventory(unittest.TestCase):
    def test_complete_incorporation_on_stat_without_st_flags(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);found=[]
            inventory=json.loads((FOLDER/'inventario.json').read_text())
            for index,record in enumerate(inventory['files']):
                path=root/str(index)/record['name'];path.parent.mkdir()
                path.write_bytes(gzip.decompress((FOLDER/record['archived_path']).read_bytes()));found.append(str(path))
            search=root/'busqueda.json';search.write_text(json.dumps({'found':found}))
            original_stat=Path.stat
            def no_flags(path,*args,**kwargs):return WithoutFlags(original_stat(path,*args,**kwargs))
            self.assertFalse(hasattr(no_flags(search),'st_flags'))
            with patch.object(Path,'stat',no_flags):result=incorporate(search,root/'output')
            self.assertEqual(result['archived_unique_inputs'],4)
            self.assertEqual(result['historical_k'],391)
            self.assertEqual(result['temporal_status'],'NOT_COMPARABLE')
    def test_bsd_cloud_placeholder_is_still_rejected_before_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);path=root/'map.geojson';path.write_text('{}')
            search=root/'busqueda.json';search.write_text(json.dumps({'found':[str(path)]}))
            original_stat=Path.stat
            def placeholder(candidate,*args,**kwargs):
                if candidate==path:return SimpleNamespace(st_flags=0x40000000)
                return original_stat(candidate,*args,**kwargs)
            with patch.object(Path,'stat',placeholder),self.assertRaisesRegex(ValueError,'CLOUD_PLACEHOLDER_NOT_PHYSICAL'):
                incorporate(search,root/'output')
            self.assertFalse((root/'output').exists())
    def test_missing_physical_input_still_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);search=root/'busqueda.json'
            search.write_text(json.dumps({'found':[str(root/'map.geojson')]}))
            with self.assertRaises(FileNotFoundError):incorporate(search,root/'output')
            self.assertFalse((root/'output').exists())
if __name__=='__main__':unittest.main()
