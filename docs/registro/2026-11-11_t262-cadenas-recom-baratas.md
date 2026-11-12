## 2026-11-11 — T-262 — Cadenas ReCom ponderado más baratas, mismos mapas bit a bit (D-89)

- `naturalidad_competicion` 1.6.0 (legacy 1.5.0): `arbol_ponderado` sobre grafos RX lee extremos y datos de todas las
  aristas de una vez (`edge_index_map`) en vez de `get_edge_from_edge_id`/`node_data`/`edge_data` por arista. Mismo orden
  de aristas (`_ordered_edge_ids`) y una llamada a `rng.random()` por arista: mismos pesos, árbol y RNG.
- `reglas/evaluar` 1.1.0 (legacy 1.0.0): `valido(problema, reglas, asig, ctx=None)` == `evaluar(...).valido` sin métricas
  ni huella; `evaluar` y `valido` comparten `_violaciones`. `Contexto.rango_municipal` memorizado por población.
- `naturalidad_clave` 1.2.0 (legacy 1.1.0): `Natural.valido` (restricción `nucleo` de la cadena) reutiliza el Contexto
  mientras no cambien `problema` ni `reglas`.
- Medición (`medir.py --rep 3`, 4 CPU, `PYTHONHASHSEED=0`), cadenas / total en s, main → rama:
  congreso_huesca 16,37 → 11,56 / 25,55 → 20,54; congreso_la_rioja 15,96 → 10,96 / 24,50 → 19,38;
  la_rioja 28,85 → 19,98 / 40,23 → 31,14. Ganador, `huella_resultado` y sha256 de cada composición iguales en las 6
  repeticiones. Sin exhaustivo (1 ejecución): illes_balears 74,5 → 56,6, cantabria 369,0 → 258,5 (idénticos).
- Descartado: guardar el recargo en los datos de la arista (sin ganancia medible). El resto del tiempo está dentro de
  GerryChain (`bipartition_tree`, `_calc_pops`, `from_rustworkx`): no se toca sin bifurcar la librería.
- Huellas: cambia `motor2` (ficheros de `ddd_motor2/`); `huella_resultado` no cambia. Test nuevo
  `tests/test_motor2_cadena_rapida.py` (valido == evaluar, rango memorizado, árbol RX == bucle 1.5.0).
