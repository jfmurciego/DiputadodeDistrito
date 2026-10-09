# Entradas

**Versión del documento:** 2.0.0 — 2026-09-11

Las entradas oficiales deben identificarse por nombre, origen, fecha y SHA-256 en `MANIFEST.sha256`.

La fuente INE 65034 dispone de descarga oficial estable. La cartografía censal se controla igualmente por versión y hash. Las fuentes no deben actualizarse silenciosamente durante una ejecución.

`COMARCAS.csv` contiene la correspondencia utilizada por el motor alternativo
de Aragón: 731 municipios, 33 comarcas y cobertura municipal completa. Su
identidad queda fijada también en `MANIFEST.sha256`.

Los módulos 01-03 generan una base preparada cacheable. La caché se invalida si cambia una fuente, la configuración o cualquiera de esos tres módulos.
