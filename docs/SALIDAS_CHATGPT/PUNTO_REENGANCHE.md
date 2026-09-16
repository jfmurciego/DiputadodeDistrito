# Punto de reenganche DDD

Versión: 1.36.0
Fecha: 2026-09-16
Estado: auditoría crítica y R034–R039 reconciliados; R040 es el único hito territorial abierto.
Anterior: versión 1.35.0 en historial Git

## Fuente operativa

- Lista canónica de cierre: `docs/CIERRE_INGENIERIA_PRODUCCION.md`.
- Continuidad de auditoría: `docs/CONTINUIDAD_AUDITORIA_PLATAFORMA.md`.
- Estado de máquina: `orchestracion/estado_operativo_g10.json`.
- Estado legible: `docs/SALIDAS_CHATGPT/ESTADO_OPERATIVO_G10.md`.
- Interfaz humana principal: `.github/workflows/ejecucion-generacion-distritos.yml`.
- Router institucional reutilizable: `.github/workflows/_reutilizable-operacion-territorial.yml`.
- Línea contractual reutilizable: `.github/workflows/producir-territorio-por-contrato.yml`.

## Estado de ingeniería

R034, R035, R036, R037, R038 y R039 están cerrados. La auditoría crítica C-01–C-14 ya no debe recorrerse como backlog lineal: sus paquetes fueron resueltos y la evidencia queda en `docs/AUDITORIA_*`, `docs/SALIDAS_CHATGPT/HITOS/`, `resultados/fase1/` y `docs/REGISTRO_DE_CAMBIOS.md`.

C-01 conserva el resultado auditado `FAIL_ROBUSTNESS`; eso no invalida los candidatos técnicos válidos, pero impide tratar la robustez como aprobada o escalar automáticamente a un lote mayor.

## Estado territorial

- Aragón: conservar productos y evidencia certificados; un run posterior no sustituye el baseline por mera existencia.
- Castilla y León: conservar evidencia certificada y controles de publicación vigentes.
- Extremadura: `EXPERIMENTAL_BLOCKED`; no promover ni modificar para forzar aprobación.

## Operación actual

La interfaz principal expone M01–M08 y las operaciones institucionales mediante una sola ruta resuelta. Los inputs humanos son `choice` o `boolean`; los run IDs de reutilización se resuelven internamente. Para tramos posteriores a M01 se busca automáticamente el último checkpoint compatible y para republicación del piloto se busca automáticamente un Aragón-10 completo y vigente.

El visor no expone ya un `workflow_dispatch` independiente: se invoca desde la interfaz única mediante el reusable `desplegar-visor-publico.yml`.

Los cambios de publicación o visor no autorizan cálculo territorial.

## Siguiente hito

**R040 — prueba ciega de generalización** es el único hito territorial abierto. Está congelado hasta autorización explícita del usuario. No interpretar tareas genéricas de mantenimiento, auditoría o publicación como autorización para ejecutarlo.

Mientras R040 siga bloqueado, sólo avanzar en deuda no territorial: documentación, contratos, validadores, pruebas sintéticas, CI o refactorizaciones que no ejecuten comunidades ni recalculen productos certificados.

## Regla de falsabilidad de R040

Cuando se autorice, el territorio nuevo debe entrar sin cambios en `.github/workflows/`, `modulos/` ni `ddd_core`. Un fallo se registra como hallazgo; no se introduce un parche territorial específico para convertirlo en PASS.
