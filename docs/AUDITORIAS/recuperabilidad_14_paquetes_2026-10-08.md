# Recuperabilidad de los 14 paquetes territoriales exactos

**Versión:** 1.0.0 — Inventario de recuperación sin regeneración
**Fecha:** 2026-10-08
**Alcance:** 14 candidatos del inventario cerrado; búsqueda local y metadatos remotos.
**Estado:** CI_PENDIENTE; DESCARGA_PENDIENTE_AUTORIZACION.
**Cambio y motivo:** inventario nuevo para recuperar y conservar paquetes exactos.
**Origen:** `2ad0446adfea94543e8116ed55086e4128b1d153`; documento nuevo, sin predecesor.

## Referencia y método

Se continúa en `codex/fuentes-oficiales`, limpio al inicio y HEAD coincidente con el origen. No se rehace la matriz de 19 territorios. Referencia exclusiva: `fuentes_oficiales_19_territorios_2026-10-08.json` y su informe. No se modifica la selección territorial ni ningún receipt.

Primero se buscaron nombres de paquetes y manifiestos con rg en Desarrollo, Downloads, Library/Caches y /private/tmp. Después se inspeccionaron en sólo lectura 49 ZIP pertinentes DDD (incluidos nombres genéricos files*/Compress.zip en Downloads), sus hashes y los miembros manifest.json/ZIP de paquete fuente. No hubo coincidencias con ninguno de los 28 digests esperados (artifact y package). Se inspeccionó además ~/.cache sin encontrar nombres de paquete/manifiesto/ZIP. Library/CloudStorage no existe y /Volumes sólo muestra HD -> /; no hay almacenamiento externo montado identificado. Los snapshots nacionales ya diagnosticados no se convierten en paquetes preparados.

Límites: búsqueda acotada; no prueba ausencia absoluta en todo el disco. Se excluyeron .git, dependencias, cachés privadas de aplicaciones Apple y codex-daemon. Docker build cache declarado type=gha no acredita una copia recuperable del paquete. Las copias alternativas quedan NO_LOCALIZADAS; no se accedió a cuentas, buckets ni credenciales sin referencias concretas. Rutas, tamaños, hashes y resultados locales están en el JSON adjunto.

Se efectuaron 15 consultas de metadatos: una inicial sin filtro al run de Canarias (37596900111), seguida de 14 consultas filtradas por nombre exacto mediante `mcp__codex_apps__github_fetch_workflow_run_artifacts`, repo `jfmurciego/DiputadodeDistrito`, run_id del inventario. El conector devuelve primera página; cada respuesta filtrada contiene un único artifact esperado. Se conservan solicitud, fecha UTC, respuesta, artifact_id, URL, tamaño, expiración, digest y head_sha. Se exige nombre, digest, run_id y source_commit coincidentes y expired=false. No se descarga el archivo ni se consulta su contenido.

**Resultado:** 14 RECUPERABLES por metadatos; 0 CADUCADOS, 0 AUSENTES y 0 INDETERMINADOS en el inventario remoto exacto. Recuperable significa que existe la identidad remota esperada, no que los bytes ya estén recuperados o validados. Todas las fechas siguientes son UTC; disponibilidad sujeta a borrado o cambios posteriores.

## Tabla de recuperación

