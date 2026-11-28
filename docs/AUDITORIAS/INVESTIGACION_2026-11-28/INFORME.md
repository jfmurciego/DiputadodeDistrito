<!--
PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Informe de síntesis de la investigación profunda del 28-11 (T-509)
FECHA: 2026-11-28
ESTADO: PROPUESTA. Nada de lo que aquí se propone está autorizado. No es el plan; no autoriza lanzar ni publicar nada
CAMBIOS: 1.0.0 — síntesis de los ocho ámbitos con el veredicto del escéptico, bloques, tareas propuestas y orden; revisada por el crítico de completitud
MOTIVO: orden del propietario (28-11, 00:20, chat del Planificador): encontrar todos los gaps de mejora y pasar el proyecto a la siguiente fase, para ser un referente mundial
ANTERIOR: ninguna (fichero nuevo)
-->

# Investigación profunda del 28-11 — informe de síntesis (T-509)

**Para el propietario.** Ocho investigadores entregaron un informe por ámbito y un escéptico independiente intentó
refutar cada hallazgo. Este informe usa solo las cifras ya corregidas por el escéptico. Todo es **propuesta**.
`HALLAZGOS.json` trae 75 de los 84 hallazgos. Los 9 de seguridad se entregan aparte, en privado.

Palabras que se repiten: **exacto** = el programa que demuestra que no existe un mapa mejor; **K** = número de
distritos de un territorio; **D8** = la regla que ordena los mapas; **cota** = prueba de que ningún mapa baja de un
valor; **huella** = sha256 de un fichero; **ventana** = el límite de uso de 5 horas de los chats; **R2** = el almacén de
Cloudflare; **P40** = el workflow que publica; **run** = una ejecución en GitHub.

Más siglas: **CI** = las pruebas automáticas de GitHub; **PR** = una propuesta de cambio; **YAML** = el formato de los
workflows; **M01 a M08** = las etapas del motor (M06 es el mapa y M08 el resultado electoral); **P00** y **P20** = los
workflows de campaña y de distritos; **Pages** = el alojamiento actual de la web en GitHub; **DOI** = identificador
permanente de un depósito público; **nacNN** y **autNN** = un territorio del Congreso o autonómico por su código;
**skill** = las instrucciones de un rol; **linaje** = cuántos relevos encadena un chat; **T-** = tarea; **D-** = decisión
del propietario.

## 1. Veredicto en una página

| Ámbito | Liga en la que juega hoy | Lo que más pesa (con su cifra) |
|---|---|---|
| A1 Motor | Segunda seria | Demuestra el óptimo en 7 de 27 territorios con K ≥ 5; en 5 de 17 no devuelve nada; 4 de los 9 mapas que gana no tienen prueba |
| A2 Estado del arte | Segunda alta | En 16 de 71 territorios (K ≥ 45) el exacto no cabrá nunca: solo hay cadenas de 300 pasos, sin cota. 0 instancias publicadas |
| B Arquitectura | Primera en trazabilidad, regional en tubería | En una provincia del Congreso el motor es el 2 % de un run (0,9 de 44,6 minutos); main recibió 1.605 commits en 36 horas |
| C Agentes | Segunda alta | Coordinar cuesta en torno a un tercio del gasto conocido (34–37 %); 0 reglas nombran la ventana de 5 horas |
| D Repositorio | Segunda | 1.068 MB y 14.483 ficheros; 342 MB son copias exactas; `legacy/` crece 35 MB por semana |
| E Almacenamiento | Primera en huellas, segunda en conservación | 479 productos publicados sin ancla; 9,29 GB de fuentes en copia única; 0 simulacros de restauración |
| F Publicación | Primera en integridad, segunda en operación | 17 minutos por cambio; 4 de 18 publicaciones en rojo; 0 ficheros de la web subidos a R2 |
| G CI y seguridad | Segunda alta | Mecánica de primera (179 de 179 acciones fijadas por SHA); gobierno del repositorio por debajo (detalle en privado); 70 minutos de jobs por PR fusionada |

1. El proyecto está en primera en lo que certifica (huellas, trazabilidad, integridad de lo publicado) y en segunda en lo que lo sostiene (conservación, operación, coste de coordinar, gobierno del repositorio).
2. Ningún hallazgo fue refutado entero. De 84: 16 confirmados, 64 corregidos (casi siempre a la baja en alcance o impacto) y 4 sin verificar.
3. El salto del motor no está en subir el límite del exacto. Está en demostrar sobre la misma regla que se publica, repetir sin condiciones y mejorar lo grande por trozos exactos.
4. El recurso escaso ya no son los minutos de GitHub (son gratis). Es la ventana de 5 horas. Primero se presupuesta.
5. Tres cosas tienen fecha: comprobar que el exacto se repite antes de la regeneración del 29-11; anclar y duplicar antes del borrado de R2; hacer la primera tarea de seguridad (T-550) en la primera ventana tras la regeneración.

## 2. Los hallazgos que cambian la liga

Ordenados por impacto ya corregido (5 los seis primeros, 4 el resto). Coste: S = 1 sesión, M = 2 o 3, L = más de 3.

### 2.1 La ventana de 5 horas no tiene presupuesto (C-1) — CORREGIDO
- **Hoy:** ninguna skill, regla ni decisión nombra la ventana, el modelo ni el esfuerzo por rol (0 menciones). El relevo manda crear la sucesora con «mismo modelo»: el modelo caro se hereda. Las cifras de la flota de anoche solo constan en el encargo; no se pudieron comprobar desde el repositorio.
- **Por qué importa:** es el único recurso que para a todos los chats a la vez, también el del propietario.
- **Propongo:** un guion de presupuesto: modelo y esfuerzo por rol, reparto que fija el propietario (propuesta: 30 % reserva suya, 15 % coordinación, 55 % trabajo) y flotas en olas.
- **Criterio:** `python herramientas/presupuesto_ventana.py --plan <flota.json>` rechaza (salida distinta de 0) una flota de 26 sesiones a esfuerzo máximo y acepta una ola dentro del reparto; `grep -c 'mismo modelo' .claude/skills/*/SKILL.md` suma 0.
- **Coste S · necesita decisión del propietario** (el presupuesto por ventana y el reparto).

