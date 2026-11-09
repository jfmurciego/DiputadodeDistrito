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

- Distrito sobre el techo con «residual + enclaves» o un bloque de municipios enteros: suele ser fallo de búsqueda
  (M05 mueve unidades enteras y no redibuja las piezas internas). Desde M04 7.6.7 lo cubren el alivio de residuos y el
  reintento por enclaves (#441); antes de pedir exención, mira en el grafo los vecinos municipales y los residuales
  con hueco. Imposible estructural (Fuengirola en Málaga): exención de suelo con decisión del propietario.

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
- M06: `municipality_names` va en orden alfabético y `municipality_codes` en numérico (desalineados, nombres
  abreviados): el nombre se toma del INE por código. En el repo, C12 = nombres de distrito y C13 = comunidades de interés.
- Toda exención de suelo nueva trae su decisión en `validation` (`population_floor_exempt_decisions` /
  `_partition_decisions`: decided_at, decided_by, reason, evidence) o falla `comprobar_exenciones_gobernadas`.

## Lecciones 08-11 (Coordinador)
- Archivista (D-17): tolerancia de partidos ≤0,5 % de los votos de la provincia; contenidas y recodificadas no cuentan para el tope (#531, #535, #538).
- Sigla: tabla de homologación T-97 con D-20 aplicada (familias «Podemos–Sumar», «CiU–Junts», «UPN y coaliciones», «CHA-IU»; #537). Renombrar partidos exige actualizar a la vez el mapa Interior o `construir` falla por cobertura. Valida las discrepancias contra el dato por provincia, no de memoria (Caballas y MDyC son Ceuta; CpM, Melilla).
- Cada publicación nueva exige nombres/informes C12-C13 de la provincia (herramienta T-59) y topónimos en español.
- `congreso_350`: gemelos `congreso350_<prov>` con K = escaños reales BOE-A-2023-18907, nunca publican (#539). Gestor 2.0 (#542) y guía en `docs/GUIA_GESTOR_CAMPANAS.md`.

## Lecciones 09-11 (T-129, T-121)
- La población del reparto de escaños son las cifras oficiales por real decreto (RD 1117/2025 a 1-1-2025; RD 1037/2022 a 1-1-2022), no la tabla INE 65034: difieren 0,03 % y 241 hab. cambian un escaño (Ciudad Real/Tenerife). `configuracion/poblacion_oficial_provincias_*.csv` + `herramientas/reparto_art162.py` reproducen el anexo 52/52 en 2026 y 2023.
- El K de los distritos usa la 65034 por decisión del propietario (opción A): con la oficial Cádiz sería 10 y el total 406; fijado por test, no cambiar de fuente sin decisión.
- Los BOE se bajan con `curl https://www.boe.es/diario_boe/xml.php?id=BOE-A-…` (sha256 del XML); INE no es accesible desde la nube.
- Autonómicas: el Observatorio publica el voto CERA como pseudo-sección sin geometría en La Rioja (excluir solo si es la única sección sin geometría con ese total); `datos/composicion/<c>.csv` de 12 de 14 comunidades está desfasado frente al seccionado INE 2025 (Madrid, 46 secciones): asignación por geometría y marca `aproximado_en_distrito`, no regenerar. Ceuta y Melilla no tienen autonómicas; el día exacto de elecciones pasadas solo consta como mes hasta contrastar con boletín.
- Paso A autonómico: `historico_autonomico.py ejecutar --comunidad X` (pip install -r requirements.lock); Madrid difiere hasta 884 votos/distrito del paso B por redondeo, con suma y ganador idénticos.
- Distritos públicos 1..K (T-135, regla del propietario): lo interno (`datos/composicion`, `datos/resultados`, M06) sigue 0..K-1; la conversión se hace al publicar (`numeracion_publica.py`) y un test falla ante un distrito 0.
