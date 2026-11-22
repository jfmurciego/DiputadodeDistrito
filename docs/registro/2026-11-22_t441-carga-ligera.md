## 2026-11-22 — T-441 — Diseño de la carga ligera para el móvil (solo documento)

- **Causa:** el propietario (22-11, vía Planificador) quiere que la web abra rápido en el móvil y para quien solo echa un vistazo.
- **Cambio:** `docs/ESTUDIOS/T441_CARGA_LIGERA/DISENO.md` 1.0.0 (nuevo): inventario de lo que se descarga hoy al abrir la portada (≈ 234 KB comprimidos, 89 % imágenes) y el mapa (≈ 470 KB comprimidos conocidos, más de la mitad la librería del mapa, más cinco ficheros por medir con T-440); propuesta de primera vista ligera (fotos a la medida, carga diferida, vídeo al pulsar, vista rápida del mapa sin la librería, datos a demanda, geometría simplificada), compresión y caché; ahorro estimado (≥ 75 %); encaje con ddd-web y R2 (D-186, D-188); riesgos y 6 preguntas con recomendación, respondidas «sí a todo» por el propietario (D-192, 22-11).
- **Pruebas:** no aplica (solo documento). Pesos medidos sobre los ficheros de `main`; los tiempos reales y los ficheros generados se añaden con el run de T-440 (#970).
- **Riesgos:** ninguno: no toca código, workflows ni la web publicada.
