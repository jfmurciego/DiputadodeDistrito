# Territorios DDD

**Versión:** 2.0.0  
**Fecha:** 2026-09-11  
**Anterior:** `legacy/memoria/TERRITORIOS_README_v1.0.0.md`

Cada subdirectorio representa una implantación del motor común. Ningún territorio contiene un fork de `ddd_core/` ni de `modulos/`.

## Activos

- `aragon/` — implantación de referencia protegida. Baseline territorial Run #9 / R016. R020 adopta M06 v7.1.0 con catálogo de 67 distritos y composición de 1.463 secciones sin alterar la distritación.
- `castilla_y_leon/` — segunda implantación validada. CYL-04 cerró M05 con 82 distritos, hard=0 y fuera_12=0; CYL-05 cerró M06 con catálogo de 82 distritos y composición de 3.506 secciones. M07 está bloqueado solo por ausencia de una fuente electoral territorial validada.
- `extremadura/` — tercera prueba de portabilidad. EXT-01 validó M01 con 964 secciones, 1.053.345 habitantes y 0 faltantes. EXT-02 audita M02/M03 y singularidades topológicas antes de declarar K o coeficientes de distritación.

## Madurez de la arquitectura

El motor ya ha superado optimización y consolidación en dos territorios. Extremadura se utiliza para medir el coste marginal de incorporación y para detectar supuestos que aún deban generalizarse.

La meta no es que todos los territorios usen idénticos parámetros, sino que las diferencias sean **datos y contrato declarativo** siempre que sea posible.

## Regla

Un territorio aporta configuración, inputs, documentación, pruebas y excepciones topológicas explícitamente auditadas. Cualquier necesidad de modificar el motor debe justificarse como generalización reusable, nunca como parche local oculto.

Los bloqueos se corrigen en el módulo que crea la restricción: M02 para adyacencia, M04 para granularidad/factibilidad estructural, M05 para optimización y M06 para materialización/auditoría.
