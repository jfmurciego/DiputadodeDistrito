# Progress Log — Diputado de Distrito

**Versión:** 1.0.0  
**Fecha de inicio:** 2026-09-11  
**Objeto:** registro persistente de hitos, decisiones y bloqueos. Los logs completos y artefactos pesados permanecen en GitHub Actions; este fichero conserva los resultados que cambian el baseline o la arquitectura.

## 2026-09-11

### Aragón — referencia protegida
- R020: M06 v7.1.0 confirmado con 67 distritos, 1.463 secciones, 1.364.621 habitantes, `fuera_12=0`, max dev 9,9299366%.
- Catálogo y composición M06 adoptados sin alterar asignaciones.

### Castilla y León — CYL-04 / CYL-05
- M04 v7.4.8 resuelve bloqueo residual con una micro-unidad flexible mínima en Ávila.
- M05: 82 distritos, contigüidad 82/82, `hard=0`, `fuera_12=0`, max dev ~11,98%.
- M06 v7.1.0: 82 distritos, 3.506 secciones, 2.401.221 habitantes; identidad M05=M06.
- M07 bloqueado por ausencia de fuente electoral territorial real.

### Extremadura — EXT-01 / EXT-02
- M01: 964 secciones, 1.053.345 habitantes, 0 faltantes.
- Badajoz: 553 / 665.155. Cáceres: 411 / 388.190.
- M02 v7.2.0 introduce `contact` robusto y elimina la falsa desconexión de Monesterio causada por micro-solape cartográfico.
- Contrato topológico final: dos `administrative_bridge` internos de Don Benito: `0604405005↔0604405003` y `0604405006↔0604405004`.
- Cierre EXT-02: 2.607 aristas = 2.605 geométricas + 2 administrativas; M03 con 0 aislados, 0 provincias y 0 municipios desconectados.

### Extremadura — EXT-03 / M04
- K institucional documentado: 65. Hamilton DDD poblacional: Badajoz 41 / Cáceres 24.
- Barrido legacy tight/reference/wide: tres fallos distintos; referencia aislaba La Albuera y wide aislaba Aliseda después de prepartir capitales.
- Auditoría causal: La Albuera depende de dos puertas del municipio de Badajoz; Aliseda depende de una puerta del municipio de Cáceres. M03 es correcto; el aislamiento nace en M04.
- M04 v7.5.0 (`preserve_all_external_gateways`): descartado como política; sobreprotege capitales y evita extraer núcleos.
- M04 v7.5.1 (`preserve_component_gateways`): preserva una puerta por componente exterior, pero Badajoz sigue sin admitir un único residuo municipal conexo con cuatro puertas necesarias. R015 legacy permanece verde.
- Hipótesis activa: el supuesto erróneo es exigir un único residuo abierto por municipio sobredimensionado. Se lanza A/B `granular-open` para probar municipios grandes como unidades abiertas a nivel sección manteniendo municipios pequeños atómicos.

### Andalucía — AND-01 / AND-02
- AND-01: 6.029 secciones, 8.676.713 habitantes, 0 faltantes.
- Población: 04=770.554; 11=1.261.420; 14=773.163; 18=945.797; 21=538.789; 23=618.143; 29=1.791.183; 41=1.977.664.
- K institucional documentado: 109. Hamilton DDD poblacional de referencia: 9/16/10/12/7/8/22/25.
- AND-02 inicial: ocho provincias conexas; solo dos discontinuidades municipales reales.
- Contrato topológico: Cortegana `2102502002↔2102502001`; Vélez-Málaga `2909401015↔2909403005`.
- Cierre AND-02: 16.671 aristas = 16.669 geométricas + 2 administrativas; M03 con 0 aislados, 0 provincias y 0 municipios desconectados.
- AND-03 se mantiene detrás de la generalización M04 de EXT-03 para no multiplicar ejecuciones sobre un supuesto ya cuestionado.

### Arquitectura / herramientas
- M06 v7.1.0 pasa a baseline multi-territorio.
- `herramientas/auditar_geometria_componentes.py`: auditoría reusable de componentes desconectadas.
- `herramientas/auditar_conectividad_m04.py`: auditoría reusable de dependencias territoriales antes de M04.
- M04 v7.4.8 congelado en legacy antes de experimentos 7.5.x.
- `territorios/README.md` actualizado a v3.0.0 con cuatro implantaciones activas.

## Regla de uso

Cada resultado que cambie baseline, contrato territorial o algoritmo debe añadirse aquí o en la `CONTINUIDAD.md` del territorio. Los experimentos fallidos se registran cuando descartan una hipótesis arquitectónica útil; no se conservan como baseline activo.
