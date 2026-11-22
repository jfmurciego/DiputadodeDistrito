# T-445 · Repositorio público aparte, solo de publicación — diseño (solo documento)

VERSIÓN: 1.0.0 · FECHA: 2026-11-22 · ESTADO: candidato (espera aprobación del propietario) · ANTERIOR: ninguna (fichero nuevo)

**Encargo.** T-445 (D-193, propietario, 22-11, vía Planificador): el código de Deslinde (`paquetes/deslinde/`, 30 ficheros, y su
historial) es público aunque D-94 lo declara privado. Secuencia: (1) T-430b, la web desde R2 y Cloudflare, sin GitHub Pages;
(2) **T-445**, un repositorio público aparte, solo de publicación; (3) el propietario pone este repositorio en privado;
(4) T-446, comprobación de que no queda código público. Este documento solo diseña: no hay código, ni lanzamientos, ni
publicación. Referencias: `docs/PLAN.md` «Plan por fases del repositorio privado» (T-273, T-275, T-276, T-283), D-91 a D-95,
inventario T-272 (rama `t272-frontera-inventario`), T-430b (`docs/ESTUDIOS/T430_WEB_EDITABLE/REDISENO_R2.md`, rama `t430b-rediseno-r2`).

**Datos externos.** Lo que dependa de GitHub o de Zenodo y no esté comprobado en este repositorio lleva «por verificar»: se
comprueba en el ensayo (§8, paso 4) antes del paso a privado.

## 1. Qué cambia respecto al plan del 14-11

| Tarea del 14-11 | Qué decía | En este diseño |
|---|---|---|
| T-273 | contenido inicial por lista blanca, generado por script | se mantiene (§3, §4) |
| T-275 | la P50 escribe en el público con un token de solo ese repo; `publicaciones_visor.json` apunta al público | lo primero se mantiene (§4.2); lo segundo **no hace falta**: el registro y sus blobs se quedan en el privado y solo los lee la P40, que corre en el privado (§6) |
| T-276 | Zenodo solo mapas, desde el público | se mantiene, **por la API** como hoy (P50 1.2.1), no por la integración GitHub–Zenodo (§5) |
| T-283 | Pages y el dominio desde el público | **sustituida** por T-430b: la web va a R2, no a Pages; el público no sirve web |
| T-282 | visor sin `ddd_ensemble`, validador con esquema | **no hace falta**: el público no lleva código ni CI |

## 2. Nombre y estructura

**Nombre recomendado:** `jfmurciego/diputadodedistrito-mapas` (pregunta 1). Dice lo que contiene y no se confunde con el de trabajo.

```
diputadodedistrito-mapas/
├── README.md               # qué es, cómo citar (DOI de concepto), cómo verificar sha256, sin valor oficial
├── LICENSE                 # CC BY 4.0 (texto íntegro: docs/zenodo/LICENCIA_CC-BY-4.0.txt)
├── CITATION.cff            # type: dataset; DOI de concepto 10.5281/zenodo.24093967; repository: este repo
├── NOTA_FUENTES.md         # INE e Interior (docs/zenodo/NOTA_FUENTES.md)
├── mapas/
│   ├── MAPAS.json          # el de la última Release (territorios, versión, sha256 de cada paquete)
│   └── SHA256SUMS
└── datos_abiertos/         # árbol de datos_abiertos/ (INDEX.json, <id>/index.html, distrito-N.html, resultados.csv)
```

- **Sin `.github/`**: ni workflows, ni Actions, ni runner (D-93: ningún runner propio en un repositorio público). El público no
  ejecuta nada; solo recibe commits del puente.
- **Los paquetes de mapas no van al árbol git**: van como assets de la Release `mapas-vX.Y.Z` (como hoy). En git solo
  `MAPAS.json` y `SHA256SUMS`, para que el árbol diga qué hay en cada versión.
- **Los GeoJSON M06** (~50 MB, hoy fuera de git) tampoco: ya viajan dentro de cada paquete de la Release.
- **Sin `legacy/` ni cabeceras VERSIÓN**: el público es salida generada; la versión es la de `MAPAS.json` y la historia es la del
  propio git del público (pregunta 5).
