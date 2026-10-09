# R004 — Preparación territorial independiente de la validación algorítmica

**Fecha:** 2026-09-11  
**Estado:** candidato a GitHub

## Hallazgo
La caché M01-M03 estaba correctamente identificada en R003, pero se construía dentro del mismo job que M04-M08. GitHub solo debe promover una preparación válida con independencia de que el algoritmo experimental posterior supere su puerta de calidad.

## Cambio
El workflow se divide en dos jobs. `preparar-territorio` restaura o construye M01-M03 y termina independientemente. `ejecutar-distritacion` restaura esa preparación y ejecuta M04-M08.

Además, el checkout ordinario no descarga Git LFS. Los ZIP nacionales solo se materializan cuando la preparación falta o el usuario selecciona `completo`. Una iteración normal de M05 reutiliza la caché sin transferir de nuevo los ficheros nacionales.

## Razón fuerte
El estado de la infraestructura territorial y el estado de calidad de un algoritmo candidato son hechos distintos. Mezclarlos hace que un algoritmo malo penalice el coste de preparación y crea acoplamiento operacional injustificado.

## Criterio de aceptación
Una ejecución con M05 en FAIL debe conservar/publicar sus resultados y no impedir que la siguiente ejecución iterativa restaure M01-M03 sin descargar ni reprocesar los ZIP nacionales.
