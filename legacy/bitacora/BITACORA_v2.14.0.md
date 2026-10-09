# Bitácora de progreso

**Versión:** 2.14.0  
**Fecha:** 2026-09-11  
**Anterior:** `legacy/bitacora/BITACORA_v2.13.0.md`

## R001–R011 — Base reproducible y outputs auditables
Se recupera y profesionaliza el procedimiento; se formalizan M01–M08, caché territorial, fuentes congeladas, validación, manifiestos, ejecución GitHub y publicación completa de outputs por módulo.

## Run #5 — 34584775443
R011 demuestra auditabilidad, pero la auditoría posterior descubre una validación territorial incompleta: 13 distritos interprovinciales y 30 municipios fragmentados. No es referencia territorial.

## R012 — Provincia dura y disciplina municipal
Reglas estructurales vigentes: 67 distritos; Huesca 11 / Teruel 7 / Zaragoza 49; provincia infranqueable; municipio íntegro mientras quepa bajo techo; municipio sobredimensionado particionado internamente en bloques conexos; distritos urbanos completos exclusivamente municipales y solo residual mezclable; contigüidad estricta; suelo 0,80 y techo 1,75; objetivo fino ±12%.

Validación v1.3.0. M04 v7.3.0.

## Run #6 — 34587157452
FAIL detectado por M05: distrito 52 desconectado. Auditoría del producto M04 demuestra que M04 ya lo entregaba con 15 componentes. Causa raíz: el particionador preservaba cada bloque extraído pero no la conectividad del residuo municipal.

Expediente: `docs/EJECUCIONES/GITHUB_RUN_0006_2026-09-11.md`.

## M04 v7.3.0
Se preserva v7.2.1. Se introduce partición municipal balanceada y conexa, ensamblaje rural conexo, eliminación de fallback no adyacente y autovalidación dentro de M04.

## Run #7 — 34588834266
SUCCESS. Primera evidencia GitHub simultánea de las reglas estructurales R012: 67 distritos, reparto 11/7/49, provincias PASS, disciplina municipal PASS, contigüidad PASS y límites duros de población PASS. M04 deja un único distrito fuera de ±12 %: distrito 56 de Zaragoza, 31.563 habitantes. M05 v7.2.0 acepta 0 movimientos y no mejora la solución.

Expediente: `docs/EJECUCIONES/GITHUB_RUN_0007_2026-09-11.md`.

## R013 documental — Continuidad y puerta de entrada
Se revisa la documentación para impedir pérdida de contexto entre conversaciones. `README.md`, Estado Maestro, bitácora y `docs/CONTINUIDAD_NUEVO_CHAT.md` constituyen la entrada canónica; los antiguos `docs/MEMORIA*` quedan retirados como fuentes de estado.

## Mantenimiento workflow v2.7.1
Se corrige el error `PRODUCTOS.json: command not found` de Run #7 eliminando los backticks interpretados por shell dentro del heredoc del README de resultados. Workflow v2.7.0 preservado en `legacy/workflows/`. Es un cambio operativo sin efecto territorial.

## R014 — Escape de mínimo local en M05
Auditoría formal: `docs/AUDITORIAS/AUDITORIA_M05_RUN7_2026-09-11.md`.

La auditoría reproduce M05 sobre los artefactos exactos del Run #7 y demuestra que el problema no es ausencia de candidatos. Existen 642 relaciones dirigidas únicas inicialmente; el bloqueo aparece porque los movimientos que permiten descargar el distrito 56 preservando contigüidad crean temporalmente un segundo distrito fuera de ±12 %, y el greedy lexicográfico de v7.2.0 los rechaza.

Se preserva M05 v7.2.0 y se publica **M05 v7.3.0 — Escape determinista de mínimos locales**. Mantiene el objetivo canónico para seleccionar la mejor solución, pero separa la exploración: primero greedy determinista; después, solo si queda desequilibrio fino, recocido simulado reproducible dentro de la provincia afectada. Ninguna transición puede violar suelo/techo, provincia, contigüidad, atomicidad `ddd_unit_id` ni cierre urbano.

La configuración pasa a **v7.5.0**, con parámetros explícitos de greedy, recocido, energía, churn y temperaturas. La clave de preparación territorial solo depende de M01–M03 y sus fuentes, por lo que estos cambios de M05 no invalidan la caché territorial.

Prueba diagnóstica sobre M03/M04 exactos del Run #7: 67 distritos, `hard=0`, `fuera_12=0`, máximo desvío ≈11,943 %, mínimo 18.345, máximo 22.800, 0 desconectados, 0 cruces provinciales y 0 infracciones municipales. Este resultado justifica el candidato pero **no sustituye una ejecución GitHub**.

R014 está pendiente de ratificación por un nuevo workflow desde `main`.

## Reglas permanentes
Un informe nunca sustituye al producto. Una ejecución de IA no sustituye a GitHub reproducible. Corregir el primer módulo que rompe el contrato, no parchear módulos posteriores. Toda versión nueva preserva legacy, documenta el cambio y solo se promociona si mantiene las restricciones ya aceptadas.
