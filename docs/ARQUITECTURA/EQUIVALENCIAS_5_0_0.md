# Equivalencias viejo → nuevo del corte 5.0.0 (T-198)

GENERADO por `python tests/generar_equivalencias_5_0_0.py`; no editar a mano (lo comprueba
`tests/test_corte_5_0_0_equivalencias.py`). Fuente de los ids: `configuracion/notacion_territorial.csv` y el
catálogo; el resto, `docs/ARQUITECTURA/CORTE_5_0_0.md` §a-c. Ids nuevos en minúsculas (DECISIÓN 5, pendiente).

Nota: el test de entorno `produccion` (`tests/test_corte_5_0_0_equivalencias.py`) cubre solo la 05 y la 06.

Separadores (T-215, aceptado por el Planificador): « — » en los nombres de flujo con botón manual (lo exige
`test_all_manually_dispatchable_workflow_names_are_free_of_middle_dot`); «·» solo en territorios (`NAC01 · Álava`),
en «Interno ·» y en los run-name. Desviación declarada: el job `archivar_r2` sigue en «Automático — Mantenimiento»;
su traslado a ARC, después del corte.

## Módulos → fases

| Viejo | Nuevo |
|---|---|
| M01 `01_preparar_base_territorial.py` | P21 población y secciones + P22 geometría |
| M02 `02_construir_adyacencias.py` | P23 grafo de vecindad |
| M03 `03_construir_grafo.py` | P23 grafo de vecindad |
| M04 `04_generar_semillas.py` | P32 generación (punto de partida) |
| M05 `05_optimizar_distritos.py` | P32 generación (competidor canónico) |
| M06 `06_consolidar_distritos.py` | P34 certificación |
| M07 `07_agregar_resultados_electorales.py` | P41 votos a secciones + P42 agregación |
| M08 `08_integrar_resultados.py` | P42 agregación + P43 validación |

## Flujos de trabajo → flujo v5

| Fichero | Nombre anterior | Flujo v5 | Nombre visible v5 |
|---|---|---|---|
| `gestor-campanas.yml` | 0 Gestor de Campañas | P00 Campaña | P00 Campaña — Gestor |
| `ejecucion-completa-proyecto.yml` | 00 Ejecución Completa del Proyecto | P00 Campaña | P00 Campaña |
| `activacion-por-eleccion.yml` | Auxiliar — Activación por Elección | P00 Campaña | P00 Campaña — Elección |
| `preparacion-legislatura-vigente.yml` | Auxiliar — Activación de Legislatura Vigente | P00 Campaña | P00 Campaña — Legislatura |
| `preparacion-fuentes.yml` | 01 Preparación de Datos Territoriales | P10 Fuentes | P10 Fuentes — P11 Territoriales |
| `preparacion-resultados-electorales.yml` | 03 Preparación de Resultados Electorales | P10 Fuentes | P10 Fuentes — P12 Electorales |
| `produccion-distritos.yml` | 02 Generación de Distritos Autonómicos | P20 Base territorial + P30 Distritos | P20 Base territorial — P30 Distritos |
| `generar-alternativas-territoriales.yml` | 06 Escenarios y Ensembles | P30 Distritos (P33) | P30 Distritos — P33 Alternativas |
| `incorporacion-resultados-electorales.yml` | 04 Incorporación de Resultados Electorales | P40 Resultados electorales | P40 Resultados electorales |
| `desplegar-visor-publico.yml` | 05 Publicación del Visor | P50 Publicación | P50 Publicación |
| `cadena-publicacion.yml` | 05 Cadena de Publicación | P50 Publicación | P50 Publicación — Cadena |
| `publicar-version-mapa.yml` | Publicar versión de mapa | P60 Publicación académica | P60 Publicación académica |
| `podar-r2.yml` | Auxiliar — Poda de R2 | ARC Archivo | ARC Archivo — Poda de R2 |
| `recuperar-producto-electoral-durable.yml` | Recuperar producto electoral durable | ARC Archivo | ARC Archivo — Recuperar producto electoral |

## Productos

| Hoy | v5 |
|---|---|
| M06, `kind=canonical_m06` | Mapa certificado, `kind=mapa_certificado` |
| M08, `kind=canonical_m08` | Resultados por distrito, `kind=resultados_distrito` |
| `kind=static` | `kind=estatico` |
| `kind=ensemble` | `kind=alternativas` |
| id `m06-<id>-<run>` | `mapa-<id5>-<run>` |
| id `m08-<id>-<run>` | `resultados-<id5>-<run>` |
| id `static-<id>` | `estatico-<id5>` |

