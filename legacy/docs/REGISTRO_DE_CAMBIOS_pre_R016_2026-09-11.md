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

Se preserva M05 v7.2.0 y se publica M05 v7.3.0. Se añade greedy determinista + recocido reproducible limitado a provincias afectadas, manteniendo en cada transición suelo/techo, provincia, contigüidad, `ddd_unit_id` y cierres urbanos. Configuración Aragón pasa a v7.5.0.

## 2026-09-11 — Run #8 — Promoción de R014

GitHub Run `34592470470` termina SUCCESS. M05 pasa de `fuera_12=1`, `max_rel_dev=0.549676430306` a **`fuera_12=0`, `max_rel_dev=0.119431695687`**. Validación final: 67 distritos, 1.463 secciones, 1.364.621 habitantes, 11/7/49, sin cruces provinciales, desconexiones, infracciones municipales ni violaciones de suelo/techo. R014 queda promocionado.

## 2026-09-11 — Reconciliación de gobernanza post-auditoría

Se alinean documentos canónicos con R014, se retiran `MEMORIA*` como fuentes vigentes, se fija `main` como rama canónica y se documenta la deuda histórica de `legacy/` sin inventar antecedentes.

## 2026-09-11 — R015 — Pruebas automáticas y gobernanza verificable

**Objetivo:** cerrar la deuda de pruebas y de trazabilidad sin cambiar el algoritmo territorial aceptado.

**Pruebas:** se añade `tests/test_r015_invariantes.py` y `.github/workflows/pruebas-ddd.yml`. La regresión comprueba las invariantes R012/R014 contra Run #8 y un fixture sintético ejecuta M05 dos veces con la misma semilla para exigir determinismo y atomicidad de unidad.

**Normalización:** se archivan predecesores inmediatos reales y se incrementan como PATCH de gobernanza configuración 7.5.0→7.5.1, core 1.3.0→1.3.1, herramientas activas, M01–M08, `procedimiento.sh` 2.1.0→2.1.1 y workflow territorial 2.7.1→2.7.2. La lógica funcional no cambia. Inventario: `docs/R015_COMPONENTES_NORMALIZADOS.tsv`.

**Deuda histórica:** `docs/DEUDA_HISTORICA_LEGACY.md` conserva el inventario de antecedentes pre-R015 no recuperados. No se reconstruyen ficticiamente.

**Incidencias de migración:** un primer lint detectó whitespace existente dentro de una copia histórica; se decidió conservar el antecedente byte a byte y excluir `legacy/**` del lint. GitHub Actions tampoco podía modificar workflows por su permiso restringido; se separó esa operación y se realizó por el canal autorizado. Los migradores temporales quedaron archivados y fueron retirados del árbol activo.

**Aceptación inicial:** `Pruebas DDD — R015`, Run `34594827070`, termina SUCCESS después de retirar la migración temporal. La auditoría de cabeceras/legacy y la regresión territorial/determinismo pasan. Ejecuciones posteriores, incluida `34595195694`, permanecen verdes.

## 2026-09-11 — R015 — cierre final de trazabilidad documental

Se detecta que Estado Maestro, Continuidad, Bitácora y Política declaraban predecesores `legacy/` que todavía no estaban materializados. Se recuperan las versiones exactas desde el commit anterior y se escriben en las rutas declaradas, sin reeditarlas. También se preservan el README v3.2.0 y las instantáneas anteriores de los documentos que se modifican en este cierre.

La suite R015 se amplía para que la CI valide también las referencias `Anterior` de los documentos canónicos versionados. De este modo, una ruta documental activa hacia un `legacy/` inexistente pasa a ser un fallo automático.

`docs/MODULOS/M05_OPTIMIZACION.md` se formaliza como contrato documental versionado y distingue el ejecutable activo M05 v7.3.1, cuyo cambio R015 es solo de gobernanza, de la lógica funcional v7.3.0 validada territorialmente por Run #8. No se modifica código algorítmico, configuración territorial ni solución de distritos.

El cierre se considera completo únicamente si el nuevo HEAD consolidado vuelve a superar `Pruebas DDD — R015`.
