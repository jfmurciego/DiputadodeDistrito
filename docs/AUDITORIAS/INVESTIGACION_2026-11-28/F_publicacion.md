# T-509 · F · Publicación y visor

Fecha: 2026-11-28 · Ámbito: `p40-publicacion.yml`, `p90-automatico.yml` (pruebas por rama y medición), plan de corte a
Cloudflare (`REDISENO_R2.md`) y visor publicado (`visor/v4/`). Solo lectura. Detalle para la máquina: `F_publicacion.json`.

**Verificación independiente (28-11, contra `origin/main` 548968c47):** 10 hallazgos revisados (F-1 a F-10): 3 confirmados,
7 corregidos, 0 refutados. F-11 sin revisar. El texto ya lleva las correcciones; resumen en §8 y §9.

## 1. Veredicto

1. **Liga de hoy: segunda división.** En integridad juega arriba; en operación, abajo.
2. Lo bueno es raro de ver en un proyecto cívico: el sitio se monta entero antes de tocar nada, cada dato lleva sha256 y el
   visor lo comprueba en el navegador, Pages se despliega de una vez, no se carga nada de terceros y MapLibre va con `integrity`.
3. Lo malo: publicar una coma cuesta 17 min de máquina y una frase del propietario; 4 de las 18 publicaciones acabaron en
   rojo (22 %); no hay vuelta atrás; nadie comprueba qué ve el público después de desplegar.
4. **Dato grave, ya conocido (F-1; T-510 abierta el 28-11):** los pasos que suben la web y sus datos a R2 no han subido
   nada nunca. Datos: 11 de 11 publicaciones medidas; web: 9 de 9 (el paso existe desde el 23-11). 0 s, «sin R2_WEB_BUCKET:
   no se sube nada», y verde. La fila de T-430 del plan dice lo contrario (`PLAN.md:501`).
5. Consecuencia: el ensayo «en paralelo a Pages» en que se apoya el corte a Cloudflare no ha empezado. Y cuando empiece,
   la web en R2 saldrá sin datos mientras `mapa/datos.json` siga vacío (F-2): activarlo está apuntado y en espera desde
   el 23-11, pero ninguna comprobación lo exige.
6. El camino corto aprobado (D-194: publicar la web sola al fusionar, ~2 min) está inerte por la misma causa.
7. El visor es sólido por dentro (guarda de revisión, huellas, avisos), pero no tiene enlace por distrito, ni techo de
   peso en la CI (el de D-192 no está en ninguna prueba), ni telemetría de errores.
8. Para buscadores: título, canónica y tarjeta sí; robots.txt, mapa del sitio, 404 y datos estructurados no.
9. Seguridad: sin terceros y con SRI, pero sin política de contenido ni cabeceras. Pages no las admite; Cloudflare sí.
10. Nada de esto pide rehacer: son 11 hallazgos, 7 de ellos de esfuerzo S. El orden importa más que el esfuerzo.

## 2. Estado objetivo: referente mundial

- **Cada publicación es una versión inmutable con su dirección**, y producción es un puntero. Volver atrás es mover el
  puntero: un minuto, sin reconstruir. Así trabajan Netlify, Vercel (Instant Rollback) y Cloudflare Pages (Rollbacks).
- **Vista previa por PR** con el mismo artefacto que irá a producción (ya diseñada aquí: `pruebas.`).
- **La máquina comprueba lo público**: tras desplegar, pide la versión a la dirección real y un navegador abre el mapa.
- **Presupuesto de peso y Core Web Vitals en la CI** (Lighthouse CI; LCP ≤ 2,5 s, INP ≤ 200 ms, CLS ≤ 0,1; web.dev, 2024).
- **Una dirección por territorio y por distrito**, con su tarjeta al compartir (Dave's Redistricting, Districtr, el
  Atlas of Redistricting de FiveThirtyEight de 2018).
