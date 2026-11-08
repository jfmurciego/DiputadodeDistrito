## 2026-11-08 — T-94c — LICENSE y requisitos de repositorio de JOSS

**Causa.** El borrador de JOSS (#512) detectó que `CITATION.cff` y `.zenodo.json` declaran Apache-2.0 sin fichero `LICENSE`, y que
faltaban `CONTRIBUTING.md` y código de conducta.

**Cambio.** `LICENSE` = texto oficial de https://www.apache.org/licenses/LICENSE-2.0.txt (sha256
`cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`, descargado, no escrito de memoria; sin apéndice rellenado).
`CONTRIBUTING.md` (instalación, pruebas, flujo) y `CODE_OF_CONDUCT.md` (Contributor Covenant 2.1, fuente oficial en GitHub; contacto = mantenedor).
No se toca código, datos, README ni versiones.

**Pendiente (no resuelto).** Versión: `CITATION.cff` 4.7.0 (fecha 2026-09-20) frente a «README v4.9.0» (versión del documento README, no
necesariamente del proyecto); no hay VERSIÓN de proyecto ni etiquetas que decidan. Se consulta al Coordinador/propietario. La licencia es
decisión del propietario: PR `no-automerge`. Sin DOI ni afiliaciones inventados.

**Pruebas.** Gobernanza R015 y guardián de `main` (ver PR).
