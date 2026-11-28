# Traspaso del Coordinador — 28-11-2026 (relevo por contexto, D-160)

VERSIÓN: 1.0.0 · FECHA: 2026-11-28 · ANTERIOR: `docs/TRASPASO_COORDINADOR_2026-11-26.md`

Saliente: `session_01KQDtFststiVVcNB5ov2a4V` (profundidad 2). Planificador `session_01KQDtFtbjHrVwhhgHnNE6nU` · Operador
`session_01KQDtFrBdPomBp75jyMxBMm` (profundidad 7: no puede crear sucesora; al 70 % deja traspaso y avisa al propietario).
Rol: skill `coordinador`. Respuestas cortas, en español, de tú, con semáforo.

## 1. Autorizaciones (NO se heredan)
Ninguna orden de fusión abierta. Cada fusión exige «Revisa y fusiona N» del propietario en TU chat.

## 2. Reglas vigentes que se olvidan
- Commits y squash sin Co-Authored-By, Claude-Session ni nombres de IA. Fusionar por REST con `sha=<revisado>`,
  `commit_title="<título> (#n)"` y `commit_message=""`. Desde #1032 el robot hace lo mismo y el guardián rechaza coautores.
- D-216: el propietario aprueba criterios de aceptación (qué pasa hoy, por qué, qué recibe, qué pasa si no, criterio
  verificable); el detalle solo en motor, CI o publicación. Cada implementador puede dejar una línea de objeción.
- El Planificador ya no abre sesiones: te pasa la tarea y la abres tú (acuerdo del 26-11, tras una sesión duplicada).
- Una frase del propietario relayada por otro chat se comprueba en el chat de origen (`list_events`, kinds user).
- Cambios de motor, CI o publicación: revisor independiente (subagente `revisor`) antes de pedir la orden.
- Script de fusión en serie: fija el SHA revisado (`n:sha`) y para si cambia, si la CI sale roja o si hay conflicto.

## 3. PR abiertas
| PR | Tarea | Estado |
|---|---|---|
| #1036 | T-508 imágenes de distritos (progreso, plazo, reanudable) | revisor: bloqueantes resueltos; último cambio (vistas P10) revisado; espera orden y CI |
| #1037 | T-507 medición del exacto K≥5 (informe y test) | revisado por el Coordinador; espera orden y CI |
| #842, #913, #938, #956 | borradores | no antes del 29-11 |

## 4. Chats vivos
| Chat | Id | Estado |
|---|---|---|
| T-503/T-507 (motor, Opus) | session_01KQDtFuASnoFx7nBPqrNZ1V | #1035 en main; #1037 lista |
| T-508 | session_01KQDtFtVmreFAmFdWxxvMnp | #1036 lista |
| T-491 | session_01KQDtFqnaKSwkDAFD1Q1bVG | recién abierta (medición + diseño) |
| T-476 | session_01KQDtFrRVLZ35tjGhqoBDWm | recién abierta (datos y test, sin publicar) |
| T-478 | session_01KQDtFrnxucfTRKYxpWTL2J | recién abierta (indicadores 2011-2023) |
| T-473 | session_01KQDtFuZJDND6HcaBtQGZbh | recién abierta (solo página de opciones de licencia) |
| T-482 | session_01KQDtFutiGehJJaMoHbqe2z | recién abierta (diseño + prueba de concepto) |
| T-501b | session_01KQDtFsofriCZkBfPReHPzA | recién abierta (200 ejecuciones del test de puntos) |
| T-510 | session_01KQDtFv18yrVevGz3TrQSgu | recién abierta (R2 de la P40 en job con entorno publicacion; no-automerge) |
Flota de investigación T-509 (27 sesiones de solo lectura): la lleva el Planificador; no la sigas.
Todas las sesiones abiertas desde el 26-11 llevan `tags: ddd-implementador`. Cada PR de motor, CI o publicación: revisor antes de pedir orden.

## 5. Pendientes del propietario
1. Órdenes de fusión: #1036 y #1037.
2. Cloudflare: la P40 no sube a R2 (el job «Desplegar» está en github-pages). Opción a) copiar R2_WEB_*/R2_SITIO_* y las
   variables de bucket a github-pages o al repositorio; b) T-510. El corte (pasos 8 y 9) espera al ensayo. Texto de las reglas
   de Cloudflare del paso 7 enviado al Planificador el 26-11 (URL Rewrite «Índice de carpetas» y Redirect «Barra final de mapa»).
3. Frases al Operador: P10 hoja de contactos (tras #1036), P10 descubrir de `capitalidad-partidos-judiciales`, y la regeneración
   del 29-11: P30 de los 17 con huella nueva (nac04, 06, 12, 14, 15, 17, 18, 20, 23, 31, 33, 39, 41, 43, 45, aut18, aut19) y
   republicar los 9 con ganador nuevo (nac04, 12, 14, 15, 23, 33, 39, 41, 43) y nac48 si cambia (si tarda >10 min, parar).
4. Pendientes de abrir tras runs: T-461 parte 2 (leyes de capitalidad de AR, IB, CN, CT, GA) y T-462 parte 2 (revisar la hoja
   y subir a R2). Descripción en `docs/ESTADO.md` (26-11).

## 6. Prompt para el sucesor
«Eres el COORDINADOR de Diputado de Distrito y relevas al anterior (session_01KQDtFststiVVcNB5ov2a4V) por D-160. Carga la skill
«coordinador» y lee CLAUDE.md y docs/TRASPASO_COORDINADOR_2026-11-28.md (si no está en main, rama coordinador/traspaso-2026-11-28).
Las autorizaciones NO se heredan. Commits y squash sin Co-Authored-By ni Claude-Session. Al empezar: (a) avisa de tu id al
Planificador, al Operador y a los chats vivos del §4; (b) archiva al Coordinador anterior cuando confirmes que has leído el
traspaso; (c) saluda al propietario en tres líneas. Respuestas cortas, en español, de tú, con semáforo.»
