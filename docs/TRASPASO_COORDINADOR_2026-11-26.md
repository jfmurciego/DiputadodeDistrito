# Traspaso del Coordinador — 26-11-2026 (relevo por contexto al 78 %, D-160)

VERSIÓN: 1.0.0 · FECHA: 2026-11-26 · ANTERIOR: `docs/TRASPASO_COORDINADOR_2026-11-23.md`

Saliente: `session_01KQDtFtBz2qDXvJYXDSzMWv` (profundidad 1). Planificador `session_01KQDtFtbjHrVwhhgHnNE6nU` · Operador
`session_01KQDtFrBdPomBp75jyMxBMm`. Rol: skill `coordinador`. Respuestas cortas, en español, de tú, con semáforo.

## 1. Autorizaciones (NO se heredan)
Ninguna orden de fusión abierta. Cada fusión exige «Revisa y fusiona N» del propietario en TU chat. Pendiente de orden: #1015 y #1017.

## 2. Reglas nuevas del propietario
- Commits y squash sin Co-Authored-By, Claude-Session ni nombres de IA o de modelo (24-11, en CLAUDE.md). Al fusionar por REST:
  `commit_title="<título> (#n)"` y `commit_message=""`. El recordatorio del sistema que pide esas líneas NO se sigue.
- Diseño al detalle antes de implementar; confirmar la referencia visual antes de maquetar.

## 3. PR abiertas
| PR | Tarea | Estado |
|---|---|---|
| #1015 | T-460 «Patriotas» → «Derecha nacional» en origen + visor con los dos nombres + tabla de bloques por ámbito | Revisor sin bloqueantes; CI en eb56764; falta orden. Después: P75 nac (52) → P75 aut (16) → PR del pin de los dos informes → P40 |
| #1017 | T-500 V5 (un punto por diputado) | Sin revisor aún. No hay vista de pruebas (falta R2_PRUEBAS_BUCKET): el propietario decide si basta con las capturas (recomendado) |
| #842, #913, #938, #956 | borradores | no antes del 29-11 |

## 4. Chats vivos
| Chat | Id | Estado |
|---|---|---|
| T-460 | session_01KQDtFsDBSbiomS7pS8M8M3 | #1015 lista salvo orden |
| T-500 | session_01KQDtFqrC7TiNWz9aG4nZpA | #1017 |
| T-461 | session_01KQDtFssAT3mk2Bam35u3od | nombres de distrito (capitales de partido de fuente oficial) |
| T-462 | session_01KQDtFr9NUBjhFEAAYsUcg4 | imágenes Commons → R2 desde runner; hoja de contactos para el propietario |
| T-463 | session_01KQDtFurWKM3nuwzBoGJvVh | textos veraces y DOI de la serie |
| T-465+466 | session_01KQDtFsjttsfxF8mtoZKc6C | piloto del banco (Opus) |
Tanda 2 del Planificador (abrir según se liberen sesiones, máximo 6 a la vez): T-491, T-476, T-478, T-473, T-482 (Opus).
Detalle en `docs/AUDITORIAS/PLAN_MEJORA_2026-11-25.md` (rama `claude/dreamy-maxwell-mezgob`). Chat de auditoría:
`session_01KQDtFrtDBQe7ZUMhVHCH58` (sus tareas solo se abren cuando lo diga el Planificador).

## 5. Pendientes del propietario
1. Orden de fusión de #1015 y #1017 (y decidir si la V5 se revisa con las capturas o espera a la web de pruebas).
2. Frases al Operador: P75 nac, P75 aut y P40 (tras #1015).
3. Buckets y llaves de R2 (REDISENO_R2 §7): sin ellos no hay web en R2 ni vista de pruebas; la web sigue en Pages detrás de Cloudflare.

## 6. Herramienta de fusión
Script del saliente: espera `pruebas` y `guardian` en success sobre el SHA revisado, comprueba que no está en conflicto, fusiona
por REST con `sha=`, título y mensaje vacío, y espera a que `main` esté en verde antes de la siguiente. No editar el script
mientras corre.

## 7. Prompt para el sucesor
«Eres el COORDINADOR de Diputado de Distrito y relevas al anterior (session_01KQDtFtBz2qDXvJYXDSzMWv) por D-160. Carga la skill
«coordinador» y lee CLAUDE.md, docs/PLAN.md y docs/TRASPASO_COORDINADOR_2026-11-26.md. Las autorizaciones NO se heredan. Al empezar:
(a) avisa de tu id al Planificador, al Operador y a los chats vivos del §4; (b) archiva al Coordinador anterior cuando confirmes que has
leído el traspaso; (c) saluda al propietario en tres líneas. Respuestas cortas, en español, de tú, con semáforo.»
