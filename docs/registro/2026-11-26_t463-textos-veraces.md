## 2026-11-26 — T-463 — Textos públicos veraces y DOI de la serie

- Causa: la Metodología prometía «miles de mapas alternativos» (retirados el 16-11; hoy hay cero) y un programa que se puede «repetir» (la licencia exige permiso escrito).
- Cambio: `metodo.md` 2.0.1 (frase del motor actual: una docena de candidatos con criterio fijo; código legible, uso con permiso); README rev. 5.0.0-r2 y `CITATION.cff` con el DOI de la serie 10.5281/zenodo.24448721 (el de Huesca queda como versión 1.0.0); `PUBLICACION_ZENODO.md` 2.0.1; test T-127 actualizado. Legacy con ANTERIOR.
- Pruebas: `grep -rn` en tests/ de cada literal; test_t127, test_t429, test_visor_v4_base y GovernanceHeaders en local.
- Riesgos: ninguno de producto. El sitio no cambia hasta que el Operador publique «solo el sitio» con frase del propietario.
- PR: esta.