### 2.2 Coordinar cuesta un tercio del gasto: los chats residentes se releen (C-2) — CORREGIDO
- **Hoy:** el chat del Planificador lleva 216,33 USD y relee 379 tokens por cada token que escribe. Planificador y Coordinador suman entre 370 y 400 USD; los 93 chats de trabajo, 602 USD. El relevo automático (D-160) llega tarde: el umbral ya está superado y el linaje va en 7 de 8.
- **Por qué importa:** el coste de un chat largo crece con el cuadrado de su longitud. Esta investigación infla algo la cifra.
- **Propongo:** chats de coordinación efímeros, uno por ola, que leen solo el tablero y la cola (menos de 20.000 tokens). Mientras se decide: relevo a los 150.000 tokens usados.
- **Criterio:** el guion del libro de costes falla si un chat de rol supera 200.000 tokens usados o linaje 6; en el resumen semanal, los roles de coordinación suman menos del 15 %.
- **Coste M · necesita decisión del propietario** (cambia D-160).

### 2.3 Las fuentes preparadas están en una sola copia y el borrado va antes que la red (E-2, E-10) — CORREGIDO y CONFIRMADO
- **Hoy:** 120 paquetes de fuentes (9,29 GB), las fuentes del INE (1,55 GB) y el espejo del Observatorio (625 ficheros) están en un solo almacén de un solo proveedor. No consta segunda copia, bloqueo de borrado ni una prueba de restauración. Sí tienen segunda copia el ZIP nacional de Interior y los 71 mapas 1.0.0. El plan fecha un borrado de unos 4 GB tras el 29-11 y no tiene ninguna tarea de copia de seguridad.
- **Por qué importa:** si se pierde ese almacén, los mapas dejan de poder repetirse bit a bit. El INE ya no sirve el seccionado de aquel día.
- **Propongo:** bloqueo de borrado, segunda copia en otro proveedor de lo irrepetible (unos 11 GB, céntimos al mes), simulacro mensual, y que el borrado espere a esas pruebas.
- **Criterio:** existe `orchestracion/simulacro_restauracion.json` con menos de 35 días y 3 territorios restaurados desde la segunda copia, con sha256 iguales a los del contrato; un test falla si caduca; la herramienta de poda da error si no cita ese informe.
- **Coste M · necesita decisión del propietario** (otra cuenta y el bloqueo los pone él).

### 2.4 El motor ocupa el 2 % del tiempo de una ejecución (B-1) — CORREGIDO
- **Hoy:** en un run «Generar» de provincia del Congreso (mediana de 10) el motor usa 0,9 de 44,6 minutos de pasos: el 2,0 % (8,9 % en Andalucía). Montar el entorno se lleva el 56–57 %: 31 jobs por run y 15 reconstruyen la imagen. Reloj: 63,6 minutos, 17,8 de cola.
- **Por qué importa:** a 45 minutos de máquina por 1 de cálculo, mil ejecuciones son 750 horas y la campaña de 71 no cabe en una tarde.
- **Propongo:** (b) construir la imagen una vez y usarla por su huella; (a) un solo job para las etapas M01 a M06. La parte (a) reabre D-143.
- **Criterio:** en 10 runs, mediana de minutos de job del tramo P20 ≤ 12 (hoy 35,0), entorno ≤ 25 % del run, y composición sección→distrito idéntica (sha256) en 3 territorios de control.
- **Coste M · necesita decisión del propietario** (cambia la CI de producción).

### 2.5 Gobierno del repositorio (ámbito G, detalle en privado) — CONFIRMADO
- **Hoy:** la mecánica de los workflows es de primera. El gobierno del repositorio no: varias garantías viven en reglas escritas y no en GitHub. El detalle no se publica.
- **Por qué importa:** es lo primero que comprueba un auditor externo y protege todo lo demás.
- **Propongo:** las cinco tareas del bloque 7. La primera (T-550) es la más urgente. Detalle en el resumen privado.
- **Criterio:** los tests y comandos del apartado «Criterios de aceptación por tarea» del resumen privado, con el resultado que allí se indica.
- **Coste S la primera, M el bloque · necesita decisión del propietario** y ajustes que solo él puede hacer en GitHub.

### 2.6 El orden de las etapas vive en 11.193 líneas de YAML (B-2) — CORREGIDO
- **Hoy:** qué etapa va tras cuál está repartido en 15 workflows; el 48 % de sus líneas es lógica embebida. Solo M01–M08 se ejecutan fuera de GitHub; las puertas, la reanudación y el registro, no.
- **Por qué importa:** cada cambio de flujo se prueba lanzando runs reales, y un tercero no puede repetir una ejecución completa.
- **Propongo:** un fichero que declara las etapas y un ejecutor único, igual en un portátil que en la CI. Por etapas y en paralelo con lo actual. Reabre D-143.
- **Criterio:** en un contenedor limpio, un comando produce el M06 de un territorio con la misma composición (sha256) que la CI; los workflows suman ≤ 3.000 líneas; un test recorre el grafo sin red en menos de 60 segundos.
- **Coste L (muy largo; primero solo el diseño, 1 sesión) · necesita decisión del propietario.**

### 2.7 Cuatro mapas del exacto son «mejor válido», no «óptimo demostrado» (A1-4) — CORREGIDO
- **Hoy:** en la medición T-507, 4 de los 9 mapas que gana el exacto (nac12, nac15, nac41, nac43) son el mejor plan hallado cuando se acabó el tope de cálculo. Ese plan entra en la huella y se publicará en la regeneración del 29-11. Solo Sevilla se ha repetido (misma huella); los demás, una vez, y siempre en la misma clase de máquina.
- **Por qué importa:** la regla del proyecto es «misma entrada, mismo mapa». Es el eslabón menos probado.
- **Propongo:** antes de republicar, repetir 5 veces en local los 5 territorios con «mejor válido»: los 4 que ganan y nac20 (unos 60 minutos de CPU). Después, una etapa final que haga depender el plan solo de los datos.
- **Criterio:** las 25 ejecuciones dan una sola huella de plan por territorio.
- **Coste S la prueba, M el cambio · necesita decisión del propietario** (estudio, D-18; el cambio es de motor).

### 2.8 El exacto no devuelve nada en 5 de 17 territorios (A1-1) — CORREGIDO, confianza baja
- **Hoy:** en nac06, nac17, nac18, nac31 y nac45 el exacto termina sin solución aunque había un plan válido: 215 segundos sin resultado. La causa que proponía el investigador no se sostuvo en la verificación.
- **Por qué importa:** falla en el 29 % de los casos donde aplica. Si es un defecto del modelo, conviene saberlo antes de la regeneración.
- **Propongo:** solo diagnóstico: repetir los 5 guardando el estado de cada etapa (unos 8 minutos de CPU). El arreglo se decide con ese dato.
- **Criterio:** tabla con el estado de la primera etapa de los 5 y el dato «pista aplicada: sí o no».
- **Coste S · necesita decisión del propietario** (estudio, D-18).

