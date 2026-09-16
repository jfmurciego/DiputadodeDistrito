#!/usr/bin/env python3
"""Compatibilidad temporal: use herramientas/informe_orquestacion.py."""
try:
    from herramientas.informe_orquestacion import build, main, markdown, read
except ModuleNotFoundError:
    from informe_orquestacion import build, main, markdown, read

if __name__=="__main__":
    raise SystemExit(main())
