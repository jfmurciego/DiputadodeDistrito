# T-509 · L1 — Mejora local exacta sobre el ganador de Deslinde

VERSIÓN: 1.0.0 · FECHA: 2026-11-28 · ANTERIOR: ninguna (fichero nuevo)

Laboratorio, no motor: no cambia producción, no lanza workflows, no abre PR.
Guion y datos: `docs/ESTUDIOS/T509_LAB_MEJORA_LOCAL/` (`reproducir.sh`, `mejora_local.py`, `resultados/`).

## Pregunta

Partiendo del mapa ganador de Deslinde, ¿mejora la clave D8 si se reoptimizan de forma exacta (CP-SAT)
grupos de 2 o 3 distritos vecinos con el resto fijo, repitiendo hasta que nada mejore? ¿Cuánto cuesta?

## Respuesta corta

**Sí: mejora en 6 de 6 territorios**, con todas las reglas duras cumplidas en las 12 ejecuciones.
Cuesta entre 4 y 15 minutos por territorio con 4 núcleos (de 3 a 37 veces lo que tarda la competición).
Se repite en 5 de 6. En 3 de 6 se agotó el tope de 15 minutos sin terminar: ahí queda mejora por recoger.

## Con qué se decide que un plan «mejora»

Con la **clave oficial del motor**: `Natural.clave(plan, "D8")[:5]`, sobre el mismo objeto que usa
`competicion.juzgar` (`natural_desde_m06`). Es decir: (distritos fuera de tolerancia, exceso sobre el 8 %,
demarcaciones partidas, frontera cortada en km redondeada a metros, desvío máximo).

- El submodelo CP-SAT trabaja, como `exacto.py`, con la frontera en milímetros. Solo **propone**.
- Una propuesta se acepta solo si la clave oficial baja estrictamente y `nat.valido(plan)` es cierto
  (`mejora_local.py`, líneas 139-140 y 381-384). Las propuestas que no bajan la clave oficial se descartan
  y se cuentan (`no_mejora_clave_oficial`).
- Las columnas «antes» y «después» de la tabla salen de esa misma función. Al final, el plan pasa por
  `deslinde.reglas.evaluar.evaluar` (el evaluador del motor) para las reglas duras.

No hubo que corregir nada: la comparación final ya es con la clave oficial.

## Resultados

Clave D8 = fuera · exceso 8 % · partidas · frontera (km) · desvío máximo. Valores exactos en `resultados/RESUMEN.csv`.
Tamaño = átomos × K (el exacto del motor aplica hasta 2.000). Tiempos de las dos repeticiones, 4 núcleos.

| Territorio | K | Átomos | Tamaño | D8 antes | D8 después | Tiempo (s) | Competición (s) | Reglas duras | ¿Se repite? | ¿Terminó? |
|---|---|---|---|---|---|---|---|---|---|---|
| Zaragoza (Congreso) | 8 | 298 | 2.384 | 0 · 0,0344 · 8 · 945,2 · 0,114 | 0 · 0,0343 · **3** · **631,0** · 0,114 | 639 / 629 | 24 | sí | sí | sí, con 10 de 123 subproblemas sin cerrar |
| Alicante (Congreso) | 17 | 145 | 2.465 | 0 · 0,0699 · 12 · 728,5 · 0,150 | 0 · 0,0699 · 12 · **692,8** · 0,150 | 299 / 299 | 100 | sí | sí | sí (231 subproblemas; 0 y 1 sin cerrar) |
| Cantabria (autonómica) | 35 | 160 | 5.600 | 8 · 0,0295 · 13 · 762,1 · 0,723 | **5** · 0,0299 · **10** · 623,2 (rep. 2: 642,9) · 0,723 | 900 / 899 | 342 | sí | **no** | no: tope de 15 min |
| Asturias (autonómica) | 45 | 137 | 6.165 | 3 · 0,0262 · 26 · 1.243,0 · 0,371 | **2** · 0,0325 · **19** · 1.144,5 · 0,637 | 233 / 222 | 47 | sí | sí | sí: óptimo local demostrado (1.218 subproblemas, todos cerrados) |
| Valencia (Congreso) | 23 | 272 | 6.256 | 0 · 0,0109 · 26 · 1.088,4 · 0,091 | 0 · **0** · **19** · **812,5** · 0,078 | 900 / 900 | 40 | sí | sí | no: tope de 15 min |
| La Rioja (autonómica) | 33 | 205 | 6.765 | 1 · 0,0366 · 7 · 563,0 · 0,418 | 1 · 0,0366 · **6** · **523,6** · 0,418 | 900 / 900 | 35 | sí | sí | no: tope de 15 min |

