# Registro de cambios DDD

Registro cronológico acumulativo. No se reescriben entradas antiguas.

## 2026-09-14 — Blindaje de cálculo y publicación

C‑01, las regresiones M06, Flourish y los despliegues web quedan exclusivamente
bajo orden manual. Una prueba impide reintroducir `push` o `schedule`. La fuente
`COMARCAS.csv` se verifica aisladamente: 731 municipios, 33 comarcas, sin claves
inválidas ni duplicados contradictorios. No se ejecuta M01–M08.

El commit `24eb07e` supera la suite `34882876061`. Fue el único workflow
activado; queda certificado que el blindaje evita cálculo y publicación por push.

## 2026-09-14 — Paquete local-first — Comarcas e interfaz M01–M08

M01 añade una unión comarcal opcional por código municipal de cinco dígitos y
registra cobertura, duplicados contradictorios y faltantes. M03 conserva código
y nombre de comarca en los nodos y M06 en catálogo y composición, sin usar la
comarca como restricción. La interfaz manual se unifica bajo **Operación
territorial DDD — M01 a M08**; la línea contractual queda solo como workflow
reutilizable y el formulario G10 por tramo pasa a legacy. El paquete se prueba
con datos sintéticos y no habilita fuentes ni ejecuta territorios.

La primera certificación detecta que la baja del workflow G10 no se materializó
en el árbol remoto. Tras retirarlo, la segunda detecta una comprobación legacy
dentro del contenedor que excluye esa carpeta por diseño. Se corrige la prueba
sin relajar la ausencia del workflow activo ni la verificación legacy exterior.

## 2026-09-14 — R039 — Contrato electoral universal

M07 deja de contener el formato RTVE y de recibir tablas de partidos en el YAML
territorial. Un contrato común identifica la convocatoria, verifica fuentes y
diccionario por SHA-256, declara el adaptador de entrada y rechaza partidos no
catalogados. M08 exige igualdad exacta de distritos y rechaza duplicados. Aragón
se migra como implantación de referencia usando el fichero ya certificado; no
se ejecuta ni recalcula ningún módulo territorial.

### R039.1 — Prueba compatible con la imagen reproducible

El CI `34832589193` falla únicamente porque `.dockerignore` excluye los inputs
voluminosos. La prueba conserva la comprobación de bytes cuando están presentes
y valida dentro de la imagen la igualdad de huella entre contrato y manifiesto.
M07 mantiene la verificación obligatoria sin bypass. No se ejecuta territorio.

### R039.2 — Certificación CI

El commit `6e8162b` supera la suite general `34833051502`; el candidato inicial
también superó la validación de contratos `34832589145`. No se activó ningún
workflow territorial. R039 queda cerrado y R040 continúa bloqueado hasta orden
expresa.

## 2026-09-14 — C-01.1 — Corrección del falso PASS de robustez

El run `34778283915` completó 50 procesos, pero solo 15 produjeron mapas dentro
de la tolerancia poblacional. Se corrige el evaluador para separar éxito de
proceso y solución técnica; G01 queda `FAIL_ROBUSTNESS`. La semilla canónica
continúa siendo un resultado técnico válido, pero no robusto. No se reejecuta
ningún módulo territorial.

## 2026-09-14 — C-12.1 — Certificación de nombres

El commit `148d705` supera la suite `34786913415`. Se certifican 214 nombres
técnicos únicos y recomputables. C-12 queda cerrado sin modificar límites.

## 2026-09-14 — R038 — Picadora y operación limpia

Se archivan diez workflows territoriales sustituidos y se crea una única
interfaz manual con cinco operaciones. La línea común pasa a ser reutilizable,
publica los productos del run y comparte un único identificador entre decisión
y ejecución. Se corrige además un error de sintaxis preexistente en
`procedimiento.sh` que impedía ejecutar M04-M08.

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

### R036.1 — Certificación CI

Commit `3d1337c` supera cinco workflows: puerta contractual, suite general, G10 y regresiones de evidencia de Aragón y Castilla y León. R036 queda cerrado sin ejecutar ni recalcular M01–M06.

## 2026-09-13 — R037 — Gobierno topológico

Los siete diagnósticos continentales R023 pasan a un registro ejecutable de bloqueo/reparación/admisión. Se prohíben puentes por proximidad automática y se exige expediente completo para cada arista lógica. En archipiélagos, la contigüidad se aplica dentro de cada componente, se prohíben aristas marítimas y distritos entre componentes, y el reparto de K debe preceder a M04. No se abre ni ejecuta ningún territorio.

### R037.1 — Certificación CI

Commit `8376276` supera la suite general en CI `34757140425`. El cambio no dispara regresiones territoriales ni ejecuta M01–M06. R037 queda cerrado y el reenganche avanza a R038.

## 2026-09-13 — Paquete A — C-05/C-09 Integridad electoral

