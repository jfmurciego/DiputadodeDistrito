## 2026-11-18 — T-413 — Diseño del visor de la doble vuelta

**Causa.** D-167/D-168: el visor debe mostrar por distrito los escenarios `dv_A`, `dv_B` y `dv_base`.
**Cambio.** `docs/ESTUDIOS/T413_VISOR_DOBLE_VUELTA/DISENO.md` y `maquetas.html` (HTML estático): selector, colores con contraste y modo oscuro, ficha de distrito, leyenda y texto de la regla, datos y registro, territorios sin votos por partido, móvil, tests, orden de PR y 10 preguntas con recomendación. Solo documentación; sin código, `web/`, `visor/`, workflows ni datos.
**Pruebas.** Contrastes calculados (WCAG); comprobaciones de gobernanza y guardián.
**Riesgos.** Ninguno de producto. PR `no-automerge`; sin lanzar ni publicar.
