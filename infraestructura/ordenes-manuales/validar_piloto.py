"""DDD validators 1.1.0, 2026-10-10; offline evidence only, candidate.
Origin: existing handoff/consumer and prepared package validators. No predecessor.
Never runs territorial stages or scripts supplied by the executor.
"""
import argparse
import copy
import hashlib
import importlib
import json
from pathlib import Path
import socket
import sys
import tempfile
from unittest.mock import patch
import zipfile

sys.dont_write_bytecode = True


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(p):
    return json.loads(Path(p).read_text())


def f03(packet):
    prefix = 'DDD-F03-handoffs-20261009/'
    results = []
    with zipfile.ZipFile(packet) as z, tempfile.TemporaryDirectory(prefix='ddd-auto-handoff-') as tmp:
        require(len(z.namelist()) == len(set(z.namelist())), 'Miembros ZIP duplicados')
        for line in z.read(prefix+'SHA256SUMS').decode().splitlines():
            expected, name = line.split('  ', 1)
            require(sha(z.read(prefix+name)) == expected, 'SHA histórico contradictorio: '+name)
        for case, territory, run in [('F03-H1-cantabria','cantabria',37318299003),
                                    ('F03-H2-canarias','canarias',37596900111)]:
            case_root = Path(tmp)/case
            for name in z.namelist():
                relative = name.removeprefix(prefix)
                if relative.startswith(case+'/') and '/negative/' not in relative and not name.endswith('/'):
                    dest = Path(tmp)/relative
                    require(dest.resolve().is_relative_to(Path(tmp).resolve()), 'Traversal ZIP')
                    dest.parent.mkdir(parents=True,exist_ok=True); dest.write_bytes(z.read(name))
            root = case_root/'root'
            sys.path.insert(0, str(root))
            for name in list(sys.modules):
                if name == 'herramientas' or name.startswith('herramientas.'):
                    del sys.modules[name]
            hand = importlib.import_module('herramientas.handoff_evidencia_pre_m04')
            consumer = importlib.import_module('herramientas._resolver_ejecucion_completa_core')
            import yaml
            persisted = root/f'territorios/{territory}/evidencia/catalogo/generation_preflight_2025.json'
            evidence = read(persisted)
            args = dict(persisted_evidence=persisted, handoff=case_root/'handoff.json',
                        metadata=case_root/'handoff-metadata.json', territory_id=territory,
                        edition='2025', run_id=run, source_commit=evidence['source_commit'])
            hand.verify_handoff(**args)
            prep = next(r for r in yaml.safe_load((root/'configuracion/catalogo_preparacion.yaml').read_text())['territories']
                        if r['territory_id']==territory)['editions']['2025']['preparation_evidence']
            consumer_args = dict(root_dir=root, contract_path=f'territorios/{territory}/config/{territory}_2025.yaml',
                                 territory_id=territory, preparation_evidence=prep, require_source=True,
                                 certified_product_ready=False, source_acquisition_planned=False,
                                 pre_m04_accreditation_planned=False, source_recalculation_planned=False)
            verified = read(case_root/'handoff.json')
            accepted = consumer.generation_enablement(first_generation_evidence=verified, **consumer_args)
            require(accepted.get('allowed') is True and accepted.get('route')=='validated_pre_m04_topology', 'Consumidor no acepta')
            negatives = []
            bad = case_root/'bad.json'; bad.write_bytes(args['handoff'].read_bytes()+b' ')
            transport_cases = [('altered_bytes', dict(handoff=bad))]
            for field, value in [('territory_id','madrid'),('edition','2024'),('run_id',run+1),('source_commit','0'*40)]:
                transport_cases.append(('wrong_'+field,{field:value}))
            corrupt = copy.deepcopy(verified); corrupt['graph']['artifact_sha256']='0'*64
            changed = case_root/'bad-graph.json'; changed.write_text(json.dumps(corrupt))
            transport_cases.append(('changed_graph_digest',dict(handoff=changed)))
            for name, changes in transport_cases:
                try:
                    hand.verify_handoff(**dict(args, **changes))
                except hand.PreM04HandoffError:
                    negatives.append(name)
                else:
                    raise ValueError('Transporte aceptó negativo: '+name)
            for name, field, value in [('wrong_territory','territory_id','madrid'),('wrong_run','run_id',run+1),
                                       ('wrong_source_commit','source_commit','0'*40),('wrong_graph_nodes',None,None),
                                       ('wrong_partition_status',None,None)]:
                bad = copy.deepcopy(verified)
                if field: bad[field]=value
                elif name=='wrong_graph_nodes': bad['graph']['nodes']+=1
                else: bad['partitioning']['status']='UNKNOWN'
                rejected=consumer.generation_enablement(first_generation_evidence=bad,**consumer_args)
                require(rejected.get('allowed') is False,'Consumidor aceptó negativo: '+name)
                negatives.append('consumer_'+name)
            badprep=copy.deepcopy(prep);badprep['package_sha256']='0'*64
            rejected=consumer.generation_enablement(first_generation_evidence=verified,**dict(consumer_args,preparation_evidence=badprep))
            require(rejected.get('allowed') is False,'Consumidor aceptó fuente contradictoria')
            negatives.append('consumer_wrong_prepared_source')
            results.append({'territory':territory,'run':run,'acceptance':accepted,'negative_checks':negatives,
                            'handoff_sha256':sha(args['handoff'].read_bytes()),'status':'PASS'})
            sys.path.remove(str(root))
    return {'task':'F03','cases':results,'generation':'NOT_EXECUTED'}


