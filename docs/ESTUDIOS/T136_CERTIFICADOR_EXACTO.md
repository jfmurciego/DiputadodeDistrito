# T-136 — Prototipo de certificador exacto (CP-SAT)

Fecha: 2026-11-10 (enumeración añadida el mismo día). Herramienta: `herramientas/certificador_exacto.py` 1.0.0 (OR-Tools CP-SAT 9.15, `pip install ortools`).
Entradas: `herramientas/bateria_motor.py entradas` (T-132, rama `t132-bateria-motor`), M01 y M03 desde fuente con la
huella de población del contrato. Máquina: sesión cloud, 4 núcleos, 15 GB. Sin lanzar nada.

## Reglas

Las de `herramientas/validar_ejecucion.py` 1.3.5, con los límites de `ddd_core.config.hard_limits` y las exenciones de
`ddd_core.population_floor_exemptions`: K, una sección en un distrito, población en [suelo, techo] (suelo 0 si toca un
municipio exento), contigüidad en el grafo M03, provincia y reparto, disciplina municipal R012. Los municipios con
ceil(P/objetivo)=1 se contraen a un átomo por componente (exacto). Cada solución se vuelve a comprobar con
`evaluar_particion`, que reproduce esas reglas, y se compara con `datos/composicion/<t>.csv` (igual al motor 7.4.4 en la
matriz T-132 para los tres territorios).

Contigüidad: árbol con padre y nivel por átomo (tamaño O(E+n), independiente de K; por defecto). Se probaron también
flujo con raíz (O(K·E)) y cortes de separador perezosos: ambos más lentos y sin respuesta en los casos difíciles.

## Resultados

| Territorio | Secc. | Átomos | K | Pregunta | Resultado | Tiempo | Memoria |
|---|---|---|---|---|---|---|---|
| congreso_huesca | 286 | 202 | 2 | factibilidad | FACTIBLE (PASS) | 5,7 s | 0,6 GB |
| congreso_huesca | 286 | 202 | 2 | minimax, pista = publicado | ÓPTIMO: 113.439/113.439 (desv. 0; motor ±71) | 0,6 s | 0,3 GB |
| congreso_cadiz | 926 | 296 | 11 | techo 115 % (sin excepción) | **INFACTIBLE** (prueba CP-SAT) | 29 s | 0,5 GB |
| congreso_cadiz | 926 | 296 | 11 | techo mínimo, pista = publicado | **ÓPTIMO: 132.239 hab. = 1,15919×**; 11/11 distritos iguales al publicado | 41 s | — |
| congreso_cadiz | 926 | 296 | 11 | factibilidad 116 %, sin pista | DESCONOCIDO | 600 s | 1,3 GB |
| congreso_madrid | 4.479 | 3.603 | 59 | factibilidad (con y sin pista) | DESCONOCIDO | 120–300 s | 7,8–8,4 GB |

Escalado (bolas BFS desde Madrid capital 2807901001, reglas del contrato, K = round(P/objetivo), 120 s):

| Secciones | Átomos | K | Variables | Resultado | Memoria |
|---|---|---|---|---|---|
| 250 | 240 | 3 | 3.333 | FACTIBLE 45 s | 0,3 GB |
| 500 | 470 | 6 | 9.491 | DESCONOCIDO | 0,6 GB |
| 1.000 | 734 | 13 | 25.477 | DESCONOCIDO | 0,9 GB |
| 2.000 | 1.382 | 26 | 85.345 | DESCONOCIDO | 2,1 GB |
| 4.479 | 3.603 | 59 | 466.863 | DESCONOCIDO | 7,8 GB |

## Conclusiones

1. Cádiz: la excepción de techo 116 % era necesaria y es casi mínima. Con 115 % no hay partición válida (prueba en
   29 s); el menor techo posible es 132.239 hab. (1,15919× el objetivo), justo el distrito El Puerto de Santa María +
   Puerto Real, y la solución óptima coincide distrito a distrito con la publicada (motor 7.4.4). El motor no deja
   mejora en Cádiz.
2. Huesca: el motor queda a 71 hab. (0,06 %) del equilibrio perfecto, que existe; mejora sin valor práctico.
3. Tratabilidad: decide bien hasta ~300 átomos divisibles (secciones de municipios que se pueden partir) y K≈11. A
   partir de ~500 átomos divisibles no responde en minutos; Madrid (59 distritos, 2.450 secciones de la capital) queda
   fuera del modelo monolítico. La memoria crece ~lineal con átomos × K (8 GB en Madrid).
