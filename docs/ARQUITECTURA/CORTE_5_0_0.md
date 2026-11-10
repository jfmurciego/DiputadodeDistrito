# Especificación del corte 5.0.0 (T-178, 2026-11-10)

Estado: **especificación para decidir** (propietario + Planificador). Solo documento: nada se renombra, mueve ni migra
en `main` hasta el corte; no toca código, workflows, claves ni datos, y no lanza nada.

Fuentes (todas en el repositorio; datos nunca de memoria):
- Decisiones: `docs/PLAN.md` en `main` (D-37, D-45, D-47, D-48, D-50, D-53 a D-57) y en la rama del Planificador
  `claude/plan-d58` (D-58, D-59, D-60, aún sin fusionar en `main`).
- Lista de Actions: `docs/ESTUDIOS/T149_LISTA_ACTIONS/INVENTARIO.md` y `.github/workflows/*.yml` de `main` (`7a9bb0c`).
- Ids: `docs/ESTUDIOS/T170_MIGRACION_IDS/PLAN_MIGRACION_IDS_AUT_NAC.md`, `docs/INVENTARIO_IMPACTO_NOTACION_AUT_NAC.md`,
  `configuracion/notacion_territorial.csv` (sha256 `13299081…21ee`, 71 filas) y
  `configuracion/catalogo_territorios_espana_2025.yaml` (sha256 `841a670c…b378`).
- Productos: `orchestracion/publicaciones_visor.json` (197 productos: 103 `canonical_m06`, 92 `canonical_m08`, 2 `static`;
  más `ensembles`) y `orchestracion/archivo_r2.json` (624 objetos: 246 `ddd-state`, 172 `ddd-minimo`, 104 `ddd-audit`,
  102 `ddd-audit-electoral`).
- Fases anteriores: `docs/ARQUITECTURA/FRAMEWORK_AGENTES_Y_ESTRUCTURA.md` §2 (borrador previo, sustituido por D-47).
- Motor nuevo: `ddd_motor2/` (competición, semilla pública `ddd_motor2/semilla.py`, reglas, naturalidad).

Este documento usa los códigos antiguos (Mxx, números de workflow) solo para la tabla de equivalencias y las referencias
técnicas. Lo que se cuente al propietario se dice en la notación nueva.

---

## (a) Notación final

### Fases (D-47, con subfases de esta especificación)
| Fase | Nombre | Subfases | Qué hace |
|---|---|---|---|
| P00 | Campaña | — | Decide qué territorios y elecciones entran, autoriza (D-41) y encadena el resto |
| P10 | Fuentes | P11 territoriales · P12 electorales · P13 movilidad | Descarga o espejo, sha256, edición y vigencia; P13 es indicador sin peso (D-34) |
| P20 | Base territorial | P21 población y secciones · P22 geometría · P23 grafo de vecindad | Unidades con población, geometría normalizada (CRS 25830) y grafo de adyacencia |
| P30 | Distritos | P31 unidades y reglas · P32 generación · P33 alternativas y elección · P34 certificación · P35 estabilidad | El motor: reglas del núcleo único, competición de generadores, elección pública, certificado y estabilidad del mapa |
| P40 | Resultados electorales | P41 votos a secciones · P42 agregación a distritos · P43 validación | Una elección cualquiera; **el histórico es una elección más** (D-37, D-40) |
| P50 | Publicación | — | Registro del visor, sitio, datos abiertos |
| P60 | Publicación académica | — | Versión de mapa firmada, DOI (Zenodo) |

### Archivo continuo ARC (D-47; no es una fase)
| Clase | Contenido | Permanencia |
|---|---|---|
| ARC-E | Entradas verificadas (mínimo por territorio, D-35) | Permanente |
| ARC-C | Puntos de control del motor y de la cadena | Temporal (hoy 14 días; T-170 §1 capa 5: no se migra, caduca solo) |
| ARC-P | Productos y auditorías | Permanente |

### Territorios (D-36, D-54, D-60)
`AUT01`-`AUT19` (CODAUTO del INE) y `NAC01`-`NAC52` (CPRO del INE), siempre con el nombre en español; variante de 350
con sufijo `-350` (recomendación vigente D-60). Tabla completa en el anexo A.

---

## (b) Lista objetivo de flujos de trabajo de la versión 5

Objetivo: el propietario ve solo **P00 … P60 y ARC**, más lo automático.

