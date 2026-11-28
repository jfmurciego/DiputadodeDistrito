<!--
PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Traspaso del Planificador del 28-11 (relevo D-160)
FECHA: 2026-11-28
ESTADO: TRASPASO. No es el plan; no autoriza lanzar, publicar ni fusionar
CAMBIOS: 1.0.0 — estado al 28-11 por la noche, tras el «sí a todo» del propietario (D-217)
MOTIVO: el chat del Planificador supera el 70 % del umbral de contexto y su linaje es 7 de 8: la sucesora la abre el propietario
ANTERIOR: ninguna (fichero nuevo); traspaso previo en docs/TRASPASO_PLANIFICADOR_2026-11-20.md
-->

# Traspaso del Planificador — 28-11 (noche)

## Estado
- **«Sí a todo» del propietario (28-11, D-217).** Aprobados los siete bloques del informe de T-509 (T-511 a T-554), medir la
  repetición del exacto (T-519), terminar el laboratorio L1, archivar las sesiones paradas y el relevo. Está en
  `docs/PLAN.md` 1.0.80. Lo que cambia una decisión vigente (apartado 6 del informe) **no** entra en ese sí.
- **T-509, investigación profunda, pasada 1: HECHA.** Rama `investigacion/2026-11-28` (sin PR, a propósito):
  `docs/AUDITORIAS/INVESTIGACION_2026-11-28/INFORME.md` (informe único), `HALLAZGOS.json` (75 hallazgos) y siete informes por
  ámbito (A1 motor, A2 estado del arte, B arquitectura, C agentes, D repositorio, E almacenamiento, F publicación).
  84 hallazgos: 16 confirmados, 64 corregidos por un escéptico independiente, 0 refutados, 4 sin verificar.
  El ámbito G (CI y seguridad) tiene su detalle **fuera del repositorio**: se entregó al propietario en su chat.
  La copia de este traspaso que hay en esa rama es anterior: vale esta.
- **T-519, EN CURSO** en un workflow local del chat saliente: rama `t519-repeticion-exacto` (sin PR),
  `docs/ESTUDIOS/T519_REPETICION_EXACTO/`. Mide nac12, nac15, nac20, nac41 y nac43 con la máquina en reposo, con un solo
  núcleo y con carga; un verificador independiente repite una muestra. El resultado va al propietario antes de la regeneración.
- **Laboratorio L1 (mejora local exacta), REANUDADO:** rama `investigacion/2026-11-28-L1-mejora-local`,
  `docs/ESTUDIOS/T509_LAB_MEJORA_LOCAL/`, sesión `session_01KQDtFrGbYqQyPe1YXuNFVZ`, con tope de 40 llamadas; cierra con el
  Coordinador. Tres territorios de seis hechos: Zaragoza pasa de 8 a 3 demarcaciones partidas, Valencia de 26 a 19 y Alicante
  mejora la frontera. Sin verificar todavía: el verificador de T-519 repite Zaragoza (`VERIFICACION_L1_ZARAGOZA.md`, en la
  rama de T-519).
- **Ventana 1 (28-11):** T-511 (presupuesto de ventana) y T-512 (libro de costes), encargadas al Coordinador: una sesión
  cada una, modelo `sonnet`, esfuerzo `high` y tope de 70 llamadas. T-551 son ajustes de GitHub que hace el propietario
  (resumen privado).
- **Archivadas** las 26 sesiones «INV …» (etiqueta `ddd-investigacion-2811`). Quedan sus ramas de esqueleto
  `investigacion/2026-11-28-NN-*`: podarlas necesita la frase del propietario al Operador.
- **Tanda 2 (D-214), en espera por orden del Planificador:** T-491 `session_01KQDtFqnaKSwkDAFD1Q1bVG`, T-476
  `session_01KQDtFrRVLZ35tjGhqoBDWm`, T-478 `session_01KQDtFrnxucfTRKYxpWTL2J`, T-473 `session_01KQDtFuZJDND6HcaBtQGZbh`,
  T-482 `session_01KQDtFutiGehJJaMoHbqe2z`, T-501b `session_01KQDtFsofriCZkBfPReHPzA` y T-510
  `session_01KQDtFv18yrVevGz3TrQSgu`. Coordinador vigente: `session_01KQDtFsRapKvmmZaWddgWeF`; tiene orden de reanudarlas
  de una en una y con presupuesto solo cuando se le avise.
