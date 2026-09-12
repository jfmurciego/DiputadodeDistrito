# Registro de cambios DDD

Registro cronológico acumulativo. No se reescriben entradas antiguas.

## 2026-09-11 — R001 — Profesionalización y recuperación
Se convierte el código recuperado de Aragón en procedimiento reproducible y auditable: M01–M08, SemVer + `legacy/`, GitHub como evidencia, contenedor, checksums, validación dura y contigüidad por grafo.

## 2026-09-11 — Workflow v2.7.1
Se preserva v2.7.0 y se corrige el heredoc de `PRODUCTOS.json`.

## 2026-09-11 — R014 — M05 v7.3.0
La auditoría de Run #7 demuestra un mínimo local del greedy. Se añade greedy determinista + recocido reproducible sin relajar provincia, contigüidad, unidades municipales ni suelo/techo.

## 2026-09-11 — Run #8 — Promoción R014
Run `34592470470` SUCCESS: `fuera_12=0`, máximo desvío 11,943 %, todas las invariantes R012 PASS.

## 2026-09-11 — R015 — Pruebas y gobernanza
Se añade suite de regresión/determinismo, auditoría de cabeceras y predecesores `legacy/`, y se normaliza la gobernanza. La CI pasa a ser puerta obligatoria.

## 2026-09-11 — R016 — M05 v7.4.0
Se elimina la parada al primer `fuera_12=0`; M05 continúa refinando máximo desvío y error cuadrático hasta agotar el presupuesto.

## 2026-09-11 — Run #9 — Promoción R016
Run `34599224954` SUCCESS. Primera factibilidad en iteración 9.038; resultado final tras 20.000 iteraciones: máximo desvío 9,930 %, error cuadrático 0,161271162560. Se mantienen 67 distritos, 1.463 secciones, 1.364.621 habitantes, reparto 11/7/49 y todas las restricciones PASS. Run #9 pasa a baseline.

## 2026-09-11 — Simplificación de ramas
Se eliminan cuatro ramas históricas `infra/*` y la rama temporal R016. Queda únicamente `main`.

## 2026-09-11 — R018 — Arquitectura multi-territorio

**Objetivo:** preparar el producto DDD para 17 comunidades, España completa y posterior adaptación internacional sin forks del motor.

**Decisiones arquitectónicas:**
- un repositorio;
- una rama permanente `main`;
- motor común en `ddd_core/`, `modulos/`, `herramientas/`;
- paquetes territoriales en `territorios/<id>/`;
- Aragón pasa a implantación de referencia explícita;
- Castilla y León se crea como segunda implantación y prueba de generalización;
- Extremadura será la siguiente prueba de reutilización.

**Procedimiento:** `procedimiento.sh` 2.1.1 → 2.2.0. Se elimina `aragon_2025` duro del directorio de caché y se deriva `run_name` del YAML. No se cambia algoritmo territorial.

**Documentación nueva:** `ARQUITECTURA_MULTI_TERRITORIO.md`, `CONTRATO_TERRITORIO.md`, `CONTINUIDAD_CASTILLA_Y_LEON.md`, `territorios/README.md`, paquete Aragón y scaffold Castilla y León.

**Compatibilidad:** las rutas raíz históricas de Aragón continúan temporalmente para que el workflow validado siga reproduciendo Run #9. La estructura canónica nueva es `territorios/`.

**Limpieza:** documentos retirados/redundantes salen del árbol activo y se preservan en `legacy/docs/retirados_r018/` cuando aportan arqueología. No se elimina código histórico.

**Próximos frentes:** Aragón conserva R017 pendiente de calidad territorial. Castilla y León debe comenzar por fuentes → contrato → workflow genérico → M01 → M02/M03. No abrir M04 antes de aceptar el grafo base.


## 2026-09-12 — R021 — Auditoría y sincronización
Se audita el estado real multi-territorio y se crea `docs/SALIDAS_CHATGPT/` como continuidad ligera.

## 2026-09-12 — R022 — Observabilidad y expansión nacional
M03 v7.2.0 separa auditoría de enforcement. CAT-02 certifica Llívia; CAT-03 cierra Cataluña hasta M03. Run `34688010656` ejecuta Madrid y otros 13 territorios con un workflow reutilizable y matriz paralela.

## 2026-09-12 — R023 — Diagnóstico continental
Se lanza auditoría geométrica paralela para los siete territorios continentales con discontinuidades observadas. No se añaden pasarelas automáticas.


## 2026-09-12 — R024 — G10 semántico y evidencia durable

Se introduce el catálogo semántico v2: las tareas G10 se expresan por capa y fase legible; M01–M08 se conservan como identidad histórica compatible. Se añade admisión por huella y el índice durable `orchestracion/estado_tareas.json`.

El lote inicial `fase1-cierre-evidencia-v1` verifica evidencia ya existente de Aragón, Castilla y León y Extremadura sin recalcular M01–M08. Extremadura sigue experimental bloqueada. Un producto histórico sólo se convierte en `REUSED` después de una verificación y una huella materializada; la mera presencia de un archivo no autoriza reutilización.

## 2026-09-12 — R024.1 — Corrección de transporte de evidencia G10

El primer lote G10 detectó que la matriz entregaba la lista de artefactos como un único argumento literal. Se corrige la serialización de la lista en el workflow v1.0.1. No se modifican fuentes, contratos ni resultados territoriales; el relanzamiento solo verifica evidencia canónica ya existente.

## 2026-09-12 — R025 — Checkpoints semánticos G10

Se incorpora un adaptador de reenganche que selecciona exclusivamente el último checkpoint canónico anterior a una modificación. El inventario declara la cobertura real de Aragón, Castilla y León y Extremadura: no rellena huecos ni promueve evidencia experimental. Esta capa no recalcula resultados territoriales; prepara la integración posterior del procedimiento para ejecutar solo el tramo invalidado.

## 2026-09-12 — R025.1 — Validación del índice de checkpoints

Se corrige el validador inicial para admitir el índice multi-territorio y se preserva la primera versión en `legacy/g10/`. La validación distingue cobertura certificada de evidencia experimental bloqueada.

## 2026-09-12 — R026 — Procedimiento por tramo certificado

El lanzador territorial pasa a aceptar un intervalo semántico y registra `REENGANCHE.json`. Un reenganche posterior a M01 exige manifiesto de productos y grafo M03 materializado dentro del runner; sin ambos aborta antes de cálculo. Las ejecuciones parciales no se presentan como productos públicos validados.

## 2026-09-12 — R026.1 — Límites robustos en ejecución parcial

Se corrige el caso de tramos terminados antes de M04: el lanzador no intenta iterar un rango vacío. Se conserva v2.3.0 en `legacy/`; no hay alteración de algoritmo territorial.

## 2026-09-12 — R027 — Materialización verificable de checkpoints

Se incorpora el componente G10 que resuelve dependencias runtime, verifica bytes/SHA-256 y materializa únicamente evidencia autorizada. M05 exige M03+M04; Extremadura bloqueada se rechaza. Los informes se etiquetan `REUSED_MATERIALIZED`, sin promoción territorial.