## Territorios (71 ids AUT/NAC)

| Código | Nombre | id viejo | id nuevo |
|---|---|---|---|
| AUT01 | Andalucía | `andalucia` | `aut01` |
| AUT02 | Aragón | `aragon` | `aut02` |
| AUT03 | Principado de Asturias | `principado_de_asturias` | `aut03` |
| AUT04 | Islas Baleares | `illes_balears` | `aut04` |
| AUT05 | Canarias | `canarias` | `aut05` |
| AUT06 | Cantabria | `cantabria` | `aut06` |
| AUT07 | Castilla y León | `castilla_y_leon` | `aut07` |
| AUT08 | Castilla-La Mancha | `castilla_la_mancha` | `aut08` |
| AUT09 | Cataluña | `cataluna` | `aut09` |
| AUT10 | Comunidad Valenciana | `comunidad_valenciana` | `aut10` |
| AUT11 | Extremadura | `extremadura` | `aut11` |
| AUT12 | Galicia | `galicia` | `aut12` |
| AUT13 | Comunidad de Madrid | `madrid` | `aut13` |
| AUT14 | Región de Murcia | `region_de_murcia` | `aut14` |
| AUT15 | Comunidad Foral de Navarra | `comunidad_foral_de_navarra` | `aut15` |
| AUT16 | País Vasco | `pais_vasco` | `aut16` |
| AUT17 | La Rioja | `la_rioja` | `aut17` |
| AUT18 | Ceuta | `ceuta` | `aut18` |
| AUT19 | Melilla | `melilla` | `aut19` |
| NAC01 | Álava | `congreso_alava` | `nac01` |
| NAC02 | Albacete | `congreso_albacete` | `nac02` |
| NAC03 | Alicante | `congreso_alicante` | `nac03` |
| NAC04 | Almería | `congreso_almeria` | `nac04` |
| NAC05 | Ávila | `congreso_avila` | `nac05` |
| NAC06 | Badajoz | `congreso_badajoz` | `nac06` |
| NAC07 | Baleares | `congreso_baleares` | `nac07` |
| NAC08 | Barcelona | `congreso_barcelona` | `nac08` |
| NAC09 | Burgos | `congreso_burgos` | `nac09` |
| NAC10 | Cáceres | `congreso_caceres` | `nac10` |
| NAC11 | Cádiz | `congreso_cadiz` | `nac11` |
| NAC12 | Castellón | `congreso_castellon` | `nac12` |
| NAC13 | Ciudad Real | `congreso_ciudad_real` | `nac13` |
| NAC14 | Córdoba | `congreso_cordoba` | `nac14` |
| NAC15 | La Coruña | `congreso_la_coruna` | `nac15` |
| NAC16 | Cuenca | `congreso_cuenca` | `nac16` |
| NAC17 | Gerona | `congreso_gerona` | `nac17` |
| NAC18 | Granada | `congreso_granada` | `nac18` |
| NAC19 | Guadalajara | `congreso_guadalajara` | `nac19` |
| NAC20 | Guipúzcoa | `congreso_guipuzcoa` | `nac20` |
| NAC21 | Huelva | `congreso_huelva` | `nac21` |
| NAC22 | Huesca | `congreso_huesca` | `nac22` |
| NAC23 | Jaén | `congreso_jaen` | `nac23` |
| NAC24 | León | `congreso_leon` | `nac24` |
| NAC25 | Lérida | `congreso_lerida` | `nac25` |
| NAC26 | La Rioja | `congreso_la_rioja` | `nac26` |
| NAC27 | Lugo | `congreso_lugo` | `nac27` |
| NAC28 | Madrid | `congreso_madrid` | `nac28` |
| NAC29 | Málaga | `congreso_malaga` | `nac29` |
| NAC30 | Murcia | `congreso_murcia` | `nac30` |
| NAC31 | Navarra | `congreso_navarra` | `nac31` |
| NAC32 | Orense | `congreso_orense` | `nac32` |
| NAC33 | Asturias | `congreso_asturias` | `nac33` |
| NAC34 | Palencia | `congreso_palencia` | `nac34` |
| NAC35 | Las Palmas | `congreso_las_palmas` | `nac35` |
| NAC36 | Pontevedra | `congreso_pontevedra` | `nac36` |
| NAC37 | Salamanca | `congreso_salamanca` | `nac37` |
| NAC38 | Santa Cruz de Tenerife | `congreso_santa_cruz_de_tenerife` | `nac38` |
| NAC39 | Cantabria | `congreso_cantabria` | `nac39` |
| NAC40 | Segovia | `congreso_segovia` | `nac40` |
| NAC41 | Sevilla | `congreso_sevilla` | `nac41` |
| NAC42 | Soria | `congreso_soria` | `nac42` |
| NAC43 | Tarragona | `congreso_tarragona` | `nac43` |
| NAC44 | Teruel | `congreso_teruel` | `nac44` |
| NAC45 | Toledo | `congreso_toledo` | `nac45` |
| NAC46 | Valencia | `congreso_valencia` | `nac46` |
| NAC47 | Valladolid | `congreso_valladolid` | `nac47` |
| NAC48 | Vizcaya | `congreso_vizcaya` | `nac48` |
| NAC49 | Zamora | `congreso_zamora` | `nac49` |
| NAC50 | Zaragoza | `congreso_zaragoza` | `nac50` |
| NAC51 | Ceuta | `congreso_ceuta` | `nac51` |
| NAC52 | Melilla | `congreso_melilla` | `nac52` |

