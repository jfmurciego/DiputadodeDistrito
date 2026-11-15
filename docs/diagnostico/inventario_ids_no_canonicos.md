# Inventario de ids de territorio no canónicos por rama de reutilización (T-349)

Base: `8ab93c647747b32860e0f8af21c33fd3f041c68e`. Generado con `python -m herramientas.inventario_ids_no_canonicos`. Solo lectura, orden determinista.

## Ramas y política del código (D-102)

| Rama | Política | Motivo |
|---|---|---|
| fuentes_territoriales | ESTRICTA | Activación, P10, P00, puertas y preflight comparan el id exacto (T-336, T-349) |
| electoral_fuente | ESTRICTA | Activación, P12, puertas y elegibilidad comparan el id exacto (T-349) |
| poblacion | ESTRICTA | la población y el seccionado viajan dentro del paquete de fuentes territorial (misma rama) |
| par_fuentes | ESTRICTA | registrar_par/consumir_par comparan el id exacto (T-349): un par registrado con id viejo se rechaza y se registra el nuevo |
| producto_M06 | ESTRICTA | resolver_activos_durables: recibo y manifiesto M06 con id exacto; con id viejo la P00 en reutilizar bloquea y se genera de nuevo |
| producto_M08 | ESTRICTA | resolver_activos_durables: un M08 registrado con id viejo se descarta (rejected_electoral_product) y se reincorpora |
| composicion_datos | SOLO_LECTURA_PUBLICADO | fichero_por_id lee el id viejo solo si no existe el canónico (D-61); lo que se escribe lleva el id canónico |
| registro_visor | SOLO_LECTURA_PUBLICADO | registro de solo adición: las entradas viejas se leen; la P50 añade la entrada canónica con alias_de y el run mayor la sustituye (migración en T-313) |

## Resumen por rama

| Rama | Política | Objetos | No canónicos |
|---|---|---|---|
| fuentes_territoriales | ESTRICTA | 71 | 0 |
| electoral_fuente | ESTRICTA | 71 | 71 |
| poblacion | ESTRICTA | 71 | 0 |
| par_fuentes | ESTRICTA | 71 | 70 |
| producto_M06 | ESTRICTA | 71 | 70 |
| producto_M08 | ESTRICTA | 71 | 71 |
| composicion_datos | SOLO_LECTURA_PUBLICADO | 141 | 141 |
| registro_visor | SOLO_LECTURA_PUBLICADO | 144 | 144 |

## Activación (resultado real de `resolver_preparacion_legislatura`)

| Territorio | Territorial | Motivo | Electoral | Motivo |
|---|---|---|---|---|
| aut01 | REUSE_TEMPORAL_SUBSTITUTION | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | OFFICIAL_SPECIAL_ACQUISITION_AVAILABLE |
| aut02 | REUSE_TEMPORAL_SUBSTITUTION | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| aut03 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| aut04 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| aut05 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| aut06 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| aut07 | REUSE_TEMPORAL_SUBSTITUTION | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| aut08 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| aut09 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| aut10 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| aut11 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| aut12 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| aut13 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| aut14 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| aut15 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| aut16 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| aut17 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| aut18 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| aut19 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| nac01 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| nac02 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| nac03 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| nac04 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| nac05 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| nac06 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| nac07 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| nac08 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| nac09 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| nac10 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| nac11 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| nac12 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| nac13 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| nac14 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| nac15 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| nac16 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| nac17 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| nac18 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| nac19 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| nac20 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| nac21 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| nac22 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| nac23 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| nac24 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| nac25 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| nac26 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| nac27 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| nac28 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| nac29 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| nac30 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| nac31 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| nac32 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| nac33 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| nac34 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| nac35 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| nac36 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| nac37 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| nac38 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| nac39 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| nac40 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| nac41 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| nac42 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| nac43 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| nac44 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| nac45 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| nac46 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| nac47 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| nac48 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| nac49 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| nac50 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| nac51 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |
| nac52 | REUSE | TERRITORIAL_DURABLE_CANDIDATE | ACQUIRE | ELECTORAL_ID_NO_CANONICO |

## Territorio × rama con objetos no canónicos

