# T-435 — Estructura clara de R2 (diseño; D-188)

VERSIÓN: 1.0.0 · FECHA: 2026-11-20 · ESTADO: aprobado (propietario, 20-11: «sí» a las tres preguntas, vía Planificador) · ANTERIOR: ninguna (fichero nuevo)

Solo diseño: no se mueve ni se borra nada. Parte de lo aprobado el 20-11 (carpetas en español sin códigos ni runs; solo la versión
vigente; regeneración posterior al 29-11 ya en la estructura nueva y borrado de lo viejo junto con D-178). Fuente de lo actual:
P74 Listar, run 44751091049 (16,467 GB; el CSV está en el artefacto `p74-inventario-44751091049`, que desde la
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
Las fuentes ya preparadas de cada territorio (los paquetes P10) van en `fuentes/por-territorio/<territorio>/`.

- Nombres: español, minúsculas, sin tildes ni «ñ», palabras con guion (`la-coruna`, `santa-cruz-de-tenerife`, `ciudad-real`).
  Topónimos solo en español, según `fuentes/territorios_espana.yaml` (Gerona, Lérida, Orense, Guipúzcoa, Vizcaya, Álava).
  Prohibidos en cualquier nombre de carpeta o fichero: `nac01`, `aut05`, `congreso_…`, ids de run (`4475…`), `sha`, versiones.
- Dentro de cada carpeta de mapa, nombres fijos: `manifiesto.json`, `mapa.geojson`, `composicion.csv`, `resultados.zip`,
  `doble-vuelta.zip`. El run, la huella del motor/contrato, el sha256 de cada fichero y la fecha van **solo** en `manifiesto.json`.
- **Organismo** en `fuentes/`: `ine`, `interior`, `xunta`, `nazioenbehatokia`→`gobierno-vasco` (el nombre en euskera sale), `crem`
  (Murcia), `sadei` (Asturias), `observatorio-autonomicas`. El nombre original del fichero y su sha12 van en el manifiesto de la
  carpeta, no en la ruta.
- Solo la versión vigente, también para la web: se escribe la nueva, se comprueba el sha256 y se borra la anterior; la web refresca la caché cada 60 s (decidido, pregunta 1).

## b) Tabla de rutas actuales → ruta nueva (por patrón; tamaños del P74)

| Ruta actual | Tamaño | Ruta nueva | Notas |
|---|---:|---|---|
| `arc-e/fuentes/ine/seccionado_<año>_<sha12>.zip` | parte de 12,87 GB | `fuentes/ine/<año>/seccionado.zip` | los 5 contratos históricos lo citan por `r2_clave` |
| `arc-e/fuentes/interior/…` (ZIP por mesa 2023-07) | idem | `fuentes/interior/2023/mesas.zip` | `fuente_r2.py` |
| `arc-e/fuentes/xunta/<nombre>_<sha12>.csv` | idem | `fuentes/xunta/2024/<nombre>.csv` | |
| `arc-e/fuentes/nazioenbehatokia/{data,geo}/<época>/…/<NN>_<sha12>.json` | idem | `fuentes/gobierno-vasco/<año>/…` | 5 grupos duplicados idénticos 2019/2020 y 2016/2024: se guarda uno y el manifiesto apunta a ambos años |
| `arc-e/paquetes-p10/<package_sha256>.zip` | idem | `fuentes/por-territorio/<territorio>/paquete.zip` (+ manifiesto con el sha256) | decidido (pregunta 2) |
| `arc-e/<territorio>/<run>/…` (entradas mínimas ddd-minimo) | idem | `interno/entradas/<territorio>/` | solo la última |
| `arc-p/m06/<asset>_<sha12>.zip` | 1,11 GB (con el resto de `arc-p`) | `mapas/…/<provincia>/mapa.geojson` si es M06 vigente; resto `interno/` | `almacen_m06_r2.py`, `localizar_artefacto_durable.py` |
| `arc-p/<id>/<run>/auditoria-*.zip` | idem | `interno/auditorias/<territorio>/` | |
| `<territorio>/<run>/ddd-*.zip` (`cataluna`, `madrid`, `andalucia`…, ~11 objetos c/u; 0,37 GB la mayor) | ~1,8 GB en estados viejos | `interno/estados/<territorio>/` (solo el último) o **borrar** | claves de `archivo_r2.json`; el resto, **borrar** (D-178) |
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
- **Ventana de coexistencia**: durante los pasos 2-8 conviven rutas viejas y nuevas; el límite gratuito (ya al 164 %) sube con las copias. R2 no renombra: copiar y borrar. Se mitiga copiando por orden de peso y borrando lo seguro de D-178 antes.
- **Borrado**: `podar_r2.py` y la guarda de `produccion`; ningún borrado sin frase de campaña del propietario (D-52).
- **Datos que no están en R2**: el visor publicado es de blobs de git; esta reestructuración no lo toca.

## Decisiones del propietario (20-11)

1. Solo la versión vigente también para la web (escribir, comprobar, borrar; caché de 60 s): sí.
2. Fuentes preparadas en `fuentes/por-territorio/<territorio>/`: sí.
3. `web/actual/` solo en `ddd-web-datos`; el bucket de trabajo, con `fuentes/`, `mapas/` e `interno/`: sí.

Pendiente: el cruce clave a clave, cuando el propietario suba el CSV del P74.
