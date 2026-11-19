# T-416 (b) — Propuesta de limpieza de R2 (solo propuesta; no se ha borrado ni movido nada)

## Resumen para el propietario
1. El almacén de trabajo pesa 16,47 GB: 6,47 GB por encima de los 10 GB gratuitos. Coste actual: unos 0,10 USD/mes (6,466 GB × 0,015 USD/GB·mes). No urge por dinero.
2. Lo que ve el visor no está en R2: sus 481 productos son blobs de git. Ninguna limpieza de R2 afecta al visor publicado.
3. El peso está en `arc-e` (12,87 GB, el 78 %): fuentes oficiales y paquetes P10, que el motor sí necesita. Sin tocarlo no se baja de 10 GB.
4. Lo demás (3,59 GB) son restos: estados completos viejos (1,81 GB), productos de runs superados, la carpeta `bateria` retirada, vídeos y una prueba de conexión.
5. Propuesta: borrar unos 2,2 GB seguros tras la regeneración posterior al 29-11, conservar `arc-p` (1,11 GB) hasta entonces, y pedir un listado más fino de `arc-e` (un nivel más) antes de decidir ahí.
6. Con solo lo seguro quedaría en unos 14,3 GB (aún sobre el límite); bajar de 10 GB exige recortar `arc-e` (hasta ~6 GB posibles si hay paquetes P10 de versiones antiguas; sin confirmar).
7. Los nombres antiguos (`andalucia`, `congreso_alava`…) no se renombran: R2 no renombra, solo copia y borra. Tras regenerar, lo nuevo se escribe con el id nuevo (`aut01`, `nac01`) y lo antiguo se borra.
8. Nada se borra antes de la regeneración; el borrado lo hace el Operador con tu permiso.

## Entrada y alcance
Run 44541851289 («P70 Archivo · P74 Listar», job 135621981618, `main` f6682bb): 150 carpetas de primer nivel, 16,466 GB (164,7 %). P74 solo da el primer nivel; no distingue subprefijos de `arc-e`. Cruzado con `orchestracion/archivo_r2.json` (1.033 claves, 2,279 GB), `almacen_m06_r2.json` (51 objetos, 1,112 GB), `fuentes_r2.json` (641 objetos indexados en `arc-e/fuentes/`, 0,935 GB), `publicaciones_visor.json` (481 productos, todos `repository_blob`; 281 runs distintos), `catalogo_procedencia.json` (71 paquetes P10) y `catalogo_preparacion.yaml` (74 `package_sha256`). El bucket de vídeos (D-175) no se toca. Los números de objetos por carpeta coinciden con el manifiesto en las 145 carpetas de territorio.

## Tabla por carpeta o grupo
| Carpeta / grupo | Tamaño (objetos) | Uso | Propuesta | Motivo |
|---|---:|---|---|---|
| `arc-e` | 12,872 GB (791) | Fuentes oficiales (`arc-e/fuentes/`, 641 objetos, 0,935 GB indexados) y paquetes P10 (`arc-e/paquetes-p10/<package_sha256>.zip`) que leen P10, la 00 y P80 | **CONSERVAR**; revisar sobrantes con listado de 2.º nivel | Insumo de la regeneración. Los 150 objetos restantes (~11,94 GB) serán sobre todo paquetes P10; el catálogo exige 71-74 y puede haber versiones antiguas (hipótesis sin medir). Borrar solo los `package_sha256` que ningún contrato vigente cite |
| `arc-p` | 1,112 GB (51) | Almacén M06 (`almacen_m06_r2.json`, T-302); P72 recupera composiciones M06 de aquí | **CONSERVAR** hasta la regeneración; después decidir | Fuente de recuperación de las 63 composiciones; la regeneración crea M06 nuevo. Los releases `almacen-m06-*` son origen, no copia verificada |
| 19 carpetas con nombre antiguo de comunidad (`cataluna`, `madrid`, `andalucia`…) | 1,994 GB (210) | Archivo de artefactos de la 00 (`archivo_r2.json`) | **BORRAR** tras regenerar (ver estados abajo) | Ids antiguos (D-61); lo nuevo se escribe en `autNN` |
| de ellas: 12 `ddd-state-*` (etapa M08 de 12 runs vigentes) | 1,812 GB (12) | Checkpoint de «Reutilizar progreso»; el visor no los usa | **BORRAR** tras regenerar | Regenerables con la 00 «Generar desde fuente». Excepción: `principado_de_asturias/40132061626` (10 MB), única copia de su M08; conservar hasta que la regeneración publique Asturias |
| de ellas: `ddd-minimo`/`ddd-audit` de runs no publicados | ~0,058 GB (79) | Ninguno | **BORRAR** tras regenerar | Runs superados; el visor no los cita |
| de ellas: `ddd-minimo`/`ddd-audit` de runs publicados | ~0,124 GB (119) | Evidencia del producto vigente | **CONSERVAR**; borrar tras regenerar y publicar | Se sustituyen por los nuevos |
| 19 `autNN` | 0,086 GB (83) | Ídem, id nuevo | **CONSERVAR** | Ya con el nombre D-131 |
| 52 `nacNN` | 0,056 GB (212) | Ídem | **CONSERVAR** | Ya con el nombre D-131 |
| 52 `congreso_*` | 0,137 GB (516) | Ídem, id antiguo del Congreso | **BORRAR** tras regenerar (o RENOMBRAR a `nacNN` solo si se quiere conservar evidencia) | Duplican a `nacNN` por provincia; regeneración los reemplaza. Producto vigente: ~0,095 GB |
| 3 `congreso350_*` | 0,003 GB (12) | Mapa de 350 fuera del corte (D-76) | **CONSERVAR** | Ids sin migrar; tamaño ínfimo |
| `bateria` | 0,049 GB (19) | Sin lectores: `bateria/entradas` se retiró en T-303; los workflows usan rutas locales | **BORRAR** (tras comprobar el contenido con un listado fino) | Resto huérfano |
| `videos` | 0,152 GB (2) | Vídeo en el bucket de trabajo; D-175 lo lleva a un bucket aparte | **CONSERVAR** hasta confirmar el vídeo en el bucket público; entonces **BORRAR** | No se toca el otro bucket |
| `connection-tests` | ~0 GB (1) | Prueba de conexión | **BORRAR** | Sin uso |

