# T-136 — Prototipo de certificador exacto (CP-SAT)

Fecha: 2026-11-10. Herramienta: `herramientas/certificador_exacto.py` 1.0.0 (OR-Tools CP-SAT 9.15, `pip install ortools`).
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
