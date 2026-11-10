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
| Ceuta | `nac51` | — | 1 | — | — | — | **NO EJECUTADA** |

- «Idéntico salvo el id»: sustituyendo en los bytes del viejo el id viejo por el nuevo salen los bytes del nuevo; los
  campos que llevan el id están en `campos_con_el_id` de cada `resultado_*.json`: solo `name` de la colección (el
  `run_name`, p. ej. `nac28_2025`), siempre en M04 y en M05 de Madrid y Las Palmas.
- Entradas: `diagnostico/t02-20261101` (Álava, Cádiz, Madrid, Las Palmas; run 41240137880 y hermanos) y
  `diagnostico/t132-entradas` (Huesca); sha256 de M01, M03 y contrato en cada `resultado_*.json`.
- Ceuta: no hay volcado M01/M03 en ninguna rama `diagnostico/*` y el blob publicado (`m06-ceuta-42503542766`) solo trae
  distritos; INE no es accesible desde la nube. Hace falta que el propietario suba `ddd-state-<run>-M03` de Ceuta
  (`lanzadores/subir_diagnostico_t02.sh`) para cerrar la prueba.

Conclusión: en 5 de 6 el id no cambia el mapa. Según la orden, el `git mv` de `territorios/` espera a Ceuta.