| Flujo v5 (nombre visible) | Absorbe (fichero de hoy · nombre de hoy) | Notas |
|---|---|---|
| **P00 Campaña** | `gestor-campanas.yml` · 0 Gestor de Campañas; `ejecucion-completa-proyecto.yml` · 00 Ejecución Completa del Proyecto; `activacion-por-eleccion.yml` · Auxiliar — Activación por Elección; `preparacion-legislatura-vigente.yml` · Auxiliar — Activación de Legislatura Vigente | Modos: `plan`, `campaña`, `territorio`, `eleccion`, `legislatura`. Entorno `produccion` en el job que lanza |
| **P10 Fuentes** | `preparacion-fuentes.yml` · 01 Preparación de Datos Territoriales; `preparacion-resultados-electorales.yml` · 03 Preparación de Resultados Electorales | Entrada `subfase: P11 / P12 / P13` |
| **P20 Base territorial** | `produccion-distritos.yml` · 02 Generación de Distritos Autonómicos (parte de base territorial: M01-M03); jobs de M01-M03 de `_reutilizable-generacion-territorial.yml` · Interno · Generación territorial | Flujo propio (DECISIÓN 1, decidida). Produce la base territorial y la archiva en ARC-E |
| **P30 Distritos** | `produccion-distritos.yml` · 02 (parte de distritos: M04-M06); `_reutilizable-generacion-territorial.yml` · Interno · Generación territorial (M04-M06: generación con el motor nuevo y certificación); `generar-alternativas-territoriales.yml` · 06 Escenarios y Ensembles (→ P33); job `extraer_m06` de `mantenimiento-programado.yml` (antes Extraer composición M06) | Consume la base de P20 desde ARC-E (no la recalcula). El motor nuevo vive aquí (§d); P34 certificación dentro |
| **P40 Resultados electorales** | `incorporacion-resultados-electorales.yml` · 04 Incorporación de Resultados Electorales; `_reutilizable-incorporacion-electoral.yml` · Interno · Incorporación electoral; `_reutilizable-puerta-validacion.yml` · Interno · Puerta de validación de fase | La puerta pasa a acción compuesta (T-149 §2 paso 5): no aparece en la lista |
| **P50 Publicación** | `desplegar-visor-publico.yml` · 05 Publicación del Visor; `cadena-publicacion.yml` · 05 Cadena de Publicación; `_reutilizable-publicar-sitio.yml` · Interno · Publicador del sitio | El publicador queda como job con entorno `github-pages` dentro de P50 |
| **P60 Publicación académica** | `publicar-version-mapa.yml` · Publicar versión de mapa | Entorno `publicacion` (revisor humano) intacto |
| **ARC Archivo** | job `archivar_r2` de `mantenimiento-programado.yml` (antes Archivar artefactos en R2); `podar-r2.yml` · Auxiliar — Poda de R2; `recuperar-producto-electoral-durable.yml` · Recuperar producto electoral durable | Poda: job con `produccion` siempre (borrado irreversible). Archivo diario por `schedule` |
| *Automático* · Pruebas de la Plataforma | `pruebas-plataforma.yml` (jobs `guardian`, `suite`, `contratos`, `docs`, `productos`, `pruebas`, `catalogo`, `resultados`, `numeracion`) | **No se renombra** (T-149 §4) |
| *Automático* · Revisor de PR | `revisor-pr.yml` (job `veredicto`, exigido por el ruleset, D-55) | No se renombra el job |
| *Automático* · Mantenimiento | `mantenimiento-programado.yml` (queda el job `metricas`) | Ver DECISIÓN 2 (si el archivo diario va aquí o en ARC) |
| VER Verificación del motor (**ABIERTO**) | `bateria-motor.yml` · Auxiliar — Batería del Motor | Ver DECISIÓN 10 |
| *Automático, sin tocar* · Fusión automática y Forense | `auto-merge.yml`, `forense-00.yml` | D-53/D-58: no se tocan sin autorización expresa. Pero dependen por nombre: ver riesgo (f)4 y DECISIÓN 3 |

Resultado: 8 entradas manuales (P00, P10, P20, P30, P40, P50, P60, ARC) y 5 automáticas, más la batería según la DECISIÓN 10. Las
cuatro «Interno ·» aceptadas como excepción (D-56) desaparecen: tres se integran en su único dueño v5 y la puerta pasa a
acción compuesta.