## Variante de 350 (49 ids, sufijo `-350`)

| id viejo | padre | id nuevo |
|---|---|---|
| `congreso350_alava` | NAC01 | `nac01-350` |
| `congreso350_albacete` | NAC02 | `nac02-350` |
| `congreso350_alicante` | NAC03 | `nac03-350` |
| `congreso350_almeria` | NAC04 | `nac04-350` |
| `congreso350_avila` | NAC05 | `nac05-350` |
| `congreso350_badajoz` | NAC06 | `nac06-350` |
| `congreso350_barcelona` | NAC08 | `nac08-350` |
| `congreso350_burgos` | NAC09 | `nac09-350` |
| `congreso350_caceres` | NAC10 | `nac10-350` |
| `congreso350_cadiz` | NAC11 | `nac11-350` |
| `congreso350_castellon` | NAC12 | `nac12-350` |
| `congreso350_ciudad_real` | NAC13 | `nac13-350` |
| `congreso350_cordoba` | NAC14 | `nac14-350` |
| `congreso350_la_coruna` | NAC15 | `nac15-350` |
| `congreso350_cuenca` | NAC16 | `nac16-350` |
| `congreso350_gerona` | NAC17 | `nac17-350` |
| `congreso350_granada` | NAC18 | `nac18-350` |
| `congreso350_guadalajara` | NAC19 | `nac19-350` |
| `congreso350_guipuzcoa` | NAC20 | `nac20-350` |
| `congreso350_huelva` | NAC21 | `nac21-350` |
| `congreso350_huesca` | NAC22 | `nac22-350` |
| `congreso350_jaen` | NAC23 | `nac23-350` |
| `congreso350_leon` | NAC24 | `nac24-350` |
| `congreso350_lerida` | NAC25 | `nac25-350` |
| `congreso350_la_rioja` | NAC26 | `nac26-350` |
| `congreso350_lugo` | NAC27 | `nac27-350` |
| `congreso350_madrid` | NAC28 | `nac28-350` |
| `congreso350_malaga` | NAC29 | `nac29-350` |
| `congreso350_murcia` | NAC30 | `nac30-350` |
| `congreso350_navarra` | NAC31 | `nac31-350` |
| `congreso350_orense` | NAC32 | `nac32-350` |
| `congreso350_asturias` | NAC33 | `nac33-350` |
| `congreso350_palencia` | NAC34 | `nac34-350` |
| `congreso350_pontevedra` | NAC36 | `nac36-350` |
| `congreso350_salamanca` | NAC37 | `nac37-350` |
| `congreso350_cantabria` | NAC39 | `nac39-350` |
| `congreso350_segovia` | NAC40 | `nac40-350` |
| `congreso350_sevilla` | NAC41 | `nac41-350` |
| `congreso350_soria` | NAC42 | `nac42-350` |
| `congreso350_tarragona` | NAC43 | `nac43-350` |
| `congreso350_teruel` | NAC44 | `nac44-350` |
| `congreso350_toledo` | NAC45 | `nac45-350` |
| `congreso350_valencia` | NAC46 | `nac46-350` |
| `congreso350_valladolid` | NAC47 | `nac47-350` |
| `congreso350_vizcaya` | NAC48 | `nac48-350` |
| `congreso350_zamora` | NAC49 | `nac49-350` |
| `congreso350_zaragoza` | NAC50 | `nac50-350` |
| `congreso350_ceuta` | NAC51 | `nac51-350` |
| `congreso350_melilla` | NAC52 | `nac52-350` |