| Territorio | Estado | Run | Artifact ID / fuente exacta | Bytes | Caduca (UTC) |
|---|---|---|---|---:|---|
| Principado de Asturias | Recuperable | 37438440043 | [11400346349](https://api.github.com/repos/jfmurciego/DiputadodeDistrito/actions/artifacts/11400346349) | 1,663,660 | 2026-11-05T08:48:31Z |
| Islas Baleares | Recuperable | 37589792776 | [11468266327](https://api.github.com/repos/jfmurciego/DiputadodeDistrito/actions/artifacts/11468266327) | 7,865,466 | 2026-11-06T07:51:12Z |
| Canarias | Recuperable | 37596900111 | [11471001626](https://api.github.com/repos/jfmurciego/DiputadodeDistrito/actions/artifacts/11471001626) | 8,669,104 | 2026-11-06T08:55:35Z |
| Cantabria | Recuperable | 37318299003 | [11349491600](https://api.github.com/repos/jfmurciego/DiputadodeDistrito/actions/artifacts/11349491600) | 699,409 | 2026-11-04T13:39:05Z |
| Castilla-La Mancha | Recuperable | 37444564173 | [11402817303](https://api.github.com/repos/jfmurciego/DiputadodeDistrito/actions/artifacts/11402817303) | 12,413,530 | 2026-11-05T09:41:33Z |
| Cataluña | Recuperable | 37453376100 | [11408176177](https://api.github.com/repos/jfmurciego/DiputadodeDistrito/actions/artifacts/11408176177) | 14,493,802 | 2026-11-05T11:00:16Z |
| Galicia | Recuperable | 37155903096 | [11286084988](https://api.github.com/repos/jfmurciego/DiputadodeDistrito/actions/artifacts/11286084988) | 3,745,544 | 2026-11-02T22:19:45Z |
| Comunidad de Madrid | Recuperable | 37325328346 | [11352550551](https://api.github.com/repos/jfmurciego/DiputadodeDistrito/actions/artifacts/11352550551) | 4,060,247 | 2026-11-04T14:32:18Z |
| Región de Murcia | Recuperable | 37344628042 | [11359767395](https://api.github.com/repos/jfmurciego/DiputadodeDistrito/actions/artifacts/11359767395) | 1,725,771 | 2026-11-04T16:57:27Z |
| Comunidad Foral de Navarra | Recuperable | 37293310755 | [11337631456](https://api.github.com/repos/jfmurciego/DiputadodeDistrito/actions/artifacts/11337631456) | 6,257,751 | 2026-11-04T09:57:31Z |
| País Vasco | Recuperable | 37458584767 | [11410062497](https://api.github.com/repos/jfmurciego/DiputadodeDistrito/actions/artifacts/11410062497) | 14,138,865 | 2026-11-05T11:47:19Z |
| La Rioja | Recuperable | 37298033194 | [11340727361](https://api.github.com/repos/jfmurciego/DiputadodeDistrito/actions/artifacts/11340727361) | 653,639 | 2026-11-04T10:41:20Z |
| Ceuta | Recuperable | 37442375016 | [11401374000](https://api.github.com/repos/jfmurciego/DiputadodeDistrito/actions/artifacts/11401374000) | 90,652 | 2026-11-05T09:22:31Z |
| Melilla | Recuperable | 37315646335 | [11347967683](https://api.github.com/repos/jfmurciego/DiputadodeDistrito/actions/artifacts/11347967683) | 239,562 | 2026-11-04T13:18:36Z |

El JSON fija para cada fila nombre exacto, digest artifact, digest package, edición 2025, años de fuentes, identidad territorial, receipt y source_commit. No se presume que un ZIP con igual nombre o un checkpoint que contenga fuentes tenga la misma identidad.

## Volumen y prioridad

**Total recuperable:** 76.717.002 bytes = 76,717 MB = 73,163 MiB, suma de size_in_bytes de los 14 artifacts. Es tamaño de descarga comprimida declarado; no incluye overhead HTTP ni espacio descomprimido, desconocido antes de inspeccionar los archivos. Descargado: **0 bytes de paquetes**. No hay autorización masiva.

1. Piloto propuesto: **Melilla**, artifact `11347967683`, **239.562 bytes** (0,228 MiB), menor paquete de un territorio sin producto territorial certificado y con puerta documental habilitada. Descargar sólo ese artifact tras autorización; verificar SHA exterior `6fde2422b0e1956d4e31cf19763468f95a50653535ef9d1e3dff4ae4b5803baa`, manifiesto y package SHA `cc427ca1d5ce00ecac5c70678773fd2c2592129af1b7203151ed5ebd2a86f95b`, inventario, compatibilidad, identidad y receipt antes de declarar recuperación validada.
2. Próximos candidatos sin producto y sin bloqueo adicional registrado, por tamaño: La Rioja (653.639), Comunidad de Madrid (4.060.247), Comunidad Foral de Navarra (6.257.751), Islas Baleares (7.865.466), Canarias (8.669.104), País Vasco (14.138.865). Total de este grupo incluido Melilla: 41.884.634 bytes. Cada lote necesitará una autorización concreta; no se interpreta el piloto como permiso para descargarlo.
3. Conservar también los paquetes de territorios con certificación histórica: Ceuta (90.652), Cantabria (699.409), Principado de Asturias (1.663.660), Galicia (3.745.544; expiración más próxima: 2026-11-02), Castilla-La Mancha (12.413.530). Total: 18.612.795 bytes. Prioridad de conservación por expiración puede adelantarse a la prioridad de desbloqueo.
4. Cataluña (14.493.802) y Región de Murcia (1.725.771), total 16.219.573 bytes: recuperables, pero la recuperación no resuelve los bloqueos de persistencia y conectividad documentados. No se ejecuta generación para comprobarlos.

## Diseño de conservación permanente (sin migración)

Propuesta local pendiente de la autorización de descarga: directorio estable del worktree `.ddd-source-vault/sha256/<artifact_sha256>/artifact.zip`, fuera de /tmp y separado de evidencias productivas. Se guarda el ZIP original sin recomprimir, acompañado de metadatos de recuperación (repositorio, run/artifact ID y nombre, URL estable de API, tamaño, fecha UTC, source_commit, edición, identidad y hashes esperados/observados), copia idéntica del receipt y SHA del receipt. La copia extraída para validación se mantiene separada. No se almacenan URLs temporales firmadas ni tokens. No se añade automáticamente el ZIP a Git ni se crea aquí el directorio.

Tras una descarga autorizada: reconsultar metadatos y bloquear si cambió identidad; descargar sólo el ID autorizado a archivo parcial; calcular tamaño/SHA exterior antes de aceptar el ZIP; comprobar miembros y confinamiento de rutas antes de extraer; verificar manifest, paquete interior, materializaciones y compatibilidad con el validador existente; reconciliar identidad territorial/edición/años con receipt. Cualquier diferencia queda en cuarentena y no modifica catálogos. Registrar estado RECUPERADO_VALIDADO sólo después de esas comprobaciones. El archivo original se conserva por contenido sin sobrescritura; las observaciones se añaden como registros nuevos.

El directorio estable evita depender del vencimiento del artifact, pero **no garantiza durabilidad ante pérdida del disco o retirada del worktree**. Antes de una migración general debe acordarse almacenamiento permanente independiente del worktree y copia de seguridad con la misma identidad por contenido; este encargo sólo diseña ese contrato de conservación, sin desplegar almacenamiento remoto, alterar Git ignore ni modificar consumidores de los otros frentes.

## Verificación y cierre

Se comprueba que hay exactamente 14 filas del inventario de referencia, identidad metadata completa coincidente, URLs exactas, receipts existentes e identidades consistentes, sumas de volumen y cero descargas. No se repiten tests funcionales del diagnóstico anterior: no hay cambio de código ni ejecución de fuentes. La validación de bytes de estos 14 paquetes queda pendiente de autorización y descarga, no se afirma PASS.

Política de versiones 1.3.0: dos documentos nuevos con metadatos, origen y estado CI_PENDIENTE; ningún fichero existente sustituido, sin predecesor que conservar. Dictamen en sesión separada y commit final se entregan al cierre. Sin cambios de contratos, fuentes o catálogos productivos; sin incorporación de commits de otros frentes.

Próxima acción propuesta: autorizar únicamente el piloto de Melilla de 239.562 bytes y su verificación/conservación local; el resto del lote permanece sin descargar.

Preparación oficial / regeneración / 00 / territorios / workflows / publicación / push / PR / merge: **NO**.
