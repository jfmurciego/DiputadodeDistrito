# Ensayo aislado de reparación poblacional con ReCom

**Dictamen:** `NO_GO` para el candidato territorial; incremento experimental local, sin revisión independiente final.

## Alcance y conservación

Se conserva sin cambios el intento A2 v1.9, cuyo dictamen sigue siendo `NO_GO` en `docs/AUDITORIAS/M05_A2_2026-10-10/INFORME_V19.md`. No se modifica el Plan Maestro. El reparador monotónico A2 no se amplía ni se usa como estrategia de este ensayo.

Se prueba una entrada opt-in al motor existente GerryChain/ReCom. El selector canónico y su comportamiento por defecto permanecen intactos. La búsqueda puede observar estados con infracción de suelo/techo poblacional exclusivamente dentro de la cadena privada. Provincia, K, universo, unidades indivisibles, disciplina municipal, congelación urbana y contigüidad se mantienen como restricciones de transición. Un estado con cualquier restricción dura incumplida no es elegible para el ranking, portfolio o GeoJSON de salida. El input se lee y el output del ensayo vive fuera del repositorio.

## Identidad fijada

- Rama y HEAD base: `codex/distritos-autonomicos`, `42163cd8cebd120db9ab9fd1329c32ccdd87cf36`.
- Motor GerryChain/ReCom antes del cambio: SHA-256 `8d9e5c94389323f82948947afba4cb621d567d8e2d0cac5d034f0ce17173359e`.
- Prueba existente antes del cambio: SHA-256 `5b65793e01257b3b2cc65732d0a827d54744c8de8aa43373aa0ece21a6ecbf53`.
- Checkpoint M05 auténtico `/Users/macbookpro/Downloads/artifact-11353290857.zip`: SHA-256 `6a5181ddeca846dae3afde8e560ac51077d30ca82a09c85277d57406fe289d9c`.
- M03 extraído de ese ZIP: SHA-256 `34ac24c2be4ec810caff0d8170f54dfdf00b79fd575b1e80f8f362143c8152ec`.
- M05 de entrada extraído: SHA-256 `519ba8ab03c6089ee2a269bbeddcd40081645bcaf802e0922350c4fcf37f38c6`.
- Informe M05 correspondiente: SHA-256 `74f97b5e771cc5e54c797d48e212a0adabd3642e3630a09a60173002b3faa437`.
- Testigo manual `solucion_validada.json`: identidad conocida SHA-256 `6e832b1c6f35891d104f04ffdeedcb1fd7c7481a3598015b42aaf43f61d6091a`. Solo se consultó su identidad; no se cargó en el proceso ni se usó como inicialización, guía o candidato.
- Datos de entrada: 4.479 secciones, 135 distritos, población total 6.871.903. El informe M05 registra objetivo 50.902,985185, suelo 40.722,388148 y techo 89.080,224074; `hard=1`, 18 distritos fuera de ±12 %.

## Cambio y ejecución reproducible

El cambio añade un flag explícito `--allow-population-infeasible-initial` al camino existente. Sin ese flag, la validación de baseline continúa siendo fail-closed. La política de selección solo conserva candidatos con cero incumplimientos duros. El portfolio comparte un tope de estados entre semillas y puede cortar la iteración al vencer el plazo; si no queda candidata válida, no materializa GeoJSON ni informe.

Ensayo aislado, ejecutado desde una copia del checkpoint y con `PYTHONHASHSEED=0`:

```text
Python: /private/tmp/madrid-gerrychain-venv/bin/python (3.11)
M03: /private/tmp/ddd_madrid_recom_transient_20261011/input/m03.json
M05 inicial: /private/tmp/ddd_madrid_recom_transient_20261011/input/m05.zip
Contrato: territorios/madrid/config/madrid_2025.yaml, cargado solo como configuración de lectura
Estrategia: ReCom existente; epsilon=0,12; max_bipartition_attempts=500
Seed del ensayo: 4629; una semilla; pasos máximos compartidos=3.000; plazo=180 s
Resultado: NO_VALID_CANDIDATE_WITHIN_BUDGET
Salida candidata M05: no creada
```

La invocación reproducible usa `contract_from_yaml` y `run_from_paths` del motor citado, con `StrategyConfig(steps_per_seed=3000, seed_base=4628, seed_count=1, proposal_epsilon=0.12, max_bipartition_attempts=500)` y los topes `max_total_steps=3000`, `max_seconds=180`. La reproducción final bajo el código exacto SHA-256 `8f8034b5c7af7a64cd6cb65c2410a2e34b73eab20765d807129dbab3fb55a05b` agotó los 3.000 estados en 134,956 s de búsqueda (141,515 s de pared), antes del plazo. Observó 739 estados únicos, 2.246 self-loops y 1.436 fallos recuperables de propuesta. Los 3.000 estados emitidos mantuvieron infracciones poblacionales transitorias; no apareció candidato hard-válido. Los contadores no explican por qué las propuestas restantes no alcanzaron hard cero; ese mecanismo queda sin atribuir. La evidencia completa está en `evidencias/madrid_trial.json`.

Como no se produjo candidata `hard=0`, no se ejecutaron M06, `validar_ejecucion.py` ni la auditoría geométrica. El primer bloqueo demostrado es que esta cadena ReCom, bajo la semilla y presupuesto declarados, no visita una asignación hard-válida; la causa concreta entre propuestas, fallos ReCom y self-loops restantes no se discrimina con la telemetría actual. No se infiere nada sobre geometría ni se promueve el ensayo.

## Pruebas

- Cinco pruebas nuevas deterministas: estado inicial con déficit solo privado y selección final hard-válida; baseline estructuralmente inválido fail-closed; presupuesto compartido entre semillas; candidato rechazado sin escribir sobre el origen; timeout sin escribir sobre el origen.
- La prueba sintética repite el seed y compara el hash de asignación; distingue `hard=0` de la métrica blanda `districts_outside_tolerance`.
- Suite `tests.test_m05_gerrychain_strategy` excepto `test_resolve_paths_honours_project_root`: 30 ejecutadas, PASS; 3 Galicia omitidas porque el checkpoint opcional no está disponible.
- La suite completa bajo macOS da un fallo ambiental reproducible en `test_resolve_paths_honours_project_root`: `Path('/private/var/...') != Path('/var/...')`. El mismo entorno pasó las 30 restantes al excluir únicamente esa prueba de resolución de symlink.
- La regresión real de La Rioja/Cantabria no se ejecutó porque exige la identidad histórica exacta de M05; no se desactivó esa guarda.

## Revisión y límites

La reproducción independiente solicitada y la revisión Codex del HEAD final están pendientes. La revisión independiente del candidato de Madrid no puede certificar un cambio distinto por analogía. El caso sintético no acredita que ReCom resuelva Madrid. No se intentó otra semilla, ranking, operador o presupuesto tras el primer resultado negativo.

**Cierre:** incremento experimental instalado en el árbol de trabajo; resultado territorial `NO_GO`; A2 continúa cerrado en `NO_GO`; M06 y validador oficial `NO EJECUTADOS` por ausencia de candidata; ningún producto, catálogo o checkpoint fue modificado.
