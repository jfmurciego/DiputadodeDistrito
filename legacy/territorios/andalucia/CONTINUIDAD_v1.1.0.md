# Continuidad — Andalucía

**Proyecto:** Diputado de Distrito  
**Versión:** 1.1.0  
**Fecha:** 2026-09-11  
**Estado:** AND-01 y AND-02 cerrados; AND-03 pendiente de generalización M04

## Baseline AND-01 certificado

- Secciones: **6.029**.
- Población total 2025: **8.676.713**.
- Faltantes de población: **0**.

Por provincia:

- Almería (04): 469 secciones / 770.554 habitantes.
- Cádiz (11): 923 / 1.261.420.
- Córdoba (14): 622 / 773.163.
- Granada (18): 674 / 945.797.
- Huelva (21): 374 / 538.789.
- Jaén (23): 498 / 618.143.
- Málaga (29): 1.092 / 1.791.183.
- Sevilla (41): 1.377 / 1.977.664.

K institucional de referencia: **109**.

Hamilton DDD puramente poblacional de referencia: **9 / 16 / 10 / 12 / 7 / 8 / 22 / 25** para 04/11/14/18/21/23/29/41 respectivamente.

La regla electoral vigente y su reparto de 2026 están conservados por separado en `fuentes/normativa/andalucia_sistema_electoral_2026.md`; no se usan como cuotas DDD.

## AND-02 — cerrado

Configuración: `config/andalucia_2025.yaml` v0.3.0.

Primera pasada sin pasarelas:

- M02: 16.669 aristas geométricas, predicado robusto `contact`.
- 8 provincias: todas conexas.
- nodos aislados: 0.
- únicamente dos municipios multipartes/discontinuos:
  - Cortegana: `2102502002`, 558 habitantes, ~3.064 m hasta `2102502001`.
  - Vélez-Málaga: `2909401015`, 886 habitantes, ~1.658 m hasta `2909403005`.

Contrato v0.3.0 añade exclusivamente:

- `2102502002 ↔ 2102502001` como `administrative_bridge`.
- `2909401015 ↔ 2909403005` como `administrative_bridge`.

Ejecución de cierre AND-02:

- M01: **6.029 nodos**, población completa.
- M02: **16.671 aristas = 16.669 geométricas + 2 administrativas**.
- M03: **0 aislados, 0 provincias desconectadas, 0 municipios desconectados**.
- Auditoría geométrica posterior: **0 componentes provinciales y 0 componentes municipales pendientes**.

## Siguiente módulo

AND-03 será la entrada a M04 y no se abrirá copiando parámetros de Extremadura/CYL. Primero se fijarán solo los datos estructurales demostrados:

- K=109.
- Hamilton DDD 9/16/10/12/7/8/22/25.
- topología AND-02 cerrada.

Tolerancia, suelo, techo y atomicidad municipal se someterán a un barrido diagnóstico comparable al EXT-03 **después** de resolver y validar la generalización M04 que está descubriendo Extremadura. Esto evita lanzar decenas de ejecuciones andaluzas sobre una condición de conectividad que ya sabemos sospechosa.

## Regla de dependencia

Andalucía reutilizará el motor común. No se hará un fork andaluz de M04. Si EXT-03 demuestra una deficiencia general del modelo de unidades abiertas, se corregirá una sola vez en el motor y se validará después sobre Aragón, Castilla y León, Extremadura y Andalucía.
