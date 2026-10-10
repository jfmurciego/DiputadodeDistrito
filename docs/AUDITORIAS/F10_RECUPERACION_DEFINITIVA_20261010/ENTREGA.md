# Recuperación definitiva y acción aislada F10

Versión: 1.0.0. Fecha: 2026-10-10. Nombre: Recuperación completa y caller territorial aislado.
Alcance: cinco acreditaciones territoriales 2025, Fuentes oficiales.
Estado: BLOCKED_CON_ACCION_EJECUTABLE; código candidato para revisión local.
Cambios: inventarios completos, 60 descargas oficiales, verificador y caller exclusivo a 01.
Motivo: agotar las vías accesibles y disponer una acción concreta sin promoción.
Origen: main@579ab82e84aadba778b0fe7d138ea96b66457e1e.
Predecesor: ninguno; expediente nuevo, diagnóstico y manifiesto previos intactos.

Worktree limpio creado desde main vigente en /private/tmp/ddd-f10-definitivo,
rama codex/f10-recuperacion-definitiva. El main remoto fue consultado por el
conector autenticado y git ls-remote HTTPS: ambos SHA 579ab82…; ningún avance.
El sandbox permite escribir sólo en workspace/tmp, con Git común anterior de
solo lectura. Se creó un repositorio local aislado con objetos compartidos de sólo
lectura, sin tocar referencias ni index del anterior. git fetch falló por DNS;
se recuperó el commit original firmado por API GitHub y se reprodujeron sus bytes,
verificando SHA exacto antes de escribirlo y actualizar origin/main en la copia.
Su árbol e81075a25b212f465543048f638ba7b0fe78448a estaba íntegro localmente.
No hubo restack, cherry-pick ni cambio del worktree previo en 35c0f6e….

## Recuperación agotada en las vías accesibles

Se volvió a consultar la colección completa: 183 runs manuales desde 2026-09-30,
en dos páginas. Los 171 runs de productores/coordinadores y cinco históricos
suman 176 inventarios completos, 1220 artefactos: total_count reconciliado,
IDs únicos, run coherente y todas las páginas conservadas. No quedan primeras
páginas incompletas dentro de este alcance. No es una afirmación de inexistencia
global fuera de ese intervalo/evento; los otros eventos posteriores examinados
en el expediente previo no correspondían a preparaciones reales.

Selección: cinco artefactos históricos, doce diagnósticos y 43 genéricos
(41 posteriores y dos valencianos históricos), 60 IDs / 341729809 bytes declarados.
Todos existen y ninguno está expirado. Se ejecutó download_workflow_artifact
oficial para **cada uno de los 60**: el backend devolvió 60 referencias de archivo,
con file_id conservados en descargas-conector.json. Esto no permite calcular
SHA/CRC/manifest localmente sobre los 55 adicionales: el único transporte de
esas referencias al filesystem falla por DNS. No se presentan referencias como
bytes persistidos y verificados. No se han acreditado por nombre los diagnósticos
ni los genéricos, ni se les han asignado años/territorio/identidad desconocidos.

Vías probadas y diferenciadas en acceso.json: HTTPS GitHub/API/raw (DNS),
git ls-remote (éxito), git fetch en copia aislada (DNS), CLI gh (ausente), GET
autenticado del conector (éxito), API binaria genérica del conector (endpoint no
admitido), descarga oficial (60 referencias), transporte de referencia recién
emitida (DNS oaiusercontent), nueva consulta HTTPS REST local (DNS), copias Git.
No es fallo de permisos, expiración ni ausencia: el conector autentica y descarga.
No se pidieron credenciales ni se usaron servicios externos de escritura para
transportar ZIP. Las URLs firmadas temporales no se almacenan en el expediente.

