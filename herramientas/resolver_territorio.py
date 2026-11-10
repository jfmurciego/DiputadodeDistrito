#!/usr/bin/env python3
# PROYECTO: Diputado de Distrito
# VERSIÓN: 1.0.0
# NOMBRE DE VERSIÓN: CLI del resolutor único de ids de territorio (T-214)
# FECHA: 2026-11-10
# ESTADO: vigente — T-214
# QUÉ HACE: `python herramientas/resolver_territorio.py <id>...` imprime id nuevo, id viejo y etiqueta visible. La lógica
#   vive en ddd_core/territorio_ids.py (T-170 §2: un solo resolutor); este fichero solo la reexporta.
# CAMBIOS: fichero nuevo.
# MOTIVO: D-61; consulta del resolutor desde workflows y chats sin importar ddd_core a mano.
# ANTERIOR: ninguna (fichero nuevo)
"""CLI del resolutor único de ids de territorio."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ddd_core.territorio_ids import (  # noqa: E402,F401
    IdReservado, IdTerritorioDesconocido, codigo_semilla, es_variante_350, etiqueta, id_legacy,
    mismo_territorio, notacion, resolver_id, territorio,
)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("ids", nargs="+")
    a = ap.parse_args(argv)
    rc = 0
    for x in a.ids:
        try:
            if es_variante_350(x):
                print(f"{x}\t{resolver_id(x)}\t(variante 350, fuera del corte)")
            else:
                t = territorio(x)
                print(f"{x}\t{t.id}\t{t.id_legacy}\t{t.etiqueta}")
        except (IdTerritorioDesconocido, IdReservado) as e:
            print(f"{x}\tERROR\t{e}", file=sys.stderr)
            rc = 2
    return rc


if __name__ == "__main__":
    sys.exit(main())
