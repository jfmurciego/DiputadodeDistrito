# T-296 · Óptimo exacto de D8 y hueco del ganador de Deslinde (estudio privado, D-73, D-92)

Fecha: 2026-11-14. Prototipo: `optimo_d8.py` 1.0.0, con OR-Tools CP-SAT 9.14.6206 (el pin de `requirements-banco-motor.lock`).
Solo lee `ddd_motor2` y `herramientas/certificador_exacto.py`. No cambia el motor ni producción, no lanza nada y no publica nada.
Máquina: sesión cloud con 4 núcleos y 15 GB. Tope de 120 s por etapa, 4 hilos.

## Qué se resuelve

**Problema.** Es el mismo que juzga la competición, en estos pasos:
- Unidades: las de la composición M06 del canónico (`adaptadores.problema_y_plan`), con los núcleos cerrados del canónico.
- Reglas: `Reglas.desde_contrato` (K, suelo, techo, provincia, contigüidad, R-NUCLEO y R012 con su máximo de mixtos).
- Átomos: `certificador_exacto.construir_atomos`.
- Demarcaciones y frontera: las de `naturalidad_clave.natural_desde_m06`, que es la clave D8 oficial.

**Modelo.** Es la formulación de `certificador_exacto.resolver` 1.4.0:
- contigüidad por árbol padre/nivel;
- simetría rota por el átomo mínimo de cada distrito;
- R012 con K entre ceil(P/techo) y ceil(P/objetivo).

El prototipo no admite exenciones de suelo o techo ni varias circunscripciones. Si un territorio las tiene, el script se niega a resolverlo.

**Objetivo.** Es la clave D8 lexicográfica, resuelta por etapas. El óptimo de cada etapa queda fijado antes de la siguiente:

| Etapa | Término |
|---|---|
| E1 | distritos fuera de tolerancia |
| E2 | exceso del desvío máximo de los distritos dentro de tolerancia sobre el 8 % |
| E3 | partidos judiciales y comarcas agrarias partidos |
| E4 | frontera cortada |
| E5 | desvío máximo |

La huella del plan solo desempata y no se modela. Todos los valores son enteros exactos: el 8 % se trata como 2/25 y los desvíos se escalan por el denominador del objetivo.

**Garantías.**
1. Cada plan del modelo se vuelve a juzgar con `reglas.evaluar`, y su clave se calcula con `Natural.clave("D8")`.
2. El canónico y el ganador, fijados en el modelo, son factibles y dan exactamente su clave oficial («modelo_acepta»: 20 de 20 casos). Por tanto el modelo no es más estricto que el núcleo, y su óptimo es una cota inferior válida.
3. Si una etapa no termina, el script da el mejor valor encontrado y la cota probada, y se para: las etapas siguientes ya no serían exactas.

**Ganador de Deslinde.** Sale de la competición local (`ddd_motor2.competir`: D8, 10 cadenas, `PYTHONHASHSEED=0`), con el código de `main` en 2c4e2471 (procedencia anotada a mano; los JSON no guardan el commit). Las entradas son las de `bateria_motor.py entradas --seccionado shapefile`, con la huella de población del contrato. La clave del ganador recalculada coincide con la de `COMPETICION.json` en los 9 territorios.

## Resultados

En la tabla, «partidas» cuenta los partidos judiciales más las comarcas agrarias partidos, y «desv.» es el desvío máximo. Los tiempos son del recálculo final (`resultados/*.json`).

