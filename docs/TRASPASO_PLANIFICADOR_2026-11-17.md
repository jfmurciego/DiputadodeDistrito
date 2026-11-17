# Traspaso del Planificador — 17-11-2026 (mañana)

VERSIÓN: 1.0.0 · FECHA: 2026-11-17 · ANTERIOR: docs/TRASPASO_PLANIFICADOR_2026-11-16.md

Motivo: relevo por contexto (69 % del umbral), primer relevo con las reglas de D-160 (T-403 aún sin fusionar).
Sesiones: Planificador saliente `session_01KQDtFsPWJU3AMdHjHmWcvp` (profundidad de linaje 5 de 8) · Coordinador
`session_01KQDtFu1megDcVH451BXPQv` (Sonnet) · Operador `session_01KQDtFqw1LBgGn6nCuxP8Yx` (Opus).
Plan vigente: `docs/PLAN.md` 1.0.62 (D-131 a D-160, cola hasta T-404). Siguiente id libre: **T-405**.

## Cómo trabaja el propietario (además de CLAUDE.md)
- Diseño al detalle y aprobación antes de implementar; preguntas numeradas, en una ronda, con recomendación («sí» la acepta).
- El Planificador planifica: no da comandos ni pasos manuales (los da el Coordinador). Corrige en voz alta.
- Respuestas cortas, de tú, con semáforo. Prioridad máxima: terminar la migración (D-149); ninguna campaña hasta entonces.
- Errores repetidos del saliente que no hay que repetir: dar frases D-52 antes de que exista la ficha; anotar como
  «decidido» lo que el propietario eligió en otro chat sin verlo (caso «opción A»); dar por fusionada una corrección
  del plan sin comprobar que entró (D-145 y D-156 se colaron sin la corrección: comprobar `origin/main` antes de cada
  versión nueva del plan).

## Autorizaciones vivas
- Coordinador: fusionar sin esperar al propietario hasta las 23:59 del 17-11 (D-157), con CI verde en la PR y en `main`
  y revisor conforme; la PR 2a de P00 solo con el entorno `registro` con secretos y su primera prueba verde. No lanza ni publica.
- Operador: frases de las fichas `2026-11-17_reensayo-p00-2026-11` y `2026-11-17_historico-2019-11` dadas por el
  propietario («cuando se cumpla su condición previa»). Comprobar con el Operador que las dio DESPUÉS de fusionarse #876.

## Migración (D-129), estado
- Hechos: P90 (#845), P70 (#851), P80 (#853), P50 (#855), P40 (#862), P10 (#874), P30 (#866), P20 (#880), P00 PR 1 (#861) y PR 4 (#882), nombres P90 (#877).
- En curso: T-379 PR 2a (entorno `registro`: el propietario crea el entorno y copia los secretos; dos pruebas del Operador),
  2b y 3 (Opus); luego validación P00 (aut11 + piloto `nac22_h2019_11`), re-ensayo 2026-11 y T-383 (documentación),
  T-397 (prefijo «_», borrado de ejecuciones de retirados, diagnóstico de dinámicos).
- Excepciones ya aprobadas a «nada interno»: fusión automática (D-135), revisor de PR (D-144), cadena y registro de P00.

## Histórico, estado
- Diseños fusionados: alta `<t>_hAAAA_MM` (T-393, #873) y P43 (T-395, #875; kind propio, M06 de cada época).
- T-399: 2011-11 con B' (D-158), rehaciendo #883. T-400: La Graciosa (35). T-402: geometrías inválidas. T-396 hecha.
- Implementación del alta y de P43: tras la PR 3 de P00. Campaña histórica: con P00, por elecciones, dentro del tope semanal (63 % usado el 17-11).

## Pendiente del propietario
Zenodo (desactivar integración, `publicacion` limitado a `main`, tokens, sandbox), T-380 (publicar el visor y borrar 3
Releases de ensembles), ruleset con `pruebas` requerido, entorno `registro`, frase de D-160 en el chat del Operador
(«las frases anotadas en su ficha valen para el Operador sucesor»), registro de la propiedad intelectual.