4. Las pruebas de infactibilidad dependen de la corrección del modelo: el modelo acepta la partición publicada de Cádiz
   (con 116 %), y las soluciones se comprueban aparte con las reglas de la validación. Las otras dos codificaciones de
   contigüidad no cerraron la de 115 % en 600 s (no la contradicen).

## Enumeración exacta (decisión del propietario: enumerar donde el espacio es pequeño)

`--objetivo enumerar`: cada plan hallado se excluye con una cláusula sobre la asignación (única por la ruptura de
simetría) y se repite hasta INFACTIBLE, que da el recuento exacto. `--unidades <M04>` aplica la atomicidad de
producción (`ddd_unit_id`, la misma unidad atómica que el ensemble).

| Territorio | Átomos | K | Resultado | Tiempo |
|---|---|---|---|---|
| congreso_alava (unidades M04) | 53 | 3 | **ENUMERADO: 1 plan válido**, igual 3/3 al publicado | 0,04 s |
| congreso_alava (secciones, sin unidades M04) | 216 | 3 | parcial: 6 planes en 120 s | 120 s |
| congreso_huesca (unidades M04) | 202 | 2 | parcial: 159 planes en 600 s (~3,8 s por plan), sin terminar | 600 s |

Álava: con las unidades de M04 (Vitoria en 3 unidades internas) solo existe un plan válido, el publicado; por eso la
cadena sale degenerada (unique_state_ratio y self_loop_rate fuera de umbral): no hay otro estado al que moverse. La
enumeración cabe con ~50 átomos; con ~200 (Huesca) ya no por este método (una resolución por plan). Para espacios
medianos haría falta un contador específico (diagramas de decisión por frontera) o muestreo.

## Siguiente paso posible (sin hacer)

Descomposición exacta para provincias grandes: la disciplina municipal obliga a que Madrid capital ocupe 25–29 distritos
con un solo mixto, así que ≥24 distritos son subproblemas de la capital; resolver capital y resto por separado con la
frontera del distrito mixto como variable. Y pista completa (padre/nivel) desde el motor para validar a escala.

## Reproducir

```
python herramientas/bateria_motor.py nacionales && python herramientas/bateria_motor.py entradas congreso_cadiz
E=bateria/entradas/congreso_cadiz
python herramientas/certificador_exacto.py --params territorios/congreso_cadiz/config/congreso_cadiz_2025.yaml \
  --grafo $E/congreso_cadiz_2025_m03_grafo.json --secciones $E/congreso_cadiz_2025_m01_secciones_poblacion.geojson.zip \
  --objetivo factibilidad --techo-ratio 1.15 --tiempo 900          # INFACTIBLE
python herramientas/certificador_exacto.py ... --objetivo techo --pista datos/composicion/congreso_cadiz.csv \
  --referencia publicado=datos/composicion/congreso_cadiz.csv       # ÓPTIMO 132239
```

## 1.1.0 (2026-11-10): núcleo de reglas y fallos F1/F2

T-132 detectó dos fallos de la 1.0.0 al usarla como semilla:
- **F1 (Canarias):** daba INFACTIBLE en 2 s, aunque el canónico 7.4.4 pasa la validación. Tomaba la provincia y el
  municipio del M01, que no trae `DDD_PARTITION` ni `DDD_MUNICIPALITY_PARTITION`, y no aplicaba la exención por partición.
- **F2 (Cádiz):** partía unidades M04. Agrupaba las unidades dentro de cada municipio, y una unidad puede abarcar varios.

En la 1.1.0, las reglas, los límites exactos y el veredicto salen del núcleo `ddd_motor2.reglas`. Las secciones se leen del
M04, con los campos del contrato. Las unidades M04 se unen con unión-búsqueda. Perfiles: `nucleo` (Criterio D-44) y
`produccion` (compatibilidad con `validar_ejecucion` 1.3.5).

| Caso (secciones del M04 de la batería, motor 7.4.4) | Átomos | Resultado | Tiempo |
|---|---|---|---|
| canarias, K=70, ambos perfiles | 117 | FACTIBLE; el canónico da PASS | 1,5 s |
| congreso_cadiz, factibilidad | 46 | FACTIBLE, sin unidades partidas | 0,3 s |
| congreso_cadiz, techo mínimo | 46 | ÓPTIMO 132.239 (1,15919×), igual que en la 1.0.0 | 0,4 s |
| congreso_cadiz, techo 115 % | 46 | INFACTIBLE | 0,4 s |
| congreso_cadiz, techo mínimo sin unidades | 296 | ÓPTIMO 132.239 | 63 s |
| congreso_cadiz, enumerar | 46 | parcial: 264 planes en 120 s | 120 s |
| congreso_alava, enumerar | 53 | ENUMERADO: 1 plan | 0,06 s |