**DECISIÓN DEL PROPIETARIO 1 — DECIDIDO (10-11, vía Planificador):** P20 Base territorial y P30 Distritos son dos flujos
visibles y separados; P20 produce y archiva la base en ARC-E y P30 la consume. Al
dividir el Interno · Generación territorial (13 jobs), la concurrencia `ddd-territorial-engine-…` debe cubrir los dos
(un P20 y un P30 del mismo territorio no pueden correr a la vez sobre la misma base).

**DECISIÓN DEL PROPIETARIO 10 — ABIERTO: batería del motor.** Propuesta (Planificador): visible bajo demanda con el
código **VER** («VER Verificación del motor»), fuera de las fases. Alternativa (recomendación de esta especificación):
automática (cada noche y en toda PR que toque el motor, D-49) con disparo manual, fuera de la lista del propietario.

**DECISIÓN DEL PROPIETARIO 2 — archivo diario.** Recomendación: el archivo diario (cron) va en ARC (un solo dueño de R2,
misma concurrencia que la poda); «Mantenimiento» queda solo con métricas.

---

## (c) Nombres nuevos de productos y claves

**DECISIÓN DEL PROPIETARIO 4 — nombres de productos y claves** (recomendación abajo; regla: la fase que lo produce +
qué es, en español, sin códigos de módulo).

| Hoy | v5 (recomendado) | Fase |
|---|---|---|
| M06 (GeoJSON de distritos consolidados), `kind=canonical_m06` | **Mapa certificado**, `kind=mapa_certificado` | P34 |
| M08 (ZIP de resultados integrados por distrito), `kind=canonical_m08` | **Resultados por distrito**, `kind=resultados_distrito` | P42 (validados en P43) |
| `kind=static` | `kind=estatico` | P50 |
| `ensembles[]`, `kind=ensemble` | `kind=alternativas`, en `ensembles[]` (lista sin cambios) | P33 |
| id `m06-<id>-<run>` | `mapa-<id5>-<run>` | — |
| id `m08-<id>-<run>` | `resultados-<id5>-<run>` | — |
| id `static-<id>` | `estatico-<id5>` | — |
| `label`: «M06 territorial · run N» | «Mapa certificado · <código> · <nombre> · run N» | — |
| campo nuevo | `alias_de: <id viejo del producto>` (T-170 §2) | — |

`<id5>` = id de territorio v5 (anexo A).

Claves de R2 (hoy `r2://ddd-research-archive/<id>/<run>/<artefacto>-<run>.zip`, `orchestracion/archivo_r2.json`):

| Hoy (artefacto) | v5 | Clase |
|---|---|---|
| `ddd-minimo-<run>` | `arc-e/<id5>/<run>/entrada-minima.zip` | ARC-E |
| `ddd-state-<run>` | `arc-c/<id5>/<run>/punto-control.zip` | ARC-C (no se copia: caduca, T-170 §1) |
| `ddd-audit-<run>` | `arc-p/<id5>/<run>/auditoria-territorial.zip` | ARC-P |
| `ddd-audit-electoral-<run>` | `arc-p/<id5>/<run>/auditoria-electoral.zip` | ARC-P |
| — | `arc-p/<id5>/<run>/mapa-certificado.geojson`, `…/resultados-distrito.zip` (si se decide archivar los productos en R2 además del blob de git) | ARC-P |

El cubo (`ddd-research-archive`) no cambia. Las claves viejas se conservan hasta la retirada de alias (T-170 capa 7).

### Tabla de equivalencias viejo ↔ nuevo

**Módulos** (los ficheros `modulos/0X_*` no se renombran, `.claude/rules/gobernanza.md`; ver §d):

| Viejo | Nuevo |
|---|---|
| M01 `01_preparar_base_territorial.py` | P21 población y secciones + P22 geometría |
| M02 `02_construir_adyacencias.py` | P23 grafo de vecindad (adyacencias) |
| M03 `03_construir_grafo.py` | P23 grafo de vecindad (grafo) |
| M04 `04_generar_semillas.py` | P32 generación — proveedor del punto de partida (D-48) |
| M05 `05_optimizar_distritos.py` | P32 generación (competidor «canónico») |
| — `ddd_motor2/competicion.py`, GerryChain | P32 generación (competidor) + P33 elección |
| — `ddd_motor2/reglas/` (núcleo único, D-44) | P31 unidades y reglas |
| M06 `06_consolidar_distritos.py` | P34 certificación → producto «Mapa certificado» |
| — (pilar «estabilidad», D-32) | P35 estabilidad |
| M07 `07_agregar_resultados_electorales.py` | P41 votos a secciones + P42 agregación |
| M08 `08_integrar_resultados.py` | P42 agregación → producto «Resultados por distrito»; P43 validación |
| piloto de movilidad (D-34) | P13 movilidad |

