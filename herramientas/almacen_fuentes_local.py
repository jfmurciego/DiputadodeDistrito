#!/usr/bin/env python3
"""Almacén local explícito de fuentes preparadas, sin adquisición.

Versión: 1.0.0; nombre: Recuperación local; fecha: 2026-10-08.
Alcance: recuperación y lectura local; estado: candidato local.
Cambios: nuevo adaptador; motivo: conservar artifacts exactos.
Origen: 4e5e3be53364874d0e056ade64d64ab6471b28b7; predecesor: ninguno.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

from herramientas.identidad_fuentes_legislatura import digest, territorial_identity
from herramientas.seleccionar_paquete_fuentes import validate_prepared_package

SCHEMA = "ddd.local-source-recovery/1.0"
BASE = "4e5e3be53364874d0e056ade64d64ab6471b28b7"


class LocalSourceError(ValueError):
    """Paquete ausente, corrupto o incompatible; nunca activa adquisición."""


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise LocalSourceError(message)


def inspect_zip(archive: zipfile.ZipFile) -> None:
    """Rechaza ambigüedad, traversal y tipos especiales antes de leer/extractar."""
    seen = set()
    total = 0
    for item in archive.infolist():
        p = PurePosixPath(item.filename)
        mode = item.external_attr >> 16
        require(bool(item.filename) and not p.is_absolute()
                and '..' not in p.parts and '\\' not in item.filename
                and ':' not in item.filename and '\x00' not in item.filename,
                'ZIP: ruta peligrosa')
        require(str(p) not in seen, 'ZIP: ruta duplicada')
        seen.add(str(p))
        require(stat.S_IFMT(mode) in (0, stat.S_IFREG, stat.S_IFDIR),
                'ZIP: enlace o tipo especial')
        total += item.file_size
        require(total <= 1024 * 1024 * 1024, 'ZIP: expansión superior a 1 GiB')
    require(archive.testzip() is None, 'ZIP: CRC incorrecto')


def validate_artifact(path: Path, expected: dict, remote: dict, receipt: dict,
                      destination: Path) -> dict:
    for key in ('artifact_sha256', 'package_sha256', 'territorial_identity_sha256',
                'compatibility_report_sha256', 'compatibility_identity_sha256'):
        require(digest(expected[key], label=key) == expected[key], 'digest no canónico: ' + key)
    require(path.is_file(), 'artifact ausente')
    require(path.stat().st_size == remote['size_in_bytes'], 'tamaño artifact incorrecto')
    require(sha256(path) == expected['artifact_sha256'], 'SHA artifact incorrecto')
    require(remote['digest'] == 'sha256:' + expected['artifact_sha256'], 'digest remoto contradictorio')
    require(remote['workflow_run']['id'] == expected['run_id'], 'run remoto contradictorio')
    require(remote['workflow_run']['head_sha'] == expected['source_commit'], 'commit remoto contradictorio')
    require(remote['name'] == expected['artifact_name'], 'nombre remoto contradictorio')
    require(not remote['expired'], 'artifact expirado')
    for key in ('territory_id', 'edition', 'population_year', 'section_year', 'run_id',
                'artifact_name', 'artifact_sha256', 'package_sha256', 'source_commit',
                'territorial_identity_sha256', 'compatibility_report_member',
                'compatibility_report_sha256', 'compatibility_identity_sha256'):
        require(receipt.get(key) == expected[key], 'receipt contradictorio: ' + key)
    require(receipt.get('schema') == 'ddd.territorial-source-receipt/1.0'
            and receipt.get('kind') == 'territorial_source', 'receipt incompatible')
    identity = territorial_identity(**{k: expected[k] for k in
        ('territory_id', 'edition', 'population_year', 'section_year', 'package_sha256',
         'compatibility_identity_sha256')})
    require(identity['territorial_identity_sha256'] == expected['territorial_identity_sha256'],
            'identidad territorial contradictoria')
    with zipfile.ZipFile(path) as archive:
        inspect_zip(archive)
        require(set(archive.namelist()) == {'manifest.json', 'prepared_sources.zip'},
                'estructura exterior incompatible')
        manifest = json.loads(archive.read('manifest.json'))
        require(manifest.get('path') == 'prepared_sources.zip', 'ruta interior incompatible')
        for key in ('territory_id', 'edition', 'population_year', 'section_year'):
            require(str(manifest.get(key)) == str(expected[key]), 'manifest incompatible: ' + key)
        require(manifest.get('sha256') == expected['package_sha256'], 'SHA interior contradictorio')
        destination.mkdir(parents=True, exist_ok=False)
        archive.extractall(destination)
    bundle = destination / 'prepared_sources.zip'
    require(sha256(bundle) == expected['package_sha256'], 'SHA paquete incorrecto')
    with zipfile.ZipFile(bundle) as archive:
        inspect_zip(archive)
        report = archive.read(expected['compatibility_report_member'])
        require(hashlib.sha256(report).hexdigest() == expected['compatibility_report_sha256'],
                'SHA compatibilidad incorrecto')
        require(json.loads(report).get('compatibility_identity_sha256')
                == expected['compatibility_identity_sha256'], 'identidad compatibilidad contradictoria')
    valid, reasons = validate_prepared_package(destination, **{k: expected[k] for k in
        ('territory_id', 'edition', 'population_year', 'section_year')})
    require(valid, 'contenido inválido: ' + '; '.join(reasons))
    return manifest


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent,
                                     delete=False) as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
        temporary = Path(stream.name)
    temporary.replace(path)


def recover(inventory: Path, downloads: Path, store: Path, repository: Path) -> dict:
    """Importa exclusivamente bytes ya descargados; conserva inventario/receipts originales."""
    store = store.resolve()
    store.mkdir(parents=True, exist_ok=True)
    rows = json.loads(inventory.read_text())['rows']
    previous_path = store / 'recovery-manifest.json'
    previous = json.loads(previous_path.read_text()) if previous_path.exists() else None
    if previous is not None:
        require(previous.get('schema') == SCHEMA, 'manifiesto previo incompatible')
        require(previous.get('inventory_sha256') == sha256(inventory),
                'inventario distinto: conservar manifiesto previo')
    result = {'schema': SCHEMA, 'metadata': {'version': '1.0.0', 'date': '2026-10-08',
              'scope': 'recuperación local; sin promoción productiva', 'origin': BASE,
              'predecessor': None, 'status': 'LOCAL_ONLY', 'changes': 'nuevo manifiesto',
              'reason': 'conservación reproducible'}, 'inventory_sha256': sha256(inventory),
              'inventory_path': str(inventory), 'store': str(store), 'rows': []}
    order = {'melilla': 0, 'la_rioja': 1, 'galicia': 2}
    for row in sorted(rows, key=lambda r: order.get(r['territory_id'], 3)):
        prior = [r for r in previous['rows'] if r['expected'] == row['expected']] if previous else []
        require(len(prior) <= 1, 'manifiesto previo ambiguo')
        if prior:
            require(prior[0]['origin'] == row['observation']['result']['structuredContent']['artifacts'][0],
                    'procedencia previa contradictoria')
            result['rows'].append(dict(prior[0]))
            continue
        result['rows'].append({'expected': row['expected'],
            'origin': row['observation']['result']['structuredContent']['artifacts'][0],
            'status': 'PENDING', 'artifact_path': None, 'recovered_at': None, 'checks': []})
    atomic_json(store / 'recovery-manifest.json', result)
    for entry in result['rows']:
        expected = entry['expected']
        remote = entry['origin']
        source = downloads / ('ddd-' + expected['territory_id'] + '-original.zip')
        # El almacén sigue siendo recuperable cuando desaparecen las descargas temporales.
        if not source.is_file():
            source = store / 'objects' / expected['artifact_sha256'] / 'artifact.zip'
        try:
            if not source.is_file():
                entry.update(status='UNAVAILABLE', error='bytes descargados ausentes')
                continue
            receipt_path = repository / expected['receipt_path']
            receipt = json.loads(receipt_path.read_text())
            with tempfile.TemporaryDirectory(prefix='.verify-', dir=store) as temporary:
                work = Path(temporary)
                staged = work / 'artifact.zip'
                shutil.copyfile(source, staged)
                validate_artifact(staged, expected, remote, receipt, work / 'prepared')
                target = store / 'objects' / expected['artifact_sha256'] / 'artifact.zip'
                target.parent.mkdir(parents=True, exist_ok=True)
                require(target.resolve().is_relative_to(store), 'objeto fuera del almacén')
                if target.exists():
                    require(sha256(target) == expected['artifact_sha256'], 'objeto existente contradictorio')
                else:
                    with staged.open('rb') as stream:
                        os.fsync(stream.fileno())
                    os.link(staged, target)  # creación atómica sin sobrescritura
                # Los recibos se conservan como objetos separados, por su propio contenido.
                receipt_sha = sha256(receipt_path)
                saved_receipt = store / 'receipts' / (receipt_sha + '.json')
                saved_receipt.parent.mkdir(parents=True, exist_ok=True)
                require(saved_receipt.resolve().is_relative_to(store), 'receipt fuera del almacén')
                if saved_receipt.exists():
                    require(sha256(saved_receipt) == receipt_sha, 'receipt persistente contradictorio')
                else:
                    temp_receipt = work / 'receipt.json'
                    shutil.copyfile(receipt_path, temp_receipt)
                    require(sha256(temp_receipt) == receipt_sha, 'receipt cambió durante copia')
                    with temp_receipt.open('rb') as stream:
                        os.fsync(stream.fileno())
                    os.link(temp_receipt, saved_receipt)
                entry.update(status='RECOVERED_VERIFIED', artifact_path=str(target),
                    receipt_path=str(saved_receipt), receipt_sha256=receipt_sha,
                    recovered_at=datetime.now(timezone.utc).isoformat(),
                    checks=['artifact_size', 'artifact_sha256', 'package_sha256', 'CRC',
                            'safe_zip', 'receipt', 'territorial_identity', 'compatibility',
                            'materialized_sources', 'edition'])
        except (ValueError, OSError, KeyError, zipfile.BadZipFile) as exc:
            entry.update(status='RECOVERED_INVALID', error=str(exc))
        finally:
            atomic_json(store / 'recovery-manifest.json', result)
        print(' '.join(filter(None, (expected['territory_id'], entry['status'],
                                    entry.get('error', '')))), flush=True)
    return result


def consume(store: Path, *, territory_id: str, edition: str,
            territorial_identity_sha256: str, package_sha256: str,
            destination: Path) -> Path:
    """Resuelve por identidad exacta, vuelve a verificar y entrega una copia preparada."""
    store = store.resolve()
    try:
        manifest = json.loads((store / 'recovery-manifest.json').read_text())
        require(manifest.get('schema') == SCHEMA, 'manifiesto local incompatible')
        matches = [r for r in manifest['rows'] if
            all(str(r['expected'].get(k)) == str(v) for k, v in {
                'territory_id': territory_id, 'edition': edition,
                'territorial_identity_sha256': territorial_identity_sha256,
                'package_sha256': package_sha256}.items())]
        require(len(matches) == 1, 'identidad exacta ausente o ambigua')
        row = matches[0]
        require(row['status'] == 'RECOVERED_VERIFIED', 'paquete no verificado')
        expected = row['expected']
        for key in ('artifact_sha256', 'receipt_sha256'):
            value = expected[key] if key == 'artifact_sha256' else row[key]
            require(digest(value, label=key) == value, 'digest no canónico: ' + key)
        artifact = store / 'objects' / expected['artifact_sha256'] / 'artifact.zip'
        require(artifact.resolve().is_relative_to(store), 'objeto fuera del almacén')
        require(str(artifact) == row['artifact_path'], 'ubicación contradictoria')
        receipt = store / 'receipts' / (row['receipt_sha256'] + '.json')
        require(receipt.resolve().is_relative_to(store), 'receipt fuera del almacén')
        require(sha256(receipt) == row['receipt_sha256'], 'SHA receipt incorrecto')
        require(not destination.exists(), 'destino ya existe')
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=destination.parent) as tmp:
            prepared = Path(tmp) / 'prepared'
            validate_artifact(artifact, expected, row['origin'], json.loads(receipt.read_text()), prepared)
            prepared.replace(destination)
        return destination
    except LocalSourceError:
        raise
    except (OSError, KeyError, TypeError, ValueError, zipfile.BadZipFile) as exc:
        raise LocalSourceError('recuperación local fallida: ' + str(exc)) from exc


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--store', required=True, type=Path)
    sub = parser.add_subparsers(dest='action', required=True)
    importer = sub.add_parser('import')
    importer.add_argument('--inventory', required=True, type=Path)
    importer.add_argument('--downloads', required=True, type=Path)
    importer.add_argument('--repository', required=True, type=Path)
    reader = sub.add_parser('read')
    for field in ('territory-id', 'edition', 'territorial-identity-sha256', 'package-sha256'):
        reader.add_argument('--' + field, required=True)
    reader.add_argument('--destination', required=True, type=Path)
    args = vars(parser.parse_args())
    action = args.pop('action')
    store = args.pop('store')
    if action == 'import':
        recover(store=store, **args)
    else:
        print(consume(store, **args))


if __name__ == '__main__':
    main()
