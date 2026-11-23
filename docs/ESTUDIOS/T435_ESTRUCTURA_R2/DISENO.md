# T-435 — Estructura clara de R2 (diseño; D-188)

VERSIÓN: 1.2.0 · FECHA: 2026-11-23 · ESTADO: aprobado (propietario, 20-11: «sí» a las tres preguntas, vía Planificador) · ANTERIOR: legacy/docs/ESTUDIOS/T435_ESTRUCTURA_R2/DISENO_v1.1.0.md

CAMBIOS 1.2.0 (T-443): §f, D-198 (quién escribe cada rama y «vigente = publicado + último» en `interno/`). 1.1.0: §e, precisiones de la implementación (módulo `herramientas/rutas_r2.py`).

Solo diseño: no se mueve ni se borra nada. Parte de lo aprobado el 20-11 (carpetas en español sin códigos ni runs; solo la versión
vigente; regeneración posterior al 29-11 ya en la estructura nueva y borrado de lo viejo junto con D-178). Fuente de lo actual:
P74 Listar, run 44751091049 (20-11; 16,467 GB = 164,7 % de 10 GB; el listado anterior, run 44541851289 del 19-11, daba 16,466 GB (T-416, Traspaso del Operador): la diferencia de 0,001 GB es de dos listados de días distintos, no verificada, compatible con objetos subidos entre ambos; el CSV está en el artefacto `p74-inventario-44751091049`, que desde la
sesión cloud no se puede descargar: la tabla b) sale de los totales por carpeta del log y de las claves que escribe el código; la
asignación clave a clave la genera una herramienta (§c, paso 1) con el CSV.

## a) Árbol definitivo y reglas de nombres

```
fuentes/<organismo>/<año>/                      fuentes oficiales con sha256 (INE, Interior, Xunta, Nazioen Behatokia, CREM, SADEI…)
mapas/nacionales/congreso-2023/<provincia>/     mapa vigente, composición, resultados y doble vuelta de cada provincia
mapas/autonomicas/<comunidad>-<año>/<provincia>/
mapas/historicos/congreso-2011/<provincia>/     (idem 2015, 2016, 2019-04, 2019-11 cuando toque)
interno/                                        checkpoints, auditorías, batería y pruebas; nunca lo lee la web
```

El bucket de trabajo tiene solo `fuentes/`, `mapas/` e `interno/`. `web/actual/` (índice vigente `actual.json`, D-186) va **solo** en el bucket público `ddd-web-datos` de T-430.
Las fuentes ya preparadas de cada territorio (los paquetes P10) van en `fuentes/por-territorio/{nacionales,autonomicas}/<territorio>/` (subcarpeta de ámbito: `nac` y `aut` comparten nombres, como Madrid o Murcia; decidido el 21-11).

- Nombres: español, minúsculas, sin tildes ni «ñ», palabras con guion (`la-coruna`, `santa-cruz-de-tenerife`, `ciudad-real`).
  Topónimos solo en español, según `fuentes/territorios_espana.yaml` (Gerona, Lérida, Orense, Guipúzcoa, Vizcaya, Álava).
  Prohibidos en cualquier nombre de carpeta o fichero: `nac01`, `aut05`, `congreso_…`, ids de run (`4475…`), `sha`, versiones.
- Dentro de cada carpeta de mapa, nombres fijos: `manifiesto.json`, `mapa.geojson`, `composicion.csv`, `resultados.zip`,
  `doble-vuelta.zip`. El run, la huella del motor/contrato, el sha256 de cada fichero y la fecha van **solo** en `manifiesto.json`.
- **Organismo** en `fuentes/`: `ine`, `interior`, `xunta`, `nazioenbehatokia`→`gobierno-vasco` (el nombre en euskera sale), `crem`
  (Murcia), `sadei` (Asturias), `observatorio-autonomicas`. El nombre original del fichero y su sha12 van en el manifiesto de la
  carpeta, no en la ruta.
- Solo la versión vigente, también para la web: se escribe la nueva, se comprueba el sha256 y se borra la anterior; la web refresca la caché cada 60 s (decidido, pregunta 1).

## b) Tabla de rutas actuales → ruta nueva (por patrón)

**Aviso:** sin el CSV del P74 (no descargable desde la nube) la columna «Tamaño» es el orden de magnitud tomado del log del P74 (totales por carpeta de primer nivel) y los conteos (52 `nacNN`, 19 `autNN`, ~11 objetos por territorio, 57 duplicados) salen del mismo log; las rutas son las que escribe el código. Es una propuesta por patrón, no una lista de claves. «Borrar» significa «candidata a borrar»: **ningún borrado ocurre antes del 29-11 ni antes de regenerar, copiar y verificar, y siempre con frase de campaña del propietario (D-52; D-176/D-178)**.

