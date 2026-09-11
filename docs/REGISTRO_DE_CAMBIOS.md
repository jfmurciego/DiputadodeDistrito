# Registro de cambios DDD

Registro cronológico acumulativo. No se reescriben entradas antiguas.

## 2026-09-11 — Ronda R001 — Profesionalización y recuperación

**Objetivo:** convertir el código recuperado de Aragón en un procedimiento reproducible, auditable y ejecutable por su autor en GitHub.

**Decisiones:** terminología Procedimiento DDD → Módulos → Ejecuciones → Rondas; arquitectura M01–M08; SemVer + `legacy/`; GitHub como evidencia arbitral; contenedor, dependencias fijadas, checksums y validación dura; correcciones de cableado, ingesta y CUSEC; contigüidad validada sobre grafo.

**Baseline recuperado:** 1.463 secciones; 67 distritos; 1.364.621 habitantes; distribución poblacional todavía inválida.

## 2026-09-11 — Mantenimiento operativo — Workflow v2.7.1

Se preserva workflow v2.7.0 en `legacy/workflows/` y se publica v2.7.1. Se elimina la sustitución de comandos provocada por backticks alrededor de `PRODUCTOS.json` en un heredoc. Cambio exclusivamente operativo/documental.

## 2026-09-11 — R014 — M05 v7.3.0, escape de mínimo local

Run #7 dejó el distrito 56 de Zaragoza con 31.563 habitantes y M05 v7.2.0 aceptó 0 movimientos. La auditoría sobre artefactos exactos probó 642 relaciones candidatas dirigidas únicas: el bloqueo era un mínimo local del greedy, no ausencia de adyacencias.

Se preserva M05 v7.2.0 y se publica M05 v7.3.0. Se añade greedy determinista + recocido reproducible limitado a provincias afectadas, manteniendo en cada transición suelo/techo, provincia, contigüidad, `ddd_unit_id` y cierres urbanos. La salida restaura siempre la mejor solución canónica encontrada. Configuración Aragón pasa a v7.5.0, preservando v7.4.0.

La prueba diagnóstica local alcanzó `fuera_12=0`; quedó pendiente de GitHub.

## 2026-09-11 — Run #8 — Promoción de R014

GitHub Run `34592470470`, ejecutado sobre `d57dc9cd77af4fa09780794401381d9727d1c71b`, termina **SUCCESS**.

M05 v7.3.0 pasa de `fuera_12=1`, `max_rel_dev=0.549676430306` a **`fuera_12=0`, `max_rel_dev=0.119431695687`**. La validación final confirma 67 distritos, 1.463 secciones, 1.364.621 habitantes, reparto 11/7/49, sin cruces provinciales, sin desconexiones, sin infracciones municipales y sin violaciones de suelo/techo. R014 queda promocionado.

Run #8 también confirma workflow v2.7.1: publicación completa M01–M08 sin `PRODUCTOS.json: command not found`.

## 2026-09-11 — Reconciliación de gobernanza post-auditoría

Se preservan y actualizan README, Estado Maestro, Continuidad, Bitácora, Registro, política y contrato M05. `POLITICA_DE_VERSIONES.md` v1.1.0 sustituye la obligación obsoleta de actualizar `MEMORIA_DEL_PROYECTO.md` por los documentos canónicos actuales; prohíbe rutas `legacy` ficticias; distingue predecesor recuperado de deuda histórica; fija `main` como rama canónica y documenta ramas `infra/*` como históricas/no activas.

Se crea `docs/AUDITORIAS/DEUDA_HISTORICA_LEGACY_2026-09-11.md` para registrar las referencias heredadas no materializadas. Se reconoce explícitamente la ausencia de suite unitaria completa como deuda de ingeniería, manteniendo workflow + validaciones integradas como evidencia arbitral actual.
