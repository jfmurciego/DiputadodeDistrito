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
| 17:30 | Congreso Lérida (2, reintento único tras 503 de cuota; las 7 autonómicas descargaron sin 503) | P00 Generar desde fuente, motor2, cadena | 43059014993 | SUCCESS: Activación 43063913076 y electoral 43064129984 en success |

Estado: EN ESPERA (el propietario aparca los distritos, 17:51 vía Planificador): Andalucía y la P50 de las 71 no se lanzan hasta que reactive.

## Reactivación y publicación (2026-11-12)
- Frase del propietario (09:30 aprox.): «Reactivo la ficha de Lérida y publicación: autorizo una P50 por lotes con todos los territorios publicables del inventario del Planificador, con la guarda del INDEX; un reintento si falla por cuota, después parar e informar.»
- Antes: registro 232 productos; datos_abiertos/INDEX.json 52 territorios.
- Inventario: `docs/autorizaciones/inventario_publicacion_2026-11-12.tsv` (territorio, run electoral, artefactos M06/M08 vivos). Publicables 69. No publicables: Andalucía (sin electoral: la P00 del bot cayó por la avería de la puerta 01→02, ya arreglada; no se relanza) y Cataluña (su P00 Reutilizar 43045037822 no tiene artefacto M08).
- 09:30 · P50 por lotes «Visor territorial» con los 69 runs electorales · 43183569340 · SUCCESS (aprobada por el propietario). Después: registro 335 productos (+103), los 69 runs del lote registrados, INDEX 52 territorios (sin pérdidas). Visor no comprobable por HTTP desde la nube (github.io da 000).

## Andalucía y Cataluña (2026-11-12)
- Frase del propietario (09:51 aprox.): «Autorizo relanzar la ejecución completa de Andalucía y de Cataluña reutilizando el progreso existente, con el motor nuevo y sin publicar, un intento cada una; y, si las dos dejan su mapa y sus resultados, publicarlas en el visor en un solo lote»
- 09:51 · P00 Reutilizar motor2: Andalucía 43186369510, Cataluña 43186377473 · EN_VUELO.
- 09:51 (resultado): las dos en success pero con 03/04 omitidos (sin M08): error del Operador al lanzar en `territorial_only` sin cadena.
- Frase nueva del propietario (11:55 aprox.): «Autorizo relanzar Andalucía y Cataluña reutilizando el progreso existente en modo electoral, con el motor nuevo y sin publicar, un intento cada una; y, si las dos dejan su mapa y sus resultados, publicarlas en el visor en un solo lote.»
- 11:55 · P00 Reutilizar motor2 `publication_mode=electoral`, `publish_result=false`: Andalucía 43204696160, Cataluña 43204706233 · EN_VUELO.
- 12:08: las dos en success con M08 (03 omitido por reutilización, 04 y puertas en success): Andalucía ddd-state-43204696160-M08, Cataluña ddd-state-43204706233-M08.
- 12:09 · P50 por lotes «Visor territorial» con 43204696160 y 43204706233 · 43206627505 · EN_VUELO (antes: registro 335, INDEX 52).
