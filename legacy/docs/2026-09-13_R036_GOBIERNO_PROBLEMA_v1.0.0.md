# Hito R036 — Gobierno del problema territorial

**Versión:** 1.0.0  
**Fecha:** 2026-09-13  
**Estado:** implementado; pendiente de certificación CI  
**Anterior:** ninguno — documento nuevo

## Resultado

La puerta de producción ya no admite un K sin procedencia, una excepción de límites sin expediente ni un YAML cuyo nivel de contrato sea ambiguo. Catálogo, contrato, M04, M06 y validación deben coincidir.

## Alcance preservado

No se ejecutó ni recalculó M01–M06. No se abrió ningún territorio. Aragón y Castilla y León mantienen sus valores certificados. Extremadura conserva sus valores históricos como evidencia bloqueada, sin promoción.

## Evidencia

- Política: `docs/POLITICA_K_LIMITES_Y_ESQUEMA.md`.
- Contrato: `docs/CONTRATO_TERRITORIO.md` v1.2.0.
- Puerta: `ddd_core/territory_contract.py` v1.1.0.
- Pruebas: 11 controles locales PASS en admisión, interfaz común y catálogo.

## Siguiente puerta

Certificar CI general. Si pasa, R037 definirá políticas topológicas sin ejecutar comunidades.
