# Estado operativo (mantiene el Coordinador)

Fecha: 2026-11-07 · Actualizar en cada PR de lecciones o de estado.

## PR abiertas
- #463 T-67 composición sección→distrito y votos por partido (`no-automerge`).
- Coordinador: roles + lecciones (esta PR, `no-automerge`).

## Runs en curso
- Ninguno conocido a las 20:10 (el Operador informa).

## Chats activos
| Chat | Tarea |
|---|---|
| Operador (session_01KQDtFqsraJQeuw8tvfQg47) | 00 Barcelona, Alicante, Málaga (desde el principio) y Andalucía (fuente acreditada); ensembles Guadalajara y 9 más; extracción M06; republicar sitio |
| Implementador nuevo (session_01KQDtFqecLysw6SpKyf7DKj) | Constructor de agentes e infraestructura; sin tarea |
| T-67 Votos por partido (session_01KQDtFtbQBvVq6db2h4Bw66) | #463; luego extracción M06 (prioridad alta: los artefactos caducan) |
| T-58 Álava (…FvRk5…) y T-64 Partidos judiciales (…FudLo…) | Inactivos al 07-11 20:10; lecciones de T-64 recogidas |

## Pendientes del propietario
- `CLAUDE_CODE_OAUTH_TOKEN` no llega a Actions (revisor saltado 20:03): ponerlo en Settings → Secrets and variables → Actions → Repository secrets.
- D-3: publicar en el visor cada provincia al terminar su 00 o todas al final (recomendado: cada una).
- Confirmar que existe el entorno `produccion` (el primer lanzamiento manual debe quedar en «Waiting»).
- Auto-merge: `disabled_manually`; reactivarlo (`PUT …/workflows/auto-merge.yml/enable`) requiere su autorización en este chat.
