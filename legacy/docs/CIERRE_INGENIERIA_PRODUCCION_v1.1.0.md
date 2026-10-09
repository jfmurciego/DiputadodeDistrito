# Cierre de ingeniería de producción DDD

**Versión:** 1.1.0
**Inicio:** 2026-09-13
**Estado:** CERRADO — línea base lista para auditoría
**Anterior:** `legacy/docs/CIERRE_INGENIERIA_PRODUCCION_v1.0.0.md`
**Propósito:** completar la línea reutilizable sin ejecutar ni abrir territorios durante la congelación.

## Criterio de salida

Un territorio podrá entrar mediante un contrato completo, ser rechazado antes del cálculo si falla, recorrer una única cadena común cuando exista una autorización explícita y dejar una evidencia auditable que otro equipo pueda revisar sin depender de este chat.

## Lista de cierre

- [x] R034 — Puerta de admisión: contrato, fuentes, restricciones y cadena M01–M06 verificables antes de cálculo.
- [x] R035.1 — Resolver universal: eliminar las selecciones Aragón/Castilla y León codificadas de la ejecución G10.
- [x] R035.2 — Línea única: workflow por contrato con modos de admitir, verificar y ejecutar bajo autorización explícita.
- [x] R035.3 — Prueba de fábrica: demostrar contrato válido, rechazos tempranos y ausencia de cálculo en los modos de control.
- [x] R035.4 — Paquete de auditoría: evidencia de CI, trazabilidad, versión, legacy y punto de reenganche.
- [x] R035.5 — Cierre: congelar la interfaz de producción y declarar el trabajo restante como incorporación de territorios, no ingeniería base.

## Límites inviolables

- No se ejecuta M01–M06 ni se abre una comunidad durante este cierre.
- Aragón y Castilla y León siguen siendo los únicos productos territoriales certificados.
- Extremadura continúa `EXPERIMENTAL_BLOCKED`.
- Una futura ejecución exige contrato admitido y autorización explícita; ninguna publicación, documentación o cambio de visor puede activarla.

## Reenganche

No quedan casillas de ingeniería base. Si esta sesión se interrumpe, el siguiente trabajo será una incorporación territorial concreta: contrato, fuentes, decisión explícita de ejecución y evidencia del run.
