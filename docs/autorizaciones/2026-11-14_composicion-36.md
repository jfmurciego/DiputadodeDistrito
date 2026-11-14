# Autorización de campaña 2026-11-14_composicion-36

- Decisión: D-52. Chat del Operador: session_01KQDtFqw1LBgGn6nCuxP8Yx. Pedida por el Planificador tras #758 (P50 3.15.0, versiona la composición vigente).
- Frase literal del propietario: «Autorizo las campañas 2026-11-14_archivo-p10-71, 2026-11-14_composicion-36 y 2026-11-14_deslinde11-r2 tal como figuran en sus fichas; la de Deslinde 1.1 solo cuando T-297 esté en main con la CI en verde.» (y las tres frases individuales en el mismo mensaje), 2026-11-14 17:40 Europe/Madrid aprox.
- Caducidad: 2026-11-15 23:59.
- Qué: `desplegar-visor-publico.yml` (P50), `pagina_publicar=Sitio completo`, `production_run_id=<lote>`, con los MISMOS runs ya publicados de los 36 SIN_VIGENTE de la batería 43605070831 (`composicion_36_2026-11-14.tsv`); sin cambiar los mapas.
- Lotes: 1 (43204696160, aut01) → comprobación → 12 → 12 → 11; cada lote, cuando el anterior ha terminado en success.
- Comprobación tras cada lote: en `main`, `datos/composicion/<id>.csv` del run publicado para cada territorio del lote; `datos_abiertos/INDEX.json` no pierde territorios (52 antes); el registro no pierde productos.
- Tope: 4 P50 más 1 reintento por fallo transitorio con evidencia; 300 min.
- FUERA: runs distintos de la lista; Congreso de 350; producción nueva; borrados.
- Parada: al primer fallo no transitorio, o si un CSV no llega o el INDEX pierde algo: no lanzar más; informar.

## Ejecutado
| Hora | Lote | Run P50 | Resultado | Comprobación |
|---|---|---|---|---|

Frase propuesta: «Autorizo la campaña 2026-11-14_composicion-36 tal como figura en la ficha.»
| 17:42 | 1 (aut01 43204696160) | 43617006619 | FAILURE no transitorio: LOTE_RECHAZADO «sin producto publicable»; el M08 de 43204696160 se borró en la poda T-278 (archivado en R2) y la P50 solo lo busca en los artefactos | INDEX 52 → 52; registro sin cambios |

## Cierre
Estado: `PARADA` (43617006619). Los 36 runs tienen el M08 solo en R2 (poda T-278); hace falta que la P50 restaure el M08 desde R2 (`orchestracion/archivo_r2.json`) antes de seguir.
