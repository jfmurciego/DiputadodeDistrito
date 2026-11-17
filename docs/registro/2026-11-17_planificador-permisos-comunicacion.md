## 2026-11-17 — Permisos de comunicación entre sesiones sin pregunta

- Causa: el propietario (17-11, chat del Planificador) no quiere más avisos de permiso cada vez que una sesión de rol se comunica con otra.
- Cambio: `.claude/settings.json` permite sin preguntar `send_message`, `get_session`, `list_sessions`, `list_events` y `get_event` del MCP `claude-code-remote`, y `ReadNotifications`. No incluye crear ni archivar sesiones, fusionar, lanzar ni publicar.
- Efectos: solo configuración; aplica a las sesiones que carguen la nueva versión.
