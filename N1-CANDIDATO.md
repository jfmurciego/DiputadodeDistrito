# N1 candidato adicional — versión 1.0.1 — 2026-10-10

Anterior: legacy/N1-CANDIDATO_v1.0.0.md. Cambios: portabilidad de procedencia C3 y redacción de localizadores privados.

Base exacta: commit 35101a13afc20417606971db569caee9b7be8dd9; árbol
8e04187c618eb6dceda1069ae791b2dc9774b35c; ZIP recibido SHA-256
785b0c0909ec4932993d91259b630a09531c85e01ad1f035848b9356298194c6.
Original 7307536ae720b2d68321d7d5e35ab8206c5cc568 intacto.

Delta mínimo: C2 exige atributos y geometrías presentes; negativos completos
por atributo nulo/ausente/vacío y geometría ausente; error de geometría controlado.
C1 verifica además seis indicadores derivados por alternativa (30 mutaciones).
C3 verifica modelo y fuente poblacional antes de parsearlos. Cuotas, reglas,
tolerancias y fixture cartográfico corregido del expediente previo conservados.
Predecesores guardados en legacy; incremento PATCH; CI pendiente y prohibida.

Pruebas macOS: 5 C1/C2 + 22 cartográficas/portabilidad + 8 alternativas + 3
integridad = 38 métodos PASS. Receta completa PASS en salida nueva.
Python 3.11.4; pyproj 3.7.2 / PROJ 9.7.1; shapely 2.1.1 / GEOS 3.13.1.
El fallo 99.9910806 del fixture anterior dependía de PROJ 9.3.0 frente a 9.7.1;
la prueba geográfica→métrica acreditada conserva precisión y tolerancia previas.

NO_GO formal hasta revisión independiente y Linux nativo: no hay runtime Linux
local ni destino remoto autorizado identificado. Prueba de stat sin st_flags es
regresión funcional, no prueba Linux. Procedimiento offline acompaña el paquete.
392/391, geometría inválida 44 de Baleares y decisión institucional K abiertas.
Histórico 27/27 separado: atribución pendiente. Sin integración ni producción.

C3 sin datos de ubicación privada: las rutas de restauración y el `busqueda.json` son relativas al expediente; los localizadores históricos personales se reducen a identificadores/nombres de archivo y quedan rotulados como redactados. Los hashes y rutas dentro del paquete mantienen la procedencia verificable. La receta limpia además inspecciona sus JSON y falla si reaparecen rutas personales absolutas o directorios temporales privados.
