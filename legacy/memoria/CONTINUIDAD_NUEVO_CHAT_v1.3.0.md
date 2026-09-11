# Continuidad del proyecto en un nuevo chat

**Versión:** 1.3.0  
**Fecha de corte:** 2026-09-11  
**Anterior:** `legacy/memoria/CONTINUIDAD_NUEVO_CHAT_v1.2.0.md`

## Fuente de verdad

El repositorio `jfmurciego/DiputadodeDistrito` manda sobre cualquier recuerdo del chat. Leer en este orden: `README.md`, `docs/ESTADO_MAESTRO_PROYECTO.md`, este documento, `docs/BITACORA.md`, arquitectura, contratos M01–M08, última ronda/ejecución, configuración, workflow y código afectado. Los antiguos `docs/MEMORIA*` están retirados.

## Arquitectura y reglas

M01 base territorial+población → M02 adyacencias → M03 grafo → M04 construcción inicial → M05 optimización → M06 consolidación → M07 agregación electoral → M08 producto final.

Aragón: 67 distritos; 1.463 secciones; 1.364.621 habitantes; provincia 11/7/49; contigüidad estricta; suelo 0,80×target; techo 1,75×target; objetivo ±12 %; municipio pequeño indivisible; municipio sobredimensionado particionado de forma conexa con solo residual mezclable; resultados electorales fuera del algoritmo geométrico.

## Última referencia aceptada — Run #8

**GitHub Run #8 `34592470470` — SUCCESS**, commit ejecutado `d57dc9cd77af4fa09780794401381d9727d1c71b`, modo iterativo.

- M01–M03: caché reutilizada.
- M04 v7.3.0: 67 distritos, 11/7/49, `hard=0`.
- M05 v7.3.0: `hard=0`, **`fuera_12=0`**, `max_rel_dev=0.119431695687`.
- M05: greedy=0, anneal=1.030, unidades finalmente cambiadas=75, iteraciones de recocido=9.038.
- Validación final: provincia PASS, disciplina municipal PASS, contigüidad PASS, población PASS, conservación exacta.
- M01–M08 y artefactos publicados.
- Workflow v2.7.1 verificado: no reaparece `PRODUCTOS.json: command not found`.

R014 queda **promocionado/validado**. Run #7 permanece como antecedente causal, no como referencia vigente.

## Ingeniería y auditoría

Toda versión nueva preserva predecesor en `legacy/` cuando éste existe materialmente y documenta versión, cambio y motivo. Si una versión histórica de la recuperación no está disponible, se registra como `PREDECESOR HISTÓRICO NO RECUPERADO`; nunca se inventa una ruta.

La política vigente es `docs/POLITICA_DE_VERSIONES.md` v1.1.0. Los huecos heredados están en `docs/AUDITORIAS/DEUDA_HISTORICA_LEGACY_2026-09-11.md`.

Un resultado local/IA es diagnóstico. La aceptación exige GitHub Actions reproducible y validaciones. Los outputs ligeros completos viven en `resultados/ejecuciones/<RUN_ID>/Mxx/`; geometrías pesadas, en artefactos Actions con `PRODUCTOS.json`.

`main` es la rama canónica. Las ramas `infra/fuentes-reproducibles*` son históricas/no activas mientras no se reactiven expresamente.

## Siguiente trabajo seguro

No modificar M04/M05 sin abrir una nueva ronda y preservar los PASS de Run #8. Prioridad de ingeniería: introducir pruebas unitarias de invariantes/función objetivo, normalizar cabeceras auxiliares y resolver cuando sea posible las referencias legacy históricas verificables.

**Siguiente paso:** auditar y diseñar la primera suite de pruebas automáticas sin cambiar el comportamiento territorial aceptado.
