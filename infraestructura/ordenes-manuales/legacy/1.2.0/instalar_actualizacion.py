#!/usr/bin/env python3
"""DDD installer 1.2.0, 2026-10-10, candidate local update of existing ddd.
Predecessor: legacy/1.1.0/instalar_actualizacion.py; explicit dry-run and backup.
Origin: original manual launcher; backup in legacy/1.0.0. Never changes runtime
catalogue, parameters, history, Plan Maestro or ~/.local/bin/ddd.
"""
import argparse
import datetime
import hashlib
from pathlib import Path
import shutil
import sys

BASE=Path(__file__).resolve().parent
FILES=('ddd.py','ddd_auto.py','validar_piloto.py','review.schema.json','auto-policy.json','AUTO.md')


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--target',type=Path,default=Path.home()/'Desarrollo/DDD-control/ordenes-manuales')
    mode=p.add_mutually_exclusive_group()
    mode.add_argument('--apply',action='store_true',help='Aplicar actualización local; NO ejecuta el piloto')
    mode.add_argument('--dry-run',action='store_true',help='Inspeccionar sin escrituras (también por defecto)')
    a=p.parse_args();target=a.target.expanduser().resolve()
    predecessor=BASE/'legacy/1.0.0/ddd.py'
    if digest(target/'ddd.py')!=digest(predecessor):
        raise RuntimeError('Lanzador instalado cambió: revisar nuevo diff antes de aplicar')
    protected=[target/n for n in ('catalogo.json','parametros.json','encargos.json','historial.jsonl')]
    before={p:digest(p) for p in protected}
    for name in FILES:
        if name!='ddd.py' and (target/name).exists():
            raise RuntimeError('Archivo destino ya existe; no se sustituye sin revisión: '+name)
    print('Actualizar el ddd existente:',target)
    print('Conservar ddd.py en legacy/1.0.0; catálogo, parámetros e historial permanecen intactos')
    for name in FILES:print(name,digest(BASE/name))
    if not a.apply:
        print('DRY_RUN: cero escrituras. --apply instala; no consume Codex ni ejecuta tareas.')
        return 0
    timestamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    backup_dir=target/'respaldos-instalacion'/timestamp
    backup_dir.mkdir(parents=True)
    for original in [target/'ddd.py',*protected]:
        shutil.copy2(original,backup_dir/original.name)
    print('Copia de seguridad:',backup_dir)
    backup=target/'legacy/1.0.0/ddd.py'
    backup.parent.mkdir(parents=True,exist_ok=True)
    if backup.exists() and digest(backup)!=digest(predecessor):
        raise RuntimeError('Predecesor existente contradictorio')
    if not backup.exists():shutil.copy2(target/'ddd.py',backup)
    # Install new modules before swapping the entrypoint, preserving manual compatibility.
    for name in FILES[1:]:shutil.copy2(BASE/name,target/name)
    staged=target/'.ddd-1.2.0.py.tmp';shutil.copy2(BASE/'ddd.py',staged);staged.replace(target/'ddd.py')
    if before!={p:digest(p) for p in protected}:raise RuntimeError('Archivo protegido cambió durante instalación')
    print('Instalado. No se ha lanzado ninguna campaña ni modificado el Plan Maestro.')
    return 0

if __name__=='__main__':
    try:sys.exit(main())
    except (OSError,RuntimeError) as e:print('BLOCKED:',e,file=sys.stderr);sys.exit(2)