- **Cabeceras de seguridad con nota A** (OWASP Secure Headers, MDN HTTP Observatory) y errores del visor medidos.
- **Geometría pesada en teselas de un solo fichero** servidas por rangos desde R2 (PMTiles), no GeoJSON entero.

## 3. La secuencia real de una publicación (run 45900288067, «Solo el sitio», 26-11)

| # | Paso | Tiempo | Toca lo público | Si se corta aquí |
|---|---|---|---|---|
| 1 | `resolver`: qué 00 se publica | 20 s | no | nada cambia |
| 2 | `preparar`: estado operativo a `main` | 58 s | repo | queda un commit de estado; inocuo |
| 3 | Comprobación del registro vigente | 220 s | no | nada cambia |
| 4 | (con territorios) recuperar, acreditar y promover a blob | — | blobs en git | blobs sin registrar; inocuo |
| 5 | Comprobación del registro candidato | 219 s | no | nada cambia |
| 6 | Construir sitio, portadas V2-V4 | 176 s | no | nada cambia |
| 7 | Doble vuelta desde R2 (fijado) | 90 s | no | nada cambia (falló aquí el 19-11) |
| 8 | Validar (`test -s`, `grep`, `node --check`) | 18 s | no | nada cambia |
| 9 | Subir artefacto (295 MB) y esperar | 51 s | no | nada cambia |
| 10 | **`deploy-pages`** | 25 s | **web entera, de una vez** | o la vieja o la nueva (falló 2 veces el 24-11) |
| 11 | **Persistir registro** (push a `main`, 3 intentos) | <1 s | repo | **web nueva y registro viejo**: la siguiente «Solo el sitio» retira en silencio lo recién publicado |
| 12 | Datos de la web en R2 | 0 s (no hace nada) | — | cuando funcione: ficheros nuevos con índice viejo; el visor en R2 falla por huella; job en verde |
| 13 | Web en R2 | 0 s (no hace nada) | — | cuando funcione: recursos nuevos con páginas viejas, hasta 60 s o hasta la siguiente publicación |
| 14 | **Promover doble vuelta a `mapas/`** | 187 s | R2 `mapas/` | web desplegada y `mapas/` sin promover; job en rojo (pasó el 26-11) |
| 15 | Evidencia | 2 s | no | — |

**Atómico:** solo el paso 10. **No atómico:** 10→11 (web y registro), 12→13 (datos y web en dos buckets), 14 (va después
de lo público). **Vuelta atrás hoy:** ninguna directa. Repetir el job reconstruye desde `origin/main` (no restaura); el
artefacto de Pages dura 1 día. El camino real es revertir en `main` (PR + CI) y otra P40 con su frase: más de 40 min.

**Dato del 26-11 (entorno).** Dependen de variables que el job no ve: solo los pasos 12 y 13 (`p40:765-797`:
`vars.R2_WEB_BUCKET`, `vars.R2_SITIO_BUCKET`, secretos `R2_WEB_*` y `R2_SITIO_*`). Los pasos 4, 7 y 14 usan `R2_BUCKET`,
que sí llega (el log imprime `R2_BUCKET: ddd-research-archive`). En P90, `publicar_web` (`p90:1066-1116`) no declara
entorno y tampoco las ve. **Ya está en manos del propietario** (traspaso del Coordinador del 28-11, pendiente 2): a) copiar
las 2 variables y los 4 secretos al entorno `github-pages` o al repositorio (sin código); b) T-510, abierta el 28-11: la
subida a R2 en un job con el entorno `publicacion`. Objeción del autor a b): partir el job toca la atomicidad (T-379 2a, D-162).

## 4. Hallazgos (impacto tras la verificación; veredicto del revisor en cada título)

