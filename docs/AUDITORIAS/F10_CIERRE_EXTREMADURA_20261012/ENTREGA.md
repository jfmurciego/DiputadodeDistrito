# F10 — cierre de Extremadura

Versión 1.0.0 — 2026-10-12; estado: candidato técnico; territorio: Extremadura.

## Identidad de fuentes y procedencia

La pareja del receipt F10 es INE población 2025 / seccionado 2025. El receipt
`ddd.territorial-source-receipt/1.0`, run `38091144559`, referencia el artefacto
`ddd-source-package-extremadura-2025-38091144559` y el commit productor
`776006e62ebd80ec5e6f51c89123e56649cc3790`.

El original está preservado fuera de Git en
`~/Desarrollo/DDD-almacen/fuentes-oficiales/F10-20261011-autenticos/artefactos/ddd-source-package-extremadura-2025-38091144559.zip`.
Su SHA-256 es `b4241708cbc7eb1fcf3dd7b6298152392731975106bbddaf6d8ae03bc3fcd8dc`;
el digest coincide con el artefacto publicado. El SHA-256 de `prepared_sources.zip`
verificado dentro del original es
`5f55db978522cc3fe5c32cbe25e61005a3e30823acab1ff10b3fe2a824f21b0a`.
El recibo versionado tiene SHA-256
`3de2f0f6ba4bc9cd69ace34d69a5dc51a83d6e1cdc55397fe8d9e475f0f3c593`.

El paquete declara las fuentes oficiales INE 65034 y el seccionado 2025, con sus
URLs en `manifest.json`. El reporte de compatibilidad tiene SHA-256
`a45c3ff9833d9898c56f177180731fd07b52e6dadeb3d3e937a510eaa1664346`; la identidad
de compatibilidad es `cccf94fe04269dc88a5b187bd99ab90c68010619f9b1e6c25319f4b4820d1959`.
La identidad territorial es
`70d7a964b7b837555ce03d5874c5fa04a74a80d5d724947b89fa9107684fd084`.

## Cambio y linajes

Antes, el consumidor #179 bloqueaba Extremadura porque el catálogo no exponía un
`receipt_path` para el receipt F10. El campo aditivo `independent_source_evidence`
registra el receipt como evidencia auténtica no promovida. La validación canónica de
receipt ahora acepta esa vía sin reemplazar la evidencia de preparación histórica.

Se preservan exactamente:

- Preparación histórica: run `35755043806`, paquete SHA-256
  `edd43c6e3589825100d73dd9ecb5af054cf65b3013987616afe5b901f1affb07`.
- Producto territorial M06: run `36472516474`, artefacto SHA-256
  `1a491b8ae90a1051989cca29ffa712ade781adb81d622ac0607cc6fac15d26dd`.
- Receipt F10: run `38091144559`, `promoted: false`, bajo su identidad y hash propios.

No se modificaron el producto, el checkpoint M06, la preparación histórica ni el
catálogo productivo de distritos. El receipt F10 acredita una fuente independiente;
no demuestra que el producto M06 histórico se generara con ella.

## Pruebas y consumidor

- `validate_prepared_package(..., territory_id='extremadura', edition='2025', population_year=2025, section_year=2025)`: `(True, [])`.
- `tests.test_f10_receipt_contract...test_extremadura_f10_receipt_is_authentic_evidence_without_replacing_product_lineage`: PASS.
- `tests.test_f10_receipt_contract...test_extremadura_independent_receipt_consumes_without_replacing_product_source`: PASS.
- `tests.test_f10_preparacion_aislada...test_fourteen_historical_receipts_remain_and_extremadura_f10_is_unpromoted`: PASS.
- Los 14 recibos históricos siguen aceptados; los receipts derivados sin contrato siguen bloqueados.

El consumidor territorial de fuente #179 acepta ahora la evidencia F10 2025/2025.
No se ejecutó `00`, M01–M08, una campaña, generación ni publicación. F10 global sigue
PENDING porque los otros cuatro territorios tienen puertas de población/geometría abiertas.

## Riesgos, entrega y continuidad

La admisión por receipt no sustituye revisión independiente del paquete, acreditación
cartográfica ni promoción. La geometría es la del INE 2025 verificada dentro del paquete;
los demás productos y elecciones siguen regidos por sus contratos propios.

Base: `f87445f5d75a53cee17cd3bcc711854318b795ff`; rama
`codex/f10-cierre-extremadura`; la implementación compartida depende de
`codex/f10-fuente-independiente`. HEAD y PR se anotan al cerrar el incremento.
