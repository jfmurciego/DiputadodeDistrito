<!--
PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Traspaso del Planificador del 28-11 (relevo D-160)
FECHA: 2026-11-28
ESTADO: TRASPASO. No es el plan; no autoriza lanzar, publicar ni fusionar
CAMBIOS: 1.0.0 — estado al cierre de la pasada 1 de la investigación T-509
MOTIVO: el chat del Planificador supera el 70 % del umbral de contexto y su linaje es 7 de 8: la sucesora la abre el propietario
ANTERIOR: ninguna (fichero nuevo); traspaso previo en docs/TRASPASO_PLANIFICADOR_2026-11-20.md
-->

# Traspaso del Planificador — 28-11 (mediodía)

## Estado
- **T-509, investigación profunda, pasada 1: HECHA.** Rama `investigacion/2026-11-28` (sin PR, a propósito):
  `docs/AUDITORIAS/INVESTIGACION_2026-11-28/INFORME.md` (informe único), `HALLAZGOS.json` (75 hallazgos) y siete informes por
  ámbito (A1 motor, A2 estado del arte, B arquitectura, C agentes, D repositorio, E almacenamiento, F publicación).
  84 hallazgos: 16 confirmados, 64 corregidos por un escéptico independiente, 0 refutados, 4 sin verificar.
  El ámbito G (CI y seguridad) tiene su detalle **fuera del repositorio**: se entregó al propietario en su chat.
- **Propuesta del informe:** 44 tareas provisionales (T-511 a T-554) en 7 bloques, para aprobar con «sí al bloque N».
  No están en `docs/PLAN.md`. El plan vigente es el 1.0.79; T-506 a T-510 tampoco están anotadas.
- **Laboratorio L1 (mejora local exacta), PARCIAL y sin verificar:** rama `investigacion/2026-11-28-L1-mejora-local`,
  `docs/ESTUDIOS/T509_LAB_MEJORA_LOCAL/`. Tres territorios de seis: Zaragoza pasa de 8 a 3 demarcaciones partidas,
  Valencia de 26 a 19 y Alicante mejora la frontera; reglas duras cumplidas y resultado repetido en 2 ejecuciones.
  Sesión `session_01KQDtFrGbYqQyPe1YXuNFVZ`, parada por el límite.
- **Paradas, sin gasto:** 26 sesiones «INV …» (etiqueta `ddd-investigacion-2811`), solo con el esqueleto empujado a sus
  ramas `investigacion/2026-11-28-NN-*`. Archivarlas necesita el sí del propietario; podar ramas, su frase al Operador.
- **Tanda 2 (D-214), en espera por orden del Planificador:** T-491 `session_01KQDtFqnaKSwkDAFD1Q1bVG`, T-476
  `session_01KQDtFrRVLZ35tjGhqoBDWm`, T-478 `session_01KQDtFrnxucfTRKYxpWTL2J`, T-473 `session_01KQDtFuZJDND6HcaBtQGZbh`,
  T-482 `session_01KQDtFutiGehJJaMoHbqe2z`, T-501b `session_01KQDtFsofriCZkBfPReHPzA` y T-510
  `session_01KQDtFv18yrVevGz3TrQSgu`. Coordinador vigente: `session_01KQDtFsRapKvmmZaWddgWeF`; tiene orden de reanudarlas
  de una en una y con presupuesto solo cuando se le avise.
- **PR abiertas que esperan orden del propietario:** #1036 (T-508, imágenes de distritos) y #1037 (T-507, medición del exacto).
- **Regeneración del 29-11:** P30 de los 17 territorios con huella nueva y republicar los 9 con ganador nuevo (nac04, 12, 14,
  15, 23, 33, 39, 41 y 43), más nac48 si cambia (si pasa de 10 minutos en el exacto: parar e informar). Novedad de T-509:
  4 de esos 9 mapas (nac12, nac15, nac41 y nac43) son «mejor válido» bajo un tope de tiempo, no «óptimo demostrado»; el
  informe propone medir antes si se repiten (T-519 provisional). Decide el propietario.
- **Cloudflare:** el job de P40 que sube a R2 corre en el entorno `github-pages` y no ve las variables de `publicacion`:
  0 ficheros subidos en 11 publicaciones. Arreglo por código: T-510 (job propio con entorno `publicacion`).

## Decisiones que esperan al propietario
1. Bloques del informe (1 presupuesto y agentes, 2 motor, 3 conservación, 4 publicación, 5 arquitectura, 6 repositorio y CI,
   7 seguridad). El apartado 6 del informe lista lo que choca con decisiones vigentes (D-92, D-127, D-146, D-188…).
2. Medir la repetición del exacto antes de la regeneración (T-519 provisional).
3. Qué hacer con las 26 sesiones paradas y con el laboratorio L1 (terminarlo y verificarlo cuesta una sesión).
4. Segunda pasada: ciencia y método, análisis electoral, calidad numérica de los mapas, producto, legal y laboratorios.
5. D-96: el repositorio sigue público con el motor y los estudios dentro.

## Lecciones (para la skill del Planificador y `CLAUDE.md`)
- El tope real es la **ventana de 5 horas**, no el semanal. Estimación de la noche: unos 90 USD de equivalencia por ventana.
  Una sesión del modelo mayor a esfuerzo máximo gastó 11,4 USD en 6,5 minutos. Dos flotas agotaron la ventana y dejaron al
  propietario sin uso. Regla propuesta: 6 sesiones por ventana como mucho, cada una con modelo, esfuerzo y tope de llamadas.
- Lo que sí cupo: ocho investigadores locales con unas 55 llamadas cada uno (media ventana) y un solo aviso al final.
- El escéptico por informe es imprescindible: 0 refutados, pero 64 de 84 hallazgos corregidos (cifras, alcance, impacto).
- Seguridad: nunca al repositorio público; exclusión local y entrega al propietario en su chat.
- Cada turno de un chat con mucho contexto cuesta en torno a medio dólar: agrupar llamadas y relevar pronto (150.000 tokens).
- Con linaje 7 de 8, el relevo lo abre el propietario, no el chat saliente.

## Línea para abrir la sucesora
«Usa la skill planificador. Eres el relevo del Planificador (D-160). Lee, en la rama `investigacion/2026-11-28`,
`docs/TRASPASO_PLANIFICADOR_2026-11-28.md` y `docs/AUDITORIAS/INVESTIGACION_2026-11-28/INFORME.md`. No abras ni reanudes
sesiones sin presupuesto de ventana. Espera mis decisiones por bloques.»
