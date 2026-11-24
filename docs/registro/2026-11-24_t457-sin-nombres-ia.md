## 2026-11-24 — T-457 — Sin nombres de IA ni de modelo en commits ni en los textos de los robots
- Causa: orden del propietario (24-11): ningún commit lleva Co-Authored-By ni Claude-Session ni nombres de IA o de modelo; los comentarios de los robots de la PR nombraban «Sonnet».
- Cambio: `CLAUDE.md` (regla de commits y squash, 99 líneas); `revisor-pr.yml` 1.1.3 («Revisor automático (solo lectura)») y `p90-automatico.yml` 1.5.3 («Forense automático (solo lectura; …)»), con copia en `legacy/`; `test_t379_p90_ia_cierre.py` con el pie nuevo y `tests/_t430d.deshacer_nombre_ia` para la equivalencia con la 1.4.0 congelada (fixture intacto).
- Pruebas: `test_t379_p90_ia_cierre`, `test_t379_2a_entorno_registro`, gobernanza R015 y suite completa.
- Efecto: solo texto de comentarios; no cambia motor, huellas ni disparadores.
