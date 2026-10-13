# NAT-G-003 — perfil de escala sintético de M05

## Alcance y criterio

Este diagnóstico mide `ddd_core.m05_population_repair.repair()` con una ruta sintética no geográfica. No carga ni altera fuentes DDD, no atribuye población real y no produce distritos territoriales. La carga mantiene distritos contiguos de diez nodos y población exacta 100; suelo 90 y techo 110 hacen que un movimiento simple entre distritos vecinos sea rechazado por cotas. Sirve para medir la búsqueda bajo candidatos inválidos, no para estimar una campaña provincial ni probar calidad de una partición.

Criterios: el constructor debe producir exactamente `N` nodos, `N-1` aristas simétricas, bloques contiguos iguales; cada reparación debe terminar por vaciado de cola o por los límites declarados, restaurar el baseline válido y reportar su terminación. Memoria es el pico de asignación Python medido con `tracemalloc` dentro de `repair()`, excluye la construcción del fixture y no equivale a RSS del proceso.

## Reproducción

```sh
python herramientas/benchmark_m05_escalabilidad_sintetico.py \
  --sizes 100 500 1000 --seconds 0.5 --candidates 2000 --block-size 10
python -m unittest tests.test_m05_scalability_benchmark
```

La primera ejecución observada fue Python 3.10.19, macOS 11.7.11 x86_64. Tiempo y contadores en caso de timeout dependen del equipo y carga; el fixture, sus nodos/aristas y parámetros son deterministas.

| Nodos | Aristas | Distritos | Tiempo (s) | Pico Python en repair (bytes) | Transiciones evaluadas | Terminación |
|---:|---:|---:|---:|---:|---:|---|
| 100 | 99 | 10 | 0.089774 | 485,468 | 118 | `QUEUE_EMPTY` |
| 500 | 499 | 50 | 0.526209 | 5,982,199 | 59 | `TIME_BUDGET_EXHAUSTED` |
| 1.000 | 999 | 100 | 0.540659 | 6,186,876 | 27 | `TIME_BUDGET_EXHAUSTED` |

Los tres casos conservaron baseline y devolvieron `NO_FEASIBLE_REPAIR_FOUND`; aquí esto sólo significa que no había movimiento mejorador válido en el fixture. No es una afirmación de imposibilidad territorial. El límite de 0,5 s se excedió hasta 0,041 s en estos casos porque las operaciones internas comprueban la hora entre transiciones y no pueden interrumpir una operación en curso.

## Observaciones de escalabilidad

- En esta topología, aumentar de 100 a 500 nodos sube el pico Python observado de aproximadamente 0,46 MiB a 5,70 MiB; a 1.000 nodos el pico fue aproximadamente 5,90 MiB. Son medidas de una ejecución local, no garantías ni estimaciones de memoria residente.
- A 500/1.000 nodos el presupuesto de tiempo termina la búsqueda antes que el límite de 2.000 candidatos. `candidates_examined` cuenta transiciones aceptadas para expandir estado; las transiciones rechazadas por cotas pueden consumir tiempo y elevar `transitions_evaluated` sin gastar dicho presupuesto. El límite temporal es, por ello, la protección efectiva para esta carga adversa.
- No hay API de checkpoint/reanudación en `repair()`: `SearchLimits` impone profundidad, conjunto transferido, candidatos, tiempo y semilla; el resultado expone contadores/causa final, pero no serializa frontera de búsqueda, cola ni conjunto `seen`. El estado de campaña puede reanudar una nueva llamada/provincia, pero no continuar exactamente esta búsqueda interrumpida.
- El barrido no modela municipios, multipolígonos, provinciales reales, construcción del grafo ni fases M01–M04/M06. No acredita escalabilidad nacional de la reparación ni certifica resultados.

## Resultado

**Evidencia útil, alcance limitado:** se agrega un benchmark repetible y pruebas del constructor de fixtures. No se cambió M05 ni su política. Para garantizar pausa/reanudación dentro de una provincia hará falta una tarea separada de diseño de checkpoint que serialice y valide la frontera y el estado de búsqueda; este expediente no afirma que exista.
