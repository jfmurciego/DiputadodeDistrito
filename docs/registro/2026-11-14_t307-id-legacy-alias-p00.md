## 2026-11-14 — T-307 — El registro de la preparación escribe el id canónico; la puerta sigue estricta

- Causa: la regeneración deslinde11-r2 (aut01-aut05) falló en «Verificar datos territoriales preparados» porque los paquetes P10 llevaban el id legacy (`andalucia`) y el run pide el nuevo (`aut01`); además el registro de la preparación escribió ids legacy en los yamls de los territorios. Criterio del propietario: motor repetible, sin aceptar ids legacy; los P10 se rehacen con ids nuevos.
- Cambio: `adquirir_fuentes_oficiales` 1.4.3 escribe siempre el id canónico resuelto (`aut02`) en inventario, procedencia y `resolved_source_contract`, aunque la declaración lleve el legacy (`aragon`). La puerta y las comparaciones de la cadena P00 quedan estrictas: no se añade ninguna aceptación por alias.
- Pruebas: `tests/test_t307_territory_id_alias.py` (`RegistroIdCanonicoTests` rojo con main y verde ahora; la puerta rechaza el id legacy).
- Efectos: sin cambio de huellas M04/M05; los P10 y los yamls ya escritos los rehace/revierte T-308.
