# Continuación NAC — 20-10-2026

Esta nota añade resultados al expediente existente; no reescribe `RESULTADO_EJECUCION_NAC_20261019.md` ni la evidencia histórica. Rama local `codex/nac-continuacion-20261020`, base exacta `6d489af7069aa8888a92618a07204fec6da17cc1`.

## Estado de integración y publicación

El incremento revisado anterior sigue disponible en el worktree conservado y no se alteró. La continuación se aisló en una rama derivada de su HEAD. La API de GitHub confirma permiso de repositorio `push=true`, pero `gh` no alcanza `api.github.com` y la escritura del conector GitHub fue previamente denegada bajo la política de aprobación activa `never`. No se intentó una vía alternativa de escritura. No existe PR para este HEAD ni CI remota asociable. `main` vigente comprobado por el conector: `2762b92db86b2207f11c5411392207fdd73056cf`. La comparación `2355b0e...` → `2762b92...` contiene dos commits y solo añade `docs/AUDITORIAS/F10_FUENTES_OFICIALES_20261020/ORIGENES_ELECTORALES_Y_PUERTAS.md`; no se incorporó ni se tocó el Gestor. El candidato sigue local y su commit `6d489af...` no existe en remoto.

## NAC-02 y NAC-01 — fuente histórica

El IGN anuncia que la capa temporal del WMS de Unidades Administrativas admite `TIME` y permite visualizar la evolución desde 2009. Esto acredita una capacidad de visualización temporal, no una exportación vectorial nacional ni la geometría fuente sin generalización. Un `GetMap` depende de BBOX, tamaño, CRS y renderizado; reconstruir límites desde imágenes no puede acreditar vértices, precisión ni integridad de identificadores. Por ello, no se acepta como fuente de contraste geométrico.

La colección OGC API Features `administrativeboundary` publica actualmente 48.195 objetos y campos como `nationalcode`, `date_boundary`, `legalstatus`, `endlifespanversion` y `accuracy`. El esquema declara CRS84 sin época indicada; `accuracy` es una cadena y los ejemplos de navegación muestran descripciones de método, no una tolerancia métrica uniforme. La colección es paginada y advierte que no se recomiendan límites altos. Estos metadatos y la lista actual no fijan un snapshot inmutable efectivo al 2025-01-01, no explican semántica jurídica suficiente para resolver vigencia en esa fecha, y no son por sí solos un manifiesto de páginas/objetos descargados. El auditor existente puede comprobar una captura suministrada (secuencia de `next`, consulta estable, `numberMatched`, IDs y SHA); no descarga el servicio ni acredita que el universo entregado fuese completo, estable o temporalmente válido.

En consecuencia, `NAT-C-056` permanece `BLOCKED_EXTERNAL`; no se adquirieron datos nuevos ni se elevó la acreditación. Requisitos concretos para solicitar al CNIG/IGN:

1. Paquete vectorial oficial e íntegro de límites administrativos, efectivo exactamente al 2025-01-01, que cubra las 50 provincias, Ceuta y Melilla; no una imagen WMS ni una edición actual presentada como histórica.
2. Identificación de producto, edición/snapshot inmutable, autoridad, fecha de publicación y adquisición, licencia y atribución, CRS por capa, precisión declarada, transformaciones, generalizaciones y linaje.
3. Capas y esquema completos, códigos estables, correspondencia CPRO/CUMUN, tipos de límite y estado jurídico/provisional; recuento total y cobertura por CPRO.
4. Explicación oficial del significado temporal de `date_boundary` y `endlifespanversion` (fecha efectiva, inclusividad, zona horaria y tratamiento de cambios/reversiones) y de `legalstatus`; documentación que permita seleccionar el estado existente en el instante de referencia.
5. Exportación original lossless (preferentemente GeoPackage/GML o equivalente), bytes y hashes SHA-256 por archivo, manifiesto de capas/registros y evidencia de paginación completa si se entrega por API: `numberMatched` constante, continuaciones sin huecos/duplicados y reglas para detectar cambios durante la extracción.
6. Si no existe el snapshot requerido, confirmación escrita de esa limitación y referencia al expediente/versión oficial que sí permita reconstruir el estado al 2025-01-01.

El paquete solo desbloquea el recibo para validación; no acredita automáticamente topología INE, excepciones ni los 52 informes.

## NAC-09 — diagnóstico acotado K>1

Se ejecutaron 44 unidades con K>1 sobre el grafo seccional físico ya acreditado, con la población INE 2025 y cotas exactas 85–115% del objetivo provincial. El solver existente de subconjuntos conexos agotó su presupuesto de estados exactos (`max_states=1`); se añadió una búsqueda DP acotada sobre un bosque generador determinista, que solo corta aristas físicas presentes y devuelve digest de testigo, nunca asignaciones.

