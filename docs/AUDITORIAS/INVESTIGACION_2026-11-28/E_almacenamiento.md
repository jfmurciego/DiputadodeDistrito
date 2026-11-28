# T-509 · E — Almacenamiento y datos

VERSIÓN: 1.0.0 · FECHA: 2026-11-28 · ESTADO: informe de investigación, solo lectura; revisado por el escéptico independiente (3 confirmados, 7 corregidos, 0 refutados; sección 10) · ANTERIOR: ninguna (fichero nuevo)

Hallazgos en formato de máquina: `E_almacenamiento.json` (10 hallazgos, E-1 a E-10). Sin credenciales de R2: todo sale de
lo versionado, de la API de GitHub en lectura y de los estudios T-145, T-430, T-432 y T-435.

## 1. Veredicto

1. **Liga de hoy:** primera en huellas, segunda en conservación. El proyecto sabe qué sha256 tiene cada cosa; casi todo
   existe en un solo sitio y nadie ha probado a recuperarlo.
2. Lo bueno, medido: 1.459 de 1.459 objetos del archivo con sha256; 642 de 651 fuentes con sha256; lectura que falla
   cerrada si la huella no cuadra; depósito de 71 mapas con DOI y atestación (441 descargas).
3. **El mayor riesgo es R2 como copia única de las fuentes preparadas**, sin bloqueo de borrado, sin segunda copia y sin
   simulacro de restauración (E-2). Ahí están las fuentes que ya no se pueden volver a bajar igual. Excepciones: el ZIP
   de Interior (Release pública) y los 71 mapas 1.0.0 (Release y Zenodo).
4. **En git, los 479 productos canónicos del registro (y 2 estáticos) son blobs sin árbol ni referencia.** P40 solo
   hace `POST git/blobs`; GitHub no promete conservarlos (E-1). Son regenerables con el motor, pero no bit a bit.
5. **La doble vuelta y los datos de la web no tienen versión fijada:** «solo la vigente» (D-188, decisión del
   propietario) y claves fijas que se pisan; falló dos veces, las dos cerrado: no salió nada erróneo (E-3).
6. **Los datos abiertos no pasan FAIR:** no hay metadatos de máquina ni DOI del conjunto, y la geometría solo está en la
   web (P40 la extrae del blob; no va en git por diseño) (E-4). Y un tercero no puede repetir un mapa: las fuentes
   preparadas están en un bucket privado (E-5).
7. El catálogo de procedencia da 284 avisos falsos y DOI nulo en todo (E-7): la pieza que debería ver una pérdida, no la vería.
8. La estructura D-188 está escrita en el código pero no aplicada a los datos; el borrado llega mañana, antes que la red (E-9, E-10).
9. Nada de esto es caro: todo lo publicado de los 71 territorios pesa 85 MB; lo irrepetible, unos 11 GB.
10. **Liga objetivo:** archivo de datos de investigación de referencia (ALARM, VEST, Redistricting Data Hub).

## 2. Mapa real: dónde vive cada cosa

| Sitio | Qué guarda | Tamaño medido | Retención | Copias | Riesgo |
|---|---|---|---|---|---|
| git, árbol de `main` | código, contratos, índices, `datos/` (19 MB), `datos_abiertos/` (2,4 MB, sin GeoJSON), composición por run (286 CSV), evidencia | repositorio 467 MB | indefinida | clones, GitHub | bajo |
| git, **blobs sin ancla** | 245 M06 + 234 M08 + 2 estáticos del registro del visor | no medible sin 481 llamadas | **no garantizada** | 1 | **alto (E-1)** |
| R2 `ddd-research-archive` (privado) | fuentes (`arc-e/fuentes`, `fuentes/`), 142 paquetes P10, estados y auditorías, almacén M06, doble vuelta | 2.042 objetos, 16,47 GB (P74 del 21-11) | indefinida; borrado manual | 1 | **alto (E-2)** |
| R2 `ddd-web-datos` (público) | `web/actual/` y `actual.json`: datos que lee la web | sin inventario | solo la vigente | regenerable desde git y blobs | medio |
| R2 `ddd-web-sitio` (público) | la web sin los datos | sin inventario | solo la vigente | hoy también en Pages; tras D-194, 1 | medio |
| R2 `ddd-web-pruebas` | una carpeta por rama | sin inventario | hasta cerrar la PR | desechable | nulo |
| R2 de vídeos (D-175, D-178) | el vídeo de presentación; **sin nombre ni variable en ningún fichero del repositorio** | desconocido | desconocida | desconocidas | sin evaluar |
| Artefactos de Actions | estados por etapa, auditorías, paquetes, inventarios P74 | unos 30.500 artefactos (30.531 el 28-11) | 1, 7, 14, 30 o 90 días (54 declaraciones) | pasan a R2 con el archivo diario (P71) | medio |
| Releases | `mapas-v1.0.0` (73 ficheros, 37 MB), Huesca 1.0.0, espejo de Interior, ensayo; **9 de 13 en borrador** (1,11 GB de `almacen-m06-*`) | 1,27 GB | indefinida | Zenodo solo los mapas | bajo |
| Zenodo | serie de mapas 10.5281/zenodo.24448721: paquetes, `SHA256SUMS`, `LINAJE.json`, licencia y nota de fuentes | 37 MB | permanente | Release | muy bajo |