**Workflows**: ver la tabla de (b) (fichero y nombre de hoy → flujo v5). Ficheros v5 recomendados:
`p00-campana.yml`, `p10-fuentes.yml`, `p20-base-territorial.yml`, `p30-distritos.yml`, `p40-resultados.yml`, `p50-publicacion.yml`,
`p60-publicacion-academica.yml`, `arc-archivo.yml`; los automáticos conservan fichero y nombre. Los ficheros viejos
pasan a `legacy/workflows/` (como hizo T-149 con `mantenimiento-programado.yml`).

**Productos y claves**: tablas de arriba.

**Territorios**: anexo A (71 + 49 filas, generadas de `notacion_territorial.csv` y del catálogo).

**DECISIÓN DEL PROPIETARIO 5 — forma del id** (pendiente en `docs/ESTADO.md`, «Pendientes»): minúsculas (`nac01`,
recomendado por T-170 §0: rutas, claves de R2 y URL sin mayúsculas) o el código tal cual (`NAC01`). El anexo usa
minúsculas.

---

## (d) El motor nuevo como P30 y destino de M01-M08

- P30 = el motor nuevo (D-48): competición entre el canónico y GerryChain bajo el núcleo único de reglas, semilla pública
  (D-50), el mejor plan por territorio y nunca peor que el canónico. El relevo **no está decidido** (D-57): requiere
  núcleos cerrados en el certificador, enumeración exacta en territorios pequeños (D-33), regla pública de elección
  escrita y la decisión de naturalidad con los mapas delante.
- **El corte 5.0.0 coincide con el relevo (D-45).** Si el propietario no releva, no hay corte.
- M01-M03 siguen siendo el código de P20 (sin reescribir; solo cambia cómo se nombran sus etapas y productos).
- M04 sigue como proveedor del punto de partida de P32 (D-48: el arranque genérico por árboles no basta en 41
  territorios).
- M05 pasa a ser **un competidor** de P32 (el canónico); deja de ser el motor que decide.
- M06 se divide: consolidación (P32/P34) y certificado (P34, certificador ligero). Su producto es el «Mapa certificado».
- M07-M08 son P40 sin cambios de lógica.
- Las versiones de `ddd_core/m04_seed_engine_v7*.py` y demás copias activas no se borran en el corte (son entrada de
  huellas e historia); su retirada es una tarea posterior.
- **DECISIÓN DEL PROPIETARIO 6 — semilla y territorio.** `ddd_motor2/semilla.py` mete en la semilla el identificador
  del territorio (`…|<territorio>|<i>`). Si se le pasa el id interno, el id viejo y el nuevo dan **semillas distintas** y
  la prueba «mismo mapa bit a bit» (D-60) falla por construcción. Recomendación: la semilla usa el **código de la tabla
  maestra** (`AUT01`, `NAC01`, `NAC01-350`), obtenido del resolutor único con cualquiera de los dos ids. Consecuencia:
  los mapas del corte difieren de los de la batería actual (otra semilla), así que la batería se repite tras el cambio.

---

## (e) Orden del corte, aceptación, regeneración y vuelta atrás

### Precondiciones (todas, antes de abrir el corte)
1. Decisiones del propietario 1-9 de este documento tomadas.
2. Relevo del motor decidido (D-57) y sus condiciones cumplidas.
3. Ventana de congelación: sin runs en curso, Gestor sin lanzar, ninguna PR abierta que toque workflows, `main` en
   verde (`pruebas` y `veredicto`).
4. Presupuesto aprobado (D-46: 15.000 min/semana, aviso al 70 %) y frase de campaña del propietario en el chat del
   Operador (D-41) para los lanzamientos.

