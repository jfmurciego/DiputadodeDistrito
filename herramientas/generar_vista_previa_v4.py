"""Genera la imagen de vista previa al compartir y los iconos de la V4 a partir de la propia portada (T-451).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-23 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
MOTIVO: al compartir la web (WhatsApp, X…) no salía imagen ni icono: `og:image` apuntaba a `assets/compartir-1200x630.jpg`, que no existía,
  y la V4 no declaraba icono.
QUÉ HACE (a mano, en local; no lo usa ningún workflow):
  - `assets/compartir-1200x630.jpg`: captura con Chromium (Playwright, preinstalado en la sesión) de `visor/v4/compartir-tarjeta.html`
    (los textos, ilustraciones y estilos de la portada; no se publica) a 1200×630, JPEG progresivo de calidad 82.
  - Iconos desde `assets/logotipo_espana.webp` (el logotipo de la cabecera), centrado sobre el fondo de la web (#0b0d0e):
    `assets/favicon.ico` (16, 32 y 48 px), `assets/icono-32.png` y `assets/apple-touch-icon.png` (180 px).
  Requiere Pillow y Node con Playwright. Imprime el sha256 y el tamaño de cada fichero.
USO: python3 herramientas/generar_vista_previa_v4.py
"""
from __future__ import annotations

import hashlib
import io
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

RAIZ = Path(__file__).resolve().parents[1]
V4 = RAIZ / "visor" / "v4"
FONDO = (11, 13, 14)  # --coal de styles.css
CAPTURA_JS = """
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1200, height: 630 }, deviceScaleFactor: 1 });
  await p.goto('file://' + process.argv[2]);
  await p.waitForLoadState('networkidle');
  await p.screenshot({ path: process.argv[3] });
  await b.close();
})();
"""


def icono(lado: int, margen: float = 0.12) -> Image.Image:
    logo = Image.open(V4 / "assets" / "logotipo_espana.webp").convert("RGB")
    util = round(lado * (1 - 2 * margen))
    escala = util / max(logo.size)
    logo = logo.resize((max(1, round(logo.width * escala)), max(1, round(logo.height * escala))), Image.LANCZOS)
    lienzo = Image.new("RGB", (lado, lado), FONDO)
    lienzo.paste(logo, ((lado - logo.width) // 2, (lado - logo.height) // 2))
    return lienzo


def main() -> int:
    salidas = {}
    with tempfile.TemporaryDirectory() as d:
        js, png = Path(d) / "captura.js", Path(d) / "tarjeta.png"
        js.write_text(CAPTURA_JS, encoding="utf-8")
        subprocess.run(["node", str(js), str(V4 / "compartir-tarjeta.html"), str(png)], check=True)
        img = Image.open(png).convert("RGB")
        if img.size != (1200, 630):
            print(f"Tamaño inesperado de la captura: {img.size}", file=sys.stderr)
            return 1
        b = io.BytesIO()
        img.save(b, "JPEG", quality=82, optimize=True, progressive=True)
        salidas["assets/compartir-1200x630.jpg"] = b.getvalue()
    b = io.BytesIO()
    icono(48).save(b, "ICO", sizes=[(16, 16), (32, 32), (48, 48)])
    salidas["assets/favicon.ico"] = b.getvalue()
    for nombre, lado in (("assets/icono-32.png", 32), ("assets/apple-touch-icon.png", 180)):
        b = io.BytesIO()
        icono(lado, 0.06 if lado == 32 else 0.12).save(b, "PNG", optimize=True)
        salidas[nombre] = b.getvalue()
    for rel, datos in salidas.items():
        (V4 / rel).write_bytes(datos)
        print(f"{rel}: {len(datos):,} bytes · sha256 {hashlib.sha256(datos).hexdigest()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