Índices versionados que describen R2: `orchestracion/archivo_r2.json` (1.459 objetos, 2,50 GB, 499 runs),
`fuentes_r2.json` (651 fuentes, 1,04 GB con huella), `almacen_m06_r2.json` (51 objetos). Suman unos 4,7 GB: **los
9,29 GB de paquetes P10, lo más pesado y lo menos repetible, no tienen índice propio en git** (su huella está en cada
contrato: 120 paquetes citados).

### Lo que ya se perdió o hubo que rehacer

- **47 de 63 composiciones sección→distrito** de los primeros M06: vivían en artefactos de 14 días (CLAUDE.md, T-67)
  y hubo que regenerarlas. Hoy las 71 vigentes están en git (`datos/composicion/MANIFEST_RUNS.json`).
- **Los estados completos de la lista de poda de T-145 (234 claves, 26 GB)**, borrados a propósito por ser regenerables. Correcto, pero la
  regeneración ya no da el mismo mapa: el motor ha cambiado desde entonces (Deslinde 1.0, 1.1 y 1.2).
- **El fichero oficial de Castilla-La Mancha 2023**: desapareció del portal y se recuperó de la Wayback (D-203).
- **Casi:** el M08 de Asturias 40132061626 solo existía en R2 y se salvó por una excepción escrita a mano; #998 llegó
  a borrar con la lista de citados vacía y lo paró la revisión.

### Lo que hoy se puede perder sin copia

1. Los 481 blobs del registro (19 de ellos sin ningún objeto de su run en R2; ninguno de los 19 es vigente).
2. Los 120 paquetes P10 vigentes y las fuentes INE: una sola copia, un solo proveedor. Es lo único irrepetible.
3. Los 625 ficheros del Observatorio (fuente secundaria que contrasta el histórico): solo en R2.
4. La doble vuelta y los históricos publicados: clave fija, sin versión.
5. Diez piezas de fuentes que aún están solo en el ordenador del propietario o sin bajar (T-356).

## 3. Estado objetivo «referente mundial»

- **ALARM 50-State Redistricting Simulations** (Harvard Dataverse, DOI 10.7910/DVN/SLCD3E; Scientific Data 9, 689, 2022):
  cada estado, un conjunto con entradas, planes, documentación y versión; cualquiera lo baja y lo repite.
- **VEST y MEDSL** (Harvard Dataverse): resultados por mesa con DOI por conjunto y por versión.
- **Redistricting Data Hub**: cada fichero con ficha de metadatos e informe de validación.
- **NDSA Levels of Digital Preservation 2.0** (2019): nivel 1, dos copias separadas; nivel 3, huellas comprobadas a
  intervalos y copia en otra zona geográfica.

Aquí se vería así: toda versión publicada es inmutable y se cita por DOI y sha256; hay tres copias en dos proveedores;
un simulacro mensual restaura al azar y deja informe; un tercero, sin llaves y sin preguntar, baja las fuentes y el
mapa y comprueba que cuadran.

## 4. Hallazgos (impacto tras la verificación; el mayor es E-2)

**E-1 · Los 479 productos canónicos del registro son blobs de git sin ancla** (impacto 4, esfuerzo S, decisión del propietario: toca P40) · CORREGIDO
- Hoy: `p40-publicacion.yml:475` hace `POST git/blobs` y guarda solo el sha. No hay `git/trees` ni `git/refs` en ningún
  fichero. `git ls-remote` solo da ramas, PR y 4 etiquetas. 479 de 481 blobs no están en el clon (330 ramas); el clon es
  superficial, así que la prueba de que no tienen ancla es el código de P40, no esa ausencia.
