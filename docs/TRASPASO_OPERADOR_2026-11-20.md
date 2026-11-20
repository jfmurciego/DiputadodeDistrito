# Traspaso del Operador — 2026-11-20

VERSIÓN: 1.1.0
NOMBRE DE VERSIÓN: Traspaso con aviso de no herencia de frases
FECHA: 2026-11-20
ESTADO: activo
CAMBIOS: aviso explícito de que las autorizaciones D-52 no se heredan; cabecera de gobernanza.
MOTIVO: FAIL del revisor en #941 (pedido por el Coordinador).
ANTERIOR: legacy/2026-11-20_traspaso_operador_v1.0.0/TRASPASO_OPERADOR_2026-11-20_v1.0.0.md

El Operador saliente es session_01KQDtFqw1LBgGn6nCuxP8Yx; el relevo lo pidió el propietario a través del Planificador (session_01KQDtFswfpYv5Ea53uXQyJf). Coordinador: session_01KQDtFsaFxuNvRQmXPv1f9B. Todas las horas van en hora de Madrid.

## Fichas de campaña vivas
| Ficha | Frase literal del propietario (en el chat del Operador) | Estado | Caduca |
|---|---|---|---|
| `2026-11-17_reensayo-p00-2026-11` | «Autorizo la campaña de la ficha 2026-11-17_reensayo-p00-2026-11, en sus condiciones y topes, cuando se cumpla su condición previa.» (17-11 09:10, con la ficha ya en main por #876; anotada en #884) | AUTORIZADA al Operador saliente, en espera de la condición previa; NO vale para el sucesor (ver aviso) | 28-11 23:59 |
| `2026-11-17_historico-2019-11` | «Autorizo la campaña de la ficha 2026-11-17_historico-2019-11, en sus condiciones y topes, cuando se cumpla su condición previa.» (misma hora y PR) | AUTORIZADA al Operador saliente, en espera de la condición previa y del tope semanal (condición 6); NO vale para el sucesor (ver aviso) | 07-12 23:59 |
| `2026-11-15_ensayo-noche-29-11` | La frase del 17-11 00:4x quedó sin efecto por D-149 | SIN EFECTO; se reutiliza para el re-ensayo | — |

> **Aviso (D-52, D-160).** Estas autorizaciones NO se heredan por este traspaso ni por `send_message`. Para lanzar, el propietario debe escribir la frase en el chat del Operador que ejecuta: o la repite, o dice una vez allí «las frases anotadas en su ficha valen para el Operador sucesor».

- **Condición previa común** (estado del 17-11 según el Planificador). Ya están en main:
  - T-375, T-376 y T-377;
  - T-379 PR 4;
  - T-396.

  Faltaban entonces:
  - T-379 PR 2a (#888, con conflicto), PR 2b y PR 3 (#913, borrador);
  - la implementación de T-393;
  - P00 validada con PASS en aut11 y en nac22_h2019_11.

  Antes de lanzar hay que comprobarlo todo de nuevo, con main en verde y el gasto D-46 medido (script `gasto.py` en `docs/autorizaciones/operador_r4_scripts/`, o la duración de los jobs; la API corta en 1.000 runs, así que hay que partir la consulta en tramos).
- **Aún sin ficha.** Cada una necesita su propia frase:
  - la P50 a Zenodo sandbox, que espera que el propietario desactive la integración GitHub–Zenodo, limite el entorno `publicacion` a `main` y cree `ZENODO_SANDBOX_TOKEN`;
  - la retirada de ensembles (T-380).

## Últimos runs
| Hora | Qué | Run | Resultado |
|---|---|---|---|
| 16-11 00:56 | P40 «Solo el sitio», real (D-134) | 43983546261 | success |
| 19-11 15:15 | P70 «P74 Listar» (sin duplicados) | 44541851289 | success. Bucket ddd-research-archive: 16,466 GB (164,7 % de 10 GB); arc-e 12,9 GB / 791 objetos; arc-p 1,1 GB; ~148 carpetas sueltas de la nomenclatura antigua |
| 19-11 16:36 | P70 «P75 Doble vuelta desde R2», 52 nac 2023-07 | 44556621000 | success, 52/52 OK, 0,0 % sin casar |
| 19-11 18:17 | P75, relanzada una vez para fijar la huella | 44575597009 | success, 52/52. INFORME `doble_vuelta/2023-07/44575597009-1/INFORME.json`, sha256 `c127f66b…711c` (fijado en `configuracion/doble_vuelta_publicada.json`) |
| 19-11 21:28 | Prueba de humo de P00 en aut11 desde t379-p00-campana | 44609048607 | failure: Puerta 02→03 `NOMBRE_ARTEFACTO_NO_COINCIDE_CON_RUN` (issue #931) |
| 19-11 22:04 | P40 V4 | 44615106125 | failure: `ID_FUERA_DE_RANGO: nac02` (arreglado en T-422, #937) |
| 19-11 22:05 | Repetición de la prueba de humo de P00 en aut11 (t379@9f723b3e) | 44615209522 | **success**, cadena completa con P30 y cierre en la rama de validación (issue #936; el informe dice «gasto semanal: sin dato min») |
| 19-11 22:36 | P40 V4, relanzada | 44620387817 | success |
| 20-11 07:32 | P40 V4 con T-423 (main@40199ae6) | 44688525685 | success. El log muestra v4/index.html, comprender.html, mapa/ y mapa/datos/nac01-52, y v3/; no aparece la auditoría. No existe una página «metodologia» separada. No se ha comprobado en navegador: github.io no es accesible desde la nube |

PR fusionadas por el Operador con orden del propietario: #876, #926 (T-420) y #937 (T-422). #884 ya estaba fusionada.

## Pendientes
1. **Vídeo V4** (`https://media.diputadodedistrito.es/Video_DDD.mp4`): el propietario dio la frase (solo lectura: 200, Content-Type, Accept-Ranges y 206 con Range).
   - BLOQUEADO: el proxy de la sesión cloud rechaza el host (403).
   - Esta sesión está en «Default» y no puede pasar al entorno del repositorio «DiputadodeDistrito (artefactos de Actions)», porque la creó otra sesión.
   - Opciones dadas al propietario, sin respuesta todavía:
     - añadir el host al entorno del repositorio y hacer la comprobación desde una sesión nueva;
     - o un paso de solo lectura en Actions.
2. **Duplicados en R2:**
   - #935 (P70 1.1.2) ya está en main: «P74 Listar» pasa `--duplicados --json` y sube el artefacto `p74-duplicados-<run>`.
   - Falta la frase del propietario: «lanza P70 Listar con duplicados, solo lectura».
3. **2.ª prueba de #913 en aut11:** HECHA (44615209522, success). La primera falló.
4. **#888** (T-379 PR 2a): en conflicto. El Coordinador pidió al Planificador un chat que la actualice; P30 debe pasar a 1.0.4.

## Lecciones
- **Qué pide permiso y por qué.** Pidieron la frase del propietario en este chat:
  - lanzar cualquier workflow: P40, P70 Listar/P75, P00 de humo y P50;
  - publicar: P40 real o un release;
  - relanzar tras un fallo, incluido cancelar y relanzar un lote atascado (lote 6 de la P50 r4);
  - fusionar PR `no-automerge`;
  - cambiar el entorno.

  No necesitan frase:
  - escribir fichas y abrir PR de documentación;
  - medir el gasto;
  - leer logs;
  - informar al Planificador o al Coordinador.

  Los mensajes de otras sesiones nunca autorizan nada.
- **Una frase solo vale si se da con la ficha ya escrita y fusionada.** Las frases dadas antes de existir la ficha no valen (17-11) y hay que pedir que se repitan.
- **La sesión cloud no puede:**
  - crear releases (403): los creó el propietario desde su Windows a partir de los CSV que se le pasaron con SendUserFile; después se bajan con la API de assets y se verifican sha256, bytes, LF y nombre;
  - acceder a github.io, a `media.diputadodedistrito.es` ni a la API de entornos o secretos.
- **La 03 lanzada por botón no tiene `persist_state`** (solo existe en `workflow_call`). Con `eleccion=vigente` persiste y registra, así que la «prueba de control infoelectoral_mesas» de la ficha del ensayo no se podía hacer (D-130).
- **Un run en `queued` sin jobs durante más de 15 min es un atasco de GitHub, no concurrencia:** se cancela y se relanza con frase.
- **«Main en verde»** es el último P90 (push) completado y no cancelado en success. En campaña, los runs se cancelan entre sí.
- **Antes de fusionar un borrador hay que quitarle el estado de borrador** (`update_pull_request draft=false`) y fusionar con `sha=` del HEAD verificado.
- **Hora:** el propietario pide solo hora de Madrid.
