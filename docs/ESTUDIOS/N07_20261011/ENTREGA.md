# Entrega nacional local N07 y continuidad

Versión 1.0.0; fecha 2026-10-11; candidato CI_PENDIENTE; origen nuevo.
Alcance: mandato Congreso del Plan Maestro ddd-maestro-20261008. No constituye cierre del Plan.

N07 entrega `result/crosswalk.csv`: 36.554 secciones de la edición INE 2025, asignadas exactamente a los 52 códigos oficiales CPRO. Cada CUSEC coincide con CUMUN+CDIS+CSEC y CUMUN con CPRO+CMUN. Ceuta (51, municipio 001) tiene 56 secciones y Melilla (52, municipio 001) 44. No se usan reglas de K ni ediciones poblacionales. La orden actual autoriza esta correspondencia técnica antes de N06, sin modificar la dependencia productiva del Plan Maestro.

El ZIP reconstruido debe coincidir con SHA-256 `55c9da7e34d3bb3cb725400c35b58e72f4db2ea8321ef91237a89e708d2dbcc4`, protegido en inputs/MANIFEST.sha256. Se reutiliza sectioning_reference y se contrastan los recuentos del inventario conservado. El CSV se relee y compara contra el universo original: claves, atributos, cobertura, cero pérdidas, extras y duplicados. evidence.json conserva hash de CSV, de cada miembro del ZIP y de la identidad geométrica por CUSEC, CRS y runtime.

Las 36.554 geometrías son no vacías e individualmente válidas; no se transforman. Esto no certifica adyacencias, ausencia de solapamiento geométrico entre secciones, conectividad física, overlay contra límites provinciales independientes ni admisibilidad productiva. La asignación provincial es la declarada y corroborada por atributos de la misma fuente oficial. No se extrapola equivalencia con 2022, otras ediciones o las 391 geometrías históricas. No se ha generado ningún distrito.

## Reproducción offline

Usar un intérprete con las dependencias de requirements-cartografia-nacional.lock y geopandas/pyogrio ya disponibles; no se instala ni descarga nada. En esta sesión: /usr/local/Caskroom/miniforge/base/envs/ddd/bin/python.

```sh
python -c "from pathlib import Path; p=Path('/tmp/n07-source.zip'); p.write_bytes(b''.join(x.read_bytes() for x in sorted(Path('inputs/partes').glob('seccionado_2025.zip.part*'))))"
python herramientas/crosswalk_nacional.py /tmp/n07-source.zip /tmp/n07-reproduccion-nueva
python -m unittest discover -s tests -p 'test_crosswalk_nacional.py' -v
python herramientas/evidencia_continuidad_nacional.py /tmp/nacional-diagnostico-nuevo
python -m unittest discover -s tests -p 'test_evidencia_continuidad_nacional.py' -v
```

Destinos nuevos obligatorios. Los CSV y hashes son deterministas; las versiones de runtime pueden diferir. El validador reutilizable validate_rows acepta universo y correspondencia independientes y recuentos esperados, rechaza sustituciones aun manteniendo recuentos, claves incoherentes, identidades numéricas, duplicados, pérdidas y municipios incorrectos en ciudades.

## Continuación conservada

Contrato: cuatro archivos recuperados byte a byte desde ae4a1cb68c352fcbde84d556e38992cf7e1906d7, incluyendo sus correcciones anteriores. No se repite su investigación ni el piloto sintético propuesto en la documentación histórica. Se ejecutan únicamente regresiones. Mantiene WAIT_OWNER, generación false, separación de los 19 ámbitos autonómicos y rechazo de objetos alternativos contaminantes.

Base inicial nacional: 7d50f7f5f2695cfac339122b5d7a95953a37d1f7. main local era 2d8508a0; lectura remota y fetch sin merge actualizan origin/main a cb3927b93edc9dd67703316d3fa47d769a42dc5e (PR #238). La base comunicada 4f9fd499 está disponible tras fetch. Ninguna de las cuatro rutas del contrato existe en origin/main; se prepara su incorporación y regresión en una copia temporal de ese árbol, sin fusionar ramas ni tocar main. La integración queda preparada localmente, CI_PENDIENTE y sin aprobación productiva.

N03: BLOCKED, los bytes históricos están conservados y verificados, pero los descriptores no acreditan fuente ni edición de geometría/población. No se inventa una pareja temporal.

N04: diagnóstico material completo. El índice 44/ID 44 pertenece a provincia 07 (no a provincia 44). Su único hueco está fuera del shell: explain_validity y covers lo confirman. Se conserva íntegro el original con hash a2c8f630bd84c8d7b31724496cb86db676b9765e5ad986a5b485dc60f813b756. Tratamiento: rechazar geometría inadmisible, sin make_valid, borrado del hueco ni sustitución. Una reparación requiere fuente o transformación acreditadas.

N05/N06: las cinco alternativas se reproducen con el modelo protegido. K=383 (inferior), 407 (más próximo), 435 (superior), 409 (Hamilton) y 409 (mínimos de referencia). continuacion/evidence.json incluye consecuencias por cada provincia, métricas y restricciones. 383 deja sin representación Soria/Ceuta/Melilla; 407/409/435 exceden el máximo constitucional de referencia del análisis. Barreras provinciales, suelo hipotético 96.000 y representación positiva en las tres circunscripciones pequeñas son incompatibles. No se adopta K ni contrato; N06 queda WAIT_OWNER.

N08–N10 permanecen BLOCKED para ejecución productiva: faltan contrato aprobado, fuentes admisibles y autorización. No se cambian políticas, reglas, geometrías ni catálogos autonómicos.

## Conservación y revisión

Archivos nuevos con versión/origen; las cuatro rutas del contrato no tenían predecesor en este worktree y se recuperan con identidad Git exacta. No se sustituye ningún archivo funcional existente. CI remota pendiente; ninguna ejecución territorial ni certificación. Pruebas y revisión se conservan en este expediente.

El Plan Maestro externo está fuera de las raíces de escritura permitidas de esta sesión. checkpoint.json registra un delta de continuidad con los IDs originales, la identidad de estado/plan leídos y evidencias locales, sin crear otro plan ni reescribir el estado externo.

Push / PR / merge / workflows / generación territorial / publicación: NO.

La conservación Git en la rama original está bloqueada ambientalmente: index.lock reside en el Git compartido fuera de las raíces escribibles. Se conserva el mismo árbol en un repositorio temporal independiente, con padre exacto 7d50f7f5 y bundle incremental dentro del expediente; la rama original permanece sin mover y el diff nuevo queda íntegro. El bundle requiere ese padre, ya existente en el almacén original. No se presenta como commit de la rama original.

Comprobación estática del incremento: los archivos nuevos pasan diff --check; el documento contractual recuperado conserva cuatro espacios finales Markdown de ae4a1cb, reportados por Git. Se conservan los bytes exactos; no se declara PASS global de diff --check.
