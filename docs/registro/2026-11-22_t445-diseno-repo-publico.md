## 2026-11-22 — T-445 — Diseño del repositorio público aparte, solo de publicación

- Causa: el código de Deslinde es público aunque D-94 lo declara privado; antes de poner el repositorio en privado (D-193) hace falta
  un repositorio público solo de publicación (mapas y datos abiertos) del que salgan la Release de mapas y el depósito de Zenodo.
- Cambio: `docs/ESTUDIOS/T445_REPO_PUBLICO/DISENO.md` 1.0.0 (solo documento): nombre y estructura, lista blanca con guardas, puente
  de la P50 con una app de solo `contents: write` en el público, Zenodo por la API conservando el concepto 10.5281/zenodo.24093967,
  copia de las Releases `mapas-v1.0.0` y `mapa-congreso_huesca-v1.0.0`, qué deja de leerse al pasar a privado, riesgos, orden y
  10 preguntas al propietario.
- Pruebas: no aplica (sin código).
- Riesgos: ninguno al fusionar; la implementación espera la aprobación del propietario.
