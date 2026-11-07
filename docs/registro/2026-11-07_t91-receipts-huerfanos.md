## 2026-11-07 — T-91 — Receipts electorales huérfanos (Barcelona, Málaga, Alicante)

- Causa: los runs 42416213698, 42418628975 y 42418334746 registraron el producto electoral (receipt + `electoral_product_available=true`) y después fallaron en el archivo en origen (ARCHIVO_ORIGEN_FAILED, ya corregido en #491). Sus manifiestos tienen la fase 04 en `failure` sin run/artefacto. La 00 «Reutilizar» los toma como activo durable y para en DURABLE_LINEAGE_INCOMPATIBLE.
- Cambio: se revierten los tres commits de registro (borra `electoral_product_2025.json` de cada uno; catálogo vuelve a `electoral_product_available=false`, checkpoint M06 run 42409499602 / 42409615215 / 42409605030). `_reutilizable-incorporacion-electoral.yml` 1.2.2: el registro se hace tras el archivo en origen.
- Pruebas: `tests/test_t91_receipt_tras_archivo.py`; gobernanza R015; catálogo.
- Riesgos: la 04 sigue pendiente en los tres; el M06 y la 03 siguen vigentes. Relanzar 00 «Reutilizar» por territorio (Operador, con permiso). Sin tocar motor.
