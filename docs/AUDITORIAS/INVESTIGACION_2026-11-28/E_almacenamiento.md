# T-509 · E — Almacenamiento y datos

VERSIÓN: 1.0.0 · FECHA: 2026-11-28 · ESTADO: informe de investigación, solo lectura · ANTERIOR: ninguna (fichero nuevo)

Hallazgos en formato de máquina: `E_almacenamiento.json` (10 hallazgos, E-1 a E-10). Sin credenciales de R2: todo sale de
lo versionado, de la API de GitHub en lectura y de los estudios T-145, T-430, T-432 y T-435.

## 1. Veredicto

1. **Liga de hoy:** primera en huellas, segunda en conservación. El proyecto sabe qué sha256 tiene cada cosa; casi todo
   existe en un solo sitio y nadie ha probado a recuperarlo.
2. Lo bueno, medido: 1.459 de 1.459 objetos del archivo con sha256; 642 de 651 fuentes con sha256; lectura que falla
   cerrada si la huella no cuadra; depósito de 71 mapas con DOI y atestación (441 descargas).
3. **El mayor riesgo no está en R2 sino en git:** los 481 productos canónicos del registro son blobs sin árbol ni
   referencia. No viajan en ningún clon y GitHub no promete conservarlos (E-1).
4. **R2 es copia única**, sin bloqueo de borrado, sin segunda copia y sin simulacro de restauración (E-2). Ahí están las
   fuentes que ya no se pueden volver a bajar igual.
5. **Lo publicado no es inmutable:** «solo la vigente» y claves fijas que se pisan; ya falló dos veces (E-3).
6. **Los datos abiertos no pasan FAIR:** la geometría que anuncia el índice no está en git, no hay metadatos de máquina
   ni DOI del conjunto (E-4). Y un tercero no puede repetir un mapa: las fuentes están en un bucket privado (E-5).
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
| R2 `ddd-publico` | **no consta en ningún fichero del repositorio** (¿vídeo, D-175?) | desconocido | desconocida | desconocidas | sin evaluar |
| Artefactos de Actions | estados por etapa, auditorías, paquetes, inventarios P74 | 30.569 artefactos | 1, 7, 14, 30 o 90 días (54 declaraciones) | pasan a R2 con el archivo diario (P71) | medio |
| Releases | `mapas-v1.0.0` (71 paquetes, 37 MB), Huesca 1.0.0, espejo de Interior, ensayo; **9 de 13 en borrador** (1,11 GB de `almacen-m06-*`) | 1,27 GB | indefinida | Zenodo solo los mapas | bajo |
| Zenodo | serie de mapas 10.5281/zenodo.24448721: paquetes, `SHA256SUMS`, `LINAJE.json`, licencia y nota de fuentes | 37 MB | permanente | Release | muy bajo |

Índices versionados que describen R2: `orchestracion/archivo_r2.json` (1.459 objetos, 2,50 GB, 499 runs),
`fuentes_r2.json` (651 fuentes, 1,04 GB con huella), `almacen_m06_r2.json` (51 objetos). Suman unos 4,7 GB: **los
9,29 GB de paquetes P10, lo más pesado y lo menos repetible, no tienen índice propio en git** (su huella está en cada
contrato: 120 paquetes citados).

### Lo que ya se perdió

- **47 de 63 composiciones sección→distrito** de los primeros M06: vivían en artefactos de 14 días (CLAUDE.md, T-67).
  Hoy las 71 vigentes están en git (`datos/composicion/MANIFEST_RUNS.json`).
- **Los estados completos de 32 runs (26 GB)**, borrados a propósito (T-145) por ser regenerables. Correcto, pero la
  regeneración ya no da el mismo mapa: el motor ha cambiado desde entonces (Deslinde 1.0, 1.1 y 1.2).
- **El fichero oficial de Castilla-La Mancha 2023**: desapareció del portal y se recuperó de la Wayback (D-203).
- **Casi:** el M08 de Asturias 40132061626 solo existía en R2 y se salvó por una excepción escrita a mano; #998 llegó
  a borrar con la lista de citados vacía y lo paró la revisión.

### Lo que hoy se puede perder sin copia

1. Los 481 blobs del registro (19 de ellos sin ningún objeto de su run en R2).
2. Los 120 paquetes P10 vigentes y las fuentes INE: una sola copia, un solo proveedor.
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

## 4. Hallazgos (de mayor a menor impacto)

