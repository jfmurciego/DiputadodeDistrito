## 2026-11-07 — T-48 — Revisor y forense en CI

Causa: el revisor (T-39) y el forense (T-40) solo corrían a mano desde un chat. Cambio: dos workflows nuevos, sin
botón manual y con `anthropics/claude-code-action` fijada por SHA (v1). «Revisor de PR» (`revisor-pr.yml`): en cada
PR del repositorio que no sea borrador, el revisor (Sonnet, solo lectura, `--json-schema`) deja su veredicto ligado
al SHA del HEAD en un comentario fijo y en el resumen; el job falla si da FAIL (no es check obligatorio). «Forense
de la 00» (`forense-00.yml`): cuando una 00 termina en failure, el forense lee anotaciones y `diagnostico/auto/` y
abre un issue con la causa en cinco líneas (uno por run); no relanza nada. En ambos, el agente corre con permisos
de solo lectura y la publicación en un job aparte con un único permiso de escritura; sin el secreto
`CLAUDE_CODE_OAUTH_TOKEN` se saltan limpiamente. Pruebas: `tests/test_agentes_ci.py` (4) y los tests de workflows
(credencial, sintaxis, concurrencia, diseño A, seguridad) en verde. Primera entrada del registro por fichero (T-46).
