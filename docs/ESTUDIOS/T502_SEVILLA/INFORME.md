# T-502 · Por qué Deslinde pierde en Sevilla (diagnóstico)

Fecha: 2026-11-26. Hecho solo en local, con los datos del piloto del banco (#1025). Código de `main` 9e34ba52.
No hay runner, no se ha ejecutado nada en producción y no se ha publicado nada. Sevilla es el Congreso nac41, con K = 16
y 111 unidades (átomos) en el espacio del canónico.

## Las dos soluciones, demarcación por demarcación

Las dos son válidas en el núcleo (`evaluar(...).valido`). Tienen 0 distritos fuera de tolerancia y el mismo exceso
sobre el 8 % (13,50 % de desvío máximo, que fija la población). La diferencia está en el tercer término de D8.

| Demarcación | Deslinde (ganador `ponderado-s1767573395`) | Exacto (óptimo demostrado) |
|---|---|---|
| Partido judicial 41-03 | partido en 3 distritos | partido en 4 |
| Partido judicial 41-04 | partido en 2 | **entero** |
| Partido judicial 41-05 | partido en 2 | **entero** |
| Partido judicial 41-06 | partido en 10 | partido en 10 |
| Partido judicial 41-08 | entero | partido en 2 |
| Partido judicial 41-13 | partido en 2 | **entero** |
| Comarca agraria El Aljarafe | partida en 4 | partida en 4 |
| Comarca agraria La Campiña | partida en 6 | partida en 6 |
| Comarca agraria La Vega | partida en 13 | partida en 13 |
| **Demarcaciones partidas** | **8** | **6** |
| Frontera cortada | 763,8 km | 786,0 km |

El exacto deja enteros tres partidos (41-04, 41-05 y 41-13). A cambio, parte el 41-08 y corta 22 km más de frontera,
que es un término posterior de D8. Las tres comarcas agrarias están partidas igual en los dos planes, porque son más
grandes que un distrito.

## Causa

No es la semilla, ni las restricciones, ni el tiempo de las cadenas. Es la **aplicabilidad de los candidatos que
buscan el óptimo**. `COMPETICION.json` de Sevilla lo dice:

- `exacto`: «NO_APLICA, K=16 fuera de 2..4». Deslinde solo usa CP-SAT con K ≤ 4 (`deslinde/exacto.py`,
  `K_MAX = 4`, fijado en T-297 con los casos de T-296).
- `exhaustivo`: «no se intenta, el árbol de enumeración tiene al menos 200.160 nodos > presupuesto 200.000».
- Así que solo compiten las 10 cadenas «ponderado», el canónico y el vigente. Ninguno baja de 8: siete empatan en 8
  (con el vigente) y los demás dan entre 10 y 15. GerryChain puro (10 semillas × 10⁵ pasos, #1025) tampoco baja de 8.

**Prueba:** misma entrada y misma competición, cambiando solo `K_MAX` a 16 en memoria (sin tocar el repositorio).
- Gana el candidato `exacto`, con 6 demarcaciones partidas y 785,968 km de frontera. Es exactamente el óptimo D8 de
  `optimo_d8.py`.
- Tarda 1 min 44 s de reloj y 3 min 32 s de CPU, frente a 20 s y 21 s sin el exacto.
- Dos ejecuciones seguidas dan el mismo plan (misma `huella_plan`).

## Segundo hallazgo: la huella del resultado no se reproduciría

Con K = 16, la etapa 4 (frontera) no demuestra el óptimo dentro del tope determinista. El estado queda en
`MEJOR_VALIDO`, con el valor correcto pero sin prueba. La **cota** que CP-SAT da de esa etapa cambia de una ejecución a
otra, con la misma entrada, `interleave_search` y `random_seed` 0:

| Tope determinista | Ejecución | Cota de la etapa 4 | Tiempo |
|---|---|---|---|
| 60 | 1 | 345.072.575 | 1 min 44 s |
| 60 | 2 | 355.377.584 | — |
| 300 | 1 | 717.996.794 | 4 min 27 s |
| 300 | 2 | 463.416.305 | 4 min 10 s |

El plan y el valor (785.968.300 mm) no cambian, pero esa cota entra en `huella_resultado`, y la huella cambia. En los
territorios con K ≤ 4 del piloto no pasa nada, porque todas las etapas cierran. Subir el tope no lo resuelve.

## Propuesta para Deslinde (sin implementar)

1. **Aplicabilidad por tamaño y no por K.** `exacto.aplicable` aceptaría 2 ≤ K ≤ 16 y, como tope de tamaño,
   átomos × K ≤ 2.000. Sevilla da 1.776, Burgos 1.116 y Valladolid 904. Se mantienen la clave D8, una circunscripción y
   sin exenciones. El límite exacto se calibra con la pasada del exacto por las 28 provincias restantes (T-468); 2.000
   es el mínimo que cubre lo medido hoy.
2. **Huella reproducible.** En una etapa que no termina OPTIMAL, a `huella_resultado` solo entran el nombre, el estado y
   el valor, no la cota. La cota sigue en el informe como dato.
3. **Coste.** Unos 85 s de reloj y 3 min de CPU más por competición en Sevilla. Para los demás territorios de K entre 5
   y 16 hay que medirlo en la misma pasada de T-468.

**Efectos, si se implementa:**
- cambia el ganador de Sevilla y la huella `motor2` de todos los territorios donde el exacto pase a aplicar;
- se regeneran `HUELLAS_FIJAS` y la aceptación del motor 2;
- hay que rehacer la 00 (el P30) de los territorios afectados y volver a publicar Sevilla, con permiso del propietario;
- no toca M04, M05 ni N08.

## Test de regresión

`tests/test_t502_sevilla_exacto.py` hace la competición real de Sevilla y exige que el ganador parta 6 demarcaciones
(el literal del óptimo demostrado en #1025). Está **desactivado**: se salta salvo con `DDD_T502_ACTIVO=1`, y además
necesita las entradas de la batería (`DDD_BATERIA_OUT`), que no están en git. En la CI no corre.

Comprobado en local:
- sin activar, se salta;
- activado sobre `main`, falla con «8 != 6, ganador ponderado-s1767573395 parte 8 demarcaciones»;
- con `K_MAX = 16` en memoria, la misma competición da 6. El test, que ejecuta la competición en un subproceso, pasará
  cuando el arreglo esté en el código.

## Coste de este diagnóstico

Unos 31 min de CPU: dos competiciones con tope 60 (3,5 min cada una), dos con tope 300 (11,4 min cada una) y la
prueba del test (menos de 1 min). Reutiliza las entradas y
el entorno del piloto.
