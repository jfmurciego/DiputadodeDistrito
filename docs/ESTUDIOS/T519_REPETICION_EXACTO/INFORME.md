# T-519 · ¿Se repite el exacto de Deslinde cuando cambia la velocidad de la máquina?

Fecha: 2026-11-28. Código: `main` 548968c4 (Deslinde 1.2). Sesión cloud, 4 núcleos y 15 GB; Python 3.13.18, ortools
9.14.6206. En local, con el motor real. No se ha lanzado nada, no se ha publicado nada y no se ha cambiado el motor.

## Resultado

Clave D8 del ganador: fuera de tolerancia · exceso sobre el 8 % · demarcaciones partidas · frontera · desvío máximo.
Las huellas van cortadas a 12 caracteres; enteras, en `RESULTADOS.json`.

| Territorio | Condición | Ganador | Clave D8 | Exacto (etapa que no cierra) | `huella_resultado` | sha256 de la composición | Reloj (s) |
|---|---|---|---|---|---|---|---|
| nac12 | reposo 1 | exacto | 0 · 0,00 % · 3 · 196,3 km · 3,31 % | óptimo demostrado | `98a90a590d37` | `ed1d920c3e48` | 132 |
| nac12 | reposo 2 | exacto | 0 · 0,00 % · 3 · 196,3 km · 3,31 % | mejor válido (desvío: con plan, sin cerrar) | `855d9ddaf6cd` | `ed1d920c3e48` | 141 |
| nac12 | un núcleo | exacto | 0 · 0,00 % · 3 · 196,3 km · 3,31 % | óptimo demostrado | `98a90a590d37` | `ed1d920c3e48` | 231 |
| nac12 | con carga | exacto | 0 · 0,00 % · 3 · 196,3 km · 3,31 % | mejor válido (desvío: con plan, sin cerrar) | `855d9ddaf6cd` | `ed1d920c3e48` | 123 |
| nac15 | reposo 1 | exacto | 0 · 0,00 % · 6 · 483,9 km · 7,25 % | mejor válido (frontera: con plan, sin cerrar) | `5422228aaf3a` | `c39a0bbc8ec9` | 128 |
| nac15 | reposo 2 | exacto | 0 · 0,00 % · 6 · 483,9 km · 7,25 % | mejor válido (frontera: con plan, sin cerrar) | `5422228aaf3a` | `c39a0bbc8ec9` | 129 |
| nac15 | un núcleo | exacto | 0 · 0,00 % · 6 · 483,9 km · 7,25 % | mejor válido (frontera: con plan, sin cerrar) | `5422228aaf3a` | `c39a0bbc8ec9` | 211 |
| nac15 | con carga | exacto | 0 · 0,00 % · 6 · 483,9 km · 7,25 % | mejor válido (frontera: con plan, sin cerrar) | `5422228aaf3a` | `c39a0bbc8ec9` | 129 |
| nac20 | reposo 1 | vigente | 0 · 0,00 % · 3 · 190,3 km · 7,57 % | mejor válido (desvío: sin plan) | `795e0a181fda` | `6f9aa9fff709` | 141 |
| nac20 | reposo 2 | vigente | 0 · 0,00 % · 3 · 190,3 km · 7,57 % | mejor válido (desvío: sin plan) | `795e0a181fda` | `6f9aa9fff709` | 145 |
| nac20 | un núcleo | vigente | 0 · 0,00 % · 3 · 190,3 km · 7,57 % | mejor válido (desvío: sin plan) | `795e0a181fda` | `6f9aa9fff709` | 272 |
| nac20 | con carga | vigente | 0 · 0,00 % · 3 · 190,3 km · 7,57 % | mejor válido (desvío: sin plan) | `795e0a181fda` | `6f9aa9fff709` | 138 |
| nac41 | reposo 1 | exacto | 0 · 5,50 % · 6 · 786,0 km · 13,50 % | mejor válido (frontera: con plan, sin cerrar) | `ca56e3c6cfc7` | `0bba8f52830d` | 154 |
| nac41 | reposo 2 | exacto | 0 · 5,50 % · 6 · 786,0 km · 13,50 % | mejor válido (frontera: con plan, sin cerrar) | `ca56e3c6cfc7` | `0bba8f52830d` | 153 |
| nac41 | un núcleo | exacto | 0 · 5,50 % · 6 · 786,0 km · 13,50 % | mejor válido (frontera: con plan, sin cerrar) | `ca56e3c6cfc7` | `0bba8f52830d` | 269 |
| nac41 | con carga | exacto | 0 · 5,50 % · 6 · 786,0 km · 13,50 % | mejor válido (frontera: con plan, sin cerrar) | `ca56e3c6cfc7` | `0bba8f52830d` | 150 |
| nac43 | reposo 1 | exacto | 0 · 6,10 % · 6 · 467,2 km · 14,10 % | mejor válido (frontera: sin plan) | `ff878f74cca4` | `61c7a48fa08f` | 201 |
| nac43 | reposo 2 | exacto | 0 · 6,10 % · 6 · 386,8 km · 14,10 % | mejor válido (frontera: con plan, sin cerrar) | `e1415f76031d` | `847f87edf182` | 198 |
| nac43 | un núcleo | exacto | 0 · 6,10 % · 6 · 467,2 km · 14,10 % | mejor válido (frontera: sin plan) | `ff878f74cca4` | `61c7a48fa08f` | 358 |
| nac43 | con carga | exacto | 0 · 6,10 % · 6 · 386,8 km · 14,10 % | mejor válido (frontera: con plan, sin cerrar) | `e1415f76031d` | `847f87edf182` | 200 |