### F-1 · P40 nunca ha subido la web ni sus datos a R2 (impacto 4, esfuerzo S) · CORREGIDO
- **Hoy:** el paso de los datos, 11 de 11 publicaciones en 0-1 s y `conclusion=success`; el de la web, 9 de 9 (existe
  desde el 23-11). Log del job 140184639697: `R2_WEB_BUCKET:` y `R2_SITIO_BUCKET:` vacíos, secretos vacíos;
  «[datos_web] sin R2_WEB_BUCKET: no se sube nada»; «[sitio_r2] sin R2_SITIO_BUCKET: no se sube nada».
- **Ya previsto:** T-510 (abierta el 28-11) y pendiente 2 del propietario en el traspaso del Coordinador (§3). No es nuevo.
- **Por qué importa:** no hay ensayo en paralelo; la fila de T-430 en `PLAN.md:501` («P40 ya sube la web a R2») es falsa;
  el fallo es mudo (`continue-on-error` y salida 0), y lo seguirá siendo con un fallo real. Lo público no está
  afectado (Pages sigue sirviendo): por eso el impacto baja de 5 a 4.
- **Propongo (lo que T-510 no dice):** que cubra también `publicar_web` de P90; una línea fija en el resumen del job
  («Web en R2: N subidos / NO SUBIDA: motivo») con `::warning` en `main` si falta la variable; corregir la fila de T-430.
- **Aceptación:** tras una P40 desde `main`, el log imprime «[sitio_r2] N ficheros; M a subir» con N>0 y
  `_sitio/actual.json` lleva el `p40_run` de ese run; un test exige en los YAML la línea de resumen y el `::warning`.
- **Riesgo:** la primera subida real (≈2.000 ficheros, ≈295 MB) puede tardar y destapar errores hoy invisibles.

### F-2 · Requisito del corte sin guarda: `mapa/datos.json` sigue vacío (impacto 3, S) · CORREGIDO
- **Hoy:** `visor/v4/mapa/datos.json` = `{"actual": ""}`. `publicar_sitio_r2.py` sube el sitio sin los árboles de datos
  y no toca ese fichero; solo `pruebas_web_r2.py:74` lo escribe, para la vista de pruebas. En R2 el mapa pediría
  `../v2/datos/provincias.json`, recibiría 404 y diría «No es posible inicializar el visor».
- **Ya previsto:** activarlo está apuntado y en espera desde el 23-11 (traspaso del Coordinador: «cuando `ddd-web-datos`
  tenga datos»); depende de F-1. Lo que no existe es una comprobación que pare un corte con el fichero vacío.
- **Opciones:** (a) la prevista: fijar la dirección en el fichero del repo (también la usa Pages); (b) que solo el
  montaje para R2 la escriba desde `DATOS_WEB_ACTUAL`. En las dos, la subida a R2 avisa (y tras el corte falla) si queda vacía.
- **Aceptación:** prueba Node con `fetch` simulado sobre el árbol que sube `publicar_sitio_r2.py` y un índice simulado:
  hay distritos y no hay aviso; test Python: con `actual` vacío la herramienta avisa (y sale ≠ 0 en modo producción).

### F-3 · No hay vuelta atrás de una publicación (impacto 4, M) · CORREGIDO
- **Hoy:** ver §3. En R2 («solo la vigente», D-188) los ficheros se pisan con el mismo nombre; no queda versión
  anterior. Durante la subida, un visitante con el índice viejo recibe ficheros nuevos y el visor falla por huella.
  Coincide con E-3 (almacén); aquí se mide el efecto en el visitante y en el tiempo de retirada.
- **Propongo, en dos partes:** Pages, mientras viva (no toca decisiones): `retention-days: 14` y un modo de P40 que
  vuelva a desplegar un artefacto anterior (por verificar cómo: `deploy-pages` toma el del propio run). R2: claves por
  versión (`web/v/<version>/…`), `actual.json` como único puntero, 3 versiones y orden `revertir`. **La parte de R2 va
  contra D-188** (propietario, 20-11): solo se puede hacer si la reabre.
