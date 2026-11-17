## 2026-11-17 — T-403 — Relevo automático de chats (D-160)

**Causa.** D-160: el relevo de chats no debe depender del propietario.
**Cambio.** Sección «Relevo» en las skills `planificador`, `coordinador`, `operador`, `implementador` e `ingeniero-motor`: umbral del 70 % con `get_session` en el propio turno, pasos del relevo (lecciones, traspaso en PR de docs, sucesora con `create_session`, avisos, confirmación y archivo), límite de linaje (profundidad ≥ 7: traspaso y prompt listos y aviso al móvil, D-122), y regla del Operador (frases D-52 anotadas en la ficha; el sucesor solo las acepta con la frase del propietario; nunca se heredan por `send_message` ni traspaso). Una línea nueva en `CLAUDE.md`; para no pasar de 99 líneas se fusionaron entradas del historial, sin perder lecciones. No amplía la autoridad de ninguna sesión.
**Pruebas.** `tests/test_t403_relevo_skills.py` (sección «Relevo» en los cinco roles, regla del Operador, CLAUDE.md < 100 líneas).
**Riesgos.** Ninguno de producto. PR `no-automerge`; sin lanzar ni publicar.
