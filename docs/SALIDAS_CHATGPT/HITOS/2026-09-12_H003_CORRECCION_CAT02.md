# H003 — Corrección de orquestación CAT-02

**Versión:** 1.0.0  
**Fecha:** 2026-09-12  
**Estado:** relanzado  
**Anterior:** H002  
**Run fallido:** `34688010519`

CAT-02 v2.0.0 reprodujo M01 y M02, pero el diagnóstico no encontró sus ficheros porque `BASE` no se exportó al contenedor. Se preservó el workflow y v2.0.1 corrige únicamente esa variable. No cambia código territorial, topología ni criterios de certificación.
