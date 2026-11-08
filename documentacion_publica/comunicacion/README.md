# Kit de comunicación (T-93b · D-16)

> **Mapa de investigación sin valor oficial.** Todo es borrador para el propietario: no se ha publicado ni enviado nada. Pendientes que rellena el propietario: **[DOI de Zenodo]**, **[URL del visor]**, contacto de prensa.

| Pieza | Fichero |
|---|---|
| Nota metodológica (1 página) | `nota_metodologica.md` |
| Ficha de prensa | `ficha_prensa.md` |
| 6 textos de LinkedIn | `linkedin_borradores.md` |
| Imágenes (capturas reales de `visor/nacional`, PR #513, deviceScaleFactor 2) | `imagenes/` |

## Trazabilidad de cifras (revisión 08-11-2026)
| Cifra | Fuente | sha256 |
|---|---|---|
| 49 provincias; 325 distritos; 38.580.009 hab.; 30.500 secciones; extremos 36.684 y 166.927; media 118.708 (=38.580.009/325) | suma de `distritos[]` en `datos_abiertos/INDEX.json` (n_distritos, poblacion, secciones) | `296c592dbc5c87f9a18fb16da64d8d0dcce981da8fd77a1c9ff593e0f1863885` |
| Padrón 2025 | `datos/distritos/municipios_ine_2025.csv` | `456856947f4d170f319a14c5431db2b7bf5c60accb0a7dbaf849e90f2b775b92` |
| K=407, 52 circunscripciones, regla (P+60.000)/120.000, `N06-OWNER-20261012-K` | `k_districts` y `k_rationale` en `configuracion/catalogo_territorios_espana_2025.yaml` | `0fd6fa6cb31f046fdd0acdfd28df9151c0dc2bf00782519ea029cbb7edcb2668` |
| Hamilton, contigüidad, una comunidad por distrito, política v1.7.4 | `configuracion/politica_generacion_territorial_2025.yaml` | `17110e86a8bd36374816f7b5b0387a2f55fd50d5fde30977bd2f95b4810675b5` |
| Solo ganador por distrito, CC-BY-4.0 | `datos_abiertos/README.md` | (en el mismo árbol de INDEX) |
| 350 escaños; BOE-A-2023-18907 | `configuracion/resultados_oficiales_congreso_2023.csv` | `c7a636f2d4f08944b3a84cc9a6cd855bd5665eafd619d53a944e910e93475d8b` |
| Faltan Alicante, Barcelona y Málaga | las 49 claves de `INDEX.json` frente a las 52 de la política | (idem) |

Imágenes (sha256): `mapa_nacional_2023.png` `a440dc3a…bfe4`, `visor_nacional_escritorio_2023.png` `e1e58e6c…d155`, `visor_nacional_movil_2023.png` `7d6e6ff9…8e50`.

## Cómo se hicieron las capturas
Visor Nacional de la PR #513 (`8f6c96a`) sobre los 49 GeoJSON materializados con `herramientas/generar_datos_abiertos.py --materializar` (sha256 verificados contra `INDEX.json`). Sin mapa base (OSM y unpkg bloqueados en el entorno): MapLibre 5.7.0 desde npm, fondo liso. El encuadre del móvil se ajustó con `fitBounds` (a 390 px el visor carga con el mapa vacío al zoom inicial; lo anoto para T-84).

## Antes de usar
- Si se publican cifras nuevas (Alicante, Barcelona, Málaga o T-90 con escaños 2026 distintos), rehacer las capturas y la tabla.
- La propia nota advierte de que son distritos propuestos y de que solo consta el ganador de 2023.
