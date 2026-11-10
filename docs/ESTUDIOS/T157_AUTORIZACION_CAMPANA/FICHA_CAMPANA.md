# Ficha de campaña (la presenta el Operador antes de pedir la frase)

Una campaña = un conjunto cerrado de lanzamientos. Todo lo que no figure aquí queda FUERA.

| Campo | Contenido (rellenar; sin campo vacío) |
|---|---|
| Nombre | `AAAA-MM-DD_<campaña>` (nombre del fichero de registro) |
| Qué se lanza | workflows (`gestor-campanas.yml` / `ejecucion-completa-proyecto.yml` / `preparacion-*` / `desplegar-visor-publico.yml`) y modo |
| Elección y territorios | elección (p. ej. Congreso 2023-07-23) y lista con notación (AUTnn / NACnn) y nombre en español |
| Mapa / ensemble | contrato de mapa, `scenario_id` y `scenario_strategy` si hay ensemble |
| Publica | **sí** (qué territorios, `production_run_id`) o **no** (`publish_result=false`) |
| Tope de coste | máx. N ejecuciones de 00 y M minutos de job (suma de la duración de los jobs; `/timing` da 0) |
| Tope de reintentos | máx. R por territorio, solo tras fallo transitorio (red, runner, rate limit); 0 si no se admiten |
| Caducidad | fecha y hora (Europe/Madrid); pasada, la autorización muere |
| FUERA (siempre) | borrados; relevo de motor o cambio de M04/M05/política/umbrales; publicar si «Publica: no»; cambios de criterio (K, suelo, techo, atomicidad, fuente); territorios no listados; fusionar PR `no-automerge`; aprobar `produccion` |
| Parada | primer fallo **no transitorio** → no relanzar, `diagnosticar-run`, informar y esperar nueva frase |
| Frase propuesta | «Autorizo la campaña `<nombre>` tal como figura en la ficha.» |

Fallo transitorio = el log/anotación muestra red, runner perdido o rate limit sin error de código ni de dato. Cualquier otro
(`::error` del motor, puerta, contrato, par incompatible) es no transitorio. Ante la duda, no transitorio.
Cada reintento transitorio cuenta en ambos topes. Al agotar un tope: parar e informar.
