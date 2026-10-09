# Auditoría R039 — Contrato electoral universal

Versión: 1.0.0  
Fecha: 2026-09-14  
Estado: candidato, pendiente de CI  
Anterior: ninguno — documento nuevo.

## Decisión

M07–M08 son una capa posterior a límites ya fijados. El contrato exige
`boundary_independence: true`: votos, candidaturas y clasificaciones no pueden
alimentar M01–M06. R039 no reabre C-11 ni convierte el resultado partidista en
criterio de distritación.

## Contrato vinculante

La familia `ddd-election` 1.0.0 obliga a declarar convocatoria, territorio,
fecha, procedencia y fecha de recuperación. Cada fuente y el diccionario de
partidos llevan SHA-256. El adaptador de cada fuente es `nested_json` o
`long_csv`; sus campos están en el contrato, no en el ejecutable.

El diccionario aplica normalización Unicode y de espacios, asigna cada alias a
un identificador canónico y usa política `reject`. Los alias ambiguos y las
siglas nuevas bloquean la ejecución, evitando agregaciones silenciosas.

M07 conserva la reconciliación íntegra de C-05. M08 añade una segunda puerta:
geometría y resumen deben contener exactamente los mismos distritos y el
resumen no puede duplicarlos.

## Implantación de referencia

Aragón referencia `aragon_cortes_2026.json`. El contrato conserva el hash
canónico del fichero materializado, declara el adaptador RTVE fuera del código,
incluye las quince candidaturas observadas y traslada sin alterarlas las dos
excepciones electorales certificadas por el Paquete A.

No se adquieren datos nuevos, no se ejecutan territorios y no se recalcula
M01–M08. Las pruebas leen el input electoral existente únicamente para verificar
checksum y cobertura del diccionario; el resto son casos sintéticos.

## Criterio de cierre

- contrato real y fuente superan checksum;
- las quince siglas tienen identidad canónica;
- checksum alterado, alias ambiguo y partido desconocido fallan;
- M08 acepta cobertura exacta y rechaza faltantes y duplicados;
- M07–M08 no contienen nombres ni tablas de Aragón;
- suite general CI en verde.

R040 permanece fuera de alcance y requiere orden expresa.