**E-1 · Los 481 productos canónicos son blobs de git sin ancla** (impacto 5, esfuerzo S, fusión)
- Hoy: `p40-publicacion.yml:475` hace `POST git/blobs` y guarda solo el sha. No hay `git/trees` ni `git/refs` en ningún
  fichero. `git ls-remote` solo da ramas, PR y 4 etiquetas. 479 de 481 blobs no están en el clon (que trae 329 ramas).
- Importa: 13 herramientas leen por ese sha; las copias de R2 y Zenodo tienen otro empaquetado y otro sha256, así que no
  acreditan que lo recuperado es lo publicado.
- Propuesta: un commit sin padres cuyo árbol liste los blobs, bajo `refs/ddd/productos`; P40 lo actualiza. Sin volver a subir nada.
- Aceptación: `git clone --mirror` y `git cat-file -e` de cada `blob_sha` del registro: 481 de 481. Test en el guardián.
- Refutación intentada: T-275 (repositorio público) lo habría cambiado, pero no se hizo; no hay tarea ni decisión.

**E-2 · R2 es copia única: sin segunda copia, sin bloqueo y sin simulacro** (5, M, decisión del propietario)
- Hoy: 0 menciones de versionado, bloqueo, copia de seguridad o prueba de restauración en plan, estudios, herramientas
  y workflows. El sha256 se comprueba al leer; lo que no se lee no se comprueba (el ETag multiparte no sirve).
- Importa: el paquete P10 es la única instantánea del seccionado del INE de ese día. Sin él, el mapa publicado no se repite.
- Propuesta: bloqueo por prefijo en `fuentes/` y lo publicado; segunda copia en otro proveedor (11 GB, céntimos al mes);
  acción «Simulacro» mensual en P70; auditoría de huellas por muestreo.
- Aceptación: `orchestracion/simulacro_restauracion.json` con menos de 35 días, 3 territorios restaurados de la segunda
  copia y huellas iguales a contrato y registro; un test falla si caduca.

**E-3 · Lo publicado no es inmutable** (4, M, decisión: matiza D-188)
- Hoy: D-188 guarda solo la vigente y saca run y huella de la ruta. El pin de la doble vuelta apunta a una clave fija;
  un P75 posterior la cambió y P40 falló con `INFORME_SHA256_DISTINTO` (run 45873075949). Reincidencia documentada.
- Propuesta: servir desde «actual», conservar en `publicado/<sha256>`; los pines citan la huella, no la ruta.
- Aceptación: cada sha256 fijado alguna vez en git responde 200 en `publicado/<sha256>`; relanzar P75 no cambia lo que publica P40.

**E-4 · Los datos abiertos no pasan FAIR** (4, M, decisión; T-476 lo cubre en parte)
- Hoy: `INDEX.json` da ruta y sha256 de 52 GeoJSON que no están en git (0 de 52). Solo Congreso, solo ganador. Sin fecha,
  versión, DOI ni diccionario tipado. 0 ficheros con DCAT, schema.org o datapackage. GitHub: licencia `NOASSERTION`.
- Aceptación: con solo el DOI, `frictionless validate` sin errores, huellas iguales y un guion de 10 líneas pinta una provincia.
- Detalle FAIR en la sección 5.

**E-5 · Un tercero no puede repetir un mapa: fuentes en bucket privado** (4, M, decisión)
- Hoy: el contrato cita `package_sha256`, pero el paquete solo está en R2 privado. 9 de 651 fuentes sin huella; 0 con licencia.
- Propuesta: depositar en Zenodo los paquetes de los contratos vigentes que se puedan redistribuir. Es la tercera copia de E-2.
- Aceptación: sin llaves, bajar del DOI el paquete de una provincia y comprobar que su sha256 es el del contrato.

**E-6 · No hay mapa declarado de dónde vive cada clase de artefacto** (4, S, fusión)
- Hoy: seis sitios, 6 plazos de retención distintos, 9 releases en borrador, un bucket que no consta. Cada limpieza ha
  necesitado un estudio (T-145, T-302, T-416, T-432, T-435) y aun así se escapó Asturias.
- Propuesta: `orchestracion/mapa_almacenamiento.yaml` (clase, dónde, copias, retención, quién borra, regenerable) y un test.
- Aceptación: el test falla con un `upload-artifact` o un prefijo de R2 sin clase, o con una clase irrepetible con menos de dos copias.

**E-7 · El catálogo de procedencia da 284 avisos falsos y DOI nulo** (3, S, fusión)
- Hoy: `catalogo_procedencia.py:78` busca `ddd-state-<run>`, que ya no se sube. Avisa en 284 vigentes; los 71 canónicos
  sí tienen copia (142 claves `publicado/`). 0 de 70 composiciones del catálogo corresponden al M06 vigente. DOI nulo en 142 de 142.
