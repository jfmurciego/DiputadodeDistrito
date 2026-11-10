# Autorización de campaña 2026-11-10_historico-autonomico-andalucia-baleares-aragon

- Decisión: D-52 (autorización por campaña). Chat del Operador: session_01KQDtFsAtHP9atzNnDthr9A.
- Frase literal del propietario: «Autorizo la campaña de la ficha del histórico autonómico de Andalucía, Baleares y Aragón 2019-2026, con su tope de coste y caducidad»
- Fecha y hora de la frase (Europe/Madrid): 2026-11-10 16:00 (aprox.). El propietario añadió: «esperate a que te lo pida el planificador, pero date por autorizado, es una tarea para cuando terminen otras pendientes».
- Estado de la ficha: BORRADOR. La frase llegó antes que la ficha; el Operador la presenta al propietario antes del primer lanzamiento.
- Caducidad: 7 días desde el aviso del Planificador que abre el lanzamiento (y como máximo 2026-11-24 23:59).
- Gasto semanal al autorizar: se mide en el momento del lanzamiento (`herramientas/metricas_proceso.py`) y se anota aquí; tope 15.000 min/semana, aviso al 70 %.

## Límites
| Campo | Contenido |
|---|---|
| Qué se lanza | `ejecucion-completa-proyecto.yml`, «Generar desde fuente territorial acreditada», edición 2025, Canónico, `publication_mode=territorial_only`, `publish_result=false`, `cadena_electoral=false` |
| Elección y territorios | base territorial para el histórico autonómico: Andalucía (2012, 2015, 2018, 2022, 2026), Islas Baleares (2011, 2015, 2019, 2023), Aragón (2019, 2023, 2026); 12 elecciones, 3 ejecuciones (una por comunidad) |
| Mapa / ensemble | contrato vigente de cada comunidad; sin ensemble |
| Publica | no |
| Tope de coste | 3 ejecuciones (+ reintentos) y 180 min de job (estimado: 26 + 26 + 61 min, duración de las vigentes) |
| Tope de reintentos | 1 por comunidad, solo tras fallo transitorio (red, runner, rate limit) |
| Condición previa | aviso del Planificador de que la reagregación acepta la composición resultante (canónica por `composicion_m06.py` o `runs/`) |
| FUERA | lo de `README.md`; publicar; Cantabria/Extremadura/Álava/Huesca; cambios de motor, contrato o criterio; aprobar `produccion` |
| Parada | primer fallo no transitorio → no relanzar, diagnóstico, informar y esperar nueva frase |

## Ejecutado
| Hora | Territorio | Workflow y modo | Run | Resultado | Ejecuciones/min acumulados | Reintento (n/R) |
|---|---|---|---|---|---|---|

## Cierre
Estado: `EN_ESPERA` (aviso del Planificador). Último uso: —.