- **Aceptación:** test con R2 simulado: publicar A, publicar B, `revertir` deja los índices de A byte a byte sin
  reconstruir; durante la subida de B un cliente con el índice de A solo lee ficheros de A. El tiempo real (objetivo:
  menos de 2 min) se mide en un simulacro en `nueva.`, no en el test.

### F-4 · 4 de 18 publicaciones en rojo y nada comprueba lo público (impacto 3, M) · CORREGIDO
- **Hoy:** los 4 rojos: `deploy-pages` (2; arreglado en 1.7.0, T-454); doble vuelta antes de desplegar (1, 19-11,
  `ID_FUERA_DE_RANGO: nac02`: un dato malo parado a tiempo) y promoción después de desplegar (1, run 45873075949,
  `INFORME_SHA256_DISTINTO` en el informe de las autonómicas): web desplegada, `mapas/` sin promover, job en rojo.
  Dos runs tienen segundo intento; uno es ya uno de los 4 rojos: 5 de 18 con algún problema. Antes de desplegar, la
  huella del informe se comprueba contra la copia ya promovida; el candidato de `interno/` solo se mira al promover.
  La validación previa no abre un navegador. `evaluar_publicacion_visor.py` no hace ninguna petición a la web.
- **Impacto, de 4 a 3:** de los 4 rojos, 2 están arreglados, 1 fue la guarda funcionando y 1 dejó lo público coherente.
- **Propongo:** (1) comprobar la huella del informe fijado antes de `deploy-pages`; (2) humo con navegador sobre el
  sitio candidato; (3) `version.json` en el sitio y, tras desplegar, pedirlo a la dirección pública hasta que coincida.
- **Aceptación:** el caso del 26-11 repetido en simulación falla antes de desplegar; un `throw` en `explorar.js` en una
  rama pone el humo en rojo; el log de una P40 real imprime «version.json público = <run>».

### F-5 · Al plan de corte a Cloudflare le faltan siete piezas y dos están a medias (impacto 4, M) · CORREGIDO
1. **Regla de carpetas (a medias):** el texto de las dos reglas se envió al Planificador el 26-11 (traspaso del 28-11),
   pero no está en el repo ni tiene prueba. Tres casos: `/mapa/`, `/mapa` y `/docs/citar.html`.
2. **404:** no hay `404.html`; R2 da un texto técnico en inglés.
3. **`www.`:** el plan conecta los dos dominios al bucket (contenido doble). Mejor redirigir a uno.
4. **`github.io`:** `CITATION.cff:20` y otros 8 ficheros (2 de ellos, salidas históricas) apuntan a
   `jfmurciego.github.io/DiputadodeDistrito/`. Al retirar Pages mueren y no se pueden redirigir desde fuera. Opción para
   el propietario (cambia D-194): Pages no se apaga; queda con una página que lleva al dominio.
5. **Vuelta atrás:** §3.4 («1 minuto, Pages sigue desplegado») choca con §7 paso 10 (quitar el dominio propio en
   Pages). Y desde que `publicar_web` publique solo en R2, Pages queda atrasada: volver es volver a una web vieja.
6. **Caché:** 60 s para todo, también para `v2/vendor/maplibre-gl/5.7.0/` (939 KB, nombre con versión). La marca de
   contenido de §1.2.4 no está hecha. No hay regla de borde: Cloudflare no guarda HTML ni JSON por defecto (de memoria).
7. **Cabeceras de seguridad:** ver F-10.
8. **`nueva.`** no lleva `noindex` (solo `pruebas.`): contenido doble indexable durante el ensayo.
9. **Umbrales (a medias):** retirar Pages tiene criterio («dos semanas sin incidencias», D-194) sin definir qué es una
   incidencia; «listo para cortar» tiene la lista del ensayo (§3.2) sin umbrales.
- **Propongo:** una lista de corte de una página y un guion de solo lectura que recorra 20 direcciones en `nueva.`.
- **Aceptación:** `python herramientas/comprobar_corte.py --base https://nueva.diputadodedistrito.es` devuelve 0;
  simulacro de vuelta atrás cronometrado y anotado.