M07 deja de descartar votos mediante un `inner join` silencioso. El nuevo cruce izquierdo produce un informe que conserva la identidad votos de entrada = asignados + no asignables y bloquea cualquier descuadre no declarado. Aragón registra expresamente la sección electoral `5002501003` y sus 608 votos no asignables, además de la sección censal `2221301003` sin resultados. La comprobación sobre evidencia certificada arroja 648.799 = 648.191 + 608 votos y 1.463 secciones en cada universo. M07 se reescribe en formato revisable. La implementación no solicita M01–M06.

### Paquete A.1 — Certificación CI

El commit `113c04c` supera la suite general `34760389448` y la puerta contractual `34760389449`. Por el disparador común `ddd_core/**` se ejecutaron además, de forma incidental, las regresiones M06 de Aragón y Castilla y León (`34760389453`, `34760389444`), ambas SUCCESS y sin modificación de productos en `main`. Esta activación no era necesaria para C-05/C-09 y queda registrada como riesgo de acotación de workflows.

## 2026-09-13 — Paquete B — C-02/C-03/C-14 Publicabilidad

Se separa formalmente `TECHNICAL_PASS` de `PUBLICABLE` mediante nueve criterios sustantivos y cuatro garantías. C-02 queda confirmado: Castilla y León incumple la puerta provisional de forma con 40/82 distritos bajo 0,15 y mínimo 0,02809. C-03 queda corregido: la correlación −0,3293 es real, pero no demuestra que apretar población empeore la forma; el cuartil con peor balance es también el de peor forma. C-14 queda resuelto con definición, umbrales y regla de promoción. Ningún mapa se declara hoy publicable como propuesta política. No se ejecuta M01–M06.

## 2026-09-13 — C-01.0 — Protocolo de robustez frente a semilla

Se fija antes de observar resultados una prueba de 50 semillas para Aragón. El
workflow reutiliza por hash M03/M04 del run certificado `34599224954`, ejecuta
solo M05, calcula distribución poblacional y de forma y elimina cada geometría
intermedia. No ejecuta M01–M04 ni M06–M08 y no lee resultados partidistas. La
semilla publicada `12345` debe ser técnicamente válida y no atípica entre los
percentiles 5 y 95; se exige al menos 95 % de ejecuciones satisfactorias.

### Paquete B.1 — Certificación CI

El commit `ccaa62a` supera la suite general `34773094091`, la validación de productos `34773094067` y G10 en modo control `34773094049`; ningún workflow territorial se activa. El despliegue `34773094057` alcanza correctamente el empaquetado y falla exclusivamente en `configure-pages`, por la habilitación externa pendiente de GitHub Pages ya documentada.

## 2026-09-13 — C-04 — Sesgo poblacional del reparto de K

Se publica una métrica reproducible de carga poblacional provincial frente a la media territorial usando solo evidencia ya certificada. El máximo absoluto es 4,546 % en Aragón (Teruel) y 9,674 % en Castilla y León (Palencia). Extremadura se mide en 0,190 % sin alterar su estado `EXPERIMENTAL_BLOCKED`. La herramienta, su entrada gobernada, tres pruebas y la evidencia JSON cierran C-04 sin ejecutar M01–M06 ni abrir territorios. El reenganche avanza a C-10; C-01 queda fuera de este bloque.

### C-04.1 — Certificación CI

El commit `83ea22a` supera la suite general `34779361255`. No se activa ningún workflow territorial ni se ejecuta M01–M06. C-04 queda certificado y el siguiente hito rector es C-10.

## 2026-09-13 — C-10 — Contrato único del catálogo M06

Se fija `polsby_popper` como nombre canónico y se publica el esquema único del catálogo distrital M06. Un adaptador cerrado hace explícita la migración de nombres históricos sin reescribir runs certificados. La prueba verifica Aragón, Castilla y León y Extremadura mediante el mismo contrato, sin condicionales por territorio; Extremadura permanece bloqueada. El cambio no invoca M01–M06 y el reenganche avanza a C-07 tras certificación CI.

### C-10.1 — Certificación CI

El commit `188c980` supera la suite general `34782359264`. Los patrones históricos de workflow activan incidentalmente las regresiones M06 de Aragón (`34782359206`) y Castilla y León (`34782359236`), ambas SUCCESS y sin persistir cambios de producto en `main`. La activación se registra como riesgo operativo; C-10 queda cerrado y el reenganche avanza a C-07.

## 2026-09-13 — C-07 — Prueba sintética adversarial

Se añade un pipeline sintético con población desigual 60/40/30/70, K=2 y solución contigua óptima única 100/100. La prueba exige la asignación exacta de secciones y contiene una mutación plausible que el oráculo debe rechazar. Deja de confundirse un smoke permisivo con capacidad de detección real. Solo se ejecutan datos temporales sintéticos; no se leen ni recalculan territorios certificados. C-01 permanece intacto.

### C-07.1 — Certificación CI