Mejoras aceptadas por territorio: 8, 9, 48, 41, 47 y 13. La mayoría son de pares; los tríos aportan pocas (2 o 3).

## Veredicto honesto

1. **Mejora de verdad.** En los seis territorios la clave oficial baja y el evaluador del motor da el plan por válido.
   Los saltos grandes: Zaragoza (8 → 3 demarcaciones partidas, un tercio menos de frontera), Valencia
   (26 → 19 y el exceso sobre el 8 % a cero) y Cantabria (8 → 5 distritos fuera de tolerancia).
2. **Alicante mejora poco:** solo la frontera (−36 km); población y demarcaciones partidas quedan igual.
3. **Asturias mejora la clave pero no a ojos de cualquiera:** un distrito menos fuera de tolerancia y 7 demarcaciones
   partidas menos, a cambio de que el peor distrito pase del 37 % al 64 % de desvío. La clave lo permite porque el
   desvío máximo es el último término. Es un asunto de la clave, no de la mejora local, pero aquí se ve.
4. **No es el óptimo global.** Solo Asturias llega a un óptimo local demostrado. En Valencia, La Rioja y Cantabria se
   cortó a los 15 minutos; en Zaragoza quedaron 10 subproblemas sin cerrar en su tiempo.
5. **Cantabria no se repite** (623,2 km frente a 642,9 km): los topes de reloj (60 s por subproblema, 15 min en total)
   cortan en puntos distintos según la carga de la máquina. Donde no se tocó el tope total, el resultado fue idéntico.
6. **Límites de la muestra:** 6 territorios; el «antes» es el ganador de una competición local con 10 cadenas
   reproducida desde la fuente, no el mapa publicado; Madrid quedó fuera (no se adquiere en la nube).

## Coste

- De 222 a 900 s por territorio con 4 núcleos; la competición sola tarda de 24 a 342 s.
- El tiempo se va en pares que no mejoran: en Asturias, 1.218 subproblemas para 41 mejoras.

## Cómo entraría en el motor (si el propietario lo decide)

- Como **un candidato más** de la competición: se siembra en el ganador, se pule y lo juzga el mismo `juzgar`.
  Nunca sustituye al ganador si la clave oficial no baja o el evaluador no lo valida; así no puede empeorar nada.
- **Sin topes de reloj:** solo `max_deterministic_time` por etapa y un presupuesto en número de subproblemas, con
  4 hilos, `interleave_search` y semilla fija, como el exacto. Es condición para que entre en la huella del resultado.
- Mismo ámbito que el exacto en cuanto a reglas (una circunscripción, mismas disciplinas), pero sin el límite de tamaño.
- Cambia el resultado de los territorios donde actúe: es cambio de motor (versión del paquete y decisión D-216).

### Criterio de aceptación propuesto (verificable)

1. En estos seis territorios, clave oficial D8 del candidato ≤ la del ganador en todos y estrictamente menor en al
   menos cinco; `evaluar` válido en todos.
2. Dos ejecuciones en la misma máquina dan la misma huella de plan en los seis (hoy: cinco).
3. Tiempo añadido ≤ 15 minutos por territorio con 4 núcleos.
4. En un territorio donde el exacto del motor ya aplica, la mejora local sobre su resultado no encuentra nada.
5. Los territorios donde no actúa conservan su huella.

Objeción (una línea): antes de llevarlo al motor conviene decidir si el caso de Asturias (mejor clave con peor
desvío máximo) es lo que se quiere de la clave D8.

## Reproducir

```
bash docs/ESTUDIOS/T509_LAB_MEJORA_LOCAL/reproducir.sh
```

Necesita red a `www.ine.es` y a PyPI, 4 núcleos y unas 2 horas para los seis territorios (OR-Tools 9.14.6206).
