## 2026-11-28 — T-519 — Repetición del exacto de Deslinde en cuatro condiciones de máquina

- **Causa:** T-509, hallazgo A1-4: cuatro de los nueve mapas que gana el exacto (nac12, nac15, nac41 y nac43) son «mejor
  válido» y solo se habían ejecutado una vez. Había que saber antes de la regeneración del 29-11 si se repiten.
- **Medición** (`docs/ESTUDIOS/T519_REPETICION_EXACTO/INFORME.md`, `RESULTADOS.json` y `TABLA.md`; motor real, en local,
  `main` 548968c4): nac12, nac15, nac20, nac41 y nac43, cuatro competiciones cada uno (dos en reposo, una con un solo
  núcleo y una con carga). nac15, nac20 y nac41 repiten ganador, mapa y `huella_resultado`. nac12 repite el mapa y da dos
  huellas (el exacto cierra la última etapa en dos de cuatro). nac43 da dos mapas (467,2 km y 386,8 km de frontera). Las
  dos ejecuciones en reposo ya difieren: no depende de la velocidad. El tope ya es tiempo determinista de CP-SAT.
- **Cambio:** solo el estudio y su guion (`repetir.sh`, `tabla.py`, `carga.py`). El motor no cambia. Opción de arreglo y
  criterio de aceptación, en el informe; no implementada.
- **Pruebas:** `bash docs/ESTUDIOS/T519_REPETICION_EXACTO/repetir.sh` (20 competiciones, unos 50 min). Nada lanzado ni
  publicado.
