# Prueba A de T-170 (T-214, 2026-11-10): mismo mapa con id viejo y nuevo

Canónico de `main` (M04 `modulos/04_generar_semillas.py` + M05 `modulos/05_optimizar_distritos.py`, sin editar),
mismo contrato con el id sustituido (`meta.territory_id`, rutas y `hard_partition_territory_id`) y mismas entradas M01/M03.
Arnés: `prueba_a.py` (crea `territorios/<id_nuevo>/` temporal y lo borra). Semilla: `seed: 12345` del contrato; el motor
no usa el id para sembrar (no aparece `territory_id` en `ddd_core/m04_*` ni `m05_*`).

| Territorio | Id nuevo | Unidades | K | Asignación M04 | Asignación M05 | GeoJSON M05 | Resultado |
|---|---|---|---|---|---|---|---|
| Álava | `nac01` | 240 | 3 | idéntica | idéntica | idéntico byte a byte | PASA |
| Huesca | `nac22` | 286 | 2 | idéntica | idéntica | idéntico byte a byte | PASA |
| Cádiz | `nac11` | 926 | 11 | idéntica | idéntica | idéntico byte a byte | PASA |
| Madrid (Congreso) | `nac28` | 4.479 | 59 | idéntica | idéntica | idéntico salvo el id | PASA |
| Las Palmas (insular) | `nac35` | 715 | 10 | idéntica | idéntica | idéntico salvo el id | PASA |
| Ceuta → Melilla (Planificador, 10-11) | `nac52` / `aut19` | — | 1 / 25 | — | — | — | **DISPENSADA** (motivo abajo) |

- «Idéntico salvo el id»: sustituyendo en los bytes del viejo el id viejo por el nuevo salen los bytes del nuevo; los
  campos que llevan el id están en `campos_con_el_id` de cada `resultado_*.json`: solo `name` de la colección (el
  `run_name`, p. ej. `nac28_2025`), siempre en M04 y en M05 de Madrid y Las Palmas.
- Entradas: `diagnostico/t02-20261101` (Álava, Cádiz, Madrid, Las Palmas; run 41240137880 y hermanos) y
  `diagnostico/t132-entradas` (Huesca); sha256 de M01, M03 y contrato en cada `resultado_*.json`.
- Ceuta y Melilla: por decisión del Planificador (10-11), Ceuta se sustituye por Melilla, que es el mismo caso especial
  (ciudad autónoma duplicada AUT/NAC, un distrito en el Congreso). Ninguna de las dos tiene entradas M01/M03 en
  `diagnostico/*`. Las de la batería están en R2 (`bateria/entradas/<t>/`), sin credenciales en esta sesión, o salen
  de la fuente oficial (INE), que no es accesible desde la nube. **Queda dispensada con este motivo:** `congreso_melilla`
  tiene K=1, así que el mapa es trivial (todas las unidades van al único distrito), y la parte del id que se ejerce
  (contrato, rutas, carpeta de configuración) es la misma que en los cinco territorios que sí pasan. Salvedad:
  `melilla` (AUT19) tiene K=25 y no es trivial; no queda probada aquí, aunque el motor no usa el id para sembrar.

Conclusión: en los 5 territorios ejecutados el id no cambia el mapa; el sexto (Melilla) está dispensado. El `git mv`
de `territorios/` no va en esta PR: es un paso propio (T-220), tras fusionar #688.
