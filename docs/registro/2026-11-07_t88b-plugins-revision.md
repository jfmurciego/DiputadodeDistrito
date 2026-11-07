## 2026-11-07 — T-88 (ampliación) — Plugins oficiales de revisión y desarrollo frente a revisor e implementador

Causa: comparar `code-review`, `pr-review-toolkit` y `feature-dev` (anthropics/claude-plugins-official, donde viven ahora
los de claude-code) con `revisar-pr`, el revisor de CI e `implementador`; adoptar solo lo que faltaba.
Cambio: el revisor y `revisar-pr` añaden el punto 10, fallos silenciosos (del `silent-failure-hunter`). Ya cubierto:
revisión independiente con SHA, cumplimiento de CLAUDE.md, rojo/verde, preguntas previas (planificador). No adoptado por
coste o encaje: validación de cada hallazgo con subagentes Opus, 4-6 agentes en paralelo, exploración y arquitectura con
varios agentes, analizadores de comentarios y de tipos, comentarios en línea automáticos. Nada instalado; sin cambio de autoridad.
Pruebas: guardián y `GovernanceHeaders`. Riesgos: el revisor podría marcar algo más; recalibrar con `evals/oro/` si la CI del
revisor da falsos positivos.
