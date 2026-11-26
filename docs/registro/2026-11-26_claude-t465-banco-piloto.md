## 2026-11-26 — T-465/T-466 — Piloto del banco: Deslinde frente a GerryChain puro y el óptimo exacto

- **Causa:** el plan de mejora (bloque B) pide medir el motor contra referencias externas. El propietario aprobó solo el
  piloto: Burgos, Valladolid, La Rioja, Sevilla y Madrid, con GerryChain puro y el exacto.
- **Cambio:** estudio en `docs/ESTUDIOS/T465_BANCO_PILOTO/`, con el diseño de una página, `gerrychain_puro.py` (ReCom
  sobre los átomos del exacto, juzgado con la clave D8 oficial), `tabla.py`, los resultados y el informe con la decisión.
  No toca el motor, la producción ni las huellas.
- **Resultado:**
  - el exacto demuestra el óptimo D8 en los 4 territorios;
  - Deslinde lo iguala en Burgos, Valladolid y La Rioja, y pierde en Sevilla (8 demarcaciones partidas frente a 6);
  - GerryChain puro (10 semillas a 10⁵ pasos) no mejora a Deslinde en ninguno.
  
  Madrid da FALLO_ADQUISICION en la nube y pasa al banco completo. Decisión: seguir, con el exacto como referencia
  principal.
- **Pruebas:** ejecución local en la sesión cloud, con unas 7,2 h de CPU (6,9 h de ellas de GerryChain).