### F-6 · El mapa no tiene enlace por territorio ni por distrito (impacto 4, M) · CONFIRMADO
- **Hoy:** `explorar.js:118` lee solo `regla`; la l. 312 escribe `?regla=` pisando lo demás. `DV.leerEnlace` ya
  devuelve `territorio` (`dv.js:113`) y nadie lo usa. La imagen al compartir es una para todo el sitio.
- **Propongo:** estado en la dirección (`?t=nac28&d=7&capa=…&regla=…`) y botón «Copiar enlace». Página por territorio
  con su tarjeta: opción aparte, a decidir.
- **Aceptación:** prueba Node: abrir con `?t=nac28&d=7&regla=dos` restaura provincia, distrito y regla; un código
  inexistente da vista nacional y aviso, sin excepción.

### F-7 · Un fallo de red pasajero se muestra como «provincia sin distrito certificado» (impacto 3, S) · CONFIRMADO
- **Hoy:** la provincia que falla entra en `D.districtFailures` y no se reintenta (`explorar.js:525-526`); el aviso
  (l. 601-602) dice «sin distrito certificado», que es falso. Igual en la doble vuelta (l. 237, 242). Ningún `fetch`
  tiene tiempo límite. `map.on("error")` solo escribe en consola. No hay `window.onerror` ni `unhandledrejection`.
- **Propongo:** separar «no publicado» de «no se pudo cargar» (con Reintentar), límite de 20 s y aviso de error al
  contador propio, sin datos personales.
- **Aceptación:** prueba Node: `fetch` falla una vez y luego responde → tras Reintentar se pinta; el texto no contiene
  «certificado».

### F-8 · El tope de 100 KB de D-192 no está en ninguna prueba (impacto 3, S) · CORREGIDO
- **Hoy:** 0 topes en los 12 `tests/test_visor_v4*`. La vista rápida del móvil no existe en el mapa. Peso comprimido
  al abrir `mapa/`, medido en el repo: 465 KB (MapLibre 247,2; provincias 102,7; comunidades 46,5; JS propio 39,1; CSS
  21,3; HTML 5,4; puntos 2,8), más el índice (20,6) y cuatro ficheros sin medir. El JS propio pasó de 81,0 KB (T-441,
  22-11) a 113,4 KB en seis días (+40 %, con `puntos.js`). T-441 consta HECHA: era el diseño.
- **Matiz (D-192):** la carga ligera del mapa va «con la web nueva», tras el corte; que falte hoy no incumple la
  decisión. Lo que falta es la tarea que la haga y un techo que impida crecer mientras tanto.
- **Propongo:** una prueba en el job `web` con un techo que solo baja; tarea explícita para la vista rápida.
- **Aceptación:** `tests.test_visor_v4_peso` falla al añadir 30 KB a `explorar.js`.

### F-9 · P40 tarda 17 min y 7 se van en dos pasadas de la misma comprobación (impacto 2, S) · CORREGIDO
- **Hoy:** en «Solo el sitio» no hay entradas nuevas y aun así el registro se materializa y comprueba dos veces: 220 s +
  219 s (y 180 s + 193 s en el run anterior). Sobra una pasada: unos 3,5 min. Job completo: 1.014 s (entre 565 y
  1.635 s en 11 runs correctos). Artefacto: 294.807.655 bytes.
- **Impacto, de 3 a 2:** ahorra de 3,5 a 6,5 min en un flujo manual; el atajo de verdad para un texto es `publicar_web` (F-1).
- **Propongo:** si el registro candidato es byte a byte el vigente, reutilizar lo materializado; promover a `mapas/`
  solo si el fijado cambió.
- **Aceptación:** sin cambios de datos, la segunda comprobación dura menos de 15 s y lo dice en el log, y promover dura
  menos de 30 s si el fijado no cambió; con una entrada nueva, las dos comprobaciones siguen corriendo.