- **PR abiertas que esperan orden del propietario:** #1036 (T-508, imágenes de distritos), #1037 (T-507, medición del exacto)
  y la del plan 1.0.80 (rama `planificador/plan-1-0-80`).
- **Regeneración del 29-11:** P30 de los 17 territorios con huella nueva y republicar los 9 con ganador nuevo (nac04, 12, 14,
  15, 23, 33, 39, 41 y 43), más nac48 si cambia (si pasa de 10 minutos en el exacto: parar e informar). 4 de esos 9 mapas
  (nac12, nac15, nac41 y nac43) son «mejor válido» bajo un tope de tiempo, no «óptimo demostrado»: T-519 mide si se repiten.
  Si las huellas cambian, esos territorios necesitan otra regla antes de publicarse (decide el propietario, D-215).
  La víspera no se toca el motor, la CI de producción ni las reglas de la rama.
- **Cloudflare:** el job de P40 que sube a R2 corre en el entorno `github-pages` y no ve las variables de `publicacion`:
  0 ficheros subidos en 11 publicaciones. Arreglo por código: T-510 (job propio con entorno `publicacion`).

## Decisiones que esperan al propietario
1. Apartado 6 del informe, decisión por decisión y cuando llegue la tarea que la toca: D-92, D-127, D-143, D-146, D-160,
   D-188, D-49, la copia en `legacy/` y «sin vigilantes».
2. Según salga T-519: qué regla siguen los territorios del exacto que no se repitan, antes de publicarlos (D-215).
3. La orden de fusión de #1036 y #1037, y si el informe de T-509 entra en `main` (hoy está solo en su rama).
4. Segunda pasada: ciencia y método, análisis electoral, calidad numérica de los mapas, producto, legal y laboratorios.
5. D-96: el repositorio sigue público con el motor y los estudios dentro.

## Orden por ventanas (D-217)
Como mucho 6 sesiones por ventana de 5 horas, cada una con modelo, esfuerzo y tope de llamadas. Ventana 2 (tras la noche del
29-11): T-527, T-528, T-529, T-550 y T-533. Ventana 3: T-530, T-554 y T-544; solo después se autoriza el borrado de R2.
El resto, en el apartado 5 del informe y en el estado de cada tarea del plan.

## Lecciones (para la skill del Planificador y `CLAUDE.md`)
- El tope real es la **ventana de 5 horas**, no el semanal. Estimación de la noche: unos 90 USD de equivalencia por ventana.
  Una sesión del modelo mayor a esfuerzo máximo gastó 11,4 USD en 6,5 minutos. Dos flotas agotaron la ventana y dejaron al
  propietario sin uso. Regla vigente (D-217): 6 sesiones por ventana como mucho, cada una con modelo, esfuerzo y tope de llamadas.
- Lo que sí cupo: ocho investigadores locales con unas 55 llamadas cada uno (media ventana) y un solo aviso al final.
- El escéptico por informe es imprescindible: 0 refutados, pero 64 de 84 hallazgos corregidos (cifras, alcance, impacto).
- Seguridad: nunca al repositorio público; exclusión local y entrega al propietario en su chat.
- Cada turno de un chat con mucho contexto cuesta en torno a medio dólar: agrupar llamadas y relevar pronto (150.000 tokens).
- Con linaje 7 de 8, el relevo lo abre el propietario, no el chat saliente.

## Línea para abrir la sucesora
«Usa la skill planificador. Eres el relevo del Planificador (D-160). Lee `docs/TRASPASO_PLANIFICADOR_2026-11-28.md` y la
decisión D-217 de `docs/PLAN.md` (en `main`; si la PR del plan 1.0.80 no está fusionada, en la rama
`planificador/plan-1-0-80`) y, en la rama `investigacion/2026-11-28`, `docs/AUDITORIAS/INVESTIGACION_2026-11-28/INFORME.md`.
Como mucho 6 sesiones por ventana de 5 horas. Empieza por el estado de T-519 y dime qué toca.»
