## 2026-11-17 — T-383 — Documentación al día con los workflows migrados (D-142)

**Causa.** Con P10, P20, P30, P40, P50, P70, P80, P90 y P00 PR 1 y 4 migrados, la documentación viva seguía citando ficheros retirados.

**Cambio.** Solo documentación. Nuevo `docs/ARQUITECTURA/EQUIVALENCIAS_D129.md` 1.0.0 (qué hace cada workflow, opciones visibles en español, fichero viejo que sustituye, excepciones D-135/D-144/D-159; P00 PR 2a/2b/3 marcado pendiente sin diseño final). Referencias corregidas en `FICHAS_AGENTES` 1.1.1, `MADUREZ` 1.0.1 (copias en `legacy/2026-11-17_t383_docs/`), `ADR-001-enfoque`, `.claude/rules/workflows.md`, y notas en `INVENTARIO_OPERATIVO` y `CRITICAL_PATH_EJECUTABLES`. Sin tocar `.github/workflows/`, `herramientas/`, `modulos/` ni `ddd_core/`.

**No tocado (histórico, D-142):** `CORTE_5_0_0`, `DESLINDE_1_0` (citas de línea), `docs/ESTUDIOS/`, `autorizaciones/`, `traspasos/`, `AUDITORIAS/`, skills (`lanzar-00`/`lanzar-campana`/`publicar-visor` siguen con su nombre; la fusión en `lanzar-p00` y `publicar-p40` queda para la parte de skills de T-383), CLAUDE.md (sin referencias a ficheros retirados).

**Pruebas.** `tests.test_r015_invariantes.GovernanceHeaders`, guardián `todo`.

**Riesgos.** Ninguno funcional. Regla implícita anotada: `workflows.md` dice que `p40-publicacion.yml` pide `produccion` solo si `github.workflow ==` su nombre; no se cambia.