- Importa: 16 herramientas manejan ese sha (7 llaman a `git/blobs`); ningún sha256 del registro está en el índice de R2
  (0 de 481), así que la copia de R2 no acredita que lo recuperado es lo publicado. No es pérdida irreparable: los mapas
  se regeneran y los 71 M06 de la 1.0.0 están en Release y Zenodo. Por eso el impacto baja de 5 a 4.
- Propuesta: un commit sin padres cuyo árbol liste los blobs, bajo `refs/ddd/productos`; P40 lo actualiza. Sin volver a subir nada.
- Aceptación: `git clone --mirror` y `git cat-file -e` de cada `blob_sha` del registro: 481 de 481. Test en el guardián.
- Refutación intentada: T-275 (repositorio público) lo habría cambiado, pero no se hizo; no hay tarea ni decisión.

**E-2 · R2 es copia única de las fuentes preparadas: sin segunda copia, sin bloqueo y sin simulacro** (5, M, decisión del propietario) · CORREGIDO
- Hoy: 0 menciones de versionado, bloqueo, copia de seguridad o prueba de restauración en plan, estudios, herramientas
  y workflows. El sha256 se comprueba al leer; lo que no se lee no se comprueba (el ETag multiparte no sirve).
- Importa: el paquete P10 es la única instantánea del seccionado del INE de ese día. Sin él, el mapa publicado no se repite.
- Propuesta: bloqueo por prefijo en `fuentes/` y lo publicado; segunda copia en otro proveedor (11 GB, céntimos al mes);
  acción «Simulacro» mensual en P70; auditoría de huellas por muestreo.
- Aceptación: `orchestracion/simulacro_restauracion.json` con menos de 35 días, 3 territorios restaurados de la segunda
  copia, paquete igual a `package_sha256` del contrato y publicado igual a `archivo_r2.json` (el sha256 del registro del
  visor es de otro empaquetado y no coincide ninguno); un test falla si caduca. El bloqueo se prueba con un objeto
  centinela y la lectura de las reglas, nunca borrando una clave real.
- Matices: la inmutabilidad de `fuentes/` de D-198 es una guarda de la herramienta, no un bloqueo del bucket. Depositar
  en Zenodo algo más que mapas amplía D-146.

**E-3 · La doble vuelta y los datos de la web no tienen versión fijada** (3, M, decisión: reabre D-188) · CORREGIDO
- Hoy: D-188 guarda solo la vigente y saca run y huella de la ruta. El pin de la doble vuelta apunta a una clave fija;
  un P75 posterior la cambió y P40 falló con `INFORME_SHA256_DISTINTO` (run 45873075949). Reincidencia documentada.
  Las dos veces falló cerrado: la web siguió con la versión anterior. D-198 ya da candidato y promoción con huella, y
  los mapas sí tienen serie inmutable (Release y Zenodo). Por eso el impacto baja de 4 a 3.
- Propuesta: servir desde «actual», conservar en `publicado/<sha256>`; los pines citan la huella, no la ruta.
- Aceptación: desde la entrada en vigor (lo ya pisado no se recupera), cada sha256 fijado en git responde 200 en
  `publicado/<sha256>`; un test con dos informes prueba que relanzar P75 no cambia lo que publica P40.

**E-4 · Los datos abiertos no pasan FAIR** (3, M, decisión; ampliar T-476, que ya trae diccionario, validador y DOI) · CORREGIDO
- Hoy: `INDEX.json` da ruta y sha256 de 52 GeoJSON que no están en git por diseño: P40 los extrae del blob, los verifica
  y los publica en la web (`generar_datos_abiertos.py --materializar`). Solo Congreso, solo ganador. Sin fecha,
  versión, DOI ni diccionario tipado. 0 ficheros con DCAT, schema.org o datapackage. GitHub: licencia `NOASSERTION`.
- Aceptación: con solo el DOI, `frictionless validate` sin errores, huellas iguales y un guion de 10 líneas pinta una
  provincia; un test comprueba el bloque JSON-LD `Dataset` de la página de datos contra `INDEX.json`.
- Detalle FAIR en la sección 5.

