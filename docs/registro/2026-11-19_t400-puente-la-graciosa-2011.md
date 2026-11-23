## 2026-11-19 — T-400 — nac35 2011-11: puente de La Graciosa ausente del seccionado 2012

**Causa (reproducida en local con `seccionado_2012.zip` sha256 772ad76b…).** `materializar` fallaba con `PUENTE_FUERA_DEL_SECCIONADO`: el contrato base 2025 declara el puente 3502401010–3502401001 (decisión del propietario 31-10-2026), pero en el seccionado 2012 La Graciosa no es sección propia: es uno de los dos polígonos de **3502401005** (el otro, en Lanzarote). El INE la segrega como 3502401010 en 2019; esa geometría queda contenida al 100 % en 3502401005 de 2012 (medido contra `seccionado_2019.zip` 656119da…, igual en 2022). Como la 005 ya une isla y Lanzarote, un puente trasladado a ella tampoco vale: M02 lo rechaza («bridge does not resolve a diagnosed disconnection»).

**Cambio.** `configuracion/historico_epoca/puentes_epoca.json` (declaración atada al sha256 del seccionado, con la evidencia del donante) y `herramientas/contrato_historico_epoca.py` 1.3.2: `_puentes_de_epoca` omite el puente cuyo extremo no existe si hay declaración (sección declarada existente y del mismo municipio); sin declaración o con otro seccionado, falla cerrado. Puentes con extremos presentes, intactos.

**Pruebas.** `tests/test_t365_historico_epoca.py` 1.4.2, clase `PuentesDeEpoca` (3 tests). Local, cadena real de nac35 2011-11: M01, M02 y M03 OK (antes fallaba en materializar y, con el puente trasladado, en M02).

**Riesgos / efectos.** Solo yaml de la época (no versionado); no toca M04/M05 ni huellas del motor; sin 00. nac35 2011-11 sigue sin generarse: M04 falla por dos causas ajenas a esta PR (reparto de K por partición insular y suelo de Fuerteventura 102.810 < 115.523), en el informe de T-400 (b). `no-automerge`.
