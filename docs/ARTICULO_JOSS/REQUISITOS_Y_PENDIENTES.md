# Artículo JOSS — requisitos y pendientes

**Versión:** 1.0.0
**Fecha:** 2026-11-08
**Anterior:** ninguno — documento nuevo
**Tarea:** T-94b (borrador; no se envía)

## 1. Requisitos de JOSS — NO VERIFICADOS

No se pudo consultar joss.theoj.org ni joss.readthedocs.io desde la sesión (proxy: 403). Lo siguiente es lo que recuerda el
redactor y **debe confirmarse en las páginas «Submitting», «Paper format» y «Review criteria»** antes de enviar:

| Requisito (a confirmar) | Estado en el repo |
|---|---|
| Licencia aprobada por la OSI, con fichero `LICENSE` en el repositorio | **FALTA `LICENSE`.** `CITATION.cff` y `.zenodo.json` declaran Apache-2.0 pero no hay fichero. Decisión del propietario. |
| Repositorio público y abierto, con incidencias (issues) habilitadas | Público (repo-code en `CITATION.cff`); comprobar issues. |
| Software de investigación con ámbito sustancial (esfuerzo no trivial) | Plausible: ~72 000 líneas Python en `ddd_core`/`modulos`/`herramientas`, 329 ficheros de test. |
| Documentación: instalación, uso, ejemplo, guía de contribución, API | Hay `docs/INSTALACION_LOCAL.md` y `documentacion_publica/`; **falta `CONTRIBUTING.md` y código de conducta** (comprobar). |
| Tests automatizados | Sí (`tests/`, CI «pruebas»). |
| Historial de desarrollo y versiones | El historial git visible empieza el 2026-11-07 (50 commits); **sin etiquetas (tags)**. JOSS suele pedir historia pública sostenida (≈6 meses, a confirmar): posible problema. |
| Paper breve (≈250–1000 palabras), con secciones Summary, Statement of need, State of the field, Software design, Research impact, AI usage disclosure | Borrador en `paper.md` (hay secciones nuevas que JOSS ha ido añadiendo: confirmar la lista actual). |
| Sin software ya publicado como solo-wrapper, ni «dump» de datos | Riesgo: el valor está en el contrato y la procedencia; explicarlo. |

## 2. Qué falta para poder enviarlo

1. **Fichero `LICENSE`** (Apache-2.0 u otra OSI) coherente con `CITATION.cff` y `.zenodo.json` — decisión del propietario.
2. **Versión etiquetada** (`CITATION.cff` dice 4.7.0, README 4.9.0: unificar) y **release**; lo publica el propietario.
3. **DOI de Zenodo**: HUECO. No existe en ningún fichero; se obtiene al archivar la release. No inventado.
4. **Autores y afiliación**: nombre y ORCID están en `CITATION.cff` (0009-0002-4434-959X); falta afiliación. ¿Coautores/colaboradores?
5. **Historia pública**: confirmar el criterio de antigüedad de JOSS frente al historial desde 2026-11-07.
6. **Impacto** (Research impact statement) y **declaración de uso de IA**: las redacta el autor.
7. **Revisión bibliográfica** del «state of the field»; `paper.bib` solo tiene DeFord–Duchin–Solomon (2021) y GerryChain; **comprobar DOI y metadatos** (escritos de memoria; ninguna cifra del proyecto lo está).
8. Documentación: `CONTRIBUTING.md`, código de conducta, ejemplo mínimo reproducible, guía de uso; revisar que el repo es instalable según JOSS.
9. Aviso de derechos de datos INE/Interior (`.zenodo.json` ya advierte); decidir qué se archiva.
10. Compilar el paper con el flujo de JOSS (Docker `openjournals/inara`) — no probado aquí.

## 3. Origen de las cifras del paper
- 49 escenarios y 325 distritos: suma de `n_distritos` en `datos_abiertos/INDEX.json` (licencia CC-BY-4.0 en el mismo fichero).
- Límites 0.80 / 1.75 / 0.12: `docs/POLITICA_K_LIMITES_Y_ESQUEMA.md` y `docs/CONTRATO_TERRITORIO.md`.
- GerryChain 1.0.0 y NetworkX 3.6.1: `requirements-gerrychain-m05.lock`.
- Líneas y tests: recuento local del 2026-11-08 (`ddd_core`, `modulos`, `herramientas`; `tests/*.py`).