**E-5 · Un tercero no puede repetir un mapa: fuentes en bucket privado** (4, M, decisión; amplía D-146, «solo mapas») · CORREGIDO
- Hoy: el contrato cita `package_sha256`, pero el paquete solo está en R2 privado. 9 de 651 fuentes sin huella; 0 con licencia.
- Propuesta: depositar en Zenodo los paquetes de los contratos vigentes que se puedan redistribuir (condiciones de INE,
  Interior y Observatorio: a confirmar en origen). Es la tercera copia de E-2. El ZIP de Interior ya es público en una Release.
- Aceptación: sin llaves, bajar del DOI el paquete de una provincia y comprobar que su sha256 es el del contrato.

**E-6 · No hay mapa declarado de dónde vive cada clase de artefacto** (3, S, fusión) · CORREGIDO
- Hoy: seis sitios, 5 plazos de retención distintos, 9 releases en borrador, un bucket (vídeos) sin nombre en el
  repositorio. Cada limpieza ha necesitado un estudio (T-145, T-302, T-416, T-432, T-435); Asturias se detectó a tiempo.
  No consta ninguna pérdida irreparable por esta causa: por eso el impacto baja de 4 a 3.
- Propuesta: `orchestracion/mapa_almacenamiento.yaml` (clase, dónde, copias, retención, quién borra, regenerable) y un test.
- Aceptación: el test falla con un `upload-artifact` o un prefijo de R2 escrito por el código sin clase (el test no lee
  el bucket), o con una clase irrepetible con menos de dos copias.

**E-7 · El catálogo de procedencia da 284 avisos falsos y DOI nulo** (3, S, fusión) · CONFIRMADO
- Hoy: `catalogo_procedencia.py:78` busca `ddd-state-<run>`, que ya no se sube. Avisa en 284 vigentes; los 71 canónicos
  sí tienen copia (142 claves `publicado/`). 0 de 70 composiciones del catálogo corresponden al M06 vigente. DOI nulo en 142 de 142.
- Aceptación: `--comprobar` da 0 avisos en los 71 canónicos y DOI en los 71; quitar una clave del índice lo hace fallar.

**E-8 · Índice de fuentes desfasado y sin licencias** (3, S, fusión; T-356 en parte) · CORREGIDO
- Hoy: 633 de 651 entradas dicen «pendiente de subir» y el P74 lista subidas las 625 del Observatorio; 641 en ruta vieja y 1 en la nueva.
- Aceptación: 651 de 651 con licencia y con verificación de menos de 35 días, rellenadas por el inventario.

**E-9 · D-188 a medias y un solo bucket inventariado de cinco** (3, M, lanzamiento; T-416 en parte) · CONFIRMADO
- Hoy: 426 claves nuevas (219 MB) y 1.033 viejas (2.279 MB) en el índice; `mapas/` sin claves; último P74 el 21-11.
- Aceptación: `orchestracion/inventario_r2.json` con los 5 buckets y menos de 8 días; al cerrar, 0 claves de prefijo viejo.

**E-10 · El borrado del 29-11 va antes que la red de seguridad** (3, S, decisión) · CONFIRMADO
- Hoy: el plan fecha el borrado (D-178, D-190) y la retirada de Pages (D-194); ninguna tarea de copia ni de simulacro.
- Aceptación: la ficha de campaña del borrado cita el simulacro en verde y el test de anclaje; sin ellos, la poda sale con error.

## 5. Datos abiertos frente a FAIR, punto por punto

| Principio | Hoy | Falta |
|---|---|---|
| F1 identificador persistente | DOI solo para la serie de mapas; `datos_abiertos/` no tiene | DOI del conjunto y de cada versión |
| F2 metadatos ricos | LEEME en prosa e índice con huellas | título, autor, fecha, versión, cobertura, elección y fuentes en campos |
| F3 los metadatos citan el identificador | no | DOI dentro de `INDEX.json` y de cada CSV |
| F4 indexado en un buscador | no | JSON-LD `Dataset` en la página; alta en datos.gob.es (DCAT-AP-ES) |
| A1 protocolo abierto | HTTPS del sitio y de GitHub; la geometría canónica exige la API de GitHub | URL estable por fichero, sin API ni llave |
| A2 metadatos aunque el dato desaparezca | no | ficha en Zenodo |
| I1 formato y lenguaje formal | CSV y GeoJSON (bien) | esquema de campos con tipos (`datapackage.json`) |
| I2 vocabularios | siglas propias; clave `nacNN` | código INE de provincia y municipio como columnas; tabla de homologación de siglas enlazada |
| I3 referencias a otros datos | `sha256_origen` y `blob_sha` | enlace a la fuente (INE, Interior, BOE) con su huella y a la composición sección→distrito |
| R1.1 licencia clara | CC BY 4.0 en LEEME y en el índice (bien) | fichero de licencia propio en la carpeta; hoy GitHub da `NOASSERTION` |
| R1.2 procedencia | run y huellas (bien, mejor que la media) | motor y versión, contrato y fecha de generación por fichero |
| R1.3 estándares de la comunidad | parcial | paquete Frictionless; equivalencia por secciones al estilo de los ficheros de asignación |

