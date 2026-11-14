## 2026-11-14 — T-305 — La P50 restaura de R2 el estado M08/M06 podado de Actions

Causa: la poda T-278 borró de Actions el `ddd-state-<run>-M08` de los 36 runs archivados en R2 y la P50 por lotes solo lo buscaba allí (lote 1 de composicion-36, run 43617006619: LOTE_RECHAZADO «sin producto publicable»).
Cambio: `herramientas/restaurar_estado_r2.py` 1.0.0 (paquete `ddd-minimo-<run>-M08/M06` de `orchestracion/archivo_r2.json`, sha256 verificado, mismo patrón que `fuente_r2.py`); `_reutilizable-publicar-sitio.yml` 3.16.0 (Actions → R2 → error claro con run, estado y claves; M07 extra si falta la composición; credenciales R2 solo en el env del paso de descarga; copia en `legacy/`).
Pruebas: `tests/test_t305_restaurar_estado_r2.py` (solo en R2 se restaura; sha256 alterado → 53; ausente en ambos → mensaje; M06 si no hay M08; sin credenciales; orden del workflow).
Riesgos: sin 00 ni cambio de huellas. La composición sale del M07 de la descarga completa; si falta, COMPOSICION_NO_RECUPERADA (T-301) rechaza el lote.
