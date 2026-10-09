# Continuidad — Andalucía

**Proyecto:** Diputado de Distrito  
**Versión:** 1.2.0  
**Fecha:** 2026-09-11  
**Estado:** AND-01/AND-02 cerrados; AND-03 readiness cerrado; M04 espera política multi-identidad validada en EXT-03.
**Anterior:** `legacy/territorios/andalucia/CONTINUIDAD_v1.1.0.md`

## Baseline AND-01
- 6.029 secciones.
- 8.676.713 habitantes.
- 0 faltantes.
- Provincias: 04=770.554; 11=1.261.420; 14=773.163; 18=945.797; 21=538.789; 23=618.143; 29=1.791.183; 41=1.977.664.
- K=109.
- Hamilton DDD: **9/16/10/12/7/8/22/25**.

## AND-02 — topología cerrada
- M02: 16.671 aristas = 16.669 geométricas + 2 administrativas.
- Puentes: Cortegana `2102502002↔2102502001`; Vélez-Málaga `2909401015↔2909403005`.
- M03: 0 aislados, 0 provincias y 0 municipios desconectados.

## AND-03 readiness — escala municipal
Run `34626804248` SUCCESS. Target con K=109: **79.602,87 habitantes**.

Municipios que superan múltiplos del target:
- >1,05×: 20
- >1,10×: 19
- >1,12×: 18
- >1,20×: 13
- >1,50×: 10
- >1,75×: 9

Mayores ratios observados:
- Sevilla: 688.714 = **8,652× target**.
- Málaga: 597.173 = **7,502×**.
- Córdoba: 324.159 = **4,072×**.
- Granada: 235.294 = **2,956×**.
- Jerez: 215.025 = **2,701×**.
- Almería: 204.772 = **2,572×**.
- Marbella: 160.478 = **2,016×**.
- Huelva: 143.774 = **1,806×**.
- Dos Hermanas: 142.463 = **1,790×**.
- Algeciras: 126.500 = **1,589×**.

## Implicación de arquitectura
Andalucía demuestra que la cuestión de municipios sobredimensionados no es una excepción extremeña: el motor debe soportar ciudades equivalentes a 8–9 distritos internos sin perder identidad municipal ni crear fragmentación arbitraria.

El diseño candidato está en `docs/DISENO_M04_MUNICIPIOS_SOBREDIMENSIONADOS.md`: separar `municipality_field` real de una identidad/unidad de partición interna de M04. No se ejecutará el M04 masivo andaluz hasta que EXT-03 determine si esa granularidad debe ser por sección, por piezas conectas mayores o acompañada de operadores compuestos M05.

## Dependencia activa
EXT-03 ha demostrado que granularizar por sección desbloquea M04, pero el primer M05 mantiene 2 outliers y puede fragmentar demasiado los grandes municipios. La herramienta `auditar_bloqueos_m05.py` debe explicar esos dos bloqueos. Solo después se promoverá una política M04 común y se lanzará AND-03 M04.
