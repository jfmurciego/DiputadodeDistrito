---
name: cierre-sesion
description: Al terminar una sesión de trabajo en Diputado de Distrito, añade a CLAUDE.md las lecciones nuevas que costó descubrir y abre una PR pequeña. Úsala cuando el propietario diga que va a cerrar la sesión o pida guardar la experiencia.
---

# Cierre de sesión

Objetivo: que la próxima sesión no repita los tropiezos de esta. Mínimo consumo.

1. Relee `CLAUDE.md` en `origin/main` (puede haber cambiado por otras sesiones).
2. Repasa la sesión y quédate solo con lo que cumpla las tres condiciones:
   - costó tiempo o ejecuciones descubrirlo;
   - no se deduce leyendo el código;
   - seguirá siendo cierto en próximas sesiones.
   Descarta estados pasajeros (runs en curso, PRs abiertas) y lo que ya esté en `CLAUDE.md`.
3. Edita `CLAUDE.md`:
   - si la lección solo aplica al tocar ciertos ficheros, va en la regla de `.claude/rules/` que los cubre
     (o en una nueva con `paths:`), no en `CLAUDE.md`;
   - si la lección encaja en una sección existente, añádela allí en una o dos líneas;
   - si corrige algo que ya estaba, sustitúyelo en vez de añadir;
   - añade una línea al «Historial de lecciones»: `AAAA-MM-DD · lección breve · PR/run de evidencia`.
   `CLAUDE.md` no pasa de 100 líneas: si se acerca, condensa entradas antiguas o muévelas a una regla.
4. Rama `docs/experiencia-<fecha>` desde `origin/main`, commit, push y PR con título
   `docs: experiencia de sesión <fecha>`. No toques otros ficheros que `CLAUDE.md` y `.claude/rules/`.
5. Dile al propietario en dos líneas qué has añadido y el enlace de la PR. Si no hay nada nuevo, dilo y no abras PR.
