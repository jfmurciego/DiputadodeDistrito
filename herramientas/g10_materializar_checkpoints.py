#!/usr/bin/env python3
"""Compatibilidad temporal: use herramientas/materializar_checkpoints.py."""
try:
    from herramientas.materializar_checkpoints import *  # noqa: F401,F403
    from herramientas.materializar_checkpoints import main
except ModuleNotFoundError:
    from materializar_checkpoints import *  # noqa: F401,F403
    from materializar_checkpoints import main

if __name__=="__main__":
    raise SystemExit(main())
