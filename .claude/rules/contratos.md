---
paths:
  - "territorios/**"
  - "configuracion/**"
  - "herramientas/generar_provincias_congreso.py"
---

# Contratos, política y población

- El materializador sobrescribe en el contrato los umbrales con los de la política: cualquier ajuste por territorio
  va en `configuracion/politica_generacion_territorial_2025.yaml` (`population_limits`, `structural_floor_exemptions`),
  no solo en el contrato.
- Exenciones de suelo: por partición (isla/provincia, `population_floor_exempt_partitions`) o por municipio
  (`population_floor_exempt_municipalities`, código INE de 5 cifras; Beniel en Murcia).
- En contratos con islas el campo municipal es `DDD_MUNICIPALITY_PARTITION` («35012:35-C01») y las secciones M06
  pueden no traerlo: las exenciones municipales comparan solo el municipio y caen a `CUMUN` o CUSEC[:5] (#394 #398).
- Bloqueo por población: suele ser estructural (municipios indivisibles o núcleos cerrados que encajonan distritos
  pequeños). Palancas: `municipality_atomicity_limit_ratio` más bajo, `population_repair` (private_annealing),
  exención de suelo. Más presupuesto de reparación no ayuda si es estructural.
- Estructural sin palanca de contrato: municipio atómico rodeado de municipios que solo lindan con él (Lorca+Águilas+
  Puerto Lumbreras) o enclaves dentro de un municipio con núcleos cerrados (Alcantarilla y Beniel en Murcia).
  Comprueba vecinos municipales en el grafo M03 antes de proponer ajustes.
- La exención municipal va en `validation` del contrato (el materializador no la toca) y la valida el motor; el techo por
  territorio, en la política (`population_cap_ratio` y `target_tolerance_ratio` = techo−1; la atomicidad no puede pasarlo).
  `population_repair` (profundidad 6, conjunto 3, 500.000 candidatos) no mejoró ningún exceso estructural el 01-11.
- En el informe M05, `population_status_by_district` es un dict y `final_hard_population_violations` cuenta también los
  distritos exentos: mira los no-PASS, no ese contador.
- CRS de M02 en provincias del Congreso: el generador pone EPSG:3035; donde el autonómico usa 25830 (Comunidad
  Valenciana, Región de Murcia) cópialo. En 3035 los solapes INE crecen (0,19 → 11,8 m²) y fallan la admisibilidad
  de 01 (`GEOMETRY_INVALID_AUDITED`) o la conectividad pre-M04 (#374, #383). Los parámetros de M02 viven en el
  contrato; la política solo sobrescribe población; `population_repair` va en `modulo_05` del contrato.

## Congreso / nacional (provincias)
- `herramientas/generar_provincias_congreso.py` (idempotente) da de alta provincias desde el reparto N06 y hereda
  los puentes de enclaves de los contratos autonómicos: sin ellos el pre-M04 falla con «grafo territorial no
  supera conectividad administrativa» (Palencia, #371).
- Islas: componentes agrupadas y `bridges` en `particiones_insulares_2025.json`; inventario 2023 sacado del ZIP de
  Interior (coincide en hash con el INE 2023); `component_districts` en la política fija el reparto (#369 #370).
- Ámbitos sin CODAUTO usan `pilot_code` (C+CPRO) para ordenar en dashboard y visor (#367).
- Los robots de registro reescriben `catalogo_preparacion.yaml` y el catálogo maestro mientras corren
  ejecuciones: una PR que los toca choca enseguida. Rebasa tomando `main` y reinserta solo lo tuyo; fusiona rápido.
- `TERRITORIAL_REPLAN_BLOCK: fuente elegida difiere del catálogo`: la fila del catálogo apunta a un receipt antiguo
  (`territorial_source_declaration` / `independent_source_evidence`); alinéala con `preparation_evidence` (#338, #352).