Las conclusiones de Cádiz y Álava no cambian. Con las unidades M04, que son la atomicidad de producción, el problema
queda en decenas de átomos y se resuelve en menos de un segundo. Los resultados de Huesca y Madrid de la 1.0.0 se
hicieron sin unidades M04 y con secciones del M01.

Límite conocido de la 1.1.0: R-NUCLEO (núcleos urbanos cerrados) no se aplica, porque el M04 no rellena
`Unidad.nucleo_cerrado`. Ese dato sale de un adaptador que T-160 deja para F2/F3: distritos de la semilla formados solo
por unidades `ddd_closed_urban`.

## 1.2.0 (2026-11-10, T-164, D-48): modelo ligero con cotas

`--modelo ligero` combina dos modelos que escalan, y el completo si es pequeño:
- **Cota inferior: relajación fluida.** Sin contigüidad y por clave R012. Una clave indivisible es un objeto entero.
  Una clave divisible reparte su población en enteros entre lo..hi distritos. Refuerzos válidos: hi ≤ sus grupos
  indivisibles, y cada trozo lleva al menos su menor pieza. Conserva K, cuotas, suelo, techo, tolerancia, mixtos y
  exenciones (permisivas). Todo plan válido proyecta en una solución, así que su cota vale y su infactibilidad prueba
  que no hay plan. Comprobado: el plan publicado, impuesto (`fijar_pista`), es solución en los cuatro territorios y da
  su propio valor. La cota de CP-SAT vale aunque no termine.
- **Cota superior: superátomos.** Junta átomos contiguos de un mismo distrito de la pista hasta grano × objetivo
  (0,25 por defecto). Cada plan es válido (se juzga con el núcleo) y la pista sigue siendo factible.
- **Exacto** si hay ≤ 400 átomos (`--umbral-exacto`): su plan y su cota entran en la combinación.
- Resultado: `OPTIMO_CERTIFICADO` si las cotas coinciden; si no, `COTA` con el hueco.

Átomos = unidades M04 (secciones del M04 de la batería, motor 7.4.4, perfil núcleo; pista = publicado). Tiempo límite:
120 s (300 s en Madrid). 4 núcleos.

| Territorio | K | Átomos (superátomos) | Pregunta | Resultado | Tiempo inf. / sup. | Total |
|---|---|---|---|---|---|---|
| congreso_alava | 3 | 53 (10) | minimax | ÓPTIMO certificado: 16.748 = publicado | 0,03 / 0,01 s | 1,2 s |
| congreso_alava | 3 | 53 (10) | techo | ÓPTIMO certificado: 127.496 = publicado | 0,02 / 0,01 s | 1,2 s |
| congreso_huesca | 2 | 202 (19) | minimax | ÓPTIMO certificado: 0 (publicado 71) | 0,03 / 0,03 s | 2,1 s |
| congreso_huesca | 2 | 202 (19) | techo | ÓPTIMO certificado: 113.439 (publicado 113.510) | 0,03 / 0,03 s | 2,1 s |
| congreso_cadiz | 11 | 46 (29) | minimax | ÓPTIMO certificado: 20.007 = publicado | 0,09 / 0,15 s | 1,5 s |
| congreso_cadiz | 11 | 46 (29) | techo | ÓPTIMO certificado: 132.239 = publicado | 0,09 / 0,14 s | 1,8 s |
| congreso_madrid | 59 | 214 (105) | factibilidad | FACTIBLE (plan del modelo restringido, PASS) | 4,0 / 9,7 s | 166 s |
| congreso_madrid | 59 | 214 (105) | minimax | **ÓPTIMO certificado: 17.236 = publicado** | 18,5 / 16,6 s | 187 s |
| congreso_madrid | 59 | 214 (105) | techo | **COTA: [133.447, 133.450], hueco 3 hab.** (publicado 133.450) | 3,5 / 8,5 s | 164 s |

Solo las cotas, sin el exacto, tardan 10-35 s en Madrid. El resto del total es el modelo completo, que llega al tope
sin terminar (150 s). Memoria máxima: 0,6 GB en Madrid (antes, 8 GB).

