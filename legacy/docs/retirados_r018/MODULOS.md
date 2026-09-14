# Catálogo de módulos

**Versión:** 1.0.0 — 2026-09-11

## Módulo 01 — Preparar base territorial
**Fichero:** `modulos/01_preparar_base_territorial.py`  
Integra cartografía y población oficial. Es imprescindible que sea primero porque establece el identificador canónico, la geometría y la población de cada sección. Se separa por ser estable, costoso y cacheable.

## Módulo 02 — Construir adyacencias
**Fichero:** `modulos/02_construir_adyacencias.py`  
Calcula vecindad entre secciones. Solo puede ejecutarse después del 01 porque necesita la geometría preparada. No se mezcla con el grafo para poder auditar la regla espacial de contacto y reutilizarla.

## Módulo 03 — Construir grafo territorial
**Fichero:** `modulos/03_construir_grafo.py`  
Combina nodos, población y aristas. Debe preceder a cualquier distritación porque la contigüidad se define y valida sobre este grafo. Se separa para desacoplar GIS de optimización.

## Módulo 04 — Generar distritos iniciales
**Fichero:** `modulos/04_generar_semillas.py`  
Crea una solución inicial de K distritos. No se integra con el optimizador porque interesa comparar distintas estrategias de inicialización sobre el mismo grafo.

## Módulo 05 — Optimizar distritos
**Fichero:** `modulos/05_optimizar_distritos.py`  
Es el núcleo experimental. Modifica la asignación intentando mejorar población y demás criterios sin romper contigüidad. Se mantiene aislado para poder ejecutarlo repetidamente sin reconstruir los módulos 01-03.

## Módulo 06 — Consolidar distritos
**Fichero:** `modulos/06_consolidar_distritos.py`  
Convierte la asignación algorítmica en producto territorial: resúmenes y geometrías finales. Debe ser posterior al optimizador y anterior a elecciones para validar el territorio sin contaminación analítica.

## Módulo 07 — Agregar resultados electorales
**Fichero:** `modulos/07_agregar_resultados_electorales.py`  
Agrega votos de sección a distrito. Está separado porque una elección concreta no puede condicionar la construcción del distrito.

## Módulo 08 — Integrar resultados en el mapa final
**Fichero:** `modulos/08_integrar_resultados.py`  
Une geometría final y resultados agregados. Es el último módulo porque depende de dos productos ya concluidos: el territorio del 06 y los resultados del 07.

## Regla de indivisibilidad

Dos operaciones solo pueden compartir módulo si tienen exactamente la misma cadencia de cambio, las mismas entradas y la misma condición de éxito. Si una puede reutilizarse mientras la otra cambia, deben permanecer separadas. Esta regla impide que una modificación local obligue a repetir cálculos caros o dificulte localizar una regresión.
