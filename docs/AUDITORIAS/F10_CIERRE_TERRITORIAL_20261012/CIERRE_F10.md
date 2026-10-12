# Cierre territorial F10 — estado operativo

**Versión:** 1.0.0
**Nombre:** Expediente de cierre territorial F10
**Fecha:** 2026-10-12
**Alcance:** adquisición territorial y separación de puertas electoral, conjunta y productiva para 19 territorios.
**Estado:** PENDING — Comunidad Valenciana.
**Cambios:** formaliza 18 adquisiciones territoriales cerradas, una bloqueada y las responsabilidades electorales pendientes.
**Motivo:** reflejar el estado posterior a #243, #244, #250 y #252 sin confundir adquisición territorial con admisibilidad conjunta.
**Predecesor/origen:** estado de `main@34c8793cede82e1f82832c84fc43c6a990394905`; evidencias fuente citadas en este expediente.

**Base verificada:** `main@34c8793cede82e1f82832c84fc43c6a990394905` (merge #252)
**Estado global F10:** `PENDING — Comunidad Valenciana`
**Alcance:** formalización documental de las puertas de adquisición territorial, admisibilidad electoral, admisibilidad conjunta y producción.

## Estados que se registran

| Puerta | Estado | Evidencia que determina el estado |
|---|---:|---|
| Adquisición territorial | **18 CLOSED / 1 BLOCKED** | Validación real de los 14 receipts históricos y cuatro receipts F10 independientes integrados en #243/#244/#252; Valencia no tiene paquete/receipt admisible. |
| Admisibilidad electoral | **15 ADMISSIBLE / 4 BLOCKED** | Los 14 territorios históricos y Valencia son admisibles para sus elecciones de referencia; quedan pendientes los tres crosswalks 2025→2026 y la fuente granular definitiva/reconciliación de Extremadura. |
| Admisibilidad conjunta | **14 PASS / 5 BLOCKED** | Los 14 históricos conservan su estado conjunto; tres receipts 2025/2025 y Extremadura están territorialmente cerrados pero tienen su puerta electoral bloqueada; Valencia tiene la puerta territorial bloqueada. |
| Producción | **NOT RUN — no autorizada por este expediente** | No se ejecutaron `00`, campañas, M01–M08 productivos, generación ni publicación. |

La adquisición territorial y el PASS conjunto son estados distintos. El valor histórico `14 PASS / 5 BLOCKED` describe admisibilidad conjunta; no se reutiliza como fotografía de adquisición. La matriz fila por fila, con referencias y hashes de cada receipt, es [matriz_nacional_19.json](matriz_nacional_19.json).

## Matriz nacional

| Territorio | Adquisición territorial | Electoral | Conjunta | Evidencia territorial |
|---|---|---|---|---|
| Andalucía | CLOSED | BLOCKED | BLOCKED | Receipt F10 `38082966768` |
| Aragón | CLOSED | BLOCKED | BLOCKED | Receipt F10 `38093067883` |
| Principado de Asturias | CLOSED | ADMISSIBLE | PASS | Histórico `37438440043` |
| Islas Baleares | CLOSED | ADMISSIBLE | PASS | Histórico `37589792776` |
| Canarias | CLOSED | ADMISSIBLE | PASS | Histórico `37596900111` |
| Cantabria | CLOSED | ADMISSIBLE | PASS | Histórico `37318299003` |
| Castilla y León | CLOSED | BLOCKED | BLOCKED | Receipt F10 `38091055890` |
| Castilla-La Mancha | CLOSED | ADMISSIBLE | PASS | Histórico `37444564173` |
| Cataluña | CLOSED | ADMISSIBLE | PASS | Histórico `37453376100` |
| Comunidad Valenciana | **BLOCKED** | ADMISSIBLE | **BLOCKED** | Evidencia independiente 2023/2023; no existe receipt territorial #179 aceptable |
| Extremadura | CLOSED | BLOCKED | BLOCKED | Receipt F10 `38091144559`, independiente y no promovido |
| Galicia | CLOSED | ADMISSIBLE | PASS | Histórico `37155903096` |
| Comunidad de Madrid | CLOSED | ADMISSIBLE | PASS | Histórico `37325328346` |
| Región de Murcia | CLOSED | ADMISSIBLE | PASS | Histórico `37344628042` |
| Comunidad Foral de Navarra | CLOSED | ADMISSIBLE | PASS | Histórico `37293310755` |
| País Vasco | CLOSED | ADMISSIBLE | PASS | Histórico `37458584767` |
| La Rioja | CLOSED | ADMISSIBLE | PASS | Histórico `37298033194` |
| Ceuta | CLOSED | ADMISSIBLE | PASS | Histórico `37442375016` |
| Melilla | CLOSED | ADMISSIBLE | PASS | Histórico `37315646335` |

`matriz_nacional_19.json` registra para cada receipt el path versionado, SHA-256 del receipt, run, SHA del artefacto y paquete, identidad territorial, reporte e identidad de compatibilidad. Los 14 históricos se cotejaron con `evidencia-previa-reutilizada.json`; los cuatro receipts independientes se validaron con el consumidor real de receipts. Los hashes y linajes originales no se modificaron.

## Responsabilidades trasladadas al frente Electoral

- **Andalucía, Aragón y Castilla y León:** acreditar la correspondencia oficial entre el seccionado territorial INE 2025 y los resultados electorales 2026. La decisión `F10-20261012-PAIR-2025` solo autoriza la referencia territorial 2025/2025. No autoriza equivalencia electoral, promoción ni generación.
- **Extremadura:** incorporar la fuente electoral granular definitiva y reconciliarla con los resultados oficiales. El receipt territorial `38091144559` permanece independiente del producto histórico M06 `36472516474` y de la preparación histórica `35755043806`; `promoted: false`.

Estos cuatro bloqueos no reabren la adquisición territorial. Su seguimiento queda en Electoral y no cambia el estado `CLOSED` de sus fuentes territoriales.

## Único bloqueo territorial: Comunidad Valenciana

Se conserva sin modificación la evidencia de main [`evidencia_2023.json`](../F10_CIERRE_VALENCIA_20261012/evidencia_2023.json), los originales y sus hashes en el almacén protegido. El expediente registra población INE 2023 para las tres provincias: 3.503 filas numéricas y 5.216.195 habitantes, junto con 46 CUSEC reportados sin observación. No se transforman ausencias en ceros. La admisibilidad no se concede mientras esas observaciones y la geometría no cumplan el contrato de consumo.

La evidencia de base mantiene la discrepancia geométrica de 1.823 secciones de referencia frente a 2.183 CUSEC en la alternativa WFS, seis geometrías inválidas y dos pares de solapamiento sujetos al máximo vigente de 1 m². La causa de la diferencia de cobertura no figura acreditada en el expediente integrado en main. No se acepta la alternativa, no se sustituyen los originales ni se altera la tolerancia. Cualquier diagnóstico posterior aún no integrado debe permanecer como investigación separada hasta revisión y decisión documental.

**Criterio para cambiar Valencia a CLOSED:** conservar una edición oficial 2023 cuya identidad y cobertura provincial sean compatibles con el contrato; resolver las 46 observaciones mediante evidencia oficial específica o demostrar documentalmente que no pertenecen al universo exigible; entregar geometrías válidas y admisibles según la tolerancia vigente; materializar el paquete, versionar el receipt conforme a #179 y obtener aceptación del consumidor real. Hasta entonces, territorial y conjunto siguen `BLOCKED`.

## Criterios de cierre global F10

F10 podrá pasar de `PENDING` a cierre territorial cuando Valencia cumpla todos los criterios anteriores y la matriz nacional mantenga 19/19 estados reproducibles sin regresiones de hashes o linajes. El cierre de adquisición territorial no cerrará las cuatro dependencias electorales: Electoral deberá resolverlas en su frente. Ningún cierre de fuente autoriza producción.

## Verificación efectuada sobre la base

- `git fetch origin main`: `origin/main` coincide con `34c8793cede82e1f82832c84fc43c6a990394905`.
- `validate_territorial_receipt(..., edition='2025')`: PASS para los 14 receipts históricos y los cuatro receipts independientes.
- Se comprobaron `promoted: false` y los linajes de Extremadura: preparación `35755043806`, producto M06 `36472516474`, receipt F10 `38091144559`.
- Se contrastaron los cuatro hashes/identidades de los receipts #252 con `VERIFICACION.json` y con los receipts versionados.
- Se recalcularon los totales de la matriz: 18/1 territorial, 15/4 electoral, 14/5 conjunta y 19 `NOT_RUN` en producción.
- No se modificaron contratos, catálogos, receipts, checkpoints, geometrías, productos históricos ni decisiones de promoción.
