# sitio/geometria — geometría de publicación

**Esto NO es evidencia de ejecución.** Es material derivado, destinado únicamente al
sitio público. La evidencia canónica de cada ejecución vive en
`territorios/<id>/resultados/ejecuciones/<run>/` y no debe mezclarse con esta carpeta.

## Qué contiene

Geometría de distritos disuelta, en GeoJSON comprimido, EPSG:4326:

| Fichero | Distritos | Población |
|---|---|---|
| `aragon_distritos.geojson.zip` | 67 | 1.364.621 |
| `castilla_y_leon_distritos.geojson.zip` | 82 | 2.401.221 |
| `extremadura_distritos.geojson.zip` | 65 | 1.053.345 |

Campos: `district_id`, `district_pop`, `geometry`.

## Cómo se generó

1. Reconstrucción del seccionado censal nacional 2025 (INE) desde `inputs/partes/`
   mediante `reconstruir_fuentes.sh`, con verificación de checksums.
2. Cruce de `CUSEC` con `CUSEC_KEY` del fichero `M06/composicion_distritos.csv` del
   run canónico de cada territorio.
3. Disolución por `district_id`, suma de población, reproyección a EPSG:4326.

Las tres coberturas cruzan el 100 % de sus secciones sin pérdida.

## Advertencia de procedencia

Estos ficheros son una **regeneración** de la geometría, no los artefactos originales
producidos por M06 en sus respectivas ejecuciones. Los checksums **no coinciden** con
los declarados en `PRODUCTOS.json`, porque dependen de la versión de las librerías
geoespaciales y del orden de escritura.

Consecuencia práctica:

- **Válido** para el mapa público, para Flourish y para inspección visual.
- **No válido** como evidencia de reproducibilidad. Para eso hay que recuperar los
  artefactos originales de GitHub Actions y colocarlos en la carpeta de ejecución
  correspondiente, donde su sha256 sí debe verificar.

## Limitación conocida que afecta a lo que se ve en el mapa

Al disolver, algunos distritos aparecen partidos en piezas separadas pese a que el
sistema los declara contiguos. Medido descomponiendo cada distrito en polígonos
simples y contando componentes conexas por intersección geométrica:

| Territorio | Distritos partidos | Trozos del peor caso |
|---|---|---|
| Aragón | 9 de 67 | 3 |
| Castilla y León | 15 de 82 | 7 |
| Extremadura | 8 de 65 | 2 |

La medición repetida con 1 metro de tolerancia arroja prácticamente las mismas cifras
(9, 15 y 7), lo que descarta que se trate de huecos de digitalización cerrables con un
`buffer_m` pequeño: son discontinuidades geométricas reales.

Causa: la validación de contigüidad opera sobre el grafo de adyacencia y no sobre la
geometría disuelta. Un distrito puede ser conexo en el grafo y estar partido en el mapa.

Esto afecta a los tres territorios, incluidos los dos declarados PASS, y debe resolverse
antes de considerar publicable ningún mapa.
