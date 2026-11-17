<!--
PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Equivalencias y guía de los workflows migrados (D-129)
FECHA: 2026-11-17
ESTADO: vigente
CAMBIOS: T-383. Fichero nuevo.
MOTIVO: documentación de usuario y puente viejo → nuevo de los workflows P10-P90.
ANTERIOR: ninguna (fichero nuevo)
-->

# Workflows migrados (D-129): qué hace cada uno y qué sustituye (T-383)

Estado a 17-11. Puente entre los nombres viejos (los citan documentos históricos, que no se reescriben, D-142) y los
nuevos. Los ficheros retirados están en `legacy/workflows/`. Decisiones: D-129 a D-162 en `docs/PLAN.md`.
Reglas de nombre (D-159, `tests/test_t397_nombres_workflows.py`): los workflows con botón empiezan por «P»; los
que no tienen botón llevan «_» delante. Opciones visibles siempre en español; sin run ids, sha ni rutas.

## Workflows con botón

| Workflow | Qué hace | Opciones visibles | Sustituye a |
|---|---|---|---|
| P10 Fuentes (`p10-fuentes.yml`, D-136, D-151) | Prepara las fuentes de un territorio: P11 territoriales, P12 electorales | tipo (P11 territoriales / P12 electorales), territorio (un código por ejecución), elección (vigente / ensayo 2026-11-29; solo P12), regenerar aunque exista | `preparacion-fuentes`, `preparacion-resultados-electorales` |
| P20 Distritos (`p20-distritos.yml`, D-139, D-148) | Genera el producto territorial certificado (pasos P21…P27) | territorio (un código por ejecución), empezar de cero | `produccion-distritos`, `_reutilizable-generacion-territorial`; `generar-alternativas-territoriales` (P28) se retira sin sustituto (D-138) |
| P30 Resultados electorales (`p30-resultados-electorales.yml`, D-137, D-148) | Agrega los resultados por distrito y pasa la puerta (P31…P33) | territorio (un código por ejecución) | `incorporacion-resultados-electorales`, `_reutilizable-incorporacion-electoral` |
| P40 Publicación (`p40-publicacion.yml`, D-134) | Publica el sitio y los territorios en el visor; sin run id toma la última 00 completa con la 04 en verde | qué publicar (solo el sitio / territorios), territorios, simular (marcado por defecto) | `desplegar-visor-publico`, `cadena-publicacion`, `_reutilizable-publicar-sitio` |
| P50 Publicación académica (`p50-publicacion-academica.yml`, D-133, D-146) | Publica mapas versionados (Release por lote; Zenodo solo con permiso) | territorios (códigos o todos), destino (prueba / Zenodo), concepto nuevo | `publicar-version-mapa` |
| P70 Archivo (`p70-archivo.yml`, D-131) | Archiva, recupera, poda y lista R2 (P71…P74); cron diario de archivo | acción, simular (marcado), territorios, elección | `podar-r2`, `recuperar-producto-electoral-durable`, `archivar_r2`/`extraer_m06` de `mantenimiento-programado` |
| P80 Verificación del motor (`p80-verificacion-motor.yml`, D-132) | Batería del motor sobre los territorios elegidos | territorios (vacío = 71), alcance (motor vigente / motor base M05) | `bateria-motor` |

## Sin botón

- P90 Automático (`p90-automatico.yml` 1.1.0, D-129, T-379 PR 4): pruebas de la plataforma (checks `veredicto` y `pruebas`),
  nocturna, métricas semanales e IA de cierre por campaña. Sustituye a `pruebas-plataforma`, `forense-00` y el job
  `metricas` de `mantenimiento-programado`.
- Excepciones aprobadas (se quedan como fichero propio, sin botón): fusión automática `auto-merge.yml`, disparada por
  `workflow_run` al terminar «P90 Automático» (D-135; GitHub rechaza un `workflow_run` sobre el propio workflow);
  revisor de PR `revisor-pr.yml`, solo con la etiqueta `revisar-ia` (D-135, D-144 a: excepción permanente).
- Prefijo «_» (D-159): `_P90 Automático — Revisor de PR` y los ficheros sin botón de P00 (`_P00 Campaña — <qué hace>`);
  salen al final de la lista de Actions. «P90 Automático — Fusión automática» figura en `auto-merge.yml` (nombre en D-155).
- Interno: quedan `_reutilizable-*` que no se pueden evitar (`_reutilizable-puerta-validacion.yml`; pasa a acción compuesta, D-129).

## Pendiente: P00 Campaña
P00 (D-140, D-143, D-145, D-147) se migra en partes. Hechas: PR 1 (estado de campaña) y PR 4 (IA de cierre en P90).
Pendientes, en curso: PR 2a, 2b y 3. Mientras tanto siguen vigentes `ejecucion-completa-proyecto.yml` («P00 Campaña»),
`gestor-campanas.yml`, `preparacion-legislatura-vigente.yml` y `activacion-por-eleccion.yml`; su diseño final y la
retirada de los antiguos no se describen aquí hasta que se fusionen.

## Excepciones y puntos a recordar
- Fusión automática (D-135) y revisor de PR (D-144): excepciones permanentes a «un fichero por familia».
- El ruleset `proteger-main` pasará a exigir `pruebas` además de `veredicto` (D-144 b; lo cambia el propietario o el Operador).
- Una campaña = una ejecución: P00 llama a P10/P20/P30/P40 por dentro, nunca lanza ejecuciones por fuera (D-130).
