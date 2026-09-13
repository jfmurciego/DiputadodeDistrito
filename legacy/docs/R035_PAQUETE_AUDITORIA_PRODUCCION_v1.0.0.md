# R035 — Paquete de auditoría de producción

**Versión:** 1.0.0  
**Fecha:** 2026-09-13  
**Estado:** pendiente de certificación CI  
**Alcance:** interfaz de producción; sin ejecución territorial.

## Decisión verificable

La línea de producción recibe una ruta de contrato, no un nombre de territorio. El resolutor verifica el contrato antes de devolver una decisión y los workflows usan exclusivamente esa decisión.

## Controles incluidos

| Control | Evidencia |
|---|---|
| Admisión previa | `herramientas/resolver_ejecucion_territorial.py` + `ddd_core/territory_contract.py` |
| Tramo G10 no artesanal | `.github/workflows/g10-ejecutar-tramo-certificado.yml` |
| Línea común futura | `.github/workflows/producir-territorio-por-contrato.yml` |
| No recálculo automático | workflow manual; modos `admit_only` y `verify_only` |
| Ejecución protegida | literal `EXECUTE_WITH_EXPLICIT_USER_AUTHORIZATION` |
| Prueba de fábrica | `tests/test_factory_production_interface.py` |

## Resultado esperado de CI

- Contratos de Aragón y Castilla y León: admitidos por la misma interfaz.
- Cinco contratos defectuosos: rechazados antes de cálculo.
- No se inicia M01–M06 por `push` ni por los modos de control.

## Cierre operativo

Cuando CI quede verde, marcar R035.4 y R035.5 en `docs/CIERRE_INGENIERIA_PRODUCCION.md`. Desde ese momento, una nueva comunidad será trabajo de incorporación contractual y no una modificación de la línea base.
