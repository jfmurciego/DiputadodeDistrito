# Estado operativo (mantiene el Coordinador)

Fecha: 2026-11-07 (noche) · Actualizar en cada PR de lecciones o de estado.

## PR abiertas
- Ninguna de producto. #464 (roles) y #467 (revert de #462) fusionadas. Auto-merge activo y verificado (#465: `pruebas` 20:16:54, fusión 20:17:25).

## Runs en curso (aprobados por el propietario)
- 00 Barcelona 42409499602, Alicante 42409605030, Málaga 42409615215 («Ejecutar desde el principio», `territorial_only`+`cadena_electoral`, sin publicar).
- 00 Andalucía 42409764232 («Generar desde fuente territorial acreditada», electoral, sin publicar).

## Chats activos
| Chat | Tarea |
|---|---|
| Planificador (session_01KQDtFsB1xxRnUwERbZc1pQ) | Ola nueva: prioridades y tareas |
| Operador nuevo (session_01KQDtFrT2bfmm9SyeaFmTBq) | Relevo del anterior; sin permisos hasta que los dé el propietario. Pendiente: ensembles T-61, publicar cada provincia al acabar su 00 (D-3), sitio completo |
| Implementador (session_01KQDtFrJjXiGDMASdLPo1ZK) | Agentes, infraestructura y motor; sin tarea |
| T-64 Comarcas frente a partidos judiciales (session_01KQDtFtP8ktEcpGjEB2mC7p) | Estudio, red abierta (ine.es, mapa.gob.es, idescat.cat); sin cambiar C-13 |

## Decisiones del propietario (07-11 noche)
- D-3: se publica cada provincia al terminar su 00. Histórico 2019-11: todavía no. T-70 (D'Hondt) descartada.
- #462 (partidos judiciales) revertida hasta el estudio de T-64. T-71 (reconstruir composición de 47 provincias): en espera de decisión.
- Composición M06 recuperada en 16/63; no recuperables: 45 provincias + Ceuta y Melilla (artefactos caducados).

## Pendientes del propietario
- Approve en `produccion` de los runs que queden en `waiting`; permisos de lanzar/publicar al Operador nuevo (ensembles T-61, publicaciones por provincia, sitio completo).
- Comprobar que el revisor corre en la próxima PR (secreto `CLAUDE_CODE_OAUTH_TOKEN` actualizado).