### 2.9 En lo grande no hay exacto ni cota: mejora local exacta y ráfagas (A1-3, A2-1, A2-4) — CORREGIDO
- **Hoy:** el exacto demuestra el óptimo en 7 de los 27 territorios con K ≥ 5 medidos; 7 no caben. 16 de los 71 territorios tienen K ≥ 45 y no cabrán nunca. Allí solo hay cadenas de 300 pasos. Más pasos ayudan poco: GerryChain puro con 10 semillas y 100.000 pasos (6,9 horas de CPU) no alcanzó el óptimo en Burgos, Valladolid ni Sevilla.
- **Por qué importa:** en Madrid, Barcelona y las autonómicas nadie sabe a cuánto está el mapa del mejor posible.
- **Propongo:** partir del ganador y resolver de forma exacta grupos de 2 a 4 distritos vecinos; ráfagas cortas con el mismo gasto; una cota propia. El resultado se llama «óptimo local», no «óptimo demostrado».
- **Laboratorio parcial, sin verificar (3 de 6 territorios):** Zaragoza pasa de 8 a 3 demarcaciones partidas y de 945 a 631 km de frontera; nac46, de 26 a 19 y de 1.088 a 812 km; nac03 baja la frontera de 728 a 693 km. Misma salida en 2 repeticiones. Tarda de 5 a 15 minutos por territorio (el criterio pedía 2).
- **Criterio:** alcanza el óptimo demostrado en ≥ 6 de los 7 territorios que lo tienen y mejora al ganador en ≥ 3 de los 7 que no caben, con la misma huella en dos ejecuciones.
- **Coste L · necesita decisión del propietario** (estudio y después cambio de motor).

### 2.10 Los 479 productos publicados cuelgan de objetos sin ancla (E-1) — CORREGIDO
- **Hoy:** los 245 M06 y 234 M08 del registro están en GitHub como objetos sueltos, sin rama ni referencia. No viajan en una copia del repositorio y GitHub no promete conservarlos. La publicación y 16 herramientas leen de ahí.
- **Por qué importa:** una limpieza de GitHub o una migración pararía la publicación hasta regenerar. Son regenerables, pero no bit a bit.
- **Propongo:** sujetarlos con una referencia propia (sin volver a subir nada), copia por sha256 en R2 y un test.
- **Criterio:** en una copia espejo del repositorio (`git clone --mirror`) están 481 de 481 objetos del registro (los 479 productos y 2 ficheros estáticos); un test falla si falta uno.
- **Coste S · necesita decisión del propietario** (toca P40).

### 2.11 El corte a Cloudflare se apoya en un ensayo que no ha empezado (F-1, F-5) — CORREGIDO
- **Hoy:** el plan da por hecho que la web ya se sube a R2. En todas las publicaciones medidas (datos 11 de 11; web 9 de 9) el paso acaba en 0 segundos, en verde y sin subir nada. Ya es T-510. Además, al plan de corte le faltan siete piezas y dos están a medias (página 404, `www`, direcciones antiguas, vuelta atrás real, caché, cabeceras, umbrales).
- **Por qué importa:** es el cambio de mayor riesgo público del mes y no hay un solo día de web en R2 comparada con la actual.
- **Propongo:** completar T-510 con un aviso visible cuando no se suba nada, y una lista de corte de una página con un guion de solo lectura.
- **Criterio:** tras una P40 «Solo el sitio», el log dice «N ficheros; M a subir» con N > 0; `comprobar_corte.py` da 20 comprobaciones en verde en `nueva.` y, tras el corte, en el dominio real.
- **Coste S + M · necesita decisión del propietario** (las reglas de Cloudflare las pega él).

### 2.12 No hay vuelta atrás de una publicación (F-3) — CORREGIDO
- **Hoy:** el artefacto de Pages se guarda 1 día y R2 guarda «solo la vigente» (D-188). Deshacer un error visible exige revertir en main, pasar la CI (15–20 minutos), publicar otra vez (17 minutos) y la frase del propietario: 40 minutos como mínimo.
- **Por qué importa:** un referente no puede tardar eso en retirar un dato electoral erróneo.
- **Propongo:** en Pages, guardar 14 días y un modo «volver a la anterior» (no choca con nada). En R2, tres versiones y un puntero: choca con D-188.
- **Criterio:** test con R2 simulado: publicar A, publicar B, revertir → lo servido es A byte a byte, sin reconstruir; el tiempo real se mide en un simulacro (objetivo: menos de 2 minutos).
- **Coste M · necesita decisión del propietario.**

### 2.13 La rama main hace de base de datos (B-5) — CORREGIDO
- **Hoy:** main recibió 1.605 commits en las 36 horas de la última campaña (unos 22 por territorio). Para que no choquen hay una herramienta propia con 10–20 reintentos; los agotó en 4 de 100 runs.
- **Por qué importa:** git pone las escrituras en fila. Mil ejecuciones serían decenas de miles de commits y el historial de código, enterrado.
- **Propongo:** registros por run en R2, de solo añadir; el estado derivado se genera al publicar; main recibe un commit por campaña. T-379 ya prevé una parte.
- **Criterio:** en una campaña de 71 territorios, ≤ 2 commits de robot en main y ningún run con empuje rechazado.
- **Coste L · necesita decisión del propietario.**

### 2.14 La copia en `legacy/` cuesta 35 MB por semana y no protege (D-2, C-10) — CORREGIDO
- **Hoy:** `legacy/` tiene 2.675 ficheros y 152,7 MB. Entran 355 ficheros y 35 MB por semana; tres cuartas partes de ese peso son copias enteras del registro de cambios (hay 655 en total). El 93 % del peso no lo cita nada vivo. El test de la regla cubre 22 ficheros. De 487 commits de main desde el 16-11, 186 son solo de numerar el registro.
- **Por qué importa:** se paga en cada PR y en cada lectura de cada agente. Git ya guarda las mismas versiones sin trabajo.
- **Propongo:** tres escalones: los ficheros que solo crecen dejan de copiarse; el predecesor se cita por su sha de git; se retira lo que nadie cita, con un índice.
- **Criterio:** tras una numeración real no aparece ningún fichero nuevo en `legacy/docs/`; `git ls-files legacy | wc -l` da menos de 550; la huella M05 no cambia.
- **Coste M · necesita decisión del propietario** (es una regla suya).

