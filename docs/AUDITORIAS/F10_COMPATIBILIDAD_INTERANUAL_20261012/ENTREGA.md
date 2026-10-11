# F10 — compatibilidad interanual

Versión: 1.0.0. Fecha: 2026-10-12. Estado: candidato; F10 PENDING.
Alcance: Fuentes Oficiales, incremento local sin promoción.
Origen: main `cb3927b93edc9dd67703316d3fa47d769a42dc5e`; documento nuevo, sin predecesor.
Cambios/motivo: corregir clasificación de correspondencias y conservar la evidencia de adquisiciones poblacionales fallidas.

La rama `codex/f10-compatibilidad-interanual` parte del merge #238. El worktree original, con tres archivos de auditoría sin seguimiento, permanece intacto. El desarrollo utiliza `/Users/macbookpro/Desarrollo/DDD-fuentes-f10-compatibilidad`.

## Correcciones implementadas

La conciliación exige intersección de interiores para reconocer contribuciones a divisiones y fusiones: compartir borde o punto ya no añade candidatos espurios. Un cambio de código resuelto por igualdad geométrica exacta elimina el bloqueo obsoleto del código anterior. El informe detalla cada población sin destino y su total; `accounting_exact` comprueba la contabilidad completa, mientras `exact_conservation` sigue exigiendo asignación exacta a las geometrías destino.

La adquisición de población guarda el payload original y su SHA antes de filtrar, incluso cuando falla la cobertura. Conserva la procedencia de snapshots separada del locator configurado y rechaza colisiones sin sustituir evidencia. Este cambio no recupera los bytes que faltan de la adquisición F10 de Valencia.

Se preservan ambos predecesores íntegros en `legacy/`; versiones 1.1.0 de compatibilidad y 1.4.1 de adquisición. Las herramientas son compartidas por los consumidores territoriales de los frentes autonómico y nacional; no cambia su gobierno, contrato ni acreditación.

## Resultado territorial

| Territorio | Población original | Asignada | Sin destino acreditado | Estado |
|---|---:|---:|---:|---|
| Aragón | 1.364.621 | 1.333.597 | 31.024 | BLOCKED |
| Andalucía | 8.676.713 | 8.356.724 | 319.989 | BLOCKED |
| Castilla y León | 2.401.221 | 2.317.024 | 84.197 | BLOCKED |

Los déficits proceden de cambios reales de frontera y correspondencias no biyectivas. La igualdad exacta acredita las correspondencias permitidas; no existe en el contrato vigente una regla para redistribuir los habitantes de las demás. La contabilidad completa es exacta, pero la conservación en el destino sigue fallando. La auditoría `reconciliacion.json` identifica inputs, hashes, cambios y habitantes por sección; las regresiones usan extractos geométricos reales vinculados a esos inputs.

Comunidad Valenciana: un snapshot histórico INE ya conservado acredita población 2023 en las tres provincias, incluidas 1.823 secciones observadas en Valencia (46). Su igualdad con el payload F10 perdido no puede demostrarse. Queda como evidencia independiente no promovida. Las cuatro reparaciones geométricas seguras ya existentes se conservan; dos solapamientos originales de 11,827709 y 12,111238 m² superan el techo contractual de 1 m². Eliminarlos requiere cambiar las fronteras o el contrato. El detalle está en `comunidad_valenciana.json`; no se relajan tolerancias.

Extremadura: producto M06 `36472516474`, preparación histórica `35755043806` y receipt F10 `38091144559` mantienen sus identidades y funciones separadas. El receipt F10 permanece independiente y no promovido. Los hashes del catálogo y evidencias protegidas coinciden byte a byte con la base.

## Validación

La suite relevante pasó 119 pruebas; las 17 comprobaciones adicionales de linaje y gobierno también pasaron. El primer intento de la suite usó Python 2.7 en un subproceso y falló por el entorno: se repitió con el intérprete aislado en `PATH`. El entorno Intel usa Shapely 2.1.2, GeoPandas 1.1.2, PyProj 3.6.1 y PyOgrio 0.8.0, sin modificar dependencias del repositorio; CI valida el entorno canónico.

El verificador `verificar_consumidores.py` comprueba bytes históricos offline, compara el linaje protegido con la base y produce `consumidores.json`: **14 PASS / 5 BLOCKED**. Permanecen bloqueados Andalucía, Aragón, Castilla y León, Comunidad Valenciana y Extremadura por las puertas canónicas existentes. Los otros catorce consumidores mantienen su acreditación. No se presenta la contabilidad de candidatos como acreditación productiva.

La revisión en sesión separada, el SHA final y la CI se registran en el plan externo `/Users/macbookpro/Desarrollo/DDD-control/planes/f10-compatibilidad-interanual-20261012/` y en la PR en borrador. Su dictamen técnico se limita a este incremento y no cierra F10 ni autoriza promoción.

No se repitieron adquisiciones oficiales ni se ejecutaron `00`, M01–M08, campañas, generación de distritos, publicación o merge. Los bloqueos obligatorios mantienen **F10 PENDING**.
