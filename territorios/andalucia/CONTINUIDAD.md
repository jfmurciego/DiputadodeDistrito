# Continuidad — Andalucía

**Proyecto:** Diputado de Distrito  
**Versión:** 1.0.0  
**Fecha:** 2026-09-11  
**Estado:** AND-01 cerrado; AND-02 cierre topológico en verificación

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

## AND-02 — auditoría topológica

Configuración actual: `config/andalucia_2025.yaml` v0.3.0.

Primera pasada sin pasarelas:

- M02: 16.669 aristas geométricas, predicado robusto `contact`.
- 8 provincias: todas conexas.
- nodos aislados: 0.
- únicamente dos municipios multipartes/discontinuos:
  - Cortegana: `2102502002`, 558 habitantes, ~3.064 m hasta `2102502001`.
  - Vélez-Málaga: `2909401015`, 886 habitantes, ~1.658 m hasta `2909403005`.

Contrato candidato v0.3.0 añade exclusivamente:

- `2102502002 ↔ 2102502001` como `administrative_bridge`.
- `2909401015 ↔ 2909403005` como `administrative_bridge`.

Está en ejecución la segunda pasada AND-02, que debe exigir 0 provincias y 0 municipios desconectados antes de cerrar el módulo.

## Siguiente módulo

AND-03 será la entrada a M04 y no se abrirá copiando parámetros de Extremadura/CYL. Primero se fijarán solo los datos estructurales demostrados:

- K=109.
- Hamilton DDD 9/16/10/12/7/8/22/25.
- topología AND-02 cerrada.

Tolerancia, suelo, techo y atomicidad municipal se someterán a un barrido diagnóstico comparable al EXT-03, una vez que M04 incorpore cualquier generalización necesaria descubierta en Extremadura.

## Regla de dependencia

Andalucía reutilizará el motor común. No se hará un fork andaluz de M04. Si EXT-03 demuestra una deficiencia general del modelo de unidades abiertas, se corregirá una sola vez en el motor y se validará después sobre Aragón, Castilla y León, Extremadura y Andalucía.
