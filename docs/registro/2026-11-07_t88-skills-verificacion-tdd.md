## 2026-11-07 — T-88 — Skills de verificación de plan y TDD incorporadas a implementador y planificador

Causa: revisar las skills `tdd` y `grilling` de mattpocock/skills (MIT) y llevar solo lo que faltaba.
Cambio: `implementador` añade rebanadas verticales, pruebas por interfaz pública y valor esperado independiente
(anti-tautológico); `planificador` añade la verificación del plan (hechos buscados, preguntas numeradas en una ronda con
recomendación). Se descartó lo ya cubierto (rojo/verde, revisión independiente) y lo que añade coste (sesiones de
interrogatorio, `GLOSSARY.md`, seams acordados con el usuario por test). Sin skills externas instaladas; sin cambios de autoridad.
Pruebas: `GovernanceHeaders` y guardián. Riesgos: ninguno (solo texto de skills).
