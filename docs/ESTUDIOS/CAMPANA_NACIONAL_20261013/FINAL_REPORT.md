# RAMA NACIONAL — BALANCE A–J

**Estado global: `NATIONAL_INCOMPLETE`.** El candidato local de integración contiene incrementos revisados y pruebas reales de preflight 52/52; no existe acreditación topológica externa 52/52, partición provincial/nacional construida, producto certificado ni autorización de generación. Base de campaña: `main@21a4a150eb14f1abecd5d798b159d84a71df1f4a`. PR #265 estaba fusionada al inicio y no se reabre. Ningún distrito fue generado.

## Contabilidad verificable

Registro: `TASK_REGISTRY.json` (IDs únicos, estados por tarea); DAG: `DEPENDENCIES.json`; bitácora acumulativa: `EVENT_LOG.jsonl`; checkpoint: `CHECKPOINT.json`; matriz derivada: `MATRIZ_CIERRE_AJ.csv`. El registro contiene **80 tareas**: **6 COMPLETE**, **16 INTEGRATED** en el candidato local, **2 TESTING**, **1 REVIEWING**, **53 BLOCKED_EVIDENCE**, **1 WAIT_OWNER** y **1 BLOCKED_ENVIRONMENT** (publicación de PR/CI). `INTEGRATED` significa integrado en la rama candidata, no fusionado a `main`.

| Línea | Tareas | Complete | Integrated | Testing | Ready | Bloqueadas por evidencia | Wait owner | Estado de cierre |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| A | 1 | 1 | 0 | 0 | 0 | 0 | 0 | Cerrada para reglas N08 de alcance aprobado; K=407 y generation=false. |
| B | 3 | 1 | 1 | 1 | 0 | 0 | 0 | Parcial; fuentes/linaje históricos verificados; auditoría de rutas aún en revisión. |
| C | 54 | 1 | 0 | 0 | 0 | 53 | 0 | Parcial; producto geométrico reproducible, 53 tareas de límites externos sin fuente independiente. |
| D | 5 | 0 | 5 | 0 | 0 | 0 | 0 | Parcial; anomalías inventariadas y revisadas, excepciones nominales sin aprobación. |
| E | 3 | 1 | 2 | 0 | 0 | 0 | 0 | Parcial; condiciones necesarias y testigos condicionales; sin factibilidad territorial certificada. |
| F | 3 | 0 | 2 | 0 | 0 | 0 | 1 | Parcial; preflight y composición listos como diagnóstico; generación bloqueada. |
| G | 3 | 1 | 2 | 0 | 0 | 0 | 0 | Parcial; correcciones funcionales y perfil sintético listos; no hay benchmark territorial nacional. |
| H | 2 | 0 | 2 | 0 | 0 | 0 | 0 | Parcial; diagnóstico ejecutado 52/52; 2 M04 estructurales bloqueados, restante sin evidencia suficiente para producto. |
| I | 2 | 0 | 2 | 0 | 0 | 0 | 0 | Parcial; certificador candidato probado; cero productos reales certificados. |
| J | 4 | 1 | 0 | 1 | 1 | 0 | 0 | Parcial; DAG, checkpoint y selector READY; queda PR/CI/revisión de campaña. |

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

- Suite nacional Congreso/N08/M05/preflight/ledger: **259 passed, 7 skipped, 82 subtests passed**.
- Regresión de territorios autonómicos (Galicia, Aragón, contratos topológicos y utilidades compartidas): **65 passed, 7 subtests passed**.
- E003: 8 tests + CLI real 52; G003 2 tests; F002 composer/certifier 29 tests + 10 subtests; selector campaña 4 tests.
- Las omisiones/skips son casos marcados por las suites existentes; no se alteraron tests para obtener PASS. Las advertencias PyProj son de deprecación, sin fallos.

## Bloqueos que quedan

1. **Evidencia geográfica:** falta geometría administrativa independiente de edición/huella compatibles para cerrar los dominios provinciales. El mandato actual prohíbe descargas nuevas; trabajo por unidad C003–C054 se aparca sin inventar coincidencia con el producto INE.
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

Los incrementos técnicos E002, E003, F001, F002, G002, G003, H e I y el ledger están en la rama publicada `codex/national-campaign-controller` (`384d214e05e554fb3cddbcd16a3dddcd8cfb749d`), sin fusionar a `main`. El selector fue recalculado contra el registro vigente; sus 324 artefactos se verifican mediante `CAMPAIGN_ARTIFACTS_SHA256.json`. La punta remota sigue en `384d214e…`: el push del HEAD corregido falló por DNS (`Could not resolve host github.com`). La creación de una PR draft está bloqueada por la herramienta GitHub (aprobación requerida con política `never`) y un intento `gh pr create` también falló por conectividad. No existe PR ni CI del HEAD corregido. Los commits locales `5bd16bc5…` y `ae260f56…` están conservados. La revisión independiente del candidato final está solicitada. Estado `NATIONAL_INCOMPLETE`; no declarar `READY_FOR_FINAL_REVIEW`.