### 2.15 El estado del proyecto vive en prosa: plan, tablero y costes (C-3, C-4, C-5) — CORREGIDO
- **Hoy:** `docs/PLAN.md` tiene 1.191 líneas y 190 KB (unos 50.000 tokens cada vez que un chat lo abre), 216 decisiones y 407 tareas, y empieza con reglas del 07-11 que contradicen seis vigentes. El libro de costes está en 12 ficheros: 97 partidas y 862,13 USD del 14 al 28-11, sin id de sesión y con 0 partidas del Planificador y del Operador. El 62 % del tablero es del 16-11 o anterior.
- **Por qué importa:** sin libro fiable no se puede presupuestar una ventana, y cada chat paga por leer lo que no necesita.
- **Propongo:** libro de una fila por sesión; una ficha por tarea abierta; plan y tablero generados por guion.
- **Criterio:** el guion del libro reproduce 862,13 USD ± 1 %; `wc -c docs/PLAN.md` da menos de 20.000; el tablero generado se comprueba en la CI.
- **Coste S el libro, L el plan · el libro solo necesita fusión; el plan, decisión del propietario.**

### 2.16 El mapa no tiene enlace por distrito (F-6) — CONFIRMADO
- **Hoy:** la dirección solo guarda la regla. No se puede enviar «mi distrito» ni volver con el botón Atrás.
- **Por qué importa:** el producto es «tu diputado de distrito»: lo que la gente comparte es su distrito.
- **Propongo:** territorio, distrito, capa y regla en la dirección, y un botón «Copiar enlace».
- **Criterio:** prueba del visor: abrir con `?t=nac28&d=7&regla=dos` deja el territorio, el distrito y la regla esperados; con un código inexistente, vista nacional y aviso, sin error.
- **Coste M · necesita decisión del propietario** (producto, D-18).

### 2.17 Un tercero no puede repetir un mapa (E-5) — CORREGIDO, confianza media
- **Hoy:** el paquete de fuentes que cita cada contrato solo existe en un almacén privado, y quedan 10 piezas por subir. Sí es público el ZIP nacional de Interior.
- **Por qué importa:** «reproducible» significa hoy «reproducible por quien tiene acceso al almacén». Un revisor externo no puede comprobarlo.
- **Propongo:** depositar con DOI los paquetes de fuentes cuya licencia lo permita. La licencia está sin confirmar con cada organismo.
- **Criterio:** sin ninguna credencial, se baja del DOI el paquete de una provincia y `sha256sum` da el `package_sha256` de su contrato; un test falla si un paquete depositado no está en la tabla de huellas del depósito.
- **Coste M · necesita decisión del propietario** (amplía D-146 y D-94: Zenodo es hoy «solo mapas»).

## 3. La siguiente fase: siete bloques

**Bloque 1 — Presupuesto y sistema de agentes** (T-511 a T-518)
- **Hoy:** la ventana no se presupuesta; coordinar cuesta un tercio; plan, tablero y costes en prosa; 9 contradicciones entre skills; evaluaciones del 07-11 para 2 de 15 piezas.
- **Por qué:** el estado vive en chats largos que se releen, no en ficheros pequeños.
- **Recibe:** un guion que impide una flota que agote la ventana, un cuadro semanal de gasto por rol y un plan que se lee en un minuto.
- **Si no se hace:** se repite lo de anoche y el gasto de coordinar sigue creciendo.
- **Prueba:** el guion rechaza la flota de 26 sesiones; coordinación < 15 % del gasto semanal; `docs/PLAN.md` < 20 KB.

**Bloque 2 — Motor** (T-519 a T-526)
- **Hoy:** el exacto se aplica siempre con K de 2 a 4 (16 territorios; otros 8 tienen K = 1 y no hay nada que trazar) y demuestra el óptimo en 7 de 27 con K ≥ 5. 5 de 17 sin resultado. 4 mapas sin prueba. Sin cota en lo grande. La prueba usa una regla que difiere de la oficial por debajo de 1 metro. Ninguna prueba automática con un caso real de K ≥ 5.
- **Por qué:** el exacto es todo o nada y la búsqueda es la de 2019.
- **Recibe:** antes del 29-11, la certeza (o el aviso) de que los mapas del exacto se repiten. Después, mapas mejores en lo grande con un certificado honesto y una cota por territorio.
- **Si no se hace:** «el motor que demuestra» vale solo para lo pequeño, y un tercero puede enseñar un plan mejor que uno marcado óptimo.
- **Prueba:** 25 ejecuciones, una huella por territorio; el test de 200 instancias contra la enumeración pasa; la mejora local alcanza el óptimo en ≥ 6 de 7.

**Bloque 3 — Conservación y datos** (T-527 a T-532)
- **Hoy:** 479 productos sin ancla, fuentes en copia única, 0 simulacros, 284 avisos falsos en el catálogo y 633 de 651 fuentes marcadas «pendiente de subir» aunque 625 ya están subidas.
- **Por qué:** nadie ha declarado dónde vive cada clase de dato ni ha probado a recuperarlo.
- **Recibe:** la garantía, probada cada mes si él pide ese simulacro periódico, de que todo lo publicado se puede recuperar, y un borrado de R2 con red.
- **Si no se hace:** el borrado posterior al 29-11 se hace sobre un inventario del 21-11 y sin segunda copia.
- **Prueba:** informe de simulacro con menos de 35 días; 481 de 481 objetos en una copia espejo; 0 avisos falsos.

**Bloque 4 — Publicación y web** (T-533 a T-537)
- **Hoy:** 17 minutos y una frase por cambio; 4 de 18 publicaciones en rojo; sin vuelta atrás ni comprobación tras desplegar; web en R2 sin estrenar; mapa sin enlace por distrito y con más de 480 KB al abrir (tope decidido: 100 KB).
- **Por qué:** «publicado» significa hoy «el job terminó», no «el público ve la versión correcta».
- **Recibe:** un corte a Cloudflare con lista y prueba, un botón de volver atrás y un enlace para cada distrito.
- **Si no se hace:** el corte se hace sin ensayo y un error visible dura 40 minutos o más.
- **Prueba:** `comprobar_corte.py` con 20 comprobaciones en verde; simulacro de vuelta atrás cronometrado; el log de P40 imprime la versión que ve el público.

