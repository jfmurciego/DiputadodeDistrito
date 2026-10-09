# R034 — Admisión territorial de producción

**Versión:** 1.0.0  
**Fecha:** 2026-09-13  
**Estado:** implementación local verificada; pendiente certificación GitHub Actions  
**Anterior:** R033 — contrato exhaustivo de producto público

## Resultado de gestión

La línea dispone ya de una puerta de entrada real: antes de gastar cálculo, un territorio debe demostrar que su contrato, fuentes, restricciones y conexiones M01–M06 están completos y son coherentes. Un fallo se rechaza antes del motor.

## Evidencia

- Aragón: `ADMITTED`.
- Castilla y León: `ADMITTED`.
- Cinco rechazos probados: restricción ausente, cadena rota, K incoherente, salida fuera del repositorio y contrato no conforme.
- Cálculo territorial ejecutado: ninguno.

## Reenganche

Tras certificar R034 en CI, construir el único workflow M01–M06 por `territory_id`, con esta puerta como primera operación y sin listas internas Aragón/Castilla y León. No lanzar dicho workflow durante la congelación territorial.
