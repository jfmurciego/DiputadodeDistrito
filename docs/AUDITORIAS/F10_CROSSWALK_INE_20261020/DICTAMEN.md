# Dictamen nominal de correspondencias INE 2025–2026 — F10

**Versión:** 1.0.0
**Fecha:** 2026-10-20
**Alcance:** variaciones oficiales del callejero INE aplicables a los casos nominales de Aragón, Castilla y León y Andalucía.
**Estado:** evidencia procesada; las puertas electorales permanecen bloqueadas donde no se acredita una correspondencia electoral íntegra.
**Cambios:** se decodifican altas, bajas y movimientos de tramo en tres ZIP oficiales y se aplica fecha límite por elección.
**Motivo:** distinguir cambios de tramos/direcciones de equivalencias seccionales electorales.
**Fuentes reutilizadas:** `docs/AUDITORIAS/F10_ELECTORAL_TRES_TERRITORIOS_20261020/`, `docs/AUDITORIAS/CIERRE_FUENTES_20261017/IDENTIDADES_INE_2025_2026_F10.json`, `docs/AUDITORIAS/CIERRE_FUENTES_20261019/ANDALUCIA_INE_TRAM_3_PERIODOS_86_CUSEC.json` y `territorios/castilla_y_leon/evidencia/reconciliacion_secciones_2025_2026.json`.

## Método y archivos fuente

Se procesaron byte a byte los originales INE con el formato fijo del documento oficial `originales/Variacionesencallejero.pdf`. Se comprobaron ZIP CRC, SHA-256 y registros de `TRAM`, `VIAS`, `PSEU` y `UP`. Los archivos no contienen familia `SECC`; las familias municipales no incorporan una relación que enlace una calle con un código de sección. Cada registro conserva ruta del miembro, número de línea y SHA-256 de la línea en `procesados/*.json`. Las fechas se cotejan con las jornadas electorales; los hechos posteriores se conservan, pero se excluyen de la evidencia vigente a la elección.

| Intervalo oficial | URL | SHA-256 | Bytes | Resultado |
|---|---|---|---:|---|
| Enero–julio 2025 | `https://ine.es/prodyser/callejero/Var_Callejero_0125_0725.zip` | `852db9bcd0c6355e85020a07d229d31d00c4eab9e0493f83a8671bca789e776f` | 1.103.750 | CRC y SHA conformes |
| Julio 2025–enero 2026 | `https://ine.es/prodyser/callejero/Var_Callejero_0725_0126.zip` | `f2f8299bbcff7e79c69948b900d5c9e97c3b9c71f8cc430f8ffac0e9a475f319` | 507.975 | CRC y SHA conformes |
| Enero–julio 2026 | `https://ine.es/prodyser/callejero/Var_Callejero_0126_0726.zip` | `154b8eacdb886e5b6463283c597076b3b0dde256cfaf74cb34c4ffc5cb326635` | 577.966 | CRC y SHA conformes |

El ZIP 0125_0725 contiene directorios internos rotulados `Variaciones_01-2024_07-2024`, aunque el nombre del archivo, los miembros `D250101.A250630` y sus fechas de variación corresponden a 2025. Se conserva este hecho como anomalía de rotulación; el intervalo no se infiere del nombre del directorio. Los valores de fechas y códigos se interpretan conforme al esquema oficial y al contenido íntegro fijado por el SHA del ZIP.

Los códigos examinados son **13 identidades** (2 Aragón, 7 Castilla y León y 4 Andalucía), aunque el encargo los denomine “once” en el criterio final.

## Aragón — elección 2026-02-08

