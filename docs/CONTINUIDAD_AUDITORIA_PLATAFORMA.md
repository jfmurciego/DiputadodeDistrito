# Continuidad de la auditoría de plataforma DDD

**Versión:** 1.7.0
**Fecha de corte:** 2026-09-15
**Estado:** VIGENTE — R034–R039 cerrados; R040 bloqueado
**HEAD de reconciliación:** parte de `2b4c921834787dc4e56a3eab2ee1a381ef639526`
**Anterior:** `legacy/docs/CONTINUIDAD_AUDITORIA_PLATAFORMA_v1.6.1.md`
**Propósito:** permitir que otra sesión continúe desde el estado real sin repetir paquetes ya certificados ni ejecutar territorios sin autorización.

## 1. Veredicto vigente

La auditoría externa inicial demostró que la plataforma no podía proclamarse genérica. Desde entonces se cerraron R034–R039 y la auditoría crítica asociada sin convertir esa afirmación en un supuesto. La generalización completa sigue pendiente de R040.

## 2. Cerrado y no reabrir

- [x] R034 — admisión contractual antes de cálculo.
- [x] R035 — interfaz única y protegida por contrato.
- [x] R036 — gobierno de K, límites, excepciones y esquema.
- [x] R037 — políticas topológicas para aislados, desconexiones y archipiélagos.
- [x] R038 — operación limpia y retirada de rutas territoriales sustituidas.
- [x] R039 — contrato electoral común `ddd-election` 1.0.0 para M07–M08.
- [x] Paquete A C-05/C-09 — integridad y reconciliación M07.
- [x] Paquete B C-02/C-03/C-14 — separación de éxito técnico y publicabilidad.
- [x] C-04, C-06, C-07, C-08, C-10, C-12 y C-13 — cerrados y documentados.
- [x] C-01 — resultado auditado registrado como `FAIL_ROBUSTNESS`; no es un pendiente que deba repetirse automáticamente.

No repetir estos paquetes salvo que cambie materialmente su contrato o evidencia y exista una razón explícita documentada.

## 3. Único hito territorial abierto

- [ ] **R040 — Prueba ciega.** Permanece bloqueada hasta autorización explícita del usuario.

Cuando se autorice, la prueba debe demostrar si un territorio nuevo puede recorrer la misma cadena sin tocar `.github/workflows/`, `modulos/` ni `ddd_core`. No se permite introducir lógica específica para forzar un PASS. La Rioja y después Cantabria eran los casos previstos históricamente, pero su ejecución no se deduce de este documento: requiere orden expresa en la sesión activa.

## 4. Trabajo permitido mientras R040 esté bloqueado

- reconciliar documentación y evidencias;
- mejorar contratos o validadores sin ejecutar territorios;
- pruebas unitarias o sintéticas;
- mantenimiento de CI que no reactive cálculo pesado;
- revisión de deuda técnica sobre el motor común sin alterar productos certificados.

No lanzar nuevas comunidades, no recalcular Aragón/Castilla y León y no modificar Extremadura para hacerla aprobar.

## 5. Estado territorial que debe conservarse

- Aragón y Castilla y León conservan evidencia certificada histórica; los candidatos posteriores sólo son baseline si su `production_status.json` y auditorías independientes lo permiten.
- Extremadura permanece `EXPERIMENTAL_BLOCKED`.
- La existencia de un artefacto no equivale a promoción ni a publicabilidad.

## 6. Reenganche

Leer, en este orden:
1. `docs/CIERRE_INGENIERIA_PRODUCCION.md`.
2. `docs/SALIDAS_CHATGPT/PUNTO_REENGANCHE.md`.
3. `docs/REGISTRO_DE_CAMBIOS.md`.
4. `resultados/fase1/ESTADO_FACTUAL.json` para el cierre histórico de Fase 1.
5. Runs y commits posteriores al HEAD citado por el punto de reenganche.

La regla de seguridad prevalece: **R040 no se ejecuta por inferencia ni por una tarea de publicación; sólo por autorización explícita.**
