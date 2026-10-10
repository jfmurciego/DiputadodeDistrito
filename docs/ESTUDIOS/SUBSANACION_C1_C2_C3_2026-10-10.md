# Subsanación material C1–C3

Versión: 1.0.0. Fecha: 2026-10-10. Estado: revisión independiente pendiente.
Alcance: copia aislada del expediente obligatorio, árbol base 4248ad13a85e59697c24c3d5be0130e11425076f.
Origen: documento nuevo. Motivo: REVIEW_NO_GO por plataforma y reproducibilidad.

La protección de placeholders BSD/macOS se conserva mediante getattr(stat, 'st_flags', 0). En plataformas que no exponen ese atributo, los errores de stat y lectura siguen propagándose. La regresión ejecuta la incorporación completa con un objeto stat sin st_flags y comprueba por separado el rechazo del flag 0x40000000 y la entrada física ausente.

El fixture cartográfico anterior hacía una inversa LAEA y después otra proyección. Con el mismo GEOS 3.13.1, PROJ 9.3.0 produce 99.99108057362844 m² y PROJ 9.7.1 produce 99.9999999976717 m². El desplazamiento máximo de vértice es 0.0007638785 m en PROJ 9.3.0. La diferencia es de la inversa de proyección, no una pérdida de área introducida por el comparador. Esto acredita dependencia de PROJ; no conocemos las versiones exactas del entorno independiente y no atribuimos a éste una versión concreta.

El nuevo fixture empieza en coordenadas geográficas y construye la geometría métrica por proyección directa. Su control numérico es 94.2676535457 m²: PROJ 9.3.0 y 9.7.1 coinciden a las tres cifras decimales exigidas. Se conserva places=3 y area_epsilon_m2=0.01; no se modifica el comparador. Las pruebas analíticas de rectángulos siguen exigiendo áreas 50 y 100 m². La mejora de cálculos authálicos upstream está documentada en https://github.com/OSGeo/PROJ/pull/4446; la atribución concreta se apoya en los probes locales, no en inferir el entorno del revisor.

C1 y C2 se conservan. La herramienta de evaluación y el cuerpo de historical_material_verdict no se cambian. Predecesores conservados en legacy/ con sufijo de versión; no se sobrescribe la evidencia anterior.

La receta acepta exclusivamente inputs conservados en el código completo. Para pyproj con datos empaquetados se usa su proj.db; para compilación desde fuente debe suministrarse --proj-data explícitamente. La red PROJ se desactiva y software.json conserva versiones y hash de la base de datos. El expediente incluye ruedas Linux CPython 3.11 x86_64 para las cuatro dependencias fijadas; requieren glibc >= 2.28. No se presenta la prueba con stat simulado como ejecución Linux nativa.

Desde la raíz del expediente, reproducir_expediente.py extrae el código en un destino nuevo, acredita todos los blobs/modos y el árbol Git, ejecuta las cuatro familias de regresiones y la receta limpia. Para Linux: crear un venv, instalar sin red con --no-index --find-links wheelhouse-linux -r requirements-cartografia-nacional.lock (copia idéntica del lock de código) y llamar al script con ese Python. Para una compilación nativa sin proj_dir se añade --proj-data software/proj-data. No se necesita cartografía externa ni las rutas históricas del inventario; estas son sólo procedencia.

Las incidencias 392/391, geometría 44 de Islas Baleares y decisión institucional sobre K permanecen abiertas. Histórico 27/27: atribución pendiente, separado de las pruebas nuevas. CI y revisión independiente pendientes. No se autoriza integración. Repositorios productivos intactos; PR, workflows, generación de distritos, publicación y fusión: NO.