Todos los números de las filas de territorio salen del manifiesto del 16-11; el reparto vigente/no vigente cruza `run_id` con los 281 runs del visor (268 aparecen en el archivo; 13 no tienen archivo y no dependen de R2).

## Ahorro y coste
| Concepto | GB |
|---|---:|
| Estados `ddd-state-*` (tras regenerar; Asturias, tras publicar) | 1,812 |
| Minimos/audit de runs superados | 0,058 |
| `congreso_*` y nombres antiguos de productos vigentes (tras regenerar) | ~0,22 |
| `bateria` + `connection-tests` | 0,049 |
| `videos` (tras confirmar bucket público) | 0,152 |
| **Subtotal seguro** | **~2,3** |
| `arc-p` (decisión posterior) | 1,112 |
| `arc-e`: paquetes P10 sin contrato vigente | hasta ~6 (sin medir) |

- Actual: 16,466 GB; por encima del gratuito 6,466 GB → ~0,097 USD/mes (tarifa R2 de almacenamiento 0,015 USD/GB·mes; sin contar operaciones).
- Tras lo seguro: ~14,2 GB → ~0,06 USD/mes. Con `arc-p`: ~13,1 GB. Para bajar de 10 GB hay que recortar `arc-e` en al menos ~3-4 GB.
- Ahorro máximo en dinero: ~0,10 USD/mes. El motivo real es el límite gratuito, no el coste.

## Condiciones y próximos pasos
1. Precondición del borrado: regeneración posterior al 29-11 (T-313/T-379 PR 3, D-166, D-171) con los productos nuevos verificados; después el Operador lanza P73 «podar» con lista versionada (sha aprobado) y entorno `produccion`.
2. Pedir una ampliación de solo lectura de P74 (tamaño por subprefijo de `arc-e`: `fuentes/`, `paquetes-p10/`, otros, con `package_sha256` frente al catálogo) antes de decidir nada en `arc-e`. Esa herramienta no existe aún; es otra tarea.
3. `podar_r2.py` solo borra `ddd-state-*` de la lista T-145 y nada bajo `arc-e/`; borrar el resto exige ampliar su alcance con PR revisada.
4. Renombrar carpetas (D-131) queda como tarea aparte; esta propuesta recomienda no renombrar y reescribir con id nuevo al regenerar.
5. Verificar antes de borrar: sha256 de cada clave y que el manifiesto se actualiza; que `publicaciones_visor.json` no cita R2 (hoy ninguno).

## Límites de esta propuesta
- Sin acceso a R2 desde la nube: el contenido de `arc-e` por subprefijo, de `bateria`, `videos` y `connection-tests` no está medido, solo deducido del repositorio.
- Los productos «vigentes» se identifican por `run_id` en el visor; no se abrió ningún ZIP.
