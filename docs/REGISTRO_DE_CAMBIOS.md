<!--
Nombre: Registro de cambios DDD
Versión: 1.0.64
Fecha: 2026-11-01
Alcance: T-10 — corrección de la credencial de registro
Estado: candidato
Cambios/motivo: con los secretos creados, git enviaba dos Authorization (HTTP 400, run 41324108794)
Anterior: legacy/docs/REGISTRO_DE_CAMBIOS_v1.0.63_20261101b.md
-->

## 2026-11-01 — T-10 — credencial de registro sin cabecera duplicada

- `actions/checkout` v6 guarda su token en un fichero aparte enlazado con `includeIf.gitdir:…`; el paso solo borraba `http.extraheader` local y git enviaba las dos cabeceras («Duplicate header: Authorization», HTTP 400).
- El paso «Credencial de registro» borra también esas entradas `includeIf` antes de poner el token de la app (14 jobs, 10 workflows). Reproducido y comprobado en local con la configuración de checkout v6.
- Test: `test_credencial_registro` exige el borrado de `includeIf` antes de la nueva cabecera.

## 2026-11-01 — T-10 — robots de registro con app propia

- Los 14 jobs que registran en `main` (10 workflows) llevan el paso «Credencial de registro» justo después del checkout. Con los secretos `DDD_REGISTRO_APP_ID` y `DDD_REGISTRO_APP_KEY` firma un JWT con openssl, pide un token de instalación y sustituye la credencial del checkout; los `git push` y las herramientas de registro empujan como la app, que puede quedar exenta en el ruleset.
- Sin secretos el paso no hace nada y todo sigue con `github.token`, como hasta ahora.
- Sin acciones externas: el paso es bash en línea, así que funciona aunque el checkout sea de un commit anterior.
- Test: `tests/test_credencial_registro.py` exige el paso en todo job que registra.

## 2026-11-01 — D-2 confirmada — matrículas en español

- Clave de elección: número INE canónico; matrícula como alias, solo en español: Baleares PM, Gerona GE, Orense OR y Huesca HU. IB, GI y OU se rechazan.
- Catálogo maestro 1.7.3, `generar_provincias_congreso.py` 1.2.1 y `clave_eleccion.py` 1.0.1 con esas matrículas.
- `docs/PLAN.md` 1.0.3: D-2 confirmada y resultado de T-01 (52 provincias clasificadas, 12 PARADA con causa).

## 2026-11-01 — T-03 — Activación por elección

- `herramientas/clave_eleccion.py` 1.0.0: clave `ES-<NAC|AUT>-[unidad-]AAAAMMDD`. Nacional: número INE canónico y matrícula como alias (`ES-NAC-HU-20230723` → `ES-NAC-22-20230723`); `ES-NAC-20230723` expande a las 52 provincias. Autonómicas: `ES-AUT-02-20260208` (Aragón), `ES-AUT-20230528` (todas las de esa fecha). D-2 aplicada según la recomendación, pendiente de confirmar.
- La fecha forma parte de la clave: una fecha no registrada no resuelve a la elección vigente. `validar` rechaza claves o `territory_id` repetidos; cada elección histórica lleva su propio `territory_id`.
- Workflow «Activación por Elección» 1.0.0: fases `plan` (simulación en seco), `activar` (prepare_one), `electoral` (03) y `completa` (00) para todos los territorios; filtro `solo`.
- 00 1.4.6: entrada `lanzado_por_eleccion`; el encadenado par→04 se mantiene cuando lo lanza el bot, una sola vez.
- Tests: `tests/test_clave_eleccion.py` y listas de workflows visibles.

## 2026-10-31 — Congreso — puentes heredados de los contratos autonómicos

- El pre-M04 exige un grafo provincial conexo. Sin los puentes gobernados de los contratos autonómicos, las provincias con enclaves fallan, como Palencia (run 41235453115).
- `generar_provincias_congreso.py` 1.2.0: `inherit_bridges` copia a cada contrato provincial los puentes autonómicos cuyo ámbito cae en esa provincia. La componente administrativa de Tremp pasa a puente municipal. Un puente sólo se copia si sus secciones existen en 2023.
- 17 provincias reciben puentes: Alicante, Badajoz, Burgos, Ciudad Real, Gerona, Guipúzcoa, Huelva, Lérida, Málaga, Murcia, Navarra, Palencia, Pontevedra, Cantabria, Valencia, Valladolid y Vizcaya.
- Se omite el puente municipal 47175 de Valladolid (secciones de 2025 que no existen en 2023).
- Test: Palencia, Burgos, Valencia, Gerona y Navarra llevan sus puentes provinciales.

## 2026-10-31 — Congreso — Baleares y Las Palmas

- Baleares (K=10): Mallorca 7 (1,11 de la media), Menorca 1 (0,82) e Ibiza + Formentera 2 (0,70). Menorca y el grupo de Ibiza y Formentera quedan como exenciones estructurales de suelo. Un puente une Formentera e Ibiza.
- Las Palmas (K=10): Gran Canaria 8 (0,94), Fuerteventura 1 (1,08) y Lanzarote con La Graciosa 1 (1,38). El techo provincial sube a 1,40 y la tolerancia a 0,40. Un puente une La Graciosa con Teguise, su municipio.
- `particiones_insulares_2025.json` (esquema 1.4): congreso_baleares y congreso_las_palmas. Sus inventarios 2023 salen del ZIP de Interior; cada isla coincide en hash CUSEC con los inventarios INE 2023 acreditados.
- `materializar_contrato_generacion.py`: `component_districts` en la política fija el reparto por componentes (si no hay, Hamilton). Una componente de un distrito bajo el suelo queda declarada como excepción, igual que con Hamilton.
- Tests: reparto fijado, puentes y techo de Las Palmas.

## 2026-10-31 — Congreso — Santa Cruz de Tenerife: islas agrupadas

- Decisión del propietario (opción B): la provincia 38 (K=9) se reparte entre Tenerife (8 distritos, 1,00 de la media) y La Gomera + La Palma + El Hierro (1 distrito, 1,00).
- `particiones_insulares_2025.json` (esquema 1.3): territorio `congreso_santa_cruz_de_tenerife`, con componentes 38-C01 y 38-G01. Su inventario 2023 sale de las secciones del ZIP oficial de Interior. Cada isla coincide en conjunto CUSEC (hash) con el inventario INE 2023 ya acreditado de Canarias.
- Puentes declarados (La Gomera–La Palma y La Gomera–El Hierro) como aristas `maritime_group` de M02.
- `materializar_contrato_generacion.py` copia en M02 los puentes del lookup.
- `_resolver_ejecucion_completa_core.py` 1.0.3 admite sólo esos puentes y sólo dentro de una misma componente. Las autonómicas siguen sin aristas marinas.
- `generar_provincias_congreso.py` 1.1.0: una provincia insular entra cuando su partición está declarada (Hamilton por componentes).
- Tests: grupo de Tenerife, puentes no declarados o entre componentes rechazados, registro de archipiélagos.

## 2026-10-31 — Congreso — 48 provincias nuevas

- `herramientas/generar_provincias_congreso.py` 1.0.0 (nuevo, idempotente): con Huesca como plantilla, da de alta cada provincia del reparto N06 (52 provincias, 407 escaños). Escribe en catálogo maestro, política, matriz, registro, fuentes, catálogo de preparación, contrato Infoelectoral y contrato bootstrap M01–M06.
- Identidad: `pilot_code` C+número INE; `plate_code` con las letras de matrícula (HU, M, B, CE, ML…). Topónimos en español (Gerona, Lérida, Orense, Guipúzcoa, Vizcaya, Álava, La Coruña).
- Quedan fuera las provincias insulares (Baleares, Las Palmas y Santa Cruz de Tenerife), que necesitan la partición por islas.
- `contratos_infoelectoral.yaml` 1.2.0: 48 contratos más; sus totales se calculan del ZIP oficial nacional y cada uno cuadra mesa a mesa con el conversor.
- Versiones: catálogo maestro 1.7.0, política 1.7.0, matriz 1.1.0, fuentes 1.2.0 y los 6 workflows con selector (patch).
- `tests/test_generar_provincias_congreso.py` (nuevo): K igual a N06 en todas las declaraciones, número y matrícula únicos, topónimos en español.

## 2026-10-31 — 05 — visor con provincias del Congreso

- `preparar_visor_ejecucion.py` 1.5.1: una provincia sin CODAUTO usa su `pilot_code` (C22) para ordenar y queda detrás de las 19 autonómicas.
- `test_etiquetas_territoriales_humanas.py`: regresión con Huesca.

## 2026-10-31 — plataforma — workflows no productivos a legacy

- 16 workflows pasan a `legacy/workflows/retirados_20261031/` con `git mv`:
  - `congreso-piloto-leon`;
  - `diagnostico-eleccionesdb-grupo-a`;
  - `diagnostico-fuentes-electorales-pendientes`;
  - `f10-electoral-receipts-asturias-galicia`;
  - `f10-electoral-source-validation`;
  - `f10-preparacion-territorial-aislada`;
  - `prueba-fuentes-oficiales`;
  - `prueba-openai`;
  - `smoke-gerrychain-galicia`;
  - `validar-poblacion-ine-2026-aragon`;
  - `verificar-andalucia-2026-provisional`;
  - `verificar-cataluna-2024`;
  - `verificar_ign_temporal_2025`;
  - `p0-verificacion-remota`;
  - `publicar-checkpoint-cyl-m06` (sin llamador);
  - `adquirir-siel-andalucia-2026` (sin llamador).
- Quedan activos:
  - 0, 00–05, la activación de legislatura y la recuperación del M08;
  - los reutilizables y su orquestación;
  - `publicar-version-mapa` (publicación con DOI);
  - las comprobaciones de CI: pruebas, contratos y productos públicos.
- Los tests de los workflows retirados validan la copia retirada; los inventarios de workflows visibles se reducen a los de producción.

## 2026-10-31 — 0 — Gestor de Campañas operativo

- `gestor-campanas.yml` 1.1.0: `actions: write` en el llamador. El 00 llamado tiene un job con `actions: write` y, con `read`, GitHub rechazaba arrancar el workflow (`startup_failure` en cada PR y en cada lanzamiento). El campo de territorios acepta `todos`, números (`3,6,11`) o nombres (`Cantabria, Extremadura`), sin valor por defecto.
- `gestor_campana_nacional.py` 0.1.0: `parse_selection`, que no distingue tildes ni mayúsculas y rechaza nombres desconocidos.
- `test_gestor_campana_nacional.py`: selección y permisos del llamador frente al 00.

## 2026-10-31 — 04 — recuperación M08 con receipt declarado

