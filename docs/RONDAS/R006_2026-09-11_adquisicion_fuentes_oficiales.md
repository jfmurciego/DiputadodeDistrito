# R006 — Adquisición automática de fuentes oficiales

**Fecha:** 2026-09-11
**Objetivo:** eliminar el bootstrap manual/Git LFS de las dos fuentes territoriales grandes.

## Decisión
Las fuentes públicas del INE no se trocean ni se almacenan como binarios grandes en GitHub. El workflow las materializa cuando M01-M03 necesitan reconstruirse. La adquisición queda encapsulada en `herramientas/adquirir_fuentes_ine.py`.

## Fuentes
- Población: tabla INE 65034, CSV oficial.
- Geometría: INE OGC API Features, colección `WMS_INE_SECCIONES_G01:Secciones_2025`, filtrada a CPRO 22, 44 y 50 y TIPO SECCION.
- El INE declara que su API ofrece las series anuales de seccionado y exige la mención «Seccionado cedido por el Instituto Nacional de Estadística».

## Controles
- descarga con reintentos;
- 1.463 secciones esperadas para Aragón;
- provincia validada por feature;
- CUSEC único;
- SHA-256 y tamaño de cada fuente materializada;
- `FUENTES_ADQUIRIDAS.json` con fecha UTC, URLs y hashes;
- procedencia publicada como artefacto del run.

## Versiones
- configuración 7.2.0; anterior 7.1.1 en legacy;
- workflow 2.4.0; anterior 2.3.1 en legacy;
- adquisición INE 1.0.0.

## Riesgo controlado
R006 cambia el mecanismo de adquisición de la cartografía: de ZIP nacional local a GeoJSON oficial consultado directamente al servicio INE. La ejecución GitHub siguiente debe validar cardinalidad, población, grafo y resultados contra el baseline antes de promoverlo.
