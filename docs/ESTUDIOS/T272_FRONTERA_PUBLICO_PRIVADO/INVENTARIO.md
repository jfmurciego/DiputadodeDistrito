# T-272 · Inventario de la frontera público / privado

VERSIÓN: 1.0.0 · FECHA: 2026-11-14 · ESTADO: candidato · BASE: `origin/main` 439af6a (2026-11-12)
CAMBIOS: inventario inicial · MOTIVO: T-272 (D-91..D-94) · ANTERIOR: ninguna (fichero nuevo)
Decisiones: D-91 (privado `DiputadodeDistrito-motor` = fuente única; público = sitio + productos + reglas),
D-92 (contratos y reglas públicos), D-93 (runner propio solo en el privado; pesados a R2), D-94 (Zenodo solo mapas).

Clases: **PRIVADO** (solo en el motor) · **PÚBLICO** (vive y se edita en el público) · **AMBOS** (fuente en el
privado; el puente lo copia al público). Método: solo lectura con `git grep`/`git ls-files`, historial completo
(7229 commits) sin blobs > 300 KB; ningún valor de secreto se imprime aquí (solo ruta y tipo).

## 1. Ficheros sueltos de la raíz

| Ruta | Clase | Motivo | Notas |
|---|---|---|---|
| `README.md` | AMBOS | portada pública; el robot escribe su bloque de estado | reescribir sin roles/flujo interno; hoy lo toca `_reutilizable-publicar-sitio` (RUTAS_ROBOT) |
| `CLAUDE.md` | PRIVADO | instrucciones del propietario, roles, chats, créditos, Mac | (b) |
| `.claude/` (skills, rules, agents, hooks, agent-memory, settings.json) | PRIVADO | operación interna de agentes, presupuesto, lanzamientos | (b); 3 tests lo leen |
| `.github/` (CODEOWNERS, plantillas) | AMBOS | cada repo necesita los suyos | CODEOWNERS nombra al propietario (aceptable) |
| `Dockerfile`, `.dockerignore`, `ddd-local.sh`, `procedimiento.sh`, `receta_cierre.py` | PRIVADO | ejecución local del motor | |
| `requirements.lock` | AMBOS | tests públicos y sitio | podar a lo que use el público |
| `requirements-{banco-motor,cartografia-nacional,congreso-piloto,ensemble,f10-electoral,gerrychain-m05}.lock` | PRIVADO | entornos del motor/estudios | |
| `LICENSE`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md` | AMBOS | obligatorios en ambos | CONTRIBUTING debe decir que el código no se acepta en el público |
| `CITATION.cff`, `.zenodo.json` | PÚBLICO | D-94: Zenodo solo mapas | revisar metadatos (autor/afiliación) |
| `.gitattributes`, `.gitignore` | AMBOS | — | `.gitattributes` declara LFS para 2 ZIP de `inputs/` |
| `LEEME_KIT.md`, `N1-CANDIDATO.md`, `SUBSANACION_N1.md`, `PR_BODY.md` | PRIVADO | borradores internos | `PR_BODY.md` tiene ruta `/Users/…` |

## 2. Directorios de primer nivel

| Ruta | Clase | Motivo | Dependencias / notas |
|---|---|---|---|
| `ddd_motor2/` | PRIVADO | motor 2, competición, D8 | 22 tests, 3 herramientas |
| `ddd_core/` | PRIVADO | motor M04/M05, congreso, electoral | 74 tests, 56 herramientas. **Excepción AMBOS**: `config.py`, `territory_contract.py`, `m06_schema.py`, `territorio_ids.py` (contrato; ya listados como «contratos» en `_reutilizable-publicar-sitio`) |
| `ddd_ensemble/` | PRIVADO | GerryChain/ensembles | 11 tests; **`herramientas/preparar_visor_ejecucion.py` (sitio) importa `ddd_ensemble.gallery`** → desacoplar (T-273) |
| `modulos/` | PRIVADO | M01–M08 | |
| `g10/` | PRIVADO | orquestador interno | 2 tests, `pruebas-plataforma` |
| `herramientas/` (224 .py) | mixto | — | PRIVADO: las que importan motor (≥60) y auditorías/diagnósticos/preflight/banco. AMBOS: publicación y visor (`g10_public_product_manifest`, `preparar_visor_*` tras desacoplar, `validar_contrato_territorial`, `catalogo_territorios`, validadores de esquema M06). Lista exacta en T-273 |
| `configuracion/` | mixto | — | AMBOS (reglas/contratos, D-92): `politica_*.yaml`, `catalogo_territorios_espana_2025.yaml`, `controles_obligatorios.yaml`, `legislatura_vigente.yaml`, `elecciones_vigentes.yaml`, `registro_electoral.yaml`, `publicaciones.yaml`, `resultados_oficiales_*`, `escanos_oficiales_*`, `poblacion_oficial_*`, `partidos_judiciales*.csv`, `notacion_territorial.csv`, `nombres_distrito.json`, `comunidades_interes.json`, `equivalencia_*`, `esquemas/`, `calendario_autonomicas.csv`, `candidaturas_congreso_2026.*`. PRIVADO: `m04_engine.json`, `ensemble/`, `experimentos/`, `oleada_c/`, `campanas/`, `decisiones/`, `f10_auto_tareas.json`, `puertas_f10.v1.json`, `catalogo_preparacion.yaml`, `preparacion_legislatura_vigente.yaml`, `auditoria_reparto_k.json`, `excepciones_*`, `adquisiciones_electorales_especiales.yaml`, `contratos_*` (adaptadores), `evidencia_disponibilidad_*`, `procedencia_eleccionesdb_legacy.json`, `verificacion_independiente_m03_m06.json`, `particiones_insulares_2025.json` |
| `territorios/<t>/config/*.yaml` | AMBOS | contrato territorial (D-92) | ya en el regex «contratos» |
| `territorios/<t>/resultados/` | AMBOS | productos publicados | |
| `territorios/<t>/evidencia/` | mixto | — | `catalogo/`, `acreditaciones_historicas/` AMBOS (procedencia); `ejecuciones_completas/<run>.json` PRIVADO (runs internos; escritos por robot) |
| `territorios/<t>/inputs/` | PRIVADO | fuentes crudas; `aragon/inputs/partes` 6×20 MB duplicados de `inputs/partes` | (d) |
| `datos/` | mixto | — | AMBOS: `composicion/`, `distritos/`, `resultados/`, `homologacion_siglas/`. PRIVADO: `naturalidad/` (D8), `movilidad/` (estudio T-138/139) |
| `datos_abiertos/` | PÚBLICO | escrito por el puente; `INDEX.json` con sha256 de los 49 GeoJSON M06 | robot en `main` |
| `orchestracion/` | mixto | — | AMBOS: `publicaciones_visor.json`, `productos_publicos.json` (registro del visor). PRIVADO: `estado_operativo*.json`, `estado_tareas.json`, `metricas_proceso.json`, `checkpoints_fase1.json`, `plan_lote_g10_*`, `archivo_r2.json`, `campanas/`, `catalogo_procedencia.json`, `inventario_fuentes_historico.json`, `fuente_nazioenbehatokia.json` |
| `resultados/` | mixto | — | AMBOS: `finales/`, `fase1/NOMBRES_DISTRITO*`. PRIVADO: `lotes_autonomos/` (2×29 MB GeoJSON), `bootstrap/`, `diagnosticos/`, `experimentos/`, `cierres_f1/`, `archipielagos/`, `preparaciones/`, `promociones/` |
| `inputs/` | PRIVADO | fuentes crudas, 132 MB (2 punteros LFS + `partes/` 20 MB) | (d) |
| `fuentes/` | AMBOS | catálogo oficial, normativa, códigos INE: procedencia pública | `observatorio_autonomicas/` revisar |
| `schemas/` | mixto | — | AMBOS: `territory-production-contract`, `m06-district-catalog`, `congreso_candidate_product`, `ddd-platform-read-model`, `ddd-community-interest-policy`. PRIVADO: `g10-*`, `ddd-campaign` |
| `tests/` (402 `test_*.py`, `fixtures/` 6,1 MB) | mixto | — | 262 dependen de lo privado (import del motor, herramientas que lo importan, `legacy/`, `docs/` privados, `.claude`, `evals`) → PRIVADO; ~140 candidatos AMBOS/PÚBLICO (contratos, sitio, registro). Lista en `tests_priv` de T-273 |
| `legacy/` (1765 ficheros, 80 MB) | PRIVADO | copias versionadas del motor, docs internos, `DocsdelMacJesus/` | el público necesitará su propio `legacy/` para reglas/contratos (gobernanza) — pregunta |
| `visor/`, `web/`, `publicado/` | PÚBLICO | sitio | |
| `dashboard/` | mixto | — | PÚBLICO: `index.html`, `app.js`, `styles.css`, `hemiciclo.*`, `alternativa/`. PRIVADO: `metricas.html`, `metricas_proceso.json` (proceso interno; robot) |
| `documentacion_publica/` | PÚBLICO | documentación de usuario | |
| `evals/` | PRIVADO | oro de revisiones y `LIBRO_DE_COSTES.md` | (b) |
| `infraestructura/ordenes-manuales/` | PRIVADO | órdenes manuales, `codex_simulado.py`, rutas del Mac | (b) |
| `scripts/instalar-ddd-auto.sh` | PRIVADO | instalación local | |
| `docs/ARQUITECTURA/` | PRIVADO | DESLINDE_1_0, framework de agentes, fichas, corte 5.0.0 | contiene ids de sesión |
| `docs/ESTUDIOS/` (52 MB) | PRIVADO | estudios | |
| `docs/PLAN.md`, `docs/ESTADO.md`, `docs/ESTADO_MAESTRO_PROYECTO.md` | PRIVADO | plan y tablero | ids de sesión; robot en `ESTADO.md` |
| `docs/autorizaciones/` | PRIVADO | fichas de campaña, topes de coste | ids de sesión |
| `docs/registro/`, `docs/REGISTRO_DE_CAMBIOS.md` | PRIVADO | historia interna; numeración por robot | el público tendrá un registro propio del puente — pregunta |
| `docs/AUDITORIAS/` (291 MB, 546), `docs/auditorias/`, `docs/RONDAS/`, `docs/EJECUCIONES/`, `docs/ORQUESTACION/`, `docs/SALIDAS_CHATGPT/`, `docs/evidencia/` | PRIVADO | auditorías y trabajo interno | 53 ficheros con rutas `/Users/…`; ZIP de artefactos |
| `docs/MODULOS/` | AMBOS | descripción del método | revisar detalle de motor |
| `docs/ARTICULO_JOSS/` | PRIVADO | JOSS exige software abierto, incompatible con D-91 | pregunta |
| `docs/POLITICA_*.md`, `docs/CONTRATO_TERRITORIO.md`, `docs/POLITICA_DE_VERSIONES.md`, `docs/POLITICA_K_LIMITES_Y_ESQUEMA.md`, `docs/NOMBRES_Y_COMUNIDADES_NACIONAL.md` | AMBOS | reglas (D-92) | |
| resto de `docs/*.md` (bitácoras, continuidad, auditorías C/R, guías del Gestor, instalación, Zenodo, OSF, historial de workflows y CSV de borrado) | PRIVADO | internos | `PREINSCRIPCION_OSF.md` y `PUBLICACION_ZENODO.md`: revisar si se publican |

## 3. Workflows (`.github/workflows/`, 24)

| Workflow | Clase | Motivo | Dependencias (a)/(c) |
|---|---|---|---|
| `ejecucion-completa-proyecto.yml` (00) | PRIVADO | campaña P00 | llama 8 reutilizables (incl. `desplegar-visor-publico`); `pull_request` |
| `_reutilizable-generacion-territorial.yml` | PRIVADO | M01–M06 | importa `ddd_motor2`; R2; push |
| `_reutilizable-puerta-validacion.yml` | PRIVADO | puerta 02 | |
| `_reutilizable-incorporacion-electoral.yml` | PRIVADO | M07/M08 | `validar_paquete_electoral` (motor); R2 |
| `incorporacion-resultados-electorales.yml`, `produccion-distritos.yml`, `preparacion-fuentes.yml`, `preparacion-legislatura-vigente.yml`, `preparacion-resultados-electorales.yml`, `recuperar-producto-electoral-durable.yml`, `activacion-por-eleccion.yml` | PRIVADO | cadena de producción | encadenados por la 00 |
| `gestor-campanas.yml` | PRIVADO | Gestor P00 | llama la 00 |
| `bateria-motor.yml`, `generar-alternativas-territoriales.yml` | PRIVADO | motor/ensembles | R2; la segunda llama `_reutilizable-publicar-sitio` |
| `podar-r2.yml` | PRIVADO | secretos R2 | |
| `forense-00.yml`, `revisor-pr.yml` | PRIVADO | usan `CLAUDE_CODE_OAUTH_TOKEN`; en público, `revisor-pr` en `pull_request` gastaría cuota con PR ajenas | |
| `cadena-publicacion.yml` | PRIVADO | se convierte en el puente (05 + mapa) | llama `desplegar-visor-publico` y `publicar-version-mapa` |
| `_reutilizable-publicar-sitio.yml` | PÚBLICO | despliegue del sitio | **adaptar**: `preparar_visor_ejecucion.py` → `ddd_ensemble`; escribe `docs/REGISTRO_DE_CAMBIOS.md`, `legacy/docs`, README; lee M06 de artefactos del run privado |
| `desplegar-visor-publico.yml` (05) | PÚBLICO | publica el visor | hoy `workflow_call` desde la 00: llamada privado→público entre repos (ver (c)) |
| `publicar-version-mapa.yml` | PÚBLICO | release/Zenodo de mapas (D-94) | |
| `pruebas-plataforma.yml` | AMBOS (dividir) | CI | importa `ddd_core`, `g10`, lee `legacy/docs`; push de robot |
| `mantenimiento-programado.yml` | AMBOS (dividir) | tareas de cada repo | R2 + push (8) |
| `auto-merge.yml` | AMBOS | cada repo | app `DDD_REGISTRO_*` |

## 4. (a) Tests y workflows del público que dependen del motor

- Tests: 262 de 402 dependen de lo privado (cota superior: incluye 63 que solo citan `legacy/` y 257 que usan `herramientas/`); 74 importan `ddd_core`, 22 `ddd_motor2`, 11 `ddd_ensemble`, 2 `g10`, 30 leen `docs/` privados, 3 `.claude`.
- Workflows públicos que hay que adaptar: `_reutilizable-publicar-sitio` (import de `ddd_ensemble.gallery` vía `preparar_visor_ejecucion.py`; escritura de `legacy/docs` y registro), `pruebas-plataforma` (`ddd_core`, `g10`, `validar_contrato_territorial` importa `ddd_core`), `mantenimiento-programado`.
- Contrato compartido: `ddd_core/config.py` y `territory_contract.py` los usan a la vez el motor y la validación pública → extraer a un paquete de contrato pequeño copiado por el puente.

## 5. (b) Contenido que no debe quedar público (ruta y tipo, sin valores)

| Tipo | Dónde (HEAD) | Recuento |
|---|---|---|
| Tokens/claves (GitHub, AWS/R2, Anthropic, OpenAI, Slack, Google, claves privadas, JWT, asignaciones `*_KEY=`) | — | **0** en HEAD y en el historial escaneado |
| Secretos de Actions referenciados (solo nombre) | workflows | `DDD_REGISTRO_APP_ID/KEY` (24), `R2_*` (7×3), `CLAUDE_CODE_OAUTH_TOKEN` (4) |
| Rutas del Mac `/Users/<usuario>` | `docs/AUDITORIAS` (53), `infraestructura/ordenes-manuales` (10), `legacy/docs` (7), `docs/ESTUDIOS` (5), `tests/`, `territorios/comunidad_valenciana`, `PR_BODY.md` | 85 blobs (380 apariciones) |
| Ids de sesión de Claude (`session_01…`) | `docs/PLAN.md`, `docs/ESTADO.md`, `docs/ARQUITECTURA/FICHAS_AGENTES.md`, `docs/autorizaciones/*` (4), `legacy/docs/PLAN_*` | 35 blobs |
| Nombre personal en ruta | `legacy/DocsdelMacJesus/` | 1 |
| Instrucciones internas, roles, chats, cuotas, costes | `CLAUDE.md`, `.claude/**` (skill `presupuesto`, `lanzar-*`, `operador`…), `docs/autorizaciones`, `evals/oro/LIBRO_DE_COSTES.md`, `docs/PLAN.md`, `docs/registro` | — |
| Metadatos de commits | correo profesional del propietario (dominio propio) como autor | 194 commits |
| Mensajes de commit con enlace `Claude-Session` | `main` | 844 commits |
| Correos en contenido | solo `github-actions@`, `noreply@`, `*.invalid` y de organismos (INE, Junta de Extremadura) | sin correos personales |

## 6. (c) Dependencias cruzadas y robots en `main`

- Reutilizables: la 00 llama `desplegar-visor-publico` → `_reutilizable-publicar-sitio`; `generar-alternativas-territoriales` llama `_reutilizable-publicar-sitio`; `cadena-publicacion` llama 05 + `publicar-version-mapa`. Un repo privado **sí** puede llamar un reutilizable de un repo público, pero los secretos y el `GITHUB_TOKEN` son del llamante: el push al público necesita la app `ddd-registro` instalada en ambos y un token con alcance al público. Alternativa más limpia: el privado hace `repository_dispatch` al público con el `run_id` y el público descarga desde R2.
- Artefactos: la 05 baja el M06 de artefactos del run de la 00; en otro repo, los artefactos privados no son accesibles → el puente debe pasar por R2 o subir el paquete (encaja con D-93).
- Robots en `main` (RUTAS_ROBOT): `orchestracion/*.json`, `datos/**`, `publicado/**`, `datos_abiertos/INDEX.json`, `docs/registro/*`, `docs/REGISTRO_DE_CAMBIOS.md`, `legacy/docs/*`, `README.md`, `dashboard/metricas_proceso.json`, `territorios/*/evidencia/*.json`, `docs/ESTADO.md`. Repartir: públicos escritos solo por el puente (`publicaciones_visor.json`, `productos_publicos.json`, `datos/`, `datos_abiertos/INDEX.json`, `publicado/`); privados por los robots del motor. Si ambos escriben el mismo fichero hay carreras; regla: fuente en el privado, el público solo recibe.
- `orchestracion/publicaciones_visor.json` referencia M08 como blobs de git del repo actual: en el público nuevo esos `blob_sha` no existirán si no se copia el historial → regenerar o reapuntar a R2/releases.

## 7. (d) Copia y limpieza del historial

- Tamaño: GitHub declara 381 MB; árbol de trabajo 919 MB; pack local 304 MB parcial (sin blobs > 300 KB). Mayores en HEAD: 2×29 MB GeoJSON (`resultados/lotes_autonomos`), ≥12×20 MB `*.zip.partNN` duplicados (`inputs/partes` y `territorios/aragon/inputs/partes`), ZIP de artefactos en `docs/AUDITORIAS` (291 MB). Los 49 GeoJSON M06 (~50 MB) no están versionados (blobs/R2): no viajan con el historial.
- LFS: `inputs/seccionado_2025.zip` y `inputs/65034.csv.zip` declarados LFS; `git clone --mirror` no copia objetos LFS → `git lfs fetch --all` + `push --all` al privado.
- Lo que no viaja con el historial: issues, PR y sus comentarios, runs y logs de Actions, artefactos, releases (`fuente-infoelectoral-02202307`, versiones de mapa), secretos, Pages, apps instaladas, protección de rama.
- Si el repo actual vuelve a ser público **con su historial**: se exponen todas las versiones del motor (`ddd_core`, `ddd_motor2`, `legacy/`), CLAUDE.md, `.claude/`, PLAN, autorizaciones, costes, 85 blobs con rutas del Mac, 35 con ids de sesión, el correo profesional de 194 commits y 844 enlaces de sesión; además los logs de Actions y las `refs/pull/*`, que un `filter-repo` + force push no borra (hace falta soporte de GitHub), y lo que ya se haya expuesto antes en abierto o en forks.
- Escaneo de secretos: 17 977 blobs ≤ 300 KB de todo el historial, sin tokens ni claves. No escaneados: blobs > 300 KB (sobre todo ZIP/GeoJSON/JSON grandes); recomendable `run_secret_scanning`/push protection de GitHub antes de abrir.

## 8. Riesgos mayores

1. Abrir el repo actual con su historial expone todo lo privado (motor, CLAUDE.md, costes, ids de sesión, correo en commits). La limpieza no alcanza a `refs/pull/*`, logs ni cachés.
2. El sitio público depende de código del motor: `preparar_visor_ejecucion.py` → `ddd_ensemble.gallery`; validación de contrato → `ddd_core`.
3. El puente entre repos: la 05 hoy lee artefactos y `GITHUB_TOKEN` del mismo repo; entre repos hace falta R2 + token/app con alcance cruzado.
4. `publicaciones_visor.json` apunta a blobs de git del repo actual: se rompe en un público con historial nuevo.
5. Robots que escriben en `main` en los dos lados: carreras y divergencia si un fichero se escribe en ambos.
6. `revisor-pr`/`forense-00` con `CLAUDE_CODE_OAUTH_TOKEN` en un repo público: gasto por PR ajenas → solo en el privado.
7. 262/402 tests dependen del motor: la CI pública se quedaría casi vacía o rota sin la separación de T-273.
8. LFS y releases no viajan con `--mirror`; el espejo Infoelectoral (release) lo usa la 03.
9. Peso del historial (381 MB, ZIP duplicados): conviene limpiar también el privado (`inputs/partes` duplicado, `docs/AUDITORIAS/*.zip`, `resultados/lotes_autonomos`).

## 9. Preguntas abiertas

1. ¿Qué repo conserva issues/PR/Actions/secretos? Opción recomendable: el **actual pasa a ser el privado** (renombrado) y el **público se crea nuevo con historial limpio** (huérfano) alimentado por el puente; evita reescribir historia y exponer `refs/pull/*`.
2. ¿El público lleva su propio `legacy/` y registro para reglas y contratos, o la gobernanza de versiones solo aplica en el privado?
3. ¿Se extrae un paquete de contrato (`ddd_core/config.py`, `territory_contract.py`, `m06_schema.py`, `territorio_ids.py`) copiado por el puente, o el público valida solo con JSON Schema?
4. ¿`dashboard/metricas*` y `docs/MODULOS` son públicos?
5. JOSS (`docs/ARTICULO_JOSS`) y OSF: ¿se abandonan con D-91/D-94?
6. Pages: ¿el visor se sirve desde el público (Actions del público) y el privado solo dispara?
7. ¿Se reescribe el autor de los 194 commits con correo profesional en la copia privada, o solo importa en el público?
