# Propuesta de cierre de adquisición y acreditación F10

**Estado propuesto: NO CERRAR F10 todavía.** Se conserva la separación entre acreditación territorial, consumo territorial, correspondencia electoral y producción. La matriz verificable de 19 registros está en [matriz_19_consumidores.json](matriz_19_consumidores.json).

Los 14 receipts históricos conservan su SHA de paquete e identidad territorial y la regresión `test_fourteen_historical_receipts_remain_and_extremadura_f10_is_unpromoted` pasa. Los cuatro receipts independientes añadidos tras #252 pasan la validación real de receipt para Extremadura (`38091144559`), Aragón (`38093067883`), Castilla y León (`38091055890`) y Andalucía (`38082966768`). En Extremadura siguen separados el receipt nuevo, preparación `35755043806` y producto histórico M06 `36472516474`; el receipt no está promovido. En las otras tres comunidades se conserva la selección autorizada 2025/2025 sin modificar la decisión aprobada en #250.

Valencia tiene cobertura poblacional exacta para 2023/2023, pero la admisibilidad de su fuente territorial sigue bloqueada por dos solapamientos mayores que 1 m² sin corrección oficial acreditada. Su receipt territorial versionado bajo #179 no existe. La decisión mínima es recibir del INE una geometría corregida/fe de erratas para esos dos pares, o que Work decida mantener el bloqueo o emitir una excepción contractual explícita. Una excepción no convertiría la geometría en corregida ni se ha aplicado.

La correspondencia electoral 2025 territorial → 2026 para Extremadura, Aragón, Castilla y León y Andalucía sigue bloqueada por evidencia oficial pendiente. Esta dependencia no invalida los cuatro receipts territoriales ni permite declarar PASS conjunto. No se cambia el año de las fuentes, no se ejecuta producción y no se habilita generación.

La prueba local de resolución de los 19 planes separa esos estados. Los 14 consumidores históricos permanecen `PASS` en su puerta efectiva F03; cuatro recibos F10 pasan como fuentes territoriales; Valencia queda bloqueada geométricamente. Producción no se ejecutó en ninguno. Por estas razones, esta entrega documenta el cierre de lo acreditable y deja F10 global `BLOCKED`, sin declarar adquisición/acreditación completa.

## Condiciones para cerrar

1. Resolver los dos solapamientos valencianos mediante fuente/corrección oficial, o una decisión explícita de Work sobre una excepción contractual con alcance delimitado.
2. Obtener el receipt/adaptador #179 y lograr aceptación del consumidor territorial real de Valencia.
3. Mantener las correspondencias electorales abiertas en su frente; no forman parte del cierre territorial de F10 y no deben ocultarse como PASS conjunto.
4. Repetir matriz, regresiones y revisión sobre el HEAD que integre el incremento autorizado.
