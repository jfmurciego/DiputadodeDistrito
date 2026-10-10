#!/usr/bin/env python3
"""Versión 1.0.0; Verificación offline; fecha 2026-10-08; candidato local.

Alcance: reconocimiento de todos los paquetes conservados; cambios: nuevo comando.
Motivo: demostrar reutilización sin red; predecesor: ninguno.
Origen: 4e5e3be53364874d0e056ade64d64ab6471b28b7.
"""
import argparse
import json
import socket
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from herramientas.almacen_fuentes_local import consume, sha256


def verify(store: Path) -> dict:
    manifest_path = store / 'recovery-manifest.json'
    manifest = json.loads(manifest_path.read_text())
    before = {str(p): sha256(p) for p in store.rglob('*') if p.is_file()}
    results = []
    with patch.object(socket.socket, 'connect', side_effect=RuntimeError('red prohibida')), \
         patch.object(socket, 'create_connection', side_effect=RuntimeError('red prohibida')):
        with tempfile.TemporaryDirectory(prefix='ddd-offline-') as tmp:
            for row in manifest['rows']:
                expected = row['expected']
                try:
                    path = consume(store, destination=Path(tmp) / expected['territory_id'],
                        **{k: expected[k] for k in ('territory_id', 'edition',
                          'territorial_identity_sha256', 'package_sha256')})
                    digest = sha256(path / 'prepared_sources.zip')
                    results.append({'territory_id': expected['territory_id'],
                        'status': 'PASS', 'package_sha256': digest})
                except Exception as exc:
                    results.append({'territory_id': expected['territory_id'],
                                    'status': 'FAIL', 'error': str(exc)})
    after = {str(p): sha256(p) for p in store.rglob('*') if p.is_file()}
    return {'version': '1.0.0', 'name': 'Verificación de recuperación offline',
        'date': datetime.now(timezone.utc).isoformat(), 'scope': 'local, sin promoción',
        'status': 'PASS' if before == after and results and
            all(r['status'] == 'PASS' for r in results) else 'FAIL',
        'origin': 'herramientas/almacen_fuentes_local.py', 'predecessor': None,
        'changes': 'nueva evidencia', 'reason': 'proceso limpio sin adquisición',
        'manifest_sha256': sha256(manifest_path), 'network_connections': 'FORBIDDEN',
        'originals_unchanged': before == after, 'rows': results}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--store', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    result = verify(args.store.resolve())
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(result['status'], sum(r['status'] == 'PASS' for r in result['rows']),
          '/', len(result['rows']), 'originals_unchanged=', result['originals_unchanged'])
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