**Bloque 5 — Arquitectura y ejecución** (T-538 a T-543)
- **Hoy:** fiable en lote (95 de 100 runs en éxito) y cara: 2 % de motor, unos 90 minutos de reloj por territorio, 1.605 commits por campaña y la medida parada desde el 9-11.
- **Por qué:** el orquestador es GitHub Actions y la base de datos es la rama main.
- **Recibe:** una campaña de 71 territorios que cabe en una tarde y un motor que se puede ejecutar miles de veces.
- **Si no se hace:** mil ejecuciones cuestan 750 horas de máquina y decenas de miles de commits.
- **Prueba:** tramo P20 ≤ 12 minutos de job (hoy 35,0); ≤ 2 commits de robot por campaña; métricas con fecha posterior a la última campaña.

**Bloque 6 — Repositorio y CI** (T-544 a T-549)
- **Hoy:** 1.068 MB; 342 MB de copias; el 17–18 % de las aserciones comprueba texto; cada PR fusionada gasta 70 minutos de jobs y entre el 26 % y el 40 % son solo documentación; entre el 58 % y el 95 % de lo que devuelve una búsqueda son copias.
- **Por qué:** código, archivo, datos y salidas comparten árbol y nada vigila el tamaño.
- **Recibe:** un repositorio que un tercero puede clonar y entender, y PR de documentación que esperan menos (2–3 minutos en vez de 10: estimación sin medir).
- **Si no se hace:** cada sesión y cada búsqueda pagan el peso muerto, y lo que se limpie vuelve a llenarse.
- **Prueba:** árbol < 600 MB; `legacy` < 550 ficheros; una PR con un fichero de 2 MB queda en rojo; una PR solo de `docs/` acaba `pruebas` en menos de 3 minutos.

**Bloque 7 — Seguridad** (T-550 a T-554)
- **Hoy:** 11 hallazgos: 4 confirmados, 7 corregidos, ninguno refutado. Dos son de coste y organización de la CI y están en el bloque 6.
- **Familias:** gobierno de las fusiones y de la rama principal; identidad y permisos; custodia de llaves; cadena de dependencias; ajustes de seguridad de la plataforma.
- **Recibe:** garantías que cualquiera puede comprobar desde fuera en GitHub. El detalle (gravedad, arreglo y orden) va en un resumen privado.
- **Si no se hace:** esas garantías siguen dependiendo de reglas escritas.
- **Prueba:** los tests y comandos del apartado «Criterios de aceptación por tarea» del resumen privado, con su resultado esperado. Parte la hace el propietario hoy desde los ajustes de GitHub, sin código.

## 4. Tareas propuestas

Son propuestas: **no están en el plan**. Se aprueban por bloques («sí al bloque N») o una a una. «Sesiones» es una estimación.
La última columna dice si toca motor, CI o publicación: esas necesitan diseño aprobado antes de implementarse (D-216).

