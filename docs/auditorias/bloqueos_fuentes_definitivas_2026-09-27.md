# Bloqueos de fuente electoral definitiva — 2026-09-27

Este documento separa disponibilidad de escrutinio provisional granular de validez como fuente electoral definitiva para DDD. Una fuente provisional puede demostrar formato y granularidad, pero no se promueve si no reconcilia con el resultado definitivo oficial.

## Andalucía — Parlamento 2026

- elección: `andalucia_parlamento_2026`
- fecha: `2026-05-17`
- fuente granular disponible: export Minsait/EleccionesDB, escrutinio provisional
- granularidad observada: 6.044 secciones
- votos a candidaturas observados en provisional: **4.128.575**
- referencia definitiva: Junta Electoral de Andalucía, BOJA 115 de 17-06-2026, corrección del resumen general
- votos a candidaturas definitivos: **4.157.539**
- delta definitivo - provisional: **28.964**
- referencia: https://www.juntadeandalucia.es/boja/2026/115/1
- decisión operativa de #147: usar el CSV granular ya disponible como fuente de trabajo, conservando su clasificación **PROVISIONAL**.
- estado DDD para #147: **PACKAGEABLE_IN_COPY / PRODUCTION_BLOCKED**. El CSV está fijado por SHA-256, tiene 6.044 secciones y 10.403 mesas, y puede producir paquete + registro en copia. El paquete declara `production_eligible=false`; no sustituye ni pretende sustituir una fuente definitiva.

## Extremadura — Asamblea 2025

- elección: `extremadura_asamblea_2025-12-21`
- fecha: `2025-12-21`
- fuente granular disponible: export Minsait/EleccionesDB, escrutinio provisional
- granularidad observada: 966 secciones
- votos a candidaturas observados en provisional: **522.418**
- referencia definitiva: Junta Electoral de Extremadura, DOE 8 de 14-01-2026
- Badajoz, votos a candidaturas: 326.196
- Cáceres, votos a candidaturas: 198.641
- total definitivo: **524.837**
- delta definitivo - provisional: **2.419**
- referencia: https://doe.juntaex.es/otrosFormatos/html.php?anio=2026&doe=80o&xml=2026AC0001
- repositorio granular descrito por la Junta: `https://prensa.elecciones2025.juntaex.es`, con acceso mediante credenciales; la documentación oficial lo describe como repositorio de **resultados provisionales**
- gobierno DDD del repositorio de prensa: `data_status: provisional_only`, `promotion_allowed: false`; el checker común lo bloquea antes de red con `BLOCK_NOT_PROMOTABLE`
- estado DDD: **BLOCKED_FINAL_GRANULAR_SOURCE** mientras no exista una adquisición pública/reproducible definitiva a sección/mesa que reconcilie con 524.837.

## Regla

Una fuente provisional puede cerrar la **prueba técnica de paquete + registro en copia** si su estado queda explícito y el paquete declara `production_eligible=false`. No puede usarse para registro productivo ni presentarse como definitiva. Si aparece una fuente granular definitiva, deberá validarse identidad, territorio, sección/mesa, votos, procedencia y huella antes de sustituir la provisional.
