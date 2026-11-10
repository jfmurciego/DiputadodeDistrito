# T-149 — Inventario «quién llama a quién» (36 workflows) y plan de consolidación

Solo informe: no cambia nada. Datos extraídos de `.github/workflows/*.yml` de `main` (10-11).
Leyenda: WC = workflow_call, WD = workflow_dispatch, PR = pull_request, P = push a main, WR = workflow_run, S = schedule.

## 1. Inventario

### Numerados y entrada manual (se conservan)
| Workflow | Disparo | Llama a | Permisos (máx.) | Secretos | Entorno | Concurrencia |
|---|---|---|---|---|---|---|
| 0 Gestor de Campañas | WD, PR(24 rutas) | 00 | contents/issues/pages/id-token w, actions w | – | produccion (si lanza) | – |
| 00 Ejecución Completa | WC, WD, PR(20 rutas) | _gen. territorial, _puerta, 01, 02, 03, 04, 05, recuperar | contents/issues/pages/id-token w | REGISTRO app | produccion (WD humano) | ddd-full-prod-… |
| 01 Preparación Datos | WC, WD | – | contents w | REGISTRO | – | ddd-territorial-prod-… |
| 02 Distritos Autonómicos | WC, WD | _gen. territorial | contents/issues w | – | – | ddd-territorial-prod-… |
| 03 Resultados Electorales | WC, WD | – | contents w | REGISTRO | – | ddd-electoral-prod-… |
| 04 Incorporación Resultados | WC, WD | _incorporación electoral | contents w | – | – | ddd-electoral-prod-… |
| 05 Publicación del Visor | WC, WD | _publicar sitio | contents/pages/id-token w | REGISTRO | produccion | – |
| 05 Cadena de Publicación | WD | 05 Visor, Publicar versión de mapa | contents r | – | – | por run |
| 06 Escenarios y Ensembles | WC, WD | _gen. territorial, _publicar sitio | contents/pages w | – | produccion | ddd-ensemble-… |

### Auxiliares manuales (renombrados en este PR)
| Workflow | Disparo | Llama a | Secretos | Nota |
|---|---|---|---|---|
| Auxiliar — Activación de Legislatura Vigente | WD | 01, 03 | REGISTRO | la 00 la invoca por `dispatches` (cadena) |
| Auxiliar — Activación por Elección | WD | (lanza 00 por API) | – | entorno produccion |
| Auxiliar — Archivar artefactos en R2 | **S diario 05:17**, WD | – | REGISTRO, R2 | único con cron de producción |
| Auxiliar — Extraer composición M06 | WD | – | REGISTRO, R2 | puntual |
| Publicar versión de mapa | WC, WD | – | – | entorno publicacion; llamado por Cadena |
| Recuperar producto electoral durable | WC, WD | _puerta | REGISTRO | llamado por 00 |
| Producción Territorial Modular | WC | _publicar sitio | – | llamado por _operación territorial |

