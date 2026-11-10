---
name: lanzar-campana
description: Procedimiento para lanzar la legislatura vigente (nacional, autonómicas, una comunidad o provincias) con el «P00 Campaña · Gestor» (gestor-campanas.yml, modos plan y lanzar). Úsala solo en el chat operador; «lanzar» exige permiso explícito del propietario en ese mensaje.
---

# Lanzar una campaña de la legislatura vigente

Fuente: `configuracion/legislatura_vigente.yaml` (71 territorios: 52 provincias del Congreso 2023-07-23 y 19 autonómicas),
generado desde el registro electoral, la preparación de la legislatura y el BOE (`herramientas/legislatura_vigente.py
generar`; la CI comprueba que coincide). Si cambia una elección, se regenera; nunca se edita a mano.

1. Plan en seco (sin efectos, sin permiso): `modo=plan`, `ambito` = `legislatura completa` | `nacional` | `autonómicas` |
   `comunidad` (una, CODAUTO o nombre) | `provincias` (INE, matrícula o nombre, separadas por comas), `territorios`.
   ```
   gh api -X POST repos/jfmurciego/DiputadodeDistrito/actions/workflows/gestor-campanas.yml/dispatches -f ref=main \
     -f "inputs[modo]=plan" -f "inputs[ambito]=provincias" -f "inputs[territorios]=HU,Teruel"
   ```
   El resumen del run lista clave T-03, estado y acción por territorio: `nada` (M08 publicado), `publicar` (00 completa
   de ≤ 12 días sin publicar), `reutilizar`, `desde_el_principio`, `esperar` (00 en curso).
2. Pasa el plan al propietario y pide permiso explícito para lanzar ese ámbito (y publicar: D-3). Con D-52, presenta la
   ficha de campaña (ámbito, territorios, mapa, ensemble, publica sí/no, topes, caducidad, FUERA) y pide una sola frase:
   registrada en `docs/autorizaciones/`, cubre el `lanzar` y los `continuar`/reintentos del Gestor solo tras un fallo transitorio y dentro de los topes.
3. Lanzar: los mismos inputs con `modo=lanzar` (opcional `forzar=true` rehace también los publicados;
   `max_paralelo`, por defecto 3; `estrategia`). Queda esperando el clic del propietario en `produccion`: uno por campaña.
   Después, el Gestor (como bot, sin más clics): territorio de prueba si el lote es > 1 (si falla, para); el resto con
   `max_paralelo`; por territorio 00 `publish_result=true` + `lanzado_por_eleccion` (la 00 encadena par → 00 electoral si
   falta) y la 05 del run final si la cadena no publicó. Cerca de las 5 h 20 min se releva con `modo=continuar`.
4. Anota el run del Gestor y termina el turno. Sin vigilar. El resultado por territorio está en el resumen del run.
5. Tras un fallo no relances: diagnostica (`diagnosticar-run`) e informa. `continuar` solo lo usa el propio Gestor.

`modo=matriz` conserva la campaña anterior (manifiesto inmutable, 00 por `workflow_call`).
