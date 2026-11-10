# T-137 · Inventario de divergencias de «plan válido»

Fecha: 2026-11-10. Código: `origin/main` 0ec9728. Solo lectura. Amplía la tabla de T-132
(`docs/ESTUDIOS/T132_BATERIA_MOTOR/NOTA_ARQUITECTURA_REGLAS.md`, rama `t132-bateria-motor`) con la línea exacta de
cada definición; no la repite. `herramientas/certificador_exacto.py` (T-136) aún no está en `origin`: cuando llegue se
añade como séptima columna (debe coincidir con el núcleo, no ser otra copia).

Siglas: **VAL** `herramientas/validar_ejecucion.py` · **CAN** `ddd_core/m05_opt_engine_v741.py` ·
**M05** `modulos/05_optimizar_distritos.py` · **REP** `ddd_core/m05_population_repair.py` ·
**GCP** `ddd_core/m05_gerrychain_strategy.py` (producción) · **GCE** `ddd_core/m05_gerrychain_engine.py` (+ `ddd_ensemble/`).

## Dónde se decide cada regla

| Regla | VAL | CAN / M05 / REP | GCP | GCE |
|---|---|---|---|---|
| Suelo/techo (razones) | `hard_limits` :136 | `hard_limits` CAN:229, M05:215/278 | :264-265 `step5 ▸ validation ▸ 0,80/1,75` | dataclass :43-44 `0,80/1,75` |
| Comparación | `pops>cap` sin margen :140 | `bounds_move_ok` :93 sin margen | `±1e-9` :638-640 | `±1e-9` :429-431 |
| Tolerancia objetivo | no se comprueba | métrica (`outside`) :274 | **objetivo, no dura** (:691) | **dura** (:433-436), con exención por debajo |
| Exención municipal | campo municipal de las secciones :49-66 | CAN: id de unidad `{prov}:{mun}:…` (:263); M05: campo + ancla :265 | :582-587 propio | :55-58 propio |
| Exención por partición | `zfill(2)` del valor de la sección, contrato sin `zfill`; solo la **primera** partición ordenada (:65-66) | CAN sin `zfill` (:230); M05 `zfill(2)` del contrato (:216) | sin `zfill` (:631) | no existe (T-132: inválida para el ensemble) |
| Contigüidad | componentes sobre aristas del grafo M03 (:127-134) | `connected` CAN:78 | BFS propio, incluye `topology_bridges` (:670-690, :1159) | BFS propio; sin puentes |
| Provincia única | `require_single_province_per_district` **por defecto False** (:146) | sí | **por defecto True** (:284) | **por defecto True** (dataclass) |
| Cuotas por provincia | clave tal cual (:158-161) | — | clave `zfill(2)` (:648) | clave tal cual (:445) |
| R012 mín/máx | `⌈P/techo⌉ … ⌈P/objetivo⌉` (:185-186) | **no** (lo confía a M04; REP solo penaliza :149, :458) | sí (:657-658) | sí (:452-453) |
| R012 mixtos | **`>1` fijo** (:191) | `max_mixed…` del contrato (CAN:222) | contrato (:662) | contrato (:457) |
| Campo de R012 | `partition_unit_field` si `connected_internal_units` (:168-170) | igual; **si falta el campo usa `id_field`** (CAN:109) | igual (:242-248) | atributo del nodo |
| Atomicidad `ddd_unit_id` | conservación de población (:125) | unidades | unidades colapsadas | `atomic_unit` :439 |
| Núcleos cerrados | no | `swap_polish` / ancla | `frozen_districts` (:665) | `preserve_closed_urban` (:459) |

## Divergencias con efecto (ejemplos)

1. **Tolerancia**: el mismo plan con un distrito a +13 % y tolerancia 12 % es PASS en VAL y en GCP, y violación dura
   en GCE (:433). GCE descarta planes que producción acepta; la batería debe compararlos con la misma vara.
2. **Defaults de provincia única**: un contrato sin `require_single_province_per_district` es PASS en VAL con
   distritos interprovinciales y FAIL en GCP/GCE.
3. **Campo R012 ausente**: CAN cae en `id_field` (cada sección es su propio «municipio», R012 vacía); VAL falla
   «falta campo de disciplina municipal».
4. **Exención municipal por id de unidad** (CAN): solo funciona si el `ddd_unit_id` sigue `{prov}:{mun}:…`; unidades
   con otro formato (p. ej. renombradas o `:F` sin municipio) no eximen, aunque VAL sí exima por el campo de sección.
5. **Partición exenta**: VAL normaliza la sección (`zfill(2)`) y no el contrato; un contrato con `"7"` nunca casa con
   `"07"`. Hoy los 115 contratos con la clave usan `[]` o códigos tipo `35-C02` (latente). VAL además mira solo la
   primera partición del distrito.
6. **Cuotas por provincia**: GCP compara con `zfill(2)` y VAL tal cual; una clave `"8"` en el contrato pasa en GCP y
   falla en VAL.
7. **Margen numérico**: un distrito exactamente en `techo+5e-10` es FAIL en VAL y PASS en GC (irrelevante con
   poblaciones enteras; se fija una regla única).
8. **Mixtos** y **mín/máx R012** y **razones por defecto**: ya en T-132 (puntos 1-3).