| Tarea | Bl. | Qué recibe el propietario | Criterio de aceptación | Ses. | Depende de | Motor, CI o publicación |
|---|---|---|---|---|---|---|
| T-511 Presupuesto de ventana | 1 | Ninguna flota vuelve a agotar la ventana | El guion rechaza 26 sesiones a esfuerzo máximo y acepta una ola dentro del reparto; 0 «mismo modelo» en las skills | 1 | Su cifra de reparto | No |
| T-512 Libro de costes | 1 | Gasto semanal por rol y por tarea | El guion reproduce 862,13 USD ± 1 % con las 97 partidas; falla si una fila nueva no tiene sesión o rol | 1 | — | No |
| T-513 Coordinación efímera | 1 | Coordinar cuesta menos del 15 % | El guion del libro de costes sale con error si un chat de rol pasa de 200.000 tokens usados o de linaje 6; en su resumen semanal, coordinación < 15 % | 2 | T-512; cambia D-160 | No |
| T-514 Plan en fichas y tablero generado | 1 | Plan y tablero al día sin leer 190 KB | `wc -c docs/PLAN.md` da menos de 20.000; un test falla si una tarea abierta no tiene ficha con criterio; la CI falla si el tablero versionado difiere del generado | 3 | Decisión | CI (un test) |
| T-515 Skills coherentes y reglas con límite | 1 | Una sola regla por asunto | `tests/test_skills_coherencia.py` en verde (0 apariciones de las frases contradictorias listadas en C-7); un test falla si `CLAUDE.md` pasa de 8 KB o una regla de 12 KB | 1 | — | No |
| T-516 Guion de lanzar | 1 | Las comprobaciones previas las hace una máquina | Ficha caducada o territorio fuera de ficha → salida 2; run en curso → 3; dentro de ficha, imprime el envío sin enviarlo | 2 | — | Publicación |
| T-517 Evaluaciones por rol | 1 | Saber qué modelo barato basta para cada rol | Un test falla si hay menos de 15 escenarios (3 por rol) o si falta un resultado por agente y modelo con fecha posterior al último cambio de reglas | 2 | T-511 | CI |
| T-518 Límites de rol por entorno | 1 | «No lanza» y «no edita el plan» dejan de ser solo prosa | Cuatro tests nuevos en `tests/test_t78_rol_herramientas.py` en verde: lanzar sin rol de operador → salida 2 y con él → 0; editar `docs/PLAN.md` sin rol de planificador → 2 y con él → 0. `list_environments` muestra los entornos de rol | 1 | Sus entornos | No |
| T-519 Repetición y diagnóstico del exacto | 2 | Saber antes del 29-11 si los mapas del exacto se repiten | 25 ejecuciones, una huella por territorio; tabla de los 5 sin solución con el estado de la primera etapa | 1 | Sí al estudio (D-18) | No (solo mide) |
| T-520 Una sola regla entera y etapas completas | 2 | «Óptimo» significa óptimo de la regla publicada | Test de 200 instancias (50 con diferencias de menos de 1 m) igual a la enumeración; en los 5 «mejor válido» la clave no empeora | 2 | T-519 | Motor (cambia huellas) |
| T-521 Motor repetible sin condiciones | 2 | Mismo mapa sin depender de una variable ni del día | La orden de la batería sale con código 6 sin la variable; la CI resuelve una instancia versionada en óptimo; más las comprobaciones de dependencias del resumen privado | 2 | — | Motor y CI |
| T-522 Laboratorio de búsqueda | 2 | Mapas mejores donde el exacto no cabe | Mejora local: óptimo en ≥ 6 de 7 y mejora en ≥ 3 de 7; ráfagas: óptimo en ≥ 2 de 3 y nunca peor que la línea base | 3 | Sí al estudio | No (estudio) |
| T-523 Cota y certificado | 2 | «Como mucho a N del mejor posible» en cada territorio | Cota ≤ óptimo demostrado en 4 territorios, con el hueco anotado en el informe del estudio; certificado de Sevilla atado a reglas e instancia y confirmado por un segundo resolutor | 3 | Sí al estudio; D-92 si se quiere publicar | No (estudio) |
| T-524 Exacto por circunscripción | 2 | El exacto entra en autonómicas con varias provincias | Tabla de tamaños de los 9 contratos; en nac38 deja de dar «no aplica»; misma clave que el modelo entero en un caso de prueba | 2 | T-520 | Motor |
| T-525 Certificados guardados y menos lecturas | 2 | Una segunda pasada tarda la tercera parte | Segunda competición de nac41 en ≤ 40 s (hoy 113–149) con la misma huella; el grafo se lee ≤ 2 veces (esta parte sale de A1-9, sin verificar) | 2 | T-520; regla del 08-11 | Motor |
| T-526 Estudios de método | 2 | Respuesta con datos a «¿por qué ese orden?» y a la población futura | Existe la tabla de 3 filas por territorio en 4 territorios, con su estado y la fila elegida por D8 marcada; existe la tabla de distritos fuera de tolerancia con la población de 4 años antes | 2 | Sí al estudio; D-92 si se quiere publicar | No |
| T-527 Anclar los productos publicados | 3 | Lo publicado no depende de objetos sueltos | 481 de 481 objetos del registro en una copia espejo (`git cat-file -e` por objeto); un test del guardián falla si falta uno | 1 | — | Publicación |
| T-528 Segunda copia, bloqueo y simulacro | 3 | Todo lo irrepetible, en dos sitios y probado | Informe de simulacro < 35 días con 3 territorios restaurados y sha256 iguales; borrar un objeto centinela da error | 2 | Su cuenta y su bloqueo; que pida el simulacro periódico | CI |
| T-529 Mapa de almacenamiento y borrado condicionado | 3 | Una tabla que dice dónde vive cada dato | El test falla si una clase irrepetible tiene menos de dos copias; la poda da error sin el informe del simulacro | 1 | T-527, T-528 | CI |
| T-530 Catálogo, índice e inventario veraces | 3 | Los avisos vuelven a significar algo | 0 avisos falsos en los 71 canónicos; 651 de 651 fuentes con licencia; inventario de los 5 almacenes con menos de 8 días | 2 | Un lanzamiento (inventario) | CI |
| T-531 Datos abiertos reutilizables | 3 | Un tercero usa los datos sin preguntar | Con solo el DOI: el paquete se valida sin errores y un guion de 10 líneas pinta una provincia | 1 | T-476 | Publicación |
| T-532 Versiones publicadas y fuentes con DOI | 3 | Poder decir qué decía la web un día dado | Todo sha256 fijado responde en `publicado/<sha256>`; un paquete de fuentes se baja por DOI y su sha256 es el del contrato | 2 | Reabrir D-188 y D-146 | Publicación |
| T-533 Web en R2 de verdad | 4 | El ensayo del corte empieza | Log con «N ficheros; M a subir» y N > 0; aviso visible si falta la variable; guarda si el mapa llega sin datos | 1 | T-510 | Publicación |
| T-534 Lista de corte a Cloudflare | 4 | Un corte con prueba por línea | `comprobar_corte.py` da 20 comprobaciones en verde. Entre ellas: las cabeceras de seguridad están en la respuesta; `robots.txt` y el mapa del sitio responden 200; una dirección inexistente responde 404 (estos tres ficheros salen de F-11, sin verificar) | 2 | T-533; él pega las reglas | Publicación |
| T-535 Publicar con comprobación y vuelta atrás | 4 | Un error se retira en minutos | Un test con el caso del 26-11 falla antes del paso de desplegar; el log de P40 imprime la versión que sirve la web y es la publicada; el modo «volver a la anterior» de Pages deja la versión previa byte a byte, sin reconstruir | 2 | — | Publicación y CI |
| T-536 Enlace por distrito | 4 | Cada persona comparte su distrito | Prueba del visor con `?t=nac28&d=7&regla=dos`; un código inexistente no da error | 2 | Sí de producto (D-18) | Publicación (web) |
| T-537 Errores pasajeros y techo de peso | 4 | El mapa no dice «sin distrito certificado» por un corte de red | Tras «Reintentar» la provincia se pinta; aviso a los 20 s; 30 KB de más dejan la prueba de peso en rojo | 1 | — | CI (web) |
| T-538 Medida viva de la tubería | 5 | Saber cada campaña cuánto es motor y cuánto es espera | El fichero de métricas tiene fecha posterior a la campaña e incluye el porcentaje de motor por territorio | 1 | — | CI |
| T-539 Imagen construida una vez | 5 | Menos de la mitad de minutos por territorio | Entorno ≤ 25 % del run (hoy 56–57 %); misma composición en 3 territorios | 2 | T-538 | CI |
| T-540 Un job para M01–M06 y líneas base de T-379 | 5 | Una campaña que cabe en una tarde | Tramo P20 ≤ 12 minutos (hoy 35,0); 0 runs lanzados por el bot; reloj ≤ 30 minutos por territorio (hoy unos 90) | 3 | Reabrir D-143; T-379 | CI y motor |
| T-541 Reanudar por clave y huella única | 5 | No hay que acordarse de qué modo usar | Relanzar sin cambios ejecuta 0 etapas; cambiar un byte de M02 invalida M02 en adelante y no M01 | 3 | T-539 | Motor y CI |
| T-542 Estado fuera de main | 5 | Historial de código legible | ≤ 2 commits de robot por campaña; ≤ 3 ficheros de evidencia cambiados por territorio | 3 | T-379 | CI y publicación |
| T-543 Diseño del ejecutor único | 5 | Decidir con un diseño delante | Existe el documento de diseño con tres apartados (etapas, migración en sombra y fecha de retirada de la ruta vieja); el revisor independiente lo da por conforme; `git diff --stat` de la PR no toca `.github/` | 1 | Reabrir D-143 | Motor y CI (solo diseño) |
| T-544 Higiene inmediata del árbol | 6 | Búsquedas limpias y un tope de tamaño | La búsqueda de `production_run_id` da menos de 80 resultados (hoy 1.154); un fichero de 2 MB deja la CI en rojo | 2 | — | CI (un test) |
| T-545 Gobernanza ligera de `legacy/` | 6 | La regla deja de costar 35 MB por semana | 0 copias nuevas del registro; `legacy` < 550 ficheros; huella M05 igual | 2 | Su sí a cambiar la regla | CI |
| T-546 Binarios y copias fuera del árbol | 6 | Un repositorio de menos de 600 MB | Árbol < 600 MB (hoy 1.068); copias exactas < 50 MB (hoy 342); cada fichero retirado, en un índice con sha256 | 2 | T-544 | CI |
| T-547 CI por niveles y reparto al día | 6 | Menos espera en las PR de documentación | PR solo de `docs/` < 3 minutos; minutos por PR fusionada −30 % sobre 70; una PR con código ejecuta todo | 2 | Su frase (D-49) | CI |
| T-548 Tests clasificados y código sin uso | 6 | Tests que fallan cuando algo deja de funcionar | Aserciones de texto < 10 % (hoy 17–18 %); 0 ficheros de código sin cita ni motivo | 3 | T-544 | CI |
| T-549 Workflows sin bloques repetidos | 6 | Un arreglo se hace en un sitio, no en 24 | Menos de 8.000 líneas (hoy 11.193) sin cambiar comportamiento | 3 | T-543 | CI |
| T-550 Seguridad 1: gobierno de las fusiones | 7 | Detalle en el resumen privado | Resumen privado, «Criterios de aceptación por tarea» | 1 | — | CI |
| T-551 Seguridad 2: ajustes del repositorio en GitHub | 7 | Detalle en el resumen privado | Resumen privado, «Criterios de aceptación por tarea» | 0 | Lo hace él, sin código | No |
| T-552 Seguridad 3: custodia de llaves | 7 | Detalle en el resumen privado | Resumen privado, «Criterios de aceptación por tarea» | 2 | T-550 | CI y publicación |
| T-553 Seguridad 4: permisos y análisis de workflows | 7 | Detalle en el resumen privado | Resumen privado, «Criterios de aceptación por tarea» | 2 | — | CI |
| T-554 Seguridad 5: revisión y operaciones irreversibles | 7 | Detalle en el resumen privado | Resumen privado, «Criterios de aceptación por tarea» | 2 | Sus excepciones | CI |