- **`.zenodo.json` no**: solo lo lee la integración GitHub–Zenodo, que no se usa (§5). Los metadatos salen de
  `herramientas/zenodo_deposito.py` como hoy. Si se quiere por documentación, se genera igual que `CITATION.cff` (pregunta 4).

## 3. Lista blanca exacta

Fichero nuevo en el privado, `configuracion/lista_blanca_publico.yaml` (versionado). Cada entrada: ruta en el público ← origen en
el privado. **Todo lo que no esté aquí no sale.**

| Ruta en el público | Origen (privado) | Tipo admitido |
|---|---|---|
| `README.md` | plantilla `docs/publico/README.md` (nueva) | `.md` |
| `LICENSE` | `docs/zenodo/LICENCIA_CC-BY-4.0.txt` | texto |
| `NOTA_FUENTES.md` | `docs/zenodo/NOTA_FUENTES.md` | `.md` |
| `CITATION.cff` | plantilla `docs/publico/CITATION.cff` (nueva; `type: dataset`, sin `repository-code`) | `.cff` |
| `mapas/MAPAS.json`, `mapas/SHA256SUMS` | salida de la P50 de esa versión | `.json`, texto |
| `datos_abiertos/**` | `datos_abiertos/` | `.json`, `.csv`, `.html` |

**Guardas del puente** (fallan cerradas, con test):
1. Cada fichero del árbol generado casa con una entrada; si sobra uno, se para.
2. Prefijos prohibidos aunque alguien los añada a la lista: `paquetes/`, `modulos/`, `ddd_core/`, `ddd_motor2/`, `ddd_ensemble/`,
   `herramientas/`, `g10/`, `.github/`, `.claude/`, `docs/`, `legacy/`, `tests/`; extensiones prohibidas: `.py`, `.sh`, `.yml`, `.yaml`,
   `.ipynb`, `.js` (el HTML de `datos_abiertos` no lleva scripts: se comprueba que no haya `<script`).
3. **Contenido de cada paquete de la Release** (lección del incidente del 20-11, T-434): se lista cada `ddd-*-v*.tar.gz` y solo se
   admiten `.geojson`, `.csv`, `.json`, `.md`, `.txt`; un paquete por territorio de `MAPAS.json`, nunca un glob del árbol.
4. Texto: sin `session_01`, sin `/Users/`, sin correos personales (lo que T-272 §5 encontró en el privado).
5. Tope de tamaño (p. ej. 20 MB el árbol git) y árbol armado en `$RUNNER_TEMP`, nunca en el directorio del repositorio.

Enlaces al repositorio de trabajo que hay que cambiar en lo que sale (`github.com/jfmurciego/DiputadodeDistrito`): la atribución de
`herramientas/generar_datos_abiertos.py` (`INDEX.json` y páginas HTML), `zenodo_deposito.py` (`VISOR` y la URL de la Release) y la
plantilla de `CITATION.cff`. Pasan a la web (`diputadodedistrito.es`) o al repo público. La guarda 4 añade: ningún enlace al
repositorio de trabajo.

## 4. Cómo publica la P50 en el público

### 4.1 Credencial mínima

**Recomendado: una GitHub App nueva, `ddd-publicador`**, instalada **solo** en `diputadodedistrito-mapas`, con un único permiso:
`contents: write` (commits, etiquetas y Releases). Sus `APP_ID` y clave privada van como secretos del entorno `publicacion` del
privado (que ya solo admite `main`). El token se emite en el job con `actions/create-github-app-token` (versión fija por sha),
`repositories: diputadodedistrito-mapas`, y caduca en una hora.

| Opción | A favor | En contra |
|---|---|---|
| **App nueva solo en el público** (recomendada) | si la clave se filtra, solo alcanza el público; no caduca; los commits salen como el bot, sin correo personal | el propietario crea una app (5 min) |
| Reusar `ddd-registro` instalándola también en el público | nada que crear | su clave pasa a poder escribir en los dos repositorios |
| Token fine-grained del propietario | sencillo | caduca (máx. 1 año, por verificar), va ligado a la persona y sus commits llevan su identidad |

