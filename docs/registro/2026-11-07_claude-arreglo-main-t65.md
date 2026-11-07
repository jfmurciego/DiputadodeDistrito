## 2026-11-07 — Arreglo — main en rojo tras #458 (T-65)

Causa: #458 se fusionó antes de que existiera su `pruebas` y dejó `main` en rojo: `metricas-proceso.yml` tiene
`workflow_dispatch` y no estaba en la lista de workflows manuales que fijan `test_design_a_matriz_sintetica` y
`test_codauto_preparation_contract`, y `dashboard/index.html` enlazaba «Métricas del proceso» sin que la copia
publicada (`publicado/dashboard/index.html`) lo hiciera. Cambio: las dos listas incluyen `metricas-proceso.yml`; la copia
publicada del índice vuelve a ser igual a la fuente; el publicador 3.5.0 copia `dashboard/metricas.html` y
`metricas_proceso.json` para que el enlace no dé 404 en Pages. Pruebas: diseño A, `codauto`, `dashboard_pages`,
`hemiciclo_sitio`, `metricas_proceso`, tests de workflows y R015 en verde.
