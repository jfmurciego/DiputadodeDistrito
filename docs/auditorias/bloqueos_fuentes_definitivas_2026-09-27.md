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
- API oficial granular conocida: SIEL, `https://ws040.juntadeandalucia.es/siel-api/v1`
- estado DDD: **BLOCKED_FINAL_GRANULAR_SOURCE** mientras no se adquiera de forma reproducible una extracción definitiva a sección/mesa que reconcilie con 4.157.539.

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
- repositorio granular descrito por la Junta: `https://prensa.elecciones2025.juntaex.es`, con acceso mediante credenciales
- estado DDD: **BLOCKED_FINAL_GRANULAR_SOURCE** mientras no exista una adquisición pública/reproducible a sección/mesa que reconcilie con 524.837.

## Regla

No se sustituye una fuente definitiva por el provisional para obtener un PASS. Si aparece una fuente granular definitiva, el adaptador debe validar identidad, territorio, sección/mesa, votos, procedencia y huella y reconciliar exactamente contra los totales definitivos antes de producir un paquete registrable.