### 4.2 Pasos nuevos de la P50 (1.3.0)

Solo con destino **Zenodo** (el real). Con destino **prueba** no se escribe nada en el público (lección del 20-11): el árbol armado y
el informe de las guardas salen como artefacto del run, para revisarlos.

1. **Resolver** (como hoy) pero leyendo las etiquetas `mapas-v*` **del público** (con el token de la app, solo lectura del contenido):
   la serie de versiones vive allí.
2. **Armar** el árbol de la lista blanca en `$RUNNER_TEMP` con `herramientas/puente_publico.py` (nuevo) y pasar las guardas de §3.
3. **Commit** en `main` del público: un único commit «mapas vX.Y.Z» con el árbol completo (sustituye lo anterior; lo que sale de la
   lista se borra), autor el bot de la app.
4. **Release** `mapas-vX.Y.Z` en el público, sobre ese commit, con los paquetes, `SHA256SUMS` y `MAPAS.json`.
5. **Zenodo** (job `zenodo`, sin cambios de fondo): baja el lote de la Release del público y deposita por la API con
   `--repo jfmurciego/diputadodedistrito-mapas` → los enlaces del depósito apuntan al público.

**P40:** no escribe en el público (recomendado, pregunta 6). El público es la instantánea académica de cada versión de mapas; la web
viva sale de R2 (T-430b) y ya muestra cada regeneración. Así hay un solo escritor (la P50) y una versión del público por versión de
Zenodo. Si el propietario quiere `datos_abiertos/` al día entre versiones, la P40 añadiría el paso 3 solo para esa carpeta.

### 4.3 Atestación (Sigstore)

Hoy la P50 firma cada paquete con `actions/attest-build-provenance` y la nota de la Release dice «verificar con `gh attestation
verify … --repo`». Con el privado en privado, esa atestación queda en el privado y nadie de fuera puede verificarla (por verificar
cómo se ve una atestación de repositorio privado). Opciones (pregunta 7):
- **A (recomendada)**: dejar de atestar; la verificación pública es `SHA256SUMS` + la suma que guarda Zenodo de cada fichero. La nota
  de la Release lo dice.
- B: seguir atestando en el privado, sin valor para terceros.

## 5. Zenodo: integración, concepto y sin concepto nuevo

- **Por la API, no por la integración.** La P50 ya deposita con `zenodo_deposito.py` («sin integración GitHub–Zenodo»), abriendo
  **versión nueva** del registro `24093968` (`CONCEPTO_REAL`), que cuelga del concepto **10.5281/zenodo.24093967**. Cambiar de
  repositorio solo cambia `--repo` y los enlaces: el concepto se conserva solo, sin tocar nada en Zenodo.
- **La integración GitHub–Zenodo no se activa en el público**: la integración abre un concepto por repositorio en su primera Release
  (por verificar que no admite enlazarse a un concepto existente), es decir, un concepto nuevo, que D-193 excluye; y además
  depositaría dos veces cada versión (integración + API). Se mantiene desactivada también en el privado (paso del propietario del 20-11).
  La pregunta 3 deja constancia por si el propietario la quería expresamente.
- **Depósitos ya publicados.** `10.5281/zenodo.24448721` (mapas 1.0.0, tag `mapas-v1.0.0`) y `10.5281/zenodo.24093968` (Huesca 1.0.0)
  enlazan a Releases del repo de trabajo, que serán 404 al pasar a privado. Se corrige editando **solo los metadatos**
  (`related_identifiers` y descripción) de esos registros por la API: no cambia el DOI ni crea versión (por verificar que Zenodo
  admite esa edición en registros publicados sin abrir versión). Lo hace una opción nueva de la P50, «Actualizar enlaces de los
  depósitos», con `ZENODO_TOKEN` y frase del propietario al Operador.
- La copia de Zenodo del 9-11 que contiene código es T-284 (retirada), no esta tarea.

## 6. Qué deja de leerse cuando este repositorio sea privado

