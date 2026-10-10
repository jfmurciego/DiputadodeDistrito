# Aragón 2025 — investigación factual y corrección propuesta para F10

Fecha: 2026-10-11. Estado: **candidato técnico; NO_PROMOTED; sin aprobación de merge ni reejecución**.

## Identificación inequívoca de la ejecución

- Repositorio: `jfmurciego/DiputadodeDistrito`.
- Run fallido: [38086465532](https://github.com/jfmurciego/DiputadodeDistrito/actions/runs/38086465532), `main@776006e62ebd80ab20a55b186c3778bce76e9f19`.
- Job original fallido: `114313978581`, paso `Adquirir y congelar fuentes`.
- Diagnóstico auténtico: artefacto [11683685832](https://github.com/jfmurciego/DiputadodeDistrito/actions/runs/38086465532/artifacts/11683685832), `ddd-source-diagnostics-aragon-2025-38086465532`, digest ZIP GitHub `sha256:f6d64c67d4ff819deb0f7b5b9198eeb0ef487d9315c90e539d420b33a06329aa`.
- El fallo posterior del job `resultado` es consecuencia de `PREPARATION_FAILURE`, no una segunda causa.
- La adquisición se bloqueó con `GEOMETRY_INVALID_AUDITED`; no existe paquete final `READY` ni receipt canónico del run.

## Evidencia material: bytes descargados, no solo logs

Se recuperó íntegro el ZIP de diagnóstico, que conserva las respuestas originales GeoJSON del INE y `geometry_normalization/secciones_censales_2025.json`. Integridad SHA-256 de los miembros:

| Provincia | Secciones de tipo SECCIONADO | Archivo | SHA-256 |
|---|---:|---|---|
| Huesca | 287 | `raw/secciones_censales/2025/22.geojson` | `7c69ebc3808855e390a6e200399cc07f469593d4349c2a38eee7ff81759c8cfb` |
| Teruel | 284 | `raw/secciones_censales/2025/44.geojson` | `f098229c37de572acba4a42aaf309f2d0d1f189060540a515a3eff59ccff035e` |
| Zaragoza | 892 | `raw/secciones_censales/2025/50.geojson` | `62dac177b1275b5968eb5c0df80524849b7d4c1e357899d6f5a581c06c3893ed` |

Secciones efectivas: **1.463**. Identidad del conjunto de geometrías antes y después de normalización: `fa9cf574cb29518ad4e2178309cb1924bd4addd261bcff5c7ae3a734d1e6dd94`. No hubo geometrías alteradas, ni nuevas intersecciones debidas a la normalización.

## Comparación directa con el consumidor M02

Se reconstruyeron independientemente las 1.463 geometrías de las respuestas oficiales, filtrando `TIPO=SECCIONADO`, y reproyectando de WGS84 a `EPSG:25830`, exactamente el CRS de trabajo de M02. Se evaluaron 4.302 pares que intersectan, usando `shapely.STRtree` y el predicado real de `modulos/02_construir_adyacencias.py`.

El contrato histórico `7.14.0` usaba `predicate: touches`, `min_shared_border_m: 1.0`, sin tolerancia para solapes. Da **4.063** aristas, coincidiendo con la referencia histórica del contrato Aragón. Con `predicate: contact`, `max_precision_overlap_area_m2: 0.025` y el mismo mínimo de frontera, da **4.070** aristas (**solo siete nuevas**). No se detectan cambios de componentes: un único componente con 1.463 secciones en ambos grafos; cero municipios con subgrafo desconectado en ambos.

De los once pares observados inicialmente por el auditor:

- **2** pasan a ser simples contactos (`touches=true`) en EPSG:25830, área 0, y ya están incluidos en las 4.063 aristas originales.
- **7** poseen solape positivo de precisión y frontera compartida ≥1 m; son las únicas aristas nuevas con `contact`.
- **2** tienen solape positivo pero frontera compartida 0 m; permanecen **sin arista** con `contact`. Admitir el solape de fuente no inventa conexión.

### Nueve solapes positivos evaluados en el CRS efectivo de M02

| Pareja de secciones | Solape m² | Frontera compartida m | Arista nueva |
|---|---:|---:|---|
| 4402502001–4402501003 | 0.0009709997 | 529.485 | Sí |
| 5008901003–5008901004 | 0.0021232358 | 299.246 | Sí |
| 5008901003–5008901007 | 0.0245334351 | 273.833 | Sí |
| 5008901005–5008901004 | 0.0069163009 | 1140.827 | Sí |
| 5008901005–5008901007 | 0.0001135387 | 622.052 | Sí |
| 5029708007–5029708020 | 0.0020772728 | 0 | **No** |
| 5029708007–5029708029 | 0.0000022293 | 5.133 | Sí |
| 5029708025–5029708020 | 0.0001219311 | 330.993 | Sí |
| 5029708025–5029708029 | 0.0007707258 | 0 | **No** |

La mayor área positiva es `0.0245334351 m²`; se declara explícitamente un techo de `0.025 m²`, en metros cuadrados reales, ligado al predicado del **consumidor M02**. En este dataset, utilizar 1 m² no añadiría más aristas que 0.025 m², pero se escoge el límite menor para reducir la superficie de aceptación de defectos futuros. Un área mayor queda `BLOCKED`.

No se confunde `touches` con ausencia de área: el análisis distingue el interior geométrico, el área de la intersección y la longitud real de la frontera compartida. Las áreas de 0 en EPSG:25830 no se tratan como solapes positivos.

## Corrección implementada en esta rama

1. Archivar **idéntico** el contrato anterior en `legacy/configuracion/aragon_2025_v7.14.0.yaml`.
2. Versionar `territorios/aragon/config/aragon_2025.yaml` como `7.15.0`, únicamente en su M02: `touches` → `contact`, `max_precision_overlap_area_m2: 0.025`, conservando `min_shared_border_m: 1.0`, `buffer_m: 0`, `simplify_m: 0`, CRS y demás parámetros.
3. Añadir regresión de M02 + admisibilidad de fuente: contacto genuino, cuña de precisión, exceso sobre techo, contacto puntual sin arista y conservación del contrato histórico.

**No** se modifica `ddd_core/official_geometry.py`, el descargador, fuentes oficiales, otras autonomías ni el contrato canónico #179. La tolerancia semántica de **normalización** permanece nula. La excepción es únicamente del **consumidor Aragón M02** y afecta su grafo: por ello la nueva versión debe revisarse y no hereda automáticamente la certificación histórica de K=67 / 4.063 aristas.

## Reproducción externa, desde el artefacto original

Descargar el ZIP auténtico del artefacto 11683685832 del run 38086465532. Con Python, `shapely`, `pyproj` y `networkx`, filtrar `TIPO=SECCIONADO`; transformar geometrías `EPSG:4326`→`EPSG:25830`; indexarlas con `STRtree`; para cada pareja que `intersects`, medir `boundary.intersection().length` y `intersection().area`; evaluar:

- **touches:** `a.touches(b) and shared_border >= 1`
- **contact:** `a.intersects(b) and shared_border >= 1 and (a.touches(b) or intersection_area <= 0.025)`

Resultados esperados: 1.463 secciones, 4.063 / 4.070 aristas, siete nuevas, un solo componente, cero desconexiones municipales.

## Puertas pendientes: ninguna promoción implícita

- CI y revisión independiente del nuevo contrato/efecto M02.
- Sólo tras autorizar e integrar la corrección, ejecutar de nuevo la adquisición aislada F10 de Aragón con SHA efectivo revisado.
- Descargar el nuevo paquete, confirmar `READY`, obtener bytes e informe de compatibilidad congelado, vinculándolos al run y artefacto exactos; emitir receipt #179 únicamente si todas las condiciones se cumplen.
- Verificar por separado regresión funcional de Aragón M01–M06, dado que el grafo nuevo ya no tiene 4.063 aristas.
- Castilla y León puede continuar en paralelo; no se toca ningún job en ejecución.
