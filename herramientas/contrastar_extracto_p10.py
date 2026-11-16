#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T-323b: contraste local y de solo lectura del extracto del padrón de un paquete P10 con el de un CSV nacional (sin red).

VERSIÓN: 1.0.0
ANTERIOR: ninguna (fichero nuevo)

Uso (lo ejecuta quien tenga R2: Operador/propietario):
  aws s3 cp s3://$R2_BUCKET/arc-e/paquetes-p10/<package_sha256>.zip paquete.zip   # no lo hace este script
  python herramientas/contrastar_extracto_p10.py --paquete-dir <carpeta con manifest.json y prepared_sources.zip> \\
      --padron <65034.csv nacional> --declaracion <declaración territorial> --edicion 2025 --provincias 10
Imprime los dos sha256 (crudos y canónicos) y sale 0 si el canónico coincide, 1 si no.
"""
import argparse
import hashlib
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from herramientas import p10_desde_r2 as p  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--paquete-dir", type=Path, required=True)
    ap.add_argument("--padron", type=Path, required=True)
    ap.add_argument("--declaracion", type=Path, required=True)
    ap.add_argument("--edicion", type=int, required=True)
    ap.add_argument("--provincias", nargs="+", required=True)
    a = ap.parse_args(argv)
    declaracion = yaml.safe_load(a.declaracion.read_text(encoding="utf-8"))
    ref = p.extracto_de_paquete(a.paquete_dir)
    if ref is None:
        print("El paquete no lleva un único 65034.csv")
        return 2
    with a.padron.open("rb") as f:
        vivo = p.extracto_en_streaming(iter(lambda: f.read(1 << 20), b""), declaracion, a.edicion, a.provincias)["extracto"]
    h = lambda b: hashlib.sha256(b).hexdigest()  # noqa: E731
    print(f"paquete  bruto={h(ref)} canonico={h(p.canonico(ref))} bytes={len(ref)} tab={'\\t' in ref.decode('utf-8-sig').splitlines()[0]}")
    print(f"padron   bruto={h(vivo)} canonico={h(p.canonico(vivo))} bytes={len(vivo)}")
    igual = p.canonico(ref) == p.canonico(vivo)
    print("IGUAL" if igual else "DISTINTO")
    return 0 if igual else 1


if __name__ == "__main__":
    sys.exit(main())
