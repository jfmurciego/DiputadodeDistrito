# Autorización 2026-11-11_lerida-reintentos-publicacion-71

- Chat del Operador: session_01KQDtFsAtHP9atzNnDthr9A.
- Frase literal del propietario (2026-11-11 16:39 aprox.): «Autorizo, sin publicar hasta el punto 3: (1) preparar de nuevo las fuentes territoriales de Congreso Lérida y su ejecución completa con el motor nuevo; (2) reintentar una sola vez cualquier ejecución de la regeneración que falle por causa transitoria; (3) cuando las 71 estén completas y el arreglo de la publicación esté en main, publicar en el visor las 71 juntas en un solo lote, con su mapa y sus resultados.»
- Causa del punto 1 (corregida, T-250): el paquete de Lérida está vivo (hasta 01-12); la P00 43043776004 cayó por «HTTP 503: Egress is over the account limit» (cuota de egress de la cuenta agotada) = transitorio. Se cancela la P10 y Lérida se reintenta con su P00 (punto 2) cuando se reponga la cuota.

## Límites
| Punto | Contenido |
|---|---|
| (1) Lérida | `preparacion-fuentes.yml` («P10 Fuentes — P11 Territoriales») `territory_id=Congreso Lérida`; después P00 Campaña «Generar desde fuente territorial acreditada», `motor=motor2`, Canónico, `territorial_only`, `cadena_electoral=true`, `publish_result=false` |
| (2) Reintentos | 1 por ejecución de las campañas de regeneración vigentes (Congreso, nocturna v2, reparación), solo tras fallo transitorio acreditado en el log (red, runner, rate limit, push rechazado por contención) |
| (3) Publicación | una P50 en lote «Visor territorial» con las 71 (52 Congreso + 19 autonómicas), solo cuando las 71 tengan cadena completa y el arreglo de la publicación (T-249 o el que lo cierre) esté en `main`; una aprobación de `produccion` |
| FUERA | publicar antes de cumplir (3); otros territorios; cambios de motor, contrato o criterio |

## Ejecutado
| Hora | Territorio | Workflow y modo | Run | Resultado |
|---|---|---|---|---|
| 16:39 | Congreso Lérida (1) | P10 Fuentes — P11 Territoriales | 43050510708 | CANCELADA por el Operador (innecesaria; estaba en cola) |
