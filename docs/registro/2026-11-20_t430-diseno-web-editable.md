## 2026-11-20 — T-430 — Diseño de la web editable en minutos (solo documento)

- **Causa:** el propietario quiere editar los textos de la web en minutos; hoy una coma exige PR con 15-20 min de CI y una P40.
- **Cambio:** `docs/ESTUDIOS/T430_WEB_EDITABLE/DISENO.md` 1.1.0 (nuevo; aprobado D-186, 20-11: índice «actual» por mapa y dato, V3 congelada): repositorio `ddd-web` solo para la web en Cloudflare Pages (publicación por commit y vista previa por rama); datos en un bucket R2 público `datos.diputadodedistrito.es` con prefijos inmutables por P40 y `actual.json` con sha256; reparto de ficheros y traslado con `git filter-repo`; Explorar (rutas, CORS, caché); V3 congelada; P40 nuevo; pruebas en la construcción de Pages; pasos del propietario en Cloudflare y GoDaddy; corte sin caída y vuelta atrás; Zenodo; riesgos y 11 preguntas con recomendación.
- **Pruebas:** no aplica (solo documento); guardián y cabeceras de gobernanza en local.
- **Riesgos:** ninguno en producción: no crea repositorios ni toca Cloudflare, GoDaddy, workflows ni código.
