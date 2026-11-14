#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PROYECTO: Diputado de Distrito
# CLASE: herramienta auxiliar de publicación
# VERSIÓN: 1.0.0
# NOMBRE DE VERSIÓN: V3 como portada con V1 y V2 preservadas
# FECHA: 2026-11-12
# ESTADO: candidato
# CAMBIOS: transforma la redirección V2 ya validada en una redirección V3 con controles de precondición.
# MOTIVO: publicar el nuevo explorador sin perder los visores anteriores ni alterar los productos.
# ANTERIOR: ninguna (fichero nuevo)
"""Promociona /v3/ a portada tras ejecutar preparar_portada_v2.py, conservando /v1/ y /v2/."""
from __future__ import annotations
import argparse
from pathlib import Path


def preparar_portada_v3(site: Path) -> None:
    principal = site / "index.html"
    required = [principal, site / "v1" / "index.html", site / "v2" / "index.html",
                site / "v3" / "index.html", site / "v3" / "v3.js", site / "v3" / "v3.css",
                site / "v3" / "calendario.json"]
    missing = [str(p.relative_to(site)) for p in required if not p.is_file()]
    if missing:
        raise FileNotFoundError("Faltan recursos de publicación V3: " + ", ".join(missing))
    old = principal.read_text(encoding="utf-8")
    if old.count('url=v2/') != 1 or old.count('new URL("v2/"') != 1:
        raise ValueError("La portada anterior no es el redirect V2 certificado")
    new = old.replace("v2/", "v3/").replace("Visor V2", "Visor V3").replace("visor V2", "visor V3")
    if 'url=v3/' not in new or 'new URL("v3/"' not in new:
        raise ValueError("No se ha construido una redirección V3 válida")
    principal.write_text(new, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, required=True)
    args = parser.parse_args()
    preparar_portada_v3(args.site)


if __name__ == "__main__":
    main()