Los números T-511 a T-554 son provisionales: `docs/PLAN.md` llega hoy a T-505 y el Planificador debe confirmar que no chocan.

Total: 44 tareas y unas 81 sesiones. Bloque 1: 13; bloque 2: 17; bloque 3: 9; bloque 4: 8; bloque 5: 13; bloque 6: 14; bloque 7: 7.

## 5. Orden recomendado para dos semanas

**La restricción es la ventana.** Una ventana de 5 horas da para 6 a 8 sesiones de trabajo con presupuesto de llamadas (estimación de una sola noche, sin medir).
Planifico 6: el resto es la reserva del propietario y de la coordinación. Ocho ventanas en 14 días son 45 sesiones:
cabe algo más de la mitad de las 81. Cada sesión, con modelo, esfuerzo y tope de llamadas explícitos.
Este orden no cierra ningún frente (D-216: siguen todos abiertos): solo reparte la ventana.

| Ventana | Cuándo | Qué va | Sesiones |
|---|---|---|---|
| 1 | Hoy, 28-11, **antes de la regeneración** | T-519 (repetición y diagnóstico del exacto), T-511, T-512. El propietario: la parte sin riesgo de T-551 | 3 |
| 2 | Tras la noche del 29-11 | T-527, T-528, T-529, T-550, T-533 | 6 |
| 3 | Siguiente | T-530, T-554, T-544. **Solo después de esta ventana se autoriza el borrado de R2** | 6 |
| 4 | Siguiente | T-534, T-535, T-513. Solo después se ensaya el corte a Cloudflare | 6 |
| 5 | Semana 2 | T-522, T-520, T-538 | 6 |
| 6 | Semana 2 | T-521, T-545, T-547 | 6 |
| 7 | Semana 2 | T-539, T-552, T-553 | 6 |
| 8 | Semana 2 | T-514, T-536, T-515 | 6 |

- **Antes de la regeneración del 29-11:** solo medir (T-519) y presupuestar (T-511, T-512). Propongo no tocar la víspera el motor, la CI de producción ni las reglas de la rama: un ajuste mal puesto pararía la campaña. Si T-519 da huellas distintas, los 4 territorios del exacto necesitan otra regla antes de publicarse (decide el propietario, D-215).
- **Antes del borrado de R2:** productos anclados (T-527), segunda copia con simulacro en verde (T-528), mapa de almacenamiento (T-529), inventario fresco (T-530) y T-554 (seguridad; detalle en privado). Esperar cuesta céntimos al mes.
- **Antes de retirar Pages:** T-533, T-534 y T-535 en verde y un simulacro de vuelta atrás cronometrado.
- **Queda para después de las dos semanas (36 sesiones):** T-516, T-517, T-518, T-523, T-524, T-525, T-526, T-531, T-532, T-537, T-540, T-541, T-542, T-543, T-546, T-548 y T-549.
- Los cambios de motor (T-520, T-524, T-525 y parte de T-521) pueden cambiar huellas: entran en una regeneración posterior, no en la del 29-11.

## 6. Lo que choca con decisiones vigentes

Nada de esto se da por hecho. Cada línea necesita que el propietario revise la decisión citada.

