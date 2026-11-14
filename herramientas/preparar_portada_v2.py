# PROYECTO: Diputado de Distrito
# CLASE: herramienta auxiliar de publicación
# VERSIÓN: 1.0.0
# NOMBRE DE VERSIÓN: Portada V2 sin alterar el visor técnico V1
# FECHA: 2026-11-12
# ESTADO: candidato
# CAMBIOS: redirige la portada a V2 y conserva V1 en /v1/ con base relativa al raíz del sitio.
# MOTIVO: habilitar la web pública V2 manteniendo las rutas y datos de V1.
# ANTERIOR: ninguna (fichero nuevo)

"""Promueve V2 a portada del sitio construido sin modificar los visores de origen.

Uso: python herramientas/preparar_portada_v2.py --site /tmp/site-candidate
"""
from __future__ import annotations

import argparse
from pathlib import Path

PORTADA = """<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta http-equiv="refresh" content="0; url=v2/">
  <title>Diputado de Distrito · Visor V2</title>
  <script>
    window.location.replace(new URL("v2/" + window.location.search + window.location.hash, window.location.href));
  </script>
</head>
<body>
  <p>Accede al <a href="v2/">visor V2 de Diputado de Distrito</a>.</p>
</body>
</html>
"""


def preparar_portada(site: Path) -> None:
    """Sustituye la portada V1 por un redirect a V2, preservando V1 en /v1/."""
    principal = site / "index.html"
    v2 = site / "v2" / "index.html"
    if not principal.is_file() or not v2.is_file():
        raise FileNotFoundError("Faltan index.html de V1 o de V2 en el sitio candidato")
    original = principal.read_text(encoding="utf-8")
    if "<head>" not in original or 'href="dashboard/"' not in original:
        raise ValueError("La portada candidata ya no coincide con la V1 esperada")
    legacy = site / "v1"
    legacy.mkdir(exist_ok=True)
    (legacy / "index.html").write_text(
        original.replace("<head>", '<head>\n  <base href="../">', 1),
        encoding="utf-8",
    )
    principal.write_text(PORTADA, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, required=True)
    args = parser.parse_args()
    preparar_portada(args.site)


if __name__ == "__main__":
    main()
