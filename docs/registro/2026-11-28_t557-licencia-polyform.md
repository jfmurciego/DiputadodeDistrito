## 2026-11-28 — T-557 — Licencia del código: PolyForm Strict 1.0.0 (D-218)

- **Causa:** el repositorio no declaraba la licencia elegida por el propietario («Licencia B»; `docs/LICENCIA_OPCIONES.md`, PR #1043).
- **Cambio:** `LICENSE` pasa a ser el texto oficial de PolyForm Strict 1.0.0, byte a byte (fuente: etiqueta 1.0.0 de
  `polyformproject/polyform-licenses`, `PolyForm-Strict-1.0.0.md` vía raw.githubusercontent.com; 3593 bytes; sha256
  `9eb48619fbc193ab7bb327b090cfcc703000265b83e670f81f231d0b1c43c56e`; blob git `90abd0e6c64a135f42451762337a397bf27f4862`).
  La licencia propia anterior queda en `legacy/licencias/LICENSE_pre_t557_20261128.txt`. Los apartados 3 a 5 (datos CC BY,
  fotos de terceros, historial Apache-2.0, sin garantía) pasan a `AVISOS_LICENCIA.md`. Mención en `README.md` (rev. r3),
  `CONTRIBUTING.md`, `CITATION.cff` (`license`), `paquetes/deslinde/` (README y `pyproject.toml`) y `documentacion_publica/docs/metodo.md` 2.0.2.
- **Pruebas:** `tests/test_t557_licencia_polyform.py` (sha256 y tamaño literales; menciones; sin otra licencia para el código);
  adaptados `test_t325_licencia_terceros` y `test_t127_metadatos_zenodo`, que fijaban el texto de la licencia anterior.
- **Riesgos / pendiente:** no toca motor, huellas ni checkpoints (no hace falta 00). Pendiente de comprobar fuera de la nube:
  licencia y contenido de los depósitos de Zenodo; datos CC BY. Pendiente de decidir (objeción D-216): el pie de la web
  («Todos los derechos reservados»), `LEEME_KIT.md` (aún recomienda Apache-2.0) y `docs/PUBLICACION_ZENODO.md` no se han tocado;
  «reglas y contratos en CC BY 4.0» y «visor y web: derechos reservados» del antiguo apartado 3 se retiran porque son código y quedan
  bajo PolyForm Strict.
