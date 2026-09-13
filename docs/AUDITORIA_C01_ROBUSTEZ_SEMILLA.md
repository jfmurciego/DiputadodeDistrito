# Auditoría C-01 — Robustez frente a semilla

**Versión:** 1.0.0  
**Nombre de versión:** Protocolo previo y ejecución mínima  
**Fecha:** 2026-09-13  
**Estado:** candidato; pendiente del run de 50 semillas  
**Anterior:** ninguno — documento nuevo

## Decisión previa a observar resultados

C-01 se evalúa sobre Aragón porque es el baseline publicable prioritario. La
unidad experimental es una ejecución de M05 con los mismos M03, M04, contrato,
objetivo y presupuesto de 20.000 iteraciones que el mapa publicado. Solo cambia
la semilla efectiva del recocido.

Se ejecutan 50 semillas: la publicada `12345` y 49 semillas predeclaradas por la
herramienta. M04 no se repite: su parámetro `seed` no interviene en el algoritmo
y ya se certificó que su resultado es determinista. M01–M03 y M06–M08 tampoco
se ejecutan. Los insumos son los artefactos M03 y M04 del run certificado
`34599224954`, verificados por SHA-256 antes del barrido.

No se cargan resultados electorales ni se calculan métricas partidistas. C-01
mide robustez geométrica y poblacional del procedimiento.

## Métricas y puerta

Por semilla se registran máximo desvío poblacional, distritos fuera de
tolerancia, Polsby–Popper mínimo/medio/mediano, proporción bajo 0,15 y hash de
asignación. Las geometrías intermedias se eliminan después de medirlas.

La garantía G01 queda en `PASS` si, simultáneamente:

1. al menos el 95 % de las semillas produce solución técnica;
2. la semilla publicada queda entre los percentiles 5 y 95 en máximo desvío,
   Polsby–Popper medio y mínimo;
3. la semilla publicada conserva tolerancia poblacional y la puerta provisional
   de forma P05.

La regla se fija antes del run para impedir seleccionar el criterio después de
ver la distribución. El número de asignaciones únicas se informa, pero no se
fuerza diversidad: una salida idéntica para todas las semillas sería robustez
determinista, no un fallo.

## Evidencia esperada

- `C01_SEMILLAS.csv`: una fila por ejecución satisfactoria.
- `EVIDENCIA_C01.json`: distribuciones, percentiles de la semilla publicada,
  fallos, hashes y decisión G01.
- Workflow: `.github/workflows/auditar-robustez-semillas-aragon.yml`.

El primer push del workflow lanza una única ejecución de 50 semillas. Después
queda disponible por `workflow_dispatch`; no se activa por cambios del motor ni
por documentación, evitando recálculos incidentales.
