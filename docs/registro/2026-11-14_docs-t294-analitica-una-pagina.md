## 2026-11-14 — T-294 — Propuesta de analítica sin cookies condensada a una página

- **Causa:** la PR #767 se fusionó con la versión larga (116 líneas); el propietario pide una página como máximo.
- **Cambio:** solo `docs/ESTUDIOS/T294_ANALITICA_SIN_COOKIES/PROPUESTA.md`: cuatro opciones (contador propio, GoatCounter, Plausible, ninguno), privacidad y recomendación. No toca visor, workflows ni producción.
- **Pruebas:** `GovernanceHeaders` y `numerar_registro --comprobar`.
- **PR:** pendiente de abrir (etiqueta `no-automerge`).
