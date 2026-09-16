# Manifiesto de limpieza de workflows — 2026-09-16

Base de trabajo: `47db9e4c77e07532932416ed06e38ac5f22f5c0d`.

Este paquete es mecánico y no modifica lógica territorial, contratos, K, cuotas, tolerancias, geometría, GerryChain, G10 ni la interfaz principal. Su objetivo es reducir formularios manuales y retirar un reusable huérfano antes de la integración del workflow único.

## Archivados íntegros

| Origen activo | Copia histórica | Motivo |
|---|---|---|
| `.github/workflows/auditar-robustez-semillas-aragon.yml` | `legacy/workflows/consolidacion-interfaz/auditar-robustez-semillas-aragon_v1.1.0.yml` | auditoría pesada manual especializada |
| `.github/workflows/regresion-m06-aragon.yml` | `legacy/workflows/consolidacion-interfaz/regresion-m06-aragon_v1.6.1.yml` | regresión pesada manual especializada |
| `.github/workflows/regresion-m06-castilla-y-leon.yml` | `legacy/workflows/consolidacion-interfaz/regresion-m06-castilla-y-leon_v1.3.0.yml` | regresión pesada manual especializada |
| `.github/workflows/_reutilizable-bootstrap-territorio.yml` | `legacy/workflows/consolidacion-interfaz/_reutilizable-bootstrap-territorio_v1.0.0.yml` | sin referencias entrantes activas; sustituido funcionalmente por la producción modular M01–M03 |

Las copias de `legacy` reutilizan exactamente los blobs de los YAML activos sustituidos.

## Puertas automáticas sin botón manual

- `pruebas-ddd.yml`: conserva `push` y `pull_request`; elimina `workflow_dispatch`.
- `validar-contratos-territoriales.yml`: conserva `push` y `pull_request`; elimina `workflow_dispatch`.
- `validar-productos-publicos.yml`: conserva `push`; elimina `workflow_dispatch`.

## Pruebas adaptadas

- `test_workflow_safety.py`: exige que los workflows especializados estén archivados y que las tres puertas CI no tengan `workflow_dispatch`.
- `test_workflows_regresion_manual.py`: valida la preservación histórica de los disparadores manuales dentro de `legacy`, no su presencia activa.
- `test_estado_produccion_y_visor.py`: traslada la garantía de auditoría geométrica al workflow común `producir-territorio-por-contrato.yml`.

## Clasificación del estado combinado objetivo

Tras integrar este paquete con PR #9 y PR #10, los workflows activos previstos son 12:

- interfaz humana: `ejecucion-generacion-distritos.yml`;
- reutilizables operativos: `_reutilizable-operacion-territorial.yml`, `_reutilizable-auditoria-topologica.yml`, `producir-territorio-por-contrato.yml`, `generar-alternativas-territoriales.yml`, `desplegar-visor-publico.yml`, `g10-control.yml`, `g10-operar-lote.yml`;
- CI/puertas automáticas: `pruebas-ddd.yml`, `validar-contratos-territoriales.yml`, `validar-productos-publicos.yml`;
- notificación automática: `notificar-finalizacion-orquestacion.yml`.

Criterio final: exactamente un `workflow_dispatch`, el de `Ejecucion Generacion de Distritos`. G10 queda reusable/automático, el visor reusable sin botón propio y las puertas CI sin botón manual.

## Integración pendiente con Work

Este paquete no toca `operacion-territorial.yml`, `ejecucion-generacion-distritos.yml`, el visor reusable ni G10. Debe integrarse junto con PR #9 y PR #10, resolviendo los solapes de `test_workflow_safety.py` contra el estado final combinado y actualizando `docs/INVENTARIO_OPERATIVO.md`, que todavía cita el bootstrap como vigente en `main`.
