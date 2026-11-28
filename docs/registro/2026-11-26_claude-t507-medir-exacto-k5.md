## 2026-11-26 — T-507 — El exacto con K ≥ 5: medición en local

- **Causa:** #1035 (Deslinde 1.2) aplica el exacto con K ≥ 5 si átomos × K ≤ 2.000 (`TAMANO_MAX`). Había que comprobar
  que ningún territorio empeora ni pasa de 10 min.
- **Medición** (`docs/ESTUDIOS/T507_EXACTO_K5/INFORME.md` y `RESULTADOS.json`; motor real, en local, antes = `main` a1132d2e,
  después = Deslinde 1.2): 25 de los 27 candidatos (Madrid no se puede medir en la nube). Ninguno empeora; el máximo es
  161 s; `TAMANO_MAX = 2.000` se queda. Gana el exacto en nac04, nac12, nac14, nac15, nac23, nac33, nac39, nac41 y nac43.
  Cambia `huella_resultado` en esos y en nac06, nac17, nac18, nac20, nac31, nac45, aut18 y aut19 (17 en total). Madrid
  (nac28, aut13) no puede aplicar (178 municipios × K > 2.000). nac48 falla en el canónico con las entradas de la nube y
  no está medido.
- **Cambio:** solo test (`tests/test_t503_exacto_tamano.py` 1.1.0): con `TAMANO_MAX = 0`, `aplicable` e `info` son
  iguales a los de la 1.0.0 archivada en 15 casos. Se salta sin `legacy/` (imagen de CI). El motor no cambia.
