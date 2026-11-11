## 2026-11-11 — T-244 — Andalucía 2025 resuelve el receipt territorial vivo (253f…/40946875467)

- **Causa** (T-243): la 00 de Andalucía en «Generar desde fuente territorial acreditada» (run 43011608060) salió con
  exit 72 «Artefacto territorial ausente o ambiguo». El catálogo declaraba `independent_source_evidence`
  (057a…/38082966768, `AUTHENTIC_EVIDENCE_ONLY…`, `promoted=false`), cuyo paquete
  `ddd-source-package-andalucia-2025-38082966768` está purgado, y el resolver
  (`consumir_par_fuentes_legislatura._territorial_receipt_evidence`, `resolver_preparacion_legislatura._territorial_candidate`)
  lo prefiere siempre a `preparation_evidence` (253f…/40946875467, paquete vivo hasta 2026-11-28).
- **Cambio**: se retira el bloque `independent_source_evidence` de Andalucía 2025 en `configuracion/catalogo_preparacion.yaml`
  (sin tocar el resolver). Decisión aceptada por el Planificador: el cambio de linaje 057a→253f vale porque D-82 regenera
  todo con el motor nuevo y ambas son la misma fuente oficial INE 2025/2025 en dos adquisiciones. El catálogo no lleva
  cabecera VERSIÓN (YAML de datos que reescriben los runs; no está en `GovernanceHeaders`); la copia anterior queda en git.
- **Par desalineado hasta regenerarlo**: `evidence.prepared_source_pair` (f7a5276f…) sigue apuntando al receipt
  057a…/38082966768; no se edita a mano. `catalogo_preparacion.py validate` (l.219-238) solo comprueba la coherencia
  interna del par (schema, identidad, clave geométrica = identidad territorial del par, receipts durables existentes);
  no lo cruza con `preparation_evidence`, así que el estado valida. Se regenera con `preparacion-legislatura-vigente`
  `prepare_one andalucia`.
- **Secuencia para el Operador** (no ejecutada aquí, antes del 28-11): `preparacion-resultados-electorales` con
  reutilizar=false si el paquete electoral 42463442007 está purgado → `preparacion-legislatura-vigente` `prepare_one andalucia`
  → 00 «Generar desde fuente territorial acreditada» de Andalucía.
- **Pruebas**: `catalogo_preparacion.py validate` OK; test nuevo `tests/test_t244_andalucia_receipt_vigente.py` (el resolver
  elige 253f…/40946875467; si `prepare_one` reescribe `preparation_evidence` con otro run, hay que actualizarlo).
  Comparación completa del catálogo antes/después (fuera de la suite): solo difiere la fila de Andalucía (120 filas). Suite de catálogo/preparación sin fallos nuevos
  respecto a `main`.
