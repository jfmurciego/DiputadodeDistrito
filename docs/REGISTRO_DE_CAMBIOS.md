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

## 2026-09-12 — R028 — Workflow de tramo certificado

Se añade un workflow manual único que materializa checkpoints antes de ejecutar. Su modo por defecto `verify_only` no calcula; `execute` requiere una decisión explícita y corre solo el intervalo semántico seleccionado en contenedor. Al finalizar deja artefacto y notificación compacta en la incidencia G10.

## 2026-09-12 — R028.1 — Compatibilidad del workflow de tramo

Se sustituye la sintaxis compacta rechazada por GitHub Actions por YAML expandido compatible. El workflow fallido se conserva en `legacy/`; no llegó a iniciar ningún job ni alteró datos territoriales.

## 2026-09-12 — R029 — Cierre factual F1 y operación G10

Se elimina la duplicación exacta de los cinco árboles históricos de Aragón bajo `resultados/ejecuciones/`, conservando su evidencia territorial canónica. `ESTADO_FACTUAL.json` v1.1 registra contratos territoriales, margen de tolerancia, línea base de compacidad y el bloqueo de Extremadura. El workflow G10 valida modo y la notificación se centraliza para evitar correo/issue duplicado.

## 2026-09-13 — R030 — Visor público y reenganche sin recálculo

Se incorpora el visor estático MapLibre y el despliegue GitHub Pages para Aragón y Castilla y León. Consume únicamente GeoJSON finales canónicos, transforma coordenadas para dibujo en el cliente y valida 67/82 entidades antes de publicar. El punto de reenganche deja de recomendar el lote autónomo que repetía M01–M06 y limita G10 a cambios con huella nueva.

## 2026-09-13 — R030.1 — Habilitación autónoma de GitHub Pages

El primer despliegue del visor validó y empaquetó correctamente, pero GitHub Pages no estaba habilitado. El workflow activa explícitamente Pages en el primer uso y conserva su predecesor; no modifica datos territoriales.

## 2026-09-13 — R031 — Estado operativo durable G10

Se añade un generador Python de informe operacional, su contrato de prueba y la primera salida canónica JSON/Markdown. El informe expresa territorios, estado y reenganche sin autorizar nuevo cálculo territorial.

## 2026-09-13 — R031.1 — Cierre de lote con informe G10

El workflow durable genera el informe operativo antes de persistir y lo versiona junto al estado de tareas. Los artefactos del lote incluyen ambas salidas de reenganche.

## 2026-09-13 — R031.2 — Entrega completa de informe G10

El artefacto durable incorpora ahora los informes JSON y Markdown, y el comentario de finalización comunica la decisión de reenganche. Se corrige el contrato de prueba antes de consolidarlo como baseline.

## 2026-09-13 — R032 — Contrato declarativo de producto público

El visor MapLibre pasa de territorios codificados a un registro declarativo. El empaquetado de Pages genera un manifiesto verificando cardinalidad, propiedades y SHA-256 de cada GeoJSON canónico. La lista activa sigue limitada a Aragón y Castilla y León.

## 2026-09-13 — R032.1 — Reenganche alineado con producto público

El punto de reenganche pasa a señalar el estado operativo G10 y el registro declarativo de productos. Se elimina cualquier ambigüedad que pudiera provocar una repetición de M01–M06.

## 2026-09-13 — R033 — Contrato exhaustivo y verificación independiente de producto público

El manifiesto público valida ahora cada distrito: identidad única, geometría poligonal no vacía y campos declarados presentes. Se añade un workflow de verificación y empaquetado que genera el mismo sitio estático como artefacto, sin requerir GitHub Pages ni ejecutar M01–M06. Pages conserva únicamente la responsabilidad de despliegue.

## 2026-09-13 — R034 — Puerta de admisión territorial de producción

El contrato territorial pasa de guía documental a control ejecutable. La puerta verifica identidad, fuentes con checksum, seis módulos completos, continuidad de artefactos, coherencia de K/códigos/campos/restricciones y confinamiento de outputs antes de admitir M01–M06. Aragón y Castilla y León generan certificado `ADMITTED`; cinco pruebas negativas demuestran el rechazo anticipado de contratos incompletos. G10 sustituye su comprobación parcial por esta puerta. No se ejecuta ni recalcula ningún territorio.

### R034.1 — Procedencia disponible dentro del contenedor

La CI general y G10 revelaron que la imagen excluía correctamente los datasets, pero también su manifiesto ligero. `.dockerignore` conserva ahora `inputs/MANIFEST.sha256` sin empaquetar los datos; la puerta puede comprobar procedencia dentro y fuera del contenedor.

## 2026-09-13 — R035 — Interfaz única de producción territorial

La ejecución deja de seleccionar Aragón o Castilla y León mediante condicionales de workflow. Un resolutor toma el YAML admitido y deriva de él territorio, nombre de run y rutas. La nueva línea manual admite, verifica o ejecuta M01–M06; `execute` exige el literal de autorización explícita. Las pruebas demuestran dos contratos admitidos, rechazos tempranos y que los modos de control no ejecutan cálculo. No se ha lanzado ningún territorio.

### R035.1 — Certificación y cierre de la interfaz

CI `34747763671` completa correctamente. El checklist de cierre, el paquete de auditoría y el reenganche pasan a estado cerrado: el trabajo futuro es incorporar contratos territoriales autorizados, no seguir modificando la línea base.

## 2026-09-13 — R036.0 — Migración de auditoría y corrección de alcance

Se crea `docs/CONTINUIDAD_AUDITORIA_PLATAFORMA.md` como fuente de verdad para migrar la revisión externa a un nuevo hilo. Se distingue el cierre certificado de la interfaz R034–R035 del cierre todavía pendiente de la plataforma nacional. El backlog conserva política de K/límites, esquema, topología, limpieza operativa, capa electoral y prueba ciega. Se versionan el cierre y el punto de reenganche, preservando sus versiones anteriores en `legacy/`. No se ejecuta M01–M06 ni se abre ningún territorio.

## 2026-09-13 — R036 — Gobierno de K, límites y esquema

El catálogo registra la procedencia y justificación de K para los tres contratos M01–M06 existentes; el YAML conserva el valor ejecutable y la puerta exige coherencia con M04, M06 y validación. Se fija el perfil general `0.80/1.75/0.12`, con expediente obligatorio para excepciones. Se distinguen formalmente `bootstrap_m01_m03` y `production_m01_m06`. Aragón y Castilla y León conservan parámetros; Extremadura queda como excepción histórica bloqueada. Se añaden pruebas negativas y no se ejecuta ningún módulo territorial.