- **D-188** («solo la versión vigente» en R2): conservar lo publicado por sha256 (E-3) y guardar tres versiones para volver atrás (F-3, parte de R2).
- **D-146 y D-94** (Zenodo, solo mapas): depositar con DOI los paquetes de fuentes (E-5) y usarlo como tercera copia (E-2).
- **D-92, D-94 y D-96** (motor, definición de D8 y mediciones, secretos): banco público con verificador (A2-6), publicar la tabla de renuncias (A2-9), cualquier certificado comprobable por terceros (A2-7) y publicar la cota o el hueco de un territorio (A2-2). T-523 y T-526 se quedan en estudio interno mientras D-92 no cambie.
- **D-143, D-129, D-130 y D-145** (cadena de P00; un workflow por familia): un solo job para M01–M06 (B-1, parte a) y el ejecutor único (B-2).
- **D-160** (relevo automático al 70 % del umbral; la skill añade «mismo modelo»): relevo por tamaño absoluto, modelo explícito y chats de coordinación efímeros (C-1, C-2).
- **D-49** (batería completa en cada cambio de código; «main en verde»): vía rápida para documentación y no repetir la suite al fusionar (G-5).
- **D-82** (lo antiguo se archiva, no se borra) **y la regla de gobernanza** (copia en `legacy/` de cada cambio): dejar de copiar lo que solo crece y retirar lo que nadie cita, con un índice por sha256 (D-2, C-10).
- **Regla del 08-11** (no conservar resultados antiguos): almacén de certificados del exacto (A1-6) y versiones publicadas (E-3).
- **D-176, D-178 y D-190** (borrado de R2 tras el 29-11): se añaden condiciones previas (E-10). **D-194** (retirar Pages a las 2 semanas): la retirada también se condiciona, y hay una opción de dejar Pages con una página mínima para no romper las direcciones antiguas (F-5).
- **D-138 y D-141** (alternativas retiradas): validar un muestreador solo tiene sentido si vuelven (A2-5).
- **D-127 y T-293**: dos propuestas de seguridad (dentro de T-554) piden una excepción a cada una. Detalle en el resumen privado.
- **Regla «sin vigilantes ni revisiones programadas salvo que se pidan»** (`CLAUDE.md`): el simulacro mensual de restauración (E-2, T-528), el inventario con menos de 8 días (E-9, T-530) y alguna comprobación nocturna de seguridad son revisiones periódicas. Solo entran si el propietario las pide.
- **D-52 y la regla de lanzamientos**: la ejecución en GitHub de T-519, el inventario de T-530, los simulacros y las campañas de medida necesitan su frase en el chat del Operador. Ninguna tarea la da por hecha.
- **D-216** (se rechazó reducir a dos o tres frentes: siguen todos abiertos): el orden del apartado 5 reparte la ventana, no cierra ningún frente. Si el propietario prefiere avanzar todos a la vez, cada ventana admite menos tareas por frente.
- **D-18** (ningún estudio sin aprobación): T-519, T-522, T-523 y T-526 son estudios y necesitan un sí expreso.
- **D-215** (el exacto por tamaño entra en la regeneración del 29-11): no choca, pero A1-4 y A1-1 piden comprobarlo antes.
- **D-214** (el resto de la auditoría del 25-11 queda como propuesta): T-467, T-468, T-469, T-490, T-493 y T-494 de aquel plan se solapan con T-522, T-523, T-545, T-516 y T-512. Conviene fundirlas, no duplicarlas.

## 7. Qué queda por investigar (segunda pasada)

- **Ciencia y método:** si D8 mide lo que dice medir; sensibilidad al orden de sus cinco términos; comparación con `redist` y GerryChain en casos de la literatura (D-73, D-86).
- **Análisis electoral:** qué cambian los distritos en la representación (proporcionalidad, doble vuelta, estabilidad entre elecciones). Ningún ámbito lo miró.
- **Calidad numérica de los mapas publicados:** los 71 mapas uno a uno (desvíos, demarcaciones partidas, fronteras, casos raros). Aquí se auditó el motor, no sus salidas.
- **Producto y estrategia:** para quién es, qué hace el visitante, qué falta para que otros lo usen. Solo se tocó el enlace por distrito.
- **Legal y ética:** licencias de las fuentes (ninguna de las 651 lleva licencia anotada), protección de datos del contador, neutralidad y riesgos de uso partidista.
- **Resto de laboratorios del algoritmo:** terminar la mejora local (faltan aut17, aut06 y aut03 y los 7 territorios con óptimo), ráfagas, cota propia, variantes de contigüidad, problema maestro y validación del muestreador. Salvo la mejora local parcial, ninguno se ha ejecutado.
- **Lo que quedó sin verificar** (apartado 8) y el coste real de cada nivel de la CI, que hoy es una estimación.

## 8. Límites de esta investigación

- **Sin verificar por el escéptico (4):** A1-9 (lecturas repetidas del grafo), A2-11 (diagramas de potencia), B-10 (capas retiradas en el árbol) y F-11 (robots, mapa del sitio y 404). Están en `HALLAZGOS.json` como SIN_VERIFICAR y no entran en el apartado 2. Alimentan una parte de T-525, T-548 y T-534; A2-11 no tiene tarea.
- **Laboratorio de mejora local:** parcial. 3 de 6 territorios, 2 repeticiones, sin informe escrito y sin pasar por el escéptico. No demostró óptimo local en ninguno; en nac46 agotó su tope de 900 segundos. Partió del ganador de una competición local, que puede no ser el de producción.
- **No se pudo comprobar:** las cifras de la flota de anoche (solo constan en el encargo); la configuración real del almacén R2 y los secretos y entornos de GitHub (la API responde 403 desde la nube); varias cifras de artículos externos (sitios no accesibles); una cita sobre la caché de Cloudflare, que queda «de memoria».
- **Estimaciones, no medidas:** los ahorros de la CI por niveles; el efecto de los tiempos viejos en el reparto de tests; que la mejora local sirva con exenciones o varias circunscripciones.
- **Ningún experimento del estado del arte (A2) se ejecutó.** Sus criterios dicen cómo se comprobaría cada técnica y cuándo descartarla.
- **Cifras que difieren entre informes:** el repositorio «pesa» 467 MB (GitHub), 1.068 MB (árbol en disco) o 356 MB (árbol comprimido) según qué se mida; aquí se dice cuál. `legacy/` son 152,7 MB en disco y 15,2 MB en el clon. Se ha usado siempre la cifra del escéptico.
- **Esta síntesis no volvió a verificar nada:** se apoya en el campo de verificación de cada hallazgo. Las decisiones citadas se han leído en `docs/PLAN.md`.
- **Incidente de consumo de la noche (según el encargo; no comprobable desde el repositorio):** dos flotas agotaron el límite de 5 horas; la primera, de 26 sesiones, en unos 6 minutos. Ocho investigadores con 55 llamadas cada uno cupieron después en media ventana. De ahí sale la estimación de 6 a 8 sesiones por ventana y la tarea T-511. Parte del trabajo (el laboratorio y cuatro verificaciones) quedó sin terminar por ese motivo.