| Lector | Qué lee hoy de aquí | Tras el paso a privado | Qué hace falta |
|---|---|---|---|
| Web/visor público | Pages de este repo | sin Pages (T-430b): R2 | T-430b en verde **antes** (orden §8) |
| Web: Explorar | `datos.diputadodedistrito.es/web/actual/` (R2) | igual | nada |
| P40 (en el privado) | blobs de `publicaciones_visor.json` (481 filas `github-git-blob://`), assets de Releases, artefactos | igual: el `GITHUB_TOKEN` del propio repo los lee aunque sea privado | nada; `publicaciones_visor.json` **no** se toca (T-275 parcial queda sin efecto) |
| P10, 03, hemiciclo | Release `fuente-infoelectoral-02202307`, artefactos | igual (mismo repo) | nada |
| Sesiones cloud (`gh api` de blobs y assets) | con token | igual, con el token de la sesión (por verificar en la primera sesión tras el cambio) | nada |
| Público: enlaces a `github.com/jfmurciego/DiputadodeDistrito` | README, `CITATION.cff`, `datos_abiertos/INDEX.json` y HTML, `dashboard/` (enlaces a runs), `documentacion_publica/` (citar, fuentes con enlace a blob), V2/V3 congeladas | 404 | reescribir a la web o al público en lo que se publica (§3); las V1-V3 congeladas: un cambio de texto de los enlaces en el montaje de la P40 (pregunta 8) |
| Zenodo 24448721 y 24093968 | enlace a Releases de aquí | 404 | §5, editar metadatos |
| `raw.githubusercontent.com` | ningún lector en `visor/v4`, `dashboard`, `datos_abiertos` (búsqueda del 22-11) | — | la guarda 4 lo impide en lo nuevo |
| Actions | minutos gratis de repositorio público (CLAUDE.md: 0 min facturables) | **se facturan** los minutos de repositorio privado por encima del cupo (por verificar el cupo del plan) | riesgo R1; lo resuelve el runner propio (T-274, D-93), fuera de esta tarea |

## 7. Releases y etiquetas de este repositorio

| Release / tag | Qué es | Propuesta |
|---|---|---|
| `mapas-v1.0.0` (73 assets) | mapas 1.0.0, depositada en Zenodo (24448721) | **copiar** al público con los mismos ficheros y sha256 (sin el tarball de Deslinde, ya borrado), sobre el commit inicial; en el privado se queda (invisible) |
| `mapa-congreso_huesca-v1.0.0` | primera versión de la serie (24093968) | **copiar** al público igual |
| `fuente-infoelectoral-02202307`, `fuente-ensayo-congreso-2026-11-29` | espejos de fuentes que usan los workflows | se quedan en el privado; no son publicación |
| `almacen-m06-*` (6 borradores), `ensemble-congreso-*` (3 borradores) | internos | se quedan; su borrado es T-285 |

La copia la hace una opción de la P50 «Copiar Releases existentes al público» (una sola vez; comprueba el sha256 de cada asset antes y
después; idempotente si la Release ya existe con los mismos ficheros). Al ser una publicación, la lanza el Operador con frase del
propietario.

## 8. Orden

1. Propietario: aprueba este diseño (preguntas de §10).
2. Propietario: crea `diputadodedistrito-mapas` vacío y público, crea la app `ddd-publicador` (solo `contents: write`, instalada solo
   ahí) y guarda `DDD_PUBLICADOR_APP_ID` y `DDD_PUBLICADOR_KEY` en el entorno `publicacion`. Protección de `main` del público: sin
   push salvo la app (por verificar si el plan lo permite en un repo personal; si no, basta con no dar acceso a nadie más).
3. Implementador (una PR, `no-automerge`): lista blanca, `puente_publico.py` con sus guardas y tests (incluido uno que mete un `.py`
   y un `paquetes/` y debe fallar), P50 1.3.0 (pasos de §4.2, opciones de §5 y §7), plantillas de README y CITATION, enlaces de
   §3. Test de que el público no recibe nada con destino prueba.
4. Operador, con frase del propietario: P50 destino **prueba** (árbol como artefacto, sin escribir en el público); revisión del
   árbol. Después «Copiar Releases existentes al público» (crea el commit inicial y las dos Releases) y «Actualizar enlaces de los
   depósitos».
