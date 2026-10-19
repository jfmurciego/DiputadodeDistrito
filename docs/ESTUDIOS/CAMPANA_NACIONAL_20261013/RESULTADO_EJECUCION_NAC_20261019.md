# Ejecución NAC-01…NAC-12 — 19-10-2026

Base verificada: `main@4545491ca70066e2004b53b30ebe9994ed4d9df6`.

Este registro continúa la campaña existente en `CAMPANA_NACIONAL_20261013`; no crea un nuevo planificador ni modifica el DAG ni los estados autoritativos del registro de 82 tareas. La clasificación distingue el trabajo reutilizado del ejecutado en esta sesión. No se generaron distritos y `generation_authorized=false` permanece vigente.

## Resultado por trabajo

| ID | Estado terminal | Resultado y evidencia | Siguiente dependencia concreta |
|---|---|---|---|
| NAC-01 | `BLOCKED_EXTERNAL` | La solicitud oficial CNIG/IGN del 18-10-2026 está confirmada, pero el recibo registra `official_reply_received=false`, `source_bytes_received=false`, sin SHA y `source_accredited=false`. No hay paquete histórico acreditado. | Obtener respuesta, bytes originales, metadatos temporales/licencia y SHA; validar la fecha 2025-01-01 y la cobertura. |
| NAC-02 | `BLOCKED_EXTERNAL` | La documentación IGN confirma que `LimitesTime` permite visualizar límites con `TIME` desde 2009; esto no demuestra exportación vectorial histórica íntegra ni extracción sin generalización. La API Features pública declara 48.195 objetos en la colección actual, con paginación y campos `nationalcode`, `date_boundary` y `endlifespanversion`; el número actual y esos campos no acreditan una captura histórica ni su semántica jurídica. Se añadió un auditor de páginas capturadas con paginación incremental, URLs oficiales, consulta estable y límites. No se adquirió ni fabricó una captura oficial. | Disponer de respuesta oficial o captura completa verificable; contrastar versiones, temporalidad, geometría y completitud. |
| NAC-03 | `COMPLETE` | Instrumentación disponible y probada con fixtures: recibo seguro CNIG, sonda WMS histórica acotada, comparador GeoJSON, auditor de captura paginada API incorporado en esta entrega. La nueva prueba rechaza filtros mutados, paginación incompleta, URLs ajenas, IDs duplicados y geometría malformada. La evidencia de fixtures no se presenta como contraste oficial. | Al recibirse la fuente, fijar el formato/capa real y validar su correspondencia con la interfaz de comparación existente. |
| NAC-04 | `NOT_EXECUTABLE` | No se emitieron los 52 informes oficiales independientes: dependen de una fuente histórica y recibo válidos. Los preflights INE/N08 ya existentes son diagnósticos internos, no sustitutos de esos contrastes. | NAC-01 acreditada y NAC-03 adaptada al paquete recibido. |
| NAC-05 | `NOT_EXECUTABLE` | La consolidación 52/52 no puede cerrarse sin 52 informes individuales verificados. El agregador del DAG ya depende de los informes provinciales, no introduce una dependencia circular artificial. | Completar NAC-04 para las 52 unidades y validar consistencia temporal, hashes y excepciones. |
| NAC-06 | `BLOCKED_EXTERNAL` | Reutilizados diagnósticos geométricos internos de Baleares, Burgos, Gerona, Palencia y Pontevedra; se distinguen componentes físicos/seccionales, aristas lineales, contactos, distancias y solapamientos. No se cambió geometría ni se inventaron conexiones. La atribución administrativa histórica y las excepciones nominales no están acreditadas por una fuente externa recibida. | Obtener límites oficiales históricos y luego someter cada excepción nominal a decisión institucional. |
| NAC-07 | `BLOCKED_EXTERNAL` | Reutilizados los diagnósticos internos de Almería, A Coruña, Lugo y Murcia. La fragmentación física se mantiene como diagnóstico, sin etiquetarla como defecto ni como imposibilidad provincial. | Contraste independiente para determinar cuáles son discontinuidades administrativas y cuáles requieren corrección o expediente nominal. |
| NAC-08 | `BLOCKED_EXTERNAL` | El software nacional de #268/#270/#273 y sus CI se conservan como integrados. La corrida de CI de #273 no equivale a revisión independiente: GitHub no registraba review formal. Esta sesión no atribuye al revisor nacional externo la revisión integral de esos cambios. | Revisión independiente integral del HEAD integrado, separada de la revisión de este incremento. |
| NAC-09 | `BLOCKED_EXTERNAL` | Reutilizados el solver exacto y los testigos condicionales. Los artefactos detallados prueban la condición necesaria de componentes seccionales > K en CPRO 09 y 34. Nueve provincias tienen más componentes de partes poligonales que K, pero ese conteo no demuestra por sí solo imposibilidad; una afirmación heredada de cinco contradicciones no queda conciliada con esos criterios y no se presenta aquí como hecho. Los 36 casos restantes K>1 no tuvieron búsqueda constructiva. | Aclarar el criterio de la afirmación heredada y obtener contraste/decisiones nominales donde corresponda; luego, testigo constructivo verificable por unidad. |
| NAC-10 | `WAIT_OWNER` | Sin distritos reales generados. La puerta mantiene `generation_authorized=false`; no existe en esta sesión autorización productiva específica. | Orden expresa tras superar puertas de fuente, topología, contrato y autorización. |
| NAC-11 | `NOT_EXECUTABLE` | No existe producto real autorizado para certificar. Las pruebas del certificador y sus fixtures no se presentan como certificación territorial. | Producto real generado bajo autorización y excepciones nominales válidas. |
| NAC-12 | `WAIT_OWNER` | No se publicó producto territorial. Sin certificación ni autorización de promoción/publicación. | Certificación del producto y autorización expresa de publicación. |