### Orden (una PR por paso; cada paso con `pruebas` en verde en la PR y en `main` antes del siguiente)
| Paso | Qué | Capa T-170 | Reversible |
|---|---|---|---|
| 0 | Congelar: etiqueta `pre-5.0.0`; inventario `(clave, sha256)` de R2, copia del registro del visor, de `INDEX.json` y del catálogo de procedencia | — | Sí |
| 1 | Catálogo con `id_legacy` y `notacion`; resolutor único `resolver_id`; carpetas `territorios/` con `git mv` | 1 | Sí |
| 2 | Contratos y políticas leen ambos ids y escriben el nuevo; semilla por código (DECISIÓN 6) | 2 | Sí |
| 3 | Motor nuevo como P30 (relevo); huella nueva | — | Sí, antes del paso 6 |
| 4 | **Workflows v5 en una sola PR atómica**: ficheros nuevos, viejos a `legacy/`, y a la vez todo lo que depende de nombres (riesgo f4); requiere revisión independiente y autorización expresa para fusión automática y forense | 3 | Sí, antes del paso 6 |
| 5 | Pruebas A, D, E, F de T-170 §4 y batería 71/71 (aceptación de motor) | — | — |
| 6 | **Regeneración** (abajo) — primer punto de no retorno práctico | — | Solo regenerando con lo viejo |
| 7 | Copia verificada de ARC-E y ARC-P a claves nuevas; `archivo_r2.json` con el par nueva/vieja | 5 | Sí, hasta borrar las viejas |
| 8 | Registro del visor: solo adición de productos v5 con `alias_de`; visor y datos abiertos leen el nuevo id con respaldo al viejo; carpetas nuevas de `datos_abiertos` junto a las viejas | 4, 6 | Sí, mientras convivan |
| 9 | P50 con permiso del propietario; P60 si se decide nueva versión de mapa | — | Publicar es visible fuera |
| 10 | Versión del proyecto 5.0.0 (D-51 la fija en 4.9.0 hasta entonces), README y entrada de registro | — | Sí |
| 11 | Retirada de alias y claves viejas, tras un ciclo sin lecturas por id viejo | 7 | **No** |

### Pruebas de aceptación
1. **Mismo mapa bit a bit con id viejo y nuevo** (D-60, T-170 §4 A): Álava, Huesca, Cádiz, Madrid, uno insular y Ceuta,
   misma semilla; asignación unidad→distrito y GeoJSON idénticos byte a byte. Si falla, parar.
2. **Batería 71/71** válidos con el motor de P30, ninguno peor que el canónico (D-48), reproducible bit a bit.
3. **Registro y visor coherentes**: cada producto v5 tiene `alias_de` a uno existente o es nuevo del corte; los 197
   productos viejos siguen idénticos campo a campo a la copia del paso 0;
   el visor carga cada territorio por URL vieja y nueva con el mismo contenido (T-170 §4 G); `INDEX.json` lista ambas.
4. T-170 §4 B-H (datos abiertos, R2 objeto a objeto, catálogo biyectivo 71 + 49, resolutor, Gestor en `plan` con el
   mismo plan, suite completa).
5. Lista de Actions: solo los nombres de (b); los checks `pruebas` y `veredicto` siguen saliendo con ese nombre.

### Plan de regeneración
- Todos los territorios con el motor de P30 desde la fuente acreditada (equivalente hoy a la 00 «Generar desde fuente
  territorial acreditada»; «Reutilizar» no sirve: restaura checkpoints del contrato viejo, `CLAUDE.md` §Ejecución 00).
- Alcance: 71 (19 autonómicos + 52 provincias). **DECISIÓN DEL PROPIETARIO 7**: las 49 de 350 entran o no
  (recomendación: no en el corte; el mapa de 350 sigue «en desarrollo», D-58).
- Orden por territorio: territorial (P30) → electoral (P12 con reutilizar=false si el paquete caducó) → legislatura
  (P00 modo legislatura) → P40. La cadena `territorial_only` con `cadena_electoral=true` lo encadena sola (`CLAUDE.md`).
- Por campaña de P00 (autorización por campaña, D-41; su propuesta sigue en borrador, D-52/D-58).
- **DECISIÓN DEL PROPIETARIO 8 — histórico**: recomendación, en el corte solo la legislatura vigente; las elecciones
  históricas se regeneran después como «una elección más» de P40, sin bloquear el corte.
- Coste: no estimado aquí; lo calcula la skill `presupuesto` con las duraciones reales antes de pedir la frase.

