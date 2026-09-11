# Estado maestro del proyecto — Diputado de Distrito

**Versión:** 1.9.0  
**Fecha de corte:** 2026-09-11  
**Anterior:** `legacy/memoria/ESTADO_MAESTRO_PROYECTO_v1.8.0.md`

## 1. Fuente de verdad y arranque
Leer `README.md`, este documento, `docs/CONTINUIDAD_NUEVO_CHAT.md`, `docs/BITACORA.md`, arquitectura, contratos M01–M08, última ronda/ejecución, configuración, workflow y código afectado. Los dos archivos antiguos `MEMORIA*` están retirados y no son fuentes de estado.

## 2. Reglas duras Aragón — R012
1. 67 distritos exactos.
2. Provincia como frontera dura: Huesca 11 / Teruel 7 / Zaragoza 49.
3. Contigüidad estricta por grafo M03.
4. Conservación de 1.463 secciones y 1.364.621 habitantes.
5. Suelo 0,80×target; techo 1,75×target.
6. Objetivo fino ±12%.
7. Municipio que cabe bajo techo: indivisible.
8. Municipio sobredimensionado: partición interna conexa; distritos completos exclusivamente municipales y solo residual mezclable con municipios menores adyacentes de la misma provincia.
9. Resultados electorales nunca condicionan geometría.
10. Determinismo, CUSEC único/no nulo y una configuración canónica.

## 3. Implementación vigente
Configuración `configuracion/aragon_2025.yaml` **v7.5.0**. Validación `herramientas/validar_ejecucion.py` v1.3.0. Workflow `.github/workflows/procedimiento-ddd.yml` **v2.7.1**.

M04 **v7.3.0**: construcción provincia-first, partición municipal balanceada/conexa, ensamblaje rural conexo, sin fallback no adyacente y autovalidación de cardinalidad, cuotas, provincia, contigüidad y suelo/techo.

M05 **v7.3.0**: optimización por unidades territoriales protegidas con dos fases. Primero greedy determinista de mejor mejora; si persiste desequilibrio ±12 %, recocido simulado reproducible limitado a la provincia afectada. La exploración nunca puede violar suelo/techo, provincia, contigüidad, atomicidad `ddd_unit_id` ni cierre urbano. La salida siempre restaura la mejor solución encontrada según el objetivo canónico lexicográfico.

La clave de caché M01–M03 es selectiva: no depende de M04/M05 ni de sus parámetros. Por tanto la nueva configuración M05 no obliga a reconstruir la preparación territorial.

## 4. Ejecuciones relevantes
Run #5 `34584775443`: R011 demuestra outputs auditables, pero no es referencia territorial por cruces provinciales y fragmentación municipal detectados después.

Run #6 `34587157452`: FAIL. M04 produjo distrito 52 con 15 componentes; M05 lo detectó. Causa corregida en M04 v7.3.0.

### Run #7 — `34588834266` — SUCCESS — última referencia GitHub
Commit ejecutado: `98a2e68907273fcd382a241687e645e8615bb47a`. Modo `iterativo`; M01–M03 restaurados desde caché.

Resultados:
- M04 v7.3.0: `hard=0`, K=67, cuotas 11/7/49, min=18.345, max=31.563.
- M05 v7.2.0: `hard=0`, `fuera_12=1`, `max_rel_dev=0.5497`, `movimientos_unidad=0`.
- M06–M08 completados.
- Validación final: **67 distritos; provincias PASS; disciplina municipal PASS; contigüidad PASS; población dentro de [16.294,0, 35.643,1]**.
- Outputs M01–M08 materializados y publicados.

Run #7 demuestra las reglas duras R012, pero todavía no es solución final de equilibrio porque queda 1 distrito fuera de ±12 %.

## 5. Mantenimiento operativo cerrado
El error `PRODUCTOS.json: command not found` de Run #7 estaba causado por backticks Markdown dentro de un heredoc no protegido. Se corrigió en workflow v2.7.1, preservando v2.7.0 en `legacy/workflows/`. Este cambio no toca el algoritmo territorial.

## 6. R014 — causa raíz y candidato M05 v7.3.0
Auditoría: `docs/AUDITORIAS/AUDITORIA_M05_RUN7_2026-09-11.md`. Diseño: `docs/RONDAS/R014_2026-09-11_escape_minimo_local_m05.md`.

El distrito problemático del Run #7 es el **56 de Zaragoza, 31.563 habitantes**. La auditoría demuestra que M05 v7.2.0 sí tenía candidatos: 642 relaciones dirigidas únicas inicialmente. El bloqueo es un mínimo local. Los movimientos que descargan el distrito 56 manteniendo contigüidad empeoran temporalmente de 1 a 2 el número de distritos fuera de ±12 %, por lo que el greedy estrictamente monótono los rechaza; movimientos menores que mejorarían inmediatamente la población rompen la contigüidad y deben seguir rechazándose.

M05 v7.3.0 separa selección y exploración: la función canónica sigue decidiendo qué solución es mejor, pero el recocido puede atravesar estados intermedios peores dentro del espacio duro válido.

Prueba diagnóstica contra los artefactos exactos M03/M04 del Run #7:
- K=67;
- 1.463 secciones y 1.364.621 habitantes conservados;
- cuotas 11/7/49;
- `hard=0`;
- `fuera_12=0`;
- `max_rel_dev≈0,11943`;
- min=18.345; max=22.800;
- 0 desconectados;
- 0 cruces provinciales;
- 0 violaciones municipales según la validación R012.

Este resultado es **diagnóstico, no referencia arbitral**. R014 sigue candidato hasta ser reproducido por GitHub Actions sobre el `main` actual.

## 7. Outputs y auditabilidad
R011 sigue siendo obligatoria: cada módulo expone su producto completo. Los ligeros se publican en `resultados/ejecuciones/<RUN_ID>/Mxx/`; los GeoJSON pesados quedan en artefactos Actions y `PRODUCTOS.json` los identifica por hash/tamaño/ruta.

M06 debe seguir evolucionando como ficha territorial completa del distrito, no como mero resumen poblacional.

## 8. Siguiente acción exacta
1. Lanzar una nueva ejecución `Procedimiento DDD — Aragón` en modo `iterativo` desde el `main` actual.
2. Verificar que M01–M03 reutilizan la caché territorial.
3. Comprobar M05 v7.3.0: `hard=0`, `fuera_12=0`, métricas y número de unidades finalmente modificadas.
4. Confirmar validación completa: provincia PASS, disciplina municipal PASS, contigüidad PASS, conservación exacta y outputs M01–M08.
5. Si el run es SUCCESS, crear su expediente y promocionar R014 actualizando README, bitácora, Estado Maestro y continuidad. Si falla, diagnosticar el primer módulo que rompa contrato sin relajar R012.