| Ruta actual | Tamaño | Ruta nueva | Notas |
|---|---:|---|---|
| `arc-e/fuentes/ine/seccionado_<año>_<sha12>.zip` | parte de 12,87 GB | `fuentes/ine/<año>/seccionado.zip` | los 5 contratos históricos lo citan por `r2_clave` |
| `arc-e/fuentes/interior/…` (ZIP por mesa 2023-07) | idem | `fuentes/interior/2023/mesas.zip` | `fuente_r2.py` |
| `arc-e/fuentes/xunta/<nombre>_<sha12>.csv` | idem | `fuentes/xunta/2024/<nombre>.csv` | |
| `arc-e/fuentes/nazioenbehatokia/{data,geo}/<época>/…/<NN>_<sha12>.json` | idem | `fuentes/gobierno-vasco/<año>/…` | 5 grupos duplicados idénticos 2019/2020 y 2016/2024: se guarda uno y el manifiesto apunta a ambos años |
| `arc-e/paquetes-p10/<package_sha256>.zip` | idem | `fuentes/por-territorio/{nacionales,autonomicas}/<territorio>/paquete.zip` (+ manifiesto con el sha256) | decidido (pregunta 2) |
| `arc-e/<territorio>/<run>/…` (entradas mínimas ddd-minimo) | idem | `interno/entradas/<territorio>/` | solo la última |
| `arc-p/m06/<asset>_<sha12>.zip` | 1,11 GB (con el resto de `arc-p`) | `mapas/…/<provincia>/mapa.geojson` si es M06 vigente; resto `interno/` | `almacen_m06_r2.py`, `localizar_artefacto_durable.py` |
| `arc-p/<id>/<run>/auditoria-*.zip` | idem | `interno/auditorias/<territorio>/` | |
| `<territorio>/<run>/ddd-*.zip` (`cataluna`, `madrid`, `andalucia`…, ~11 objetos c/u; 0,37 GB la mayor) | ~1,8 GB en estados viejos | `interno/estados/{nacionales,autonomicas}/<territorio>/` (solo el último) o **borrar** | claves de `archivo_r2.json`; el resto, **borrar** (D-178) |
| `nacNN/<run>/ddd-doble-vuelta-…-p75-<run>-1.zip` (52) | ~0,1 GB | `mapas/nacionales/congreso-2023/<provincia>/doble-vuelta.zip` | 57 duplicados idénticos (0,001 GB): solo queda el de la última generación |
| `autNN/…` (19) | ~0,1 GB | `mapas/autonomicas/<comunidad>-<año>/…` | P75 autonómicas |
| `congreso_<provincia>/…`, `congreso350_<provincia>/…` | ~0,3 GB | `interno/` o **borrar** | territorios antiguos; `congreso350_*` son la competición (T-428), no producto |
| `doble_vuelta/<AAAA-MM>/<run>/INFORME.json`, `doble_vuelta/autonomicas/<run>/` | ~0 | dentro de cada carpeta de mapa (`manifiesto.json` + `doble-vuelta.zip`) | `doble_vuelta_publicada.json` pasa a apuntar a ruta nueva |
| `bateria/…` | 0,05 GB | **borrar** (retirada) o `interno/bateria/` si P80 la sigue leyendo | `p80-verificacion-motor.yml` aún la cita: confirmar |
| `videos/` | 0,15 GB | **mover al bucket público de vídeos** (D-178) | no es del bucket de trabajo |
| `campanas/`, `connection-tests/` | ~0 | `interno/campanas/` · **borrar** | |
| (nuevo) | — | `web/actual/actual.json` **en `ddd-web-datos`**, no en este bucket | lo escribe P40 (decidido, pregunta 3) |

## c) Código, workflows e índices que cambian, y orden

Hoy cada herramienta compone la clave a su manera. Orden propuesto (cada paso es una PR; ninguno borra):