**Lo que un tercero tiene que preguntar hoy:** dónde está el GeoJSON; qué versión es y de qué fecha; qué es cada
columna y en qué unidad; qué secciones forman cada distrito (está en `datos/composicion/`, no en el paquete);
dónde están las autonómicas; cómo citarlo; si puede redistribuir las fuentes.

## 6. Estructura objetivo y su prueba de restauración

Respeta D-188 y D-198 (nombres en español, quién escribe cada rama) y añade tres cosas: conservar por huella, segunda
copia y bloqueo.

```
git      main ........................ código, contratos, índices, mapa_almacenamiento.yaml
         refs/ddd/productos .......... árbol con todos los blobs del registro (ancla; E-1)
R2 A     fuentes/ .................... inmutable, bloqueada; índice con licencia y verificación (E-8)
         publicado/<sha256> .......... todo lo que salió alguna vez a la web o a un informe; bloqueada (E-3)
         mapas/ ...................... la vigente, nombres claros (D-188): apunta a publicado/
         interno/ .................... candidato y último; lo único borrable
R2 web   web/actual/ y sitio ......... solo la vigente; regenerable desde git + publicado/
Copia B  otro proveedor .............. fuentes/ y publicado/, sincronizadas a diario, solo añadir
Zenodo   mapas (ya), datos abiertos, fuentes redistribuibles: DOI por versión (E-4, E-5)
Actions  artefactos .................. un plazo por clase; nada irrepetible vive solo aquí (E-6)
```

**Prueba de restauración («Simulacro», mensual y antes de cualquier borrado):**
1. Elegir 3 territorios al azar con semilla impresa en el log.
2. En un job sin la llave de R2 A: bajar de la copia B el paquete de fuentes y el producto publicado de cada uno.
3. Comprobar: sha256 del paquete = `package_sha256` del contrato; sha256 del producto = el del registro; el blob de
   git se obtiene de un `clone --mirror` y coincide.
4. Recalcular M01 a M03 de uno de los tres con el motor vigente y comparar con la huella del linaje (unos minutos).
5. Escribir `orchestracion/simulacro_restauracion.json` (fecha, semilla, territorios, huellas, duración).
6. Un test falla si el informe tiene más de 35 días o algún resultado distinto de «igual».

## 7. Camino en tres pasos

| Cuándo | Qué | Prueba |
|---|---|---|
| Esta semana | E-1 (anclar blobs; con permiso del propietario), E-7 (catálogo veraz), E-6 (mapa de almacenamiento con test). E-10: el borrado espera | `clone --mirror` con 481 de 481 blobs; `--comprobar` con 0 avisos falsos; el test del mapa en verde |
| Este mes | E-2 (bloqueo, copia B, primer simulacro), E-3 (`publicado/<sha256>`), E-8 y E-9 (índices e inventario de los 5 buckets). Después, la migración y el borrado de D-178 y D-190 | informe del simulacro en git y en verde; 0 claves de prefijo viejo; inventario de menos de 8 días |
| Este trimestre | E-4 y E-5: datos abiertos como paquete con DOI y fuentes depositadas; alta en datos.gob.es | un tercero, sin llaves, repite la comprobación de una provincia a partir de dos DOI |

## 8. Lo que no pude comprobar

- **Configuración real de los buckets** (bloqueo, ciclo de vida, llaves y sus permisos): sin credenciales. Se comprueba
  en el panel de Cloudflare o con un job de solo lectura que imprima la configuración.
- **Qué hay en el bucket de vídeos y en los tres buckets web, y cómo se llama el primero**: no hay inventario ni nombre
  versionado. Se comprueba con E-9.
- **Cuándo recolecta GitHub los objetos inalcanzables**: no lo publica. Hoy los blobs responden; el riesgo es de
  plazo desconocido. La parte comprobada es que P40 no crea árbol ni referencia para ellos (el clon local es superficial
  y no sirve de prueba).