| Territorio | Rama | Objeto | Id (ejemplo) | Run/artefacto | Fecha | No canónicos/objetos | Resultado esperado |
|---|---|---|---|---|---|---|---|
| aut01 | composicion_datos | datos/composicion | fichero=andalucia.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| aut01 | electoral_fuente | evidence.electoral_source | recibo=andalucia | ddd-electoral-package-andalucia-2025-42463442007 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut01 | par_fuentes | evidence.prepared_source_pair | par=andalucia | 008152d29f59 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut01 | producto_M06 | evidence.territorial_product | recibo=andalucia | ddd-state-43107035084-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut01 | producto_M08 | evidence.electoral_product | recibo=andalucia | ddd-state-43204696160-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut01 | registro_visor | publicaciones_visor/canonical_m06 | 2 de 2 con id viejo | 42495072594,43204696160 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| aut02 | composicion_datos | datos/composicion | fichero=aragon.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| aut02 | electoral_fuente | evidence.electoral_source | recibo=aragon | ddd-electoral-package-aragon-2025-40896686254 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut02 | par_fuentes | evidence.prepared_source_pair | par=aragon | b52021ffe6d7 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut02 | producto_M06 | evidence.territorial_product | recibo=aragon | ddd-state-43011616681-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut02 | producto_M08 | evidence.electoral_product | recibo=aragon | ddd-state-43016936483-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut02 | registro_visor | publicaciones_visor/canonical_m06 | 2 de 2 con id viejo | 42497101869,43016936483 | — | 3/3 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| aut03 | composicion_datos | datos/composicion | fichero=principado_de_asturias.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| aut03 | electoral_fuente | evidence.electoral_source | recibo=principado_de_asturias | ddd-electoral-package-principado_de_asturias-2025-40693720831 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut03 | par_fuentes | evidence.prepared_source_pair | par=principado_de_asturias | 96f6b6b1fa3e | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut03 | producto_M06 | evidence.territorial_product | recibo=principado_de_asturias | ddd-state-43011625216-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut03 | producto_M08 | evidence.electoral_product | recibo=principado_de_asturias | ddd-state-43016768497-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut03 | registro_visor | publicaciones_visor/canonical_m06 | 6 de 6 con id viejo | 35728626894,36321743580,36398139343… | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| aut04 | composicion_datos | datos/composicion | fichero=illes_balears.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| aut04 | electoral_fuente | evidence.electoral_source | recibo=illes_balears | ddd-electoral-package-illes_balears-2025-40955056606 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut04 | par_fuentes | evidence.prepared_source_pair | par=illes_balears | 2a8ec31fdd7b | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut04 | producto_M06 | evidence.territorial_product | recibo=illes_balears | ddd-state-43011633844-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut04 | producto_M08 | evidence.electoral_product | recibo=illes_balears | ddd-state-43019811578-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut04 | registro_visor | publicaciones_visor/canonical_m06 | 2 de 2 con id viejo | 41033500476,43019811578 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| aut05 | composicion_datos | datos/composicion | fichero=canarias.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| aut05 | electoral_fuente | evidence.electoral_source | recibo=canarias | ddd-electoral-package-canarias-2025-42521092889 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut05 | par_fuentes | evidence.prepared_source_pair | par=canarias | 9de267ffb50c | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut05 | producto_M06 | evidence.territorial_product | recibo=canarias | ddd-state-43011642069-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut05 | producto_M08 | evidence.electoral_product | recibo=canarias | ddd-state-43020588641-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut05 | registro_visor | publicaciones_visor/canonical_m06 | 3 de 3 con id viejo | 40951280657,42523951377,43020588641 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| aut06 | composicion_datos | datos/composicion | fichero=cantabria.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| aut06 | electoral_fuente | evidence.electoral_source | recibo=cantabria | ddd-electoral-package-cantabria-2025-42707820760 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut06 | par_fuentes | evidence.prepared_source_pair | par=cantabria | e6f708de40a7 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut06 | producto_M06 | evidence.territorial_product | recibo=cantabria | ddd-state-43025633460-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut06 | producto_M08 | evidence.electoral_product | recibo=cantabria | ddd-state-43033094596-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut06 | registro_visor | publicaciones_visor/canonical_m06 | 3 de 3 con id viejo | 40241638106,41037133327,43033094596 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| aut07 | composicion_datos | datos/composicion | fichero=castilla_y_leon.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| aut07 | electoral_fuente | evidence.electoral_source | recibo=castilla_y_leon | ddd-electoral-package-castilla_y_leon-2025-42521090842 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut07 | par_fuentes | evidence.prepared_source_pair | par=castilla_y_leon | 3f2c6ef7aafa | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut07 | producto_M06 | evidence.territorial_product | recibo=castilla_y_leon | ddd-state-43025642604-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut07 | producto_M08 | evidence.electoral_product | recibo=castilla_y_leon | ddd-state-43030986959-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut07 | registro_visor | publicaciones_visor/canonical_m06 | 3 de 3 con id viejo | 40969454399,42521090842,43030986959 | — | 3/3 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| aut08 | composicion_datos | datos/composicion | fichero=castilla_la_mancha.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| aut08 | electoral_fuente | evidence.electoral_source | recibo=castilla_la_mancha | ddd-electoral-package-castilla_la_mancha-2025-40690624792 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut08 | par_fuentes | evidence.prepared_source_pair | par=castilla_la_mancha | c8d8bc1e4822 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut08 | producto_M06 | evidence.territorial_product | recibo=castilla_la_mancha | ddd-state-43025652192-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut08 | producto_M08 | evidence.electoral_product | recibo=castilla_la_mancha | ddd-state-43031565452-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut08 | registro_visor | publicaciones_visor/canonical_m06 | 6 de 6 con id viejo | 36018449928,36332474966,36344350450… | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| aut09 | composicion_datos | datos/composicion | fichero=cataluna.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| aut09 | electoral_fuente | evidence.electoral_source | recibo=cataluna | ddd-electoral-package-cataluna-2025-43036592492 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut09 | par_fuentes | evidence.prepared_source_pair | par=cataluna | 3090588ad0a3 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut09 | producto_M06 | evidence.territorial_product | recibo=cataluna | ddd-state-43025661789-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut09 | producto_M08 | evidence.electoral_product | recibo=cataluna | ddd-state-43204706233-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut09 | registro_visor | publicaciones_visor/canonical_m06 | 3 de 3 con id viejo | 40952013601,41062562553,43204706233 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| aut10 | composicion_datos | datos/composicion | fichero=comunidad_valenciana.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| aut10 | electoral_fuente | evidence.electoral_source | recibo=comunidad_valenciana | ddd-electoral-package-comunidad_valenciana-2025-40956462986 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut10 | par_fuentes | evidence.prepared_source_pair | par=comunidad_valenciana | dabb1f70e89c | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut10 | producto_M06 | evidence.territorial_product | recibo=comunidad_valenciana | ddd-state-43025671156-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut10 | producto_M08 | evidence.electoral_product | recibo=comunidad_valenciana | ddd-state-43030421638-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut10 | registro_visor | publicaciones_visor/canonical_m06 | 3 de 3 con id viejo | 40973760398,41062567297,43030421638 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| aut11 | composicion_datos | datos/composicion | fichero=extremadura.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| aut11 | electoral_fuente | evidence.electoral_source | recibo=extremadura | ddd-electoral-package-extremadura-2025-42720735134 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut11 | producto_M08 | evidence.electoral_product | recibo=extremadura | ddd-state-43051488486-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut11 | registro_visor | publicaciones_visor/canonical_m06 | 5 de 5 con id viejo | 35859241320,36136783101,40965231300… | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| aut12 | composicion_datos | datos/composicion | fichero=galicia.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| aut12 | electoral_fuente | evidence.electoral_source | recibo=galicia | ddd-electoral-package-galicia-2025-40389705458 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut12 | par_fuentes | evidence.prepared_source_pair | par=galicia | fe42fdfcdd62 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut12 | producto_M06 | evidence.territorial_product | recibo=galicia | ddd-state-43045478748-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut12 | producto_M08 | evidence.electoral_product | recibo=galicia | ddd-state-43051951192-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut12 | registro_visor | publicaciones_visor/canonical_m06 | 4 de 4 con id viejo | 35978568807,36403519566,40241719200… | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| aut13 | composicion_datos | datos/composicion | fichero=madrid.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| aut13 | electoral_fuente | evidence.electoral_source | recibo=madrid | ddd-electoral-package-madrid-2025-40773465956 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut13 | par_fuentes | evidence.prepared_source_pair | par=madrid | 4e4ba55364eb | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut13 | producto_M06 | evidence.territorial_product | recibo=madrid | ddd-state-43045415140-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut13 | producto_M08 | evidence.electoral_product | recibo=madrid | ddd-state-43053498550-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut13 | registro_visor | publicaciones_visor/canonical_m06 | 2 de 2 con id viejo | 40787900559,43053498550 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| aut14 | composicion_datos | datos/composicion | fichero=region_de_murcia.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| aut14 | electoral_fuente | evidence.electoral_source | recibo=region_de_murcia | ddd-electoral-package-region_de_murcia-2025-40954443883 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut14 | par_fuentes | evidence.prepared_source_pair | par=region_de_murcia | 317d547fe041 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut14 | producto_M06 | evidence.territorial_product | recibo=region_de_murcia | ddd-state-43045426513-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut14 | producto_M08 | evidence.electoral_product | recibo=region_de_murcia | ddd-state-43053208175-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut14 | registro_visor | publicaciones_visor/canonical_m06 | 3 de 3 con id viejo | 40957577850,42504383790,43053208175 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| aut15 | composicion_datos | datos/composicion | fichero=comunidad_foral_de_navarra.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| aut15 | electoral_fuente | evidence.electoral_source | recibo=comunidad_foral_de_navarra | ddd-electoral-package-comunidad_foral_de_navarra-2025-40838170635 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut15 | par_fuentes | evidence.prepared_source_pair | par=comunidad_foral_de_navarra | 4e2ececa3fb0 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut15 | producto_M06 | evidence.territorial_product | recibo=comunidad_foral_de_navarra | ddd-state-43045437345-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut15 | producto_M08 | evidence.electoral_product | recibo=comunidad_foral_de_navarra | ddd-state-43052874017-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut15 | registro_visor | publicaciones_visor/canonical_m06 | 3 de 3 con id viejo | 40847881909,41049986588,43052874017 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| aut16 | composicion_datos | datos/composicion | fichero=pais_vasco.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| aut16 | electoral_fuente | evidence.electoral_source | recibo=pais_vasco | ddd-electoral-package-pais_vasco-2025-43036604667 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut16 | par_fuentes | evidence.prepared_source_pair | par=pais_vasco | 76289209d07c | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut16 | producto_M06 | evidence.territorial_product | recibo=pais_vasco | ddd-state-43041060549-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut16 | producto_M08 | evidence.electoral_product | recibo=pais_vasco | ddd-state-43047232024-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut16 | registro_visor | publicaciones_visor/canonical_m06 | 2 de 2 con id viejo | 40951146225,43047232024 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| aut17 | composicion_datos | datos/composicion | fichero=la_rioja.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| aut17 | electoral_fuente | evidence.electoral_source | recibo=la_rioja | ddd-electoral-package-la_rioja-2025-40850322464 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut17 | par_fuentes | evidence.prepared_source_pair | par=la_rioja | b5a3bc5961e4 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut17 | producto_M06 | evidence.territorial_product | recibo=la_rioja | ddd-state-43003614878-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut17 | producto_M08 | evidence.electoral_product | recibo=la_rioja | ddd-state-43007066596-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut17 | registro_visor | publicaciones_visor/canonical_m06 | 2 de 2 con id viejo | 40867456776,43007066596 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| aut18 | composicion_datos | datos/resultados | fichero=ceuta.csv | — | — | 1/1 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| aut18 | electoral_fuente | evidence.electoral_source | recibo=ceuta | ddd-electoral-package-ceuta-2025-40773443591 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut18 | par_fuentes | evidence.prepared_source_pair | par=ceuta | 43ce033b960a | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut18 | producto_M06 | evidence.territorial_product | recibo=ceuta | ddd-state-43045447315-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut18 | producto_M08 | evidence.electoral_product | recibo=ceuta | ddd-state-43052923691-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut18 | registro_visor | publicaciones_visor/canonical_m06 | 3 de 3 con id viejo | 36272095647,42503542766,43052923691 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| aut19 | composicion_datos | datos/composicion | fichero=melilla.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| aut19 | electoral_fuente | evidence.electoral_source | recibo=melilla | ddd-electoral-package-melilla-2025-40832114779 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut19 | par_fuentes | evidence.prepared_source_pair | par=melilla | f545e3ed494c | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut19 | producto_M06 | evidence.territorial_product | recibo=melilla | ddd-state-43045458268-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut19 | producto_M08 | evidence.electoral_product | recibo=melilla | ddd-state-43051007542-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| aut19 | registro_visor | publicaciones_visor/canonical_m06 | 3 de 3 con id viejo | 40840795932,42504386196,43051007542 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac01 | composicion_datos | datos/composicion | fichero=congreso_alava.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac01 | electoral_fuente | evidence.electoral_source | recibo=congreso_alava | ddd-electoral-package-congreso_alava-2025-41239750223 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac01 | par_fuentes | evidence.prepared_source_pair | par=congreso_alava | 29577f2efcc4 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac01 | producto_M06 | evidence.territorial_product | recibo=congreso_alava | ddd-state-42940320710-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac01 | producto_M08 | evidence.electoral_product | recibo=congreso_alava | ddd-state-42983088643-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac01 | registro_visor | publicaciones_visor/canonical_m06 | 2 de 2 con id viejo | 41346917857,42983088643 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac02 | composicion_datos | datos/composicion | fichero=congreso_albacete.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac02 | electoral_fuente | evidence.electoral_source | recibo=congreso_albacete | ddd-electoral-package-congreso_albacete-2025-41239755540 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac02 | par_fuentes | evidence.prepared_source_pair | par=congreso_albacete | cab052dbdcaf | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac02 | producto_M06 | evidence.territorial_product | recibo=congreso_albacete | ddd-state-42940326013-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac02 | producto_M08 | evidence.electoral_product | recibo=congreso_albacete | ddd-state-42952791883-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac02 | registro_visor | publicaciones_visor/canonical_m06 | 3 de 3 con id viejo | 41294417893,42514994231,42952791883 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac03 | composicion_datos | datos/composicion | fichero=congreso_alicante.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac03 | electoral_fuente | evidence.electoral_source | recibo=congreso_alicante | ddd-electoral-package-congreso_alicante-2025-42463675548 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac03 | par_fuentes | evidence.prepared_source_pair | par=congreso_alicante | f8ffc966848c | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac03 | producto_M06 | evidence.territorial_product | recibo=congreso_alicante | ddd-state-42940331557-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac03 | producto_M08 | evidence.electoral_product | recibo=congreso_alicante | ddd-state-42953235024-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac03 | registro_visor | publicaciones_visor/canonical_m06 | 2 de 2 con id viejo | 42495067503,42940331557 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac04 | composicion_datos | datos/composicion | fichero=congreso_almeria.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac04 | electoral_fuente | evidence.electoral_source | recibo=congreso_almeria | ddd-electoral-package-congreso_almeria-2025-41239766467 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac04 | par_fuentes | evidence.prepared_source_pair | par=congreso_almeria | a94d24b963d4 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac04 | producto_M06 | evidence.territorial_product | recibo=congreso_almeria | ddd-state-42940336572-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac04 | producto_M08 | evidence.electoral_product | recibo=congreso_almeria | ddd-state-42952468083-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac04 | registro_visor | publicaciones_visor/canonical_m06 | 3 de 3 con id viejo | 41295979497,42519378789,42940336572 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac05 | composicion_datos | datos/composicion | fichero=congreso_avila.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac05 | electoral_fuente | evidence.electoral_source | recibo=congreso_avila | ddd-electoral-package-congreso_avila-2025-41235288504 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac05 | par_fuentes | evidence.prepared_source_pair | par=congreso_avila | 0d49207a4ae0 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac05 | producto_M06 | evidence.territorial_product | recibo=congreso_avila | ddd-state-42940341213-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac05 | producto_M08 | evidence.electoral_product | recibo=congreso_avila | ddd-state-42948760863-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac05 | registro_visor | publicaciones_visor/canonical_m06 | 2 de 2 con id viejo | 41241662219,42940341213 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac06 | composicion_datos | datos/composicion | fichero=congreso_badajoz.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac06 | electoral_fuente | evidence.electoral_source | recibo=congreso_badajoz | ddd-electoral-package-congreso_badajoz-2025-41239771818 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac06 | par_fuentes | evidence.prepared_source_pair | par=congreso_badajoz | 5ce0eb79edc0 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac06 | producto_M06 | evidence.territorial_product | recibo=congreso_badajoz | ddd-state-42940345930-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac06 | producto_M08 | evidence.electoral_product | recibo=congreso_badajoz | ddd-state-42949289470-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac06 | registro_visor | publicaciones_visor/canonical_m06 | 3 de 3 con id viejo | 41299475924,42519381013,42940345930 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac07 | composicion_datos | datos/composicion | fichero=congreso_baleares.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac07 | electoral_fuente | evidence.electoral_source | recibo=congreso_baleares | ddd-electoral-package-congreso_baleares-2025-41465837048 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac07 | par_fuentes | evidence.prepared_source_pair | par=congreso_baleares | 61ff422e7d31 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac07 | producto_M06 | evidence.territorial_product | recibo=congreso_baleares | ddd-state-42940350970-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac07 | producto_M08 | evidence.electoral_product | recibo=congreso_baleares | ddd-state-42953068884-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac07 | registro_visor | publicaciones_visor/canonical_m06 | 2 de 2 con id viejo | 41481449507,42940350970 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac08 | composicion_datos | datos/composicion | fichero=congreso_barcelona.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac08 | electoral_fuente | evidence.electoral_source | recibo=congreso_barcelona | ddd-electoral-package-congreso_barcelona-2025-42489980111 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac08 | par_fuentes | evidence.prepared_source_pair | par=congreso_barcelona | b90ce4e74864 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac08 | producto_M06 | evidence.territorial_product | recibo=congreso_barcelona | ddd-state-42940355981-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac08 | producto_M08 | evidence.electoral_product | recibo=congreso_barcelona | ddd-state-42953127263-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac08 | registro_visor | publicaciones_visor/canonical_m06 | 2 de 2 con id viejo | 42495069270,42953127263 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac09 | composicion_datos | datos/composicion | fichero=congreso_burgos.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac09 | electoral_fuente | evidence.electoral_source | recibo=congreso_burgos | ddd-electoral-package-congreso_burgos-2025-41239782586 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac09 | par_fuentes | evidence.prepared_source_pair | par=congreso_burgos | 5175fb880e69 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac09 | producto_M06 | evidence.territorial_product | recibo=congreso_burgos | ddd-state-42981415070-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac09 | producto_M08 | evidence.electoral_product | recibo=congreso_burgos | ddd-state-42986581831-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac09 | registro_visor | publicaciones_visor/canonical_m06 | 2 de 2 con id viejo | 41299221887,42981415070 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac10 | composicion_datos | datos/composicion | fichero=congreso_caceres.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac10 | electoral_fuente | evidence.electoral_source | recibo=congreso_caceres | ddd-electoral-package-congreso_caceres-2025-41239788468 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac10 | par_fuentes | evidence.prepared_source_pair | par=congreso_caceres | f8f3ff6511a1 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac10 | producto_M06 | evidence.territorial_product | recibo=congreso_caceres | ddd-state-42940366579-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac10 | producto_M08 | evidence.electoral_product | recibo=congreso_caceres | ddd-state-42953363103-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac10 | registro_visor | publicaciones_visor/canonical_m06 | 2 de 2 con id viejo | 41294658600,42940366579 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac11 | composicion_datos | datos/composicion | fichero=congreso_cadiz.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac11 | electoral_fuente | evidence.electoral_source | recibo=congreso_cadiz | ddd-electoral-package-congreso_cadiz-2025-41465820761 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac11 | par_fuentes | evidence.prepared_source_pair | par=congreso_cadiz | c61f13ea3804 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac11 | producto_M06 | evidence.territorial_product | recibo=congreso_cadiz | ddd-state-42940371696-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac11 | producto_M08 | evidence.electoral_product | recibo=congreso_cadiz | ddd-state-42953019279-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac11 | registro_visor | publicaciones_visor/canonical_m06 | 2 de 2 con id viejo | 41500124775,42953019279 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac12 | composicion_datos | datos/composicion | fichero=congreso_castellon.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac12 | electoral_fuente | evidence.electoral_source | recibo=congreso_castellon | ddd-electoral-package-congreso_castellon-2025-41239799217 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac12 | par_fuentes | evidence.prepared_source_pair | par=congreso_castellon | 8bbe77deb9c9 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac12 | producto_M06 | evidence.territorial_product | recibo=congreso_castellon | ddd-state-42940377493-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac12 | producto_M08 | evidence.electoral_product | recibo=congreso_castellon | ddd-state-42953757677-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac12 | registro_visor | publicaciones_visor/canonical_m06 | 2 de 2 con id viejo | 41295629673,42940377493 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac13 | composicion_datos | datos/composicion | fichero=congreso_ciudad_real.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac13 | electoral_fuente | evidence.electoral_source | recibo=congreso_ciudad_real | ddd-electoral-package-congreso_ciudad_real-2025-41239804426 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac13 | par_fuentes | evidence.prepared_source_pair | par=congreso_ciudad_real | 8f01feca87df | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac13 | producto_M06 | evidence.territorial_product | recibo=congreso_ciudad_real | ddd-state-42940382446-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac13 | producto_M08 | evidence.electoral_product | recibo=congreso_ciudad_real | ddd-state-42954776957-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac13 | registro_visor | publicaciones_visor/canonical_m06 | 2 de 2 con id viejo | 41298749455,42940382446 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac14 | composicion_datos | datos/composicion | fichero=congreso_cordoba.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac14 | electoral_fuente | evidence.electoral_source | recibo=congreso_cordoba | ddd-electoral-package-congreso_cordoba-2025-41239809492 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac14 | par_fuentes | evidence.prepared_source_pair | par=congreso_cordoba | 96d55857b5d5 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac14 | producto_M06 | evidence.territorial_product | recibo=congreso_cordoba | ddd-state-42940387433-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac14 | producto_M08 | evidence.electoral_product | recibo=congreso_cordoba | ddd-state-42953300723-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac14 | registro_visor | publicaciones_visor/canonical_m06 | 2 de 2 con id viejo | 41296161083,42940387433 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac15 | composicion_datos | datos/composicion | fichero=congreso_la_coruna.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac15 | electoral_fuente | evidence.electoral_source | recibo=congreso_la_coruna | ddd-electoral-package-congreso_la_coruna-2025-41239814650 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac15 | par_fuentes | evidence.prepared_source_pair | par=congreso_la_coruna | 0edcee83874a | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac15 | producto_M06 | evidence.territorial_product | recibo=congreso_la_coruna | ddd-state-42940392520-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac15 | producto_M08 | evidence.electoral_product | recibo=congreso_la_coruna | ddd-state-42953518518-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac15 | registro_visor | publicaciones_visor/canonical_m06 | 2 de 2 con id viejo | 41296991598,42940392520 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac16 | composicion_datos | datos/composicion | fichero=congreso_cuenca.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac16 | electoral_fuente | evidence.electoral_source | recibo=congreso_cuenca | ddd-electoral-package-congreso_cuenca-2025-41236657374 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac16 | par_fuentes | evidence.prepared_source_pair | par=congreso_cuenca | 26ab70d72f02 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac16 | producto_M06 | evidence.territorial_product | recibo=congreso_cuenca | ddd-state-42940397668-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac16 | producto_M08 | evidence.electoral_product | recibo=congreso_cuenca | ddd-state-42954007732-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac16 | registro_visor | publicaciones_visor/canonical_m06 | 2 de 2 con id viejo | 41294075778,42940397668 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac17 | composicion_datos | datos/composicion | fichero=congreso_gerona.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac17 | electoral_fuente | evidence.electoral_source | recibo=congreso_gerona | ddd-electoral-package-congreso_gerona-2025-41239820081 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac17 | par_fuentes | evidence.prepared_source_pair | par=congreso_gerona | 9c4dfa40bc7d | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac17 | producto_M06 | evidence.territorial_product | recibo=congreso_gerona | ddd-state-42940402050-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac17 | producto_M08 | evidence.electoral_product | recibo=congreso_gerona | ddd-state-42954957703-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac17 | registro_visor | publicaciones_visor/canonical_m06 | 2 de 2 con id viejo | 41298839274,42940402050 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac18 | composicion_datos | datos/composicion | fichero=congreso_granada.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac18 | electoral_fuente | evidence.electoral_source | recibo=congreso_granada | ddd-electoral-package-congreso_granada-2025-41239825488 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac18 | par_fuentes | evidence.prepared_source_pair | par=congreso_granada | 94c196621c8f | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac18 | producto_M06 | evidence.territorial_product | recibo=congreso_granada | ddd-state-42940407337-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac18 | producto_M08 | evidence.electoral_product | recibo=congreso_granada | ddd-state-42954091088-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac18 | registro_visor | publicaciones_visor/canonical_m06 | 2 de 2 con id viejo | 41296546816,42940407337 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac19 | composicion_datos | datos/composicion | fichero=congreso_guadalajara.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac19 | electoral_fuente | evidence.electoral_source | recibo=congreso_guadalajara | ddd-electoral-package-congreso_guadalajara-2025-41236827273 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac19 | par_fuentes | evidence.prepared_source_pair | par=congreso_guadalajara | 8e2ca58bb58c | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac19 | producto_M06 | evidence.territorial_product | recibo=congreso_guadalajara | ddd-state-42940412378-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac19 | producto_M08 | evidence.electoral_product | recibo=congreso_guadalajara | ddd-state-42955217289-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac19 | registro_visor | publicaciones_visor/canonical_m06 | 2 de 2 con id viejo | 41294169221,42940412378 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac20 | composicion_datos | datos/composicion | fichero=congreso_guipuzcoa.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac20 | electoral_fuente | evidence.electoral_source | recibo=congreso_guipuzcoa | ddd-electoral-package-congreso_guipuzcoa-2025-41239830502 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac20 | par_fuentes | evidence.prepared_source_pair | par=congreso_guipuzcoa | 9651126a3a22 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac20 | producto_M06 | evidence.territorial_product | recibo=congreso_guipuzcoa | ddd-state-42940417361-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac20 | producto_M08 | evidence.electoral_product | recibo=congreso_guipuzcoa | ddd-state-42955375065-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac20 | registro_visor | publicaciones_visor/canonical_m06 | 2 de 2 con id viejo | 41298935355,42940417361 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac21 | composicion_datos | datos/composicion | fichero=congreso_huelva.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac21 | electoral_fuente | evidence.electoral_source | recibo=congreso_huelva | ddd-electoral-package-congreso_huelva-2025-41239835955 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac21 | par_fuentes | evidence.prepared_source_pair | par=congreso_huelva | bf33d2ba8fd2 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac21 | producto_M06 | evidence.territorial_product | recibo=congreso_huelva | ddd-state-42991542477-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac21 | producto_M08 | evidence.electoral_product | recibo=congreso_huelva | ddd-state-42996002594-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac21 | registro_visor | publicaciones_visor/canonical_m06 | 2 de 2 con id viejo | 41335929678,42991542477 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac22 | composicion_datos | datos/composicion | fichero=congreso_huesca.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac22 | electoral_fuente | evidence.electoral_source | recibo=congreso_huesca | ddd-electoral-package-congreso_huesca-2025-41194293941 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac22 | par_fuentes | evidence.prepared_source_pair | par=congreso_huesca | e279142c8642 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac22 | producto_M06 | evidence.territorial_product | recibo=congreso_huesca | ddd-state-42991551418-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac22 | producto_M08 | evidence.electoral_product | recibo=congreso_huesca | ddd-state-42996217596-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac22 | registro_visor | publicaciones_visor/canonical_m06 | 3 de 3 con id viejo | 41194447427,42519383275,42991551418 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac23 | composicion_datos | datos/composicion | fichero=congreso_jaen.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac23 | electoral_fuente | evidence.electoral_source | recibo=congreso_jaen | ddd-electoral-package-congreso_jaen-2025-41239841417 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac23 | par_fuentes | evidence.prepared_source_pair | par=congreso_jaen | 6a04a5cdb0ca | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac23 | producto_M06 | evidence.territorial_product | recibo=congreso_jaen | ddd-state-42940432935-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac23 | producto_M08 | evidence.electoral_product | recibo=congreso_jaen | ddd-state-42955644352-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac23 | registro_visor | publicaciones_visor/canonical_m06 | 2 de 2 con id viejo | 41295799269,42955644352 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac24 | composicion_datos | datos/composicion | fichero=congreso_leon.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac24 | electoral_fuente | evidence.electoral_source | recibo=congreso_leon | ddd-electoral-package-congreso_leon-2025-41239847787 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac24 | par_fuentes | evidence.prepared_source_pair | par=congreso_leon | ec2b27c201a1 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac24 | producto_M06 | evidence.territorial_product | recibo=congreso_leon | ddd-state-42991571678-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac24 | producto_M08 | evidence.electoral_product | recibo=congreso_leon | ddd-state-42996717873-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac24 | registro_visor | publicaciones_visor/canonical_m06 | 3 de 3 con id viejo | 41295452035,41629735636,42991571678 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac25 | composicion_datos | datos/composicion | fichero=congreso_lerida.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac25 | electoral_fuente | evidence.electoral_source | recibo=congreso_lerida | ddd-electoral-package-congreso_lerida-2025-41239853848 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac25 | par_fuentes | evidence.prepared_source_pair | par=congreso_lerida | ce3113b33666 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac25 | producto_M06 | evidence.territorial_product | recibo=congreso_lerida | ddd-state-43059014993-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac25 | producto_M08 | evidence.electoral_product | recibo=congreso_lerida | ddd-state-43064129984-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac25 | registro_visor | publicaciones_visor/canonical_m06 | 2 de 2 con id viejo | 41299033915,43064129984 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac26 | composicion_datos | datos/composicion | fichero=congreso_la_rioja.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac26 | electoral_fuente | evidence.electoral_source | recibo=congreso_la_rioja | ddd-electoral-package-congreso_la_rioja-2025-41239859752 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac26 | par_fuentes | evidence.prepared_source_pair | par=congreso_la_rioja | d7f15db5d446 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac26 | producto_M06 | evidence.territorial_product | recibo=congreso_la_rioja | ddd-state-42932144515-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac26 | producto_M08 | evidence.electoral_product | recibo=congreso_la_rioja | ddd-state-42935762636-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac26 | registro_visor | publicaciones_visor/canonical_m06 | 3 de 3 con id viejo | 41294822309,42504388624,42932144515 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac27 | composicion_datos | datos/composicion | fichero=congreso_lugo.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac27 | electoral_fuente | evidence.electoral_source | recibo=congreso_lugo | ddd-electoral-package-congreso_lugo-2025-41239865976 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac27 | par_fuentes | evidence.prepared_source_pair | par=congreso_lugo | e4e97c5fbb0e | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac27 | producto_M06 | evidence.territorial_product | recibo=congreso_lugo | ddd-state-42991580539-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac27 | producto_M08 | evidence.electoral_product | recibo=congreso_lugo | ddd-state-42995722473-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac27 | registro_visor | publicaciones_visor/canonical_m06 | 3 de 3 con id viejo | 41294985244,42514986960,42991580539 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac28 | composicion_datos | datos/composicion | fichero=congreso_madrid.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac28 | electoral_fuente | evidence.electoral_source | recibo=congreso_madrid | ddd-electoral-package-congreso_madrid-2025-41611821388 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac28 | par_fuentes | evidence.prepared_source_pair | par=congreso_madrid | 5772cae5b6ab | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac28 | producto_M06 | evidence.territorial_product | recibo=congreso_madrid | ddd-state-43001749134-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac28 | producto_M08 | evidence.electoral_product | recibo=congreso_madrid | ddd-state-43006307734-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac28 | registro_visor | publicaciones_visor/canonical_m06 | 2 de 2 con id viejo | 41622703086,43001749134 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac29 | composicion_datos | datos/composicion | fichero=congreso_malaga.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac29 | electoral_fuente | evidence.electoral_source | recibo=congreso_malaga | ddd-electoral-package-congreso_malaga-2025-42489981909 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac29 | par_fuentes | evidence.prepared_source_pair | par=congreso_malaga | 118cccdb9a9a | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac29 | producto_M06 | evidence.territorial_product | recibo=congreso_malaga | ddd-state-43001775134-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac29 | producto_M08 | evidence.electoral_product | recibo=congreso_malaga | ddd-state-43006442219-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac29 | registro_visor | publicaciones_visor/canonical_m06 | 2 de 2 con id viejo | 42495070976,43001775134 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac30 | composicion_datos | datos/composicion | fichero=congreso_murcia.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac30 | electoral_fuente | evidence.electoral_source | recibo=congreso_murcia | ddd-electoral-package-congreso_murcia-2025-41613691816 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac30 | par_fuentes | evidence.prepared_source_pair | par=congreso_murcia | ed71f8585afa | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac30 | producto_M06 | evidence.territorial_product | recibo=congreso_murcia | ddd-state-43001766635-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac30 | producto_M08 | evidence.electoral_product | recibo=congreso_murcia | ddd-state-43005676593-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac30 | registro_visor | publicaciones_visor/canonical_m06 | 2 de 2 con id viejo | 41622862185,43001766635 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac31 | composicion_datos | datos/composicion | fichero=congreso_navarra.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac31 | electoral_fuente | evidence.electoral_source | recibo=congreso_navarra | ddd-electoral-package-congreso_navarra-2025-41239887617 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac31 | par_fuentes | evidence.prepared_source_pair | par=congreso_navarra | a84c449cfcfd | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac31 | producto_M06 | evidence.territorial_product | recibo=congreso_navarra | ddd-state-43001785293-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac31 | producto_M08 | evidence.electoral_product | recibo=congreso_navarra | ddd-state-43006653960-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac31 | registro_visor | publicaciones_visor/canonical_m06 | 2 de 2 con id viejo | 41299128213,43001785293 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac32 | composicion_datos | datos/composicion | fichero=congreso_orense.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac32 | electoral_fuente | evidence.electoral_source | recibo=congreso_orense | ddd-electoral-package-congreso_orense-2025-41239892753 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac32 | par_fuentes | evidence.prepared_source_pair | par=congreso_orense | 69a968f6d481 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac32 | producto_M06 | evidence.territorial_product | recibo=congreso_orense | ddd-state-43012119307-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac32 | producto_M08 | evidence.electoral_product | recibo=congreso_orense | ddd-state-43016113065-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac32 | registro_visor | publicaciones_visor/canonical_m06 | 2 de 2 con id viejo | 41295142111,43012119307 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac33 | composicion_datos | datos/composicion | fichero=congreso_asturias.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac33 | electoral_fuente | evidence.electoral_source | recibo=congreso_asturias | ddd-electoral-package-congreso_asturias-2025-41239897911 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac33 | par_fuentes | evidence.prepared_source_pair | par=congreso_asturias | c37c091cfaa3 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac33 | producto_M06 | evidence.territorial_product | recibo=congreso_asturias | ddd-state-42981406489-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac33 | producto_M08 | evidence.electoral_product | recibo=congreso_asturias | ddd-state-42985447971-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac33 | registro_visor | publicaciones_visor/canonical_m06 | 2 de 2 con id viejo | 41296638877,42981406489 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac34 | composicion_datos | datos/composicion | fichero=congreso_palencia.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac34 | electoral_fuente | evidence.electoral_source | recibo=congreso_palencia | ddd-electoral-package-congreso_palencia-2025-41235462609 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac34 | par_fuentes | evidence.prepared_source_pair | par=congreso_palencia | 001c856efe99 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac34 | producto_M06 | evidence.territorial_product | recibo=congreso_palencia | ddd-state-43012127687-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac34 | producto_M08 | evidence.electoral_product | recibo=congreso_palencia | ddd-state-43016085888-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac34 | registro_visor | publicaciones_visor/canonical_m06 | 2 de 2 con id viejo | 41298660623,43012127687 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac35 | composicion_datos | datos/composicion | fichero=congreso_las_palmas.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac35 | electoral_fuente | evidence.electoral_source | recibo=congreso_las_palmas | ddd-electoral-package-congreso_las_palmas-2025-41432561787 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac35 | par_fuentes | evidence.prepared_source_pair | par=congreso_las_palmas | a3f2cf94231c | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac35 | producto_M06 | evidence.territorial_product | recibo=congreso_las_palmas | ddd-state-42991561887-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac35 | producto_M08 | evidence.electoral_product | recibo=congreso_las_palmas | ddd-state-42998268332-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac35 | registro_visor | publicaciones_visor/canonical_m06 | 2 de 2 con id viejo | 41442913288,42991561887 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac36 | composicion_datos | datos/composicion | fichero=congreso_pontevedra.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac36 | electoral_fuente | evidence.electoral_source | recibo=congreso_pontevedra | ddd-electoral-package-congreso_pontevedra-2025-41239903028 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac36 | par_fuentes | evidence.prepared_source_pair | par=congreso_pontevedra | da60eabd85ab | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac36 | producto_M06 | evidence.territorial_product | recibo=congreso_pontevedra | ddd-state-43012135258-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac36 | producto_M08 | evidence.electoral_product | recibo=congreso_pontevedra | ddd-state-43016524347-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac36 | registro_visor | publicaciones_visor/canonical_m06 | 2 de 2 con id viejo | 41353894475,43012135258 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac37 | composicion_datos | datos/composicion | fichero=congreso_salamanca.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac37 | electoral_fuente | evidence.electoral_source | recibo=congreso_salamanca | ddd-electoral-package-congreso_salamanca-2025-41239908359 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac37 | par_fuentes | evidence.prepared_source_pair | par=congreso_salamanca | a3f54f25701e | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac37 | producto_M06 | evidence.territorial_product | recibo=congreso_salamanca | ddd-state-43012143922-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac37 | producto_M08 | evidence.electoral_product | recibo=congreso_salamanca | ddd-state-43017179163-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac37 | registro_visor | publicaciones_visor/canonical_m06 | 2 de 2 con id viejo | 41295298674,43012143922 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac38 | composicion_datos | datos/composicion | fichero=congreso_santa_cruz_de_tenerife.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac38 | electoral_fuente | evidence.electoral_source | recibo=congreso_santa_cruz_de_tenerife | ddd-electoral-package-congreso_santa_cruz_de_tenerife-2025-41239515252 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac38 | par_fuentes | evidence.prepared_source_pair | par=congreso_santa_cruz_de_tenerife | 281ded9a6026 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac38 | producto_M06 | evidence.territorial_product | recibo=congreso_santa_cruz_de_tenerife | ddd-state-43012151677-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac38 | producto_M08 | evidence.electoral_product | recibo=congreso_santa_cruz_de_tenerife | ddd-state-43020203637-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac38 | registro_visor | publicaciones_visor/canonical_m06 | 3 de 3 con id viejo | 41294259017,42519017008,43012151677 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac39 | composicion_datos | datos/composicion | fichero=congreso_cantabria.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac39 | electoral_fuente | evidence.electoral_source | recibo=congreso_cantabria | ddd-electoral-package-congreso_cantabria-2025-41239913823 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac39 | par_fuentes | evidence.prepared_source_pair | par=congreso_cantabria | 158e44483cc2 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac39 | producto_M06 | evidence.territorial_product | recibo=congreso_cantabria | ddd-state-42981422592-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac39 | producto_M08 | evidence.electoral_product | recibo=congreso_cantabria | ddd-state-42985965354-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac39 | registro_visor | publicaciones_visor/canonical_m06 | 2 de 2 con id viejo | 41356175674,42981422592 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac40 | composicion_datos | datos/composicion | fichero=congreso_segovia.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac40 | electoral_fuente | evidence.electoral_source | recibo=congreso_segovia | ddd-electoral-package-congreso_segovia-2025-41235628457 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac40 | par_fuentes | evidence.prepared_source_pair | par=congreso_segovia | 11f94d349540 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac40 | producto_M06 | evidence.territorial_product | recibo=congreso_segovia | ddd-state-43024836898-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac40 | producto_M08 | evidence.electoral_product | recibo=congreso_segovia | ddd-state-43029353804-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac40 | registro_visor | publicaciones_visor/canonical_m06 | 2 de 2 con id viejo | 41241846017,43029353804 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac41 | composicion_datos | datos/composicion | fichero=congreso_sevilla.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac41 | electoral_fuente | evidence.electoral_source | recibo=congreso_sevilla | ddd-electoral-package-congreso_sevilla-2025-41239919571 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac41 | par_fuentes | evidence.prepared_source_pair | par=congreso_sevilla | cb79f6e4011e | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac41 | producto_M06 | evidence.territorial_product | recibo=congreso_sevilla | ddd-state-43024845069-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac41 | producto_M08 | evidence.electoral_product | recibo=congreso_sevilla | ddd-state-43029566265-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac41 | registro_visor | publicaciones_visor/canonical_m06 | 2 de 2 con id viejo | 41297168461,43029566265 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac42 | composicion_datos | datos/composicion | fichero=congreso_soria.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac42 | electoral_fuente | evidence.electoral_source | recibo=congreso_soria | ddd-electoral-package-congreso_soria-2025-41235804865 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac42 | par_fuentes | evidence.prepared_source_pair | par=congreso_soria | b73e7070cb80 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac42 | producto_M06 | evidence.territorial_product | recibo=congreso_soria | ddd-state-43024852774-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac42 | producto_M08 | evidence.electoral_product | recibo=congreso_soria | ddd-state-43029280043-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac42 | registro_visor | publicaciones_visor/canonical_m06 | 2 de 2 con id viejo | 41250310066,43029280043 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac43 | composicion_datos | datos/composicion | fichero=congreso_tarragona.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac43 | electoral_fuente | evidence.electoral_source | recibo=congreso_tarragona | ddd-electoral-package-congreso_tarragona-2025-41239925359 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac43 | par_fuentes | evidence.prepared_source_pair | par=congreso_tarragona | 40740f8c1f08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac43 | producto_M06 | evidence.territorial_product | recibo=congreso_tarragona | ddd-state-43024860841-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac43 | producto_M08 | evidence.electoral_product | recibo=congreso_tarragona | ddd-state-43029795470-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac43 | registro_visor | publicaciones_visor/canonical_m06 | 3 de 3 con id viejo | 41296449975,42514991952,43029795470 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac44 | composicion_datos | datos/composicion | fichero=congreso_teruel.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac44 | electoral_fuente | evidence.electoral_source | recibo=congreso_teruel | ddd-electoral-package-congreso_teruel-2025-41235977145 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac44 | par_fuentes | evidence.prepared_source_pair | par=congreso_teruel | cae6a511035d | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac44 | producto_M06 | evidence.territorial_product | recibo=congreso_teruel | ddd-state-43024869107-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac44 | producto_M08 | evidence.electoral_product | recibo=congreso_teruel | ddd-state-43029189395-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac44 | registro_visor | publicaciones_visor/canonical_m06 | 2 de 2 con id viejo | 41250394074,43029189395 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac45 | composicion_datos | datos/composicion | fichero=congreso_toledo.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac45 | electoral_fuente | evidence.electoral_source | recibo=congreso_toledo | ddd-electoral-package-congreso_toledo-2025-41239931236 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac45 | par_fuentes | evidence.prepared_source_pair | par=congreso_toledo | 044bfae7409d | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac45 | producto_M06 | evidence.territorial_product | recibo=congreso_toledo | ddd-state-43034928684-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac45 | producto_M08 | evidence.electoral_product | recibo=congreso_toledo | ddd-state-43040968638-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac45 | registro_visor | publicaciones_visor/canonical_m06 | 2 de 2 con id viejo | 41296268720,43040968638 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac46 | composicion_datos | datos/composicion | fichero=congreso_valencia.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac46 | electoral_fuente | evidence.electoral_source | recibo=congreso_valencia | ddd-electoral-package-congreso_valencia-2025-41239936932 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac46 | par_fuentes | evidence.prepared_source_pair | par=congreso_valencia | 1f1c1081dd78 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac46 | producto_M06 | evidence.territorial_product | recibo=congreso_valencia | ddd-state-43034939625-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac46 | producto_M08 | evidence.electoral_product | recibo=congreso_valencia | ddd-state-43041144007-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac46 | registro_visor | publicaciones_visor/canonical_m06 | 3 de 3 con id viejo | 41335936727,42525625044,43041144007 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac47 | composicion_datos | datos/composicion | fichero=congreso_valladolid.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac47 | electoral_fuente | evidence.electoral_source | recibo=congreso_valladolid | ddd-electoral-package-congreso_valladolid-2025-41239942087 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac47 | par_fuentes | evidence.prepared_source_pair | par=congreso_valladolid | 7c5b5b5ecaec | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac47 | producto_M06 | evidence.territorial_product | recibo=congreso_valladolid | ddd-state-43034949749-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac47 | producto_M08 | evidence.electoral_product | recibo=congreso_valladolid | ddd-state-43040794081-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac47 | registro_visor | publicaciones_visor/canonical_m06 | 2 de 2 con id viejo | 41299313598,43040794081 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac48 | composicion_datos | datos/composicion | fichero=congreso_vizcaya.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac48 | electoral_fuente | evidence.electoral_source | recibo=congreso_vizcaya | ddd-electoral-package-congreso_vizcaya-2025-41239947749 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac48 | par_fuentes | evidence.prepared_source_pair | par=congreso_vizcaya | a00b60911ff3 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac48 | producto_M06 | evidence.territorial_product | recibo=congreso_vizcaya | ddd-state-43034959389-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac48 | producto_M08 | evidence.electoral_product | recibo=congreso_vizcaya | ddd-state-43040430397-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac48 | registro_visor | publicaciones_visor/canonical_m06 | 2 de 2 con id viejo | 41356074013,43040430397 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac49 | composicion_datos | datos/composicion | fichero=congreso_zamora.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac49 | electoral_fuente | evidence.electoral_source | recibo=congreso_zamora | ddd-electoral-package-congreso_zamora-2025-41236149824 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac49 | par_fuentes | evidence.prepared_source_pair | par=congreso_zamora | 9456a3656fd9 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac49 | producto_M06 | evidence.territorial_product | recibo=congreso_zamora | ddd-state-43034969907-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac49 | producto_M08 | evidence.electoral_product | recibo=congreso_zamora | ddd-state-43040878307-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac49 | registro_visor | publicaciones_visor/canonical_m06 | 2 de 2 con id viejo | 41250479211,43040878307 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac50 | composicion_datos | datos/composicion | fichero=congreso_zaragoza.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac50 | electoral_fuente | evidence.electoral_source | recibo=congreso_zaragoza | ddd-electoral-package-congreso_zaragoza-2025-41239953681 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac50 | par_fuentes | evidence.prepared_source_pair | par=congreso_zaragoza | 1c7a2bca1765 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac50 | producto_M06 | evidence.territorial_product | recibo=congreso_zaragoza | ddd-state-43034979460-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac50 | producto_M08 | evidence.electoral_product | recibo=congreso_zaragoza | ddd-state-43041544479-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac50 | registro_visor | publicaciones_visor/canonical_m06 | 2 de 2 con id viejo | 41296815536,43041544479 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac51 | composicion_datos | datos/composicion | fichero=congreso_ceuta.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac51 | electoral_fuente | evidence.electoral_source | recibo=congreso_ceuta | ddd-electoral-package-congreso_ceuta-2025-42488846588 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac51 | par_fuentes | evidence.prepared_source_pair | par=congreso_ceuta | 5b85f3875068 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac51 | producto_M06 | evidence.territorial_product | recibo=congreso_ceuta | ddd-state-42981430591-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac51 | producto_M08 | evidence.electoral_product | recibo=congreso_ceuta | ddd-state-42985728070-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac51 | registro_visor | publicaciones_visor/canonical_m06 | 2 de 2 con id viejo | 41250564472,42981430591 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac52 | composicion_datos | datos/composicion | fichero=congreso_melilla.csv | — | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |
| nac52 | electoral_fuente | evidence.electoral_source | recibo=congreso_melilla | ddd-electoral-package-congreso_melilla-2025-41236491113 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac52 | par_fuentes | evidence.prepared_source_pair | par=congreso_melilla | c9abeb289e80 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac52 | producto_M06 | evidence.territorial_product | recibo=congreso_melilla | ddd-state-43001757563-M06 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac52 | producto_M08 | evidence.electoral_product | recibo=congreso_melilla | ddd-state-43006105644-M08 | — | 1/1 | RECHAZA → ACQUIRE/prepara de nuevo |
| nac52 | registro_visor | publicaciones_visor/canonical_m06 | 2 de 2 con id viejo | 41293988485,43001757563 | — | 2/2 | SOLO LECTURA de lo publicado (no se reutiliza en la cadena) |

## No verificable desde el repo

Artefactos de Actions (ddd-source-package-*, ddd-electoral-package-*, ddd-state-<run>-M0x): solo el nombre y el digest están en el repo. Comprobar vigencia con: gh api repos/<repo>/actions/runs/<run>/artifacts --jq '.artifacts[]|{name,expired,digest}'
