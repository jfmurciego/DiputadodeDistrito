# T-104 · Valencia: desajuste de secciones ZIP 2023 ↔ M06 (informe interno)

Mantenimiento interno (D-18): no sale del repositorio. Sin lanzar ni cambiar nada. Cifras de ficheros versionados.

## 1. Fuente del contrato de Valencia
- `territorios/congreso_valencia/config/congreso_valencia_2025.yaml`: `source_section_year: 2023`,
  `inputs/seccionado_2023.zip` (INE), población `65034.csv` del año 2023. `fuentes_oficiales.yaml`: `section_year: 2023`.
- Las 52 provincias del Congreso usan el mismo par (seccionado 2023 + padrón 2023): **no hay incoherencia**. «2025» es
  la edición del contrato, no el seccionado. La premisa «M06 INE 2025» no se sostiene.
- M06 vigente: producto territorial run 41318119259; par y M08 run 41335936727
  (`evidencia/catalogo/*.json`); composición en `datos/composicion/congreso_valencia.csv` (sha256 `012274d0…`,
  `sha256_m06` `9a828…`, `anio_secciones` 2023).

## 2. Origen del desajuste
- Todo el desajuste está en **Bétera (46070)** salvo `4612301002` (838 votos, contenida):
  el ZIP (`fuente-infoelectoral-02202307`, sha256 `e78fc231…`) trae `4607001001–016` y ningún distrito 02;
  el seccionado INE 2023 (sha256 `7a15e700…`) trae `4607001001–004` y `4607002001–009`. Bétera se reseccionó
  durante 2023, después del corte del INE (fuente: `configuracion/equivalencia_secciones_congreso_2023.json`).
- Partidas (T-103): 4607001005 y 007–015 = 8.511 votos = 0,600 % de 1.419.017. 006 y 016 son contenidas.
- **Dato clave**: las 13 secciones de Bétera del M06 están todas en el **distrito 22**
  (`datos/composicion/congreso_valencia.csv`). Cualquier reparto de esos 8.511 votos acaba en el distrito 22:
  el error a nivel de distrito es **0**, pese al 0,600 % a nivel de sección.

## 3. Seccionado que daría desajuste 0 y coste de regenerar
- Candidato: INE `seccionado_2024.zip` (sha256 `df931fa0…`, ya registrado en el JSON de T-85 como primera geometría
  con las secciones del ZIP). No está comprobado que dé 0 en toda la provincia: puede introducir secciones de 2024
  ausentes del ZIP (desajuste inverso). Exigiría además el padrón por sección de 2024 (otra tabla del INE, por
  acreditar con fuente y sha256): Valencia quedaría en 2024 y las otras 51 en 2023 (**esa sí sería incoherencia**).
- Efectos: nuevo M01–M06 (los 23 distritos de Valencia cambian; el total nacional de 407 no), huellas M04/M05 y
  checkpoints nuevos (modo «Generar desde fuente territorial acreditada»), par electoral incompatible
  (`TERRITORIAL_READY_PAIR_INCOMPATIBLE`) → `prepare_one` + 00 «Reutilizar», nuevo M08 y nueva publicación
  (permiso del propietario). Coste: 1 cadena 00 completa de una provincia grande (horas de runner) + revisión.
- Regenerar con la **misma** fuente 2023 (lo autorizado el 08-11) reproduce el desajuste: no sirve.

## 4. Alternativa sin cambiar la fuente
- **(a) Regla general, recomendada**: en `herramientas/resultados_partidos.py`, una sección partida cuyas secciones
  M06 candidatas caen **todas en el mismo distrito** se trata como «contenida en distrito»: distrito exacto, fuera del
  tope. No es una excepción por provincia; se quita `CASOS_APARTE["46"]`. Valencia pasaría a 0 % partido entre
  distritos. Coste: una PR pequeña con test (caso Bétera) y decisión del propietario sobre la regla (amplía T-103).
  Riesgo: bajo; los votos por sección dentro de Bétera siguen siendo un reparto D-13, que se declara en la evidencia.
- (b) Excepción gobernada (`decided_at/by/reason/evidence`) o subir el tope solo para Valencia: funciona, pero es
  una excepción por territorio cuando el motivo (todo en un distrito) es general. No recomendada.

## 5. Recomendación
- **No regenerar el M06 de Valencia.** Aplicar 4(a) y, tras fusionar, relanzar la 00 de Valencia en
  «Reutilizar progreso existente» (sin cambio de M04/M05 ni de par; coste de una 00 corta, como Badajoz).
- Si el propietario prefiere el seccionado 2024: primero acreditar `seccionado_2024.zip` y el padrón 2024 con sha256
  y medir el desajuste en local; solo entonces 00 en «Generar desde fuente territorial acreditada».
- Nota: el seccionado del M06 (`79a76b14…` en `datos/composicion/MANIFEST.json`) y el de la tabla T-85 (`7a15e700…`)
  tienen sha256 distintos; conviene confirmar que son el mismo seccionado 2023 (otro empaquetado) antes de 4(a).
