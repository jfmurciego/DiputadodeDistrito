# Diputado de Distrito · nota metodológica

> **Mapa de investigación sin valor oficial.** Los distritos son una propuesta técnica reproducible; no sustituyen a ninguna demarcación vigente ni prejuzgan una reforma.

**Versión del kit:** 1.0.0 · 2026-11-08 · borrador para revisión del propietario. **DOI de la versión:** [DOI de Zenodo: pendiente]. **Visor:** [URL del visor: pendiente de publicación].

## Qué es
Diputado de Distrito (DDD) es un motor abierto y reproducible que divide cada circunscripción en distritos uninominales a partir de las secciones censales oficiales, y muestra sobre ellos los resultados de las elecciones generales de 2023. Código y datos: <https://github.com/jfmurciego/DiputadodeDistrito>.

## Cómo se forman los distritos
1. **Unidades.** Secciones censales del INE con población del padrón de 2025 (`datos/distritos/municipios_ine_2025.csv`). Las 49 provincias publicadas suman 30.500 secciones.
2. **Número de distritos (K).** Decisión del propietario `N06-OWNER-20261012-K`: K = el mayor entre 1 y la parte entera de (población + 60.000) / 120.000, por provincia. Es un reparto propio del proyecto (suma 407 en las 52 circunscripciones), **no** el número de escaños del Congreso (350).
3. **Reparto.** Método de Hamilton. Cada distrito es contiguo y queda dentro de una sola comunidad autónoma; los municipios se conservan enteros salvo que superen el techo de población (política `configuracion/politica_generacion_territorial_2025.yaml`, v1.7.4). Los límites de población por distrito y sus excepciones (islas, municipios indivisibles) están en esa política y en el contrato de cada territorio.
4. **Optimización y validación.** Solución inicial (M04), mejora con cadenas de GerryChain (M05), consolidación y validación del producto (M06). Cada paso deja informes y huellas sha256.

## Cómo se incorporan los resultados
Los votos por sección de las generales de 2023 (Ministerio del Interior) se agregan por distrito (M07/M08). Por ahora se publica **solo el ganador por distrito**, no los votos de cada partido. Los escaños oficiales provienen del BOE-A-2023-18907.

## Alcance actual (08-11-2026)
- 49 de 52 circunscripciones publicadas en `datos_abiertos/`: 325 distritos, 38.580.009 habitantes (media 118.708 por distrito; extremos 36.684 y 166.927). Faltan Alicante, Barcelona y Málaga, en generación.
- Solo generales de 2023. Otras elecciones, rotación y participación aún no están.

## Límites
- Un ganador por distrito de 2023 no predice resultados futuros ni equivale a escaños: con otro voto, otra participación u otras listas, el mapa cambia.
- Los distritos dependen de decisiones declaradas (K, límites de población, indivisibilidad municipal); otras decisiones legítimas darían otros mapas.
- La población es del padrón de 2025; los votos, de 2023.

## Reutilización y verificación
Datos con licencia **CC-BY-4.0** (atribución: «Diputado de Distrito»); las fuentes oficiales (INE, Interior, BOE) mantienen sus condiciones. `datos_abiertos/INDEX.json` da, por provincia, run de origen y sha256 del producto, del GeoJSON y del CSV. Cita: [DOI de Zenodo: pendiente].
