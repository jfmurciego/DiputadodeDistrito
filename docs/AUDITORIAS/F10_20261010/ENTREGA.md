# F10 — acreditación territorial bajo #179

Versión: 1.0.0. Fecha: 2026-10-10. Nombre: Receipts con ejecución de origen.
Estado: candidato local; dictamen F10 **BLOCKED**; preparado para revisión del diff.
Alcance: cinco fuentes territoriales 2025 y defecto demostrado del consumidor.
Cambios: expediente reproducible y cierre de una aceptación indebida de receipts locales.
Motivo: exigir acreditación durable antes de declarar READY al paquete efectivo.
Origen: `c83f6e3f5b9d25ec12c0124e42b372e7d838031e`; predecesor: ninguno.

HEAD de entrada confirmado y worktree limpio, rama `codex/f10-receipts`, en
`/Users/macbookpro/Desarrollo/DDD-f10-receipts`. Work dirige. F05–F09 no repetidos.

El [contrato #179](https://github.com/jfmurciego/DiputadodeDistrito/pull/179)
exige informe de compatibilidad congelado dentro del paquete, hashes e identidad
ligados a sus inputs reales; excluye la reutilización automática de paquetes históricos
sin informe. Snapshot literal consultado: [contrato-179.json](contrato-179.json).
No se cambia el contrato, ningún dato oficial ni ninguna evidencia canónica.

| Territorio | Run territorial registrado | Artefacto exacto | Receipt actual | Resultado |
|---|---:|---:|---|---|
| Andalucía | 36020646219 | 10819721995 | Ausente | BLOCKED |
| Comunidad Valenciana | 36273981926 | 10917135113 | Ausente | BLOCKED |
| Extremadura | 35755043806 | 10710105975 | Ausente | BLOCKED |
| Aragón | 35728613828 | 10695433906 | Histórico sin campos de compatibilidad | BLOCKED |
| Castilla y León | 35610439734 | 10645871597 | Histórico sin campos de compatibilidad | BLOCKED |

Los cinco runs y artefactos **existen y son identificables**. Sus ZIP conservados
reconcilian tamaño, SHA exterior, SHA interior, CRC y metadata remota (incluido commit
de origen). Los cinco paquetes carecen de `compatibilidad_poblacion_seccionado.json`;
el validador común los rechaza por paquete histórico no reutilizable. Completar campos
de sus receipts no puede suplir bytes ausentes. Los candidatos v3 tienen SHA e identidad
diferentes y ningún run productor acreditado para esos bytes. No se emite receipt canónico.

[resultados.json](resultados.json) contiene por territorio todos los hashes recalculados,
commit/run/URL, miembros originales, ruta de artefacto conservado, rechazo efectivo del
receipt actual y actuación pendiente del productor. [remote-artifacts.json](remote-artifacts.json)
conserva respuestas GET completas de los cinco runs, con `total_count == artifacts.length`.

Límite de la comprobación: no se afirma inexistencia global de otros runs. En el run
valenciano hay además dos ZIP de nombre genérico idéntico, IDs `10917250160` y `10917245848`,
con distintos hashes exteriores. Se obtuvieron referencias de descarga mediante el conector,
pero curl falló con exit 6 por DNS; sus bytes no pudieron comprobarse. Metadata y nombre
no acreditan un receipt. [descarga-adicional.log](descarga-adicional.log) conserva el fallo
sin URLs temporales firmadas. Para aprovecharlos haría falta recuperar por ID exacto,
reconciliar digest y contenido y demostrar informe #179 READY e identidad correspondiente.

La actuación necesaria en **cada uno de los cinco territorios** es una ejecución real,
autorizada y limitada al productor `01 · Preparación de Datos Territoriales`, con
`territory_id` de la tabla, `data_edition=2025`, `population_year=2025`, `section_year=2025`
y `reutilizar_si_ya_preparada=false`. El commit productor debe estar revisado e identificado;
no se preasigna un SHA futuro, un run, un nombre de artefacto futuro ni un digest.

El productor deberá reproducir dentro de esa ejecución la materialización/derivación que
origina los bytes candidatos, conservar inputs y trazabilidad al origen, congelar un informe
READY y validar roles exactos, tamaños, SHA, CRS, correspondencias y conservación. Los
receipts locales actuales sólo documentan operaciones locales: cambiarles schema o añadir
run histórico no sustituye esa actuación. Lanzar 01 sin materializar correctamente esas
operaciones tampoco garantiza obtener un paquete compatible. Esta entrega no implementa
una nueva derivación ni vuelve a resolver F05–F09.

Después se verifica el artefacto del **nuevo** run: ID/nombre único, commit, tamaño, SHA
exterior, SHA interior, SHA del informe e identidad canónica del informe; se calcula la
identidad territorial con la función vigente y se emite el receipt ligado a esa ejecución
y declaración versionada. El registro durable debe reconciliar exactamente esos valores.
Una adquisición futura con fuentes diferentes acredita sus propios bytes, nunca retroactivamente
los candidatos locales v3. Registro/promoción posterior requiere una decisión de Work.
En 01, `persist_state=false` evita el job de registro del catálogo: permite obtener evidencia
sin promoción, pero por sí solo no deja un receipt durable consumible. No se lanza nada aquí.

Defecto demostrado y corregido: `validate_effective_territorial_package` aceptaba directamente
el receipt local v3 de Aragón y devolvía READY. La regresión conserva la demostración para
los cinco territorios y para cinco intentos de retagging con run histórico prestado.
Ahora el consumidor valida schema, consulta la acreditación durable del catálogo, valida kind
y miembro contractual del informe y exige coincidencia completa del receipt antes de leer
los bytes efectivos. La validación vigente de inputs/compatibilidad permanece activa.
Dependencia declarada: consumidor común de Fuentes, utilizado por ejecución autonómica
territorial y por pares con fuente electoral. No se cambia el mecanismo productor, porque
no se demuestra un defecto adicional del productor dentro de F10.

Política de versiones: corrección compatible PATCH 1.0.1; metadatos y registro del cambio
en este expediente; predecesor exacto en
`legacy/herramientas/consumir_par_fuentes_legislatura_pre_F10.py`.
CI y run territorial exigidos para validación productiva **no ejecutados**, por prohibición
expresa del encargo. El commit solicitado conserva un candidato local para revisión;
no equivale a integración, promoción ni cumplimiento de esas puertas productivas.

Pruebas locales: 20 PASS en [pruebas-consumidores.log](pruebas-consumidores.log), incluidos
seis tests nuevos de contrato, consumidores territorial/electoral y entorno de orquestación.
[regresion-base.log](regresion-base.log): dos tests, diez fallos esperados al usar el código
exacto de la base preservada; no se presenta ese resultado como PASS.
El primer intento de las pruebas existentes tomó Python 2.7 en un subproceso, falló y se
conserva en [pruebas-entorno-inicial.log](pruebas-entorno-inicial.log); se corrigió el entorno,
sin cambiar el test. Python principal del sistema tampoco tenía PyYAML.

Reproducción desde checkout limpio con el runtime de `requirements.lock` disponible:

```sh
export PATH=/usr/local/Caskroom/miniforge/base/envs/ddd/bin:$PATH
python -m unittest tests.test_f10_receipt_contract tests.test_prepared_source_pair_execution tests.test_geospatial_package_validation_environment
python docs/AUDITORIAS/F10_20261010/verificar_f10.py --compare docs/AUDITORIAS/F10_20261010/resultados.json
DDD_F10_BASELINE=1 python -m unittest tests.test_f10_receipt_contract.F10ReceiptContractTests.test_local_derived_receipts_never_accredit_effective_bytes tests.test_f10_receipt_contract.F10ReceiptContractTests.test_retagging_and_borrowing_historical_run_cannot_accredit_candidate
```

Los dos primeros comandos deben terminar con exit 0; el tercero con exit 1 y diez fallos.
Runtime utilizado: Python 3.10.19, PyYAML 6.0.3, GeoPandas 1.1.2, Shapely 2.1.2;
sin instalar dependencias. El verificador no usa red, no recompone datos ni ejecuta GIS intensivo.
Hashes del expediente en [MANIFEST.json](MANIFEST.json); no contiene hash de sí mismo.
El sandbox rechazó `git add` al crear `index.lock` en el directorio Git común,
fuera de las rutas de escritura permitidas. No se pidió elevación ni se modificó ese
directorio. El commit y árbol se conservan en un repositorio temporal permitido y se
exportan como bundle; HEAD del worktree solicitado permanece en la base con el diff
preservado. Esa copia sirve exclusivamente para conservación, checkout limpio y revisión
separada; no integra cambios en otra rama o frente. SHA/árbol/bundle y resultado de revisión
se entregan aparte, evitando referencias circulares dentro del propio commit.

push / PR / merge / workflows / ejecución territorial / promoción / publicación: **NO**.
La recuperación adicional intentada fue de artefactos ya existentes, nunca de fuentes oficiales.