- Aceptación: `--comprobar` da 0 avisos en los 71 canónicos y DOI en los 71; quitar una clave del índice lo hace fallar.

**E-8 · Índice de fuentes desfasado y sin licencias** (3, S, fusión; T-356 en parte)
- Hoy: 630 de 651 entradas dicen «pendiente de subir» y el P74 las lista subidas; 641 en ruta vieja y 1 en la nueva.
- Aceptación: 651 de 651 con licencia y con verificación de menos de 35 días, rellenadas por el inventario.

**E-9 · D-188 a medias y un solo bucket inventariado de cinco** (3, M, lanzamiento; T-416 en parte)
- Hoy: 426 claves nuevas (219 MB) y 1.033 viejas (2.279 MB) en el índice; `mapas/` sin claves; último P74 el 21-11.
- Aceptación: `orchestracion/inventario_r2.json` con los 5 buckets y menos de 8 días; al cerrar, 0 claves de prefijo viejo.

**E-10 · El borrado del 29-11 va antes que la red de seguridad** (3, S, decisión)
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
| Esta semana | E-1 (anclar blobs), E-7 (catálogo veraz), E-6 (mapa de almacenamiento con test). E-10: el borrado espera | `clone --mirror` con 481 de 481 blobs; `--comprobar` con 0 avisos falsos; el test del mapa en verde |
| Este mes | E-2 (bloqueo, copia B, primer simulacro), E-3 (`publicado/<sha256>`), E-8 y E-9 (índices e inventario de los 5 buckets). Después, la migración y el borrado de D-178 y D-190 | informe del simulacro en git y en verde; 0 claves de prefijo viejo; inventario de menos de 8 días |
| Este trimestre | E-4 y E-5: datos abiertos como paquete con DOI y fuentes depositadas; alta en datos.gob.es | un tercero, sin llaves, repite la comprobación de una provincia a partir de dos DOI |

## 8. Lo que no pude comprobar

- **Configuración real de los buckets** (bloqueo, ciclo de vida, llaves y sus permisos): sin credenciales. Se comprueba
  en el panel de Cloudflare o con un job de solo lectura que imprima la configuración.
- **Qué hay en `ddd-publico` y en los tres buckets web**: no hay inventario. Se comprueba con E-9.
- **Cuándo recolecta GitHub los objetos inalcanzables**: no lo publica. Hoy los blobs responden; el riesgo es de
  plazo desconocido. La parte comprobada es que no están en ningún clon.
- **Tamaño total de los 481 blobs**: harían falta 481 llamadas. Orden de magnitud: los paquetes mínimos de R2 suman 680 MB.
- **Si el depósito de Zenodo coincide run a run con los vigentes del registro**: zenodo.org da 403 desde la nube. Todos
  los vigentes son anteriores a la Release del 20-11, lo que es compatible. Se comprueba leyendo `LINAJE.json`.
- **Licencia de redistribución del Observatorio** y condiciones exactas de Interior: hay que leerlas en origen.
- **Datos abiertos tal como se sirven en la web** (¿incluye el GeoJSON?): la web no es accesible desde la nube.
- El retraso del archivo diario (cron a las 05:17 UTC, runs observados entre las 13 y las 16 UTC) no lo investigué.

## 9. Objeciones (D-216)

1. **A D-188 («solo la versión vigente»):** vale para servir, no para conservar. Un proyecto que quiere ser citado
   necesita que lo publicado no se pueda pisar. La evidencia son los dos fallos del pin de la doble vuelta. No pido
   guardar todo: pido guardar lo que salió al público, que son decenas de megas.
2. **Al orden de D-178 y D-190:** borrar 4 GB para acercarse a un tramo gratuito de 10 GB que el propio cruce dice
   inalcanzable (quedan 12,3 GB) ahorra unos céntimos al mes y es la operación con más riesgo del plan. Propongo
   asumir el coste y borrar solo después del primer simulacro.
3. **A «motor repetible, no conservar resultados» (08-11):** cierto para lo intermedio. Pero «repetible» depende de
   conservar las entradas exactas y la versión del motor; con Deslinde 1.0, 1.1 y 1.2 en un mes, lo ya publicado solo
   se repite si se guardan fuentes, contrato y versión. Conservar entradas y publicado es lo que hace verdadera la regla.
4. **Al encargo:** «referente mundial» en este ámbito no se gana con más estructura interna sino con que alguien de
   fuera baje los datos y las fuentes y le cuadren. E-4 y E-5 pesan más para esa meta que la reordenación de R2.
