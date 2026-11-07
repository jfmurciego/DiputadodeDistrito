## 2026-11-07 — T-78 — Gobierno de agentes en runtime: allowlist por rol y revisor obligatorio

- Causa: la autoridad de revisor, forense y Operador dependía solo de la instrucción del prompt.
- Cambio: hook `.claude/hooks/rol_herramientas.py` 1.0.0 cableado en `.claude/settings.json` (matcher `*`): revisor y
  forense (por `agent_type`) quedan en solo lectura (Bash con allowlist, sin edición ni MCP de escritura); el Operador
  (`DDD_ROL=operador` en su entorno) no puede editar ficheros. `disallowedTools` en los subagentes y `permissions.deny`
  de crear/bifurcar repositorios. `docs/ARQUITECTURA/GOBIERNO_RUNTIME.md` 1.0.0: matriz, lo que no se puede restringir
  y el JSON del ruleset `proteger-main` para exigir `veredicto` (lo aplica el propietario).
- Hallazgo: los `hooks` del frontmatter de subagentes no se disparan en Claude Code 2.1.319; el hook global sí recibe `agent_type`.
- Pruebas: `tests/test_t78_rol_herramientas.py`; en runtime real (`claude -p`), un subagente revisor intentó
  `git commit` y lo bloqueó el hook; Write con `DDD_ROL=operador` bloqueado.
- Riesgos: sin `DDD_ROL` el Operador no queda restringido; la allowlist de Bash puede frenar un comando de lectura
  no previsto en revisor/forense (se amplía en `LECTURA`).
