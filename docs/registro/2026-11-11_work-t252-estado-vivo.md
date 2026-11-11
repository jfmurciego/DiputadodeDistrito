## 2026-11-11 — T-252 — Check «Estado vivo» tras los commits de robot en main

- `pruebas-plataforma.yml` 1.10.0 (legacy 1.9.0): job `estado_vivo` («Estado vivo») solo en push a main de robot
  (`cambios` robot=true, la suite no corre). 23 módulos que leen estado vivo (catálogo, `datos_abiertos/INDEX.json`,
  `orchestracion/`, `territorios/*/evidencia`, `datos/composicion`, status), sin Docker: setup-python 3.11.13 + caché pip de
  `requirements.lock`, `timeout 540`, timeout del job 12 min.
- No bloqueante: `continue-on-error`, fuera de `pruebas` y del ruleset. Si falla: anotación `::error` y resumen con los tests
  FAIL/ERROR y el commit sospechoso (`git log -1`). Concurrencia `ddd-estado-vivo` que cancela el del push de robot anterior.
- Medida local: 288 tests en 174 s (+ ~20 s de instalación con caché). Test estructural en `test_ahorro_ci_pruebas`.
