# Cierre de ingeniería de producción DDD

**Versión:** 1.3.0
**Fecha de corte:** 2026-09-15
**Estado:** R034–R039 CERRADOS; R040 BLOQUEADO POR AUTORIZACIÓN
**Anterior:** `legacy/docs/CIERRE_INGENIERIA_PRODUCCION_v1.2.0.md`
**Propósito:** mantener una única lista canónica del cierre de ingeniería de producción sin reabrir hitos ya certificados.

## Criterio de salida

La infraestructura común previa a la prueba ciega está cerrada: admisión contractual, resolución neutral, línea única, gobierno de K y límites, topología nacional declarativa, operación limpia y producto electoral común. La plataforma no puede declararse genérica para cualquier territorio hasta superar R040.

## Lista de cierre

- [x] R034 — Puerta de admisión contractual antes de cálculo.
- [x] R035 — Resolver universal, línea única, prueba de fábrica y paquete de auditoría.
- [x] R036 — Gobierno del problema: K, límites, excepciones y esquema contractual.
- [x] R037 — Gobierno topológico: aislados, desconexiones y archipiélagos.
- [x] R038 — Operación limpia: interfaces obsoletas retiradas y línea territorial única.
- [x] R039 — Producto electoral: contrato `ddd-election` 1.0.0 y M07–M08 comunes.
- [ ] R040 — Prueba ciega de generalización sobre territorio no implantado.

## Auditoría crítica C-01–C-14

Los paquetes críticos anteriores a R038 están resueltos en la evidencia histórica y documental del repositorio. Entre ellos figuran la integridad electoral C-05/C-09, publicabilidad C-02/C-03/C-14, sesgo de K C-04, contrato M06 C-10, caso adversarial C-07, verificación independiente C-06, motor M04 C-08, comunidades de interés C-13 y nombres C-12. C-01 quedó registrado como `FAIL_ROBUSTNESS` para el ensayo auditado; ese resultado no autoriza a promover ni a ejecutar un lote de 50 sin orden expresa.

## Único hito territorial abierto

R040 debe ser una prueba falsable. Requiere autorización explícita del usuario y, cuando se autorice, debe ejecutar primero un territorio nuevo sin modificar `.github/workflows/`, `modulos/` ni `ddd_core`. Un fallo es evidencia válida; no se parchea código específico del territorio para convertirlo en PASS.

Hasta esa autorización:

- no se abre ninguna comunidad nueva;
- no se recalculan M01–M06 de Aragón o Castilla y León;
- Extremadura continúa `EXPERIMENTAL_BLOCKED`;
- no se puede afirmar que la plataforma procesa «cualquier territorio»;
- publicación y visor son líneas separadas y no pueden disparar cálculo territorial.

## Reenganche

Continuar por `docs/CONTINUIDAD_AUDITORIA_PLATAFORMA.md` y `docs/SALIDAS_CHATGPT/PUNTO_REENGANCHE.md`. Si no existe autorización explícita para R040, el trabajo permitido es de auditoría, documentación, contratos, pruebas sintéticas o mantenimiento que no ejecute territorios.
