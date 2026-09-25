from pathlib import Path
import yaml
from herramientas.resolver_eleccion_vigente import resolve

ROOT=Path(__file__).resolve().parents[1]

def test_registry_has_exactly_19_registered_territories():
    data=yaml.safe_load((ROOT/'configuracion/registro_electoral.yaml').read_text(encoding='utf-8'))
    assert data['schema']=='ddd-election-registry/1.0'
    assert len(data['territories'])==19
    for tid,row in data['territories'].items():
        assert row['election_id'] and row['election_date'] and row['name']

def test_early_abort_territory_now_resolves_without_source_declaration():
    row=resolve('Cantabria',root_dir=ROOT,edition='2025')
    assert row['territory_id']=='cantabria'
    assert row['election_id']=='cantabria_parlamento_2023'
    assert row['resolution_mode']=='common_election_registry'
    assert row['declaration']==''

def test_ceuta_melilla_are_their_own_assembly_elections():
    ceuta=resolve('Ceuta',root_dir=ROOT,edition='2025')
    melilla=resolve('Melilla',root_dir=ROOT,edition='2025')
    assert ceuta['election_id']=='ceuta_asamblea_local_2023'
    assert melilla['election_id']=='melilla_asamblea_local_2023'
