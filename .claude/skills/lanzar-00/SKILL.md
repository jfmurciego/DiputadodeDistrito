---
name: lanzar-00
description: Procedimiento para lanzar la 00 Ejecución Completa del Proyecto (ejecucion-completa-proyecto.yml) de un territorio. Úsala solo en el chat operador y con permiso explícito del propietario en ese mensaje.
---

# Lanzar una 00

Requisitos previos (si falta uno, no se lanza):
- Permiso explícito del propietario en este chat para este territorio o lote.
- Ningún run de ese territorio en curso (incluidos los encadenados de `github-actions[bot]`).
- Evidencia local del motor si cambió M04, M05, contrato o política (skill `diagnosticar-run`).

Modo de ejecución:
| Situación | Modo |
|---|---|
| Nada cambió en motor, umbrales ni fuente; reanudar | «Reutilizar progreso existente» |
| Cambió M04, M05, política, umbrales o contrato | «Ejecutar desde el principio» |
| Cambió la fuente o `modulos/04_*` en contratos `physical_components` (islas) | «Generar desde fuente territorial acreditada» |
| `TERRITORIAL_READY_PAIR_INCOMPATIBLE` | 03 con reutilizar=false si caducó → `preparacion-legislatura-vigente.yml` `prepare_one` → 00 «Reutilizar» |

Ojo: «Reutilizar» restaura el último checkpoint REGISTRADO (mira `CHECKPOINT_RUN_ID` en el log del paso M04) y
reutiliza M04 aunque el contrato haya cambiado.

Lanzamiento (REST; `gh workflow run` falla en la nube). Comprueba antes los `inputs` vigentes del workflow en `main`
(`territory_id`, `data_edition`, `execution_mode`, `optimization_algorithm`, `publication_mode`, `publish_result`,
`lanzado_por_eleccion`). `publish_result=true` publica: solo con permiso de publicar.
```
gh api -X POST repos/jfmurciego/DiputadodeDistrito/actions/workflows/ejecucion-completa-proyecto.yml/dispatches \
  -f ref=main -f "inputs[territory_id]=<etiqueta del selector>" \
  -f "inputs[execution_mode]=Ejecutar desde el principio" -f "inputs[publish_result]=false"
```
Efecto: el run queda esperando la aprobación del propietario en GitHub (entorno `produccion`, Review deployments);
el operador no aprueba. Si el entorno aún no existe, GitHub lo crea sin reglas y no bloquea.
Después: localiza el run por `TERRITORY:` en «Planificar», anótalo y termina el turno. Sin vigilar.
Encadenados: si llega a M06 se lanza sola la activación y otra 00 «Reutilizar» como bot (desde #389, solo con la puerta 02).

Nota (07-11): todo dispatch manual de 00/05/06 queda en `waiting` hasta el Approve del propietario; `extraer-composicion-m06`
no espera. Decisión D-3: se publica en el visor cada provincia al terminar su 00, con permiso por provincia.