### F-10 · Sin política de seguridad de contenido ni cabeceras (impacto 3, S) · CONFIRMADO
- **Hoy:** ninguna página ni herramienta las pone; hay un script en línea (`mapa/index.html:95`). A favor: cero
  terceros (dominios: los propios, más enlaces a LinkedIn, ORCID y DOI) y SRI en MapLibre.
- **Propongo:** una regla de cabeceras en Cloudflare (HSTS, nosniff, Referrer-Policy, Permissions-Policy, CSP con
  `worker-src blob:`), primero en modo informe; mover el script en línea a un fichero.
- **Aceptación:** `curl -sI` muestra las cinco cabeceras; nota A en MDN HTTP Observatory.

### F-11 · Faltan robots.txt, mapa del sitio, 404 y datos estructurados (impacto 2, S) · sin revisar
- **Hoy:** título, descripción, canónica, 9 `og:*` y 5 `twitter:*` en la portada (bien, T-451). Nada de lo otro.
- **Propongo:** P40 genera los tres ficheros; JSON-LD `Dataset` en datos abiertos y `WebSite` en la portada.
- **Aceptación:** la validación del sitio candidato los exige; el mapa del sitio lista todas las páginas públicas.

## 5. Camino en tres pasos

| Cuándo | Qué | Prueba |
|---|---|---|
| **Esta semana** | F-1 (T-510 o copiar variables y secretos; línea en el resumen), F-2 (activar `datos.json` y su guarda), F-4.1 (huella del informe antes de desplegar), F-7 | Una P40 imprime «N ficheros; M a subir» con N>0; `nueva.` pinta distritos; el caso del 26-11 falla antes de desplegar |
| **Este mes** | F-5 (lista y guion de corte, con simulacro de vuelta atrás), F-4.2 y F-4.3 (navegador y `version.json`), F-8, F-9, F-10 en modo informe, F-11; el corte | `comprobar_corte.py` en verde en `nueva.` y en el dominio real; segunda comprobación de P40 en segundos cuando no hay cambios; techo de peso en la CI |
| **Este trimestre** | F-3 (versiones inmutables y `revertir`, si el propietario reabre D-188), F-6 (enlace por distrito), vista rápida del móvil, CSP en firme | `revertir` sin reconstruir, cronometrado en un simulacro; `?t=…&d=…` restaura el estado; primera vista del mapa ≤ 100 KB en el móvil |

## 6. Lo que no pude comprobar

- **Dónde están las variables y secretos de R2.** La API de entornos, variables y secretos da 403 desde la nube. Sé que
  el job no las ve (log); que estén en `publicacion` lo dicen `docs/ESTADO.md:110` y el traspaso del 28-11. Lo comprueba
  el propietario en Settings → Environments.
- **El «rojo» del ensayo de Cloudflare.** En los 18 runs de P40 esos dos pasos nunca salen en rojo: salen en verde sin
  hacer nada. Si hubo un rojo, fue en otro sitio (¿una prueba a mano?). Conviene aclararlo.
- **`publicar_web` y `pruebas_web` en runs reales.** Lo de `publicar_web` es deducción (un job sin entorno ve menos
  que uno con entorno). Se comprueba en el log de un push a `main` que solo toque `visor/v4/`. De `R2_PRUEBAS_BUCKET` no sé nada.
- **La web pública.** `diputadodedistrito.es` da 403 por el proxy de la sesión: no medí cabeceras reales, compresión,
  Core Web Vitals ni si Cloudflare añade algo. Se mide con `medir-web` de P90 o desde un navegador.
- **Lo de Cloudflare** (reglas del plan gratuito, caché por extensión, compresión de `.geojson`) y las referencias
  externas van de memoria; no se abrieron desde la nube.
- **Peso de los datos al abrir** (registro del visor, procedencia, territorial, índices): no están en el repo.
- **Fallo del push del registro tras desplegar** (paso 11): leído en el código; 0 casos en 18 runs.