El commit `a359910` supera la suite general `34783919125`, incluida la ejecución adversarial completa M01–M06 sobre cuatro secciones temporales. No se activan regresiones territoriales ni se leen productos certificados. C-07 queda cerrado y el reenganche avanza a C-06.

## 2026-09-13 — C-06 — Verificación independiente

Se añade un verificador de biblioteca estándar que no importa el productor, `ddd_core` ni el validador existente. Recalcula desde M03 y M06 universo, población, K, provincia, contigüidad, límites y disciplina municipal. Aragón y Castilla y León pasan. Extremadura queda reforzada como `BLOCKED_INDEPENDENT_VALIDATION`: además de dos distritos fuera de tolerancia, presenta cinco municipios con más de un distrito mixto. No se recalcula ni modifica ningún territorio; C-01 permanece intacto.

### C-06.1 — Certificación CI

El commit `9dde785` supera la suite general `34784297475`. No se activan regresiones territoriales. C-06 queda cerrado y el reenganche avanza a C-08.

## 2026-09-13 — C-08.0 — Autorización expresa de regresiones territoriales

Las regresiones M06 de Aragón y Castilla y León dejan de responder a cambios en `ddd_core/**` o M04 y quedan disponibles exclusivamente mediante `workflow_dispatch`. Sus definiciones automáticas anteriores se preservan en `legacy/workflows/`. Una prueba de contrato impide reintroducir disparadores `push` o `schedule`. Es una corrección mínima de seguridad operacional necesaria para trabajar C-08 sin incumplir la prohibición de recalcular M01–M06; no constituye la limpieza completa R038 y no ejecuta ningún módulo territorial.

### C-08.0.1 — Certificación CI

El commit `4e3849c` supera la suite general `34785826965`. Es el único workflow activado: las regresiones territoriales no se ejecutan. El trinquete operativo queda certificado.

## 2026-09-13 — C-08 — Motor M04 único y trazable

Se declara `ddd_core/m04_seed_engine.py` como único motor M04 vigente mediante un contrato de máquina. El ejecutable del pipeline y la herramienta de unidades internas pasan de cargar snapshots por ruta a imports estáticos del motor canónico. Una prueba AST bloquea la carga dinámica y la selección versionada en la ruta operativa. La composición algorítmica certificada no cambia y ningún producto territorial se ejecuta o recalcula. Los snapshots no operativos se declaran históricos; su traslado físico corresponde a R038, todavía suspendido.

### C-08.1 — Certificación CI

El commit `5645a23` supera la suite general `34786162160`. Es el único workflow activado y no se ejecuta ninguna regresión territorial. C-08 queda cerrado; el backlog rector avanza a C-13 y después C-12.

## 2026-09-13 — C-13 — Comunidades de interés

P07 pasa de mención inerte a contrato formal supra-municipal. Se fijan fuente admisible, neutralidad ex ante, cobertura, cuatro métricas y precompromiso obligatorio de umbrales. Aragón y Castilla y León conservan sus rutas comarcales desactivadas; Extremadura no tiene fuente declarada. Los tres quedan `NOT_EVALUABLE`, estado que bloquea publicación. Se declara alcance sin inventar datos, modificar límites ni ejecutar M01–M06. Reincorporar una fuente territorial concreta requerirá orden expresa.

### C-13.1 — Certificación CI

El commit `5a4a884` supera la suite general `34786528440`, único workflow activado. No se ejecuta ninguna regresión territorial. C-13 queda cerrado y el backlog avanza a C-12.

## 2026-09-13 — C-12 — Nombres de distrito

Se publica un sistema determinista y no partidista de nombres técnicos basado en provincia y municipio de mayor población, con regla explícita para distritos sin mayoría municipal y ordinal estable para colisiones. La evidencia contiene 214 nombres únicos, cobertura completa, pesos dominantes y hashes de las tres composiciones M06 certificadas. Las pruebas recomputan los nombres desde esas entradas. No se altera M06, ningún límite ni C-01.
## 2026-09-14 — R038.1 — Diagnóstico durable de CI

La implementación R038 falla dos veces en la suite general `34825103970`, pese a que la misma ejecución completa pasa localmente con Python 3.11 y dependencias fijadas (71/71). La puerta CI se versiona y conserva siempre el log completo como artefacto, con propagación del código de salida mediante `pipefail`. No se modifica el motor ni se ejecuta ningún territorio.

### R038.2 — Corrección exacta de la prueba en contenedor

El artefacto `ci-unittest-34830251652-1` demuestra que la única caída es la búsqueda de `legacy/` dentro de una imagen que lo excluye deliberadamente. La prueba mantiene la ausencia de workflows retirados en la ruta activa y delega la existencia de predecesores a la puerta de checkout ya vigente. No se relaja ninguna garantía ni se ejecuta un territorio.

### R038.3 — Certificación CI

El commit `7a02dba` supera la suite general `34830677071`, único workflow activado. No se ejecuta ningún territorio. R038 queda cerrado y el siguiente hito es R039.