| Territorio | Mapa | `huella_resultado` | Estado del exacto | Cota de la etapa abierta | Frente a T-507 |
|---|---|---|---|---|---|
| nac12 (Castellón) | 1 en 4 | **2 en 4** | **2 óptimo, 2 mejor válido** | 2 valores | mismo mapa |
| nac15 (La Coruña) | 1 en 4 | 1 en 4 | mejor válido | 4 valores | mismo mapa |
| nac20 (Guipúzcoa) | 1 en 4 | 1 en 4 | mejor válido (gana el vigente) | 2 valores | mismo mapa |
| nac41 (Sevilla) | 1 en 4 | 1 en 4 | mejor válido | 4 valores | mismo mapa |
| nac43 (Tarragona) | **2 en 4** | **2 en 4** | mejor válido | 4 valores | 2 iguales (467,2 km), 2 distintos (386,8 km) |

- **nac43 no repite el mapa.** En dos ejecuciones la etapa de frontera acaba sin plan y queda el de la etapa anterior
  (467,2 km, el de T-507). En las otras dos encuentra uno de 386,8 km. Los dos son válidos y parten 6 demarcaciones.
- **nac12 repite el mapa y no la huella.** La última etapa (desvío) cierra en dos ejecuciones y en dos no, con el mismo
  valor. El estado de las etapas entra en `huella_resultado`.
- **No depende de la velocidad.** Las dos ejecuciones en reposo ya difieren entre sí en nac12 y nac43. La de un núcleo
  (hasta 358 s frente a 201 s) coincide con una de ellas, y la de carga, con la otra.
- **El tope no es de reloj.** Es tiempo determinista de CP-SAT (60 unidades por etapa, 4 hilos, `interleave_search`,
  semilla 0). Aun así, la búsqueda no se repite: la cota de la etapa abierta cambia en los cinco territorios. La frase
  «misma entrada, mismo plan, con cualquier carga» de `paquetes/deslinde/src/deslinde/exacto.py` no se cumple en nac43.

## Conclusión

1. Se repiten las cuatro veces (ganador, mapa y huella) nac15, nac20 y nac41. nac12 repite el mapa, pero no la huella.
   nac43 no repite ni el mapa.
2. La causa no es la máquina: es el resolutor con 4 hilos en una etapa que no cierra. Por eso nac15, nac20 y nac41
   tampoco están garantizados: su cota también cambia, y cuatro ejecuciones no lo descartan.
3. Mañana, nac43 puede salir con cualquiera de los dos mapas, y nac12, con cualquiera de las dos huellas. Los mapas
   medidos en T-507 son uno de los resultados posibles, no el único. Ningún resultado es inválido ni peor que el de T-507.
4. Arreglo más pequeño (no implementado; es un cambio de motor): un solo hilo en el exacto (`HILOS = 1`). Es una
   hipótesis sin medir. Puede cambiar el plan y la huella en todo territorio donde aplica el exacto (también con K ≤ 4)
   y obliga a repetir T-507: el propio fichero avisa de que con un hilo Valladolid no cerraba la etapa 2. Que un «mejor válido» no compita no sirve: en nac12
   cambiaría el ganador de una ejecución a otra.
5. Criterio de aceptación: con el cambio, `repetir.sh` (20 ejecuciones) da un solo valor por territorio de ganador,
   composición, `huella_resultado`, estado del exacto y etapas con su cota (todo a 1 en `TABLA.md`), y la clave D8 del
   ganador no empeora frente a T-507 en ninguno de sus 25 territorios.

## Método
- Un comando: `bash docs/ESTUDIOS/T519_REPETICION_EXACTO/repetir.sh`. Monta el entorno (`requirements.lock`, cadenas sin
  dependencias y `requirements-exacto.lock` con hashes), baja el seccionado 2023 y 2024 de www.ine.es (sha256 comprobado
  contra `orchestracion/fuentes_r2.json`), adquiere las entradas (`bateria_motor.py entradas --desde-fuente --seccionado
  shapefile`) y ejecuta. `tabla.py` escribe `RESULTADOS.json` y `TABLA.md`.
- Cada ejecución es la competición completa en un proceso nuevo: `PYTHONHASHSEED=0 python -m ddd_motor2.competir` (D8,
  10 cadenas), con su propia carpeta de salida.
- Condiciones: «reposo 1» y «reposo 2» a la vez, cada una en su copia del repositorio; «con carga», sola y con tres
  copias de `carga.py`; «un núcleo», sola y con `taskset -c 0`.
- «Frente a T-507»: huella del plan ganador de `docs/ESTUDIOS/T507_EXACTO_K5/RESULTADOS.json`. T-507 no guardó
  `huella_resultado`.

## Límites
- 20 ejecuciones (4 por territorio), no las 25 del informe T-509. Una sola clase de máquina; sin ejecución en GitHub.
- No se sabe con qué frecuencia sale cada mapa de nac43: dos y dos en cuatro ejecuciones.
- El diagnóstico de los cinco territorios sin solución (nac06, nac17, nac18, nac31 y nac45) no entra en esta medición.

## Coste
Unos 51 min de reloj en local: entorno, fuentes y entradas (4 min) y 20 competiciones (47 min).