1. **Un solo módulo de rutas** (`herramientas/rutas_r2.py`): funciones `ruta_fuente(organismo, año)`, `ruta_mapa(ámbito, …, provincia)`, `ruta_interno(…)` y la regla de nombres. Con él, una herramienta (solo lectura) lee el CSV del P74 y genera la tabla clave a clave «actual → nueva / borrar».
2. **Lectores con doble ruta** (nueva primero, vieja de respaldo): `fuente_r2.py`, `p10_desde_r2.py`, `restaurar_estado_r2.py`, `contrastar_extracto_p10.py`, `almacen_m06_r2.py`, `localizar_artefacto_durable.py`, `bateria_motor.py`, `publicar_doble_vuelta.py`, `p75_doble_vuelta_r2.py`.
3. **Índices**: `fuentes_r2` (índice de fuentes, `GUIA_FUENTES_R2.md`), `archivo_r2.json` (claves `<territorio>/<run>/<artefacto>.zip` → nuevas, y el run pasa al manifiesto), `doble_vuelta_publicada.json`, `datos_abiertos/INDEX.json` y los `r2_clave` de los 5 `configuracion/historico_epoca/contrato_*.json` (265 referencias).
4. **Escritores**: `archivar_artefactos_r2.py` (`clave()`), `espejo_*_r2.ps1`, `p75_doble_vuelta_r2.py`, y el P10 (`p10-fuentes.yml`) escriben ya en la estructura nueva.
5. **Workflows**: `p70-archivo.yml` (acciones P71-P75), `p10-fuentes.yml`, `p40-publicacion.yml` (paso «Doble vuelta»; escribe `web/actual/`), `p50-publicacion-academica.yml` (rutas de datos citadas), `p80-verificacion-motor.yml` (batería), `_reutilizable-puerta-validacion.yml` (`arc-p/m06/`).
6. **`podar_r2.py`**: lista aprobada de claves `ddd-state-*` y su protección de `arc-e/` pasan a la estructura nueva (`interno/` y `fuentes/`); se actualiza **antes** del borrado.
7. **Web**: `actual.json` vive en `ddd-web-datos` y lo lee `ddd-web` (T-430); P40 escribe allí las rutas nuevas de `mapas/`; la web no cambia.
8. **Regeneración posterior al 29-11** escribe en la estructura nueva; verificación (sha256 y recuentos contra el manifiesto); **solo entonces** el borrado de lo viejo con D-178 (Operador, frase del propietario). `tests`: uno que fije el árbol y la regla de nombres.

## d) Riesgos

- **sha256 de los contratos**: los contratos históricos llevan `r2_clave`; cambiarlo cambia el fichero y su huella. Hay que ver si esa huella está fijada en otro sitio (huellas M05/N08, `INDEX.json`) antes de tocarlo. Alternativa: los contratos citan el sha256 del contenido y un índice aparte resuelve la ruta (la ruta deja de estar en el contrato).
- **Zenodo/DOI** (D-74, D-186 §9): archiva el repositorio, no R2; si algún DOI cita una URL de R2 hay que mantenerla o redirigirla. Comprobar `.zenodo.json`/`CITATION.cff` y `PREINSCRIPCION_OSF.md`.
- **Web de T-430**: `ddd-web-datos` es otro bucket público (`datos.diputadodedistrito.es`); el diseño de T-430 prevé carpetas inmutables por mapa, que aquí se sustituyen por «solo la vigente» con caché de 60 s: ajustar `DISENO.md` de T-430 y cerrarlo con `session_01KQDtFuyL5pbt5UfWdoL8g4`.
- **Ventana de coexistencia**: durante los pasos 2-8 conviven rutas viejas y nuevas; el límite gratuito (ya al 164,7 %, P74 44751091049) sube con las copias. R2 no renombra: copiar y borrar. Se mitiga copiando por orden de peso. **No se borra nada para hacer sitio**: ningún borrado antes del 29-11 ni antes de regenerar, copiar y verificar, y siempre con frase de campaña D-52 del propietario (D-176/D-178); hasta entonces el bucket sigue sobre el límite.
- **Borrado**: `podar_r2.py` y la guarda de `produccion`; ningún borrado sin frase de campaña del propietario (D-52).
- **Datos que no están en R2**: el visor publicado es de blobs de git; esta reestructuración no lo toca.

## Coordinación con T-430

