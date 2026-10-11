# Cierre ejecutivo de Fuentes Oficiales — propuesta local

Versión: 1.0.0. Fecha: 2026-10-11. Estado: BLOCKED; conservación local revisable.
Alcance: cierre de Fuentes Oficiales dentro del Plan Maestro ddd-maestro-20261008.
Origen: main@5216a1b25da7726dd73296723f22754dcf7451e1. Predecesor: ninguno.
Cambios: conciliación F04, checkpoint auténtico de cinco runs nuevos y regresión offline de 19 consumidores.
Motivo: completar las fases locales permitidas y delimitar decisiones reservadas.

## Resultado y criterio de cierre

**F04 cumple técnicamente “Matriz de 19 con gaps y pruebas”.** Se han comprobado los 242 archivos exactos del manifiesto v3 aceptado, los 16 del overlay de referencias ya integrado, los cinco paquetes locales y sus informes/bindings, y la matriz final de 19. La aceptación histórica GO_ACOTADO está en continuacion/REVISION_F04_ACEPTADA.md. Se propone PENDING → PASS; no se registra aceptación de Work ni transición.

**F10 continúa PENDING formal y BLOCKED técnicamente.** F09 ya está PASS formal. Los cinco runs nuevos y su preparación SUCCESS son auténticos; sus jobs de registro y evaluación de generación quedaron skipped. Por tanto no existe una promoción automática que conciliar. Cero de cinco ZIP nuevos quedaron materializados/verificados localmente; cero receipts nuevos emitidos; cero paquetes nuevos conservados duraderamente. Cinco expedientes de acreditación pendientes no son receipts #179.

Los catorce consumidores históricos sí se volvieron a ejecutar realmente sobre bytes del almacén fuera del repositorio, con el código actual y red prohibida: 14 PASS. Los otros cinco consumidores canónicos fallan cerrados con las causas anteriores, sin trasladarles los runs nuevos.

## Cinco paquetes nuevos: identidad y material pendiente

Los SHA siguientes son digests remotos autenticados, no SHA recalculados desde bytes locales. Los SHA interiores en productor-extractos.json proceden de logs auténticos y también se etiquetan como declarados. Nunca se utilizan para emitir acreditación.

| Territorio | Run / artefacto exacto | SHA exterior remoto | Paquete / conservación / receipt |
|---|---|---|---|
| Andalucía | 38082966768 / 11682006744 | cc70f801d5a26a522458da05a5fde15e1876071cf1738d07c90429ca2057a056 | BLOCKED / BLOCKED / BLOCKED |
| Aragón | 38093067883 / 11685591675 | 35adcbfcf41619c3e54219714aefac5b4885fae0ccd08ae5fcf9930e0528db51 | BLOCKED / BLOCKED / BLOCKED |
| Castilla y León | 38091055890 / 11684448799 | 1f9d6a7c0362b157d2bb300a4c1eca037eb7a07fa52fec53ad550d46752351bd | BLOCKED / BLOCKED / BLOCKED |
| Comunidad Valenciana | 38091132175 / 11684204844 | 528d2bfb2a7096120528fe5407473d13138551380278cfaa2a2928e521f57c5d | BLOCKED / BLOCKED / BLOCKED |
| Extremadura | 38091144559 / 11684599346 | b4241708cbc7eb1fcf3dd7b6298152392731975106bbddaf6d8ae03bc3fcd8dc | BLOCKED / BLOCKED / BLOCKED |

Faltan para cada run: ZIP original persistido, tamaño/SHA exterior/CRC, manifest y SHA interior calculados, identidad territorial, informe congelado propio y compatibility_report_member/compatibility_report_sha256/compatibility_identity_sha256 calculados sobre sus bytes. Todos los artefactos existen y no han expirado. actions.json conserva fechas, expiración, commit, jobs e inventarios completos; acreditaciones-pendientes/ contiene cinco checkpoints explícitamente no canónicos.

Vías efectivamente usadas: API GitHub autenticada, inventario completo de los cinco runs/jobs, descarga oficial de los cinco IDs, extractos acotados de los cinco jobs productores, CLI gh local, HTTPS local, transporte de referencia recién emitida y búsqueda de copias por los cinco tamaños exactos en 1.436 ZIP locales. No se encontraron copias del ZIP exterior; esto no acredita inexistencia global.

Conservación durable: se descubrió el respaldo privado DDD-respaldo/fuentes-oficiales en Drive. La creación de su subcarpeta F10 fue rechazada por la aprobación automática: “MCP tool call requires approval, but approval policy is never”. No se creó carpeta ni se subieron archivos. No se tratan las referencias temporales ni /private/tmp como respaldo durable. El almacén ~/Desarrollo/DDD-almacen está fuera de las raíces escribibles de esta sesión; se utilizó solo en lectura.

