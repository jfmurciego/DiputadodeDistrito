## 2026-11-09 — T-130 — El Gestor sigue la 00 que lanzó, no la hija del bot

Causa: `Territorio.poll` tomaba como resultado la 00 más reciente del territorio. En el run 42637133308 (Cantabria/Extremadura) siguió la «00 Reutilizar» hija encadenada por el bot (42651881625) en vez de la 00 de prueba (42637193077) y el run murió.
Cambio: `legislatura_vigente.py` 1.2.1 (copia en `legacy/`): resultado = el de la primera 00 (la lanzada por el Gestor); la hija solo cuenta si hay que publicar, porque el eslabón electoral es el que se publica (hija fallida → FALLO «eslabón encadenado»; si no, se publica la última).
Pruebas: test nuevo `test_hija_fallida_del_bot_no_hunde_la_00_propia` (falla con el código anterior, pasa ahora); `test_legislatura_vigente`, `test_gestor_campanas_2` y `GovernanceHeaders` OK.
Riesgos: con publicar = sí, una hija fallida sigue deteniendo ese territorio (deliberado). No toca motor, huellas ni workflows.
