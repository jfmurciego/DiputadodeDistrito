# Preflight nacional: corrección y evidencia

**Versión:** 1.0.0 · **Fecha:** 2026-10-10 · **Estado:** candidato local.
**Origen/base:** `d3a2238188d3f9acccfb8daf081157cf32be4c31`. Documento nuevo, sin predecesor.
**Alcance/motivo:** coherencia del gestor con el resolver común; sin cambios en N1/N2, contratos, catálogos ni fuentes. Dependencia transversal: fuentes oficiales y motor autonómico comunes, consumidos sin modificaciones.

El gestor consulta `build_plan` en continuidad (`reuse`) con la estrategia seleccionada. Los fallos efectivos bloquean la entrada y conservan su causa. `PRODUCT_REUSE_READY` distingue el producto certificado, `GENERATION_READY` exige además el contrato de generación material existente, y `SOURCE_PREPARATION_REQUIRED` expresa adquisición o reacreditación previa. Una ruta planificada no equivale a acreditación.

La matriz de lanzamiento actual es de generación: solo incluye `GENERATION_READY`. Reutilización y preparación son resultados informativos del preflight; no lanzan hijos ni cuentan como campañas completadas. Esta corrección no amplía workflows para ejecutar esas rutas.

Ceuta/Canónico: antes `GENERATION_READY`; ahora `BLOCKED` por `DURABLE_LINEAGE_INCOMPATIBLE`. Ceuta/GerryChain 50 sigue la decisión distinta del resolver para nueva generación. Extremadura/Canónico: antes `BLOCKED`; ahora `PRODUCT_REUSE_READY` mediante `certified_product_lineage`. Extremadura/GerryChain 50 requiere preparación y acreditación; no se relaja ninguna puerta.

Se conserva el predecesor de código y tests en `legacy/` y se añaden cabeceras de versión. CI y run territorial no ejecutados por prohibición expresa del encargo; esta evidencia local no constituye certificación territorial ni aprobación de integración.

## Matriz antes/después

B = BLOCKED; G = GENERATION_READY; R = PRODUCT_REUSE_READY; P = SOURCE_PREPARATION_REQUIRED. Cada celda muestra antes → después. Elect./Terr. indican alcance electoral/territorial.

| CODAUTO | Territorio | Terr. Canónico | Elect. Canónico | Terr. GerryChain 50 | Elect. GerryChain 50 |
|---|---|---|---|---|---|
| 01 | Andalucía | B → P | B → P | B → P | B → P |
| 02 | Aragón | B → B | B → B | B → P | B → P |
| 03 | Principado de Asturias | G → R | G → R | G → G | G → G |
| 04 | Islas Baleares | G → G | G → G | G → G | G → G |
| 05 | Canarias | G → G | G → G | G → G | G → G |
| 06 | Cantabria | G → R | G → R | G → G | G → G |
| 07 | Castilla y León | B → B | B → B | B → P | B → P |
| 08 | Castilla-La Mancha | G → R | G → R | G → G | G → G |
| 09 | Cataluña | B → P | B → P | B → P | B → P |
| 10 | Comunidad Valenciana | B → P | B → P | B → P | B → P |
| 11 | Extremadura | B → R | B → R | B → P | B → P |
| 12 | Galicia | B → B | B → B | B → P | B → P |
| 13 | Comunidad de Madrid | G → G | G → G | G → G | G → G |
| 14 | Región de Murcia | B → P | B → P | B → P | B → P |
| 15 | Comunidad Foral de Navarra | G → G | G → G | G → G | G → G |
| 16 | País Vasco | G → G | G → G | G → G | G → G |
| 17 | La Rioja | G → G | G → G | G → G | G → G |
| 18 | Ceuta | G → B | G → B | G → G | G → G |
| 19 | Melilla | G → G | G → G | G → G | G → G |

La comparación se calcula sobre los mismos bytes de contratos, catálogos y receipts; se usa el predecesor conservado para el antes. `matrix.json` conserva las causas y las decisiones funcionales. No es un nuevo inventario de fuentes.

## Resultados locales

- Escritura: creación, lectura y eliminación de sonda local completadas (`WRITE_OK`).
- Base verificada por `git ls-remote https://github.com/jfmurciego/DiputadodeDistrito.git refs/heads/main`: mismo SHA que HEAD inicial.
- Dos regresiones nuevas contra el gestor anterior: fallan como esperado (5 subcasos fallidos, 0 errores), `baseline-regressions.log`.
- `/private/tmp/madrid-gerrychain-venv/bin/python -m unittest tests.test_gestor_campana_nacional tests.test_continuar_ultimo_resultado_valido tests.test_temporal_source_preflight_contract -q`: **48 pruebas PASS**, `tests-targeted.log`.
- Añadiendo `tests.test_ejecucion_completa`: **83 pruebas, 1 FAIL y 1 ERROR preexistentes**, `tests-expanded.log`. Aislados sin importar gestor en `tests-preexisting.log`; el resolver, su core y estos tests son idénticos a la base.
- Error preexistente: `test_gerrychain_50_is_preserved_in_plan`, fixture Demo sin contrato M01–M06 completo (`CAP_CONTRACT`). Fallo preexistente: `test_reuse_plan_reruns_generation_for_noncanonical_selected_algorithm`, espera no preparar aunque el resolver exige preparación/acreditación. No se modifican estos tests ni se relajan sus puertas.
- `git diff --check`: PASS. CI, suite completa y ejecución territorial: NO EJECUTADAS por alcance/prohibición expresa.

El diff se entrega con commit local y revisión separada de ese SHA. Push, PR, merge, workflows, ejecución de 00/M01–M08 y publicación: NO.