- **Tamaño total de los 481 blobs**: harían falta 481 llamadas. Orden de magnitud: los paquetes mínimos de R2 suman 680 MB.
- **Si el depósito de Zenodo coincide run a run con los vigentes del registro**: zenodo.org da 403 desde la nube. Todos
  los vigentes son anteriores a la Release del 20-11, lo que es compatible. Se comprueba leyendo `LINAJE.json`.
- **Licencia de redistribución del Observatorio** y condiciones exactas de Interior: hay que leerlas en origen.
- **Datos abiertos tal como se sirven en la web**: la web no es accesible desde la nube. Por el código, P40 sí publica el
  GeoJSON (`--materializar`, `p40-publicacion.yml:530`).
- El retraso del archivo diario (cron a las 05:17 UTC, runs observados entre las 13 y las 16 UTC) no lo investigué.

## 9. Objeciones (D-216)

1. **A D-188 («solo la versión vigente»):** vale para servir, no para conservar. Un proyecto que quiere ser citado
   necesita que lo publicado no se pueda pisar. La evidencia son los dos fallos del pin de la doble vuelta (cerrados:
   P40 se negó a publicar). No pido
   guardar todo: pido guardar lo que salió al público, que son decenas de megas.
2. **Al orden de D-178 y D-190:** borrar 4 GB para acercarse a un tramo gratuito de 10 GB que el propio cruce dice
   inalcanzable (quedan 12,3 GB) ahorra unos céntimos al mes y es la operación con más riesgo del plan. Propongo
   asumir el coste y borrar solo después del primer simulacro.
3. **A «motor repetible, no conservar resultados» (08-11):** cierto para lo intermedio. Pero «repetible» depende de
   conservar las entradas exactas y la versión del motor; con Deslinde 1.0, 1.1 y 1.2 en un mes, lo ya publicado solo
   se repite si se guardan fuentes, contrato y versión. Conservar entradas y publicado es lo que hace verdadera la regla.
4. **Al encargo:** «referente mundial» en este ámbito no se gana con más estructura interna sino con que alguien de
   fuera baje los datos y las fuentes y le cuadren. E-4 y E-5 pesan más para esa meta que la reordenación de R2.

## 10. Verificación independiente (escéptico, 28-11)

Base: `origin/main` 548968c47. Reproducidos los 10 hallazgos con comandos propios (detalle en el campo `verificacion`
de cada hallazgo del JSON). Ninguno arreglado por una PR posterior ni convertido ya en tarea.

| Hallazgo | Veredicto | Qué cambia |
|---|---|---|
| E-1 | CORREGIDO | Clon superficial: la prueba es el código de P40. 16 herramientas, no 13; 330 ramas. Impacto 5→4. Pide decisión (toca P40) |
| E-2 | CORREGIDO | Cifras iguales. «Copia única» acotado; criterio sin borrar claves reales y contra `archivo_r2.json`. Sigue en 5 |
| E-3 | CORREGIDO | Reabre D-188; los fallos fueron cerrados; los 19 sin copia no son vigentes; criterio hacia adelante. Impacto 4→3 |
| E-4 | CORREGIDO | La geometría sí se publica en la web; T-476 ya trae diccionario, validador y DOI. Impacto 4→3 |
| E-5 | CORREGIDO | Criterio sin «validador público»; licencias sin comprobar; amplía D-146. Sigue en 4 |
| E-6 | CORREGIDO | 5 plazos, no 6; `ddd-publico` no comprobable; sin pérdida irreparable documentada. Impacto 4→3 |
| E-7 | CONFIRMADO | Los 284 avisos tienen su run en el índice de R2 |
| E-8 | CORREGIDO | 633 «pendiente de subir», no 630 |
| E-9 | CONFIRMADO | — |
| E-10 | CONFIRMADO | — |

### Descartados en la verificación

Ningún hallazgo refutado. Afirmaciones sueltas retiradas del texto:

- «R2 `ddd-publico`»: el nombre no aparece en ningún fichero del repositorio; no se puede afirmar que exista con ese nombre.
- «47 composiciones perdidas»: no se recuperaron del artefacto, pero se regeneraron; no es una pérdida.
- «La geometría que anuncia el índice no está» como defecto: no se versiona por diseño y P40 la publica verificada.
- «INE e Interior permiten redistribuir con atribución»: no comprobado en origen.
