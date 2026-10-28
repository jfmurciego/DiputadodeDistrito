# Diagnóstico de alternativas congeladas

Versión1.0.0, 2026-10-10. Estado: candidato de diagnóstico aislado; ninguna modificación del visor productivo. Origen: mecanismos de capas/alternativas GeoJSON/tablas ya acreditados en `docs/AUDITORIAS/NACHO_2026-10-10/INFORME.md:204–206`. No se reexamina Nacho ni se copia su código.

## Problema demostrado

`ddd_ensemble/gallery.py` ya permite mapas A/B, filtro por perfil/Pareto y selección con responsable/justificación. Su `app.js` muestra seis métricas agregadas. En los candidatos congelados no muestra población por distrito, floor/cap/banda dura, municipios divididos, causas de rechazo C o explicación de la dominancia técnica. El ensamblador conserva sólo candidatos válidos para selección y únicamente IDs en `invalid_candidates`; la galería no muestra estos IDs/causas. La selección exportada contiene territorio/bundle/candidato/responsable/justificación/status, sin hashes visibles de la configuración/asignación.

## Requisitos del candidato de diagnóstico

1. Comparación A/B sobre exactamente el mismo universo de16 secciones y las mismas geometrías locales. No generar particiones ni cambiar score/ranking.
2. Tabla por alternativa/distrito: población, target1000, floor800, cap1750, banda dura800–1200, desviación, outlier, municipios divididos y fallos. La banda de tolerancia y el cap genérico son puertas diferentes; mostrar ambos.
3. Explicación objetiva: A máximo15% y L1300, B máximo10% y L1400; PP/comarca/corredor/assignment_delta del report idénticos. B domina A en los objetivos del ensamblador; A sigue siendo admisible. No confundir `assignment_delta=0` de este report congelado con churn del motor, que tiene otros valores.
4. C visible como evidencia negativa, sin opción de selección/promoción. Mostrar población2000/100/950/950 y los cuatro fallos originales: `population_cap:0`, `population_floor:1`, `population_tolerance:0`, `population_tolerance:1`.
5. Semilla/perfil/K/configuración/origen/assignment hash y hashes de geometría reproducibles en ledger. Semilla0 y perfilcontrolled son metadata de fixture, no ejecución real GerryChain.
6. Capas existentes del fixture: sección/unidad/municipio/comarca coinciden porque son singleton; provincia es universo, distritos dependen de la asignación. No inventar capa postal ni componentes acreditados ausentes. Mostrar el límite de esta coincidencia sintética.
7. GeoJSON web derivado con embedding explícito; métricas siempre calculadas/congeladas en plano local sintético. No asignar EPSG falso a las coordenadas0–4. No publicar ni reemplazar geometrías oficiales.
8. Diagnóstico offline sin nuevas dependencias; JSON/CSV son evidencia principal y Excel opcional posterior. Las SVG se construyen directamente de las16 geometrías/asignaciones; Kepler no es necesario.

## Ejemplo y aceptación

`diagnostico.html` satisface estos requisitos de información y muestra dos SVG, tabla A/B/C, explicación y enlaces de procedencia; incluye toggles de fronteras/rechazo. `comparison.csv` expone12 filas de distrito. `assets_metric/` conserva plano local; `assets_web/` conserva exportación sintética RFC7946 sin CRS EPSG inventado.

Pruebas realizadas: assembler/build_gallery reales, hashes exactos, conservación de shortlist/Pareto/rechazo, assets A/B íntegros, HTML estático y ejecución de `app.js` real en JavaScriptCore con DOM/MapLibre **simulados** (registro de carga de16 features por mapa, filtro Pareto, botón selección B y serialización del JSON; toggles del diagnóstico simulados). No se renderizaron mapas MapLibre ni se validaron CSS/WebGL/legibilidad/interacción en un navegador.

Chrome138 está instalado pero su arranque fue bloqueado por el sandbox (`bootstrap_check_in ... Permission denied`); `ps` para control de memoria también produjo EPERM. No se reintentó sin sandbox ni se pidió elevar permisos. Conservar `gallery_dom.stderr.log` y `validation_results.json`. El runtime JavaScriptCore local no requiere navegador, red ni instalación; no sustituye una captura de navegador.

## Decisiones propuestas a Work

| Objeto | Dictamen | Límite |
|---|---|---|
| Selección/Pareto congelados | SIN_VENTAJA_DEMOSTRADA | Ya funcionaban en DDD; score intacto |
| Tabla/rechazos/explicación/ledger | MEJORA_DEMOSTRADA | Más información verificable en diagnóstico local del mismo fixture |
| Mejora del algoritmo | NO_EVALUABLE | No se ejecutó generación ni nuevas alternativas |
| Render/usabilidad del visor | NO_EVALUABLE | Sin navegador operativo/WebGL ni estudio de usuario |

Prioridad recomendada: añadir tablas y causas a una herramienta de diagnóstico aislada antes de considerar cambios del visor; autorización y revisión separadas. No convertir `SELECTED_FOR_PROMOTION` serializado por el código de la galería en autorización real de promoción, validación o certificación. No se ejecuta runner.finish ni ningún promotor.