| CUSEC | Hechos oficiales anteriores a la elección | Evidencia adicional ya preservada | Dictamen |
|---|---|---|---|
| `5002501003` (608 votos) | No aparece como origen o destino de ningún registro `TRAM` en los tres períodos examinados. | La evidencia geométrica ya existente sitúa su polígono 2026 sobre partes de `5002501002` (87,8506%) y `5002501001` (12,1494%). La geometría no identifica la adscripción electoral de esos 608 votos. | `BLOCKED_ACREDITADO`: falta documento electoral/OCE que vincule íntegramente la mesa o electorado del CUSEC a una o varias secciones 2025. No se distribuyen votos. |
| `2221301003` | 1 alta `A` el 2025-01-01 y 364 movimientos `M` desde `2221301003` a `2221301002` el 2025-09-28; todos anteriores al 2026-02-08. Las líneas exactas están en `procesados/0125_0725.json` y `procesados/0725_0126.json`. | La comparación geométrica INE archivada muestra que las secciones territoriales 2025 `2221301002`+`2221301003` componen la geometría 2026 `2221301002`. El resultado electoral 2026 carece de `2221301003`. | `BLOCKED_ACREDITADO`: la concentración de 364 tramos en el código 1002 es parcial a nivel de callejero; no prueba un crosswalk de votos entre la sección electoral 1002 y el universo 2025. Falta certificación de correspondencia de electorado/mesas para la jornada. |

La lista oficial de mesas de Aragón puede confirmar sección y mesa publicadas, pero no resuelve por sí sola qué CUSEC 2025 corresponde a cada conjunto de electores ni prueba transferencia completa de votos. No se declara equivalencia 1:1.

## Castilla y León — elección 2026-03-15

| CUSEC | Variación `TRAM` anterior a elección | Lectura | Dictamen |
|---|---|---|---|
| `2408904017` | 100 registros `M` desde `2408904015` (2025-01-28). | Cambio de tramos; no totalidad demostrada del electorado ni identidad completa. | `BLOCKED_ACREDITADO` |
| `2408906020` | 61 registros `M` desde `2408906009` (2025-07-28). | Cambio de tramos; no totalidad demostrada. | `BLOCKED_ACREDITADO` |
| `3702301002` | 484 `M` desde `3702301001` (2025-03-17), cuatro `A` (2025-08-01) y una `A` (2026-01-01), todas anteriores al 15-03-2026. También hay una `A` el 2026-05-01, posterior a la elección, excluida del dictamen electoral. | Alta/movimiento de tramos con cambios posteriores; no completa una identidad de votos. | `BLOCKED_ACREDITADO` |
| `4217302016` | 60 `M` desde `4217302014` y cinco en sentido inverso (2025-10-01). | Transferencia bidireccional de tramos; evidencia de que una lectura de simple fusión sería incorrecta. | `BLOCKED_ACREDITADO` |
| `4701001012` | 69 `M` desde `4701001010` (2025-03-11); tres `M` en sentido inverso el mismo día; cinco `A` hacia 1012 (2025-03-19). | Altas y transferencias parciales en ambas direcciones; no correspondencia íntegra. | `BLOCKED_ACREDITADO` |
| `3412004006` | 37 `M` hacia `3412004002` (2025-10-01). | Baja/movimiento de tramos; no prueba qué votos de 2026 pertenecen a la sección 2025. | `BLOCKED_ACREDITADO` |
| `3710701002` | 210 `M` hacia `3710701001` (2025-02-18). | Baja/movimiento de tramos; no prueba qué votos de 2026 pertenecen a la sección 2025. | `BLOCKED_ACREDITADO` |

Los cinco códigos electorales con 3.874 votos sumados permanecen sin atribución a CUSEC 2025. Las dos secciones territoriales sin resultado directo tampoco se consideran cubiertas por movimientos parciales. Los 19 códigos CERA quedan fuera de este análisis y conservan su separación vigente. La comparación espacial y el cambio administrativo de tramos no sustituyen un documento electoral de correspondencia completa ni autorizan repartir votos.

## Andalucía

### Sevilla — `4109110025` y `4109110027` (elección 2026-05-17)

En los tres ZIP no se encuentra una línea `TRAM` que cite ninguna de las dos secciones como origen o destino. Los archivos incluyen cambios municipales `VIAS` para el municipio `41091` (11, 23 y 17 líneas respectivamente); esos registros carecen de vínculo a sección (`section_link=NOT_PROVIDED_BY_THIS_FAMILY`). La familia `SECC` no está presente. Por tanto, estas variaciones municipales no explican documentalmente las diferencias geométricas de ambas secciones.

