# Hito R036 — Gobierno del problema territorial

**Versión:** 1.1.0  
**Fecha:** 2026-09-13  
**Estado:** certificado  
**Anterior:** `legacy/docs/2026-09-13_R036_GOBIERNO_PROBLEMA_v1.0.0.md`

## Resultado

La puerta de producción ya no admite un K sin procedencia, una excepción de límites sin expediente ni un YAML cuyo nivel de contrato sea ambiguo. Catálogo, contrato, M04, M06 y validación deben coincidir.

## Alcance preservado

No se ejecutó ni recalculó M01–M06. No se abrió ningún territorio. Aragón y Castilla y León mantienen sus valores certificados. Extremadura conserva sus valores históricos como evidencia bloqueada, sin promoción.

## Evidencia

- Política: `docs/POLITICA_K_LIMITES_Y_ESQUEMA.md`.
- Contrato: `docs/CONTRATO_TERRITORIO.md` v1.2.0.
- Puerta: `ddd_core/territory_contract.py` v1.1.0.
- CI: commit `3d1337c`; cinco workflows SUCCESS: contratos `34756687089`, suite general `34756687115`, G10 `34756687096`, Aragón `34756687111` y Castilla y León `34756687113`.
- Pruebas: 11 controles locales PASS en admisión, interfaz común y catálogo.

## Siguiente puerta

R037 definirá políticas topológicas sin ejecutar comunidades.