- `recuperar-producto-electoral-durable.yml` 1.0.2: la verificación de identidad lee la fuente electoral con el mismo criterio que el detector (#360), el receipt declarado en el catálogo. El legacy `evidencia/catalogo/electoral_source_2025.json` estaba obsoleto en Cantabria (run 36629227614 frente a 40689735716) y no existía en Extremadura.
- `test_recuperacion_producto_electoral.py`: regresión del contrato del workflow.

## 2026-10-31 — 03 — espejo del ZIP Infoelectoral

- Run 41192319910: Interior devuelve error HTTP a los runners de GitHub (curl 22).
- `contratos_infoelectoral.yaml` 1.1.0: `mirror` con el release `fuente-infoelectoral-02202307` y el asset `02202307_MESA.zip`.
- `preparacion-resultados-electorales.yml` 1.0.5: si la URL oficial falla, descarga el espejo; la huella SHA-256 del contrato se exige igual.
- `test_fuente_infoelectoral_mesas.py` 1.0.1: contrato con espejo y orden descarga→huella en el workflow.

## 2026-10-31 — 03 — fuente oficial Infoelectoral por mesa

- `herramientas/fuente_infoelectoral_mesas.py` 1.0.0 (nuevo): resuelve el contrato y convierte el ZIP oficial por mesa (ficheros 09, 10 y 03) en el CSV largo del adaptador común; excluye el CERA y exige cuadre por mesa y totales.
- `configuracion/contratos_infoelectoral.yaml` 1.0.0 (nuevo): contrato `congreso_huesca_2023-07-23` con URL, SHA-256 y totales verificados sobre el ZIP real; cuadran con la JEC menos el CERA.
- `adaptador_minsait_csv.py`: parámetros `--source-class` y `--adapter-label` (por defecto, comportamiento anterior).
- `preparacion-resultados-electorales.yml` 1.0.4: ruta `infoelectoral_mesas` con descarga, huella y conversión antes de Minsait.
- Tests: `test_fuente_infoelectoral_mesas.py` (nuevo); `test_registro_electoral_comun.py` cuenta los contratos Infoelectoral como ruta y retira la exención del piloto.


## 2026-10-30 — Congreso — piloto Huesca (territorio nuevo)

Decisión N09-OWNER-20261030-PILOTO-HUESCA (`docs/ESTUDIOS/N09_PILOTO_CONGRESO_HUESCA_20261030/DECISION.md`).

- `catalogo_territorios_espana_2025.yaml` 1.6.0: lista `pilot_territories` con `congreso_huesca`
  (pilot_code C22, provincia 22, K=2); `territories` sigue con exactamente las 19 autonómicas.
- `catalogo_territorios.py`: `load_pilot_territories` y `load_all_territories`; `load_master` intacto.
- Lectores del flujo 00 que buscan por `territory_id` incluyen los pilotos: materializador de contratos,
  `territory_contract.py` 1.3.0 y validación de `catalogo_preparacion.py`.
- `resolver_preparacion_legislatura.py`: la invariante de 19 cuenta las autonómicas; los pilotos llevan
  `pilot_code` en la matriz de legislatura (1.0.5) y en `registro_electoral.yaml`.
- `politica_generacion_territorial_2025.yaml` 1.6.0: K=2 (`formula`), suelo 0,85, techo 1,15, tolerancia
  0,15 y atomicidad municipal 1,15.
- Territorio `territorios/congreso_huesca/config/`: fuentes INE 2023 (provincia 22) y contrato bootstrap
  materializado con paquete sintético (la 01 lo rematerializa con el paquete real).
- `fuentes/territorios_espana.yaml` 1.1.0 y opción «Congreso Huesca» en los 7 workflows con lista territorial.

## 2026-10-30 — M05 GerryChain — cuatro familias de fallo del lote nocturno

Lote de 18 runs GerryChain 50 (00:24–00:26 UTC): 6 PASS (Aragón, Asturias, Castilla y León, Castilla-La
Mancha, País Vasco, La Rioja) y 12 FAIL en M05.

- `ddd_core/m05_gerrychain_strategy.py` 2.2.0:
  - la partición dura sale del `province_field` de M05/M04 (`DDD_PARTITION` en archipiélagos), no de
    `CPRO`: Baleares y Canarias fallaban en `province_count` y no aplicaban sus exenciones insulares;
  - `population_floor_exempt_municipalities` (#343) exime del suelo al distrito que contiene el municipio
    (Murcia, distrito 38 con Beniel);
  - un grupo atómico administrativo `{p}:{a|b}:M` se admite si sus municipios son exactamente los
    declarados (Cataluña `25:25215|25234:M`); una unidad intermunicipal no declarada sigue rechazada;
  - `--initial` sustituye la semilla también con `--params`;
  - preflight de cardinalidad: con tantas unidades como distritos y más de una semilla, falla con
    `GERRYCHAIN50_ENSEMBLE_INFEASIBLE_AT_DECLARED_GRANULARITY` (Ceuta y Melilla: 25 unidades, 25 distritos);
    no se certifican 50 alternativas falsas.
- `procedimiento.sh` 2.9.3: si la Formación inicial M04 no es admisible (distritos bajo suelo que la ruta
  canónica repara: Cantabria, Galicia, Madrid, Valencia, Navarra; `ddd_unit_id` no legible: Extremadura),
  se ejecuta el M05 canónico, su salida se copia como `*_semilla_canonica.geojson.zip`, se revalida con
  el mismo contrato y GerryChain arranca de ella. Sin semilla admisible, falla cerrado.
- `tests/test_gerrychain50_cuatro_familias.py` (nuevo).
- Ninguno de estos ficheros forma parte de la huella M05 (`huella_checkpoint_m05.ENGINE_FILES`).
- `test_preparacion_legislatura_vigente`: el M06 de Aragón puede salir de un run posterior que reutiliza la
  fuente (GerryChain 40979465420); se compara la preparación con el paquete fuente de su manifiesto productor.

## 2026-10-29 — M05 — disciplina municipal en la reparación privada

Andalucía (40969274807): M05 base deja hard=1; `private_annealing` llega a hard=0, pero la puerta
oficial rechaza el candidato con `VALIDAR_EJECUCION_FAIL`. La reparación movía trozos de municipios
partidos sin comprobar la regla R012 de `validar_ejecucion` (un municipio partido admite un solo
distrito mixto), la misma que incumple Ávila en el M06 de Castilla y León.

- `ddd_core/m05_private_annealing.py` 1.1.0: rechaza todo movimiento que aumente los municipios
  partidos con más de un distrito mixto. No forma parte de la huella M05, así que no invalida M06.
- `tests/test_m05_private_annealing.py` 1.1.0.

## 2026-10-29 — 02 — final del log de M04/M05 al fallar

Andalucía (40965846902), con su exención por municipio, no tiene distritos fuera de límites en M04 ni
informe M05: el fallo de M05 sólo queda en el log. `_reutilizable-generacion-territorial.yml` 1.2.3
guarda la salida de la etapa en `.ddd-logs/<etapa>.log` (con `pipefail`, sin cambiar el código de salida)
y, si M04 o M05 fallan, publica sus 40 últimas líneas como `DIAG_<etapa>`.

## 2026-10-29 — 04 — ruta de VALIDACION.json en el diagnóstico

`validar_ejecucion.py` escribe `ejecuciones/<RUN_ID>/VALIDACION.json` en la raíz, no en el `io.runs.dir` del
contrato; el diagnóstico de 1.1.3 sólo miraba `RUNS_DIR` y Castilla y León (40964570303) volvió a fallar
en M08 sin detalle. `_reutilizable-incorporacion-electoral.yml` 1.1.4 busca en las dos rutas.

## 2026-10-29 — 02 — diagnóstico M05 con exención por municipio

Andalucía (40958892613) incluía #347 y siguió en M05 `NO_FEASIBLE`; el diagnóstico seguía listando los
cuatro distritos exentos porque no conocía `population_floor_exempt_municipalities`.

- `diagnosticar_poblacion_m05.py` 1.1.0: respeta la exención por municipio y publica `DIAG_M05_INFORME`
  (estado, motivo y claves de reparación/violaciones del informe M05).
- `tests/test_diagnosticar_poblacion_m05.py` 1.1.0.

## 2026-10-29 — 03/04 — retrieved_at en contratos Minsait y DIAG_VALIDACION

- Extremadura (40957543745) falla en M07: `contrato.sources[0]: falta retrieved_at`.
  `adaptador_minsait_csv.py` declara `retrieved_at` (parámetro `--retrieved-at`; por defecto, la hora UTC
  de adaptación). El paquete electoral debe regenerarse (03 sin reutilizar).
- Castilla y León (40957531696) falla en M08: `municipios con fragmentación inválida=1`, sin decir cuál.
  `_reutilizable-incorporacion-electoral.yml` 1.1.3: si la 04 falla, publica `DIAG_VALIDACION` con
  `failures` y `municipality_violations` de `VALIDACION.json`.
- `generar_estado_operativo.py` 2.3.1: si la fase fallida no está numerada (Murcia, 40957577850:
  «Reanudación de producto electoral durable»), «parado en» la muestra en vez de quedar vacío.

## 2026-10-29 — Población — exención de suelo por municipio en Andalucía

Decisión del propietario. Con atomicidad 1,25 (#342) y semillas M04 nuevas, Andalucía (40952332904) sigue
en `NO_FEASIBLE_REPAIR_FOUND` por cuatro distritos de municipios rurales bajo el suelo: en Cádiz, los de
11002 (20.261 hab., 0,25), 11005 (35.805, 0,45) y 11001 (52.719, 0,66); en Sevilla, el de 41001 (55.814, 0,70).

- `andalucia_2025.yaml`: `validation.population_floor_exempt_municipalities` = 11001, 11002, 11005 y
  41001 (mecanismo de #343): sólo el distrito que contiene cada municipio queda exento del suelo.

## 2026-10-29 — 02/04 — checkpoints M04 y consumo de M06 certificado

- Andalucía (40946875467), País Vasco y Cataluña reanudaron M05 desde un checkpoint M04 de un run
  anterior generado con atomicidad 1,75: la selección sólo comparaba fuentes. Los diagnósticos
  salieron idénticos a los previos a #342.
- Castilla y León (40954321463) y Extremadura (40954334572) fallan en la 04 con «No existe un producto
  territorial certificado y reutilizable»: #343 cambió `modulos/05_optimizar_distritos.py`, que forma
  parte de la huella M05, y todos los M06 anteriores dejaron de ser «reutilizables».

Cambios:

- `seleccionar_checkpoint_productivo.py`: un checkpoint M04 o posterior exige que su informe M04 tenga
  la misma K y el mismo umbral de atomicidad que el contrato vigente (sin informe: no verificable, no
  bloquea). Nuevo `--consume-certified-product`: un M06 certificado no exige la huella del motor M05
  (sí fuentes, configuración M04 y certificación poblacional).
- `incorporacion-resultados-electorales.yml` 2.0.2: la 04 localiza el M06 con ese modo.
- `tests/test_checkpoint_m04_configuracion.py` (nuevo).
- `test_materializacion_contratos_nacionales` 1.0.4 y `test_pre_m04_evidence_pipeline` 1.0.2: los casos
  históricos de archipiélagos pasan a la raíz congelada (Baleares y Canarias ya tienen M06 en main).

## 2026-10-29 — 00 — detector de M08 huérfano con receipts del catálogo

Los 00 40946826228 (Castilla y León) y 40946838414 (Extremadura) fallan antes de la 04 con
`RECOVERY_IDENTITY_CONTRADICTORY: faltan receipts territorial o electoral vigentes`. El detector sólo
buscaba `evidencia/catalogo/electoral_source_2025.json`, pero los receipts que registra la 03 viven en
`evidencia/fuentes_electorales/...`, donde los declara el catálogo.

- `detectar_producto_electoral_huerfano.py`: si no existe el receipt en `evidencia/catalogo/`, usa la
  ruta de `evidence.<kind>` del catálogo. Con los inventarios reales de 40895514741 y 40895537017 el
  resultado pasa a `NO_RECOVERY / M08_ABSENT` y la 04 puede ejecutarse.
- `tests/test_huerfano_recibo_declarado.py` (nuevo).

## 2026-10-29 — Población — atomicidad municipal 1,25 en Andalucía, País Vasco y Cataluña

Decisión del propietario (opción B). Andalucía (40891753503), País Vasco (40891768209) y Cataluña
(40891810589) terminan M05 en `NO_FEASIBLE_REPAIR_FOUND` con distritos residuales bajo el suelo.

- `materializar_contrato_generacion.py`: `population_limits` admite `municipality_atomicity_limit_ratio`
  por territorio (1 < valor <= techo, con rationale/evidence/decided_at). Si es la única clave, el
  perfil de límites sigue siendo `standard-1.0.0`. Así el umbral sobrevive a la re-materialización
  (el cambio de Valencia, #336, sólo tocó su contrato).
- `politica_generacion_territorial_2025.yaml` 1.5.1 y contratos de los tres territorios: umbral 1,25
  en `territory_contract`, M04 y `validation`.
- `test_materializacion_contratos_nacionales` 1.0.3.

## 2026-10-29 — Población — exenciones de suelo en Ibiza, Tenerife y 35-C02

Decisión del propietario (opción A). Con el diagnóstico de la 02 (#337), Baleares (40891796781) y
Canarias (40891782899) terminan M05 en `NO_FEASIBLE_REPAIR_FOUND` sólo por distritos residuales de
particiones insulares bajo el suelo.

- `politica_generacion_territorial_2025.yaml` 1.5.0: `structural_floor_exemptions` para Ibiza
  (07-C04), Tenerife (38-C01) y 35-C02, con evidencia y motivo.
- Contratos de Baleares y Canarias: las particiones se añaden a `population_floor_exempt_partitions`
  y su auditoría marca `floor_exception_required`.
- `test_materializacion_contratos_nacionales` 1.0.2.
- Andalucía, País Vasco y Cataluña siguen pendientes (opción B no aplicada).

## 2026-10-29 — 04 — diagnóstico de M07/M08 al fallar

Castilla y León (40895514741, M08, exit 3) y Extremadura (40895537017, M07, exit 1) fallan en la 04 y
los logs de Actions no son legibles desde fuera del repositorio.

- `_reutilizable-incorporacion-electoral.yml` 1.1.2: la salida de M07 y M08 se guarda en
  `.ddd-logs/<etapa>.log` (sin cambiar el código de salida) y, si la 04 falla, sus 40 últimas
  líneas se publican como anotación `DIAG_M07` / `DIAG_M08`.
- `test_gestor_campana_nacional` 0.0.7: el caso histórico de Extremadura sin par se evalúa sobre la
  raíz congelada (Extremadura ya tiene fuente electoral y par en main).

## 2026-10-29 — 00 — encadenado del par también en modo reutilizar

Los 00 40892947074 (Aragón), 40892962009 (Castilla y León) y 40892977224 (Extremadura) terminaron
con `SKIPPED_NO_ACCREDITED_PAIR` y el job `encadenar_par_y_04` se saltó: su condición excluía el modo
reutilizar, que es el modo por defecto.

- `ejecucion-completa-proyecto.yml` 1.4.1: el encadenado se dispara en cualquier modo salvo si el 00
  lo lanzó `github-actions[bot]` (el propio relanzamiento); así se sigue encadenando como mucho una
  vez y la UI no gana controles nuevos.
- `tests/test_00_encadenado_par.py` 1.0.1.
- `test_preparacion_legislatura_vigente`: Extremadura admite `ACQUIRE` o `REUSE` (ya tiene fuente
  electoral durable 40892977224), para que main no dependa del estado vivo.

## 2026-10-29 — 00 — reutilización con la fuente territorial re-descargada

Los 00 en reutilización de Aragón (40888544861), Extremadura (40888581480) y Castilla y León
(40888506741) fallaban en «Resolver fases necesarias»:

- Aragón y Extremadura: `TERRITORIAL_REPLAN_BLOCK: fuente elegida difiere del catálogo: run_id`.
  `independent_source_evidence` (receipt F10 antiguo, no promovido) tapaba a la re-descarga de
  `preparation_evidence` con la que se generó el M06 vigente; y, sin linaje producto→fuente, el
  M06 nuevo no se reconocía como reutilizable.
- Castilla y León: `DURABLE_ASSET_INVALID: electoral_product: receipt durable ilegible`; la evidencia
  electoral apuntaba a un informe .md del M08 anterior al M06 nuevo.

Cambios:

- `consumir_par_fuentes_legislatura.py` 1.2.0: sin linaje versionado, la reutilización geométrica
  acepta el manifiesto del productor M06 si es del mismo run que el producto y su
  `inputs.source_package_artifact` coincide (run, nombre y SHA-256) con el receipt territorial
  vigente (`SOURCE_PRODUCER_MANIFEST_MATCH`). Cualquier otra diferencia mantiene el bloqueo.
- `catalogo_preparacion.yaml`: se retira `independent_source_evidence` de Aragón, Extremadura y
  Castilla y León (su razón de ser, preservar el linaje del M06 histórico, desaparece con el M06
  nuevo); Castilla y León pasa a `electoral_product_available: false` hasta el 04 sobre el M06 nuevo.
- Tests: `test_linaje_manifiesto_productor_m06` (nuevo); `test_preparacion_legislatura_vigente`
  compara el candidato de Aragón con el receipt que el catálogo declara vigente.

## 2026-10-29 — 02 — diagnóstico de población al fallar M04/M05

Andalucía, País Vasco, Canarias, Baleares y Cataluña terminan M05 en `NO_FEASIBLE_REPAIR_FOUND` y,
al fallar, no se sube ningún artefacto M05: no había forma de saber qué distritos incumplen.

- `herramientas/diagnosticar_poblacion_m05.py` (nueva): localiza la última salida M05 (o M04) en la
  caché, calcula población, ratio, partición y municipios de cada distrito fuera de suelo o techo
  (respetando las particiones exentas) y emite `::warning::DIAG_DISTRITO {...}` por distrito.
- `_reutilizable-generacion-territorial.yml` 1.2.2: si M04 o M05 fallan, ejecuta el diagnóstico en la
  imagen de producción (sin ocultar el fallo) y sube `ddd-diag-poblacion-<run>-<etapa>`.
- `tests/test_diagnosticar_poblacion_m05.py` (nuevo).

## 2026-10-29 — Fuentes — Extremadura con provisionales por sección

Decisión del propietario (29-10-2026). El CSV provisional por sección (Minsait / EleccionesDB, 966
secciones, 522.418 votos) difiere del definitivo del DOE (524.837) en 2.419 votos (0,46 %).

- `configuracion/contratos_minsait_provisionales.yaml`: `owner_production_exception` (decided_at,
  rationale, evidence, `max_delta_ratio: 0.01`) en Extremadura 2025.
- `resolver_contrato_minsait_provisional.py`: con excepción completa y delta dentro del máximo,
  `production_eligible=true`; si el delta lo supera, falla. Sin excepción sigue en false.
- `adaptador_minsait_csv.py`: `--production-eligible`. `preparacion-resultados-electorales.yml`
  1.0.2 lo pasa cuando el contrato resuelto lo declara.
- `preparacion_legislatura_vigente.yaml` 1.0.3: Extremadura pasa de `BLOCKED_PROVISIONAL` a `ACQUIRE`;
  1.0.4: Andalucía y Castilla y León pasan, como Aragón, a `ACCEPTED_M07_RECONCILIATION`.
- `verificar-andalucia-2026-provisional.yml`: el contrato y el paquete provisional sólo son
  elegibles con `owner_production_exception`; el flag del adaptador se pasa con un array (actionlint).
- `f10_auto_tareas.json`: nueva huella del contrato Minsait en la ficha F10-EXT-ELECTORAL-SOURCE.
- Tests: `test_preparacion_legislatura_vigente`, `test_contratos_minsait_provisionales`,
  `test_territorial_only_selector`. Castilla y León generó un M06 nuevo (40868935788): su caso
  histórico 35889595424 pasa a `tests/fixtures/acreditacion_historica` y a la raíz congelada en
  `test_acreditacion_historica_territorial` y `test_prepared_source_pair_execution`.

## 2026-10-29 — Fuentes — Aragón con RTVE y reconciliación M07

La fuente electoral de Aragón (RTVE, resultados 2026 por sección, paquete 36136639133) estaba lista
para reutilizar, pero `electoral_2026_crosswalk_status: BLOCKED_PENDING_OFFICIAL_EVIDENCE` la dejaba
en BLOCKED. Decisión del propietario (29-10-2026): se usa RTVE y las secciones 2026 sin
correspondencia con el mapa 2025 cuentan como pérdida atribuible a DDD en M07, acotada por su margen.

- `preparacion_legislatura_vigente.yaml` 1.0.2: Aragón pasa a `ACCEPTED_M07_RECONCILIATION` con
  `crosswalk_decided_at` y `crosswalk_rationale`. Andalucía y Castilla y León siguen bloqueadas.
- `resolver_preparacion_legislatura.py`: admite ese estado sólo con decisión fechada y razonada.
- `test_preparacion_legislatura_vigente.py`: Aragón admisible; el resto sigue bloqueado.

## 2026-10-29 — F10 — re-descargas del mismo año

`herramientas/estado_derivado_f10.py` 1.1.4: un receipt territorial posterior al de la matriz de
seguimiento hereda el cierre F10 si conserva los años de población y seccionado, aunque cambien la
huella del paquete, la identidad territorial o la de compatibilidad (re-descarga INE desde el
principio). Otro año sigue exigiendo una auditoría nueva y un receipt anterior sigue bloqueando.
Proyección viva: adquisición territorial CLOSED 19/19. `test_f10_derived_doors.py` 1.1.6.

## 2026-10-29 — Población — exenciones estructurales y Cataluña

- Baleares (40847174556, M05 `hard=3`): la preparación territorial del 28-10 (9732a463) regeneró
  `validation` y borró la exención de Menorca (07-C02) de #313, porque el materializador sólo eximía
  componentes de un distrito bajo el suelo. `materializar_contrato_generacion.py` lee ahora
  `territories.<id>.structural_floor_exemptions` (rationale, evidence, decided_at) de la política,
  las une a las exenciones calculadas y las marca como requeridas y gobernadas en la auditoría de
  reparto. `politica_generacion_territorial_2025.yaml` 1.4.0 declara Menorca; el contrato vigente
  recupera la exención.
- Cataluña (40847205333): con #323 pasa M02–M05 y la auditoría geométrica (135 distritos, 0 BLOCK)
  y la certificación termina en `POPULATION_HARD_BLOCK`. Su contrato activa `private_annealing`
  (1800 s).
- Castilla y León (40850261102): con `private_annealing` la M05 vuelve a fallar; usa unidades
  indivisibles (`ddd_unit_id`) que sólo gestiona el reparador focal, con el que ya cumplía suelo y
  techo (sólo fallaba el ±12 %, retirado en #325). Vuelve al reparador focal.
- Tests: `StructuralFloorExemptionTests` y el archipiélago balear materializado incluye 07-C02.

## 2026-10-29 — 00 — encadenado automático del par de fuentes hasta la 04

La 04 exige un `prepared_source_pair` que sólo registra "Activación de Legislatura Vigente"; el 00
no lo creaba, y en cada primera ejecución completa (Cantabria, Castilla-La Mancha, Galicia,
Asturias, Ceuta, Madrid, Melilla, Navarra) hubo que activar el par y relanzar el 00 a mano.

- `ejecucion-completa-proyecto.yml` 1.4.0: nuevo job `encadenar_par_y_04`. Si la clasificación
  electoral termina en `SKIPPED_NO_ACCREDITED_PAIR`, la ejecución es `workflow_dispatch` en `main`,
  no está en modo reutilizar y el manifiesto quedó registrado, lanza la activación (`prepare_one`),
  espera a la suya y, si termina bien, relanza el 00 en "Reutilizar progreso existente" con el mismo
  territorio, edición, estrategia y publicación. Permisos del job: `actions: write`, `contents: read`.
  Una ejecución en modo reutilizar nunca vuelve a encadenar.
- `preparacion-legislatura-vigente.yml` 1.0.2: `run-name` con territorio y operación para que el 00
  identifique su activación entre varias simultáneas.
- `tests/test_00_encadenado_par.py` (nuevo) y `test_ejecucion_completa.py` 1.0.5 (lista de jobs del 00).

## 2026-10-29 — Plataforma — Dependabot sólo parches

`.github/dependabot.yml` 1.1.0 ignora `version-update:semver-major` y `version-update:semver-minor`
en acciones y pip. La #293 (checkout 4→7, upload-artifact 4→7, setup-python 5→7 en 34 workflows)
se cerró sin fusionar: CI en rojo y sin cabeceras, legacy ni registro. Las versiones mayores se
actualizarán en una PR propia validada con una ejecución completa.

## 2026-10-29 — Población — Castilla y León, La Rioja, Andalucía y País Vasco

- Castilla y León (M05 `hard=0 fuera_12=2`, validación oficial `VALIDAR_EJECUCION_FAIL`) y La Rioja
  (M06 PASS 33/33, certificación `POPULATION_TARGET_NOT_MET`) eran los dos únicos contratos con
  `require_zero_outside_tolerance_after_m05: true`. Decisión del propietario (29-10-2026): se retira
  y quedan con la regla de los otros 17 territorios (suelo y techo duros).
- Andalucía (M05 `hard=4`) y País Vasco (`hard=2`) agotaron la reparación `private_annealing` sin
  partición válida (`NO_FEASIBLE_REPAIR_FOUND`, 300 s y 120 s). Su `max_seconds` sube a 1800 s; si
  persiste, se examinará si la causa es estructural (unidades indivisibles, como Menorca).

## 2026-10-29 — M02/M03 y M05 — Cataluña, Canarias y Baleares

- Cataluña (40773400155): `M02 acreditación topológica obsoleta: stale topology accreditation;
  source binding changed: package_sha256, compatibility_identity_sha256`. La re-descarga INE de la
  misma edición y año de secciones trajo otra huella. `ddd_core/topology_preflight.py` 1.2.0 conserva
  la acreditación (`binding=SECTION_YEAR_REBOUND`) si sólo cambian huella de paquete e identidad de
  compatibilidad; M03 sigue verificando la pertenencia exacta de cada componente declarada (Tremp,
  Llívia). Otra edición o año de secciones sigue siendo obsoleta. Tests: `test_topology_preflight`
  (18), `test_m03_administrative_components` y `test_pre_m04_evidence_pipeline` (re-descarga
  reasigna; año distinto bloquea).
- Canarias (40832065646) y Baleares (40832091398) ya pasan M04 tras #319 y la certificación los
  bloquea como al grupo A: sus contratos activan `population_repair.strategy: private_annealing`
  (seed 0, 5.000.000 candidatos, 120 s). Sin aristas entre islas, la reparación no cruza componentes.

## 2026-10-29 — Estado operativo — README detallado

`herramientas/generar_estado_operativo.py` 2.3.0 (esquema JSON 2.2, sólo campos añadidos):

- "Cadena completa validada" exige que el M08 proceda del mismo run que el M06 vigente; Aragón deja
  de figurar como completo. FE se da por buena cuando la 04 terminó con ese linaje.
- Cada territorio informa de su última ejecución completa (`last_run`: run, estado, fase donde se
  paró, motivo y publicación 05), leída de `evidencia/ejecuciones_completas` y del preflight de
  generación, y de su siguiente paso (`next_step`).
- La tabla del README añade PUB (05), última ejecución, parada en, motivo y siguiente paso.
- `test_estado_operativo_unico.py`: reglas de linaje de la cadena completa y de la última ejecución.
- Galicia completó 01→04 (40832139215) y Baleares reacreditó su pre-M04: las regresiones de
  archipiélagos y de `test_pre_m04_evidence_pipeline` comprueban la regla (reacreditar sólo si el
  preflight no acredita el contrato) y los dos casos de Galicia pendiente de incorporar de
  `test_gestor_campana_nacional` usan la raíz congelada aee8215e.

## 2026-10-29 — M05 — reparación privada de población en cinco territorios

Los relanzamientos desde el principio del 28-10 (40784594752, 40784651090, 40784711945,
40784741627, 40784770643) generan M04–M06 y la puerta de certificación termina en
`Certificación territorial bloqueada: BLOCK`, la misma situación de Madrid antes de #313
(`POPULATION_HARD_BLOCK` / `TARGET_NOT_MET` con el reparador focal). Madrid completó 01→04
(40787900559) con `population_repair.strategy: private_annealing`.

- Los contratos de Andalucía, Castilla y León, Navarra, País Vasco y La Rioja activan el mismo
  `population_repair` (seed 0, 5.000.000 candidatos; 300 s en Andalucía y Castilla y León, 120 s
  en el resto). Castilla y León sustituye su reparador focal. La candidata sigue sometida a la
  validación oficial atómica de M05 y a la certificación M06.
- `test_territory_contract_admission.py` 1.3.0: el validador declarativo admite el perfil
  `private_annealing` (enabled, strategy, seed, max_candidates, max_seconds; requiere grafo y
  provincia) además del focal, que sigue exigiendo unidad indivisible.

## 2026-10-29 — Melilla y Galicia — excepciones decididas por el propietario

- Melilla (run 40773487000): con suelo 0,70 la M04 termina en
  `INCOMPATIBLE_ATOMIC_POPULATION_CONNECTIVITY … NO_EXACT_CONNECTED_HARD_PARTITION` (44 secciones,
  K=25, suelo 2.393,80, techo 5.984,51). `politica_generacion_territorial_2025.yaml` 1.3.0 y su
  contrato fijan suelo 0,50 y tolerancia 0,50; techo 1,75 sin cambios.
- Galicia (run 40706722115): M07 bloqueó por pérdida atribuible a DDD de 22.504/1.488.705 =
  1,5116 % > 1,5 %. `electoral_reconciliation.py` 2.1.0 admite `loss_exception` por elección
  (ratio, rationale, evidence, decided_at) con tope duro del 2 %; M07 7.3.2 la lee de
  `configuracion/excepciones_reconciliacion_electoral_2025.yaml` (nuevo), fuera del contrato
  electoral sellado por hash. Galicia 2024 declara 0,02.
- Raíz congelada aee8215e: `overlay/` guarda ya los 551 ficheros de estado de hasta 300 KB (4,4 MB),
  no sólo los reescritos hasta hoy; las ejecuciones de País Vasco, Navarra, Baleares y Castilla y
  León volvían a romperla. `test_m06_product_reuse_integration` y el caso de Castilla y León de
  `test_acreditacion_historica_territorial` usan la raíz congelada (su relanzamiento registra
  fuente nueva antes que su M06); `test_valencia_m02_native_crs` toma los años de fuente del catálogo.

## 2026-10-28 — Pre-M04 — inventario físico por año, con CUSEC verificado al materializar

La ejecución "desde el principio" de Canarias (40773378883) re-descargó del INE las secciones 2023
con otra huella (sectioning 11d3eb11…) y `_hard_partition_spec` exigía la huella exacta del
inventario de `configuracion/particiones_insulares_2025.json`: `SOURCE_IDENTITY_MISMATCH` antes de
M04 sin que cambiara ninguna sección. Rompía también `test_physical_components_source_identity`.

- `_resolver_ejecucion_completa_core.py` 1.0.2: sin huella exacta admite el único inventario del
  mismo año de secciones y población y lo declara (`inventory_binding =
  SECTION_YEAR_CUSEC_VERIFIED_AT_MATERIALIZATION`). `preparar_particiones_fisicas_m04` sigue
  verificando el universo y cada componente CUSEC a CUSEC; cualquier diferencia falla con
  `PHYSICAL_COMPONENT_INVENTORY_MISMATCH`. Un año sin inventario sigue en `SOURCE_IDENTITY_MISMATCH`.
- `test_physical_components_source_identity.py`: la re-descarga del mismo año reasigna el
  inventario; un año no acreditado falla cerrado.
- Raíz congelada aee8215e (`tests/_raiz_congelada.py`): ahora guarda la lista de ficheros de
  `configuracion/`, `orchestracion/`, `publicado/dashboard/` y `config/` y `evidencia/` de cada
  territorio con su SHA-256 (`MANIFEST.json`); oculta los añadidos después, superpone los
  reescritos (`overlay/`) y falla con mensaje explícito si uno nuevo cambia sin copia.
- Las regresiones de territorios reales que rompieron las ejecuciones del 28-10 (Ceuta, Galicia,
  Murcia, Cataluña, Canarias) usan la raíz congelada sólo en esos tests; la de archipiélagos pasa
  a regla (preparar fuente y reacreditar pre-M04 van juntos).

## 2026-10-28 — M04/M02 — rescate autonómico del 26-10

Se trae de `rescate/autonomico-20261026` (dab2299e) sólo el código y las regresiones del rescate:

- `ddd_core/m04_administrative_atomic_groups.py` (nuevo): Tremp y Talarn forman un grupo atómico
  administrativo en Cataluña.
- `ddd_core/m04_seed_engine.py`: partición exacta en Ceuta. `m04_seed_engine_v7410.py`: Canarias
  pasa de 2 a 3 núcleos residuales. `configuracion/m04_engine.json` 7.6.5.
- `territorios/region_de_murcia/config/region_de_murcia_2025.yaml`: M02 trabaja en EPSG:25830, lo
  que recupera la adyacencia Yecla–Jumilla perdida en M03.
- Predecesores en `legacy/`; regresiones `test_m04_administrative_atomic_groups`,
  `test_m04_residual_cardinality` y `test_murcia_m02_native_crs` con sus fixtures.
- El expediente N08 de Cáceres acredita el motor M04 v7.6.4: `test_preflight_caceres_n08.py` lo
  lee de `legacy/ddd_core/m04_seed_engine_v7.6.4.py` y `verificar_evidencia_n08_readonly.py`
  1.1.1 lo monta en su copia aislada, como ya hacía con el M02 v7.3.2. `.dockerignore` 1.4.2
  incluye ese snapshot en la imagen de pruebas.
- La raíz congelada F10 superpone ahora todos los ficheros que reescriben las ejecuciones
  (catálogo, contratos `*_2025.yaml` y `evidencia/catalogo/*.json` de los 19 territorios y estado
  operativo, 62 ficheros de aee8215e); la de Melilla en curso rompía la versión parcial.
- `test_gestor_campana_nacional.py` 0.0.6: la campaña de 14 rutas comprueba que cada ruta
  corresponde a su plan, sin recuentos fijos.

## 2026-10-28 — Melilla — límites de población excepcionales

La política de generación 1.2.0 admite `population_limits` por territorio: solo suelo,
techo y tolerancia, con `rationale`, `evidence` y `decided_at` obligatorios. El
materializador los aplica y emite `limits_profile: exception` con esos tres campos,
que `territory_contract` ya exige para cualquier límite distinto del estándar. Melilla,
declarada territorio excepcional por el propietario, pasa a suelo 0,70 y tolerancia
0,30. Con 44 secciones indivisibles y K=25 hacen falta al menos 6 distritos de una sola
sección, y con la población INE 2023 la 6.ª sección más poblada es el 72,8 % del
objetivo; con el suelo del 80 % no existe partición. El techo (1,75) no cambia: el par
más poblado es 1,70. El resto de territorios conserva los límites nacionales. Las
versiones anteriores de la política, del materializador y del contrato de Melilla se
conservan en `legacy/`.

- `test_gestor_campana_nacional.py` 0.0.5: con el contrato nuevo Melilla pasa a
  `SOURCE_PREPARATION_REQUIRED`, como Baleares; la campaña de 14 rutas queda en 4/3/7.

## 2026-10-28 — Puerta 02→03 — M06 caducados desde su release durable

`herramientas/localizar_artefacto_durable.py` localiza un artefacto acreditado por run,
nombre y SHA-256: usa el de Actions si sigue vivo o, si caducó, el asset
`<nombre>-<id>.zip` de las releases draft `almacen-m06-*`, y solo acepta bytes con el
mismo SHA-256. `_reutilizable-puerta-validacion.yml` 1.2.0 la usa antes de bloquear un
M06 acreditado cuyo artefacto caducó, y también para su auditoría (PR #311).

## 2026-10-28 — M05 — bloqueos de población de Madrid y Baleares

Diagnóstico con los informes M04/M05/M06 de los checkpoints (rama `diagnostico/poblacion-20261028`).

- Madrid: el reparador focal agota su cola con 90 de 135 distritos urbanos cerrados y deja una
  violación dura (distrito 110, 17.401). El ensayo local de `private_annealing` sobre el mismo
  grafo M03 y la misma salida M05 la elimina (partición válida, 27 s). El contrato activa esa
  estrategia; la candidata sigue sometida a la validación oficial atómica de M05.
- Baleares: Menorca (07-C02, 5 distritos, 99.005 habitantes) no admite ninguna partición sobre el
  suelo: Mahón (30.006) y Ciudadela (31.669) son indivisibles y los otros tres distritos dispondrían
  de 37.330 habitantes para un mínimo de 49.218. Se exime del suelo como Formentera (07-C03) y su
  auditoría de reparto lo declara. El cambio de contrato obliga a reacreditar la fase pre-M04.

## 2026-10-28 — Tests — linaje M06/M08 por regla y no por run_id fijo

Asturias (40706742818), Cantabria (40701656466) y Castilla-La Mancha (40706698510) completaron
01→04 tras activar su par de fuentes y registraron M06 y M08 del mismo run. Tres regresiones
fijaban los run_id anteriores (CLM 37444564173, Asturias 40241852045) y exigían incorporar un M08
nuevo, por lo que `main` quedó en rojo sin cambio de código.

- `test_reanudacion_m08_huerfano.py` 1.0.3: la regresión de CLM comprueba la regla: el M08 se
  reutiliza sólo si su manifiesto productor lo liga al M06 vigente; si no, se rechaza.
- `test_gestor_campana_nacional.py` 0.0.4: Asturias, Cantabria y CLM incorporan M08 sólo cuando
  no hay uno con el linaje del M06 vigente; el run_id se toma del catálogo.
- `test_m06_product_reuse_integration.py`: el resolver durable debe devolver exactamente el M06
  que declara el catálogo, en vez de siete run_id fijos.
- `test_ejecucion_completa.py` 1.0.4 y `test_continuar_ultimo_resultado_valido.py` 1.0.3: CLM
  reutiliza el M08 sólo si procede del mismo run que su M06 vigente.
- `test_preparacion_legislatura_vigente.py`: la preparación, el checkpoint y el M06 de Aragón
  proceden del mismo run. `test_promocion_automatica_catalogo.py`: la evidencia de Extremadura
  nombra el paquete de su propio run y fija digests completos.
- Los seis módulos `test_f10_*` que fijan recuentos y receipts exactos se evalúan sobre la raíz
  congelada en aee8215e (`tests/_raiz_congelada.py`, `tests/fixtures/raiz_congelada_aee8215e`):
  el árbol vivo se enlaza y se superponen los 25 ficheros que reescriben las ejecuciones.
- `F10LiveRepositoryRuleTests`: sobre el repositorio vivo sólo se exige coherencia. Asturias,
  Cantabria, Castilla-La Mancha y Galicia re-descargaron hoy del INE paquetes con bytes nuevos
  (mismos años) y F10 los deja en BLOCKED hasta una auditoría nueva; es fail-closed por diseño.
- `f10-electoral-receipts-asturias-galicia.yml` 1.0.1: la proyección F10 viva se comprueba por
  coherencia (sin errores de catálogo, 19 territorios por puerta) y no por recuentos fijos.


## 2026-10-28 — M06 — Aragón y Extremadura adoptan sus productos del 28-10

Los M06 acreditados de Aragón (36321736287) y Extremadura (36472516474) ya no tienen artefacto
en Actions; la acreditación histórica de Aragón solo sella puerta y auditoría. Se adoptan los M06
de las ejecuciones 00 del 28-10 (40656036271 y 40656175842), cerradas en SUCCESS y conservados en
los releases draft `almacen-m06-*`: catálogo, contrato, preflight y producto territorial vuelven al
estado que registraron esas ejecuciones.

- El contrato de Aragón conserva los bytes que fija su manifiesto M06, sin cabecera; sale de
  `GovernanceHeaders` (`test_r015_invariantes.py` 1.2.2) y lo gobiernan su manifiesto y
  `test_m06_product_reuse_integration.py` 1.0.2.
- `promover_catalogo_operacional.py` 1.1.2: al registrar un M06 retira el
  `territorial_product_source_lineage` del producto anterior. Aragón conservaba el de 36321736287
  y la reutilización geométrica atribuía el M06 nuevo a la fuente antigua; se retira del catálogo.
- Las regresiones del producto histórico siguen ejercitándose con fixtures del commit d497bf39
  (`tests/fixtures/acreditacion_historica`, `tests/fixtures/linaje_historico`); los demás tests
  fijan los valores adoptados.

## 2026-10-28 — 00/01/02 — estado registrado por las ejecuciones del 28-10

Las seis ejecuciones 00 "Ejecutar desde el principio" del 28-10 (Andalucía 40655989924,
Aragón 40656036271, Castilla y León 40656083930, Comunidad Valenciana 40656129840,
Extremadura 40656175842 y Madrid con GerryChain 40658423303) registraron en `main`, sin CI,
fuentes, contratos y catálogo nuevos. Cuatro terminaron en FAILED (Andalucía
`POPULATION_HARD_BLOCK`; Castilla y León `POPULATION_TARGET_NOT_MET`; Valencia sin años en la
declaración; Madrid `BASELINE_INVALID` en el M05 de GerryChain) y dejaron el catálogo
contradiciendo sus productos: Castilla y León perdía el linaje de su M06, Madrid acreditaba un
paquete nuevo que F10 bloquea y el contrato de Aragón perdía su cabecera de gobernanza.

Se devuelven la configuración, el preflight, el producto territorial y el catálogo de los seis
territorios al estado anterior. Aragón y Extremadura siguen cerrados con sus productos
acreditados (36321736287 con acreditación histórica sellada, y 36472516474); sus M06 del 28-10
quedan como evidencia en `generaciones_m06/` para adoptarlos en un cambio propio. Se conservan
también los receipts y manifiestos de ejecución de los seis runs.

- `_reutilizable-generacion-territorial.yml` 1.2.1: "Verificar datos territoriales preparados"
  usa la declaración que acredita el catálogo (`territorial_source_declaration`) y solo recurre a
  `config/fuentes_oficiales.yaml` si no hay ninguna; la ruta fija leía en Valencia una
  declaración sin `population_year` ni `section_year`.
- `materializar_contrato_generacion.py`: al reescribir un contrato conserva sus comentarios
  iniciales; `yaml.safe_dump` borraba la cabecera VERSIÓN/ANTERIOR que exige R015.

## 2026-10-28 — F10/M06 — estado registrado por las ejecuciones 00 del 27-10

Los commits automáticos de registro de esas ejecuciones avanzaron `main` sin CI y
dejaron siete pruebas en rojo. `estado_derivado_f10.py` 1.1.3 acepta como expediente
acreditado un receipt territorial distinto del de la matriz F10 solo si su run es
posterior y coinciden `package_sha256`, la identidad territorial, los dos hashes de
compatibilidad y los años: cada reutilización de 00 vuelve a registrar el mismo
paquete con run y artefacto propios, como Murcia en el run 40604944550. Un paquete
distinto sigue bloqueando hasta una nueva auditoría F10, y el receipt de la matriz
mantiene la comprobación completa. `test_m06_product_reuse_integration.py` fija los
M06 de Cantabria (40604431189), Castilla-La Mancha (40604483629) y Galicia
(40604535110), cuyos digests coinciden con sus manifiestos durables. Las versiones
anteriores se conservan en `legacy/`.

## 2026-10-28 — 01 — fuente territorial registrada con artefacto caducado

`preparacion-fuentes.yml` 1.4.2: en la reutilización ordinaria, si el artefacto del
paquete territorial registrado caducó o fue eliminado, el paso "Recuperar fuente
territorial registrada" emite un aviso y cede a "Adquirir y congelar fuentes"; el
registro posterior apunta al paquete nuevo. Antes terminaba con `exit 44`, como en
Andalucía (run 40604585745) y Comunidad Valenciana (run 40604791319). Siguen
bloqueando un digest distinto (`exit 45`), un nombre ambiguo y la recuperación exacta
con `recover_run_id`, que solo admite esos bytes. El job final ya no atribuye a una
preparación fallida el aviso de estado PENDING no persistido.
`tests/test_preparacion_fuente_caducada.py` ejecuta el script real del paso con un
`gh` simulado para cada caso. La versión anterior se conserva en `legacy/workflows/`.

## 2026-10-27 — 02 — registro del producto territorial M06

`promover_catalogo_operacional.py` 1.1.1 importa `manifest_sha256` en el mismo
bloque con respaldo de ejecución directa que sus demás dependencias. La versión
1.1.0 lo importaba como `herramientas.manifest_generacion_territorial` dentro de
`promote()`; el workflow 02 invoca la herramienta por ruta y sin `PYTHONPATH`,
así que el paso "Registrar producto territorial certificado" fallaba con
`ModuleNotFoundError` tras generar y certificar M06. Así ocurrió en los runs
40544326534 (Cantabria), 40544333932 (Castilla-La Mancha) y 40544340229 (Galicia).
`tests/test_promocion_ejecucion_directa.py` ejecuta la herramienta en modo directo
y rechaza imports de paquete sin respaldo. No cambia la lógica de promoción ni
los productos; la versión anterior se conserva en `legacy/herramientas/`.

## 2026-10-27 — N08 — puerta de publicación y trazabilidad de pilotos

Los candidatos analíticos de León y Cáceres quedan excluidos del sitio Pages por defecto. El publicador solo los empaqueta si su caller selecciona explícitamente `include_congreso_analytical_preview`; el enlace de navegación se añade únicamente en esa ruta. El flujo de preflight no despliega y registra en cada GeoJSON el SHA-256 del archivo candidato y el run ID que creó la vista. El visor valida y presenta esos valores junto con el SHA del testigo. Los candidatos siguen con `generation_authorized=false` y `NOT_CERTIFIED`; no se cambia la autorización ni se publica nada en este cambio.

## 2026-10-26 — M06 — contrastar la fuente del manifiesto 02

El resolver contrasta la referencia de `source_package_artifact` del manifiesto
M06 standalone con el run, nombre y SHA-256 de la fuente territorial durable.
Los manifiestos 00 conservan su validación por fase `01 ·`; los de 02 validan
sus `inputs` y bloquean si falta o difiere el paquete. Se añade cobertura para
fuente coincidente y paquete cruzado con `territorial_sources_prepared=true`.

## 2026-10-26 — M06 — manifiesto durable para workflow 02

El workflow 02 descarga el estado M06 ya empaquetado, verifica los recibos de
M05 y auditoría y escribe después un manifiesto independiente con identidad del
run, contrato, entradas, estrategia, portfolio cuando GerryChain 50 aplica,
decisión certificadora y referencias de artefactos con digest y tamaño. El
recibo territorial apunta al manifiesto sin alterar el ZIP ni introducir una
referencia circular. El resolver comprueba su integridad y linaje. Un M08 cuyo
M06 productor no coincide se conserva históricamente y deja de ser reutilizable,
pero ya no invalida por ello el M06 territorial. Las pruebas cubren bytes
alterados, identidad cruzada, evidencia incompleta, mismatch M06/M08 y escritura
idempotente. No se regeneran productos ni se ejecuta incorporación electoral.

## 2026-10-26 — CI — actualizar expectativas obsoletas de evidencia y preflight

Las pruebas F10 vuelven a esperar el resultado fail-closed del consumidor frente
a los recibos actuales que no coinciden con la matriz histórica: 5 adquisiciones
territoriales CLOSED y 14 BLOCKED, sin elevar la puerta conjunta ni producción.
Los tests pre-M04 reconocen los preflights vigentes de Cataluña y Baleares y no
planifican una reacreditación redundante; los casos sin evidencia suficiente
siguen exigiéndola. El test unitario de replanificación usa una fixture pequeña
para no depender del manifiesto territorial mutable de Asturias, cuya ausencia
sigue bloqueando correctamente el plan durable. Se archivan las versiones
previas de los tests y de este registro. No se cambian recibos, catálogo,
contratos ni productos.

La regresión M08 de Castilla-La Mancha distingue el M06 territorial_only del
run 40241650464 del par histórico M06/M08 del run 37444564173; la reutilización
cruzada permanece bloqueada. Asturias, Cantabria y Castilla-La Mancha quedan
bloqueadas para reutilización cuando falta el manifiesto o el linaje M06/M08 no
coincide. Ceuta, Baleares y Canarias conservan sus preflights pre-M04 vigentes y
no repiten preparación. En la matriz dirigida de 14 territorios, los 3 bloqueos
de linaje se mantienen fuera de la matriz de 11 rutas ejecutables. No se cambia
lógica de producto ni evidencias. Las versiones previas de los cuatro tests
actualizados se archivan en `tests/legacy/ci_followup_20261026/`.

## 2026-10-19 — Cataluña — acreditación municipal pre-M04 ligada a fuente

La puerta pre-M04 admite discontinuidades municipales solo cuando los componentes
M03 coinciden con la acreditación contractual vinculada a la misma edición, año,
paquete e identidad de compatibilidad. Los contadores se validan con tipos enteros
estrictos; las desconexiones globales o provinciales y los componentes no resueltos
continúan bloqueados. La materialización conserva los datos requeridos para lectura
y recuperación durable. Las evidencias M03 previas al nuevo blob M02 exigen
reacreditación antes de su uso; este cambio no ejecuta M04 ni habilita generación.

## 2026-10-19 — OPT-01 — preservar evidencia histórica y reacreditar M02

El CI mostró que los manifiestos N08 y los productos pre-M04 conservados
corresponden al blob M02 anterior. La verificación histórica usa ahora el
snapshot v7.3.2 archivado, sin reescribir los manifiestos ni outputs
inmutables; la planificación territorial fail-closed exige preparar y
acreditar de nuevo cuando detecta esa identidad anterior. La imagen de pruebas
incluye únicamente el archivo histórico necesario para comparar el defecto de
truncamiento. No se reacreditan territorios por actualizar sus hashes.

## 2026-10-19 — OPT-01 — enumeración completa de candidatos M02

M02 conserva todos los hits del índice espacial y los procesa en orden estable;
`max_candidates` deja de truncar el superset geométrico y omitir contactos
válidos. La configuración continúa aceptada por compatibilidad, pero no limita
la exhaustividad. Las evidencias pre-M04 ligadas al blob M02 anterior requieren
reacreditación antes de cualquier generación posterior.

## 2026-10-19 — AUTO-01 — identidad fail-closed de unidades topológicas

El preflight topológico valida que cada identificador de unidad sea no nulo,
no vacío y único después de normalizarlo como texto. Entradas inválidas quedan
bloqueadas antes de evaluar contactos, evitando que filas distintas colapsen
en el grafo. No cambia la construcción de M01–M03 ni los contratos territoriales.

## 2026-10-12 — F10 — receipts independientes sin promoción de producto

El consumidor territorial #179 acepta ahora un `independent_source_evidence` opcional
cuando el catálogo lo marca expresamente como evidencia auténtica no promovida. El campo
lleva su propio receipt y hashes. `preparation_evidence`, `territorial_product` y sus
linajes históricos permanecen separados. Un estado promovido, no clasificado o malformado
falla cerrado. Se añaden regresiones positivas y negativas con identidad del receipt.

La extensión permite acreditar nuevas fuentes oficiales sin inferir que los productos
existentes fueron generados desde ellas. No cambia temporalidad, contratos territoriales,
autoridad cartográfica, estado canónico ni autorización de producción.

## 2026-10-12 — F10 — receipt independiente de Extremadura

El catálogo registra el receipt auténtico de Extremadura `38091144559` en un campo
independiente, con estado explícito no promovido. El consumidor #179 puede validarlo
sin sustituir el source run histórico `35755043806` ni el producto M06 `36472516474`.
La evidencia conserva los SHA-256 del artefacto y paquete originales. Las pruebas
comprueban la aceptación del receipt, la separación de linajes y la continuidad de los
14 consumidores históricos PASS.

## 2026-09-21 — GerryChain — disciplina municipal contractual

El canary real de Asturias `35656993014` mostró que el preflight GerryChain
reinterpretaba la disciplina municipal usando siempre `CUMUN`, aunque el contrato
territorial había materializado previamente unidades internas conectadas para municipios
sobredimensionados. El validador común ya resuelve esos casos mediante
`partitioning.strategy=connected_internal_units` y `partition_unit_field`.

GerryChain pasa a consumir exactamente esa misma unidad declarada de disciplina municipal.
No se introducen excepciones por territorio ni cambios de umbrales. Los municipios reales
se conservan como metadato administrativo; la restricción dura se aplica sobre la unidad
contractual que produjo la Formación inicial. Se añade regresión específica con la
configuración vigente de Asturias y una prueba sintética que demuestra que el municipio
bruto fallaría mientras las unidades internas declaradas pasan.


## 2026-09-21 — Optimización territorial — autoridad única del grafo operativo

Se corrige la integración GerryChain tras el fallo factual del run Galicia `35586097396`.
La estrategia alternativa reconstruía una segunda contigüidad desde el contacto físico de
polígonos y podía rechazar una partición válida en el grafo territorial ya certificado,
incluidas pasarelas declaradas para islas, rías, enclaves o discontinuidades municipales.

La restricción dura de contigüidad pasa a tener una única autoridad: el grafo operativo
producido por Construcción del grafo territorial. La discontinuidad física se mantiene como
diagnóstico separado y auditable, pero no puede invalidar por sí sola una partición conectada
según dicho grafo. La semántica de aristas de Adyacencias territoriales (`edge_type`,
`admin_scope`, `reason`, `source`) se conserva en el grafo para trazabilidad.

Además, si GerryChain no produce una salida utilizable, Optimización de distritos ejecuta
automáticamente la estrategia Canónica y conserva evidencia explícita del fallback. No se
modifican contratos territoriales, umbrales, reparto provincial ni disciplina municipal.

# Registro de cambios DDD

Registro cronológico acumulativo. No se reescriben entradas antiguas.

## 2026-09-21 — Comarca efectiva en Aragón y huella territorial

Aragón activa `io.input.comarcas.enabled: true` con cobertura completa para que
`comarca_surcharge` sea efectivo en GerryChain. Este cambio modifica
deliberadamente el contenido de M01 y, por propagación, la huella de los
productos territoriales M01–M06 en la siguiente ejecución de Aragón. Una huella
distinta después de esta activación es el resultado esperado del nuevo atributo
comarcal y no debe clasificarse por sí sola como regresión. Los productos
anteriores siguen siendo evidencia histórica de ejecuciones previas.

El valor por defecto de `comarca_surcharge` pasa a `0.0`: ningún territorio
recibe presión comarcal implícita. Todo valor positivo debe declararse
explícitamente y exige comarcas activadas en M01 con cobertura completa.

## 2026-09-15 — Estado verificable y continuidad de componentes

El run Aragón `34960965537` deja de figurar como baseline canónico porque la
auditoría independiente bloquea siete de sus 67 distritos. Se conserva como
candidato reproducible. Producción genera un manifiesto `PASS/BLOCK`; el visor
toma territorio y K del contrato y muestra como diagnóstico todo resultado sin
PASS verificable. La regresión Aragón y el preflight de ensembles exigen
continuidad geométrica disuelta. GerryChain valida además un grafo de cada
componente poligonal para impedir que una sección `MultiPolygon` oculte una
discontinuidad. Comarca permanece como objetivo blando. No se ejecuta ningún
territorio ni se crean nuevas copias físicas en `legacy`; el predecesor queda
recuperable en Git.

## 2026-09-15 — Interfaz territorial en español

La interfaz manual pasa a `operacion-territorial.yml`. El formulario presenta
los 19 territorios y sus operaciones con nombres españoles legibles, incluido
**Islas Baleares**, y mantiene la compatibilidad con los identificadores
técnicos existentes. No se ejecuta ningún módulo ni resultado territorial.

## 2026-09-15 — Piloto GerryChain ejecutable y defendible

El ensemble parte ahora de M05, nunca de una semilla M04 que incumpla las
restricciones. Antes de repartir los cinco perfiles, una puerta geométrica
independiente vuelve a medir las fronteras, rechaza contactos solo puntuales y
valida la contigüidad de los 67 distritos. La selección usa memoria constante y
la forma se puntúa con Polsby–Popper geométrico, manteniendo comarca,
población, provincia, municipio y contigüidad en el contrato. El paquete se
valida localmente; no se ejecuta ningún territorio.

El primer lanzamiento remoto confirmó la puerta sintética, pero Docker no pudo
ejecutar el script montado desde el workspace por falta de permiso ejecutable.
El workflow lo invoca ahora mediante `/bin/bash`; el fallo ocurrió antes de M01.

## 2026-09-14 — Blindaje de cálculo y publicación

C‑01, las regresiones M06, Flourish y los despliegues web quedan exclusivamente
bajo orden manual. Una prueba impide reintroducir `push` o `schedule`. La fuente
`COMARCAS.csv` se verifica aisladamente: 731 municipios, 33 comarcas, sin claves
inválidas ni duplicados contradictorios. No se ejecuta M01–M08.

El commit `24eb07e` supera la suite `34882876061`. Fue el único workflow
activado; queda certificado que el blindaje evita cálculo y publicación por push.

## 2026-09-14 — Paquete local-first — Comarcas e interfaz M01–M08

M01 añade una unión comarcal opcional por código municipal de cinco dígitos y
registra cobertura, duplicados contradictorios y faltantes. M03 conserva código
y nombre de comarca en los nodos y M06 en catálogo y composición, sin usar la
comarca como restricción. La interfaz manual se unifica bajo **Operación
territorial DDD — M01 a M08**; la línea contractual queda solo como workflow
reutilizable y el formulario G10 por tramo pasa a legacy. El paquete se prueba
con datos sintéticos y no habilita fuentes ni ejecuta territorios.

La primera certificación detecta que la baja del workflow G10 no se materializó
en el árbol remoto. Tras retirarlo, la segunda detecta una comprobación legacy
dentro del contenedor que excluye esa carpeta por diseño. Se corrige la prueba
sin relajar la ausencia del workflow activo ni la verificación legacy exterior.

## 2026-09-14 — R039 — Contrato electoral universal

M07 deja de contener el formato RTVE y de recibir tablas de partidos en el YAML
territorial. Un contrato común identifica la convocatoria, verifica fuentes y
diccionario por SHA-256, declara el adaptador de entrada y rechaza partidos no
catalogados. M08 exige igualdad exacta de distritos y rechaza duplicados. Aragón
se migra como implantación de referencia usando el fichero ya certificado; no
se ejecuta ni recalcula ningún módulo territorial.

### R039.1 — Prueba compatible con la imagen reproducible

El CI `34832589193` falla únicamente porque `.dockerignore` excluye los inputs
voluminosos. La prueba conserva la comprobación de bytes cuando están presentes
y valida dentro de la imagen la igualdad de huella entre contrato y manifiesto.
M07 mantiene la verificación obligatoria sin bypass. No se ejecuta territorio.

### R039.2 — Certificación CI

El commit `6e8162b` supera la suite general `34833051502`; el candidato inicial
también superó la validación de contratos `34832589145`. No se activó ningún
workflow territorial. R039 queda cerrado y R040 continúa bloqueado hasta orden
expresa.

## 2026-09-14 — C-01.1 — Corrección del falso PASS de robustez

El run `34778283915` completó 50 procesos, pero solo 15 produjeron mapas dentro
de la tolerancia poblacional. Se corrige el evaluador para separar éxito de
proceso y solución técnica; G01 queda `FAIL_ROBUSTNESS`. La semilla canónica
continúa siendo un resultado técnico válido, pero no robusto. No se reejecuta
ningún módulo territorial.

## 2026-09-14 — C-12.1 — Certificación de nombres

El commit `148d705` supera la suite `34786913415`. Se certifican 214 nombres
técnicos únicos y recomputables. C-12 queda cerrado sin modificar límites.

## 2026-09-14 — R038 — Interfaz y operación limpia

Se archivan diez workflows territoriales sustituidos y se crea una única
interfaz manual con cinco operaciones. La línea común pasa a ser reutilizable,
publica los productos del run y comparte un único identificador entre decisión
y ejecución. Se corrige además un error de sintaxis preexistente en
`procedimiento.sh` que impedía ejecutar M04-M08.

## 2026-09-11 — R001 — Profesionalización y recuperación
Se convierte el código recuperado de Aragón en procedimiento reproducible y auditable: M01–M08, SemVer + `legacy/`, GitHub como evidencia, contenedor, checksums, validación dura y contigüidad por grafo.

## 2026-09-11 — Workflow v2.7.1
Se preserva v2.7.0 y se corrige el heredoc de `PRODUCTOS.json`.

## 2026-09-11 — R014 — M05 v7.3.0
La auditoría de Run #7 demuestra un mínimo local del greedy. Se añade greedy determinista + recocido reproducible sin relajar provincia, contigüidad, unidades municipales ni suelo/techo.

## 2026-09-11 — Run #8 — Promoción R014
Run `34592470470` SUCCESS: `fuera_12=0`, máximo desvío 11,943 %, todas las invariantes R012 PASS.

## 2026-09-11 — R015 — Pruebas y gobernanza
Se añade suite de regresión/determinismo, auditoría de cabeceras y predecesores `legacy/`, y se normaliza la gobernanza. La CI pasa a ser puerta obligatoria.

## 2026-09-11 — R016 — M05 v7.4.0
Se elimina la parada al primer `fuera_12=0`; M05 continúa refinando máximo desvío y error cuadrático hasta agotar el presupuesto.

## 2026-09-11 — Run #9 — Promoción R016
Run `34599224954` SUCCESS. Primera factibilidad en iteración 9.038; resultado final tras 20.000 iteraciones: máximo desvío 9,930 %, error cuadrático 0,161271162560. Se mantienen 67 distritos, 1.463 secciones, 1.364.621 habitantes, reparto 11/7/49 y todas las restricciones PASS. Run #9 pasa a baseline.

## 2026-09-11 — Simplificación de ramas
Se eliminan cuatro ramas históricas `infra/*` y la rama temporal R016. Queda únicamente `main`.

## 2026-09-11 — R018 — Arquitectura multi-territorio

**Objetivo:** preparar el producto DDD para 17 comunidades, España completa y posterior adaptación internacional sin forks del motor.

**Decisiones arquitectónicas:**
- un repositorio;
- una rama permanente `main`;
- motor común en `ddd_core/`, `modulos/`, `herramientas/`;
- paquetes territoriales en `territorios/<id>/`;
- Aragón pasa a implantación de referencia explícita;
- Castilla y León se crea como segunda implantación y prueba de generalización;
- Extremadura será la siguiente prueba de reutilización.

**Procedimiento:** `procedimiento.sh` 2.1.1 → 2.2.0. Se elimina `aragon_2025` duro del directorio de caché y se deriva `run_name` del YAML. No se cambia algoritmo territorial.

**Documentación nueva:** `ARQUITECTURA_MULTI_TERRITORIO.md`, `CONTRATO_TERRITORIO.md`, `CONTINUIDAD_CASTILLA_Y_LEON.md`, `territorios/README.md`, paquete Aragón y scaffold Castilla y León.

**Compatibilidad:** las rutas raíz históricas de Aragón continúan temporalmente para que el workflow validado siga reproduciendo Run #9. La estructura canónica nueva es `territorios/`.

**Limpieza:** documentos retirados/redundantes salen del árbol activo y se preservan en `legacy/docs/retirados_r018/` cuando aportan arqueología. No se elimina código histórico.

**Próximos frentes:** Aragón conserva R017 pendiente de calidad territorial. Castilla y León debe comenzar por fuentes → contrato → workflow genérico → M01 → M02/M03. No abrir M04 antes de aceptar el grafo base.


## 2026-09-12 — R021 — Auditoría y sincronización
Se audita el estado real multi-territorio y se crea `docs/SALIDAS_CHATGPT/` como continuidad ligera.

## 2026-09-12 — R022 — Observabilidad y expansión nacional
M03 v7.2.0 separa auditoría de enforcement. CAT-02 certifica Llívia; CAT-03 cierra Cataluña hasta M03. Run `34688010656` ejecuta Madrid y otros 13 territorios con un workflow reutilizable y matriz paralela.

## 2026-09-12 — R023 — Diagnóstico continental
Se lanza auditoría geométrica paralela para los siete territorios continentales con discontinuidades observadas. No se añaden pasarelas automáticas.


## 2026-09-12 — R024 — G10 semántico y evidencia durable

Se introduce el catálogo semántico v2: las tareas G10 se expresan por capa y fase legible; M01–M08 se conservan como identidad histórica compatible. Se añade admisión por huella y el índice durable `orchestracion/estado_tareas.json`.

El lote inicial `fase1-cierre-evidencia-v1` verifica evidencia ya existente de Aragón, Castilla y León y Extremadura sin recalcular M01–M08. Extremadura sigue experimental bloqueada. Un producto histórico sólo se convierte en `REUSED` después de una verificación y una huella materializada; la mera presencia de un archivo no autoriza reutilización.

## 2026-09-12 — R024.1 — Corrección de transporte de evidencia G10

El primer lote G10 detectó que la matriz entregaba la lista de artefactos como un único argumento literal. Se corrige la serialización de la lista en el workflow v1.0.1. No se modifican fuentes, contratos ni resultados territoriales; el relanzamiento solo verifica evidencia canónica ya existente.

## 2026-09-12 — R025 — Checkpoints semánticos G10

Se incorpora un adaptador de reenganche que selecciona exclusivamente el último checkpoint canónico anterior a una modificación. El inventario declara la cobertura real de Aragón, Castilla y León y Extremadura: no rellena huecos ni promueve evidencia experimental. Esta capa no recalcula resultados territoriales; prepara la integración posterior del procedimiento para ejecutar solo el tramo invalidado.

## 2026-09-12 — R025.1 — Validación del índice de checkpoints

Se corrige el validador inicial para admitir el índice multi-territorio y se preserva la primera versión en `legacy/g10/`. La validación distingue cobertura certificada de evidencia experimental bloqueada.

## 2026-09-12 — R026 — Procedimiento por tramo certificado

El lanzador territorial pasa a aceptar un intervalo semántico y registra `REENGANCHE.json`. Un reenganche posterior a M01 exige manifiesto de productos y grafo M03 materializado dentro del runner; sin ambos aborta antes de cálculo. Las ejecuciones parciales no se presentan como productos públicos validados.

## 2026-09-12 — R026.1 — Límites robustos en ejecución parcial

Se corrige el caso de tramos terminados antes de M04: el lanzador no intenta iterar un rango vacío. Se conserva v2.3.0 en `legacy/`; no hay alteración de algoritmo territorial.

## 2026-09-12 — R027 — Materialización verificable de checkpoints

Se incorpora el componente G10 que resuelve dependencias runtime, verifica bytes/SHA-256 y materializa únicamente evidencia autorizada. M05 exige M03+M04; Extremadura bloqueada se rechaza. Los informes se etiquetan `REUSED_MATERIALIZED`, sin promoción territorial.

## 2026-09-12 — R028 — Workflow de tramo certificado

Se añade un workflow manual único que materializa checkpoints antes de ejecutar. Su modo por defecto `verify_only` no calcula; `execute` requiere una decisión explícita y corre solo el intervalo semántico seleccionado en contenedor. Al finalizar deja artefacto y notificación compacta en la incidencia G10.

## 2026-09-12 — R028.1 — Compatibilidad del workflow de tramo

Se sustituye la sintaxis compacta rechazada por GitHub Actions por YAML expandido compatible. El workflow fallido se conserva en `legacy/`; no llegó a iniciar ningún job ni alteró datos territoriales.

## 2026-09-12 — R029 — Cierre factual F1 y operación G10

Se elimina la duplicación exacta de los cinco árboles históricos de Aragón bajo `resultados/ejecuciones/`, conservando su evidencia territorial canónica. `ESTADO_FACTUAL.json` v1.1 registra contratos territoriales, margen de tolerancia, línea base de compacidad y el bloqueo de Extremadura. El workflow G10 valida modo y la notificación se centraliza para evitar correo/issue duplicado.

## 2026-09-13 — R030 — Visor público y reenganche sin recálculo

Se incorpora el visor estático MapLibre y el despliegue GitHub Pages para Aragón y Castilla y León. Consume únicamente GeoJSON finales canónicos, transforma coordenadas para dibujo en el cliente y valida 67/82 entidades antes de publicar. El punto de reenganche deja de recomendar el lote autónomo que repetía M01–M06 y limita G10 a cambios con huella nueva.

## 2026-09-13 — R030.1 — Habilitación autónoma de GitHub Pages

El primer despliegue del visor validó y empaquetó correctamente, pero GitHub Pages no estaba habilitado. El workflow activa explícitamente Pages en el primer uso y conserva su predecesor; no modifica datos territoriales.

## 2026-09-13 — R031 — Estado operativo durable G10

Se añade un generador Python de informe operacional, su contrato de prueba y la primera salida canónica JSON/Markdown. El informe expresa territorios, estado y reenganche sin autorizar nuevo cálculo territorial.

## 2026-09-13 — R031.1 — Cierre de lote con informe G10

El workflow durable genera el informe operativo antes de persistir y lo versiona junto al estado de tareas. Los artefactos del lote incluyen ambas salidas de reenganche.

## 2026-09-13 — R031.2 — Entrega completa de informe G10

El artefacto durable incorpora ahora los informes JSON y Markdown, y el comentario de finalización comunica la decisión de reenganche. Se corrige el contrato de prueba antes de consolidarlo como baseline.

## 2026-09-13 — R032 — Contrato declarativo de producto público

El visor MapLibre pasa de territorios codificados a un registro declarativo. El empaquetado de Pages genera un manifiesto verificando cardinalidad, propiedades y SHA-256 de cada GeoJSON canónico. La lista activa sigue limitada a Aragón y Castilla y León.

## 2026-09-13 — R032.1 — Reenganche alineado con producto público

El punto de reenganche pasa a señalar el estado operativo G10 y el registro declarativo de productos. Se elimina cualquier ambigüedad que pudiera provocar una repetición de M01–M06.

## 2026-09-13 — R033 — Contrato exhaustivo y verificación independiente de producto público

El manifiesto público valida ahora cada distrito: identidad única, geometría poligonal no vacía y campos declarados presentes. Se añade un workflow de verificación y empaquetado que genera el mismo sitio estático como artefacto, sin requerir GitHub Pages ni ejecutar M01–M06. Pages conserva únicamente la responsabilidad de despliegue.

## 2026-09-13 — R034 — Puerta de admisión territorial de producción

El contrato territorial pasa de guía documental a control ejecutable. La puerta verifica identidad, fuentes con checksum, seis módulos completos, continuidad de artefactos, coherencia de K/códigos/campos/restricciones y confinamiento de outputs antes de admitir M01–M06. Aragón y Castilla y León generan certificado `ADMITTED`; cinco pruebas negativas demuestran el rechazo anticipado de contratos incompletos. G10 sustituye su comprobación parcial por esta puerta. No se ejecuta ni recalcula ningún territorio.

### R034.1 — Procedencia disponible dentro del contenedor

La CI general y G10 revelaron que la imagen excluía correctamente los datasets, pero también su manifiesto ligero. `.dockerignore` conserva ahora `inputs/MANIFEST.sha256` sin empaquetar los datos; la puerta puede comprobar procedencia dentro y fuera del contenedor.

## 2026-09-13 — R035 — Interfaz única de producción territorial

La ejecución deja de seleccionar Aragón o Castilla y León mediante condicionales de workflow. Un resolutor toma el YAML admitido y deriva de él territorio, nombre de run y rutas. La nueva línea manual admite, verifica o ejecuta M01–M06; `execute` exige el literal de autorización explícita. Las pruebas demuestran dos contratos admitidos, rechazos tempranos y que los modos de control no ejecutan cálculo. No se ha lanzado ningún territorio.

### R035.1 — Certificación y cierre de la interfaz

CI `34747763671` completa correctamente. El checklist de cierre, el paquete de auditoría y el reenganche pasan a estado cerrado: el trabajo futuro es incorporar contratos territoriales autorizados, no seguir modificando la línea base.

## 2026-09-13 — R036.0 — Migración de auditoría y corrección de alcance

Se crea `docs/CONTINUIDAD_AUDITORIA_PLATAFORMA.md` como fuente de verdad para migrar la revisión externa a un nuevo hilo. Se distingue el cierre certificado de la interfaz R034–R035 del cierre todavía pendiente de la plataforma nacional. El backlog conserva política de K/límites, esquema, topología, limpieza operativa, capa electoral y prueba ciega. Se versionan el cierre y el punto de reenganche, preservando sus versiones anteriores en `legacy/`. No se ejecuta M01–M06 ni se abre ningún territorio.

## 2026-09-13 — R036 — Gobierno de K, límites y esquema

El catálogo registra la procedencia y justificación de K para los tres contratos M01–M06 existentes; el YAML conserva el valor ejecutable y la puerta exige coherencia con M04, M06 y validación. Se fija el perfil general `0.80/1.75/0.12`, con expediente obligatorio para excepciones. Se distinguen formalmente `bootstrap_m01_m03` y `production_m01_m06`. Aragón y Castilla y León conservan parámetros; Extremadura queda como excepción histórica bloqueada. Se añaden pruebas negativas y no se ejecuta ningún módulo territorial.

### R036.1 — Certificación CI

Commit `3d1337c` supera cinco workflows: puerta contractual, suite general, G10 y regresiones de evidencia de Aragón y Castilla y León. R036 queda cerrado sin ejecutar ni recalcular M01–M06.

## 2026-09-13 — R037 — Gobierno topológico

Los siete diagnósticos continentales R023 pasan a un registro ejecutable de bloqueo/reparación/admisión. Se prohíben puentes por proximidad automática y se exige expediente completo para cada arista lógica. En archipiélagos, la contigüidad se aplica dentro de cada componente, se prohíben aristas marítimas y distritos entre componentes, y el reparto de K debe preceder a M04. No se abre ni ejecuta ningún territorio.

### R037.1 — Certificación CI

Commit `8376276` supera la suite general en CI `34757140425`. El cambio no dispara regresiones territoriales ni ejecuta M01–M06. R037 queda cerrado y el reenganche avanza a R038.

## 2026-09-13 — Paquete A — C-05/C-09 Integridad electoral

M07 deja de descartar votos mediante un `inner join` silencioso. El nuevo cruce izquierdo produce un informe que conserva la identidad votos de entrada = asignados + no asignables y bloquea cualquier descuadre no declarado. Aragón registra expresamente la sección electoral `5002501003` y sus 608 votos no asignables, además de la sección censal `2221301003` sin resultados. La comprobación sobre evidencia certificada arroja 648.799 = 648.191 + 608 votos y 1.463 secciones en cada universo. M07 se reescribe en formato revisable. La implementación no solicita M01–M06.

### Paquete A.1 — Certificación CI

El commit `113c04c` supera la suite general `34760389448` y la puerta contractual `34760389449`. Por el disparador común `ddd_core/**` se ejecutaron además, de forma incidental, las regresiones M06 de Aragón y Castilla y León (`34760389453`, `34760389444`), ambas SUCCESS y sin modificación de productos en `main`. Esta activación no era necesaria para C-05/C-09 y queda registrada como riesgo de acotación de workflows.

## 2026-09-13 — Paquete B — C-02/C-03/C-14 Publicabilidad

Se separa formalmente `TECHNICAL_PASS` de `PUBLICABLE` mediante nueve criterios sustantivos y cuatro garantías. C-02 queda confirmado: Castilla y León incumple la puerta provisional de forma con 40/82 distritos bajo 0,15 y mínimo 0,02809. C-03 queda corregido: la correlación −0,3293 es real, pero no demuestra que apretar población empeore la forma; el cuartil con peor balance es también el de peor forma. C-14 queda resuelto con definición, umbrales y regla de promoción. Ningún mapa se declara hoy publicable como propuesta política. No se ejecuta M01–M06.

## 2026-09-13 — C-01.0 — Protocolo de robustez frente a semilla

Se fija antes de observar resultados una prueba de 50 semillas para Aragón. El
workflow reutiliza por hash M03/M04 del run certificado `34599224954`, ejecuta
solo M05, calcula distribución poblacional y de forma y elimina cada geometría
intermedia. No ejecuta M01–M04 ni M06–M08 y no lee resultados partidistas. La
semilla publicada `12345` debe ser técnicamente válida y no atípica entre los
percentiles 5 y 95; se exige al menos 95 % de ejecuciones satisfactorias.

### Paquete B.1 — Certificación CI

El commit `ccaa62a` supera la suite general `34773094091`, la validación de productos `34773094067` y G10 en modo control `34773094049`; ningún workflow territorial se activa. El despliegue `34773094057` alcanza correctamente el empaquetado y falla exclusivamente en `configure-pages`, por la habilitación externa pendiente de GitHub Pages ya documentada.

## 2026-09-13 — C-04 — Sesgo poblacional del reparto de K

Se publica una métrica reproducible de carga poblacional provincial frente a la media territorial usando solo evidencia ya certificada. El máximo absoluto es 4,546 % en Aragón (Teruel) y 9,674 % en Castilla y León (Palencia). Extremadura se mide en 0,190 % sin alterar su estado `EXPERIMENTAL_BLOCKED`. La herramienta, su entrada gobernada, tres pruebas y la evidencia JSON cierran C-04 sin ejecutar M01–M06 ni abrir territorios. El reenganche avanza a C-10; C-01 queda fuera de este bloque.

### C-04.1 — Certificación CI

El commit `83ea22a` supera la suite general `34779361255`. No se activa ningún workflow territorial ni se ejecuta M01–M06. C-04 queda certificado y el siguiente hito rector es C-10.

## 2026-09-13 — C-10 — Contrato único del catálogo M06

Se fija `polsby_popper` como nombre canónico y se publica el esquema único del catálogo distrital M06. Un adaptador cerrado hace explícita la migración de nombres históricos sin reescribir runs certificados. La prueba verifica Aragón, Castilla y León y Extremadura mediante el mismo contrato, sin condicionales por territorio; Extremadura permanece bloqueada. El cambio no invoca M01–M06 y el reenganche avanza a C-07 tras certificación CI.

### C-10.1 — Certificación CI

El commit `188c980` supera la suite general `34782359264`. Los patrones históricos de workflow activan incidentalmente las regresiones M06 de Aragón (`34782359206`) y Castilla y León (`34782359236`), ambas SUCCESS y sin persistir cambios de producto en `main`. La activación se registra como riesgo operativo; C-10 queda cerrado y el reenganche avanza a C-07.

## 2026-09-13 — C-07 — Prueba sintética adversarial

Se añade un pipeline sintético con población desigual 60/40/30/70, K=2 y solución contigua óptima única 100/100. La prueba exige la asignación exacta de secciones y contiene una mutación plausible que el oráculo debe rechazar. Deja de confundirse un smoke permisivo con capacidad de detección real. Solo se ejecutan datos temporales sintéticos; no se leen ni recalculan territorios certificados. C-01 permanece intacto.

### C-07.1 — Certificación CI

El commit `a359910` supera la suite general `34783919125`, incluida la ejecución adversarial completa M01–M06 sobre cuatro secciones temporales. No se activan regresiones territoriales ni se leen productos certificados. C-07 queda cerrado y el reenganche avanza a C-06.

## 2026-09-13 — C-06 — Verificación independiente

Se añade un verificador de biblioteca estándar que no importa el productor, `ddd_core` ni el validador existente. Recalcula desde M03 y M06 universo, población, K, provincia, contigüidad, límites y disciplina municipal. Aragón y Castilla y León pasan. Extremadura queda reforzada como `BLOCKED_INDEPENDENT_VALIDATION`: además de dos distritos fuera de tolerancia, presenta cinco municipios con más de un distrito mixto. No se recalcula ni modifica ningún territorio; C-01 permanece intacto.

### C-06.1 — Certificación CI

El commit `9dde785` supera la suite general `34784297475`. No se activan regresiones territoriales. C-06 queda cerrado y el reenganche avanza a C-08.

## 2026-09-13 — C-08.0 — Autorización expresa de regresiones territoriales

Las regresiones M06 de Aragón y Castilla y León dejan de responder a cambios en `ddd_core/**` o M04 y quedan disponibles exclusivamente mediante `workflow_dispatch`. Sus definiciones automáticas anteriores se preservan en `legacy/workflows/`. Una prueba de contrato impide reintroducir disparadores `push` o `schedule`. Es una corrección mínima de seguridad operacional necesaria para trabajar C-08 sin incumplir la prohibición de recalcular M01–M06; no constituye la limpieza completa R038 y no ejecuta ningún módulo territorial.

### C-08.0.1 — Certificación CI

El commit `4e3849c` supera la suite general `34785826965`. Es el único workflow activado: las regresiones territoriales no se ejecutan. El trinquete operativo queda certificado.

## 2026-09-13 — C-08 — Motor M04 único y trazable

Se declara `ddd_core/m04_seed_engine.py` como único motor M04 vigente mediante un contrato de máquina. El ejecutable del pipeline y la herramienta de unidades internas pasan de cargar snapshots por ruta a imports estáticos del motor canónico. Una prueba AST bloquea la carga dinámica y la selección versionada en la ruta operativa. La composición algorítmica certificada no cambia y ningún producto territorial se ejecuta o recalcula. Los snapshots no operativos se declaran históricos; su traslado físico corresponde a R038, todavía suspendido.

### C-08.1 — Certificación CI

El commit `5645a23` supera la suite general `34786162160`. Es el único workflow activado y no se ejecuta ninguna regresión territorial. C-08 queda cerrado; el backlog rector avanza a C-13 y después C-12.

## 2026-09-13 — C-13 — Comunidades de interés

P07 pasa de mención inerte a contrato formal supra-municipal. Se fijan fuente admisible, neutralidad ex ante, cobertura, cuatro métricas y precompromiso obligatorio de umbrales. Aragón y Castilla y León conservan sus rutas comarcales desactivadas; Extremadura no tiene fuente declarada. Los tres quedan `NOT_EVALUABLE`, estado que bloquea publicación. Se declara alcance sin inventar datos, modificar límites ni ejecutar M01–M06. Reincorporar una fuente territorial concreta requerirá orden expresa.

### C-13.1 — Certificación CI

El commit `5a4a884` supera la suite general `34786528440`, único workflow activado. No se ejecuta ninguna regresión territorial. C-13 queda cerrado y el backlog avanza a C-12.

## 2026-09-13 — C-12 — Nombres de distrito

Se publica un sistema determinista y no partidista de nombres técnicos basado en provincia y municipio de mayor población, con regla explícita para distritos sin mayoría municipal y ordinal estable para colisiones. La evidencia contiene 214 nombres únicos, cobertura completa, pesos dominantes y hashes de las tres composiciones M06 certificadas. Las pruebas recomputan los nombres desde esas entradas. No se altera M06, ningún límite ni C-01.
## 2026-09-14 — R038.1 — Diagnóstico durable de CI

La implementación R038 falla dos veces en la suite general `34825103970`, pese a que la misma ejecución completa pasa localmente con Python 3.11 y dependencias fijadas (71/71). La puerta CI se versiona y conserva siempre el log completo como artefacto, con propagación del código de salida mediante `pipefail`. No se modifica el motor ni se ejecuta ningún territorio.

### R038.2 — Corrección exacta de la prueba en contenedor

El artefacto `ci-unittest-34830251652-1` demuestra que la única caída es la búsqueda de `legacy/` dentro de una imagen que lo excluye deliberadamente. La prueba mantiene la ausencia de workflows retirados en la ruta activa y delega la existencia de predecesores a la puerta de checkout ya vigente. No se relaja ninguna garantía ni se ejecuta un territorio.

### R038.3 — Certificación CI

El commit `7a02dba` supera la suite general `34830677071`, único workflow activado. No se ejecuta ningún territorio. R038 queda cerrado y el siguiente hito es R039.

## 2026-10-10 — M06 v7.2.2 — precisión GeoJSON y conservación del predecesor

Se corrige la serialización de geometrías de sección y distrito por `ensure_geojson_zip`:
el escritor GeoJSON recibe `SIGNIFICANT_FIGURES=17` para evitar que el redondeo
colapse vértices próximos y produzca anillos inválidos. No cambian asignaciones,
criterios poblacionales, geometría en memoria ni contratos territoriales.

La versión sustituida M06 v7.2.1 se conserva íntegra en
`legacy/modulo06/06_consolidar_distritos_v7.2.1.py`, con blob Git
`993763be2942715af325766139dfbe6607c55b20`, idéntico al archivo
original del `main@776006e62ebd80ab20a55b186c3778bce76e9f19`.
El módulo actual se identifica como v7.2.2 y enlaza ese predecesor.
El diagnóstico estructural `ddd.m06-population-diagnostic/1.0` emite también
`version=7.2.2`, en coherencia con la cabecera, el predecesor archivado y
el mensaje de ejecución. Una regresión exige esa correspondencia de versión.
Se añade `tests/test_m06_geojson_precision.py` como regresión del roundtrip
GeoJSON y conservación exacta WKB.

El aislamiento técnico previo sobre Madrid con GerryChain seed 461102
acreditó K=135, hard=0, geometrías válidas 135/135 y validación M06 PASS;
no supone certificación ni prueba generación autónoma desde checkpoint crudo.
El cambio requiere CI y revisión del HEAD final de la PR #235 antes de integrar.

## 2026-10-12 — F10 — compatibilidad interanual y conservación del payload poblacional

La compatibilidad v1.1.0 distingue contribuciones de interiores de contactos por borde o punto, elimina bloqueos obsoletos tras cambios de código resueltos por igualdad exacta y detalla la población sin destino acreditado, sin confundir contabilidad completa con conservación en destino. La adquisición v1.4.1 preserva payload, SHA y procedencia antes del filtro, también si éste bloquea. Ambos predecesores se conservan íntegros en `legacy/herramientas/`.

Las regresiones reales y el replay de adquisiciones existentes mantienen bloqueados Aragón (31.024), Andalucía (319.989) y Castilla y León (84.197 habitantes). Valencia conserva los defectos originales y el bloqueo contractual; el snapshot histórico con cobertura 46 sigue siendo evidencia independiente del payload F10 perdido. El producto M06 de Extremadura y su receipt F10 independiente mantienen su linaje. Suite relevante: 119 PASS; linaje/gobierno: 17 PASS; consumidores: 14 PASS / 5 BLOCKED. Expediente: `docs/AUDITORIAS/F10_COMPATIBILIDAD_INTERANUAL_20261012/`. F10 continúa PENDING; no se ejecutaron adquisiciones nuevas, generación, promoción ni publicación.

## 2026-10-12 — Fuentes nacionales INE 2025/2025

Se materializa una pareja poblacional y geométrica de sección censal por CUSEC exacto, desde ZIP protegidos y N07. El manifiesto conserva hashes de entradas y salidas, procedencia, filtros y entorno; la reproducción independiente acredita 36.554 secciones, 52 circunscripciones y 49.128.297 habitantes con conciliación provincial/nacional exacta. El contrato de Nacional registra las fuentes con acreditación técnica, pero mantiene `CANDIDATO_WAIT_OWNER`, decisiones/K/cuotas pendientes y generación deshabilitada. No se altera la acreditación institucional ni se generan distritos.

## 2026-10-13 — F10 — fichas locales fail-closed y validación de entregas

Las cuatro fichas de investigación local solo quedan seleccionables cuando sus hashes,
alcances READ_ONLY, acciones permitidas y cobertura de validadores coinciden con el
contrato. El adaptador comprueba además que la entrega estructurada del ejecutor cita
las entradas fijadas, incluye pruebas y nombra el bloqueo electoral contractual exacto. Se archivan
los predecesores de las puertas y su derivador; las puertas territorial, electoral,
conjunta y de producción siguen siendo independientes y la producción continúa no
autorizada. Las pruebas usan evidencias existentes, sin campañas, consultas externas
ni escrituras productivas.

## 2026-10-12 — A2 / M05 v7.8.4 — estrategia autónoma privada experimental

Se integra `private_annealing` como opción explícita de M05. El reparador
monotónico y sus valores predeterminados no cambian; la estrategia privada
permanece desactivada por defecto. La búsqueda usa staging y solo promueve una
candidata tras superar la validación final. Se reconstruyen los atributos y el
informe de población finales y se protegen las salidas previas ante rechazo o
error. C-01 emite `UNSUPPORTED` para esta estrategia, cuya semilla anidada no
varía en el auditor. Los runs reproducibles de Madrid constituyen evidencia
experimental, no certificación territorial. Este cambio no activa Madrid, no
certifica el Motor Nacional y no habilita A3.

## 2026-10-19 — Comunidad Valenciana: corrección de reproyección M02

Trasladado el alcance técnico de #271 sobre el `main` posterior a #269/#270/#273: M02 usa EPSG:25830 y se declaran ediciones fuente de población y seccionado 2025, sin editar geometrías, tolerancias, población, puentes o contratos. Se conservan en `docs/AUDITORIAS/F10_VALENCIA_M02_REPROYECCION_20261019/` las pruebas M01–M03, hashes y límites de acreditación. Este cambio no constituye recibo territorial ni cierra F10; M04–M06 y la validación efectiva siguen pendientes.


## 2026-10-25 — P0 — colas durables y contrato GerryChain 50

Los grupos productivos con exclusión mutua conservan sus pendientes mediante `queue: max`; los grupos por territorio siguen aislados y los registros compartidos permanecen serializados. Las interfaces manuales derivan el contrato GerryChain 50 desde la estrategia; M05 falla explícitamente si ReCom falla o su portfolio no acredita 50 artefactos íntegros con 50 hashes de asignación distintos. La evidencia M05 distingue ejecución de certificación M06. El preflight documental local identifica 17 territorios candidatos y dos bloqueos, pero los artefactos de GitHub y los runs del 24-10 quedan sin verificar por falta de credenciales API. No se lanza producción ni se publica.


## 2026-10-25 — Smoke de concurrencia: proteger input manual

El workflow no productivo restringe `ticket` a opciones 1–5, lo valida y lo recibe por variable de entorno; el valor deja de interpolarse dentro del script Bash. La cola y su grupo permanecen iguales.

## 2026-10-20 — NAC-03 — rechazo de claves JSON duplicadas en capturas IGN

El validador de páginas OGC API Features rechaza ahora claves duplicadas en
cualquier objeto JSON, incluida la metadata de paginación y propiedades
anidadas de los límites. Se preserva byte por byte la versión 1.0.0 en
`legacy/n08_nac_20261019/`; el cambio no descarga fuentes, no acredita la
captura ni habilita comparaciones históricas.

## 2026-10-20 — Congreso NAC — auditor de capturas y búsqueda K>1 acotada

El auditor OGC API IGN rechaza claves JSON duplicadas en cualquier nivel para
evitar parseos ambiguos. Se añade una búsqueda determinista de cortes sobre un
bosque generador del grafo seccional para investigar K>1 con presupuesto
acotado. El diagnóstico solo devuelve hashes de testigos condicionales,
distintos estados de búsqueda e inputs; no emite asignaciones, no ejecuta
M04–M06, no acredita límites administrativos y no abre generación.

## 2026-10-20 — Congreso NAC — búsqueda reproducible con órdenes de bosque

Se incorpora la selección determinista de órdenes BFS y se ejecuta sobre las
44 unidades K>1. Siete unidades adicionales encuentran testigos condicionales
en órdenes alternativos; los casos restantes mantienen su clasificación de
búsqueda agotada o bloqueo estructural condicional. Se añade artefacto de
reproducción y se documenta que el catálogo CNIG consultado publica snapshots
históricos 2023/2024, sin identificar uno efectivo a 01/01/2025.

La ampliación conserva como predecesores exactos la búsqueda de un solo orden
y la versión 1.0.0 del buscador en `legacy/nac_continuacion_20261020/`. La
regresión compara dos órdenes explícitos y verifica que la identidad de entrada
no depende del orden de recorrido. Las 73 pruebas focales pasan; el cambio no
emite asignaciones ni habilita generación.


## 2026-10-20 — F10: reconstrucción nominal de variaciones INE 2025–2026

Se corrige el inspector de variaciones INE para verificar los SHA-256 de los tres ZIP
allowlisted, conservar referencias de registros TRAM y fechas, y separar cambios
efectivos antes de la elección de cambios posteriores. Se preservan los tres
originales y el esquema oficial. El dictamen registra las relaciones parciales
para Aragón, Castilla y León y Andalucía sin elevarlas a equivalencia electoral.
No cambia ninguna puerta F10, no se emite receipt electoral y no se redistribuyen
votos. Suite focalizada: `tests/test_inspeccionar_variaciones_callejero_f10.py` (11 pruebas).
