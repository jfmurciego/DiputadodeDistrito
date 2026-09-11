# M04 — Generar solución inicial

## Propósito
M04 produce exactamente K=67 distritos iniciales contiguos. No pretende ser la solución final: crea un estado inicial reproducible que M05 pueda mejorar.

## Por qué existe separado de M05
Semillado y optimización son problemas distintos. Si se mezclan, no puede saberse si una mejora proviene de mejores semillas o de mejor optimización. La semilla aleatoria está fijada (`12345`) para reproducibilidad.

## Entradas
Grafo M03, geometría M01, K y semilla.

## Productos
`aragon_2025_m04_semillas.geojson.zip`: las 1.463 secciones con `district_id` inicial. `M04/asignacion_inicial.csv`: tabla completa sección→distrito, con CUSEC, municipio, provincia y población cuando están disponibles. `aragon_2025_m04_informe.json`: target, mínimo, máximo, K y control de asignación.

## Qué debe poder auditarse
Qué sección fue asignada a qué distrito; población de cada unidad; geometría resultante; cardinalidad 67; ausencia de secciones sin asignar; determinismo con la misma entrada/semilla.

## Interpretación
Una mala distribución poblacional en M04 no es por sí misma fallo si M05 puede repararla, pero M04 nunca puede entregar una asignación incompleta o estructuralmente inválida.
