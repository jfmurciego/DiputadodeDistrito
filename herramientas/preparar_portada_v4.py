#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PROYECTO: Diputado de Distrito
# CLASE: herramienta auxiliar de publicación
# VERSIÓN: 1.0.0
# NOMBRE DE VERSIÓN: V4 oficial en la raíz del sitio
# FECHA: 2026-11-20
# ESTADO: candidato
# CAMBIOS: T-428 (D-184): tras preparar_portada_v3.py, la portada de la V4 (y Comprender y Explorar) pasa a la raíz del sitio
#   construido; /v4/ queda como redirecciones a la raíz; los recursos de la V1 (app.js, escenarios.js, styles.css) se mueven a /v1/
#   porque la V4 usa esos nombres en la raíz. /v2/, /v3/, /docs/, /datos/ y /data/ no se tocan.
# MOTIVO: la V4 es la versión oficial (propietario, 20-11) sin perder ninguna ruta pública ni los enlaces ya compartidos a /v4/.
# ANTERIOR: ninguna (fichero nuevo)
"""Promociona la V4 (copiada en <sitio>/v4/) a la raíz del sitio, conservando /v1/, /v2/, /v3/ y los enlaces a /v4/.

Uso: python herramientas/preparar_portada_v4.py --site /tmp/site-candidate
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

V1_RECURSOS = {"styles.css": 'href="styles.css"', "escenarios.js": 'src="escenarios.js"', "app.js": 'src="app.js"'}
MARCA_V4 = "<title>Diputado de Distrito | Portada</title>"

REDIRECCION = """<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="robots" content="noindex">
  <meta http-equiv="refresh" content="0; url={destino}">
  <link rel="canonical" href="{destino}">
  <title>Diputado de Distrito</title>
  <script>
    window.location.replace(new URL("{destino}" + window.location.search + window.location.hash, window.location.href));
  </script>
</head>
<body>
  <p>Esta página se ha movido: <a href="{destino}">Diputado de Distrito</a>.</p>
</body>
</html>
"""


def destino_en_raiz(rel: Path) -> str:
    """Ruta relativa desde v4/<rel> a la misma página en la raíz, sin «index.html» (v4/mapa/index.html → ../../mapa/)."""
    subir = "../" * len(rel.parts)  # una por cada carpeta de rel más la propia v4/
    if rel.name == "index.html":
        return subir + (rel.parent.as_posix() + "/" if rel.parent.parts else "")
    return subir + rel.as_posix()


def preparar_portada_v4(site: Path) -> None:
    principal, v1, v4 = site / "index.html", site / "v1" / "index.html", site / "v4"
    faltan = [str(p.relative_to(site)) for p in (principal, v1, v4 / "index.html", site / "v3" / "index.html",
                                                 *(site / n for n in V1_RECURSOS)) if not p.is_file()]
    if faltan:
        raise FileNotFoundError("Faltan recursos para promocionar la V4: " + ", ".join(faltan))
    if "url=v3/" not in principal.read_text(encoding="utf-8"):
        raise ValueError("La portada anterior no es la redirección V3 certificada")
    pagina_v1 = v1.read_text(encoding="utf-8")
    if '<base href="../">' not in pagina_v1 or any(pagina_v1.count(ref) != 1 for ref in V1_RECURSOS.values()):
        raise ValueError("La V1 conservada no es la esperada (base ../ y una referencia a cada recurso)")
    choques = sorted(p.name for p in v4.iterdir() if (site / p.name).exists() and p.name not in {"index.html", *V1_RECURSOS})
    if choques:
        raise ValueError("La V4 pisaría rutas del sitio: " + ", ".join(choques))

    # 1. La V1 se lleva sus recursos a /v1/ (con <base href="../"> las rutas se resuelven desde la raíz: v1/app.js).
    for nombre, ref in V1_RECURSOS.items():
        shutil.copy2(site / nombre, site / "v1" / nombre)
        pagina_v1 = pagina_v1.replace(ref, ref.replace('="', '="v1/'), 1)
        (site / nombre).unlink()
    v1.write_text(pagina_v1, encoding="utf-8")

    # 2. La V4 completa a la raíz.
    principal.unlink()
    for p in v4.iterdir():
        (shutil.copytree if p.is_dir() else shutil.copy2)(p, site / p.name)

    # 3. /v4/ queda solo con redirecciones a la misma página en la raíz (conservan ?consulta y #ancla).
    paginas = sorted(p.relative_to(v4) for p in v4.rglob("*.html"))
    shutil.rmtree(v4)
    for rel in paginas:
        (v4 / rel).parent.mkdir(parents=True, exist_ok=True)
        (v4 / rel).write_text(REDIRECCION.format(destino=destino_en_raiz(rel)), encoding="utf-8")

    if MARCA_V4 not in principal.read_text(encoding="utf-8"):
        raise ValueError("La raíz no es la portada de la V4")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, required=True)
    args = parser.parse_args()
    preparar_portada_v4(args.site)


if __name__ == "__main__":
    main()
