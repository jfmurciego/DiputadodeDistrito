---
name: lanzar-campana
description: Procedimiento para lanzar la legislatura vigente (nacional, autonómicas, una comunidad o provincias) con el «P00 Campaña — Gestor» (gestor-campanas.yml, modos plan y lanzar) y, tras fusionarse, con la P00 nueva (p00-campana.yml: solo comprobar, comprobar y lanzar). Úsala solo en el chat operador; «lanzar» exige permiso explícito del propietario en ese mensaje.
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
   `max_paralelo`, por defecto 3; `estrategia`). Arranca al hacer el dispatch (D-127: `produccion` ya no pide clic; el control es la frase D-52 de la campaña).
   Después, el Gestor (como bot, sin más clics): territorio de prueba si el lote es > 1 (si falla, para); el resto con
   `max_paralelo`; por territorio 00 `publish_result=true` + `lanzado_por_eleccion` (la 00 encadena par → 00 electoral si
   falta) y la 05 del run final si la cadena no publicó. Cerca de las 5 h 20 min se releva con `modo=continuar`.
4. Anota el run del Gestor y termina el turno. Sin vigilar. El resultado por territorio está en el resumen del run.
5. Tras un fallo no relances: diagnostica (`diagnosticar-run`) e informa. `continuar` solo lo usa el propio Gestor.

`modo=matriz` conserva la campaña anterior (manifiesto inmutable, 00 por `workflow_call`).

## P00 Campaña nueva (`p00-campana.yml`, T-379 PR 3; se usa tras fusionarse, después del 29-11)
Una campaña = una ejecución (D-130). Botón: territorios (`todos`, `congreso`, `autonómicas` o códigos `nac22, aut11`),
elección (`vigente` | `2026-11` ensayo: no commitea ni publica), inicio (por defecto «Generar desde fuente territorial
acreditada»), modo (`solo comprobar` por defecto | `comprobar y lanzar`), publicar.
1. Siempre primero `solo comprobar` (sin efectos salvo el issue «P00 Campaña · <run>»): semáforo y gasto semanal (D-46)
   en el resumen y en el issue. Con eso, la ficha D-52 y la frase del propietario; luego `comprobar y lanzar`.
   ```
   gh api -X POST repos/jfmurciego/DiputadodeDistrito/actions/workflows/p00-campana.yml/dispatches -f ref=main \
     -f "inputs[territorios]=nac22, aut11" -f "inputs[modo]=solo comprobar"
   ```
2. Si hay otra P00 viva (también un «solo comprobar» o una en `waiting`), la nueva sale en rojo con `CAMPANA_EN_CURSO`
   y el run que bloquea; no se encola. Cancelarla exige frase del propietario.
3. Un territorio apartado no para a los demás; la parada sistémica (≥3 con la misma causa o ≥20 % con mínimo 3) es
   PEGAJOSA: no se levanta en esa campaña, ni re-ejecutando. Se sale con otra campaña.
4. Re-ejecutar «jobs fallidos» en la misma ejecución solo para `SIN_RESULTADO`/transitorios y para el cierre; un
   apartado no transitorio sale «no re-ejecutable». El job `resultado` en rojo abre la IA de cierre de P90.
