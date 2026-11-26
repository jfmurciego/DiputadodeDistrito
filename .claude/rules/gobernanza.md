---
paths:
  - "modulos/**"
  - "ddd_core/**"
  - "ddd_ensemble/**"
  - "herramientas/**"
  - "configuracion/**"
  - "docs/**"
  - "procedimiento.sh"
---

# Gobernanza de ficheros versionados

- Cada cambio de un fichero versionado sube su cabecera VERSIÓN (con FECHA, CAMBIOS, MOTIVO) y deja la copia
  anterior en `legacy/` con ANTERIOR apuntando a ella. Lo comprueba `tests.test_r015_invariantes.GovernanceHeaders`.
- Los documentos `docs/MODULOS/*.md` declaran la versión activa del código (test de gobernanza R015).
- El registro de cambios no se edita a mano: la entrada de cada PR va en `docs/registro/` y la numera un job de `main`
  (`.claude/rules/registro.md`).
- Fichero nuevo: cabecera con VERSIÓN 1.0.0 y `ANTERIOR: ninguna (fichero nuevo)`.
- No renombrar `modulos/0X_*`: están en las huellas M05, en las evidencias N08 y en los tests R015/R016.
- `herramientas/`, `modulos/`, `ddd_core/`, catálogo y política son compartidos: avisa a la otra sesión antes de tocarlos.
- No cambiar suelo, techo, K ni atomicidad sin decisión del propietario.
- Textos públicos (T-463, 26-11): `test_visor_v4_base::test_metodologia_en_lenguaje_llano` veta jerga («repositorio») en metodo.md. Cambiar un DOI exige el mismo valor en CITATION.cff, README y docs/PUBLICACION_ZENODO.md (cabecera versionada y legacy; `test_t127_metadatos_zenodo`). Suites largas (T-460): comparar por nombre de test contra un worktree de origin/main, no por recuento.
