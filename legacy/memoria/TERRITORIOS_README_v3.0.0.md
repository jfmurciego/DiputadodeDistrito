# Territorios DDD

**Versión:** 3.0.0  
**Fecha:** 2026-09-11  
**Anterior:** `legacy/memoria/TERRITORIOS_README_v2.0.0.md`

Cada subdirectorio representa una implantación del motor común. Ningún territorio contiene un fork de `ddd_core/` ni de `modulos/`.

## Activos

- `aragon/` — implantación de referencia protegida. R020 adopta M06 v7.1.0 con 67 distritos, 1.463 secciones, 1.364.621 habitantes, `fuera_12=0` y catálogo/composición completos sin alterar la distritación histórica.
- `castilla_y_leon/` — segunda implantación validada hasta M06. CYL-04 cerró M05 con 82 distritos, `hard=0`, `fuera_12=0` y desviación máxima ~11,98%; CYL-05 materializó catálogo de 82 distritos y composición de 3.506 secciones. M07 está bloqueado únicamente por ausencia de fuente electoral territorial validada.
- `extremadura/` — tercera implantación. EXT-02 está cerrado: 964 secciones, 1.053.345 habitantes, topología M03 completamente conexa mediante predicado geométrico robusto y dos pasarelas administrativas auditadas en Don Benito. EXT-03 está generalizando M04 con K=65 y Hamilton 41/24; no se han promovido todavía tolerancias o atomicidad.
- `andalucia/` — cuarta implantación y primera gran prueba de escala poblacional. AND-01 cerró M01 con 6.029 secciones, 8.676.713 habitantes y 0 faltantes. AND-02 cerró M03 con 16.671 aristas, 0 aislados, 0 provincias desconectadas y 0 municipios desconectados; solo requiere dos pasarelas administrativas auditadas, Cortegana y Vélez-Málaga. AND-03 queda deliberadamente detrás de la generalización M04 de Extremadura.

## Orden operativo

1. Mantener Aragón como regresión de referencia.
2. Mantener Castilla y León como segunda regresión de extremo a extremo hasta M06.
3. Resolver EXT-03/M04 en Extremadura y promover únicamente reglas generales demostradas.
4. Aplicar el M04 generalizado a Andalucía y someter sus parámetros a barrido propio antes de promover un contrato AND-03.
5. M07 se abre por territorio solo cuando existe una fuente electoral real, documentada y trazable.

## Madurez de la arquitectura

M01-M03 ya se han reutilizado en cuatro territorios sin forks. M06 está certificado en Aragón y Castilla y León. El foco actual de generalización es M04: preservar la conectividad del territorio abierto cuando municipios sobredimensionados se dividen en núcleos cerrados y residuos.

La meta no es imponer parámetros idénticos. El motor común debe ser estable; K, cuotas, tolerancias, atomicidad y singularidades deben ser **datos y contrato declarativo** siempre que sea posible.

## Regla

Un territorio aporta configuración, inputs, documentación, pruebas y excepciones topológicas explícitamente auditadas. Cualquier necesidad de modificar el motor debe justificarse como generalización reusable, nunca como parche local oculto.

Los bloqueos se corrigen en el módulo que crea la restricción: M02 para adyacencia, M04 para granularidad/factibilidad estructural, M05 para optimización y M06 para materialización/auditoría.
