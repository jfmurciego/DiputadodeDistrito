# Cierre técnico nacional N08 — 2026-10-13

Estado: **evidencia de entrada reproducida; factibilidad y certificación siguen separadas**. Este expediente no ejecuta generación ni altera las fuentes acreditadas.

## Resultado verificable

`verificar_evidencia.py` vuelve a leer los productos versionados existentes y valida sus hashes. Confirma 74/74 entradas del manifiesto de entrega N08 nacional y 26/26 entradas del expediente histórico de Cáceres. Los seis archivos funcionales que evolucionaron desde ese expediente se comparan con snapshots históricos byte por byte; el manifiesto original no se reescribe. La matriz `MATRIZ_FACTIBILIDAD_52.csv` se deriva de `INVENTARIO_52.csv`, `COMPONENTES_POBLACION.csv`, los 52 grafos comprimidos y las cuotas aprobadas del contrato actual.

La reproducción confirma 52 unidades, 36.554 CUSEC, 49.128.297 habitantes, K=407 y 99.597 aristas del grafo nacional archivado. Verifica además cero CUSEC por encima del techo ordinario ±15 %, nueve unidades con más componentes de partes poligonales que K, 498 pares solapados, nueve solapamientos cuyos extremos se encuentran en componentes físicos distintos y 115 CUSEC sin atribución poblacional por componente.

Los solapamientos se cuentan como anomalías geométricas y nunca como aristas. Los recuentos de componentes por encima de K y las demás condiciones necesarias no constituyen una prueba suficiente de existencia o inexistencia de una partición. La matriz conserva el estado previo de factibilidad sin elevarlo.

## Políticas y M05

La PR #259 ya contiene las validaciones semánticas exactas de las siete decisiones N08 y de su procedencia `N08-OWNER-20261013-7RULES`. Este incremento conserva esa modificación y añade el modo municipal Congreso explícito, derivado del contrato validado. El modo autónomo por defecto sigue siendo indivisible. En el modo Congreso, se rechaza la fragmentación si la población municipal cabe bajo el techo duro; si lo excede, la cantidad de distritos que la contienen debe ser exactamente `ceil(P_municipio/cap)`, con listado de las CUSEC y certificado aritmético. El auditor M06 sintético aplica la misma condición. Todo movimiento sigue sujeto a integridad CUSEC, conectividad, provincia y límites poblacionales.

Este certificado prueba la necesidad aritmética mínima de más de un distrito por el techo poblacional municipal; no demuestra por sí solo factibilidad del plan completo. Las divisiones cuya necesidad dependa de una combinación topológica distinta de ese límite aritmético quedan rechazadas y requieren una prueba/certificado específico antes de que el motor las acepte; no se habilita un corte arbitrario. Las decisiones nominales pendientes sobre islas, enclaves y discontinuidades no se convierten en excepciones aprobadas. `generation_authorized=false` permanece obligatorio.

## Linaje y transición

`TRANSICION.json` registra el reuso de las fuentes y bytes de productos históricos con las categorías separadas `SOURCE_REUSE`, `ARTIFACT_REUSE`, `STRUCTURAL_REVALIDATION`, `POLICY_REEVALUATION` y `PRODUCT_CERTIFICATION`. La igualdad SHA de una fuente o artefacto no acredita por sí sola que su evaluación topológica satisfaga la política N08 nueva ni certifica un producto territorial.

## Validación local

- Contrato Congreso, políticas, readiness, migración, coexistencia N06/INE, Cáceres, M05 y regresión autonómica pertinente: 169 pruebas pasan, 51 subtests pasan; 1 prueba se omite por el motivo declarado por pytest.
- Reproducción: `python docs/ESTUDIOS/N08_CIERRE_NACIONAL_20261013/verificar_evidencia.py`.
- No se ejecutó `00`, generación, M04–M06 sobre particiones reales, ni se publicaron distritos o mapas.

Las cifras de prueba son ejecuciones locales de este HEAD de trabajo y no sustituyen CI. La comprobación de hashes cubre los manifiestos versionados en el repositorio; no afirma la disponibilidad local de los bytes fuente originales protegidos fuera de esos productos.