## 7. Objeciones

- **«En paralelo a Pages» con `continue-on-error` y salida 0 si falta la variable** fue una decisión prudente que ha
  salido cara: ha tapado cinco días que la migración no avanzaba. Un ensayo debe poder fallar a la vista.
- **«Solo la vigente» (D-188)** ahorra espacio y quita la vuelta atrás. Guardar tres versiones cuesta menos de 1 GB.
- **Retirar Pages a las dos semanas (D-194, pregunta 8):** propongo no apagarla nunca del todo, sino dejarla
  redirigiendo; es gratis y salva las direcciones `github.io` ya citadas.
- **La frase del propietario para cada publicación** protege de publicar de más, pero no de publicar mal: eso lo
  protege una comprobación automática de lo público (F-4), que hoy no existe.

## 8. Verificación independiente (28-11)

Cada evidencia se ha repetido contra `origin/main` (548968c47) y la API de GitHub en solo lectura.

| Id | Veredicto | Impacto | Qué cambia |
|---|---|---|---|
| F-1 | CORREGIDO | 5 → 4 | Ya es T-510 y pendiente del propietario; datos 11/11 y web 9/9; lo público no está afectado |
| F-2 | CORREGIDO | 4 → 3 | La activación ya estaba apuntada (23-11); lo nuevo es la guarda; criterio sin Playwright |
| F-3 | CORREGIDO | 4 | La parte de R2 va contra D-188; duración de 565 a 1.635 s en 11 runs; el tiempo se mide en simulacro |
| F-4 | CORREGIDO | 4 → 3 | Sin «segunda vez» ni «otros 2»; el 19-11 fue un dato malo parado a tiempo |
| F-5 | CORREGIDO | 4 | Siete piezas y dos a medias; 9 ficheros con `github.io`; dejar Pages viva cambia D-194 |
| F-6 | CONFIRMADO | 4 | — |
| F-7 | CONFIRMADO | 3 | Enviar errores al contador amplía D-101: esa parte la decide el propietario |
| F-8 | CORREGIDO | 3 | D-192 deja el mapa ligero para «la web nueva»: no es incumplimiento, es trabajo sin tarea |
| F-9 | CORREGIDO | 3 → 2 | Sobra una pasada (3,5 min), no 7; «≤ 10 min» no era comprobable |
| F-10 | CONFIRMADO | 3 | Las cabeceras reales solo se pueden leer fuera de la nube |
| F-11 | sin revisar | 2 | — |

## 9. Descartados en la verificación

Ningún hallazgo queda refutado entero. Afirmaciones retiradas del texto por no reproducirse:

- **«Segunda vez del mismo orden roto (P75 → fijado → P40)» (F-4).** El fallo del 19-11 (run 44615106125) fue
  `ID_FUERA_DE_RANGO: nac02: district_id no numérico`, otra causa. Del orden roto solo consta el 26-11.
- **«Otros 2 runs necesitaron segundo intento» (F-4).** Hay dos runs con segundo intento, pero uno (45382628274) es ya
  uno de los 4 rojos.
- **«11 de 11» para el paso «Web en R2» (F-1).** Ese paso existe desde el 23-11: son 9 de 9. El de los datos sí, 11 de 11.
- **«Dato nuevo» (F-1).** Constaba ya en `docs/ESTADO.md:110` y en el traspaso del Coordinador del 28-11, con T-510 abierta.
- **«Nadie lo escribe» como hueco desconocido (F-2).** La activación estaba apuntada y en espera desde el 23-11.
- **«Nueve piezas» y «7 ficheros» (F-5).** Son siete y dos a medias; los ficheros con la dirección `github.io` son 9.
- **«Entre 602 y 1.635 s en seis runs» (F-3, F-9).** En los 11 runs correctos consultados: de 565 a 1.635 s.
- **«P40 ≤ 10 min» como criterio (F-9).** Con los dos ahorros, el run medido quedaría en 608 s.
