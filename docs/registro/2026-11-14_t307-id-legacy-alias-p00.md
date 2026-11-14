## 2026-11-14 — T-307 — La cadena P00 acepta el id legacy del paquete P10 (alias D-61)

- Causa: la regeneración deslinde11-r2 (aut01-aut05) fallaba en «Verificar datos territoriales preparados»: `evaluar_preparacion_territorial` comparaba con `!=` la cabecera `territory_id` del paquete P10 (id legacy, p. ej. `andalucia`) con el id nuevo del run (`aut01`).
- Cambio: esa comparación y las que quedaban estrictas en la cadena (`validar_puerta_ejecucion` namespace y territorio certificado, `validar_paquete_electoral` manifiesto, `ddd_ensemble/prepared_bundle`, `fuente_infoelectoral_mesas`) usan `mismo_territorio` (resolutor D-61): se acepta si ambos ids resuelven al mismo id canónico; cualquier otra discrepancia sigue bloqueando. `evaluar_preparacion_territorial` 1.2.1 y `fuente_infoelectoral_mesas` 1.0.1, con copia legacy. Sin cambios en workflows (los de `recuperar-producto-electoral-durable` comparan ids del mismo run).
- Pruebas: `tests/test_t307_territory_id_alias.py` (alias aceptado, id ajeno rechazado; rojo antes, verde después).
- Efectos: sin cambio de huellas M04/M05 ni de producto; basta relanzar la tanda 1.
