# RAMA NACIONAL — BALANCE A–J

## Actualización de auditoría y publicación — 2026-10-14

La rama remota `codex/national-campaign-controller` se verificó mediante GitHub API en `ab40ac19294487b571c9c557bb77a5005a05ac21`; no existe una PR para esa rama. La solicitud de crear PR draft fue denegada por la capa de aprobación (`approval required`, policy `never`), y la CLI `gh` no dispone de token válido. Git por shell tampoco pudo resolver `github.com`. El endpoint de runs asociados a PR devolvió cero para el candidato, porque la rama aún no tiene PR. No se repitió la operación denegada ni se eludió autorización.

La auditoría real del ledger encontró una dependencia semánticamente imposible en C: NAT-C-002 pedía acreditación 52/52, y cada uno de sus 52 hijos requería completar NAT-C-002. El grafo no tenía ciclo sintáctico, pero sí circularidad de aceptación. Se separaron catálogo (NAT-C-055), recibo de adquisición común (NAT-C-056), comparaciones independientes por CPRO (NAT-C-003…054) y agregación nacional NAT-C-002. El roll-up ahora depende de los 52 informes; ningún hijo depende del roll-up. La fuente candidata CNIG/IGN está identificada en `ADQUISICION_FUENTE_LIMITE_CNIG.md`, pero no se descargó: la fuente 2026 no prueba sin inspección su vigencia efectiva a 2025-01-01 y la adquisición requiere autorización.

La matriz `MATRIZ_CIERRE_AJ.csv` se deriva del registro; `AUDITORIA_BLOQUEOS_C_003_056.csv` documenta explícitamente la dependencia histórica supersedida y la dependencia actual del DAG. Son **82 tareas**: **6 COMPLETE**, **19 INTEGRATED** (incluido NAT-C-055), **1 REVIEW_PASS**, **53 BLOCKED_DEPENDENCY**, **2 WAIT_OWNER** y **1 BLOCKED_ENVIRONMENT**. Las tareas C003–C054 son 52 dominios provinciales distintos, no 52 fuentes distintas; comparten un único recibo faltante. NAT-C-002 es el roll-up. NAT-C-055 quedó integrado en la rama candidata en edcc767 y obtuvo REVIEW_PASS_WITH_SCOPE_LIMITS; la acreditación topológica no avanzó.

El estado `NATIONAL_EXHAUSTED_AUTHORIZED_WORK` describe el selector actual tras la corrección: no hay tareas elegibles sin el receipt externo o los permisos requeridos. No significa cierre técnico de las 52 fronteras externas, factibilidad provincial, producto certificado ni disponibilidad para producción. Se mantienen K=407 y `generation_authorized=false`.

**Estado global: `NATIONAL_EXHAUSTED_AUTHORIZED_WORK`.** El DAG corregido no tiene tareas READY/DISCOVERED con los permisos y la evidencia actuales. Esto no cierra técnicamente las 52 fronteras externas ni demuestra factibilidad/producto. La rama remota verificada está en `ab40ac19294487b571c9c557bb77a5005a05ac21`; el HEAD exacto de la base de campaña es `main@21a4a150eb14f1abecd5d798b159d84a71df1f4a`. Ningún distrito fue generado y `generation_authorized=false` permanece.

## Contabilidad verificable

Registro: `TASK_REGISTRY.json`; DAG: `DEPENDENCIES.json`; bitácora acumulativa: `EVENT_LOG.jsonl`; checkpoint: `CHECKPOINT.json`; matriz derivada: `MATRIZ_CIERRE_AJ.csv`. `INTEGRATED` representa integración en la rama candidata, no en `main`.

