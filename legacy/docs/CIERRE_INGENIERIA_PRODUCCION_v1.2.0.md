# Cierre de ingeniería de producción DDD

**Versión:** 1.2.0
**Inicio:** 2026-09-13
**Estado:** INTERFAZ CERRADA; PLATAFORMA NACIONAL EN AUDITORÍA
**Anterior:** `legacy/docs/CIERRE_INGENIERIA_PRODUCCION_v1.1.0.md`
**Propósito:** separar el cierre certificado de la interfaz R034–R035 del trabajo aún necesario para afirmar que la plataforma procesa cualquier territorio.

## Criterio de salida

Un territorio podrá entrar mediante un contrato completo, ser rechazado antes del cálculo si falla, recorrer una única cadena común cuando exista una autorización explícita y dejar una evidencia auditable que otro equipo pueda revisar sin depender de este chat.

## Lista de cierre

- [x] R034 — Puerta de admisión: contrato, fuentes, restricciones y cadena M01–M06 verificables antes de cálculo.
- [x] R035.1 — Resolver universal: eliminar las selecciones Aragón/Castilla y León codificadas de la ejecución G10.
- [x] R035.2 — Línea única: workflow por contrato con modos de admitir, verificar y ejecutar bajo autorización explícita.
- [x] R035.3 — Prueba de fábrica: demostrar contrato válido, rechazos tempranos y ausencia de cálculo en los modos de control.
- [x] R035.4 — Paquete de auditoría: evidencia de CI, trazabilidad, versión, legacy y punto de reenganche.
- [x] R035.5 — Cierre de la interfaz común: contrato, resolución y workflow neutral.
- [ ] R036 — Gobierno del problema: política auditable de K, contrato general de límites y justificación obligatoria de excepciones.
- [ ] R037 — Topología nacional: políticas declarativas para secciones aisladas, provincias desconectadas y archipiélagos.
- [ ] R038 — Operación limpia: archivar workflows territoriales obsoletos y separar auditores experimentales del procedimiento vigente.
- [ ] R039 — Producto electoral: contrato, adquisición/entrada y normalización común M07–M08.
- [ ] R040 — Prueba ciega: producir un territorio no implantado sin modificar workflows, módulos ni `ddd_core`.

## Límites inviolables

- No se ejecuta M01–M06 ni se abre una comunidad durante este cierre.
- Aragón y Castilla y León siguen siendo los únicos productos territoriales certificados.
- Extremadura continúa `EXPERIMENTAL_BLOCKED`.
- Una futura ejecución exige contrato admitido y autorización explícita; ninguna publicación, documentación o cambio de visor puede activarla.

## Reenganche

Continuar por `docs/CONTINUIDAD_AUDITORIA_PLATAFORMA.md`. R035 no demuestra todavía la producción de un territorio nuevo: demuestra que ya existe una interfaz común y protegida. La prueba territorial permanece congelada hasta orden expresa.
