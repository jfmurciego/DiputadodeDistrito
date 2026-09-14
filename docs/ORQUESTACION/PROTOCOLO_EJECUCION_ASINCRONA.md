# Protocolo de ejecución asíncrona DDD

**Versión:** 1.0.0  
**Estado:** vigente  
**Canal de finalización:** issue #5, `DDD — Orquestación asíncrona`

## Principio

GitHub Actions ejecuta; ChatGPT prepara y reanuda. Nunca se mantiene una sesión abierta esperando un cálculo.

## Ciclo de un lote

1. ChatGPT prepara un lote autocontenido: cambios, workflow, criterios de aceptación y reversibilidad.
2. Se lanza una única ejecución pesada, que incluye preflight, cálculo, validación, persistencia de evidencia y resumen.
3. ChatGPT termina inmediatamente y actualiza `PUNTO_REENGANCHE.md`.
4. El workflow de finalización publica el resultado en issue #5 y menciona a `@jfmurciego`.
5. Tras el correo de GitHub, el siguiente chat se reanuda desde el punto registrado.

## Reglas

- Un workflow debe encadenar todos los pasos deterministas del lote.
- Sólo debe detenerse ante `FAIL`, `BLOCKED` o una decisión no automatizable.
- Cada lote debe generar `RUN_SUMMARY.json` y evidencia durable.
- Antes de crear un workflow pesado, incluir su nombre en `.github/workflows/notificar-finalizacion-orquestacion.yml`.
- No se hace sondeo de runs desde ChatGPT salvo petición expresa del usuario.
- No se ejecutan territorios posteriores sin autorización expresa.

## Notificación por correo

El repositorio publica una mención en el issue #5 al terminar cada workflow registrado. GitHub entrega esa notificación por correo si la cuenta tiene activados los avisos de *participación y menciones* y el usuario está suscrito al issue.
