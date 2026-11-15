# Autorización de campaña 2026-11-14_historico-paso-a-49x6

- Decisión: D-52 (autorización por campaña); alcance D-103, D-105 y D-113; ficha de T-328 (inventario T-306 §5, paso 3). Chat del Operador: <session_id>.
- Frase literal del propietario (copiada del chat): «…» — la frase debe nombrar esta ficha y mostrar el gasto semanal (D-46).
- Fecha y hora de la frase (Europe/Madrid): AAAA-MM-DD HH:MM
- Estado de la ficha: PREPARADA, sin frase. Nada se ha lanzado.
- Caducidad: 7 días desde la frase y, como máximo, hasta el cierre de la campaña de 6 elecciones.
- Gasto semanal al autorizar: se mide en el lanzamiento (`herramientas/metricas_proceso.py`) y se anota aquí; tope 15.000 min/semana, aviso al 70 %.

## Condición previa (el Operador no lanza sin ella)
D-105 fija el mapa destino 2023. Desde T-329 (#799) `historico_campana.py ejecutar` lleva los votos al mapa 2023 con las tablas
`configuracion/equivalencia_seccionado_ine_<año>_a_2023.csv` (T-328; sha256 verificado contra su JSON) y la regla de M07 7.4.0.
**El Gestor pasa a 2023 por defecto**: el job «histórico» de `gestor-campanas.yml` (líneas 286, 326 y 366) llama a
`historico_campana.py ejecutar` sin `--mapa` y el valor por defecto es `2023`; la ejecución usa el seccionado INE 2023 (sha256
verificado) y no hay paso B: la puerta es M07 PASS y `PUERTA_<t>_<clave>.json` lleva `m07` (PASS o PASS_WITH_DECLARED_EXCEPTIONS) y
`perdidos` (votos sin asignar). Esta ficha solo se activa con la frase del propietario tras el visto bueno del Coordinador de T-334.

## Límites
| Campo | Contenido |
|---|---|
| Qué se lanza | `gestor-campanas.yml` («P00 Campaña — Gestor»), modo `gestor`, tipo `nacional`; una campaña por elección, en este orden: `histórico: generales 2019-11`, `2019-04`, `2016`, `2015`, `2011`, y la 6.ª, 2023, si el Planificador la incluye en el aviso |
| Elección y territorios | 6 elecciones × 49 circunscripciones (las 52 menos Álava, Badajoz y Huesca, ya hechas) = 294 pares; `territorios=todos` (el plan omite lo no disponible e informa) |
| Orden dentro de cada elección | primero el lote de prueba del plan (primer territorio); el resto solo si la puerta de la prueba pasa |
| Mapa / ensemble | mapas vigentes con M06 publicado; destino 2023 (D-105, valor por defecto del Gestor); ensemble `ninguno` |
| Inicio | `desde el principio` (el histórico no reutiliza: motor repetible) |
| Publica | no (`publicar=no`; la 04 del histórico no está adaptada) |
| Tope de coste | 294 jobs de paso A y, por elección, 1 ejecución del Gestor; estimado 10–25 h de job en total (T-306 §5, no medido: se mide con la prueba de 2019-11 y se corrige aquí antes de seguir). Parada si el acumulado supera 1,5 × la estimación medida o el 70 % del tope semanal |
| Tope de reintentos | 1 por territorio y elección, solo tras fallo transitorio (red, runner, rate limit); máximo 15 reintentos en toda la campaña |
| Puerta | M07 `PASS` o `PASS_WITH_DECLARED_EXCEPTIONS` (se anota cuál) y `perdidos` ≤ el tope de M07 (1,5 %); sin ella, el territorio falla |
| FUERA | lo de `README.md`; publicar en el visor; autonómicas (D-113); Álava, Badajoz, Huesca; cambios de motor, contrato, política o workflows; aprobar `produccion`; descargar Infoelectoral; 2011: la pérdida de votos (0,024 %) se hereda tal cual (D-70) |
| Parada | primer fallo no transitorio (o puerta en rojo) → no relanzar, diagnóstico, informar y esperar nueva frase |

## Ejecutado
| Hora | Territorio | Workflow y modo | Run | Resultado | Ejecuciones/min acumulados | Reintento (n/R) |
|---|---|---|---|---|---|---|

## Cierre
Estado: `PREPARADA` | `EN_CURSO` | `COMPLETADA` | `PARADA` (causa y run) | `CADUCADA`. Último uso: —.
Una línea al Coordinador por run y al cierre; el fichero se actualiza en una PR de documentación del Operador (sin código).
