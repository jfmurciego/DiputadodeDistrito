# Traspaso del Coordinador — 17-11-2026 (relevo D-160 al 80 % del contexto)

VERSIÓN: 1.0.0 · FECHA: 2026-11-17 · ANTERIOR: `docs/TRASPASO_COORDINADOR_2026-11-16.md`

Sesiones: Coordinador saliente `session_01KQDtFu1megDcVH451BXPQv` (profundidad de linaje 6; el sucesor es la 7: NO puede crear otra sucesora, avisa al propietario con notificación al móvil, D-122) · Planificador `session_01KQDtFswfpYv5Ea53uXQyJf` · Operador `session_01KQDtFqw1LBgGn6nCuxP8Yx`. Rol: skill `coordinador`. Respuestas cortas, en español, de tú, con semáforo. No implementas, no lanzas, no publicas; no editas `docs/PLAN.md`.

## 1. AUTORIZACIONES (lo más importante)
- El propietario escribió EN EL CHAT DEL COORDINADOR SALIENTE (17-11): fusionar sin esperarle, en su orden, hasta las 23:59 (peninsular = 22:59 UTC) las PR de la migración y del histórico (T-379 PR 2a, 2b y 3, T-383, T-393, T-395, T-396, T-397, T-399, T-400 y P43) y las del plan, cada una con CI verde en la PR y en `main` y revisor conforme; la PR 2a solo con el entorno `registro` ya con sus secretos y su primera prueba en verde; no autoriza lanzar ni publicar. (Anotada como D-157.)
- Esa frase NO se hereda por traspaso ni por `send_message` (regla de CLAUDE.md y de la sección «Relevo» de #889): el sucesor SOLO fusiona cuando el propietario lo diga en SU chat (basta una frase: «la autorización de hoy vale para el Coordinador sucesor»). Hasta entonces: prepara, revisa y espera. El Planificador dice que el propietario aclaró que no dará más frases por PR porque todas están en esa lista; eso llegó por mensaje (no literal): pide la confirmación una vez.
- Antecedente: dos veces el Planificador/un implementador dio por «decisión del propietario» algo que no estaba en mi chat (opción A de 2011-11; T-399 la anotó «vía Coordinador»). Verifica siempre lo literal.
- Fuera de la lista y sin orden expresa: #889 (T-403, relevo; mecanismo de autoridad) y #888 (2a; secretos y fusión: además exige los pasos del §3).

## 2. Estado (17-11 ~10:40 UTC, `main` d251fcac en verde)
Fusionadas hoy: #865, #867, #868, #869-#872, #871, #873, #874, #875, #877, #866, #880, #881, #882, #885, #886, #887, #890, #891, #878.
| PR | Qué | Estado | Qué falta |
|---|---|---|---|
| #883 | T-399, 2011-11 con B' (D-158) + 1 % de D-161 | HEAD 8d7947b3; 44 LISTA, 5 APARTADA_VOTOS, 2 BLOQUEADA_SIN_DATO (08, 36), 1 BLOQUEADA_RELLENO (51); materializar 43/52 | delta del revisor (último sobre 072c6420: sin bloqueantes), CI verde, fusionar (en la lista; tras confirmar autorización) |
| #888 | T-379 PR 2a, opción A de D-162: P40/P70 sin partir; 22 jobs con `registro`; preparar = `produccion` personas y `registro` robots | HEAD c1ec7326; el revisor dio FAIL al HEAD anterior (partir publicar); este commit es la respuesta | revisor del delta (maquinaria de fusión y secretos: máximo rigor), CI, y los pasos del §3; NO fusionar antes |
| #889 | T-403, relevo (D-160) | HEAD 1b722ff; revisor PASS_WITH_EXCEPTIONS, CI verde | orden expresa del propietario (no está en la lista) |
| #842 | fichas del histórico | BORRADOR a propósito | no tocar |
Sesiones vivas de implementadores: T-399 `session_01KQDtFrf1w47kEZWewBmHHK` (Sonnet), T-379 PR 2a→2b→3 `session_01KQDtFrARiXXwo98der5jEu` (Opus; turno EXCLUSIVO sobre P10, P20, P30, P40, P70, P90, auto-merge, la 00 y Legislatura mientras dure la 2a), T-403 `session_01KQDtFvPpjGqhivPqt1prsq`, T-405 `session_01KQDtFr59iw276ZktDJir6B` (nac14, Córdoba 2011-11, M04 «invalid administrative component source binding»; una PR por causa; avisa antes de tocar el motor M04/N08). Los revisores independientes (subagentes) son de la sesión saliente: lanza revisores nuevos (agente `revisor`) para cada delta.
Pendientes de abrir: T-400 (provincia 35, puente de La Graciosa 3502401010 ausente del seccionado 2012; diagnóstico primero; tras #883), P43 (T-395 diseñó; implementación tras T-393), implementación de T-393 (ids `<t>_hAAAA_MM`, turno exclusivo), T-379 PR 2b y 3 (la 3 añade el job `resultado` en la 00 con ese nombre exacto y titula el issue «P00 Campaña …»; la 00 no se borra hasta tras el 29-11), T-397b parte 2 (renombrar `auto-merge.yml` y Legislatura con «_»; detrás de la 2a), T-383, nac07 Baleares (M04 «need=8 > unidades abiertas=0»), votos por hija de 2011.

## 3. Pasos del propietario para la 2a (los das tú)
1. Settings → Environments: crear `registro` (sin revisores ni temporizador; Deployment branches = solo `main`); revisar `github-pages` y `produccion` (solo `main`, sin ramas ni etiquetas extra).
2. Copiar DDD_REGISTRO_APP_ID y DDD_REGISTRO_APP_KEY a los TRES entornos, sin borrar aún los del repositorio.
3. Con la PR fusionada: frase al Operador para el primer humo desde `main` (un P10 ligero de un territorio, `p11_registrar`, y P40 «Solo el sitio»).
4. Con el humo en verde, borrar los 2 secretos del repositorio.
5. Segundo humo: el mismo P10 desde `main` debe registrar; lanzado por API desde una rama debe fallar en el job de registro.
Efecto declarado tras el 4: una 00 o P10-P30 desde una rama ≠ main falla en los jobs con la app (en la 00, `actualizar_estado` y `manifestar`).
Otros pendientes del propietario: Settings → Pages (pages-build-deployment, D-155 c); contraste aut11 del padrón; entorno `publicacion` y Zenodo (D-146); ruleset con `pruebas` (D-144); visor y 3 Releases de ensemble (T-380); borrar ejecuciones de «Pruebas de la Plataforma» tras T-383 (D-155 b); el 29-11 el re-ensayo corto con P00 (D-149).

## 4. Órdenes y decisiones recientes
D-149 migración prioridad máxima, ninguna campaña hasta terminarla; D-150 el histórico no espera; D-151 P10 un territorio por ejecución; D-152 id propio `<t>_hAAAA_MM`; D-153 secciones sin geometría; D-154 verdes y ámbar con aviso, rojas nunca; kind aparte `historico_m06/m08` (P43); D-155 lista de Actions; D-156 sustituida por D-158 (2011-11 = B': seccionado 2012, madre repartida con Atlas 2015; 5 provincias APARTADA_VOTOS; D-70 intacto); D-159 «_» en workflows sin botón (los 9 con botón «P…»); D-160 relevo automático; D-161 el 1 % cuenta solo lo movido a las hijas + lo rellenado (36 y 51 bloquean); D-162 opción A de la 2a. Coste archivado hoy (USD): T-375 10,32 · T-376 13,59 · T-377 32,04 · T-379 PR4 2,23 · T-389 2,72 · T-391 1,21 · T-392 0,62 · T-393 2,19 · T-395 3,04 · T-396 3,77 · T-397 0,58 · T-397b 0,56 · T-402 0,90.

## 5. Cómo se fusiona (lo que ha funcionado)
`gh api -X PUT repos/jfmurciego/DiputadodeDistrito/pulls/N/merge -f merge_method=squash -f sha=<40hex>`; antes: `pruebas` y `guardian` en success sobre ese SHA exacto (`check-runs?per_page=100`: por defecto salen 30 y `pruebas` va en la última página), revisor conforme sobre ese SHA, `main` en verde (último run de push completado en success), PR fuera de borrador (`mcp__github__update_pull_request draft=false`) y con `no-automerge` (REST `POST issues/N/labels`). El API puede tardar en mostrar el HEAD nuevo de una PR tras un push: comprueba con `git fetch origin <rama>`. Un fallo de `pruebas` sobre un SHA anterior no cuenta. Entre sesiones, solo `send_message` del MCP `claude-code-remote`.