### Vuelta atrás
- Antes del paso 6: `git revert` de las PR 1-4 en orden inverso; los checkpoints viejos siguen valiendo.
- Después del paso 6 y antes del 8: el visor sigue con el registro viejo (no se ha añadido nada); basta revertir
  workflows y motor. Los checkpoints nuevos se pierden (caducan).
- Después del paso 8: el registro es de solo adición; la vuelta atrás es **añadir** entradas que vuelvan a apuntar a los
  productos viejos (siguen en git como blobs) o retirar lo añadido (T-170 §5). R2 viejo intacto hasta el paso 11.
- Después del paso 11: solo desde la copia del paso 0.
- Una prueba que falle se revierte entera; no se arregla sobre la marcha (dos ciclos de reparación por causa, T-170 §5).

---

## (f) Riesgos

| # | Riesgo | Evidencia | Mitigación |
|---|---|---|---|
| 1 | **Huellas** | La huella M05 es el cierre de imports del motor (`.claude/rules/huellas.md`); el id entra en el contrato; N08 fija hashes de ficheros activos | Se asume la invalidación (el corte regenera todo, T-170 §3); no renombrar `modulos/0X_*`; montar copias archivadas para N08; fuentes oficiales con sha256 intactas (comprobar antes y después) |
| 2 | **Puntos de control** | Checkpoints de 14 días; «Reutilizar» restaura el último registrado aunque cambie el contrato | Regenerar desde fuente; ARC-C no se migra; par electoral `TERRITORIAL_READY_PAIR_INCOMPATIBLE` hasta repreparar |
| 3 | **Registro de solo adición** | `publicaciones_visor.json`, 197 productos; el registro rechaza `congreso350_*` (T-125, #574) | Solo añadir con `alias_de`; el rechazo de 350 debe cubrir también `nacNN-350` (si no, se colaría la variante) |
| 4 | **Dependencias por nombre** | `auto-merge.yml`: `workflow_run` de «Pruebas de la Plataforma»; `forense-00.yml`: de «00 Ejecución Completa del Proyecto»; `herramientas/legislatura_vigente.py` (`TITLE_00`) y `herramientas/metricas_proceso.py` (`RUN_NAME`) por el nombre de la 00; **los entornos de `desplegar-visor-publico.yml` y `generar-alternativas-territoriales.yml` se activan con `github.workflow == '05 Publicación del Visor'` / `'06 Escenarios y Ensembles'`**: renombrar sin tocarlos quita en silencio la aprobación de `produccion`; 70 ficheros de `tests/` citan `.github/workflows/` | Todo en la PR atómica del paso 4; test nuevo que falle si un `github.workflow ==` o un `workflows: [...]` nombra un flujo inexistente. Ver DECISIÓN 3 |
| 5 | **Checks requeridos** | El ruleset `proteger-main` exige `veredicto` (D-55); la fusión automática espera `pruebas` | No renombrar los jobs `veredicto` ni `pruebas` ni sus workflows |
| 6 | **Entornos protegidos** | `produccion` (00, 05, 06, Gestor, Activación por Elección, Poda), `publicacion` (P60), `github-pages` (publicador) | No renombrar entornos (sus secretos y revisores van con el nombre); un entorno solo va en jobs, no en acciones compuestas (T-149 §2) |
| 7 | **Secretos** | App REGISTRO, R2, `CLAUDE_CODE_OAUTH_TOKEN` | Mismos nombres; cada job pide solo los suyos (no ampliar permisos al fusionar flujos) |
| 8 | **Concurrencia** | Grupos `ddd-full-prod-…`, `ddd-territorial-prod-…`, `ddd-electoral-prod-…`, `ddd-territorial-engine-…`, `ddd-ensemble-…`, `ddd-pages-prod`, `archivar-artefactos-r2` | Corte con ventana congelada (un run viejo y uno nuevo con grupos distintos correrían a la vez); conservar los grupos o renombrarlos solo en esa ventana |
| 9 | Semilla dependiente del id | `ddd_motor2/semilla.py` | DECISIÓN 6 |
| 10 | Colisiones AUT/NAC | 9 territorios duplicados (T-170 §7, D-60) | Resolutor por id exacto; `madrid` nunca resuelve a `nac28` |
| 11 | Enlaces externos y DOI | `datos_abiertos/`, DOI 24093967/24093968 (`docs/ESTADO.md`) | Rutas viejas como puente un ciclo; el DOI publicado no se toca |
| 12 | Cadenas automáticas del bot | La 00 encadena legislatura y otra 00 «Reutilizar» como `github-actions[bot]` (`CLAUDE.md`) | En el paso 4, las cadenas de P00 llaman a los ficheros nuevos; identificar runs por territorio |

**DECISIÓN DEL PROPIETARIO 3 — fusión automática y forense.** D-53/D-58 dicen que no se tocan, pero si la 00 pasa a
llamarse «P00 Campaña» el forense deja de dispararse. Opciones: (i) autorizar en el corte el cambio de una línea en
`forense-00.yml` (`workflows: ["P00 Campaña"]`), con revisión independiente — **recomendada**; (ii) que P00 conserve el
nombre «00 Ejecución Completa del Proyecto» (rompe el objetivo de la lista); (iii) aceptar que el forense quede inactivo.
«Pruebas de la Plataforma» no cambia, así que la fusión automática no se toca.

**DECISIÓN DEL PROPIETARIO 9 — convivencia de alias**: cuántos ciclos de publicación antes del paso 11 (recomendación:
uno completo sin lecturas por id viejo, medido por el contador del resolutor, T-170 §2).

---

## (g) Lo que NO cambia

- La historia conserva sus nombres: `legacy/`, `docs/REGISTRO_DE_CAMBIOS.md` y su numeración, `docs/registro/` ya
  fusionado, `docs/AUDITORIAS/`, `docs/ESTUDIOS/`, los runs de Actions y sus nombres, issues y PR (D-45).
- Los 197 productos ya registrados y sus ids `m06-…`/`m08-…` (solo adición).
- Las fuentes oficiales y sus sha256 (Interior `fuente-infoelectoral-02202307`, BOE-A-2023-18907, INE `fuentes/ine_codigos_territoriales_2026-11-10/`).
- Umbrales, K, suelo, techo y atomicidad (decisión aparte del propietario).
- Ficheros `modulos/0X_*` (huellas, N08, tests R015/R016) y `pilot_code` (`C01`…`C52`, `Rnn`).
- Nombres de «Pruebas de la Plataforma», «Revisor de PR», jobs `pruebas` y `veredicto`, entornos y secretos.
- El cubo de R2 y las claves viejas hasta el paso 11.
- El DOI publicado.

## Resumen de decisiones del propietario
| # | Decisión | Recomendación |
|---|---|---|
| 1 | P20 y P30 como flujos separados; P20 archiva la base en ARC-E, P30 la consume | **Decidido** (10-11) |
| 2 | Archivo diario en ARC o en Mantenimiento | ARC |
| 3 | Forense con el nombre nuevo de P00 | Autorizar el cambio de una línea en el corte |
| 4 | Nombres de productos y claves R2 | Tablas de (c) |
| 5 | Id en minúsculas o mayúsculas | Minúsculas (`nac01`) |
| 6 | Territorio en la semilla | Código de la tabla maestra vía resolutor |
| 7 | Variante de 350 en el corte | No |
| 8 | Histórico en el corte | No; después, como elecciones de P40 |
| 9 | Ciclos de alias antes de borrar lo viejo | Uno, con contador a cero |
| 10 | Batería del motor (ABIERTO) | Propuesta: VER bajo demanda, fuera de las fases; alternativa: automática con disparo manual |

Las decisiones 2 a 10 las presenta el Planificador; sus respuestas se cierran en una segunda PR.

Ya decidido y recogido aquí: corte único con el relevo (D-45), notación de fases (D-47), sufijo `-350`, nueve
duplicados AUT/NAC y prueba bit a bit (D-60), capa visible solo en el corte (D-54, D-60), cuatro «Interno ·» revisados en
el corte (D-56).

---

## Anexo A — Ids de territorio viejo ↔ nuevo

Generado de `configuracion/notacion_territorial.csv` (columnas `codigo`, `nombre_es`, `id_interno`) y, para la variante
de 350, de `parent_territory_id` en `configuracion/catalogo_territorios_espana_2025.yaml`. Id nuevo en minúsculas
(DECISIÓN 5).

| Código | Nombre | id viejo | id nuevo (propuesto) |
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

Variante de 350 (49 ids; sufijo «-350» recomendado en D-60):

| id viejo | padre | id nuevo (propuesto) |
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
