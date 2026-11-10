## 2026-11-10 — T-176 — Histórico autonómico: medición de cobertura y lote 2

**Causa:** orden del propietario (vía Planificador, 10-11): retomar el histórico autonómico desde 2011 y medir qué comunidades están completas y cuadradas.

**Cambio:** `herramientas/medir_historico_autonomico.py` 1.0.0 (nuevo; calendario + índice del Observatorio + composiciones + MANIFEST) y `docs/ESTUDIOS/T176_HISTORICO_AUTONOMICO/` (COBERTURA.csv y RESUMEN.md con causas). Reagregadas con `reagregacion_autonomicas.py` (sin cambios) Cantabria 2023, Castilla-La Mancha 2019 y Región de Murcia 2019 en `datos/resultados/historico/autonomicas/`: cuadran, pérdida 0 %; aproximadas en distrito (composición M06 con otro seccionado). Resultado global: 9/17 comunidades completas, 42/75 elecciones cuadran, 33 huecos con causa.
**Límite:** sigla tal cual, «sin homologar» (38 nuevas en `siglas_sin_homologar.json`). Andalucía, Baleares y Aragón 2019-2026 tienen dato por sección pero no distritos vigentes (requiere generar el territorio); el resto solo existe por municipio o provincia.

**Pruebas:** `tests/test_medir_historico_autonomico.py`.

**Efectos:** ninguno en huellas, checkpoints ni workflows. Nada lanzado ni publicado.