T-430 sigue adelante con «solo la vigente» (su `DISENO.md` 1.3.0, #957@72d75fa, ya sin carpetas inmutables y con todo bajo `web/actual/` de `ddd-web-datos`); el ajuste pendiente queda cerrado.

## Decisiones del propietario (20-11)

1. Solo la versión vigente también para la web (escribir, comprobar, borrar; caché de 60 s): sí.
2. Fuentes preparadas en `fuentes/por-territorio/<territorio>/`: sí. (21-11: con subcarpeta de ámbito `nacionales/` o `autonomicas/` también en `interno/`: sí.)
4. (21-11) Los 22 paquetes P10 antiguos (1,82 GB) que no cita ningún contrato vigente se borran junto con la limpieza posterior al 29-11 (D-178): sí. Siguen sujetos a D-52.
3. `web/actual/` solo en `ddd-web-datos`; el bucket de trabajo, con `fuentes/`, `mapas/` e `interno/`: sí.

Bucket público `ddd-web-datos` (acordado con T-430): todo bajo `web/actual/` (`actual.json` y los datos con las rutas del sitio: `datos/`, `mapa/datos/`, `v2/datos/`, `data/`), con carpetas de territorio en español sin códigos ni runs; el run y los sha256 van en `actual.json`. No usa la nomenclatura de `mapas/` de este bucket. P40 sube lo cambiado, comprueba sha256, escribe `actual.json` y borra lo que ya no figura en el índice.

Pendiente: el cruce clave a clave, cuando el propietario suba el CSV del P74.

## e) Precisiones de la implementación (T-443, 22-11)

Criterio técnico del Coordinador (22-11), coherente con lo aprobado; el módulo `herramientas/rutas_r2.py` y `tests/test_t443_rutas_r2.py` las fijan:

- **Nombre de territorio**: siempre el `nombre_es` completo de la tabla maestra (`configuracion/notacion_territorial.csv`), igual en `fuentes/por-territorio/`, `interno/estados/` y `mapas/` (`principado-de-asturias`, no `asturias`, en las tres; `CRUCE_claves.csv` mezclaba ambas).
- **Competición** (`congreso350_*`, T-428): paquete P10 y estados en `interno/competicion/<provincia>/` (`paquete.zip`, `<tipo>.zip`), no en `fuentes/por-territorio/nacionales/350-<provincia>/` ni con el run en el nombre.
- **Tipos de estado** en `interno/estados/<ámbito>/<territorio>/`: `audit.zip`, `audit-electoral.zip`, `minimo-m06.zip`, `minimo-m08.zip`, `decision.zip` (minúsculas y guion; el cruce escribía `minimoM06`).
- **Mapa autonómico**: una carpeta por comunidad, `mapas/autonomicas/<comunidad>-<año>/` (como el cruce; sin subcarpeta de provincia). Año = autonómica `vigente=si`; Ceuta y Melilla, sin carpeta hasta fijarlo.
- **Gobierno Vasco**: conserva la ruta original bajo `fuentes/gobierno-vasco/` (`data/<época>/…`) sin sha12, como el cruce.
- **Almacén M06** (`interno/almacen-m06/`): excepción de nombre (conserva el asset del release, con su run) hasta que la regeneración lo sustituya.
- **Transición**: los lectores que componen la clave prueban la nueva y, si falta, la vieja (`rutas_r2.candidatas`); los que la toman de un índice (`archivo_r2.json`, `fuentes_r2.json`, `almacen_m06_r2.json`, `doble_vuelta_publicada.json`) leen la clave que el índice anota, vieja o nueva. Los `r2_clave` de los contratos históricos no se reescriben hasta la regeneración (su huella, §d).

## f) D-198 (propietario, 23-11, «sí a todo»): quién escribe cada rama

Tras la revisión de #988 (sobrescribir lo publicado o certificado). Matiza D-188 en `interno/`: la vigente es **publicado + último**.

- **`mapas/` solo lo escribe la publicación**: P40 promueve lo fijado en el repositorio tras verificar su sha256, y el fijado pasa a la clave de `mapas/`. Ningún cálculo (P75, archivista) escribe en `mapas/`.
- **`interno/` con dos huecos por territorio**: `interno/estados/<ámbito>/<territorio>/publicado/` (el run de `orchestracion/publicaciones_visor.json`; solo cambia al publicar otro) y `…/ultimo/` (el más reciente). Restaurar y P75 buscan el run en los dos.
- **Guarda en R2, no en el índice**: cada objeto sube con metadatos `sha256` y `run`; antes de subir se lee con `head-object` y nunca se pisa un run mayor. El `manifiesto.json` de la carpeta se rehace con las cabeceras de R2.
- **P75** escribe en `interno/doble-vuelta/<lo mismo que su carpeta de mapas>/doble-vuelta.zip` y su informe (`interno/doble-vuelta/…/informe-doble-vuelta.json`) **se fusiona por territorio**: una ejecución parcial solo cambia sus filas OK; un fallo no sustituye a una fila OK; con otros bloques o alias, el informe empieza de nuevo. P70 serializa sus jobs (`concurrency: archivar-artefactos-r2`).
- **`fuentes/` inmutable**: si la clave ya existe con otro sha256, falla (espejos Galicia e INE/Observatorio).
- **Paquete P10 inmutable por edición del contrato** (Planificador, 23-11, dentro de D-198): `fuentes/por-territorio/<ámbito>/<territorio>/<edición>/paquete.zip` (edición = año del contrato); si cambia dentro de la misma edición, falla (`BATERIA_PAQUETE_P10_EDICION_CAMBIADA`) y obliga a abrir edición nueva; el sha256 y el package_sha256 van en el manifiesto, no en la ruta. Se conservan las ediciones que cita algún contrato vigente o histórico de `configuracion/`; el resto se borra con D-178/D-190. Lector: la edición del contrato primero y `arc-e/paquetes-p10/<package_sha256>.zip` de respaldo. **`arc-e/paquetes-p10/` no se borra hasta que exista la copia por edición de cada paquete citado, comprobada por sha256** (lo exige `podar_r2.py`, PR 5/5).
