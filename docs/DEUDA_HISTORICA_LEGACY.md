# Deuda histórica de `legacy/`

**Fecha de inventario:** 2026-09-11  
**Estado:** deuda heredada; no bloquea la trazabilidad inmediata creada por R015

## Principio
`legacy/` debe conservar el predecesor inmediato de cada versión activa a partir de la disciplina vigente. No se inventan ni reconstruyen artificialmente versiones antiguas que no fueron preservadas en su momento. Git puede conservar parte de ese pasado, pero una versión solo se declara materializada en `legacy/` cuando el fichero existe realmente.

## Huecos históricos conocidos
- M01 había declarado como anterior `legacy/2026-09-11_modulo01_v7.0.2/01_preparar_base_territorial.py`; esa ruta no estaba materializada.
- M06 utilizaba una referencia genérica a `legacy/recuperado_2026-09-11_v6/` que no constituía un predecesor inmediato verificable.
- M07 declaraba `legacy/recuperado_2026-09-11_v6/scripts/ddd_step7_aggregate_election_results_v6_1_params.py`; esa ruta no estaba materializada.
- M08 declaraba `legacy/2026-09-11_modulo08_v7.0.0/08_integrar_resultados.py`; esa ruta no estaba materializada.

## Tratamiento R015
R015 no rellena esos huecos con contenido supuesto. Antes de modificar cada componente activo, preserva exactamente su estado vigente como nuevo predecesor inmediato y hace que la nueva cabecera apunte a esa copia real. Por tanto, desde R015 la cadena futura vuelve a ser continua aunque la arqueología anterior siga incompleta.

Los huecos anteriores permanecen en este inventario para que una auditoría no confunda “predecesor inmediato preservado desde R015” con “historia completa recuperada desde el origen”.
