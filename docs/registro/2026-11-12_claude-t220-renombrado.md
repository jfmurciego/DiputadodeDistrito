## 2026-11-12 — T-220 — Carpetas de territorios con el id nuevo de la tabla maestra (aut01…aut19, nac01…nac52)

- Causa: D-61 (id interno en minúsculas, a la vista «NAC01 · Álava») y T-170 §2 (un solo resolutor; nada de comparar
  ids con literales ni de detectar el Congreso por el prefijo `congreso_`, que con `nacNN` falla en silencio).
- Tabla versionada: `configuracion/equivalencias_territorios.csv` 1.0.0 (71 filas, generada de
  `configuracion/notacion_territorial.csv` sha256 13299081…e621ee; `tests/test_t220_renombrado.py` la regenera).
- `git mv` de las 71 carpetas `territorios/<viejo>/` → `territorios/<nuevo>/` y de `config/<viejo>_AAAA.yaml` →
  `config/<nuevo>_AAAA.yaml`, con `meta.territory_id`, `run_name`, rutas de caché y anclas `#territories.<id>` nuevas;
  los contratos versionados suben de parche con copia en `legacy/territorios/<nuevo>/`. `configuracion/ensemble/<id>.json`,
  catálogo, política, registro electoral, legislatura, preparación, fuentes y Gestor con el id nuevo.
- Sin renombrar (D-61, ciclo de convivencia): `congreso350_*` (49, D-76), la carpeta agregada `congreso`, los `election_id`
  (`congreso_alava_2023-07-23`…), nombres de artefactos y claves R2, `datos/`, `datos_abiertos/<viejo>/` y URL públicas,
  `orchestracion/` (el registro del visor es de solo adición: las entradas nuevas llevan `alias_de` con el id viejo) y
  las evidencias, que se mueven con su carpeta y se leen vía `ddd_core.territorio_ids.resolver_id` (contador
  `LECTURAS_LEGACY`).
- `ddd_core/territorio_ids.py` 1.1.0: `ambito(x)` (AUT | NAC | NAC350 | CONGRESO), `es_nacional`, `ids_nuevos` y CLI
  `python -m ddd_core.territorio_ids ambito <id>`. Sustituye a los 26 usos de `startswith("congreso_")`, globs
  `congreso_*` y `case territorios/congreso_*` (`_reutilizable-generacion-territorial.yml`).
  `resultados_ligeros.vigente_por_eleccion` agrupa id viejo y nuevo como un mismo territorio (`ambito=` en vez de `prefijo=`).
- Efecto: cambian `meta.territory_id` y las rutas de los contratos, que entran en las huellas M05/N08 y en los checkpoints
  M04: tras fusionar, las 00 van con «Generar desde fuente territorial acreditada» (no «Reutilizar»). La semilla no cambia
  (D-90: código de la tabla maestra; `test_motor2_semilla`).
- Tests: `tests/test_t220_renombrado.py` (tabla = tabla maestra con sha256; carpetas = tabla ∪ `congreso350_*` ∪
  `congreso`; sin ids viejos vivos fuera de legacy/, docs, evidencias, datos derivados, registro del visor y la tabla;
  sin detección por prefijo en código ni workflows), `tests/test_t220_huella_puentes_shell.py` (el paso nuevo bajo
  `bash -eo pipefail`: autonómica y desconocida salen 0, nacional sin M01 avisa, huella que no casa sale 1).
