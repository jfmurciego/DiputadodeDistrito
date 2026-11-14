## 2026-11-14 — T-294 — Propuesta de analítica del visor sin cookies (fase 1)

- **Causa:** D-71 aplazaba la analítica sin cookies hasta publicar el visor v2; el propietario necesita decidir antes de montar nada.
- **Cambio:** solo documento `docs/ESTUDIOS/T294_ANALITICA_SIN_COOKIES/PROPUESTA.md`: tres opciones (Worker contador, autoalojada, solo hosting), marco LSSI/RGPD, encaje con GitHub Pages (sin cabeceras propias; CSP por meta), recomendación y texto de transparencia. No toca visor, workflows ni producción.
- **Pruebas:** `GovernanceHeaders` y `numerar_registro --comprobar`.
- **PR:** pendiente de abrir.
