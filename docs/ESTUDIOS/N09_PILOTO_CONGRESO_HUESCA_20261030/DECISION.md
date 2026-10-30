# Piloto Congreso — Huesca (CPRO 22)

- Versión: 1.0.0 · Fecha: 2026-10-30 · Estado: candidato
- Decisión: **N09-OWNER-20261030-PILOTO-HUESCA** — el propietario autoriza la generación del piloto
  provincial del Congreso para Huesca (opciones A + B + C del 30-10-2026). No autoriza otras provincias ni
  publicación nacional.

## Alcance

- Territorio nuevo `congreso_huesca` (pilot_code `C22`), fuera de las 19 comunidades: mismo flujo 00,
  mismo motor M01–M08 y mismo visor.
- K = 2: cuota de Huesca en N06-OWNER-20261012-K (K_i igual al mayor entre 1 y la parte entera de
  (P_i + 60.000) entre 120.000; K2025 = 407).
- Reglas N08-OWNER-20261013-7RULES: suelo 85 %, techo 115 %, tolerancia 15 %, sección CUSEC
  indivisible, municipio indivisible si cabe bajo el techo.
- Referencia temporal: población y seccionado INE **2023**, contemporáneos de la elección general del
  23-07-2023 (el motor exige el año electoral cuando existe). Los resultados por mesa de 2023 casarán con
  las secciones 2023 sin correspondencia entre ediciones.

## Selección (análisis C, sin ejecuciones)

`docs/ESTUDIOS/N08_CIERRE_NACIONAL_20261013/MATRIZ_FACTIBILIDAD_52.csv`: 9 de 52 unidades sin solapes,
sin CUSEC multiparte y con un único componente. Con K > 1 quedan Huesca (K=2), Álava, Ourense y
Salamanca (K=3); Cáceres se excluye por la discontinuidad conocida de Casar de Cáceres. Huesca es la más
sencilla: ningún municipio supera el techo.

## Pendiente

- Fuente electoral: resultados por mesa del Congreso 2023 (Ministerio del Interior); se declarará en
  `territorios/congreso_huesca/config/elecciones/`. Hasta entonces el piloto corre en `territorial_only`.
- El contrato inicial se materializó con un paquete sintético para superar la puerta de generación; la
  01 lo rematerializa con el paquete INE real en la primera ejecución.