La evidencia geométrica INE ya preservada (EPSG:25830) muestra geometrías válidas y distintas entre ediciones: `4109110025`, área 2025 338.734,374522 m² y 2026 335.622,418459 m², diferencia simétrica 3.111,956063 m²; `4109110027`, área 2025 252.903,385683 m² y 2026 259.882,287679 m², diferencia simétrica 6.978,902001 m². Las extracciones son GeoJSON reserializados, no payload HTTP byte-original: 2025 SHA-256 `e8fdd379970ea9e8c4318723f41a6a0e9f428b0838ed82a00df862a53061e91b`; 2026 SHA-256 `a90b0e308a7993825888497ae9b0cd7b0b9e94683426b319d91b0dabd81d75ff`. Ambas identifican CRS `urn:ogc:def:crs:EPSG::25830`; los códigos son `MultiPolygon`, y el metadato advierte que no se preservó el payload original. Las métricas son reproducibles sobre la extracción versionada, no certificación byte-original del servicio. La permanencia del CUSEC no acredita que el cambio sea una mera rectificación, y la variación municipal de calles no vincula esas calles a estos dos códigos. Dictamen individual de ambas: `BLOCKED_ACREDITADO`; falta explicación oficial de la modificación geométrica y su fecha efectiva, mediante historial de secciones/rectificación cartográfica o relación oficial calle–sección para las ediciones comparadas.

### Cortegana — `2102502001` y `2102502002`

Los 15 registros `M` de 2026-01-29 trasladan tramos de `2102502002` a `2102502001`; tres registros `B` de 2026-02-04 eliminan otros tramos de `2102502001`. Antes, 21 líneas `B` relativas a `2102502002` constan el 2025-03-06. Ninguno de estos grupos demuestra el traslado total de electores. El seccionado INE 2026 conserva ambos códigos y sus geometrías. El BOP/OCE asigna las mesas A, B y C de la elección al código 001, pero no establece relación completa con la edición INE 2025.

| CUSEC | Hechos y votos | Dictamen |
|---|---|---|
| `2102502001` | 15 tramos recibidos desde 2002 el 2026-01-29; 3 bajas el 2026-02-04; 658 votos a candidaturas. Las mesas A/B/C publicadas por OCE están asignadas a 001. | `BLOCKED_ACREDITADO`: falta acreditar qué sección territorial 2025 cubre todo el electorado que emitió esos 658 votos. |
| `2102502002` | 21 bajas de tramos el 2025-03-06; 15 movimientos salientes hacia 2001 el 2026-01-29; continúa en el seccionado INE 2026. | `BLOCKED_ACREDITADO`: no se demuestra su desaparición electoral completa ni que todo su electorado se integrase en 2001. |

Los 658 votos no pueden atribuirse al CUSEC territorial 2025 2002 ni reasignarse entre ambos. Hace falta un documento oficial de OCE que acredite la adscripción electoral completa por electorado/domicilio a la edición territorial 2025.

## Resultado del consumidor F10

Se ejecutó `python3 herramientas/estado_derivado_f10.py --root .` sobre `origin/main@94b62b85d199f7ccef2d74adf6ab694923db7480`. Resultado: adquisición territorial 19/19 `CLOSED`; admisibilidad territorial 18 `PASS` / 1 `BLOCKED`; admisibilidad electoral 15 `ADMISSIBLE` / 4 `BLOCKED`; conjunta 14 `PASS` / 5 `BLOCKED`; F10 `PENDING`; producción `NOT_AUTHORIZED`. Esta evidencia no habilita ninguna transición: no se emitió recibo nuevo ni se alteró la matriz de puertas. Los procesados son evidencia administrativa de soporte, no acreditación electoral ni receipt F10.

## Qué falta para cerrar los casos

En los nueve casos de Aragón y Castilla y León, y en las cuatro identidades objetivo de Andalucía, no queda una operación local sobre estos ZIP que pueda probar por sí sola la correspondencia de votos completa: las fuentes contienen transferencias de tramos y cambios municipales, no una tabla de identidad de elector/mesa a sección INE 2025. Para levantar cada bloqueo se requiere una relación oficial de la OCE/Junta Electoral o de la autoridad estadística que enlace íntegramente las mesas/domicilios electorales de 2026 con CUSEC de 2025; para Sevilla se requiere además explicar la modificación geométrica y su fecha efectiva. No se inventan correspondencias ni se modifica el contrato.
