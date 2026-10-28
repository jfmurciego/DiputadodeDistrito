# Complemento: visor productivo frente a galería de ensemble

Versión1.0.0; fecha2026-10-10; alcance: lectura y prueba pura aislada con los candidatos congelados. No se modifica el visor, no se registra un resultado ni se renderiza un mapa. Este complemento corrige cualquier extrapolación de las carencias de la **galería** al conjunto de DDD: **el visor productivo ya muestra población, objetivo, desviación y lista de municipios por distrito**.

## Componentes y capacidades comprobadas

| Capacidad | Galería ensemble | Visor productivo1.4.0 | Diagnóstico aislado EXP3 |
|---|---|---|---|
| Comparación de alternativas | Dos mapas A/B simultáneos, perfil y Pareto | Selector de resultado/alternativa; un mapa sustituye al anterior | Dos SVG del mismo universo |
| Población | Máximo de desviación agregado en tarjetas | Ficha/popup con población, objetivo y desviación por distrito | Tabla simultánea de todos los distritos A/B/C |
| Municipios | No presenta lista ni conteo de splits | Lista de nombres si `municipalities` está disponible | Municipios singleton: división0 acreditada en fixture |
| Floor/cap y banda dura | No visibles estructurados | No incluidos en `districtHtml` | Ambos límites y banda explícitos |
| Motivos de rechazo | Invalid IDs en JSON, no tarjeta/cause visible | Estado técnico/certificación/auditoría y `status_reasons` globales visibles | Cuatro incumplimientos poblacionales originales C |
| Estado de uso | Selección de campo pendiente; exportación de solicitud | Estado técnico y certificación/publicabilidad separados | DIAGNÓSTICO; ninguna certificación/promoción |
| Explicación del ranking | Pareto visual sin explicación de dominancia | No ranking/Pareto A/B en la ficha probada | Explicación específica B/A con objetivos congelados |

Referencias exactas del HEAD `42163cd8cebd120db9ab9fd1329c32ccdd87cf36`:

- `visor/app.js:11–13`: helpers de extracción/formato de campos; `69–77`: `districtHtml`, con campos población/target/desviación/municipios en70 y etiquetas visibles en76.
- `visor/app.js:96`: click produce ficha y popup con el mismo `districtHtml`.
- `visor/app.js:8`: instancia un mapa `container:"map"`; `78`: elimina capas/fuente de distritos; `81`: lo invoca antes de cargar alternativa; `85`: instala nueva fuente/capas. No comparación simultánea A/B en ese código.
- `visor/index.html:16`: selector resultado/alternativa; `20`: único contenedor de mapa; `25`: ficha; `26`: Estado de uso con advertencia de auditoría/certificación.
- `visor/app.js:87–90`: estado técnico/geometría/certificación/publicabilidad y motivos globales. `88` presenta `status_reasons`; `90` asigna `useStatus.textContent`. No afirmar que DDD carece de motivos de estado: la carencia comprobada es **causas granulares por distrito dentro de `districtHtml`**, no auditoría global.
- `ddd_ensemble/gallery.py:15–18`: comparación A/B y filtros/decisión; `29`: tarjetas de métricas agregadas; pruebas previas EXP3 conservadas.

## Prueba reproducible nueva, sin repetir la galería

```sh
/private/tmp/madrid-gerrychain-venv/bin/python /private/tmp/ddd-nacho-validacion3-20261010/run_visor_check.py
```

El script extrae exactamente helpers11–13 y función69–77 de `visor/app.js` a `visor_pure_functions.js`, verifica posiciones y SHA, y los evalúa con JavaScriptCore local. Añade únicamente un export de referencias a las funciones para el harness: no altera sus cuerpos. `visor_check.js` llama `districtHtml` para los12 distritos A/B/C ya existentes, con `kind:canonical_m06`. Población, asignación y municipios proceden de los assets métricos reconstruidos y `frozen_results.json`; no hay nuevas alternativas.

Ejemplo A/distrito0: `population=1150`, `target_population=1000`, `relative_deviation=0.15`, `municipalities="M1,M2,M3,M4"`. La lista identifica los cuatro municipios presentes; **no es un conteo de municipios divididos**. Los municipios singleton del fixture son16 y ninguno está repartido entre distritos.

HTML producido por la función actual, sin reescribirla:

```html
<p class="district-title">Distrito 0</p><dl class="detail-list"><dt>Población</dt><dd>1150</dd><dt>Objetivo</dt><dd>1000</dd><dt>Desviación</dt><dd>15,00 %</dd><dt>Municipios</dt><dd>M1,M2,M3,M4</dd></dl>
```

Se suministran además `floor=800`, `cap=1750`, `municipality_split_count=0` y la lista original de incumplimientos para cada candidato. Esos campos no aparecen en la ficha porque la función no los consume. Los12 casos pasan: población/objetivo/desviación/lista presentes; floor/cap/conteo split/causas poblacionales granulares ausentes. C puede producir un fragmento HTML de diagnóstico, pero no se ha añadido al registro del visor, seleccionado ni promovido.

Resultados: `visor_check_results.json` conserva inputs, HTML y siete aserciones por caso; `visor_execution.json` conserva comando, tiempo/RSS, hashes y origen de líneas. Ejecución medida0,039s, pico RSS5,20MB; timeout60s, CPU55s y límite DATA640MiB. Sin DOM, MapLibre, navegador ni red: es una prueba **pura de producción de HTML**, complementada por lectura del flujo del visor. Chrome no se reintenta.

Hashes exactos:

| Archivo | SHA256 |
|---|---|
| `visor/app.js` | `d8451aea3eee94e14693308e8761c4ce727870d2b01c20894ae0aed8fae3619a` |
| `visor/index.html` | `7e7b4247109efadfe78dbc5d0426ff5ef27a03e3655c992e6b4ccb16db561f9a` |
| Funciones extraídas | `88df5cc52088544315fc52d24d660b529f4a2bf375cd3a69979b119ffdf2e7c5` |

Hashes de las dos fuentes iguales antes/después; ninguna escritura productiva. El primer intento del harness falló por alcance lexical de un helper dentro de `eval`; se corrigió el export de referencias y se repitió únicamente esta prueba nueva. Las pruebas anteriores de galería, su JSON y conclusiones conservan su evidencia y no se rerun.

## Conclusión delimitada

No proponer implementar de nuevo la población/desviación ni el estado auditado que el visor ya muestra. El aporte diagnóstico demostrado es **tabla simultánea de alternativas, límites explícitos, conteo acreditado de fragmentación municipal, causas por distrito y explicación de ranking con ledger**, con candidatos/score inalterados. La conveniencia de incorporarlo al visor productivo sigue pendiente de Work y de revisión; render/usabilidad y mejora algorítmica continúan NO_EVALUABLE.