| Línea | Tareas | Complete | Integrated | Implemented | Review pass | Blocked dependency | Blocked evidence | Wait owner | Blocked environment | Estado |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| A | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | Cerrada para siete reglas N08 y K=407; generación falsa. |
| B | 3 | 1 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | Linaje N06/N08 verificado dentro del alcance acreditado. |
| C | 56 | 1 | 1 | 0 | 0 | 53 | 0 | 1 | 0 | Catálogo/dossier integrado en rama; fuente común espera autorización; 52 contrastes y roll-up bloqueados por dependencia real. |
| D | 5 | 0 | 5 | 0 | 0 | 0 | 0 | 0 | 0 | Anomalías inventariadas; excepciones nominales permanecen pendientes. |
| E | 3 | 1 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | Condiciones necesarias/testigos condicionales; sin factibilidad territorial certificada. |
| F | 3 | 0 | 2 | 0 | 0 | 0 | 0 | 1 | 0 | Preflight y composición diagnósticos; generación espera autorización. |
| G | 3 | 1 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | Correcciones funcionales revisadas; escala territorial nacional no acreditada. |
| H | 2 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | Diagnóstico 52/52 al nivel de evidencia disponible; no equivale a factibilidad/producto. |
| I | 2 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | Certificador candidato probado; cero productos reales certificados. |
| J | 4 | 1 | 1 | 0 | 1 | 0 | 0 | 0 | 1 | Ledger/selector revisados; PR/CI bloqueados por autorización de escritura. |
| TOTAL | 82 | 6 | 19 | 0 | 1 | 53 | 0 | 2 | 1 | `NATIONAL_EXHAUSTED_AUTHORIZED_WORK`; ninguna elegible sin dependencia externa/permisos. |

## Resultados comprobados

- **Contrato:** reglas institucionales `N08-OWNER-20261013-7RULES`; las siete políticas, K=407, cuotas aprobadas y barreras Congreso/autonómicos permanecen. `generation_authorized=false` en el contrato, preflight, checkpoints, composer, manifiestos candidatos y diagnósticos.
- **Linaje:** reproducción read-only de 74/74 entradas del producto nacional y 26/26 históricas de Cáceres, con resultados byte-idénticos; no se modificaron manifiestos históricos ni fuentes INE 2025.
- **Topología:** producto nacional existente: 52 unidades, 36.554 CUSEC, 99.597 aristas; 498 pares de solapamiento, de los cuales 9 conectan componentes distintos, sin convertirlos en aristas; 115 CUSEC multipartes sin población por parte. Persisten 77 componentes seccionales y 397 de partes en el inventario nacional. Evidencia original permanece en expediente N08.
- **Condiciones necesarias:** matriz previa mantiene 0 CUSEC sobre techo ordinario y 9 unidades con componentes poligonales>K. Sólo CPRO09 (4 componentes seccionales/K=3) y CPRO34 (3/K=1) fallan esta condición necesaria; no se etiquetan como imposibilidad demostrada, pues el dominio externo y las excepciones no están acreditados.
- **Preflight:** F001 ejecutó M01–M03 con fuentes/grafo reales en las 52 unidades; M04 fue condición necesaria, sin ejecución de particiones; M05/M06 fueron sólo llamadas sintéticas de contrato. Se validaron reportes y checkpoints 52/52 contra SHA del runner, fuentes, contrato, manifest y artefactos; `--resume` volvió a aceptar el checkpoint final. Los 52 registros completaron la fase de diagnóstico, aunque su estado territorial sigue bloqueado o insuficiente; no se trata de 52 PASS de factibilidad. Totales nacionales verificados: 36.554 secciones, 49.128.297 habitantes, 99.597 aristas; cero particiones. Evidencia: `F001_CAMPAIGN_52_FINAL/EVIDENCE_VERIFIED.json`.
- **Testigos condicionales E003:** resultado reproducible 7 `WITNESS_FOUND_CONDITIONAL`, 9 `NECESSARY_CONDITION_FAILED_CONDITIONAL`, 36 `SEARCH_NOT_RUN`; los 52 conservan factibilidad territorial `INSUFFICIENT_EVIDENCE`. Revisor independiente `REVIEW_PASS` en commit `18586bc3e0a20e910cd36fd707cdd36f383b5ff9`.
- **M05:** el caso de reasignación global del fixture de cuatro CUSEC demostró que la prueba de necesidad con asignación fija era insuficiente; selección final se valida independientemente y prioriza reducir cortes municipales. Regresión autonómica conservada. G003 es perfil sintético, no prueba capacidad nacional; el límite de tiempo es soft y la búsqueda intra-provincia no tiene checkpoint/reanudación exacta.
- **Composición nacional:** F002 exige receipts verificables de productos upstream en ruta real y marca explícitamente sintético el alta en memoria; review `REVIEW_PASS_WITH_SCOPE_LIMITS`. Sin producto provincial real disponible, ingesta real no se ensayó.
- **Certificación:** I001/I002 comprueban candidatos y manifiestos de forma independiente; ningún producto real existe para certificar.