## Compatibilidad temporal: divergencia que impide atribuir readiness a la legislatura

La edición operativa 2025 es distinta de los años de población/seccionado. El caller nuevo fijó 2025/2025. La matriz vigente, leída con resolver_preparacion_legislatura.resolve sin adquirir nada, exige lo siguiente:

| Territorio | Años declarados por el nuevo productor | Años seleccionados por el contrato vigente | Resultado temporal |
|---|---|---|---|
| Andalucía | 2025/2025 | 2025/2026 | BLOCKED_YEAR_MISMATCH |
| Aragón | 2025/2025 | 2025/2026 | BLOCKED_YEAR_MISMATCH |
| Castilla y León | 2025/2025 | 2025/2026 | BLOCKED_YEAR_MISMATCH |
| Comunidad Valenciana | 2025/2025 | 2023/2023 | BLOCKED_YEAR_MISMATCH |
| Extremadura | 2025/2025 | 2025/2025 | MATCH_REPORTED_NOT_BYTE_VERIFIED |

Extremadura coincide temporalmente solo a nivel declarado; su manifiesto sigue pendiente. Andalucía, Aragón y Castilla y León requieren seccionado 2026; Comunidad Valenciana requiere población y seccionado 2023. No se altera la política temporal ni el contrato para admitir 2025/2025 como sustitución. La acreditación de una fuente territorial válida para 2025 y su idoneidad para la legislatura vigente son criterios separados.

## Resultado de los 19 consumidores

Territorial: prueba real validate_territorial_receipt + consume del almacén explícito + validate_effective_territorial_package. Temporal: confrontación contra la política existente. Electoral: admisibilidad del receipt, identidad y procedencia según el resolver vigente; no se descargan ni revalidan bytes electorales. Elegibilidad: evaluación offline de la puerta existente de fuente/generación, sin habilitación ni ejecución productiva.

| CODAUTO / Territorio | Consumo territorial | Temporal | Electoral: metadatos | Puerta de generación de fuente |
|---|---|---|---|---|
| 01 Andalucía | BLOCKED | BLOCKED | ADMISSIBLE | BLOCKED |
| 02 Aragón | BLOCKED | BLOCKED | ADMISSIBLE | BLOCKED |
| 03 Principado de Asturias | PASS | PASS | ADMISSIBLE | BLOCKED |
| 04 Islas Baleares | PASS | PASS | ADMISSIBLE | READY de fuente; sin autorización |
| 05 Canarias | PASS | PASS | ADMISSIBLE | READY de fuente; sin autorización |
| 06 Cantabria | PASS | PASS | ADMISSIBLE | READY de fuente; sin autorización |
| 07 Castilla y León | BLOCKED | BLOCKED | ADMISSIBLE | BLOCKED |
| 08 Castilla-La Mancha | PASS | PASS | ADMISSIBLE | READY de fuente; sin autorización |
| 09 Cataluña | PASS | PASS | ADMISSIBLE | BLOCKED |
| 10 Comunidad Valenciana | BLOCKED | BLOCKED | ADMISSIBLE | BLOCKED |
| 11 Extremadura | BLOCKED | BLOCKED | BLOCKED provisional | BLOCKED |
| 12 Galicia | PASS | PASS | ADMISSIBLE | BLOCKED |
| 13 Comunidad de Madrid | PASS | PASS | ADMISSIBLE | READY de fuente; sin autorización |
| 14 Región de Murcia | PASS | PASS | ADMISSIBLE | BLOCKED |
| 15 Comunidad Foral de Navarra | PASS | PASS | ADMISSIBLE | READY de fuente; sin autorización |
| 16 País Vasco | PASS | PASS | ADMISSIBLE | READY de fuente; sin autorización |
| 17 La Rioja | PASS | PASS | ADMISSIBLE | READY de fuente; sin autorización |
| 18 Ceuta | PASS | PASS | ADMISSIBLE | READY de fuente; sin autorización |
| 19 Melilla | PASS | PASS | ADMISSIBLE | READY de fuente; sin autorización |

Cuatro bloqueos de generación existentes se conservan: Principado de Asturias, CAP_ADMIN_POLICY; Cataluña y Región de Murcia, evidencia pre-M04 no habilitante; Galicia, implementación pre-M04 cambiada respecto a la evidencia. Los cinco sin receipt territorial permanecen bloqueados antes de esa puerta. Diez puertas de fuente satisfacen la evaluación local; ninguna constituye autorización de producción. Extremadura conserva PROVISIONAL_NOT_PRODUCTION_ELIGIBLE electoral. No se cambia la fuente territorial por ninguna causa electoral.