5. T-430b en verde (web servida desde R2, Pages retirado) y enlaces públicos reescritos.
6. Propietario: pone `DiputadodeDistrito` en privado.
7. T-446: comprobación desde fuera (sin sesión) de que no queda código público: el público solo con la lista blanca, las Releases
   sin código (contenido de cada tarball), Zenodo sin enlaces rotos, la web sin enlaces al repo de trabajo.

## 9. Riesgos

| Riesgo | Mitigación |
|---|---|
| R1. Minutos de Actions facturados al pasar a privado (hoy repo público, 0 min) | medir antes del paso 6 el consumo semanal; runner propio (T-274) o cupo; decisión del propietario, fuera de T-445 |
| R2. Sale código por un glob o un paquete mal armado (incidente del 20-11) | lista blanca + prefijos y extensiones prohibidos + listado de cada tarball; prueba sin escritura pública |
| R3. La integración GitHub–Zenodo se activa por error en el público y abre un concepto nuevo | no se activa; T-446 comprueba en Zenodo que el público no está enlazado |
| R4. La clave de la app se filtra | solo alcanza el público (sin código); se revoca y se crea otra |
| R5. Enlaces rotos en lo ya publicado (Zenodo, webs ajenas que enlazan al repo) | metadatos de Zenodo corregidos (§5); README del público explica el cambio; lo ajeno no se controla |
| R6. Lo que ya fue público sigue en forks, cachés o Software Heritage (D-95) | no lo resuelve el paso a privado; T-284 y T-446 lo anotan |
| R7. Al poner en privado, GitHub corta los forks públicos existentes de él (por verificar el comportamiento actual) | se anota en T-446; no afecta al público nuevo |
| R8. Sesiones cloud o la app `ddd-registro` pierden acceso al pasar a privado | ensayo en la primera sesión tras el paso 6; la app ya está instalada en este repo (por verificar que conserva permisos) |

## 10. Preguntas al propietario

1. **Nombre del repositorio público.** Recomiendo `jfmurciego/diputadodedistrito-mapas`. Alternativa: `jfmurciego/deslinde-mapas`.
2. **Credencial.** Recomiendo una app nueva `ddd-publicador`, solo en el público y solo `contents: write` (§4.1). Alternativas: reusar
   `ddd-registro` o un token fine-grained.
3. **Zenodo por la API, sin integración GitHub–Zenodo.** Recomiendo mantener la API (conserva el concepto 10.5281/zenodo.24093967 sin
   tocar nada) y no activar la integración en el público, porque abriría un concepto nuevo (§5). ¿Conforme?
4. **`.zenodo.json`.** Recomiendo no incluirlo (sin integración no lo lee nadie; los metadatos salen de `zenodo_deposito.py`). ¿O se
   incluye como documentación?
5. **Gobernanza en el público.** Recomiendo sin `legacy/` ni cabeceras VERSIÓN: es salida generada, la versión es la de `MAPAS.json`.
6. **¿Escribe la P40 en el público?** Recomiendo que no: solo la P50, una instantánea por versión de mapas (§4.2).
7. **Atestación Sigstore.** Recomiendo dejar de atestar y verificar con `SHA256SUMS` y Zenodo (opción A, §4.3).
8. **Más contenido en la lista blanca.** Recomiendo empezar solo con lo de §3. ¿Se añaden la documentación pública del método
   (`documentacion_publica/`) y las reglas y contratos que D-92 declara públicos (`configuracion/politica_*.yaml`, catálogo,
   escaños y población oficiales)? Recomiendo **no** en T-445 (cada uno exige revisar que no describe el motor) y decidirlo aparte.
9. **Releases existentes.** Recomiendo copiar al público `mapas-v1.0.0` y `mapa-congreso_huesca-v1.0.0` y corregir los metadatos de
   sus depósitos (§5, §7); los espejos de fuentes y los borradores se quedan en el privado.
10. **Enlaces de las V1-V3 congeladas** al repo de trabajo: recomiendo cambiarlos en el montaje de la P40 a la web, sin descongelar
    su código.
