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

**Normalización:** se archivan predecesores inmediatos reales y se incrementan como PATCH de gobernanza configuración, core, herramientas activas, M01–M08, `procedimiento.sh` y workflow territorial. La lógica funcional no cambia.

**Deuda histórica:** `docs/DEUDA_HISTORICA_LEGACY.md` conserva el inventario de antecedentes pre-R015 no recuperados. No se reconstruyen ficticiamente.

**Aceptación:** la puerta `Pruebas DDD — R015` queda verde tras normalizar cabeceras, `legacy`, regresión territorial y determinismo.

## 2026-09-11 — R016 — M05 v7.4.0, refinamiento post-factibilidad

Se abre una ronda funcional limitada a M05. La auditoría del código v7.3.x muestra que la búsqueda se interrumpe al primer `fuera_12=0` aunque el objetivo canónico sigue ordenando por máximo desvío y error cuadrático.

Se preserva M05 v7.3.1 en `legacy/modulo05/05_optimizar_distritos_v7.3.1.py` y se publica v7.4.0 como candidato. Greedy continúa mientras existan mejoras estrictas; el recocido conserva las provincias problemáticas iniciales y agota el presupuesto configurado, manteniendo siempre la mejor solución canónica. El reporte añade primera factibilidad y número de iteraciones posteriores.

Se añade `tests/test_r016_refinamiento.py`. La promoción exige CI verde y un nuevo run territorial con todos los PASS del baseline anterior.

## 2026-09-11 — Run #9 — Promoción de R016

GitHub Run `34599224954` termina **SUCCESS** sobre `f9ca44ff005043f630fce39334d34726d8bf55c5` y publica `gh-34599224954-1`.

M05 v7.4.0 alcanza la misma primera solución factible que Run #8 en la iteración 9.038:

`objective_first_feasible = [0, 0.0, 0, 0.119431695687, 0.182704485064]`.

Continúa 10.962 iteraciones adicionales y termina en:

`objective_final = [0, 0.0, 0, 0.099299365905, 0.161271162560]`.

El máximo desvío baja de 11,943 % a **9,930 %** y el error cuadrático global cae un 11,7 %. Se mantienen 67 distritos, 1.463 secciones, 1.364.621 habitantes, reparto 11/7/49, `fuera_12=0`, contigüidad, provincia, disciplina municipal y límites duros.

Solo cambian 12 distritos respecto de Run #8, todos en Zaragoza. El peor Zaragoza baja a +9,140 %; Huesca y Teruel quedan sin cambios. **R016 queda promocionado y Run #9 pasa a ser el nuevo baseline territorial.**

## 2026-09-11 — Simplificación de ramas

Se eliminan las cuatro ramas históricas `infra/fuentes-reproducibles*` y la rama temporal `r016/cleanup-temporal` después de comprobar que no contienen estado vigente exclusivo. El repositorio queda con una sola rama: **`main`**. Desde este punto, cualquier rama técnica temporal debe eliminarse tras su integración; la historia de versiones vive en `legacy/`, no en ramas acumuladas.