## Pruebas, gobierno y revisión

79 pruebas distintas ejecutadas satisfactoriamente: 69 del bloque contractual/consumidores/compatibilidad/almacén/legislatura y diez casos de almacén persistido activados explícitamente con DDD_LOCAL_STORE. La primera ejecución detectó un fallo ambiental de PATH (un subproceso escogió Python 2 del sistema); una corrección ambiental usando el entorno existente resolvió el caso. Se conservan ambos logs; no hubo corrección de código productivo.

Verificación de cierre: F04 criterio SATISFIED, 14 consumidores PASS y cinco BLOCKED. Los casos negativos prueban digests, identidad, CRC/rutas ZIP, reportes, inputs, roles, CRS y conservation. No se ejecutó CI remota ni un producto territorial. La prueba unitaria de orquestación usa dependencias simuladas en copia temporal; no se lanzó 00 ni generación real.

Base: 5216a1b25da7726dd73296723f22754dcf7451e1, main remoto confirmado. Incremento aislado en /private/tmp/ddd-cierre-fuentes-20261011, rama codex/cierre-fuentes-20261011, mismo frente. Se protege el worktree de referencia en 35c0f6ee… y el incremento independiente codex/f10-lanzador-controlado en a287584e9081d70e179dd4fd3f7c30cbbe2d6e29. No se mueve ni altera ninguna rama anterior. El clon comparte objetos históricos de solo lectura; se entrega bundle completo para independencia de alternates.

Desde la base F10 anterior, main integró #233 (productor aislado), #234 (gestor nacional), #236 (precisión Aragón) y #235 (precisión M06). No se restackea ni se incorpora el incremento no integrado del lanzador. Los validadores y contratos canónicos actuales se utilizan tal como están.

Se entrega la revisión separada del SHA final fuera del commit para evitar referencias circulares; ninguna autoevaluación se presenta como aprobación externa. Política de versiones 1.3.0: solo altas nuevas con metadatos; no sustituciones ni predecesores funcionales que archivar. Conservación local autorizada; integración/CI quedan fuera de esta orden.

Reproducción offline desde checkout limpio, con el entorno DDD existente:

```sh
export PATH=/usr/local/Caskroom/miniforge/base/envs/ddd/bin:$PATH
export PYTHONDONTWRITEBYTECODE=1
export DDD_LOCAL_STORE=/Users/macbookpro/Desarrollo/DDD-almacen/fuentes-preparadas
python -m unittest tests.test_f10_receipt_contract tests.test_prepared_source_pair_execution tests.test_geospatial_package_validation_environment tests.test_population_sectioning_compatibility tests.test_almacen_fuentes_local tests.test_preparacion_legislatura_vigente
python docs/AUDITORIAS/CIERRE_FUENTES_20261011/verificar_cierre.py --store "$DDD_LOCAL_STORE" --compare docs/AUDITORIAS/CIERRE_FUENTES_20261011/resultados.json
git diff --check
```

## Checkpoint y decisiones reservadas a Work

1. Aprobar, si acepta el criterio y la revisión, el registro formal F04 PENDING → PASS. La propuesta está completa; no se registra aquí.
2. Facilitar un entorno con transporte autenticado de los ZIP existentes y conservación durable habilitada. El permiso de recuperar artefactos ya está concedido; no se solicitan credenciales ni nuevas adquisiciones del INE. Desde ese entorno, recuperar por los cinco IDs de la tabla, preservar los ZIP originales y ejecutar los validadores #179 antes de crear receipts. La conservación vía Drive requiere resolver el rechazo automático; el almacén local externo requiere una raíz de escritura habilitada.
3. Resolver el alcance del cierre F10 respecto a los cuatro desajustes temporales: aceptar únicamente la acreditación territorial 2025 no acredita la legislatura vigente. Cualquier paquete que deba cumplir los años seleccionados exige un encargo separado de Work; no se propone relajar ni cambiar esos años.
4. Después de disponer de bytes, receipts y revisión: autorizar separadamente integración/registro canónico y el cierre formal F10. No hay incremento de catálogo listo para activar ni propuesta PASS mientras falten criterios.

Checkpoint de continuidad: artifacts y commits auténticos en actions.json; hashes interiores declarados en productor-extractos.json; cinco expedientes pendientes; resultados actuales reproducibles; reconciliacion.json conserva hashes/estados del Plan Maestro y worktrees protegidos. No es un plan nuevo ni reabre F01–F03/F05–F09.

Acciones realizadas: lecturas/descargas de evidencia Actions y validaciones locales. Plan Maestro y estados formales sin cambios. Datos INE nuevos / workflows / 00 real / generación de distritos / promoción canónica / push / PR / merge / publicación: NO.
