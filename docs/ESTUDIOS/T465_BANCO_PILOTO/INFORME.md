# T-466 · Piloto del banco: Deslinde frente a GerryChain puro y el óptimo exacto

Fecha: 2026-11-26. Diseño y regla de decisión: `DISENO.md` (commit 6dd94600, escrito antes de los resultados de
GerryChain). Código de `main` 2f696caf. Sesión cloud, 4 núcleos y 15 GB. No se ha lanzado nada ni se ha publicado nada.

## Resultado

Clave D8 término a término: fuera de tolerancia, exceso sobre el 8 %, demarcaciones partidas (partidos judiciales más
comarcas agrarias), frontera cortada (km) y desvío máximo. «Fuera» vale 0 en todos los planes y el exceso es igual en los
tres métodos, así que la tabla empieza por las demarcaciones partidas.

| Territorio | K | Átomos | Óptimo (exacto) | Deslinde | GerryChain puro, mejor de 10 semillas a 10⁵ pasos |
|---|---|---|---|---|---|
| Burgos (nac09) | 3 | 372 | 2 · 315,8 km · 7,84 % | **= óptimo** (vigente) | 4 · 267,7 km — peor |
| Valladolid (nac47) | 4 | 226 | 2 · 270,5 km · 14,00 % | **= óptimo** (vigente) | 2 · 307,9 km — peor en frontera |
| La Rioja (nac26) | 3 | 175 | 2 · 88,9 km · 7,36 % | **= óptimo** (vigente) | **= óptimo** (10 de 10 semillas) |
| Sevilla (nac41) | 16 | 111 | **6** · 786,0 km · 13,50 % | 8 · 763,8 km — **peor** | 8 · 861,4 km — peor que Deslinde |

- **El exacto demuestra el óptimo D8 completo en los cuatro**, en 3 a 60 s y con menos de 370 MB. El plan óptimo pasa
  `evaluar(...).valido` en los cuatro.
- **Deslinde iguala el óptimo en Burgos, Valladolid y La Rioja** (la misma partición). En Burgos y Valladolid ya no está
  el hueco de T-296 (14-11).
- **Hallazgo de Deslinde: en Sevilla pierde.** Parte 8 demarcaciones y el óptimo demostrado parte 6. El plan óptimo está en
  `resultados/exacto/nac41_canonico_mejor_modelo.csv`. Las cadenas de la competición no lo encuentran.
- **GerryChain puro no gana a Deslinde en ningún caso.** Ninguna de las 40 cadenas encuentra un plan mejor:
  - solo iguala el óptimo en La Rioja, el caso más pequeño (todas las semillas a 10⁴ pasos, 3 de 10 a 10³);
  - en Burgos se queda en 4 demarcaciones partidas, frente a 2;
  - en Valladolid llega a 2 demarcaciones en 2 de 10 semillas, pero con 37 km más de frontera;
  - en Sevilla llega a 8 demarcaciones en 1 semilla, con 98 km más de frontera que Deslinde.
  
  Más pasos ayudan poco: de 10⁴ a 10⁵ pasos bajan las demarcaciones partidas solo en Valladolid y Sevilla
  (en Burgos baja solo la frontera).
- Lo que cuesta a GerryChain puro es arrancar. La primera semilla por árboles válida en el núcleo (por R-NUCLEO y
  R-MUN-MIXTOS) tarda de 1 a 31 intentos. Después, cada estado nuevo se juzga con `evaluar` y con la clave D8 oficial.

Madrid (nac28 y aut13) no entra en el piloto. `bateria_motor.py entradas` da FALLO_ADQUISICION en la nube, el fallo
conocido de la adquisición de Madrid. Por orden del Planificador, pasa al banco completo y, si hace falta, a un runner.

## Coste en CPU (tiempo de usuario)

| Paso | CPU | Reloj |
|---|---|---|
| Entradas (4 territorios, más 2 intentos de Madrid) | 1,9 min | 1,9 min |
| Deslinde: competición local | 6,7 min | 3,5 min |
| Exacto (CP-SAT, 4 hilos) | 5,8 min | 1,7 min |
| GerryChain puro (40 cadenas de 10⁵ pasos) | **6,9 h** | 1,7 h (4 en paralelo) |
| Tanda de 10⁴ abortada al subir a 10⁵ | unos 7 min | 2 min |
| **Total** | **unas 7,2 h** | **unas 1,9 h** |

Por cadena de 10⁵ pasos: Burgos 18 min, Valladolid 14 min, La Rioja 6,7 min y Sevilla 2,6 min. Frente a GerryChain
puro, el exacto cuesta unas 70 veces menos y Deslinde unas 60 veces menos.

## Decisión: seguir con el banco completo, con alcance acotado

Se cumple la condición «seguir» de `DISENO.md`: en Sevilla el exacto encuentra un plan válido estrictamente mejor que
el ganador de Deslinde. Pero el piloto cambia lo que conviene medir:

1. **El exacto es la referencia útil, y GerryChain puro no lo es.** Con K = 16 y 111 átomos, el exacto cierra en
   60 s. GerryChain puro es peor que Deslinde en los cuatro territorios y cuesta unas 60 veces más. En el banco completo
   propongo GerryChain puro solo a 10⁴ pasos y con 10 semillas, como referencia externa (unas 0,7 h de CPU por
   territorio pequeño), no a 10⁵.
2. **Lo que falta saber es hasta dónde llega el exacto.** Es el siguiente paso barato: el exacto en las 28 provincias
   restantes y en las autonómicas pequeñas. Con eso se sabe dónde hay óptimo demostrado y dónde solo cota (bloque C,
   T-468). En La Rioja autonómica, T-296 ya vio que E1 no cierra en 120 s.
3. **Sevilla abre su propia tarea** (regla de T-466): el exacto debe entrar como candidato en la competición, o la
   búsqueda de Deslinde no debe perder demarcaciones con K grande. Este piloto no decide cuál de las dos.
4. **`redist` y los casos de fuera** quedan como estaban en el plan. Su valor es que otros puedan compararse con
   nosotros, no saber si Deslinde es bueno.

## Reproducir

```
python3.12 -m venv V && V/bin/pip install -r requirements.lock -r requirements-banco-motor.lock
grep -iE '^(gerrychain|networkx|rustworkx|scipy|tqdm|six)==' requirements-ensemble.lock > cad.txt
V/bin/pip install --no-deps -r cad.txt
export PATH=$PWD/V/bin:$PATH PYTHONHASHSEED=0 DDD_ESPEJO_DIR=<carpeta con seccionado_2023.zip y seccionado_2024.zip del INE>
python herramientas/bateria_motor.py entradas --desde-fuente --seccionado shapefile --out B nac09 nac47 nac26 nac41
python -m ddd_motor2.competir --out B nac09        # uno por territorio
python docs/ESTUDIOS/T296_OPTIMO_D8/optimo_d8.py --out B --tiempo 120 --hilos 4 --salida EX --exportar INST nac09
python docs/ESTUDIOS/T465_BANCO_PILOTO/gerrychain_puro.py --out B --semillas 1 --pasos 100000 --salida GC nac09
python docs/ESTUDIOS/T465_BANCO_PILOTO/tabla.py --exacto EX --gc GC --salida resultados/RESUMEN.json
```

El sha256 de los seccionados 2023 y 2024 bajados de ine.es coincide con `orchestracion/fuentes_r2.json`
(7a15e700… y df931fa0…). Las huellas de las entradas están en `resultados/ENTRADAS.sha256`.
