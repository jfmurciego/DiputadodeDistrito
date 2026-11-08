## 2026-11-08 — T-83 B — Reagregación del histórico de generales a los distritos vigentes

Causa: D-9, D-10, D-12 y D-13 (6 generales 2011-2023 sobre los distritos vigentes, peso por población).
Cambio: `herramientas/reagregacion_historico.py` 1.0.0 (nuevo, fuera de línea): asigna las secciones INE 2025 al distrito
M06 de mayor solape, lleva votos, censo y votantes del espejo T-89 con la equivalencia de T-85 (población), redondea por
mayor resto conservando el total y escribe ganador y votos por partido en `datos/resultados/historico/<elección>/`
con `MANIFEST.json` (sha256 de espejo, seccionados, padrón y GeoJSON M06). Votos perdidos se informan, no se reparten.
Validación (Álava, Badajoz, Huesca × 6 elecciones): 0 votos perdidos, 0 secciones sin distrito, diferencia 0 con el
espejo; frente a la oficial (2019-11 y 2023, BOE) defecto del 0,25-0,72 % (CERA, tolerancia 10 %), 0 errores; el
ganador y los votos totales de 2023 coinciden con `datos/resultados/congreso_*.csv` de M08. 2011-2019-04: sin oficial local (AVISO).
Pruebas: `tests/test_reagregacion_historico.py` (6, sintéticos con valores a mano), guardián y `GovernanceHeaders`.
Riesgos: el padrón 2025 como peso (D-13); solo 3 provincias generadas; siglas sin homologar que no entran en el contraste (PSOE en Álava, SUMAR en Huesca 2023);
sin motor, contratos, workflows ni publicación; el paso A queda para después de validar.
