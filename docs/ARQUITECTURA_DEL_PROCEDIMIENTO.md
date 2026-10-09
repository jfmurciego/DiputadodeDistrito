# Arquitectura del procedimiento DDD

**Versión documental:** 1.0.0  
**Fecha:** 2026-09-11  
**Nombre:** Separación formal por módulos

## Terminología oficial

El conjunto completo se denomina **Procedimiento de Distritación DDD**. Cada unidad funcional se denomina **módulo**. Cada lanzamiento completo o parcial se denomina **ejecución**. Cada conjunto de cambios de desarrollo se denomina **ronda**.

Se evita «pipeline» y se abandona «step» en la nomenclatura nueva.

## Por qué módulos separados

Un módulo existe solo cuando transforma un estado verificable A en otro estado verificable B. La separación no es estética: permite repetir únicamente el cálculo afectado, conservar resultados intermedios, aislar fallos, comparar versiones y evitar recalcular fuentes costosas. Dos transformaciones se mantienen separadas cuando una puede validarse, reutilizarse o versionarse independientemente de la siguiente.

## Módulos

### Módulo 1 — Base territorial y población
**Función:** extraer las secciones del ámbito, normalizar CUSEC y asociar población oficial.  
**Entrada:** seccionado oficial + fuente oficial de población.  
**Salida contractual:** una fila por sección, geometría, CUSEC canónico y población.  
**Por qué es imprescindible:** todo cálculo posterior presupone una unidad territorial y una población inequívocas. Un error aquí contamina todo el procedimiento.  
**Por qué está separado:** es la operación más pesada de ingestión y puede cachearse; no debe repetirse al cambiar el algoritmo de distritación.

### Módulo 2 — Adyacencias territoriales
**Función:** calcular qué secciones son vecinas según el criterio geométrico configurado.  
**Entrada:** salida del Módulo 1.  
**Salida contractual:** lista canónica de aristas CUSEC–CUSEC.  
**Por qué es imprescindible:** la contigüidad política debe apoyarse en relaciones territoriales explícitas, no en la apariencia del mapa.  
**Por qué está separado:** la adyacencia cambia solo si cambia la geometría o su criterio; puede reutilizarse en cientos de optimizaciones.

### Módulo 3 — Grafo territorial
**Función:** construir la representación computacional del territorio con nodos, población y aristas.  
**Entrada:** Módulos 1 y 2.  
**Salida contractual:** grafo territorial validado.  
**Por qué es imprescindible:** es la estructura sobre la que se comprueban conectividad, movimientos y restricciones.  
**Por qué está separado:** desacopla GIS de optimización y permite probar motores distintos sobre exactamente el mismo territorio.

### Módulo 4 — Solución inicial
**Función:** producir exactamente K distritos iniciales a partir del grafo.  
**Entrada:** Módulo 3 y parámetros de distritación.  
**Salida contractual:** asignación CUSEC→distrito inicial.  
**Por qué es imprescindible:** un optimizador necesita un estado inicial reproducible.  
**Por qué está separado:** permite comparar distintos métodos de inicialización sin alterar el optimizador.

### Módulo 5 — Optimización de distritos
**Función:** mejorar la asignación respetando las restricciones duras y los objetivos configurados.  
**Entrada:** solución inicial + grafo + parámetros.  
**Salida contractual:** asignación optimizada y métricas.  
**Por qué es imprescindible:** aquí se resuelve el problema de equilibrio territorial.  
**Por qué está separado:** es el módulo experimental; debe poder ejecutarse diez, cien o más veces sin volver a ingerir 100–300 MB de fuentes oficiales.

### Módulo 6 — Consolidación territorial
**Función:** convertir la asignación optimizada en productos finales de secciones, distritos y resumen estadístico.  
**Entrada:** Módulo 5.  
**Salida contractual:** GeoJSON de secciones, GeoJSON de distritos y resumen.  
**Por qué es imprescindible:** separa el estado interno del motor de los productos auditables.  
**Por qué está separado:** la presentación/exportación no debe modificar el algoritmo.

### Módulo 7 — Agregación electoral
**Función:** agregar resultados electorales de sección al distrito calculado.  
**Entrada:** Módulo 6 + resultados electorales.  
**Salida contractual:** resultados por partido/distrito y resumen electoral.  
**Por qué es imprescindible:** convierte la distritación territorial en una simulación electoral verificable.  
**Por qué está separado:** las elecciones cambian con mucha más frecuencia que la geometría; un nuevo escrutinio no debe recalcular distritos.

### Módulo 8 — Producto electoral territorial
**Función:** unir geometría distrital y resultados agregados en el artefacto final.  
**Entrada:** Módulos 6 y 7.  
**Salida contractual:** distritos con resultados electorales.  
**Por qué es imprescindible:** produce el objeto final consumible por GIS, mapas y análisis.  
**Por qué está separado:** mantiene trazabilidad entre cálculo territorial, cálculo electoral y producto publicado.

## Regla de orden

El orden 1→8 es una dependencia lógica, no una preferencia. Ningún módulo puede consumir información que todavía no ha sido normalizada o validada por su predecesor. Sin embargo, una ejecución puede comenzar en un módulo posterior cuando sus entradas contractuales ya existen, sus hashes coinciden y la versión del módulo productor es compatible.

## Reutilización y rendimiento

Las fuentes brutas se descargan/leen una vez y se identifican por SHA-256. Los productos costosos de M1–M3 se consideran **base preparada** y se cachean por combinación de: hash de inputs + versión de módulo + parámetros relevantes. Las rondas de optimización M4–M6 reutilizan esa base. En una sesión con diez ejecuciones del motor no se deben volver a descargar ni reprocesar los ficheros nacionales salvo que cambie su hash, la versión de M1–M3 o sus parámetros.

GitHub Actions usará cache persistente entre ejecuciones cuando sea seguro; dentro de una misma ejecución, los artefactos preparados se reutilizan directamente desde disco. No se mantiene un dataset de cientos de MB en RAM entre jobs: eso no es portable ni garantizable en runners efímeros. La optimización correcta es cachear el resultado preprocesado, no confiar en memoria residente.
