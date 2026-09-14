# C-08 — Motor M04 único y trazable

Versión: 1.0.1  
Fecha: 2026-09-13  
Estado: cerrado y certificado en CI 34786162160.  
Anterior: `legacy/docs/AUDITORIA_C08_MOTOR_M04_v1.0.0.md`.

## Hallazgo

El ejecutable `modulos/04_generar_semillas.py` cargaba por ruta el snapshot
`m04_seed_engine_v754.py`; este repetía el mecanismo para ejecutar v7.4.5 y el
postproceso v7.4.9. Otros seis snapshots con cargadores semejantes permanecían
en el mismo directorio. El resultado era reproducible, pero no permitía
identificar el motor vigente mediante un contrato único ni seguir la cadena con
imports ordinarios.

## Resolución vinculante

- `ddd_core/m04_seed_engine.py` es el único motor vigente.
- `modulos/04_generar_semillas.py` es su único ejecutable del pipeline.
- `configuracion/m04_engine.json` identifica versión, punto de entrada y los dos
  componentes internos congelados que componen el comportamiento certificado.
- El ejecutable y la herramienta auxiliar usan imports estáticos del motor
  canónico; no contienen carga por ruta ni selector de versión.
- Los restantes ficheros `m04_seed_engine_v*.py` son snapshots históricos y el
  contrato declara expresamente que no son puntos de entrada.

## Alcance de la verificación

La prueba `tests/test_m04_engine_contract.py` valida el contrato, la existencia
de los puntos de entrada, la ausencia de `importlib` y
`spec_from_file_location` en toda la ruta operativa y la importación explícita
del motor canónico. La equivalencia de composición es estructural: núcleo
v7.4.5, política de puertas v7.5.4 y postproceso v7.4.9, sin modificar sus
algoritmos.

No se ejecuta ni recalcula M01–M06 y no se altera ningún producto territorial.
C-01 permanece fuera de alcance.

La suite general del commit `5645a23` finaliza en `SUCCESS` en la ejecución
`34786162160`. Fue el único workflow activado; no se ejecutó ninguna regresión
territorial.

## Riesgo residual

Los snapshots históricos continúan físicamente en `ddd_core/` para evitar una
retirada destructiva en el mismo cambio que fija la ruta operativa. No pueden
seleccionarse desde el pipeline ni desde la herramienta auxiliar. Su traslado
material a `legacy/` pertenece a la limpieza R038, que sigue suspendida.
