# N08 — diagnóstico topológico nacional ejecutado
Versión 1.0.0; nombre: base física Congreso; fecha 2026-10-12; alcance diagnóstico 52/52; estado N08 BLOCKED; origen nuevo. La ruta 20251012 conserva el nombre pedido por Work; no altera la fecha real.

Base: b583c52128daa85c14de9def0c9a3cb7d5f5e92e. Fuentes #239/#241/#242 reutilizadas, sin descarga ni modificación. Mónada 120.000, K=407 y 52 cuotas intactas. generation_authorized=false.

Cobertura demostrada: 36.554 CUSEC únicos, 49.128.297 habitantes, 52 unidades administrativas. Grafo original: 99,597 aristas de frontera lineal positiva con área de solapamiento cero; cero aristas interprovinciales, autorreferenciales o duplicadas. Las relaciones son no dirigidas y sus componentes se reconstruyen determinísticamente. Se excluyen 2749 contactos entre provincias.

Se distinguen 77 componentes del grafo seccional de 397 componentes de partes poligonales. 115 secciones abarcan partes en componentes distintos: el nodo seccional no acredita paso físico. Las poblaciones de los componentes seccionales concilian exactamente. En componentes de partes que comparten sección, se registra población exacta NOT_EVIDENCED, población conocida y CUSEC afectados; no se reparte por superficie.

Anomalías: 498 pares de solapamiento intraprovincial, 7 interprovinciales, 5750 contactos exclusivamente puntuales, 11 secciones aisladas y 538 municipios discontinuos por grafo inducido de secciones o partes. Los pequeños solapamientos no se admiten automáticamente como ruido tolerable. Vacíos encerrados se miden sobre la unión original; pueden incluir agua, enclaves o déficits. Falta frontera independiente para clasificar huecos externos y cobertura de dominio: NOT_EVIDENCED, no ausencia de defectos.

Los productos comprimidos ocupan 9,041,155 bytes, sin coordenadas duplicadas ni fuentes originales. Cada nodo conserva todos los atributos originales, POB_2025, hash WKB y hash del ZIP; cada arista conserva longitud, área cero y hash WKB del contacto. Los conjuntos de partes y municipios se incluyen en los 52 paquetes. Manifiesto: producto/manifest.json, identidad 59e4273f49a60d0d6f522389d0cb0c43738d68faed7053381d9bbde212d266f8.

La preparación diagnóstica A tiene cobertura PASS, integridad topológica BLOCKED y cierre externo NOT_EVIDENCED. B, factibilidad de Cantabria, BLOCKED por componentes, población interna no desagregada y decisiones pendientes. C, autorización productiva, BLOCKED. No se declara READY, no se genera ningún distrito ni se ejecuta 00/M04–M06 real. La reproducción y el dictamen independiente se conservan con hashes y logs al cierre.

Siguiente acción técnica: resolver nominalmente el enclave de Valle de Villaverde y las tres secciones multipartes de Cantabria, contrastar sus componentes con evidencia administrativa/poblacional y una frontera independiente ya acreditable, y decidir una política explícita de contigüidad/excepciones. Después aprobar unidad mínima, disciplina municipal y límites; implementar el gate nacional final M04–M06 que exija simultáneamente K, conectividad y límites. Las pruebas sintéticas actuales no autorizan el piloto.