## Cambios y verificación de esta sesión

Se agregó `ddd_core/congreso_ign_api_snapshot.py` y `tests/test_congreso_ign_api_snapshot.py`. El auditor consume páginas en streaming, limita páginas y bytes por página, preserva el orden de paginación, exige estabilidad exacta de parámetros de selección (incluidas mayúsculas/minúsculas) y produce hashes de los bytes recibidos. No realiza HTTP, no autentica que los bytes procedan de la URL, no prueba CRS/topología, no interpreta jurídicamente la temporalidad y declara expresamente:

- `historical_2025_source_accredited=false`
- `eligible_for_52_province_audits=false`
- `generation_authorized=false`

Resultados reproducibles en el clon aislado sobre la base anterior:

- Pruebas dirigidas de captura API, sonda WMS y recibo CNIG: **30 passed, 17 subtests passed**.
- Herramientas de contraste GeoJSON, recibo/consulta oficial y capturas API/WMS: **50 passed, 17 subtests passed**.
- Regresión Congreso y auditoría de entradas más relacionadas: **151 passed, 59 subtests passed**.
- `py_compile` Python 3.11: PASS.
- Revisión independiente del incremento: `REVIEW_PASS_WITH_SCOPE_LIMITS`; segunda revisión: `REVIEW_PASS`. Ambas cubren el auditor y sus tests, no el software nacional completo ni la acreditación de la fuente.
- Revisión independiente acotada de NAC-09: `GO_ACOTADO`; confirmó que el solver diferencia solución, imposibilidad y búsqueda agotada, y que los siete testigos K=1 son condicionales. Señaló que debe explicitarse la discrepancia entre dos unidades con componentes seccionales > K, nueve con componentes de partes > K y la afirmación heredada de cinco contradicciones.
- SHA-256 módulo: `9d5fdc2ad8edf72dba4ef4a04c4c1495ee7374301cf663663c47a45a7229dc0b`.
- SHA-256 pruebas: `0ce883c524bea1aac4ef085f578066593b96dd4fafbe71f3d5f8188b0b013349`.

La investigación oficial consultada indica que la colección API actual está licenciada CC BY 4.0; su metadato declara CRS de almacenamiento CRS84 y admite CRS adicionales. Estos metadatos describen el servicio actual, no certifican la vigencia ni la geometría al 01-01-2025. El boletín oficial IGN-CNIG de marzo de 2026 describe `TIME` como visualización de límites desde 2009, no como prueba de una extracción vectorial histórica completa.

Referencias oficiales consultadas: [API-Features IGN — colección y objetos](https://api-features.ign.es/collections/administrativeboundary/items?f=html), [esquema](https://api-features.ign.es/collections/administrativeboundary/schema?f=html), [metadatos/licencia/CRS](https://api-features.ign.es/collections/administrativeboundary?f=html) y [boletín IGN-CNIG, marzo de 2026](https://www.ign.es/web/resources/acercaDe/Boletines/Boletin_IGN_mar_2026.pdf), páginas 12–13.

## Bloqueos materiales y decisiones

1. **Externo:** respuesta y cartografía histórica oficial CNIG/IGN, con edición, vigencia al 01-01-2025, esquema/códigos, CRS, licencia, bytes y SHA.
2. **Externo:** revisión integral independiente del software nacional de #268/#270/#273.
3. **Institucional:** aprobación nominal de excepciones insulares/administrativas sólo tras acreditación por fuente.
4. **Producción:** autorización expresa de generación, certificación y publicación; las puertas siguen cerradas.

Ninguna de estas condiciones se rebajó. No se cambió K=407, cuotas, reglas N08 ni fuentes INE 2025. No se alteró el motor autonómico ni se ejecutó `00`, generación territorial o publicación.
