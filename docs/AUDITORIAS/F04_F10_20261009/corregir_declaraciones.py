"""DDD F04 declaration correction, version 1.0.0, 2026-10-10.
New corrective delivery only. Preserve all previous candidates and originals.
No numerical recalculation: input bytes and report bindings remain identical.
"""
from pathlib import Path
import sys, json, shutil, hashlib, zipfile, datetime, copy
OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True
from herramientas.seleccionar_paquete_fuentes import validate_prepared_package
from herramientas.identidad_fuentes_legislatura import territorial_identity

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

results = copy.deepcopy(json.loads((OUT / 'candidate-results.json').read_text()))
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
for row in results['rows']:
    territory = row['territory_id']
    old = OUT / territory / 'candidato-v2'
    new = OUT / territory / 'candidato-v3'
    assert not new.exists()
    shutil.copytree(old, new)
    manifest = json.loads((old / 'manifest.json').read_text())
    inventory = json.loads((old / 'inventario_fuentes.json').read_text())
    by_id = {source['source_id']: source for source in inventory['sources']}
    for name in ['inventario_fuentes.json', 'manifiesto_procedencia.json',
                 'decision_adquisicion.json', 'declaracion_materializacion.json']:
        document = json.loads((old / name).read_text())
        document['predecessor_document'] = {'path': str((old / name).relative_to(ROOT)),
                                          'sha256': digest(old / name)}
        document['original_environment'] = document.get('environment')
        document['original_acquisition_mode'] = document.get('acquisition_mode')
        document['environment'] = 'local_review'
        document['acquisition_mode'] = 'local_derived_candidate'
        document['local_operation_at_utc'] = now
        if 'materialization_root' in document:
            document['materialization_root'] = str(new / 'materialized')
        for source in document.get('sources', []):
            actual = by_id[source['source_id']]
            source['original_acquisition'] = {
                'document': str((OUT / territory / 'original/bundle' / name).relative_to(ROOT)),
                'urls': source.get('urls', []),
                'historical_acquired_at_utc': source.get('acquired_at_utc'),
                'mode': source.get('mode', 'official_live'),
                'note': 'Historical metadata only; no new official acquisition claimed'}
            source['sha256'] = actual['sha256']
            source['bytes'] = actual['bytes']
            source['staged_path'] = str(new / 'materialized' / actual['path'])
            source['mode'] = 'local_derived_candidate' if actual['role'] == 'population' else 'reused_original_bytes'
            if actual['role'] == 'population':
                source['local_derivation'] = actual['derivation']
                if 'acquired_at_utc' in source:
                    source['acquired_at_utc'] = now
                    source['acquired_at_kind'] = 'local_derivation_operation'
            assert digest(new / 'materialized' / source['path']) == source['sha256']
            assert (new / 'materialized' / source['path']).stat().st_size == source['bytes']
        save(new / name, document)
    package = new / 'prepared_sources.zip'
    with zipfile.ZipFile(package, 'w', zipfile.ZIP_DEFLATED) as archive:
        for file in sorted(new.rglob('*')):
            if file.is_file() and file not in [package, new / 'manifest.json']:
                info = zipfile.ZipInfo(str(file.relative_to(new)), (2026,10,10,0,0,0))
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, file.read_bytes())
    manifest.update(sha256=digest(package), bytes=package.stat().st_size,
                    acquired_at=now, predecessor_package_sha256=digest(old / 'prepared_sources.zip'))
    save(new / 'manifest.json', manifest)
    valid, reasons = validate_prepared_package(new, territory_id=territory, edition='2025',
                                              population_year=2025, section_year=2025)
    assert valid, reasons
    assert digest(new / 'compatibilidad_poblacion_seccionado.json') == digest(old / 'compatibilidad_poblacion_seccionado.json')
    identity = territorial_identity(territory_id=territory, edition='2025', population_year=2025,
        section_year=2025, package_sha256=digest(package),
        compatibility_identity_sha256=row['identity']['compatibility_identity_sha256'])
    receipt = json.loads((OUT / territory / 'derived-receipt.json').read_text())
    receipt.update(identity)
    receipt.update(created_at_utc=now, operation='correct_local_declaration_after_exact_universe_selection',
                   derivation_path=str((new / 'derivation.json').relative_to(ROOT)),
                   predecessor_receipt=str((OUT / territory / 'derived-receipt.json').relative_to(ROOT)),
                   predecessor_receipt_sha256=digest(OUT / territory / 'derived-receipt.json'))
    save(OUT / territory / 'derived-receipt-v3.json', receipt)
    row.update(package=str(package.relative_to(ROOT)), package_sha256=digest(package), identity=identity,
               receipt=str((OUT / territory / 'derived-receipt-v3.json').relative_to(ROOT)))
    print(json.dumps({'territory': territory, 'validation': 'PASS', 'report_reused_exact': True,
                      'package_sha256': digest(package)}))
results['predecessor'] = 'candidate-results.json'
results['corrective_scope'] = 'Declaration consistency and local operation labels; numerical bytes/report unchanged'
save(OUT / 'candidate-results-v3.json', results)
