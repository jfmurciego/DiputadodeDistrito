#!/usr/bin/env python3
"""Genera un único HTML autónomo del visor v2 (vista previa privada, T-109). VERSIÓN 1.0.0.
Uso: python visor/v2/construir_vista_previa.py [salida.html]   (por defecto visor_v2_vista_previa.html)
Incrusta CSS, JS, geometría y web/textos.md; necesita internet solo para MapLibre (unpkg)."""
import pathlib, sys
R = pathlib.Path(__file__).resolve().parents[2]
V = R / "visor" / "v2"
leer = lambda p: p.read_text(encoding="utf-8")
h = leer(V / "index.html")
h = h.replace('<link href="v2.css" rel="stylesheet">', "<style>" + leer(V / "v2.css") + "</style>")
datos = {f: leer(V / "datos" / f).replace("</", "<\\/") for f in ("provincias.json", "comunidades.json")}
js = leer(V / "v2.js")
js = js.replace('fetch("datos/provincias.json").then(r=>r.json())', "Promise.resolve(JSON.parse(document.getElementById('d-prov').textContent))")
js = js.replace('fetch("datos/comunidades.json").then(r=>r.json())', "Promise.resolve(JSON.parse(document.getElementById('d-ccaa').textContent))")
js = js.replace('fetch(TEXTOS_URL).then(r=>r.ok?r.text():"")', "Promise.resolve(document.getElementById('d-textos').textContent)")
md = leer(R / "web" / "textos.md").replace("</", "<\\/")
h = h.replace('<script src="v2.js" data-textos="../../web/textos.md"></script>',
    f'<script type="text/plain" id="d-prov">{datos["provincias.json"]}</script>'
    f'<script type="text/plain" id="d-ccaa">{datos["comunidades.json"]}</script>'
    f'<script type="text/plain" id="d-textos">{md}</script><script>{js}</script>')
h = h.replace('src="../nacional/"', 'src="https://jfmurciego.github.io/DiputadodeDistrito/nacional/"').replace('href="../nacional/"', 'href="https://jfmurciego.github.io/DiputadodeDistrito/nacional/" target="_blank" rel="noreferrer"')
salida = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "visor_v2_vista_previa.html")
salida.write_text(h, encoding="utf-8")
print(salida, len(h) // 1024, "KB")
