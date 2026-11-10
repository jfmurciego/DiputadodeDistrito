## 2026-11-10 — T-160 — Núcleo único de reglas del motor 2 (F1, paso 1: modelo y evaluador)

- Causa: seis definiciones de «plan válido» (VAL, CAN/M05/REP, GCP, GCE y el certificador T-136) con divergencias
  inventariadas en T-137 (`docs/ESTUDIOS/T137_NUCLEO_REGLAS/INVENTARIO_DIVERGENCIAS.md`).
- Cambio: paquete nuevo `ddd_motor2/reglas/` (solo stdlib; producción no lo importa; huellas intactas):
  `Unidad`/`Problema`/`Reglas.desde_contrato` (falla si falta K, suelo, techo o tolerancia; sin 0,80/1,75), `evaluar`
  con códigos estables (`R-K`, `R-ATOM`, `R-POB-SUELO`, `R-POB-TECHO`, `R-TOL`, `R-CONTIG`, `R-PROV`, `R-CUOTA`,
  `R-MUN-MIN/MAX/MIXTOS`, `R-NUCLEO`), límites con fracciones exactas, códigos normalizados una vez, municipio como
  campo (nunca del `ddd_unit_id`) y `ErrorDatos` si falta un campo que una regla activa exige.
  Las cuatro decisiones de criterio y el umbral cadena/enumeración son parámetros (`Criterio`), con valores por
  defecto aprobados por el propietario (D-44): tolerancia métrica; `max_mixed` del contrato (1 por política); provincia única obligatoria en
  el contrato; exención por partición solo si todas las particiones del distrito están exentas; método
  «presupuesto de nodos» con diagnóstico 0,10/0,90 como comprobación posterior.
  `comparar_criterios` y `resumen_por_opcion` dan a la batería T-132 cuántos territorios cambian de veredicto con
  cada opción.
- Pruebas: `python -m unittest tests.test_motor2_reglas` (20 tests, uno o más por divergencia 1-8 del inventario).
- Siguiente: estado incremental, poda y enumerador; el certificador T-136 pasa a usar el núcleo.
