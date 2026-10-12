# Piloto F10 de estados derivados del Plan Maestro

**Versión:** 1.0.0
**Fecha:** 2026-10-12
**Estado:** CANDIDATE — revisión técnica pendiente
**Predecesor:** Plan Maestro vivo `ddd-maestro-vivo-20261011`, revisión `1.3.0+20261011.1`; `estado.json` no se modifica.
**Base del repositorio:** `main@c0b28c4b8e2f8c018acabe7064930c3164f4683f`.

## Cambio acotado

`herramientas/estado_derivado_f10.py` deriva cuatro puertas independientes desde el catálogo vigente, el contrato legislativo, los receipts versionados y los consumidores canónicos:

- Adquisición territorial: `validate_territorial_receipt` y SHA real del receipt cotejado con el expediente.
- Admisibilidad electoral: `catalogo_preparacion.validate_repository`, identidad electoral recalculada y compatibilidad temporal con el año electoral.
- Admisibilidad conjunta: `resolve_pair`; una fila documental o una PR no puede producir `PASS`.
- Producción: siempre `NOT_AUTHORIZED_BY_F10`; el adaptador no hereda autorizaciones del catálogo productivo.

El expediente F10 solo se usa como registro de seguimiento y comprobación de contradicciones. Una contradicción deja bloqueado el territorio afectado. El par territorial-electoral se obtiene de los consumidores y los fallos no se sustituyen por estados documentales.

La extensión [puertas_f10.v1.json](../../../configuracion/puertas_f10.v1.json) representa los cinco trabajos independientes y queda también instalada como `puertas_f10.v1.json` en el Plan Maestro vivo. No modifica `estado.json`, el catálogo base ni los pins de autorización. Andalucía, Aragón, Castilla y León y Extremadura pueden avanzar en trabajo local sin esperar el cierre global. Valencia sigue en `WAIT_OWNER` porque el análisis local protegido está agotado; necesita evidencia oficial material nueva o decisión de Work.

## Reproducción

```sh
python3 herramientas/estado_derivado_f10.py \
  --root . \
  --policy ~/Desarrollo/DDD-control/ordenes-manuales/auto-policy.json \
  --plan ~/Desarrollo/DDD-control/planes/ddd-maestro-vivo-20261011

DDD_F10_REPO=~/Desarrollo/DDD-f10-auto-piloto ddd auto --dry-run --f10 \
  --plan ~/Desarrollo/DDD-control/planes/ddd-maestro-vivo-20261011 \
  --front fuentes-oficiales
```

La segunda forma es el piloto integrado con el controlador existente. `--f10` solo acepta simulación/estado; no invoca Codex ni cambia `estado.json`, el historial o los receipts.

## Resultados reproducidos

| Puerta | Resultado |
|---|---:|
| Adquisición territorial | **18 CLOSED / 1 BLOCKED** |
| Admisibilidad electoral | **15 ADMISSIBLE / 4 BLOCKED** |
| Admisibilidad conjunta | **14 PASS / 5 BLOCKED** |
| Producción | **19 NOT_AUTHORIZED_BY_F10** |
| F10 global | **PENDING — Comunidad Valenciana** |

Las cuatro nuevas evidencias independientes permanecen no promovidas: Andalucía `38082966768`, Aragón `38093067883`, Castilla y León `38091055890` y Extremadura `38091144559`. Extremadura conserva preparación histórica `35755043806` y producto M06 `36472516474`. No cambia ningún linaje.

Valencia: el consumidor bloquea el receipt territorial por falta de acreditación #179. El expediente conserva sus 46 filas sin observación y el bloqueo geométrico. El adaptador no les asigna cero ni hace imputaciones.

## Transiciones cubiertas

`tests/fixtures/f10_auto/snapshots.json` reproduce las llegadas A–D con identidades territoriales reales:

- A: 14 históricos acreditados / 5 pendientes.
- B: receipt independiente de Extremadura; 15 / 4.
- C: receipts de Andalucía, Aragón y Castilla y León; 18 / 1.
- D: se mantiene Valencia bloqueada, 15/4 electoral, 14/5 conjunta y producción sin autorización.

Las regresiones comprueban hash de receipt discordante, identidad territorial errónea, temporalidad inválida, contradicción del expediente, ausencia de autorización local y aislamiento del bloqueo de un territorio.

## Límite del piloto automático

El controlador actual puede mostrar las actividades locales habilitadas y sus dependencias, pero las cuatro fichas electorales aún tienen `task_spec_registered: false`. Por eso el selector las ofrece como `READY_LOCAL` y `selectable: false`; no lanza Codex sin prompt y validador específicos. La extensión no relaja dependencias formales ni cambia F10 de su estado reservado `WAIT_OWNER`. `ddd auto --dry-run --f10` es la simulación real disponible; no se realizó una tarea Codex porque el Plan y la política no contienen una ficha ejecutable completa para estas actividades.

El adaptador valida la integridad de los receipts y sus identidades. No vuelve a extraer todos los artefactos INE para recomputar sus bytes; el SHA del artefacto se conserva como evidencia acreditada en cada receipt. Esa limitación aparece separada de las puertas, no se presenta como una comprobación recién ejecutada.