def f04(repo):
    sys.path.insert(0,str(repo))
    from herramientas.seleccionar_paquete_fuentes import validate_prepared_package
    from herramientas.compatibilidad_poblacion_seccionado import validate_compatibility_package
    from herramientas.identidad_fuentes_legislatura import territorial_identity
    root=repo/'docs/AUDITORIAS/F04_F10_20261009'
    matrix=read(root/'matriz-19-v3.json')['rows']
    require(len(matrix)==19 and len({r['territory_id'] for r in matrix})==19, 'Matriz sin 19 territorios únicos')
    require({r['codauto'] for r in matrix}=={f'{n:02}' for n in range(1,20)}, 'Matriz sin CODAUTO completo')
    for r in matrix:
        require(r['generation'] in ('NOT_EVALUATED','UNCHANGED; historical gate evidence retained'),'Matriz promueve generación')
        require(r.get('production_promotion') in ('NONE','UNCHANGED'),'Promoción indebida')
        require(r.get('package_sha256') and r.get('territorial_identity_sha256'), 'Identidad ausente')
    checked=[]
    for territory in ['andalucia','aragon','castilla_y_leon','comunidad_valenciana','extremadura']:
        row=next(r for r in matrix if r['territory_id']==territory)
        package=root/territory/'candidato-v3'
        valid, reasons=validate_prepared_package(package,territory_id=territory,edition='2025',population_year=2025,section_year=2025)
        require(valid, '; '.join(reasons))
        report, report_hash, reasons=validate_compatibility_package(package,territory_id=territory,edition='2025',population_year=2025,section_year=2025,require_ready=True)
        require(not reasons,'; '.join(reasons))
        package_hash=sha((package/'prepared_sources.zip').read_bytes())
        identity=territorial_identity(territory_id=territory,edition='2025',population_year=2025,section_year=2025,
                                     package_sha256=package_hash,compatibility_identity_sha256=report['compatibility_identity_sha256'])
        receipt=read(repo/row['receipt'])
        require(row['package_sha256']==package_hash and row['territorial_identity_sha256']==identity['territorial_identity_sha256'], 'Matriz contradice bytes')
        require(all(receipt[k]==v for k,v in identity.items()),'Receipt contradice identidad')
        checked.append({'territory':territory,'package_sha256':package_hash,'report_sha256':report_hash,'status':'PASS'})
    originals=read(root/'resultados-cinco.json')['rows']
    require(len(originals)==5 and all(r['compatibility']=='BLOCKED' and not r['eligible'] and r['causes'] for r in originals), 'Gaps originales no conservados')
    return {'task':'F04','matrix_rows':19,'checked_candidates':checked,'original_gaps_preserved':True,'generation':'NOT_EXECUTED'}


def main():
    p=argparse.ArgumentParser();p.add_argument('task',choices=['F03','F04']);p.add_argument('--repo',type=Path,required=True)
    p.add_argument('--packet',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    with patch.object(socket.socket,'connect',side_effect=RuntimeError('Red prohibida')), patch.object(socket,'create_connection',side_effect=RuntimeError('Red prohibida')):
        try:
            result=f03(a.packet) if a.task=='F03' else f04(a.repo)
            result['status']='PASS'; rc=0
        except Exception as e:
            result={'task':a.task,'status':'BLOCKED','reason':str(e)};rc=1
    with a.output.open('x') as out: json.dump(result,out,ensure_ascii=False,indent=2);out.write('\n')
    print(json.dumps(result,ensure_ascii=False));return rc

if __name__=='__main__':sys.exit(main())
