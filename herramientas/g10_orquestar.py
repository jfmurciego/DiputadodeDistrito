#!/usr/bin/env python3
"""Compatibilidad temporal: use herramientas/orquestar_ejecucion.py."""
try:
    from herramientas.orquestar_ejecucion import main
except ModuleNotFoundError:
    from orquestar_ejecucion import main

if __name__=="__main__":
    raise SystemExit(main())
