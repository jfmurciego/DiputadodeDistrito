## 2026-11-07 — T-89 — Fuente secundaria del histórico de generales por sección (nazioenbehatokia.eus)

**Causa:** decisión D-8 del propietario: el histórico de generales 2011-2023 por sección necesita una segunda fuente y contraste con la oficial.

**Cambio:** `herramientas/fuente_nazioenbehatokia.py` 1.0.0 (lector del formato compacto, espejo con sha256, `--subir` a R2, contraste). Manifiesto `orchestracion/fuente_nazioenbehatokia.json` (625 ficheros: índice + 6 elecciones × 52 provincias × datos y geometría; 206 MB). `catalogo_procedencia.py` 1.1.0 añade la sección `fuentes_secundarias` y las incoherencias `CONTRASTE_OFICIAL` (ERROR) y `SIN_CONTRASTE_OFICIAL` (AVISO). Contraste real: 2023-07 (197 partidos-provincia comparados) y 2019-11 (256), 0 errores; la fuente por sección nunca supera a la oficial y queda por debajo hasta 7,4 % (voto CERA, no incluido por sección). 2011, 2015, 2016 y 2019-04: sin fuente oficial local (AVISO). Siglas distintas (p. ej. PSOE/PSC) quedan «sin_homologar».

**Pruebas:** `tests/test_fuente_nazioenbehatokia.py` (sintético, valores a mano) y `tests.test_catalogo_procedencia`.

**Efectos:** ninguno en huellas, checkpoints ni workflows. Pendiente (Operador): subir los ficheros a R2 con `espejar --subir` (credenciales R2); sin ello el catálogo solo registra el prefijo de destino.
