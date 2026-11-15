# Autorización de campaña 2026-11-14_historico-paso-a-49x6

- Decisión: D-52 (autorización por campaña); alcance D-103, D-105 y D-113; ficha de T-328 (inventario T-306 §5, paso 3). Chat del Operador: <session_id>.
- Frase literal del propietario (copiada del chat): «…» — la frase debe nombrar esta ficha y mostrar el gasto semanal (D-46).
- Fecha y hora de la frase (Europe/Madrid): AAAA-MM-DD HH:MM
- Estado de la ficha: PREPARADA, sin frase. Nada se ha lanzado.
- Caducidad: 7 días desde la frase y, como máximo, hasta el cierre de la campaña de 6 elecciones.
- Gasto semanal al autorizar: se mide en el lanzamiento (`herramientas/metricas_proceso.py`) y se anota aquí; tope 15.000 min/semana, aviso al 70 %.

## Condición previa (el Operador no lanza sin ella)
Fusionadas en `main`: las tablas año→2023 de #796 con su sha256 (T-328), T-329 (#799) y T-334 (#804). El paso A usa el mapa 2023 por
defecto (D-105: el job «histórico» de `gestor-campanas.yml` llama a `historico_campana.py ejecutar` sin `--mapa`); no hay paso B y
`PUERTA_<t>_<clave>.json` lleva `m07` (PASS o PASS_WITH_DECLARED_EXCEPTIONS) y `perdidos` (votos sin asignar).
**Pendiente de código (T-342):** la puerta de abajo exige dos comprobaciones (votos sin asignar ≤ 0,1 % y contraste con el BOE) que
`historico_campana.py` `puerta_json` aún no hace (hoy solo `ra == 0`); no se lanza hasta que T-342 (puerta del histórico: ≤ 0,1 % + contraste BOE por provincia) esté fusionada en `main`.

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
| Puerta | por territorio y elección: (1) M07 PASS, o PASS_WITH_DECLARED_EXCEPTIONS solo con votos sin asignar ≤ 0,1 % por provincia (2011: tope por provincia = valores de D-70 para Alicante, Asturias, León, Lugo y Orense, 0,2–0,54 %, `docs/PLAN.md:107`; el resto de provincias, ≤ 0,1 %); (2) contraste con el CSV oficial del BOE (`configuracion/resultados_oficiales_congreso_<AAAA>_<MM>.csv`: `_2011_11`, `_2015_12`, `_2016_06`, `_2019_04`, `_2019_11`; y `_2023.csv`; T-330) por provincia y por partido: todo partido del CSV de la provincia debe homologarse y compararse (sin umbral que deje partidos fuera) y su defecto relativo máximo debe estar dentro de la tolerancia CERA ya usada en 2019-11 y 2023 (`TOLERANCIA = 0.10`, `herramientas/cuadre_historico_espana.py:39`; comparación en `:137`; el espejo nunca supera a la oficial). «Ganador igual que B» es solo informativo. Sin puerta en verde, el territorio falla |
| FUERA | lo de `README.md`; publicar en el visor; autonómicas (D-113); Álava, Badajoz, Huesca; cambios de motor, contrato, política o workflows; aprobar `produccion`; descargar Infoelectoral; 2011: la pérdida de votos de D-70 (Alicante, Asturias, León, Lugo y Orense) se hereda tal cual, dentro de su tope por provincia |
| Parada | primer fallo no transitorio (o puerta en rojo) → no relanzar, diagnóstico, informar y esperar nueva frase |

## Ejecutado
| Hora | Territorio | Workflow y modo | Run | Resultado | Ejecuciones/min acumulados | Reintento (n/R) |
|---|---|---|---|---|---|---|

## Cierre
Estado: `PREPARADA` | `EN_CURSO` | `COMPLETADA` | `PARADA` (causa y run) | `CADUCADA`. Último uso: —.
Una línea al Coordinador por run y al cierre; el fichero se actualiza en una PR de documentación del Operador (sin código).
