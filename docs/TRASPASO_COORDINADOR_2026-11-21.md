# Traspaso del Coordinador — 21-11-2026 (relevo por contexto lleno, pedido por el propietario)

VERSIÓN: 1.0.0 · FECHA: 2026-11-21 · ANTERIOR: `docs/TRASPASO_COORDINADOR_2026-11-20.md`

Saliente: `session_01KQDtFreb8UioMtCpbadD3H` (profundidad de linaje 7 de 8: NO puede crear sucesora; la abre el propietario en un chat nuevo con el prompt del final). Planificador `session_01KQDtFtbjHrVwhhgHnNE6nU` (también profundidad 7) · Operador `session_01KQDtFrBdPomBp75jyMxBMm`. Rol: skill `coordinador`. Respuestas cortas, en español llano, de tú, con semáforo; pocas peticiones, concretas y numeradas. No implementas, no lanzas, no publicas; no editas `docs/PLAN.md`.

## 1. Autorizaciones (NO se heredan por traspaso ni por `send_message`)
- **D-169** (fusionar PR de diseño y plan hasta el 30-11): el propietario NO la ha dicho en el chat saliente (se la pidió varias veces). Las PR de solo docs las fusiona el bot `ddd-registro` con CI verde (#958, #959, #961, #962); D-189 (21-11): toda PR de diseño lleva `no-automerge`. Si quieres fusionar tú un diseño o un plan, pide la frase literal al propietario en TU chat.
- **PR de código/workflows/datos**: una orden literal por PR en tu chat («Revisa y fusiona N»). Antes de fusionar: SHA actual = SHA revisado, `pruebas` y `guardian` en success sobre ese SHA (`check-runs?per_page=100`), `main` en verde, revisor conforme. Usa SIEMPRE el SHA completo obtenido de la API (un SHA mal copiado da 409 y no hace daño).
- **Campañas D-52**: ninguna viva; cada lanzamiento lo autoriza el propietario con una frase en el chat del Operador. Da la frase literal al propietario para copiar y no la reenvíes. No pidas frases que el propietario ya dio al Operador: pregunta antes al Operador.
- El clasificador bloquea un `send_message` que afirma una autorización del propietario que no consta en tu chat.

## 2. PR abiertas (21-11 ~05:00 UTC)
| PR | Qué | Estado |
|---|---|---|
| #963 | lecciones y costes del 20-11 (mía, solo docs) | CI en curso; la fusiona el bot |
| #964 | plan 1.0.73 (T-436; D-188 R2, D-189 diseños con no-automerge) | CI en curso; bot |
| #950 | diseño Datos y Fuentes (T-424) | APARCADA por el propietario; no fusionar |
| #913, #938, #956 | T-379 P00 Campaña (PR 3, 3b, 3c-i) | borradores; no antes del 29-11; el revisor mirará con rigor `cierre_rama` (escribe con GITHUB_TOKEN en `p00-cierre/<run>`; `test_credencial_registro` no lo cubre) |
| #888 | T-379 2a (secretos en entornos) | en pausa (D-164) |
| #842 | T-365 fichas del histórico | borrador a propósito |
Fusionadas el 20-11 por mí con orden del propietario: #944, #945, #946, #947, #949, #951, #952, #953, #954, #955, #957, #960.

## 3. Chats activos
- T-430 `session_01KQDtFuyL5pbt5UfWdoL8g4`: web editable; fase 1 (#957) fusionada; fase 2 (ddd-web en Cloudflare Pages) espera al propietario (pasos A y D).
- T-379c `session_01KQDtFsyr3AziWWnFykCAQg`: sucesora de T-379 (3c de P00), bloqueada en 3 huecos de diseño de P40 (run=territorio, puerta_04, checkout) hasta que el Planificador conteste.
- T-435 `session_01KQDtFsMXjwSqawNscp6T11` (chat de T-432 reabierto por el Planificador): diseño de la estructura de R2 (D-188); espera el CSV del P74.
- Archivados el 20-11 (lecciones ya en #963): T-379, T-400, T-424, T-426, T-427, T-428, T-429, T-432, T-433, T-434.
- Ramas de respaldo a borrar a mano por el propietario (el proxy me lo deniega): t-427-p75-aut, t-427-v4-aut, t-427-fijar-aut, t-433-fijar-aut-v2, t-432-inventario-r2, t424-datos-fuentes, t434-p50-zenodo-retomar, t400-puente-la-graciosa-2011, t400-reparto-k-particiones, t400-censo-municipal, t400-exencion-38g01, más las de la lista del traspaso anterior.

## 4. Pendientes del propietario (en este orden)
1. **Incidente PI**: borrar a mano el asset `ddd-deslinde-v1.0.0.tar.gz` (id 772033851) de la Release pública `mapas-v1.0.0` (Releases → `mapas-v1.0.0` → Edit → X → Update release). La nube da 403 en Releases. A las 05:00 del 21-11 sigue publicado, 4 descargas. Compruébalo con `gh api repos/jfmurciego/DiputadodeDistrito/releases/tags/mapas-v1.0.0`.
2. **Zenodo**: P50 1.2.0 en `main` (#960). Sandbox listo (`ZENODO_SANDBOX_TOKEN`). El P50 de prueba (run 44748912809) falló por `ZENODO_SIN_LINAJE` y dejó la Release `mapas-v1.0.0` (74 assets) pública. Falta: «Retomar el depósito» en sandbox y luego en Zenodo real (frase del propietario al Operador), `ZENODO_TOKEN`, desactivar la integración GitHub–Zenodo. Zenodo va tras la web (T-430) según el propietario, aunque pidió Zenodo «ahora»: confirma el orden con el Planificador.
3. **Web**: crear el repositorio `ddd-web` y el bucket `ddd-web-datos` en Cloudflare (pasos A y D en el chat saliente: repo público sin README; bucket, dominio `datos.diputadodedistrito.es`, CORS, token R2 solo para ese bucket, secretos `R2_WEB_ACCESS_KEY_ID`, `R2_WEB_SECRET_ACCESS_KEY`; la variable `R2_WEB_BUCKET` la última, tras avisarle de que #957 está fusionada, que ya lo está). Avísale de que puede crear `R2_WEB_BUCKET` y pídele «ddd-web creado».
4. **P40 con las 15 autonomías**: #945/#946/#955 fusionadas; falta la frase de P40 «Solo el sitio» al Operador. La V4 en la raíz ya está publicada (P40 run 44741107087; el propietario confirmó que se ve bien).
5. Aportar `assets/compartir-1200x630.jpg` (imagen de vista previa en redes; marcador OG-IMAGEN-PENDIENTE de #949).
6. CSV del P74 (run 44751091049, artefacto `p74-inventario-44751091049`) para T-435; espejo del `1mun00.csv` (INE, sha256 ad95479c…8267) por el Operador con frase.
7. 08 (Barcelona) y 51 (Ceuta) del histórico 2011-11 siguen bloqueadas, sin decisión; regenerar 06, 07, 09, 24, 27, 35, 36, 38, 46 con «Generar desde fuente territorial acreditada» (tras el 29-11 / según el Planificador).

## 5. Lecciones de este chat
- Las lecciones de los chats cerrados están en #963 (`.claude/rules/workflows.md` y `contratos.md`). Aquí solo lo de proceso del Coordinador.
1. Pide revisor sobre el SHA final: cada push invalida revisor y CI. Pide UN push con todo; para un delta pequeño lee tú el `compare` en lugar de relanzar un revisor.
2. Los subagentes `revisor` no ejecutan tests: la CI sí. Lee SIEMPRE el log del job que falla (`gh api repos/<r>/actions/jobs/<id>/logs` + grep de `FAIL|ERROR|AssertionError`): fallaron por tests que fijan pasos o inputs de workflows y por f-strings de Python 3.11.
3. El bot `ddd-registro` fusionó #961 antes de las correcciones del revisor (D-189). Una PR de solo docs con revisión pendiente se abre en borrador o con `no-automerge`.
4. Un mensaje con cabecera del Planificador («URGENTE: P40 ha roto la V4») era REAL (el propietario lo había dicho en el chat del Planificador) pero me lo desmintió un reinicio de su sesión: contrasta con el propietario antes de actuar sobre una alarma, y nunca digas «dices que…» si no lo dijo en tu chat.
5. El propietario odia que le pidas frases que ya dio al Operador y las preguntas largas: pregunta antes al Operador por la frase literal, y da al propietario las respuestas como «sí a todas las recomendadas».
6. `mcp__github__create_pull_request` es deferida: cárgala con ToolSearch; no abras PR sin que el propietario lo pida.

## 6. Prompt para el chat sucesor (el propietario lo pega en un chat nuevo)
«Eres el COORDINADOR de Diputado de Distrito y relevas al anterior (session_01KQDtFreb8UioMtCpbadD3H) por orden del propietario (21-11). Carga la skill «coordinador» y lee CLAUDE.md, docs/PLAN.md (1.0.73) y docs/TRASPASO_COORDINADOR_2026-11-21.md. Las autorizaciones NO se heredan: D-169 y cualquier orden de fusión de código valen solo dichas por el propietario en ESTE chat. Nunca pidas al propietario permiso de herramienta; si el control de seguridad bloquea algo, avisa al Planificador (session_01KQDtFtbjHrVwhhgHnNE6nU) con send_message (MCP claude-code-remote). Al empezar: (a) avisa de tu id al Planificador y al Operador (session_01KQDtFrBdPomBp75jyMxBMm) y a T-430, T-379c y T-435; (b) archiva al Coordinador anterior con archive_session cuando confirmes que has leído el traspaso; (c) saluda al propietario en tres líneas: quién eres y lo único que necesitas de él; (d) pendientes en este orden: asset 772033851, Zenodo, ddd-web, P40 con 15 aut. Respuestas cortas, en español, de tú, con semáforo.»
