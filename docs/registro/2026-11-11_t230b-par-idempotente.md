## 2026-11-11 — T-230b — Registro del par idempotente ante `territorial_product_reuse`

- Causa (activación 42952637226, Congreso Álava, job 130300395955): `register_pair` comparaba el receipt del par por texto
  completo; el par de 2026-11-10 (`29577f2e…`) se registró antes del M06 (`NO_TERRITORIAL_PRODUCT`) y al rederivarlo
  `territorial_product_reuse` cambia, aunque fuentes y `pair_sha256` coinciden → `PAIR_BLOCK: hash de par existente con contenido contradictorio`.
- Cambio: `herramientas/registrar_par_fuentes_legislatura.py` acepta el receipt existente si solo difiere en campos derivados
  (`DERIVED_PAIR_FIELDS`), en `--persist` y en `--verify-only`, sin reescribirlo (registro histórico inmutable; el campo no entra
  en `pair_sha256` ni lo lee ningún consumidor). Otra diferencia sigue dando `PAIR_BLOCK`. Legacy: `legacy/herramientas/registrar_par_fuentes_legislatura_pre_t230b_20261111.py`.
- Tests: `tests/test_t230b_par_idempotente.py` (Álava, contradicción real, idéntico/nuevo).
