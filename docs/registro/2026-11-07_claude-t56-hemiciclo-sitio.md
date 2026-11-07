## 2026-11-07 — T-56 — Hemiciclo nacional en el sitio publicado

Causa: el propietario dio permiso para publicar el hemiciclo, pero el publicador (`_reutilizable-publicar-sitio.yml`) solo
copiaba `publicado/dashboard/` (índice, app, estilos y `status.json`) y `dashboard/hemiciclo.html` no llegaba a Pages.
Cambio: el publicador 3.3.0 comprueba `dashboard/hemiciclo.html` y que `hemiciclo.json` sea JSON válido, los copia al
`dashboard/` del sitio candidato y falla si el índice no enlaza la página. `dashboard/index.html` y su copia publicada
llevan el enlace «Hemiciclo nacional» con ruta relativa (`hemiciclo.html`, que carga `hemiciclo.json` de su carpeta).
Pruebas: `tests/test_hemiciclo_sitio.py` (3, con una construcción local del sitio y la resolución del enlace en la URL de
Pages), `test_dashboard_pages`, tests de workflows y R015 en verde. No publica: hace falta lanzar «05 Publicación del
Visor» con permiso del propietario.
