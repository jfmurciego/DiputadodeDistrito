# Memoria del forense — catálogo de causas raíz

Fuente: `docs/ARQUITECTURA/FRAMEWORK_AGENTES_Y_ESTRUCTURA.md` §9 y `CLAUDE.md`. Una fila por causa cerrada, con id
estable (`causa_id` de la salida). Causa nueva: añádela aquí en la PR del arreglo, con su PR y run.

## Población, exenciones y política
| causa_id | Síntoma típico | Causa | Arreglo · ref |
|---|---|---|---|
| `checkpoint_reutilizado_anterior` | Falla igual tras fusionar el arreglo; `CHECKPOINT_RUN_ID` antiguo en el paso M04 | «Reutilizar» restaura el último checkpoint registrado, anterior a los arreglos | 00 «Ejecutar desde el principio» o «Generar desde fuente…» · run 41432561787 |
| `validador_sin_campo_municipal` | 04: `distritos bajo límite poblacional=1` en un distrito con municipio exento | Secciones M06 sin el campo municipal del contrato (`DDD_MUNICIPALITY_PARTITION`); el validador no ve el exento | Respaldo `CUMUN` / CUSEC[:5] · #398 |
| `exencion_municipio_particion` | Exención no aplicada en provincias con islas | Comparar «35012:35-C01» con «35012» | Comparar solo el municipio · #394 |
| `reparacion_mueve_exento` | Tras M05, otro distrito queda bajo suelo; `district_floor_overrides` por número de distrito | La reparación M05 mueve el municipio exento | Anclaje `floor_exempt_anchor` · #399 |
| `politica_no_reaplicada` | Techo antiguo (1,15) en M05 aunque la política declara otro | Contrato `already_complete`: el materializador no reaplica `population_limits` | `apply_policy_population_limits` · #403 |
| `exencion_por_id_unidad` | HARD_BLOCK en `estado_produccion` con M06 hard=0; distrito exento contado como duro | Exención detectada por el formato del id de unidad (`prov:mun:…`); ids numéricos no la muestran | Campo de municipio de las secciones, M05 7.8.7 · #404 |
| `residuo_municipal_sobre_techo` | Distrito sobre el techo con enclaves o residual `:R` de un municipio dividido | M05 mueve unidades enteras y no redibuja el residual; M04 lo dimensiona sin contar lo que se le pega | M04 7.6.6 alivio de residuos · #419 |
| `bloqueo_estructural` | Exceso o déficit que no mejora con reparación profunda | Municipios indivisibles o enclaves que encajonan distritos | Decisión del propietario (exención, techo propio) · #391 |

## Geometría, puentes y CRS
| causa_id | Síntoma típico | Causa | Arreglo · ref |
|---|---|---|---|
| `crs_3035_solapes` | `GEOMETRY_INVALID_AUDITED` en 01 o «grafo territorial no supera conectividad administrativa» con los puentes del autonómico | `working_crs` EPSG:3035 donde el autonómico usa 25830; los solapes INE pierden aristas M02 | Copiar 25830 · #374 #383 |
| `puentes_heredados_ausentes` | Pre-M04: «grafo territorial no supera conectividad administrativa» en provincia con enclaves | La provincia no hereda los puentes gobernados del contrato autonómico | `generar_provincias_congreso.py` `inherit_bridges` · #371 |

## Orquestación, catálogo y registro
| causa_id | Síntoma típico | Causa | Arreglo · ref |
|---|---|---|---|
| `m08_no_descargado_linaje` | Planificar: `DURABLE_LINEAGE_INCOMPATIBLE: electoral_product`; manifiesto con `artifact_digest` vacío | La puerta final de la 04 no descargó el M08; receipt electoral sin linaje validado | `electoral_product_available=false` + «Reutilizar» · #407 |
| `encadenado_sin_puerta_02` | 00 con la 02 skipped/failed que aun así activa el par y relanza otra 00 | `encadenar_par_y_04` no exige `puerta_02` en `success` | `needs` + `if` con la puerta · #389 |
| `catalogo_maestro_piloto` | Registro de M08: `ValueError: <territorio>: ausente del catálogo territorial maestro` | Persistidor con lector viejo del catálogo (solo `territories`) frente a `pilot_territories` | Persistidor desde `main` y SHA del cálculo · #360 |
| `replan_receipt_antiguo` | `TERRITORIAL_REPLAN_BLOCK: fuente elegida difiere del catálogo` | Fila del catálogo con receipt antiguo | Alinear con `preparation_evidence` · #338 #352 |
| `par_incompatible` | `TERRITORIAL_READY_PAIR_INCOMPATIBLE` | Cambió el M06 y el par electoral es de otro producto | 03 (si caducó) → `prepare_one` → 00 «Reutilizar» · `CLAUDE.md` |
| `cabecera_authorization_duplicada` | `remote: Duplicate header: "Authorization"` → HTTP 400 al registrar | checkout v6 deja su token en `includeIf.gitdir:`; el paso de credencial solo borra `http.extraheader` | Quitar ambos · #386 |
| `ruleset_rechaza_robot` | `GH013` al registrar | Ruleset que exige PR en `main` | App de registro exenta · #381 |
| `marcas_conflicto_registro` | `main` en rojo tras una fusión; registro con `<<<<<<<`/`>>>>>>>` | Fusión con marcas de conflicto | Hotfix #422; guardián de CI |

## Fuentes externas
| causa_id | Síntoma típico | Causa | Arreglo · ref |
|---|---|---|---|
| `infoelectoral_bloquea_runners` | 03: `curl 22` al descargar el ZIP de Interior | Interior rechaza runners y la sesión cloud | Espejo en release `fuente-infoelectoral-02202307` con la misma huella · #363 |
| `artefacto_caducado` | 403/404 al descargar un artefacto de Actions | Artefactos caducados (14 días) o 403 desde la nube | Volcados de `diagnostico/*`; pedir al Mac del propietario · `CLAUDE.md` |

## Ensembles
| causa_id | Síntoma típico | Causa | Arreglo · ref |
|---|---|---|---|
| `ensemble_crs_grados` | Casi todas las aristas «débiles» (<1 m) | `shared_border_m` medido en grados (EPSG:4326) | Reproyectar a `working_crs` · #409 |
| `ensemble_multipart` | `geometric_contiguity:<n>` en todos los perfiles | `preserve_atomic_multipart_sections=false`: piezas de secciones MultiPolygon sueltas | Opción a `true` (como M06) · #411 |
| `runner_falso_verde` | Run en SUCCESS con 0 candidatos válidos | El runner sale con 0 aunque fallen candidatos | Códigos de salida 3/4 · #410 |
| `ensemble_sin_sha256` | Publicación: «sin ensemble_sha256 acreditado» (exit 56) | El despliegue no pasa el sha256 del zip al publicador | `sha256sum` como output · #418 |
| `ensemble_guarda_proyectado` | Republicación: «No se reconoce la copia analítica proyectada esperada» | La guarda exigía candidatos proyectados y ya vienen en WGS84 | Validación por candidato · #421 |
| `ensemble_web_por_seccion` | «distritos observados 532 != 3» | La copia web lleva una feature por sección | `dissolve_by_district` · #424 |