### Internos automáticos (push/PR/WR/schedule)
| Workflow | Disparo | Rutas/condición | Permisos | Secretos | Qué hace |
|---|---|---|---|---|---|
| Pruebas de la Plataforma | P, PR | todas | contents r | – | jobs `guardian`, `suite`, **`pruebas`** (check obligatorio, `always()`) |
| _Validar Contratos Territoriales | P, PR | 9 rutas | contents r | – | puerta de admisión |
| _Controlar Ejecución | P, PR, WC | 9 rutas (g10, orchestracion) | contents r | – | planificar/ejecutar/resumir; llamado por _operación territorial |
| _Validar documentación pública | P, PR | documentacion_publica/** | contents r | – | construye docs (concurrency por ref) |
| _Validar Productos Públicos | P | visor/**, resultados/finales/**… | contents r | – | valida y empaqueta |
| _Catálogo de procedencia | P | 9 rutas (publicaciones, R2, INDEX…) | contents w | REGISTRO | regenera catálogo y lo commitea |
| _Resultados ligeros | P | publicaciones_visor, composición MANIFEST | contents w | REGISTRO | regenera `datos/resultados/` |
| _Numeración del Registro | P | docs/registro/** | contents w | REGISTRO | numera entradas |
| _Revisor de PR | PR | – | contents r | CLAUDE_CODE_OAUTH_TOKEN | 3 jobs (comprobar/revisar/veredicto) |
| _Fusión automática | **WR**(Pruebas de la Plataforma) | solo PR | contents/checks/pr r | REGISTRO | fusiona con `pruebas` verde |
| _Forense de la 00 | **WR**(00) | solo si falla | contents r | CLAUDE_CODE_OAUTH_TOKEN | diagnóstico + issue |
| _Métricas del proceso | **S lunes 05:17**, WD | – | contents w | REGISTRO | `orchestracion/metricas_proceso.json` |
| _Notificar Finalización de Lote DDD | **WR**("Ejecucion de Generacion de Distritos") | – | issues w | – | **huérfano**: ese workflow no existe → nunca se dispara |

### Reutilizables (WC)
| Workflow | Llamado por | Permisos | Secretos | Concurrencia/entorno |
|---|---|---|---|---|
| _Generación Territorial (13 jobs) | 00, 02, 06 | contents w | REGISTRO, R2 | ddd-territorial-engine-… |
| _Incorporación Electoral (2 jobs) | 04 | contents w | REGISTRO, R2 | – |
| _Puerta de Validación de Fase | 00, Recuperar | contents r | – | – |
| _Publicador del Sitio | 05 Visor, 06, _operación, Producción Modular | contents/pages/id-token w | REGISTRO | **github-pages**, ddd-pages-prod |
| _Ruta Territorial Resuelta (8 jobs) | **nadie** (ningún `uses:` actual) | issues/pages w | – | – |
| _Diagnóstico Topológico | _Ruta Territorial | contents r | – | – |
| _Resolver Reutilización y Estado Durable | _Ruta Territorial | contents/issues w | REGISTRO | orquestacion-durable |

Cadena huérfana: `_Ruta Territorial Resuelta` → {Producción Territorial Modular, _Diagnóstico Topológico, _Resolver Reutilización, _Controlar Ejecución, 06, _Publicador} no tiene llamador desde `main` (ni WC externo). Candidata a retirada tras confirmarlo con el Planificador (tests g10 la referencian).

### Dependencias transversales
- **Check obligatorio**: `pruebas` (job final de «Pruebas de la Plataforma»). Los demás automáticos no son obligatorios, pero con filtro `paths` solo corren si tocan sus rutas.
- **Por nombre**: auto-merge → «Pruebas de la Plataforma»; forense → «00 Ejecución Completa del Proyecto»; ambos numerados/estables. Notificar → nombre inexistente.
- **Huellas/N08**: ningún workflow entra en huellas M05; la 00 y el Gestor se disparan en PR por rutas (20 y 24) que enumeran ficheros de motor: cualquier fusión de jobs debe conservar esas listas.
- Entornos protegidos: `produccion` (00, 05, 06, Gestor, Activación por Elección), `publicacion`, `github-pages`. Los jobs con entorno no pueden fusionarse con jobs sin él sin perder la aprobación.
- Escritores en `main` por push: Catálogo, Resultados ligeros, Numeración, R2, Métricas, Extraer M06 (todos con app REGISTRO; concurrencia propia, sin cancelar).

## 2. Plan por pasos para llegar a «numerados + 1 automático + ≤1 auxiliar»

Orden de menor a mayor riesgo; una PR por paso; cada paso verificable con `pruebas` en verde en la PR y en `main`.

**Paso 0 (hecho aquí)**: prefijo «Auxiliar — » en los 4 manuales.

**Paso 1 — Retirar lo muerto** (−2 a −8 workflows, riesgo bajo): `_Notificar Finalización de Lote` (disparador inexistente). Confirmar y retirar la cadena huérfana `_Ruta Territorial` + Producción Modular + Diagnóstico Topológico + Resolver Reutilización + Controlar Ejecución (+ los tests g10 que los cargan). Riesgo: tests y docs que los citan; huellas no.

**Paso 2 (a) — Automáticos de PR/push en «Pruebas de la Plataforma»** (−5): Validar Contratos, Controlar Ejecución (si sobrevive), Validar documentación, Validar Productos Públicos pasan a jobs con `if:` por rutas (acción `dorny/paths-filter` o `git diff` propio), cada uno con `permissions: contents: read` por job; `pruebas` los agrega con `needs` y trata «skipped» como OK. Riesgos: (i) `pruebas` hoy `always()` y falla si algún need falla: hay que distinguir skipped de failure; (ii) concurrencia por ref de docs-preview; (iii) tiempo de `pruebas` no debe crecer (los jobs corren en paralelo); (iv) el permiso del workflow debe ser `contents: read` y el de escritura quedar fuera. Revisor de PR (usa token Claude): se queda como job con su permiso y secreto propios; un `pull_request` desde forks no recibe el secreto, igual que hoy.

**Paso 3 — Escritores de `main` en un solo workflow «_Interno — Mantenimiento de main»** (−3): Catálogo, Resultados ligeros y Numeración (los tres son push a main con app REGISTRO). Un workflow con 3 jobs `if:` por rutas, `concurrency` común sin cancelar (hoy hay 3 grupos; unirlos serializa y evita carreras de push). Riesgo: orden — Catálogo depende de ficheros que escriben R2/Resultados; hoy se encadenan por el push que cada commit provoca; al unirlos hay que mantener ese re-disparo (la app REGISTRO sí dispara push) o declarar `needs`. Numeración usa legacy/docs; probar con una entrada real.

**Paso 4 (c) — workflow_run / schedule**:
- *Fusión automática*: justificable mantener, pero puede ser un job final de «Pruebas» en `pull_request` si se acepta que fusione tras `pruebas`; el WR existe porque el token de PR no puede fusionar y porque `pruebas` debe estar ya cerrado. Opción segura: mantenerlo como **el único «automático» adicional** o moverlo al workflow de Pruebas con `if: github.event_name=='pull_request'` y `needs: pruebas`. El control de seguridad puede bloquear cambios sobre fusión automática; requiere autorización del propietario en el chat que ejecuta.
- *Forense*: seguir como WR (necesita el run 00 terminado y secreto Claude; en `pull_request` no lo tendría). Alternativa: último job de la 00 con `if: failure()`; pero la 00 es el workflow más caro y delicado y alargaría su cierre. Recomendación: justificar y mantener, o mover bajo el «automático» como job WR combinado (un único workflow `_Interno — Automático` con `workflow_run` + jobs forense y fusión, dos disparadores en un fichero con `if` por `github.event_name`).
- *Métricas (lunes) y R2 (diario)*: un solo workflow de `schedule` + WD «Auxiliar — Mantenimiento programado» con dos jobs (`cron` distinto por job vía `github.event.schedule`). Es el «como mucho un auxiliar». Mantienen REGISTRO y R2 por job. Riesgo: ambos escriben en `main`; usar la concurrencia común del Paso 3.

**Paso 5 (b) — Reutilizables**:
- `_Puerta de Validación de Fase` (1 job, solo `contents/actions: r`) → acción compuesta `.github/actions/puerta-validacion/` (llamadores: 00, Recuperar). Riesgo bajo.
- `_Incorporación Electoral` (2 jobs, solo 04) → jobs del 04 (único llamador); reduce una capa. Riesgo medio: el 04 es llamado también por la 00 con WC; las entradas/salidas no cambian.
- `_Generación Territorial` (13 jobs, 3 llamadores, concurrencia `ddd-territorial-engine`): **no** convertir en acción compuesta (necesita jobs distintos, matrices y concurrencia a nivel de job); mantener como único reutilizable justificado. Si se exige cero reutilizables: sería duplicar 13 jobs en 00/02/06 (peor).
- `_Publicador del Sitio` (entorno `github-pages`, pages/id-token): mantener; los entornos solo van en jobs, no en acciones compuestas.
- `_Resolver Reutilización y Estado Durable`, `_Ruta Territorial`, `_Diagnóstico Topológico`, `Producción Territorial Modular`: salen con el Paso 1 si se confirma que están huérfanos; si no, `_Diagnóstico Topológico` → acción compuesta y los otros → jobs del llamador.

**Resultado posible**: 9 numerados/entrada (0, 00–06 con Cadena) + «Recuperar producto electoral» y «Publicar versión de mapa» (candidatos a pasar a Auxiliar o a fusionarse en la Cadena) + «Pruebas de la Plataforma» (automático único, con Contratos/Docs/Productos/Revisor/Fusión) + «Auxiliar — Mantenimiento programado» (R2, métricas, extraer M06, Activación…) + `_Generación Territorial` y `_Publicador` (WC, ocultos al usuario en la lista porque solo aparecen como WC, pero siguen en la lista de Actions por ser ficheros; GitHub lista todo `.yml` con `name`).

## 3. Riesgos globales y orden recomendado
1. Un workflow no puede ocultarse de la lista: la lista solo baja a «numerados + 1 + 1» si los WC restantes se absorben o se aceptan como excepción (`_Generación Territorial`, `_Publicador`). **Decisión del Planificador/propietario**.
2. Todos los pasos tocan `.github/workflows` (un solo escritor) y varios la fusión automática (control de seguridad).
3. Mantener el nombre de check `pruebas` y los `name:` «Pruebas de la Plataforma» y «00 Ejecución Completa del Proyecto» (los usan auto-merge y forense).
4. Orden: 1 → 2 → 3 → 5(b) → 4 (fusión/forense al final, con autorización expresa).
