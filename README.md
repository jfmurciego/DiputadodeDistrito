# Diputado de Distrito

Repositorio de referencia para el pipeline reproducible de distritación DDD.

## Principio operativo

GitHub es el entorno de referencia: una versión solo se considera válida si el mismo commit puede ejecutarse de extremo a extremo en GitHub Actions y superar las validaciones duras.

## Pipeline Aragón

El baseline recuperado ejecuta Steps 1→8:

1. Construcción de secciones + población
2. Extracción de adyacencias
3. Construcción del grafo
4. Semillado de distritos
5. Optimización por swaps
6. Exportación final
7. Agregación de resultados electorales
8. Unión de resultados a distritos

La infraestructura de reproducibilidad (contenedor, dependencias fijadas, manifiestos, checksums y validaciones) se mantiene separada de las modificaciones algorítmicas.

## Ejecución

La ejecución normal se realizará desde **Actions → DDD Aragón Pipeline → Run workflow**.

Los resultados, logs, informes y manifiestos de cada ejecución se publicarán como artifacts del workflow.