Conclusiones:
1. Madrid entra en el certificador. Con las unidades M04 tiene 214 átomos, no 3.603: los 3.603 eran secciones del M01
   sin unidades M04 (1.0.0). Aun así, el modelo completo de 214 átomos y K=59 no termina en 150 s (cota 5.086). El ligero
   prueba que el publicado es minimax-óptimo: ningún plan válido tiene una desviación máxima menor de 17.236 hab. En el
   techo, el publicado queda a 3 hab. del mínimo posible.
2. La relajación sola es débil cuando la contigüidad aprieta (Álava: cota 1 frente a 16.748; Cádiz: 9.865 frente a
   20.007). Ahí cierra el hueco el exacto, que cabe. En Madrid manda la disciplina municipal y la relajación es
   ajustada.
3. Una INFACTIBILIDAD del modelo restringido (`INFACTIBLE_RESTRINGIDO`) no prueba nada. Solo la relajación o el exacto
   prueban infactibilidad.

Reproducir (tras `bateria_motor.py entradas` y `motor`; el M04 queda en `territorios/<t>/.cache/ddd/preparacion/`):
```
python herramientas/certificador_exacto.py --params territorios/congreso_madrid/config/congreso_madrid_2025.yaml \
  --grafo bateria/entradas/congreso_madrid/congreso_madrid_2025_m03_grafo.json \
  --secciones territorios/congreso_madrid/.cache/ddd/preparacion/congreso_madrid_2025/congreso_madrid_2025_m04_semillas.geojson.zip \
  --objetivo minimax --modelo ligero --pista datos/composicion/congreso_madrid.csv --tiempo 300
```

## 1.3.0 (2026-11-10, T-175): R-NUCLEO aplicada

El certificador ya aplica R-NUCLEO. `leer_secciones` toma `district_id` y `ddd_closed_urban` de las secciones del M04. El
adaptador nuevo `ddd_motor2.adaptadores.nucleos_desde_unidades` trabaja sobre las unidades de partición: una unidad M04
es cerrada si lo son todas sus secciones, y un distrito de referencia formado solo por unidades cerradas es un núcleo.
Es la regla del M05 GerryChain, que congela esos distritos. El adaptador desde la composición usa la misma función.
En el modelo, el núcleo es un solo grupo de átomos y su distrito no admite átomos de fuera. Los superátomos no mezclan
núcleo y resto. La relajación fluida no lo usa y sigue siendo una cota válida. `--sin-nucleos` quita la regla, para
comparar. Si la entrada no trae las columnas (un M01, por ejemplo), no hay núcleos y la salida lo avisa.

Medición: minimax, `--modelo ligero`, pista = publicado, 120 s, 4 núcleos, secciones del M04 de la batería (motor 7.4.4).

| Territorio | K | Átomos | Núcleos | Con R-NUCLEO | Sin R-NUCLEO | Publicado |
|---|---|---|---|---|---|---|
| congreso_alava | 3 | 53 | 1 | ÓPTIMO certificado 16.748 (0,9 s) | igual (0,9 s) | 16.748, PASS |
| congreso_albacete | 3 | 88 | 1 | ÓPTIMO certificado 530 (0,8 s) | igual (0,9 s) | 530, PASS |
| congreso_burgos | 3 | 372 | 1 | **ÓPTIMO certificado 9** (exacto, 7,1 s) | COTA [9, 11] (61 s) | 11, PASS |
| congreso_huesca | 2 | 202 | 0 | ÓPTIMO certificado 0 | igual | 71, PASS |

El publicado cumple R-NUCLEO en los cuatro. En Burgos la regla poda el espacio de búsqueda: el modelo completo termina en
7 s y certifica que el óptimo es 9 hab. (el publicado queda a 2 hab.). Sin la regla, en 120 s solo da la cota.

Reproducir: `herramientas/bateria_motor.py entradas <t>` y `motor <t>`; después
`python herramientas/certificador_exacto.py --params territorios/<t>/config/<t>_2025.yaml --grafo bateria/entradas/<t>/<t>_2025_m03_grafo.json --secciones territorios/<t>/.cache/ddd/preparacion/<t>_2025/<t>_2025_m04_semillas.geojson.zip --objetivo minimax --modelo ligero --pista datos/composicion/<t>.csv --referencia publicado=datos/composicion/<t>.csv --tiempo 120 [--sin-nucleos]`.
