## 2026-11-11 — T-239 — P50 en lote: descarga solo lo que publica, 6 runs a la vez

- Causa: la P50 43013776158 (30 runs) llevaba 40 min en «Recuperar ejecución solicitada»: `gh run download --pattern 'ddd-*'`
  en serie baja los estados M01-M06, el paquete fuente y cachés (~640 MB por run, 19,1 GB el lote).
- Cambio: `_reutilizable-publicar-sitio.yml` 3.14.0 baja solo `ddd-audit`, `ddd-audit-electoral`, `ddd-decision`,
  `ddd-full-run-manifest` y `ddd-state` M06/M08 de cada run (lo que leen la acreditación y `describe-production`), hasta 6
  runs a la vez (`DDD_DESCARGAS_PARALELAS`). Si la selección no trae `production_status.json` y un producto M06/M08, ese run
  baja `ddd-*` completo, como antes; también si la selectiva falla o le falta decision, manifest o contigüidad. Todo o nada intacto; puerta `produccion` sin tocar.
- Medida (tamaños por la API; la descarga da 403 desde la nube): los 30 runs del lote pasan de 19,1 GB a 2,4 GB (~80 MB por
  run, de ~640). El tiempo por run sale en la línea `DESCARGA run= modo= segundos= mb=` de la próxima P50.
- Pruebas: `tests/test_t237_publicacion_lotes.py` 1.1.0 (27; `gh` falso con los artefactos de una 00 y sus patrones).