- 6 unidades encontraron un testigo condicional sobre el grafo seccional: CPRO 10, 12, 16, 19, 37 y 50.
- 30 no encontraron testigo en el bosque seleccionado dentro del diagnóstico; en todas el solver exacto agotó su presupuesto. Esto **no demuestra inviabilidad** ni descarta otras topologías/árboles.
- 8 unidades CPRO 04, 07, 09, 15, 17, 27, 30 y 36 fueron detenidas por la condición registrada `physical_part_components > K`; la conclusión es condicional a la semántica/identidad de partes del producto y no sustituye la acreditación externa.
- En ningún caso se emitió una partición, producto, distrito o certificación. No se aplicaron disciplina municipal ni excepciones nominales a los testigos; no son resultados electorales ni prueba de factibilidad territorial integral.

Artefacto: `NAC_K_MULTIPLE_BOUNDED_20261020_final.json`, 44 casos, SHA-256 `bd48322c3d12f6c5a457cc510c19ea037d09ee8711bb4545a008463aa9b0dde7`. Una segunda ejecución en proceso separado generó exactamente los mismos bytes. Código y límites declarados en el propio reporte. `generation_authorized=false`, `districts_generated=0`.

## NAC-03 — robustez de capturas API

El auditor OGC API Features ahora rechaza claves JSON duplicadas en cualquier objeto (raíz o anidado), que el decodificador JSON estándar aceptaría con interpretación ambigua. Prueba negativa en `tests/test_congreso_ign_api_snapshot.py`; el byte anterior se conserva en `legacy/n08_nac_20261019/` y se registra el cambio de versión.

La revisión separada detectó un fallo en el conteo de estados al combinar componentes en el DP. Se corrigió para insertar cada cantidad de grupos una vez y conservar los cortes canónicos mínimos; una regresión de dos componentes independientes prueba un reparto K=2 sin puente ficticio. El caso no produjo un cambio en las seis provincias con testigo y el reporte real siguió siendo idéntico tras la corrección.

## Estados operativos posteriores

- `NAC-08`: `REVIEW_PASS_WITH_SCOPE_LIMITS` para el diff local revisado en sesión separada. No equivale a PR publicada, CI remota ni acreditación territorial; el HEAD de rama sigue siendo la base y los cambios son locales.
- `NAC-09`: `PARTIAL_PROGRESS`; la investigación constructiva K>1 se ejecutó con los resultados condicionales anteriores. No se puede cerrar factibilidad territorial porque 30 casos no hallaron testigo en el bosque explorado, 8 dependen de partes físicas, y quedan fuera las reglas municipales, acreditación externa y excepciones nominales.
- `NAC-01`: `BLOCKED_EXTERNAL`; receipt temporal oficial ausente.
- `NAC-04` y `NAC-05`: `NOT_EXECUTABLE` hasta que el receipt validado habilite contrastes por provincia y roll-up.
- Producción: permanece cerrada, sin distritos y `generation_authorized=false`.

La sesión revisora comprobó el diff final posterior a la corrección del contador, el fixture de componentes separados, hashes del sidecar/checkpoint, los 70 tests reportados y el SHA del artefacto. No reejecutó las pruebas al operar en solo lectura. La revisión histórica no se convierte automáticamente en aprobación remota ni territorial.

## Referencias oficiales de la comprobación web

Consultadas el 2026-10-20; se leyó metadato/presentación pública, sin descargar ni persistir geometrías:

- [Aviso IGN sobre la capa temporal WMS de Unidades Administrativas](https://www.ign.es/web/ign/portal/noticias?_IGNNoticias_WAR_IGNNoticiasportlet_advancedSearch=false&_IGNNoticias_WAR_IGNNoticiasportlet_andOperator=true&_IGNNoticias_WAR_IGNNoticiasportlet_cur=3&_IGNNoticias_WAR_IGNNoticiasportlet_delta=50&_IGNNoticias_WAR_IGNNoticiasportlet_keywords=&_IGNNoticias_WAR_IGNNoticiasportlet_resetCur=false&p_p_col_count=1&p_p_col_id=column-1&p_p_id=IGNNoticias_WAR_IGNNoticiasportlet&p_p_lifecycle=0&p_p_mode=view&p_p_state=normal): `TIME` permite visualizar límites históricos desde 2009.
- [Colección IGN OGC API Features](https://api-features.ign.es/collections/administrativeboundary), [esquema](https://api-features.ign.es/collections/administrativeboundary/schema) y [navegación de objetos](https://api-features.ign.es/collections/administrativeboundary/items?f=html): 48.195 objetos mostrados en la consulta; la lista y campos actuales no son snapshot histórico acreditado.