Se examinaron los 67 ZIP persistidos en el checkout: sólo coinciden con los
digests remotos los cinco originales. Se verificaron SHA exterior, bytes, CRC,
manifest, edición, run/commit y SHA interior desde esos bytes auténticos. Los
cinco originales carecen del informe congelado; sus identidades difieren de v3.
Los cinco v3 pasan validación contractual de informe, roles, inputs reales, CRS,
hashes, identidad y conservación; sus receipts siguen siendo locales derivados.
Los informes originales diagnósticos existentes están BLOCKED; generar o insertar
un informe nuevo alteraría el paquete y no acredita retroactivamente el run original.
No se regenera evidencia existente ni se emiten receipts canónicos sin procedencia.

| Territorio | Run / artefacto original auténtico | SHA paquete v3 / identidad territorial (prefijos) | Pendiente exacto y causa | Acción preparada | Estado |
|---|---|---|---|---|---|
| Andalucía | 36020646219 / 10819721995 | 3f6d3104c6f2 / a82e22d1ddf4 | Receipt completo y run propio de v3; original sin informe, adicionales sin bytes locales | Caller aislado, 01 Andalucía | BLOCKED |
| Aragón | 35728613828 / 10695433906 | 0cf09615611f / 829e61e57770 | Receipt histórico sin tres campos de compatibilidad y original sin informe; run propio de v3 no acreditado | Caller aislado, 02 Aragón | BLOCKED |
| Castilla y León | 35610439734 / 10645871597 | cab158102b50 / 9d493e4f5d91 | Los mismos tres campos y original sin informe; run propio de v3 no acreditado | Caller aislado, 07 Castilla y León | BLOCKED |
| Comunidad Valenciana | 36273981926 / 10917135113 | 60a14d4a0eb3 / 1edf14fc2d20 | Receipt completo y run propio de v3; originales/genéricos adicionales no permiten acreditar informe exacto | Caller aislado, 10 Comunidad Valenciana | BLOCKED |
| Extremadura | 35755043806 / 10710105975 | 2877aba40881 / 8d9f05adac08 | Receipt completo y run propio de v3; original sin informe | Caller aislado, 11 Extremadura | BLOCKED |

Los tres campos son compatibility_report_member, compatibility_report_sha256 y
compatibility_identity_sha256. No se rellenan con datos de otros bytes/run.
resultados.json contiene SHA completos exterior/interior/v3/informe, identidad
de compatibilidad, identidad territorial, commit y fechas; todos los valores
de paquetes/reportes se recalcularon desde bytes reales. Los digests adicionales
de artefactos-seleccionados.json son **metadata remota**, no hashes recalculados.

## Acción ejecutable pendiente de Work

Se añadió .github/workflows/f10-preparacion-territorial-aislada.yml v1.0.1.
El productor .github/workflows/preparacion-fuentes.yml permanece byte-idéntico.
El nuevo dispatch admite sólo uno de los cinco nombres completos en orden CODAUTO
y reviewed_sha. Antes de llamar, rechaza territorio desconocido/matriz, SHA vacío,
abreviado, inválido o diferente del SHA real del caller. El único job reusable
depende del éxito de esa comprobación y llama exclusivamente a 01, desde el mismo
commit del caller, con:

```yaml
data_edition: '2025'
population_year: '2025'
section_year: '2025'
reutilizar_si_ya_preparada: false
persist_state: false
source_ref: ${{ github.sha }}
recover_run_id: ''
recover_artifact_sha256: ''
```

contents:write sólo porque el reusable existente declara ese permiso y GitHub
impide elevarlo desde el caller; persist_state:false omite registrar y
generation_pending. La comprobación previa tiene contents:read, no hace checkout
ni utiliza secretos adicionales. No hay llamada a 00, 03, generación ni publicación.
No se añade autorización implícita: Work debe revisar la entrega, autorizar por
separado su disponibilidad en GitHub y después el dispatch exacto, para cada
territorio que decida ejecutar. La integración y ejecución siguen prohibidas aquí.

Una vez disponible y con SHA revisado/autorizado real, el comando por territorio es:

```sh
gh workflow run f10-preparacion-territorial-aislada.yml --ref <REF_AUTORIZADA> -f territory_id='01 Andalucía' -f reviewed_sha=<SHA_COMPLETO_AUTORIZADO>
```