| Territorio | K | Unidades | Ganador | Ganador: fuera / exceso / partidas / desv. | Óptimo D8: fuera / exceso / partidas / desv. | Estado | Hueco (primer término distinto) | Tiempo |
|---|---|---|---|---|---|---|---|---|
| Álava (nac01) | 3 | 53 | canónico | 0 / 0,0694 / 2 / 14,94 % | igual | ÓPTIMO | ninguno, es la misma partición | 1 s |
| Cuenca (nac16) | 2 | 238 | cadena | 0 / 0 / 3 / 1,48 % | 0 / 0 / 3 / **0,00 %** | ÓPTIMO | desvío: 1,48 puntos | 5 s |
| Guadalajara (nac19) | 2 | 288 | vigente | 0 / 0 / 2 / 0,05 % | 0 / 0 / 2 / **0,00 %** | ÓPTIMO | desvío: 0,05 puntos | 4 s |
| Huesca (nac22) | 2 | 202 | vigente | 0 / 0 / 1 / 2,11 % | igual | ÓPTIMO | ninguno, es la misma partición | 4 s |
| La Rioja (nac26) | 3 | 175 | cadena | 0 / 0 / 2 / 0,15 % | igual | ÓPTIMO | ninguno (en una pasada anterior con 2 hilos, no versionada, salió un empate con otra partición) | 4 s |
| Lugo (nac27) | 3 | 67 | vigente | 0 / 0 / 3 / 0,55 % | 0 / 0 / 3 / **0,20 %** | ÓPTIMO | desvío: 0,35 puntos | 1 s |
| **Burgos (nac09)** | 3 | 372 | vigente | 0 / 0 / **3** / 0,02 % | 0 / 0 / **2** / 4,23 % | ÓPTIMO | **partidas: 3 frente a 2** | 8 s |
| **Valladolid (nac47)** | 4 | 226 | cadena | 0 / 0,0600 / **4** / 14,00 % | 0 / 0,0600 / **2** / 14,00 % | ÓPTIMO | **partidas: 4 frente a 2** | 9 s |
| La Rioja autonómica (aut17) | 33 | 193 (canónico) y 315 (ganador) | cadena | 1 / 0,0366 / 7 / 41,78 % | E1 sin cerrar: fuera ∈ [0, 1] | COTA | no demostrado; el ganador es el mejor plan hallado | 249 s |

Los territorios de K=1 (Ávila, Segovia, Soria, Palencia, Teruel, Zamora, Ceuta y Melilla) tienen un solo plan, la provincia entera. Ese plan es a la vez el ganador y el óptimo, así que no se resolvieron.

## Conclusiones

1. **El óptimo D8 cabe en el Congreso pequeño.** Con K ≤ 4 y hasta 372 unidades, CP-SAT demuestra el óptimo lexicográfico completo en 1-9 s y con menos de 250 MB. Basta con pocos segundos por territorio para usarlo como competidor y certificador (D-73).
2. **Deslinde ya es óptimo en 3 de 8.** En Álava, Huesca y La Rioja, el ganador iguala la clave D8 demostrada hasta la huella. En Cuenca, Guadalajara y Lugo solo pierde en el último término, el desvío máximo: 1,48, 0,05 y 0,35 puntos.
3. **Hallazgo: en Burgos y Valladolid hay planes válidos estrictamente mejores en D8 que el ganador.**
   - Burgos: 2 demarcaciones partidas, frente a 3 del ganador (el vigente).
   - Valladolid: 2, frente a 4 de la mejor cadena.

   Ambos planes cumplen el núcleo (`valido_nucleo`). En Valladolid empatan en población; en Burgos el desvío sube del 0,02 % al 4,23 %, todavía por debajo del 8 % de D8. Las 10 cadenas no encuentran estos planes. Un competidor exacto los habría elegido. Son planes del modelo y no se ha generado su M06; las composiciones están en `resultados/<t>_canonico_mejor_modelo.csv`.
4. **Hallazgo: el término de frontera (E4) vale 0 en todos los planes.** El grafo M03 de las entradas no trae `shared_border_m`, y la competición de la batería r3 (T-196) también da 0,0 km. Por tanto D8 no aplica hoy «cortar por donde hay menos vínculo» y decide directamente el desvío máximo. No he comprobado si el M03 de producción trae ese campo. Aviso: con frontera real, el modelo redondea a mm cada par de átomos y la clave oficial redondea la suma (`round(sum/1000, 3)`). Pueden diferir en milésimas de km. No se ha validado con datos, porque E4 siempre sale constante.
5. **Límite.** En una autonómica (La Rioja, K=33, 193-315 unidades, unas 21.000 variables), E1 no cierra en 120 s: la cota es 0 y la mejor solución es la del ganador, con 1 fuera de tolerancia. Para llegar a autonómicas y provincias grandes hace falta descomponer o generar columnas (véase T-136).

