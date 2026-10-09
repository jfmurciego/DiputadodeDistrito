# G10 por dentro: guía de bajo nivel

Versión: 1.1.0 · Fecha: 13-09-2026
Anterior: legacy/docs/ORQUESTACION/G10_GUIA_BAJO_NIVEL_v1.0.0.md

G10 desacopla los runners de GitHub de las ventanas del agente. Cada tarea lleva huella, contrato de éxito, artefactos y estado.

| Capa | Estado |
|---|---|
| Planes versionados y matriz paralela sin fail-fast | Activo |
| Admisión por huella y reutilización | Activo |
| Estado durable por tarea | Activo |
| Checkpoints autorizados | Activo |
| Informe JSON/Markdown de reenganche | Activo |
| Publicación MapLibre | Activa; Pages requiere habilitación inicial |
| Recalcular M01–M06 por rutina | Prohibido |

Una tarea SUCCESS o REUSED no se repite. Un bloqueo aísla sólo su tarea. Extremadura no se promociona. El informe operativo es la fuente de reenganche humana y de máquina.
