# DDD — Integración nacional en main, cierre de software candidato

**Fecha:** 2026-10-19. **Estado:** integración de software realizada; fuentes históricas y producto territorial nacional NO certificados.

## Autoridad y alcance

El propietario autorizó expresamente al director Work a avanzar en el cierre. Las PR #268 y #270 se integraron sin alterar la regla institucional de K=407 ni la barrera `generation_authorized=false`. La autorización de integración de código NO equivale a acreditar excepciones geográficas o certificar un producto territorial.

## Integraciones realizadas

- **#268**: PR fusionada, merge commit `2cfb21998b20b2ba52c7f31fcfd01b1ee37c0262`, HEAD anterior `509e449f517a85ec48965af45d47238bcdf80758`, CI [39237529402](https://github.com/jfmurciego/DiputadodeDistrito/actions/runs/39237529402) SUCCESS, 1.725 pruebas generales, 28 omitidas, 23 GerryChain.
- **#270**: PR fusionada, merge commit `51c797a89b15d324364ec578f0b76417f7de0b6b`, HEAD anterior `d4bea40085158a0ef0fe9881c97fb3a75ba5d7e2`, CI general [39251514980](https://github.com/jfmurciego/DiputadodeDistrito/actions/runs/39251514980) SUCCESS, 1.748 pruebas generales, 28 omitidas, 23 GerryChain; temporal IGN [39251514740](https://github.com/jfmurciego/DiputadodeDistrito/actions/runs/39251514740) SUCCESS.
- **Prueba 52/52**: `tests/test_auditar_52_entradas_congreso_n08.py` PASS con datos originales N08 ligados a SHA inmutable: 52 circunscripciones, 36.554 secciones, 49.128.297 habitantes y K=407. Esto acredita lectura e integridad de entradas N08, no comparación con CNIG ni existencia de 407 distritos.
- **Corrección de falsificación**: el manifiesto N08 original debe coincidir en sus bytes con hash SHA fijado en el código; un adversario que recalcule sus hashes internos o cambie las poblaciones no puede cruzar la puerta provincial únicamente con el manifiesto falso.
- **Muestra temporal IGN**: GeoJSON original con `TIME=2025-01-01` y `TIME=2026-01-01` demuestra que la capa histórica excluye/incluye una línea de límite de Algemesí y Polinyà de Xúquer. Es una muestra, no cobertura nacional ni prueba de vigencia jurídica por tramos.

## Puertas expresamente NO superadas

1. El CNIG no ha entregado todavía una edición cartográfica vectorial íntegra independiente y acreditada como efectiva a `2025-01-01`. La petición oficial enviada y la muestra IGN WMS no equivalen a ese recibo. `NAT-C-056` no puede darse por validada; las 52 comparaciones administrativas y su roll-up siguen bloqueadas.
2. Las componentes aisladas en Baleares (07), Burgos (09), Gerona (17), Palencia (34) y Pontevedra (36) impiden matemáticamente particiones estrictamente conexas dentro de las bandas de población sin **excepciones nominales** o una corrección cartográfica oficialmente acreditada. No se han concedido excepciones por el hecho de integrar el código.
3. **Revisión independiente formal sobre HEAD completo:** no consta en GitHub. Codex emitió REVIEW_PASS para un parche de anclaje de confianza local, no automáticamente sobre todo el código integrado. Se hizo constar la carencia al ejecutar la integración de software bajo autorización general del propietario. Debe ser subsanada antes de certificación territorial.
4. `NAT-F-003` no ha ejecutado generación real. No hay 407 distritos producidos, verificables ni publicables. El validador mantiene `generation_authorized=false`, sin excepciones automáticas y sin puente topológico artificial.

## Criterio del último control de integración

Esta acta se añade en una rama nacida de `main@51c797a89b15d324364ec578f0b76417f7de0b6b` para solicitar la **CI general del árbol combinado**, que incorpora tanto #268/#270 como otros cambios de fuentes publicados en main durante la campaña. El resultado de la CI se verificará contra el HEAD exacto de esta rama antes de promover esta acta.

**No usar este documento como evidencia de producto nacional terminado.** No modificar decisiones N06/N08 para obtener falsos PASS ni publicar distritos incompletos.
