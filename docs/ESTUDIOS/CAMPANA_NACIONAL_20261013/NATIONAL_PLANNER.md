# Selector de tareas READY de la campaña nacional

`ddd_core.national_campaign_planner` es un selector de solo lectura para el registro persistente. Valida identidad de tareas, dependencias, correspondencia entre DAG y registry, ciclos y locks de recursos activos. Devuelve candidatos ordenados por prioridad e ID y explica los que esperan dependencias o un lock.

Ejemplo reproducible desde la raíz:

```sh
python -m ddd_core.national_campaign_planner \
  --registry docs/ESTUDIOS/CAMPANA_NACIONAL_20261013/TASK_REGISTRY.json \
  --dependencies docs/ESTUDIOS/CAMPANA_NACIONAL_20261013/DEPENDENCIES.json \
  --locks docs/ESTUDIOS/CAMPANA_NACIONAL_20261013/RESOURCE_LOCKS.json
```

El selector no modifica estados, adquiere locks, asigna agentes ni inicia tareas. Su salida incluye `execution_started=false` y `generation_authorized=false`; la integración Git y las decisiones de producción siguen siendo puertas separadas.
