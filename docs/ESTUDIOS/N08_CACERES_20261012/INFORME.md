# N08 Cáceres: puerta técnica M01–M06

**Versión 1.0.0; 2026-10-12; candidato.** Alcance: recorrido de diagnóstico de Cáceres sobre fuentes 2025 y producto topológico N08 acreditados. **No ejecuta una partición ni autoriza producción.** Nuevo expediente, sin predecesor.

El preflight reproducible finaliza en `BLOCKED_CONTRACT_OR_OWNER_DECISIONS`. Admitió las entradas reales de M01, reconstruyó las adyacencias con el consumidor M02 y las componentes con M03: 411 secciones, 388.190 habitantes, 1.125 aristas físicas, K=3, una componente seccional y una componente de partes. Los pares calculados por M02 coinciden exactamente con el grafo N08 de la unidad `10.json.gz`. No se aplicaron buffers, simplificaciones, puentes ni transformaciones de CRS en la comparación. El filtro de longitud positiva de 1 nm excluye únicamente contactos puntuales; el cero admite puntos en la implementación existente.

M04 pasa únicamente el límite estructural necesario por componentes (1 ≤ 3), que no demuestra que exista una partición viable. Queda bloqueado porque el contrato no declara límites poblacionales territoriales y `hard_limits` los exige con fallo explícito. M05 comprobó sus invariantes finales únicamente sobre un fixture sintético; no hay entrada M04 ni se ejecutó el optimizador. M06 pasó solamente una prueba sintética de contrato de trazabilidad, cobertura, cuota, conectividad y población; se ejercitó además `joined_unique` del consumidor real. No se produjo una salida distrital de Cáceres.

El producto registra 11 municipios físicamente discontinuos: `10010`, `10038`, `10039`, `10049`, `10084`, `10124`, `10125`, `10126`, `10143`, `10177`, `10195`. No son una imposibilidad estructural por sí solos; su tratamiento requiere política municipal y territorial aprobada. Hay cero solapamientos y cero vacíos encerrados en la unidad, según el producto acreditado.

La puerta verificó identidad del contrato, hashes de edición 2025, manifiesto N08, artefacto provincial, crosswalk N07 y CSV de población. Referencias en `preflight/PREFLIGHT.json`; los hashes no reemplazan los originales protegidos. La cobertura y población nacional se revalidan mediante el loader certificado existente; no se repitió el análisis de las otras provincias.

## Resultado por módulo

| Módulo | Resultado | Evidencia / límite |
|---|---|---|
| M01 | PASS | Cargadores reales de Shapefile y CIP; unión 1:1 por CUSEC; geometría, municipio y población coinciden con los 411 nodos. |
| M02 | PASS | `iter_edges` real devuelve exactamente las 1.125 aristas N08; umbral positivo 1 nm para excluir puntos, sin buffer, simplificación ni puentes. |
| M03 | PASS | Constructor real de nodos; atributos de administración y población coinciden; componentes reconstruibles iguales a N08. |
| M04 | BLOCKED | El límite de componentes no descarta imposibilidad. Faltan `population_floor_ratio`, `population_cap_ratio`, `target_tolerance_ratio` y políticas aplicables. |
| M05 | SINTÉTICO PASS | El verificador final real valida un fixture sintético con conectividad, municipio y límites; no se ejecutó el optimizador ni se particionaron datos reales. |
| M06 | SINTÉTICO PASS | El adaptador audita un fixture de K nodos parametrizado por provincia/cuota y el consumidor real une CUSEC; no acredita salida real. |

`generation_authorized=false`, `districts_generated=0`, `real_partition_created=false` y `published=false` constan en el informe y checkpoint.

## Bloqueos y siguiente acción

El contrato devuelve `CIRCUMSCRIPTION_COVERAGE_NOT_ACCREDITED_52_OF_52` y decisiones pendientes para unidad mínima, contigüidad, límites poblacionales, indivisibilidad municipal, islas, enclaves y discontinuidades físicas. Cáceres tiene además 11 municipios discontinuos que deberán evaluarse bajo esas reglas. Sin rellenar los límites a partir de Aragón u otro territorio, M04 rechaza la configuración.

Work debe aprobar expresamente esos campos y el modo de tratamiento de cada municipio discontinuo. Sigue además activo `CIRCUMSCRIPTION_COVERAGE_NOT_ACCREDITED_52_OF_52`; la puerta exige que desaparezca junto con las decisiones locales antes de devolver PASS. Después se vuelve a ejecutar esta misma puerta para comprobar el contrato actualizado. Aunque quede en PASS, se requiere autorización separada y expresa para ejecutar M01–M06 en modo controlado; este cambio nunca activa `generation_authorized` por inferencia.

## Reproducción

El comando, entorno y salida están en `logs/ejecucion_final.txt`. `logs/reproduccion_final.txt` registra la segunda ejecución y la igualdad byte a byte de PREFLIGHT y CHECKPOINT. El informe y checkpoint incluyen el SHA-256 de la herramienta ejecutada. `MANIFEST.json` contiene los hashes del código y entradas; el checkpoint permite repetir sin modificar datos acreditados.
