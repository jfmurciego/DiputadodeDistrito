# Continuidad del proyecto en un nuevo chat

**Versión:** 1.5.0
**Fecha de corte:** 2026-09-11
**Anterior:** `legacy/memoria/CONTINUIDAD_NUEVO_CHAT_v1.4.0.md`

## Fuente de verdad

El repositorio `jfmurciego/DiputadodeDistrito` manda sobre cualquier recuerdo del chat. Leer: `README.md`, `docs/ESTADO_MAESTRO_PROYECTO.md`, este documento, `docs/BITACORA.md`, arquitectura, contratos M01–M08, última ronda/ejecución, configuración, workflows, tests y código afectado. Los antiguos `docs/MEMORIA*` están retirados.

## Arquitectura y reglas

M01 base territorial+población → M02 adyacencias → M03 grafo → M04 construcción inicial → M05 optimización → M06 consolidación → M07 agregación electoral → M08 producto final.

Aragón: 67 distritos; 1.463 secciones; 1.364.621 habitantes; provincia 11/7/49; contigüidad estricta; suelo 0,80×target; techo 1,75×target; objetivo ±12 %; municipio pequeño indivisible; municipio sobredimensionado particionado de forma conexa con solo residual mezclable; resultados electorales fuera del algoritmo geométrico.

## Referencia territorial — Run #8 / R014

GitHub Run #8 **`34592470470` — SUCCESS** sobre `d57dc9cd77af4fa09780794401381d9727d1c71b`.

M05 v7.3.0 cerró el mínimo local de Run #7: `hard=0`, `fuera_12=0`, `max_rel_dev=0.119431695687`. La validación final confirmó provincia, disciplina municipal, contigüidad, límites poblacionales y conservación exacta. R014 está cerrado.

## R015 — ingeniería cerrada

R015 no cambia lógica territorial. Normaliza cabeceras y predecesores inmediatos, preserva copias reales en `legacy/`, inventaría los huecos históricos no recuperados y añade `tests/test_r015_invariantes.py` + `.github/workflows/pruebas-ddd.yml`.

**Run de aceptación de pruebas R015: `34594827070` — SUCCESS.** Pasaron la auditoría de cabeceras/legacy y la regresión territorial/determinismo después de retirar el migrador temporal.

Versiones activas relevantes tras R015: configuración v7.5.1; M04 v7.3.1; M05 v7.3.1; validador v1.3.1; procedimiento v2.1.1; workflow territorial v2.7.2. Son PATCH de gobernanza respecto de la lógica validada en Run #8.

## R016 — ronda activa, candidato M05 v7.4.0

Objetivo: alinear la ejecución de M05 con su objetivo canónico. v7.3.x detenía el recocido al primer `fuera_12=0`; v7.4.0 continúa dentro de la provincia inicialmente problemática para intentar reducir después `max_rel_dev` y error cuadrático, sin relajar restricciones.

El reporte registra `first_feasible_iteration`, `objective_first_feasible` y `post_feasible_iterations`. La prueba R016 exige que exista refinamiento posterior y que el objetivo final no sea peor que el primer estado factible.

**Estado:** candidato; Run #8 sigue siendo la referencia territorial hasta un nuevo run completo/iterativo aceptado.

## Ingeniería y auditoría

Toda sustitución versionada conserva primero el predecesor inmediato en `legacy/`. La copia histórica se conserva literalmente, incluso si tiene whitespace o defectos cosméticos. Si una versión anterior no fue recuperada, se registra en `docs/DEUDA_HISTORICA_LEGACY.md`; nunca se fabrica.

La política vigente es `docs/POLITICA_DE_VERSIONES.md` v1.2.0. Los cambios funcionales posteriores deben superar la suite R015 y, además, un nuevo run territorial antes de promoción.

Un resultado local/IA es diagnóstico. Los outputs ligeros completos viven en `resultados/ejecuciones/<RUN_ID>/Mxx/`; geometrías pesadas, en artefactos Actions con `PRODUCTOS.json`.

`main` es la rama canónica. `infra/fuentes-reproducibles*` son ramas históricas/no activas.

## Orden para continuar

1. Confirmar HEAD de `main` y último run de `Pruebas DDD — R015`.
2. Leer la ronda activa y el contrato del módulo que se pretenda cambiar.
3. Si el cambio es funcional, preservar predecesor, incrementar versión y mantener todas las invariantes de Run #8.
4. Exigir CI R015 verde.
5. Ejecutar el procedimiento territorial y solo entonces promocionar un nuevo baseline.

**Siguiente paso:** validar M05 v7.4.0 con `Pruebas DDD — R015`; si queda verde, ejecutar `Procedimiento DDD — Aragón` en modo iterativo y comparar el objetivo final con Run #8.