## Plan de comparación con `redist` (SMC) y GerryChain puro (sin ejecutar)

1. **Instancia neutra.** `--exportar <dir>` escribe `<t>_<espacio>_instancia.json` (`ddd.t296-instancia/1.0`). Contiene:
   - los átomos, con unidades, población, claves R012, núcleo, partidos y comarcas;
   - las aristas;
   - K, los límites exactos, el máximo de mixtos y la huella de reglas.

   Los tres métodos parten de la misma instancia, así que tienen la misma atomicidad y las mismas reglas. Son unos 350 KB para los 9 territorios; no se versionan porque se regeneran con el script.
2. **GerryChain puro.**
   - Cadena ReCom sobre los átomos, con estas restricciones: población en [suelo, techo], contigüidad y `reglas.evaluar(...).valido` como restricción dura.
   - Sin el generador «ponderado» ni sus recargos; se elige con D8.
   - Las mismas 10 semillas públicas, y presupuestos de 10³, 10⁴ y 10⁵ pasos.
   - Métrica: la mejor clave D8 vista, el hueco al óptimo, el paso en que se alcanza y la tasa de autobucles.
3. **`redist` (SMC).**
   - En R 4.x y `redist` ≥ 4.2, en un entorno aparte (no entra en los locks): `redist_map` desde la instancia, con `pop_tol` de suelo y techo.
   - Las restricciones R012 y de núcleo van por átomos ya fusionados. La disciplina municipal se aproxima con `add_constr_splits(admin = municipio)`; los planes que no pasen `reglas.evaluar` se rechazan después.
   - Con N = 5.000 y 50.000 planes: fracción de planes válidos, mejor D8, percentil del ganador de Deslinde en la muestra y tiempo.
4. **Tabla común.** En los 8 territorios con óptimo demostrado, se mide para Deslinde, GerryChain puro, SMC y el exacto:
   - ¿alcanza el óptimo?
   - hueco por término;
   - tiempo y memoria.

   Burgos y Valladolid son los casos de prueba.
5. **Orden propuesto:** primero GerryChain puro (stdlib más gerrychain, ya en el lock del laboratorio) y después `redist`. Todo en local o en el runner propio (D-93), sin publicar código (D-92 y D-94).

## Reproducir

```
python3 -m venv /ruta/venv && /ruta/venv/bin/pip install -r requirements.lock -r requirements-banco-motor.lock
grep -iE '^(gerrychain|networkx|rustworkx|scipy|tqdm|six)==' requirements-ensemble.lock > /tmp/cad.txt
/ruta/venv/bin/pip install --no-deps -r /tmp/cad.txt
export PATH=/ruta/venv/bin:$PATH PYTHONHASHSEED=0
python herramientas/bateria_motor.py entradas --out /ruta/bateria --seccionado shapefile nac09   # ~15 s (más la descarga nacional la primera vez)
python -m ddd_motor2.competir --out /ruta/bateria nac09                                          # 30-60 s
python docs/ESTUDIOS/T296_OPTIMO_D8/optimo_d8.py --out /ruta/bateria --tiempo 120 --hilos 4 \
  --salida /ruta/resultados [--exportar /ruta/instancias] nac09
```

Con el OGC en vivo (`--seccionado ogc`), la adquisición agota el tiempo desde la nube; el shapefile nacional da la misma huella de contrato.
Con varios hilos, CP-SAT puede devolver otra partición empatada (La Rioja), pero el valor óptimo es el mismo. Con `--hilos 1` es determinista.