Cambiar territory_id sólo por las otras cuatro opciones de la tabla. Este comando
**no se ha ejecutado**; gh tampoco está instalado en esta sesión.
No se fija un SHA futuro ni se atribuye el commit local a un run inexistente.
Si antes se recuperan los 55 ZIP locales en un entorno con acceso a las referencias,
verificar digest/tamaño/CRC e identidad exacta antes de decidir el dispatch; ni el
nombre ni el backend de descarga permiten declarar esas ejecuciones innecesarias.

## Contrato de generación e identidad

El productor vigente normaliza INE 65034 y conserva evidencias de las observaciones
vacías; omite filas sin observación, sin convertirlas en cero, y la compatibilidad
posterior bloquea si una sección objetivo queda sin población. Después genera
el informe mediante assert_materialized_territorial_gate / build_materialized_report,
lo valida y congela el bundle determinista. Las derivaciones v3 locales conservan
otras declaraciones, derivation.json y ZIP/time metadata propios: no hay un camino
del productor que garantice reproducir **esa identidad exacta**. Las adquisiciones
actuales y evidencia de normalización pueden variar los bytes, aun con datos válidos.
Por eso la acción obtiene un paquete nuevo y acredita sólo su identidad calculada,
comparándola con v3 sin suponer igualdad. Si se bloquea la gate, se conserva el
diagnóstico y no hay paquete acreditado. Cualquier receipt nuevo deberá vincular
su propio run, artefacto, commit, informe y SHA; no se registrará/promoverá aquí.

## Pruebas y conservación

43 tests PASS: siete nuevos del caller, seis F10, consumidores territorial/electoral,
entorno de validación y 16 de compatibilidad población/seccionado (CRS, duplicados,
cambios, splits/fusiones, bindings y conservación). No se ejecutan F05–F09 ni
productos históricos: se validan los 14 receipts actuales y se conservan sus
identidades y PASS previos; los cinco consumidores canónicos siguen BLOCKED.
La última corrección del caller sólo cambia nombres visibles/orden CODAUTO y
conserva predecesor workflow/test en legacy/; siete tests afectados PASS de nuevo.
Verificador adicional PASS con 176 inventarios completos y los cinco bytes originales.
El validador integrado, contratos, Plan Maestro, catálogos y fuentes no se modifican.

Reproducir desde checkout limpio del commit entregado, con runtime DDD existente:

```sh
export PATH=/usr/local/Caskroom/miniforge/base/envs/ddd/bin:$PATH
export PYTHONDONTWRITEBYTECODE=1
python -m unittest tests.test_f10_preparacion_aislada tests.test_f10_receipt_contract tests.test_prepared_source_pair_execution tests.test_geospatial_package_validation_environment tests.test_population_sectioning_compatibility
python docs/AUDITORIAS/F10_RECUPERACION_DEFINITIVA_20261010/verificar_recuperacion.py --compare docs/AUDITORIAS/F10_RECUPERACION_DEFINITIVA_20261010/resultados.json
python docs/AUDITORIAS/F10_20261010/verificar_f10.py --compare docs/AUDITORIAS/F10_20261010/resultados.json
git diff --check
```

Política de versiones: nuevo caller compatible, versión/metadatos/predecesores
conservados y cambio registrado en este expediente. Ningún funcional anterior
se sustituye. CI y run reproducible territorial no ejecutados por prohibición
expresa: la entrega local no equivale a cumplimiento de puertas productivas.
Dependencias: nuevo caller de Fuentes usa 01 existente; no cambia interfaces ni
comportamiento de los consumidores autonómicos/nacionales. Rama técnica temporal.
El repositorio aislado usa alternates de sólo lectura para los objetos históricos;
la entrega se conservará también en bundle para revisión sin depender de alternates.
Commit, árbol, checkout limpio y revisión del HEAD exacto se entregan fuera de este
documento para evitar referencias circulares. Manifiesto con hashes, sin hash de sí mismo.

Actuaciones efectivas: consultas/descargas oficiales y pruebas locales; nuevo caller
preparado. push / PR / merge / workflows / territorios / 00 / M04–M08 / publicación /
promoción / modificación de evidencias originales: NO.
