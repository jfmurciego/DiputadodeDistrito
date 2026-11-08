# Guía del Gestor de Campañas 2.0 (una página)

Actions → **0 Gestor de Campañas** → *Run workflow* (rama `main`). Lanzarlo usted mismo es su permiso para ese
lanzamiento y esa publicación (D-22). Primero se ve el plan; nada se lanza mientras «Solo plan» esté marcado.

## Formulario (en este orden)

| # | Entrada | Opciones | Qué hace |
|---|---|---|---|
| 1 | Elección | legislatura vigente · histórico: generales 2019-11 … 2011 | El histórico aún falla al planificar (necesita T-83 A). |
| 2 | Tipo | nacional · autonómico | Congreso por provincia (52) o parlamentos autonómicos (19). |
| 3 | Territorios | `todos` o lista separada por comas | Nacional: provincias por nombre, código INE o matrícula (`Huesca`, `22`, `HU`) o comunidades por nombre (`Aragón` = sus 3 provincias). Autonómico: comunidades por nombre o código INE (`Galicia`, `13`). |
| 4 | Inicio | desde el principio · aprovechar fuentes · reutilizar progreso | Rehace todo · rehace desde la fuente territorial acreditada · decide por territorio (publicado: nada; 00 completa: publicar; producto territorial: reutilizar; sin producto: desde el principio). |
| 5 | Publicar en el visor | no · sí | «sí» publica cada 00 terminada (05) y la galería del ensemble. |
| 6 | Ensemble GerryChain | ninguno · 10 · 25 | «10» lanza la 06 `ensemble_10` al final; solo territorios con `configuracion/ensemble/<territorio>.json`. «25» aún falla (sin validar). |
| — | Mapa | 407 · 350 | 350 = escaños reales de 2023 (T-102): solo nacional, sin publicar y sin ensemble (D-18). |
| — | Solo plan | marcado (por defecto) | Muestra en el resumen del run qué se lanzaría. Desmárquelo para lanzar. |

Lo demás (`max_paralelo`, `modo`, `campana`, `estrategia`, `publication_mode`) es avanzado: déjelo como está.

## Qué ocurre al lanzar

1. Aprobación del entorno `produccion` (un clic por campaña).
2. Un territorio de prueba; si falla, se para la campaña. Después, el resto de `max_paralelo` en `max_paralelo`.
3. Por territorio: **00** (encadena sola el par y la 00 electoral) → **05** si publica → **06** si ensemble.
4. Cerca del límite de 6 h el Gestor se releva solo («continuar», sin otro clic); lo empezado no se rehace.

## Ejemplos

- Plan de todo el Congreso: tipo `nacional`, territorios `todos`, Solo plan marcado.
- Una comunidad: territorios `Castilla y León`.
- Prueba con una provincia: territorios `Soria`, inicio `reutilizar progreso`, publicar `no`, Solo plan desmarcado.

## Errores al planificar (no se lanza nada)

El resumen muestra `::error::` con la causa: histórico no disponible, ensemble 25 sin validar, territorios sin
configuración de ensemble, mapa 350 con publicar o con tipo autonómico, o partes desconocidas.