## Pruebas

- Suite nacional Congreso/N08/M05/preflight/ledger: **263 passed, 7 skipped, 82 subtests passed**. La suite focal previa de selector/ledger/dependencias temporales registró **10 passed**; tras esta conciliación, los tests de recibo/DAG, ledger, selector y dependencias temporales ejecutaron **13 passed**.
- Regresión de territorios autonómicos (Galicia, Aragón, contratos topológicos y utilidades compartidas): **65 passed, 7 subtests passed**.
- E003: 8 tests + CLI real 52; G003 2 tests; F002 composer/certifier 29 tests + 10 subtests; selector campaña 4 tests.
- Las omisiones/skips son casos marcados por las suites existentes; no se alteraron tests para obtener PASS. Las advertencias PyProj son de deprecación, sin fallos.

## Bloqueos que quedan

1. **Evidencia geográfica:** falta el recibo de bytes y SHA de una delimitación administrativa independiente, además de prueba de vigencia efectiva 2025-01-01. Se identificó CNIG/IGN BDLJE/RCC como candidato, pero su ficha 2026 no demuestra por sí sola la vigencia histórica. NAT-C-056 espera autorización/paquete; C003–C054 dependen de ese recibo común; NAT-C-002 resume esos 52 resultados; cada CPRO mantiene una comparación distinta.
2. **Decisión del propietario:** aprobar o rechazar excepciones nominales de islas, enclaves y discontinuidades, vinculadas a sus CUSEC/partes/hashes; no existe aprobación general automática.
3. **Factibilidad:** faltan población oficial por parte en 115 CUSEC multipartes; E003 sólo aporta testigos internos condicionales para K=1 y no busca para K>1. Ningún heurístico agotado se reporta como imposibilidad.
4. **Producto y operación:** no hay partición real; por tanto no se puede demostrar factibilidad constructiva general ni certificar 407 distritos. El propietario conserva la autorización expresa de generación, promoción y publicación; permanecen desactivadas.
5. **Escalabilidad:** M05 no serializa su frontera de búsqueda intra-provincial; G003 mide sólo fixtures sintéticos. Esto limita reanudación/escala, no altera reglas aprobadas.

## Decisiones necesarias para avanzar a un piloto territorial

- Autorizar adquisición puntual (o aportar) límites administrativos oficiales independientes con edición, licencia y SHA verificables.
- Resolver nominalmente cada excepción necesaria después de revisar el expediente por CUSEC/parte; la aprobación de siete reglas no la sustituye.
- Emitir autorización explícita de ejecución productiva para una provincia y su alcance; no cambia K ni tolerancias.
- Resolver población por partes cuando una regla de asignación física la requiera; no imputar por superficie.

## Integración y siguiente acción

La rama remota `codex/national-campaign-controller` fue verificada por API de solo lectura en `ab40ac19294487b571c9c557bb77a5005a05ac21`; el endpoint de PRs filtrado por esa rama devolvió lista vacía. El fast-forward del ledger ya está publicado y verificado; la creación de la PR draft sigue siendo la operación denegada. La creación de PR draft fue denegada por la capa de aprobación (`approval required`, política `never`); el token `gh` es inválido y el DNS de Git en shell falló. No se eludieron controles ni se repitió la operación denegada. Sin PR no hay CI de PR. Próxima acción de ingeniería de datos: autorización o entrega de un paquete oficial histórico adecuado, seguido del recibo NAT-C-056; próxima acción de integración: acceso GitHub de escritura autorizado para actualizar la rama y crear draft PR. No declarar `READY_FOR_FINAL_REVIEW` hasta integrar el nuevo ledger, revisar y obtener CI del HEAD exacto.
