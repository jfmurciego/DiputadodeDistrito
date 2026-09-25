# Auditoría de entrada electoral — 19 territorios

Base auditada: `main@6418677a69c8958cb4bba00e74cfef1babef2aca` (2026-09-25).

Esta matriz distingue **elección identificada** de **fuente adquirible a resolución suficiente**. La ausencia de declaración interna DDD no se interpreta como ausencia de resultados externos.

| Territorio | Elección correspondiente | Fuente oficial comprobada / referencia | Estado de carga en HEAD | Paquete / registro durable |
|---|---|---|---|---|
| Andalucía | Parlamento de Andalucía 2022-06-19 | Junta de Andalucía, resultados 2022 | BLOQUEO previo si no hay declaración resoluble | No |
| Aragón | Cortes de Aragón 2023-05-28 | Gobierno de Aragón / resultados electorales | depende del contrato materializado vigente | revisar registro |
| Principado de Asturias | Junta General 2023-05-28 | declaración DDD existente | adquisición declarada | existente |
| Islas Baleares | Parlament de les Illes Balears 2023-05-28 | Govern de les Illes Balears, `caib.es`, resultados definitivos 2023 | BLOQUEO previo: falta declaración DDD adquirible | No |
| Canarias | Parlamento de Canarias 2023-05-28 | ISTAC / Gobierno de Canarias: dataset autonómico oficial; publicación localizada llega a isla, no a sección | BLOQUEO: la fuente autonómica localizada no alcanza la resolución distrital requerida | No |
| Cantabria | Parlamento de Cantabria 2023-05-28 | Gobierno de Cantabria / resultados 2023 | BLOQUEO previo si no hay declaración resoluble | No |
| Castilla-La Mancha | Cortes de Castilla-La Mancha 2023-05-28 | Junta de Comunidades / resultados 2023 | BLOQUEO previo si no hay declaración resoluble | No |
| Castilla y León | Cortes de Castilla y León 2022-02-13 | Junta de Castilla y León / expediente electoral existente | llega a carga pero encuentra incompatibilidad con formato de registro electoral anterior | No válido |
| Cataluña | Parlament de Catalunya 2024-05-12 | Generalitat de Catalunya / resultados 2024 | BLOQUEO previo si no hay declaración resoluble | No |
| Comunidad Valenciana | Corts Valencianes 2023-05-28 | Generalitat Valenciana / resultados 2023 | BLOQUEO previo si no hay declaración resoluble | No |
| Extremadura | Asamblea de Extremadura 2025-12-21 | declaración DDD existente con fuentes oficiales | consulta fuentes; ninguna supera adquisición + resolución requeridas | No válido |
| Galicia | Parlamento de Galicia 2024-02-18 | Xunta de Galicia, cuatro CSV oficiales por provincia a nivel mesa | adquisición declarada | existente |
| Comunidad de Madrid | Asamblea de Madrid 2023-05-28 | Comunidad de Madrid / resultados 2023 | BLOQUEO previo si no hay declaración resoluble | No |
| Región de Murcia | Asamblea Regional de Murcia 2023-05-28 | Región de Murcia / resultados 2023 | BLOQUEO previo si no hay declaración resoluble | No |
| Comunidad Foral de Navarra | Parlamento de Navarra 2023-05-28 | Gobierno de Navarra / resultados 2023 | BLOQUEO previo si no hay declaración resoluble | No |
| País Vasco | Parlamento Vasco 2024-04-21 | Gobierno Vasco / resultados 2024 | BLOQUEO previo si no hay declaración resoluble | No |
| La Rioja | Parlamento de La Rioja 2023-05-28 | Gobierno de La Rioja / resultados 2023 | BLOQUEO previo si no hay declaración resoluble | No |
| Ceuta | Asamblea de Ceuta — elecciones locales 2023-05-28 | Ministerio del Interior / elección local 2023 | BLOQUEO previo si no hay declaración resoluble | No |
| Melilla | Asamblea de Melilla — elecciones locales 2023-05-28 | Ministerio del Interior / elección local 2023 | BLOQUEO previo si no hay declaración resoluble | No |

## Hallazgos de arquitectura

1. `03 · Preparación de Resultados Electorales` llama primero a `resolver_eleccion_vigente.py`. Si no existe override, declaración autodetectable o contrato electoral materializado, termina **antes** de `preparar_fuente_electoral.py`; por tanto no consulta ninguna fuente externa.
2. La solución debe ser data-driven: un catálogo común de elecciones y fuentes oficiales, más adaptadores compartidos por formato/resolución. No deben añadirse ramas de código por territorio.
3. El comprobador actual ya impide aceptar HTML como fichero de datos, exige host permitido, resolución mínima y contenido no vacío. Esa puerta debe conservarse.
4. El workflow ya exige `REUSE|ACQUIRE` y un digest antes del registro durable. Debe conservarse la semántica fail-closed: nunca `SUCCESS` sin datos electorales válidos.
5. Ceuta y Melilla se vinculan a sus elecciones a las respectivas Asambleas dentro de las elecciones locales de 2023; no a una elección autonómica ajena.

## Fuentes comprobadas expresamente

- Islas Baleares: el portal oficial del Govern de les Illes Balears publica los resultados definitivos de las elecciones autonómicas de 2023 y la serie de resultados al Parlament. La referencia oficial está localizada, pero en esta auditoría no se ha acreditado todavía un fichero descargable a sección/mesa que satisfaga el contrato DDD.
- Canarias: el portal oficial de datos abiertos/ISTAC publica el dataset de elecciones autonómicas de 2023, pero el recurso localizado declara granularidad hasta **isla**, insuficiente para asignación a distritos DDD. El mismo ISTAC sí publica otros procesos (p. ej. Congreso/municipales) hasta sección, lo que demuestra que no debe confundirse disponibilidad externa con la elección autonómica correcta.

## Criterio de cierre de esta rama

**NO CUMPLIDO todavía.** Esta rama no debe presentarse como solución completa ni fusionarse mientras no existan para los 19: elección resoluble, fuente oficial adquirible a resolución suficiente, carga válida, paquete con procedencia+digest y registro durable; además deben quedar verdes las pruebas sintéticas del flujo común.
