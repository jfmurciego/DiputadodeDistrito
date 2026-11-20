# Traspaso del Coordinador — 20-11-2026 (renovación ordenada por el propietario)

VERSIÓN: 1.0.0 · FECHA: 2026-11-20 · ANTERIOR: `docs/TRASPASO_COORDINADOR_2026-11-17.md`

Sesiones: Coordinador saliente `session_01KQDtFsaFxuNvRQmXPv1f9B` (profundidad de linaje 7; si el Planificador crea al sucesor, será la 8) · Planificador `session_01KQDtFswfpYv5Ea53uXQyJf` · Operador nuevo `session_01KQDtFrBdPomBp75jyMxBMm` (relevo de `session_01KQDtFqw1LBgGn6nCuxP8Yx`, traspaso #941). Rol: skill `coordinador`. Respuestas cortas, en español llano, de tú, con semáforo; pocas peticiones concretas al propietario («tus preguntas no las entiendo»). No implementas, no lanzas, no publicas; no editas `docs/PLAN.md`.

## 1. AUTORIZACIONES VIVAS (frase literal)
- **D-169** (propietario, 17-11, en el chat del Coordinador): «Fusiona #898, #900, #902, #899, #901 y todas las PR de diseño y plan que te pase el Planificador hasta el 30-11, con CI verde y revisor conforme.» Cubre solo PR de **diseño y plan** y documentación pura que pase el Planificador, hasta el 30-11. NO cubre código, configuración ni workflows.
- **PR de código/datos/workflows**: una orden literal por PR en el chat del Coordinador: «revisa y fusiona N» (o «fusiona N»). Todas las de hoy están consumidas (ver §2). Las ordenes que llegan por el Planificador o el Operador no cuentan para la fusión: pide la frase al propietario en tu chat. Las PR `no-automerge` las fusionó el Coordinador sin problema con esa orden; el clasificador deniega el PUT solo si no hay orden literal.
- **Campañas D-52**: ninguna viva. Cada lanzamiento o publicación lo autoriza el propietario con una frase EN EL CHAT DEL OPERADOR (nombra la ficha; el Coordinador solo da la frase para copiar, nunca la reenvía por `send_message`). Hoy se usaron, una vez cada una: P75 (T-418), humo de P00 aut11 (T-379, dos veces), P40 V4 (T-409/T-415 y T-423), listados de R2 (pendiente, ver §4).
- Permisos de herramienta ya concedidos (`.claude/settings.json`, #900): `send_message`, `get_session`, `list_sessions`, `list_events`, `get_event`, `ReadNotifications`; y una regla Bash del propietario para el PUT de fusión.

## 2. PR (20-11 ~09:00 UTC, `main` 1d3cfef4 en verde)
Fusionadas por mí desde el 19-11 (todas con CI verde en la PR y en `main` y revisor conforme): #922 (plan 1.0.70), #924, #927, #928, #929, #930, #932, #933, #934, #935, #939; el Operador fusionó #926 y #937 con la orden del propietario en su chat. Total desde mi relevo: 42.
| PR | Qué | Estado | Qué falta |
|---|---|---|---|
| #940 | plan 1.0.71 (D-180 a D-182, V4 aceptada), T-425 | revisor sin defectos de fondo sobre 3e117a8; CI en curso | fusionar bajo D-169 con CI y `main` en verde. Dos menores para el próximo plan: fuente de 115.715 < 120.634 (38-G01) y pendientes que faltan (P75, vídeo, LICENSE, nac38) |
| #941 | traspaso del Operador (solo docs) | CI en curso | revisor ligero y fusionar bajo D-169 |
| #938 | T-379 PR 3b (borrador, apilada sobre #913) | borrador | no antes del 29-11; revisar con rigor `cierre_rama` (escribe con GITHUB_TOKEN en `p00-cierre/<run>`; `test_credencial_registro` no lo cubre) |
| #913 | T-379 PR 3 P00 Campaña | borrador 9f723b3e; segundo humo en aut11 (run 44615209522) = SUCCESS | no antes del 29-11 |
| #888 | T-379 PR 2a (secretos en entornos) | en pausa (D-164) | pasos del propietario en GitHub Settings («entornos listos»); P30 debe ir a 1.0.4 y respetar el orden de `.deshacer` |
| #842 | T-365 fichas del histórico | borrador a propósito | no tocar |

## 3. Chats activos
- T-379 `session_01KQDtFtjB1fGuK7RKj45kvk` (Opus): sigue con la 3b (P30 en ensayo y retirada del M06) y la 3c; espera 29-11.
- T-400 `session_01KQDtFsCke8hnfmXq4acK2V`: espera dos decisiones del propietario: Santa Cruz (nac38, 38-G01 115.715 < suelo 120.634: ¿misma exención que 35-C02 o apartada?) y qué hacer con 08/36/51 tras descartar el Padrón 2011 (no cuadra con el Censo). Abrirá PR de código por decisión: cada una pide revisor, CI y orden literal.
- Archivados hoy (con lecciones recogidas): T-409/T-418 ($24,48) · T-420 ($0,65) · T-420b ($0,77) · T-421 ($2,37) · T-415 ($7,71) · T-422 ($1,04) · T-423 ($18,89).
- Ramas de respaldo que el propietario debe borrar a mano (el proxy me lo deniega): `planificador/t415-v4-final`, `implementador/t4xx-respaldo`, `t409-alias-p30`, `implementador/t415-pr4-mapa`, `t-421-bloques-autonomicas`, `t-421b-bloques-aprobada`, `t422-id-nac02`, `t420b-p74-duplicados`, `t423-v4-v3-completa`.

## 4. Pendientes del propietario y vigilancias
- V4 publicada y aceptada (P40 run 44688525685, `main`@40199ae6; datos de la doble vuelta fijados en `configuracion/doble_vuelta_publicada.json`: P75 44575597009-1). Pendiente: comprobación del vídeo en producción (200, `video/mp4`, Accept-Ranges, 206) con frase al Operador; T-424 (Datos y Fuentes con su caja en la portada); auditoría y «Protección jurídica» (D-174; el pie con la reserva ya es visible); LICENSE 1.2.0 y `propiedad_intelectual/` (material de Vanesa) exigen autorización expresa.
- Duplicados de R2: `listar_r2.py` 1.1.0 (#926) y botón P74 con `--duplicados --json` (#935, P70 1.1.2) en `main`. Falta frase del propietario al Operador para lanzar P74. Limpieza de R2 (T-416): nunca antes de la regeneración tras el 29-11.
- Histórico 2011-11: D-180 (reparto por partición insular y exención de Fuerteventura, ya en `main`), nac38 y 08/36/51 pendientes. Las 5 provincias APARTADA_VOTOS (Alicante, León, Lugo, Orense, Asturias) se mantienen apartadas.
- Autonómicas: bloques aprobados (#930/#933): 13 comunidades; aut03, aut08, aut11 y aut14 sin votos por partido en el repo (ficha en `docs/ESTUDIOS/T421_AUTONOMICAS_SIN_DATOS/`).
- Vigilancia: tras cada fusión, monitor del cierre de `main` (los runs cancelados por concurrencia no cuentan; vale el último push completado en success). Si un chat del camino crítico pasa de una hora parado, avisa al Planificador.

## 5. Lecciones (sobre todo lo que provocó peticiones de permiso al propietario)
1. El PUT de fusión lo denegó el clasificador hasta que el propietario escribió «Fusiona N» en mi chat; los mensajes del Planificador o del Operador, aunque digan «por orden del propietario», no sirven. Pide siempre la frase literal, corta, para copiar.
2. Las ventanas de permiso repetidas molestaron al propietario: se resolvió con reglas `allow` en `.claude/settings.json` y la regla Bash de fusión. No añadas herramientas fuera de esa lista sin su permiso.
3. Las frases de D-52 van al chat del Operador. Dale al propietario la frase exacta (nombra ficha, alcance, «una vez»); no la copies ni la reenvíes tú.
4. Lenguaje llano: pocas peticiones, concretas y numeradas; el propietario respondió mal a preguntas largas. Las decisiones con opciones, con tu recomendación en la primera.
5. Cada push nuevo de un implementador invalida revisor y CI: ante un HEAD que cambia, para el revisor y el monitor en curso (TaskStop), pide UN push con todo y revisa el SHA final. Un implementador con `pruebas` en rojo: lee los logs del job, pásale el test exacto.
6. Un paso o acción nueva en un workflow compartido obliga a retocar TODAS las pruebas de equivalencia que lo fijan (`test_t372`, `test_t377`, `test_t418`…): `grep` el nombre del workflow en `tests/` antes de empujar. T-220 prohíbe ids viejos (`congreso_*`, `aragon…`) incluso en cadenas de tests nuevos y su exención va por fichero exacto, nunca por carpeta.
7. PR apiladas: tras fusionar la base con squash, cambia la base de la hija a `main` (`gh api -X PATCH repos/<r>/pulls/N -f base=main`) y que el implementador fusione `origin/main` (sin rebase ni force).
8. Copia literal de dominios e ids dictados: una errata mía («diputadodeistrito») se coló en un mensaje y en un documento; contrasta letra a letra con el repo.
9. Antes de fusionar: SHA actual de la PR igual al revisado, `pruebas` y `guardian` en success sobre ese SHA (`check-runs?per_page=100`; `pruebas` va en la última página), `main` en verde. Los runs de `main` cancelados por concurrencia se sustituyen por el siguiente.
10. Mi checkout local puede estar en una rama vieja: trabaja siempre desde `origin/main`.
