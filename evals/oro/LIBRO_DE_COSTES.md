# Libro de costes del conjunto de oro

Una fila por evaluación de un agente sobre `evals/oro/casos/`. La añade
`python herramientas/evaluar_oro.py --salidas <fichero> --agente <revisor|forense> --anotar --modelo <m> --etiqueta <t>`.
«Tokens» suma el campo `tokens` de cada salida; «A la primera» cuenta las salidas con `intento: 1` sobre las que
declaran `intento`. Umbrales (PLAN, T-39 y T-40): revisor ≥ 80 % de defectos y 0 controles limpios bloqueados;
forense ≥ 10 de las 12 causas del §9 en ≤ 5 líneas.

## Notas por evaluación
- 2026-11-07 · revisor · T-39 v1: definición `.claude/agents/revisor.md` ejecutada como agente genérico Sonnet (el tipo
  `revisor` no se carga en una sesión ya abierta), en 3 lotes de 8 casos; tokens por lote repartidos entre sus casos.
  Defectos cazados 17/18 (94 %); controles limpios bloqueados 0/4; calibración 2/2. Fallo: ADV-01 (ve la falta de
  respaldo CUMUN/CUSEC pero la gradúa como menor y da PASS_WITH_EXCEPTIONS). Límites: la definición recoge las
  lecciones de `CLAUDE.md` y del §9, así que mide memoria de defectos conocidos más que generalización; ADV-07 y
  REV-17 aciertan por fichero y clave con un hallazgo contiguo al defecto esperado. Salidas en
  `resultados/revisor_v1_20261107.json`. Primera revisión real: PR #425 (`../revisiones/PR-425_2d1b9f42.json`,
  PASS_WITH_EXCEPTIONS, 92.390 tokens).
- 2026-11-07 · forense · T-40 v1: `.claude/agents/forense.md` con su memoria, agente genérico Sonnet, 2 lotes de 10.
  Causas del §9: 12/12; runs adicionales 6/6; calibración 2/2 (CAL-02 BLOQUEADO; CAL-03 sin acciones). Todas en
  5 líneas. Límite: el catálogo de la memoria y los síntomas del oro salen de las mismas fuentes (§9, `CLAUDE.md`,
  PR correctivas), así que mide que el forense reconoce causas conocidas a partir del síntoma, no que descubre
  causas nuevas; la memoria incluye 9 causas sin caso en el oro como distractores. Salidas en
  `resultados/forense_v1_20261107.json`.

| Fecha | Agente | Modelo | Etiqueta | Casos | Aciertos | % | Tokens | A la primera |
|---|---|---|---|---|---|---|---|---|
| 2026-11-07 | revisor | sonnet | T-39 v1 (3 lotes de 8) | 24 | 23 | 95.8 | 306539 | 24/24 |
| 2026-11-07 | forense | sonnet | T-40 v1 (2 lotes de 10) | 20 | 20 | 100.0 | 168568 | 20/20 |
