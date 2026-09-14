#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: migración temporal R016
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Refinamiento canónico post-factibilidad
FECHA: 2026-09-11
ESTADO: temporal de un solo uso
FUNCIÓN: prepara M05 v7.4.0, su legacy, documentación candidata R016 y prueba específica sin alterar configuración territorial.
CAMBIOS: elimina la parada prematura al primer fuera_12=0, conserva la provincia problemática inicial como ámbito de recocido y registra la primera factibilidad frente al objetivo final.
MOTIVO: hacer que M05 continúe optimizando max_rel_dev y error cuadrático después de satisfacer el umbral ±12 %, tal como declara su objetivo canónico.
ORIGEN: R016
"""
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATE = "2026-09-11"


def archive(src_rel: str, dst_rel: str) -> None:
    src = ROOT / src_rel
    dst = ROOT / dst_rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        if dst.read_bytes() != src.read_bytes():
            raise RuntimeError(f"legacy existente distinto: {dst_rel}")
        return
    shutil.copy2(src, dst)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if text.count(old) != 1:
        raise RuntimeError(f"R016 esperaba una ocurrencia de {label}; encontró {text.count(old)}")
    return text.replace(old, new, 1)


def patch_m05() -> None:
    rel = "modulos/05_optimizar_distritos.py"
    legacy = "legacy/modulo05/05_optimizar_distritos_v7.3.1.py"
    archive(rel, legacy)
    p = ROOT / rel
    t = p.read_text(encoding="utf-8")
    t = replace_once(t, "VERSIÓN: 7.3.1", "VERSIÓN: 7.4.0", "versión M05")
    t = replace_once(t, "NOMBRE DE VERSIÓN: Escape determinista de mínimos locales — Gobernanza R015", "NOMBRE DE VERSIÓN: Refinamiento canónico post-factibilidad", "nombre M05")
    t = replace_once(t, "ENTRADAS: grafo M03 y solución M04 v7.3.0 con ddd_unit_id y ddd_closed_urban.", "ENTRADAS: grafo M03 y solución M04 v7.3.1 con ddd_unit_id y ddd_closed_urban.", "entrada M04")
    t = replace_once(t, "ESTADO: vigente — R015 de gobernanza; lógica funcional heredada sin cambios.", "ESTADO: candidato R016 — pendiente de ejecución territorial GitHub.", "estado M05")
    t = replace_once(t, "CAMBIOS: normaliza cabecera y predecesor legacy; no modifica algoritmo ni contrato funcional.", "CAMBIOS: continúa la búsqueda después de la primera solución con fuera_12=0; conserva como ámbito las provincias que eran problemáticas al inicio y registra primera factibilidad frente al óptimo final encontrado.", "cambios M05")
    t = replace_once(t, "MOTIVO: cerrar la deuda de auditoría y hacer verificable la disciplina de versiones.", "MOTIVO: el código v7.3.x interrumpía el recocido al primer fuera_12=0 aunque el objetivo canónico todavía ordena minimizar máximo desvío y error cuadrático.", "motivo M05")
    t = replace_once(t, "ANTERIOR: legacy/modulo05/05_optimizar_distritos_v7.3.0.py", f"ANTERIOR: {legacy}", "anterior M05")

    t = replace_once(
        t,
        "    start = obj(d_pop)\n    initial_candidate_relations = len(unique_candidates())\n",
        "    start = obj(d_pop)\n    initial_candidate_relations = len(unique_candidates())\n    initial_outlier_provinces = sorted(\n        {d_prov[d] for d, p in d_pop.items() if abs(p - target) > tol}\n    )\n",
        "provincias problemáticas iniciales",
    )
    t = replace_once(
        t,
        "        unit_dist[u] = d1\n        greedy_accepted += 1\n        if obj(d_pop)[0] == 0 and obj(d_pop)[2] == 0:\n            break\n\n    greedy_final = obj(d_pop)\n",
        "        unit_dist[u] = d1\n        greedy_accepted += 1\n\n    greedy_final = obj(d_pop)\n",
        "parada greedy prematura",
    )
    t = replace_once(
        t,
        "    # Fase B: escape determinista del mínimo local.\n    # Se limita a las provincias que todavía contienen distritos fuera de ±12%.\n    active_provinces = sorted(\n        {d_prov[d] for d, p in d_pop.items() if abs(p - target) > tol}\n    )\n",
        "    # Fase B: escape determinista del mínimo local y refinamiento posterior.\n    # Se limita a las provincias que eran problemáticas al inicio de M05.\n    # Aunque greedy alcance ±12 %, esas provincias siguen activas para poder\n    # mejorar max_rel_dev y error cuadrático según el objetivo canónico.\n    active_provinces = list(initial_outlier_provinces)\n",
        "ámbito de recocido",
    )
    t = replace_once(
        t,
        "    anneal_start_energy = None\n    anneal_best_energy = None\n\n    if active_units and anneal_iters > 0 and best_obj[2] > 0:\n",
        "    anneal_start_energy = None\n    anneal_best_energy = None\n    first_feasible_iteration = 0 if best_obj[0] == 0 and best_obj[2] == 0 else None\n    objective_first_feasible = list(best_obj) if first_feasible_iteration == 0 else None\n\n    if active_units and anneal_iters > 0:\n",
        "inicio refinamiento post-factibilidad",
    )
    t = replace_once(
        t,
        "            if current_obj < best_obj:\n                best_obj = current_obj\n                best_unit_dist = dict(unit_dist)\n                best_d_units = {d: set(us) for d, us in d_units.items()}\n                best_d_nodes = {d: set(ns) for d, ns in d_nodes.items()}\n                best_d_pop = dict(d_pop)\n                if best_obj[0] == 0 and best_obj[2] == 0:\n                    break\n",
        "            if current_obj < best_obj:\n                best_obj = current_obj\n                best_unit_dist = dict(unit_dist)\n                best_d_units = {d: set(us) for d, us in d_units.items()}\n                best_d_nodes = {d: set(ns) for d, ns in d_nodes.items()}\n                best_d_pop = dict(d_pop)\n                if first_feasible_iteration is None and best_obj[0] == 0 and best_obj[2] == 0:\n                    first_feasible_iteration = i + 1\n                    objective_first_feasible = list(best_obj)\n",
        "parada anneal prematura",
    )
    t = replace_once(t, '        "version": "7.3.1",', '        "version": "7.4.0",', "versión reporte")
    t = replace_once(
        t,
        '        "anneal_iterations_executed": anneal_iterations_executed,\n        "anneal_start_objective": list(anneal_start_obj),\n',
        '        "anneal_iterations_executed": anneal_iterations_executed,\n        "first_feasible_iteration": first_feasible_iteration,\n        "objective_first_feasible": objective_first_feasible,\n        "post_feasible_iterations": (\n            max(0, anneal_iterations_executed - first_feasible_iteration)\n            if first_feasible_iteration is not None\n            else 0\n        ),\n        "anneal_start_objective": list(anneal_start_obj),\n',
        "métricas primera factibilidad",
    )
    t = replace_once(t, 'f"[Módulo 5] OK v7.3.0 hard={final[0]} fuera_12={final[2]} "', 'f"[Módulo 5] OK v7.4.0 hard={final[0]} fuera_12={final[2]} "', "versión log")
    p.write_text(t, encoding="utf-8")


def write_m05_contract() -> None:
    rel = "docs/MODULOS/M05_OPTIMIZACION.md"
    archive(rel, "legacy/docs/MODULOS/M05_OPTIMIZACION_v1.0.0.md")
    content = """# M05 — Optimizar distritos

**Versión documental:** 1.1.0  
**Nombre de versión:** Candidato R016 — refinamiento canónico post-factibilidad  
**Fecha:** 2026-09-11  
**Código activo:** M05 v7.4.0 — candidato  
**Última lógica territorial validada:** M05 v7.3.0 — GitHub Run #8 `34592470470`  
**Anterior:** `legacy/docs/MODULOS/M05_OPTIMIZACION_v1.0.0.md`  
**Cambio:** elimina la parada al primer `fuera_12=0` y permite continuar optimizando los siguientes términos de la función canónica.  
**Motivo:** v7.3.x declaraba una función lexicográfica completa pero interrumpía la búsqueda en cuanto satisfacía el tercer término.

## Propósito
M05 modifica fronteras de la solución M04 para mejorar equilibrio poblacional sin violar ninguna regla estructural. M04 construye una solución válida; M05 explora mejores soluciones dentro del espacio duro válido.

## Restricciones duras R012
1. 67 distritos;
2. Huesca 11 / Teruel 7 / Zaragoza 49;
3. provincia infranqueable;
4. contigüidad estricta por M03;
5. población entre 0,80×target y 1,75×target;
6. movimientos de `ddd_unit_id` completas;
7. distritos `ddd_closed_urban` no reciben ni ceden unidades;
8. disciplina municipal final preservada.

## Objetivo canónico
Comparación lexicográfica: violaciones duras → magnitud dura → número fuera de ±12 % → máximo desvío → error cuadrático global.

## Estrategia candidata v7.4.0
**Fase A — greedy determinista:** sigue aceptando únicamente movimientos individuales que mantienen restricciones duras y mejoran estrictamente el objetivo. Ya no se detiene por el mero hecho de llegar a `fuera_12=0`; continúa mientras exista una mejora canónica individual.

**Fase B — recocido reproducible + refinamiento:** el ámbito se fija a las provincias que tenían distritos fuera de ±12 % al inicio de M05. El recocido puede atravesar estados peores en el objetivo fino, nunca restricciones duras, conserva continuamente la mejor solución canónica y ya no se detiene en la primera solución factible. Agota el presupuesto configurado para intentar reducir después el máximo desvío y el error cuadrático.

El reporte añade `first_feasible_iteration`, `objective_first_feasible` y `post_feasible_iterations`, de modo que se pueda demostrar cuánto trabajo se realizó después de alcanzar por primera vez ±12 %.

## Principio de prudencia
R016 **no reduce el umbral ±12 %**, no modifica suelo/techo, no cambia provincia, atomicidad municipal ni contigüidad, y no introduce compactness como objetivo. El candidato solo corrige la incoherencia entre función objetivo declarada y criterio de parada.

## Productos auditables
- GeoJSON ZIP de asignación completa optimizada.
- `M05/asignacion_optimizada.csv` con las 1.463 secciones.
- `aragon_2025_m05_informe.json` con objetivos, métricas, movimientos, primera factibilidad, unidades finales cambiadas, provincia activa, semilla y parámetros.

## Aceptación R016
1. `Pruebas DDD — R015` debe permanecer verde.
2. La prueba específica R016 debe demostrar búsqueda posterior a primera factibilidad y determinismo.
3. Un nuevo run territorial debe conservar todos los PASS del Run #8.
4. `fuera_12` debe seguir en 0.
5. `objective_final` debe ser lexicográficamente igual o mejor que `objective_first_feasible`; para justificar promoción se espera mejora real en `max_rel_dev` o error cuadrático sin regresión territorial.

Hasta ese run, **Run #8 sigue siendo la referencia territorial** y M05 v7.4.0 es candidato, no baseline.
"""
    (ROOT / rel).write_text(content, encoding="utf-8")


def write_r016_test() -> None:
    p = ROOT / "tests/test_r016_refinamiento.py"
    if p.exists():
        raise RuntimeError("tests/test_r016_refinamiento.py ya existe")
    p.write_text('''#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\n"""\nPROYECTO: Diputado de Distrito\nCOMPONENTE: prueba R016 de refinamiento post-factibilidad\nVERSIÓN: 1.0.0\nNOMBRE DE VERSIÓN: Refinamiento después de fuera_12=0\nFECHA: 2026-09-11\nESTADO: candidato R016\nFUNCIÓN: demostrar que M05 continúa el recocido después de la primera solución dentro de ±12 % y conserva una solución canónica igual o mejor.\nCAMBIOS: primera versión.\nMOTIVO: impedir que reaparezca la parada prematura de M05 v7.3.x.\nORIGEN: R016\n"""\nfrom __future__ import annotations\n\nimport json\nimport tempfile\nimport unittest\nfrom pathlib import Path\n\nfrom tests.test_r015_invariantes import M05Determinism\n\n\nclass M05RefinementAfterFeasible(unittest.TestCase):\n    def test_continua_despues_de_primera_factibilidad(self):\n        helper = M05Determinism(methodName="test_m05_misma_semilla_misma_salida")\n        with tempfile.TemporaryDirectory() as td:\n            cfg, output, report = helper.make_case(Path(td), "r016")\n            helper.run_case(cfg)\n            rep = json.loads(report.read_text(encoding="utf-8"))\n            self.assertEqual(rep["version"], "7.4.0")\n            self.assertIsNotNone(rep["first_feasible_iteration"])\n            self.assertGreater(rep["post_feasible_iterations"], 0)\n            self.assertEqual(rep["anneal_iterations_executed"], 500)\n            self.assertEqual(rep["districts_outside_tolerance"], 0)\n            self.assertLessEqual(tuple(rep["objective_final"]), tuple(rep["objective_first_feasible"]))\n\n\nif __name__ == "__main__":\n    unittest.main()\n''', encoding="utf-8")


def update_readme() -> None:
    rel = "README.md"
    archive(rel, "legacy/docs/README_v3.3.1.md")
    p = ROOT / rel
    t = p.read_text(encoding="utf-8")
    t = replace_once(t, "**README v3.3.1** · 11-09-2026 · Estado: **R014 territorial validado + R015 ingeniería cerrada**  \n**Anterior:** `legacy/docs/README_v3.3.0.md`  \n**Cambio:** cierre de trazabilidad documental de R015; no cambia algoritmo, parámetros ni mapa.", "**README v3.4.0** · 11-09-2026 · Estado: **R014 territorial validado + R015 cerrada + R016 candidato**  \n**Anterior:** `legacy/docs/README_v3.3.1.md`  \n**Cambio:** abre R016 con M05 v7.4.0 candidato para completar el objetivo canónico después de la primera solución dentro de ±12 %.", "cabecera README")
    marker = "## Arquitectura\n"
    section = """## R016 — refinamiento canónico post-factibilidad — CANDIDATO\n\nM05 **v7.4.0** corrige una incoherencia de v7.3.x: el objetivo canónico ordena minimizar, tras `fuera_12`, el máximo desvío y el error cuadrático, pero el recocido se detenía al primer `fuera_12=0`. R016 conserva todos los límites y restricciones duras y continúa la búsqueda hasta agotar el presupuesto configurado, manteniendo siempre la mejor solución canónica encontrada.\n\nEl candidato registra la primera iteración factible y el objetivo de ese instante para compararlo con el resultado final. **No está promocionado**: Run #8 sigue siendo la referencia territorial hasta que un nuevo run de GitHub confirme todos los PASS y una mejora real del objetivo.\n\n"""
    t = replace_once(t, marker, section + marker, "sección R016 README")
    t = t.replace("R014 y R015 quedan cerrados. Cualquier cambio algorítmico posterior debe abrir una nueva ronda, preservar los PASS de Run #8 y superar la puerta R015 antes de ser promocionado.", "R014 y R015 quedan cerrados. R016 está abierto como candidato funcional de M05. Debe superar la puerta R015 y un nuevo run territorial antes de cualquier promoción; Run #8 continúa como baseline mientras tanto.")
    p.write_text(t, encoding="utf-8")


def update_estado() -> None:
    rel = "docs/ESTADO_MAESTRO_PROYECTO.md"
    archive(rel, "legacy/memoria/ESTADO_MAESTRO_PROYECTO_v1.11.0.md")
    p = ROOT / rel
    t = p.read_text(encoding="utf-8")
    t = replace_once(t, "**Versión:** 1.11.0  \n**Fecha de corte:** 2026-09-11  \n**Anterior:** `legacy/memoria/ESTADO_MAESTRO_PROYECTO_v1.10.0.md`", "**Versión:** 1.12.0  \n**Fecha de corte:** 2026-09-11  \n**Anterior:** `legacy/memoria/ESTADO_MAESTRO_PROYECTO_v1.11.0.md`", "cabecera Estado Maestro")
    t = replace_once(t, "- M05: **v7.3.1**.", "- M05: **v7.4.0 candidato R016**; última lógica territorial validada: v7.3.0 / Run #8.", "estado M05 en maestro")
    marker = "## 3. Reglas duras Aragón\n"
    section = """## 2.1. R016 — candidato funcional\n\nSe abre R016 para corregir la parada prematura de M05 después de alcanzar por primera vez `fuera_12=0`. El candidato v7.4.0 mantiene intactas todas las restricciones duras, el umbral ±12 %, la semilla y la configuración vigente; cambia únicamente el criterio de parada para seguir optimizando los términos posteriores del objetivo canónico.\n\nEstado: **pendiente de CI R015 y de nuevo run territorial**. Run #8 no queda reemplazado hasta promoción expresa.\n\n"""
    t = replace_once(t, marker, section + marker, "sección R016 maestro")
    t = t.replace("No modificar M04/M05 ni sus criterios sin abrir una nueva ronda. Todo cambio funcional posterior debe conservar los PASS de Run #8, superar la suite R015 y obtener un nuevo run territorial reproducible antes de promoción.", "R016 es la ronda funcional activa y afecta únicamente a M05 v7.4.0 candidato. Debe conservar los PASS de Run #8, superar la suite R015 y obtener un nuevo run territorial reproducible antes de promoción.")
    p.write_text(t, encoding="utf-8")


def update_continuidad() -> None:
    rel = "docs/CONTINUIDAD_NUEVO_CHAT.md"
    archive(rel, "legacy/memoria/CONTINUIDAD_NUEVO_CHAT_v1.4.0.md")
    p = ROOT / rel
    t = p.read_text(encoding="utf-8")
    t = replace_once(t, "**Versión:** 1.4.0  \n**Fecha de corte:** 2026-09-11  \n**Anterior:** `legacy/memoria/CONTINUIDAD_NUEVO_CHAT_v1.3.0.md`", "**Versión:** 1.5.0  \n**Fecha de corte:** 2026-09-11  \n**Anterior:** `legacy/memoria/CONTINUIDAD_NUEVO_CHAT_v1.4.0.md`", "cabecera continuidad")
    marker = "## Ingeniería y auditoría\n"
    section = """## R016 — ronda activa, candidato M05 v7.4.0\n\nObjetivo: alinear la ejecución de M05 con su objetivo canónico. v7.3.x detenía el recocido al primer `fuera_12=0`; v7.4.0 continúa dentro de la provincia inicialmente problemática para intentar reducir después `max_rel_dev` y error cuadrático, sin relajar restricciones.\n\nEl reporte registra `first_feasible_iteration`, `objective_first_feasible` y `post_feasible_iterations`. La prueba R016 exige que exista refinamiento posterior y que el objetivo final no sea peor que el primer estado factible.\n\n**Estado:** candidato; Run #8 sigue siendo la referencia territorial hasta un nuevo run completo/iterativo aceptado.\n\n"""
    t = replace_once(t, marker, section + marker, "sección R016 continuidad")
    t = t.replace("**Siguiente paso:** abrir una nueva ronda solo cuando exista un objetivo funcional concreto; R014 y R015 están cerrados.", "**Siguiente paso:** validar M05 v7.4.0 con `Pruebas DDD — R015`; si queda verde, ejecutar `Procedimiento DDD — Aragón` en modo iterativo y comparar el objetivo final con Run #8.")
    p.write_text(t, encoding="utf-8")


def update_bitacora() -> None:
    rel = "docs/BITACORA.md"
    archive(rel, "legacy/bitacora/BITACORA_v2.16.1.md")
    p = ROOT / rel
    t = p.read_text(encoding="utf-8")
    t = replace_once(t, "**Versión:** 2.16.1  \n**Fecha:** 2026-09-11  \n**Anterior:** `legacy/bitacora/BITACORA_v2.16.0.md`", "**Versión:** 2.17.0  \n**Fecha:** 2026-09-11  \n**Anterior:** `legacy/bitacora/BITACORA_v2.16.1.md`", "cabecera bitácora")
    marker = "## Reglas permanentes\n"
    section = """## R016 — Refinamiento canónico post-factibilidad — ABIERTO\n\nSe detecta una incoherencia funcional en M05 v7.3.x: la función objetivo es lexicográfica y, después de `fuera_12`, compara `max_rel_dev` y error cuadrático, pero tanto greedy como recocido podían detenerse inmediatamente al llegar a `fuera_12=0`.\n\nM05 v7.4.0 candidato elimina esa parada. El ámbito del recocido queda fijado a las provincias problemáticas al inicio, de modo que si se alcanza ±12 % durante M05 se puede continuar refinando sin abrir provincias que ya eran correctas. Se añaden métricas de primera factibilidad y una prueba R016 específica.\n\nNo cambian suelo, techo, ±12 %, provincia, atomicidad municipal, contigüidad, semilla ni configuración Aragón. Run #8 continúa como referencia hasta validación GitHub del candidato.\n\n"""
    t = replace_once(t, marker, section + marker, "sección R016 bitácora")
    p.write_text(t, encoding="utf-8")


def update_registro() -> None:
    rel = "docs/REGISTRO_DE_CAMBIOS.md"
    archive(rel, "legacy/docs/REGISTRO_DE_CAMBIOS_pre_R016_2026-09-11.md")
    p = ROOT / rel
    t = p.read_text(encoding="utf-8")
    entry = """\n## 2026-09-11 — R016 — M05 v7.4.0, refinamiento post-factibilidad\n\nSe abre una ronda funcional limitada a M05. La auditoría del código v7.3.x muestra que la búsqueda se interrumpe al primer `fuera_12=0` aunque el objetivo canónico sigue ordenando por máximo desvío y error cuadrático.\n\nSe preserva M05 v7.3.1 en `legacy/modulo05/05_optimizar_distritos_v7.3.1.py` y se publica v7.4.0 como **candidato**. Greedy continúa mientras existan mejoras estrictas; el recocido conserva las provincias problemáticas iniciales y agota el presupuesto configurado, manteniendo siempre la mejor solución canónica. El reporte añade primera factibilidad y número de iteraciones posteriores.\n\nSe añade `tests/test_r016_refinamiento.py`. La promoción exige CI R015 verde y un nuevo run territorial con todos los PASS de Run #8; hasta entonces Run #8 sigue siendo baseline.\n"""
    if "## 2026-09-11 — R016" in t:
        raise RuntimeError("R016 ya registrado")
    p.write_text(t.rstrip() + "\n" + entry, encoding="utf-8")


def write_round() -> None:
    p = ROOT / "docs/RONDAS/R016_2026-09-11_refinamiento_canonico_m05.md"
    if p.exists():
        raise RuntimeError("ronda R016 ya existe")
    p.write_text("""# R016 — Refinamiento canónico post-factibilidad en M05\n\n**Fecha:** 2026-09-11  \n**Tipo:** cambio funcional controlado en M05  \n**Baseline protegido:** Run #8 `34592470470` / R014  \n**Estado inicial:** candidato, pendiente de CI y ejecución territorial\n\n## Problema\nM05 declara como objetivo canónico: restricciones duras → número fuera de ±12 % → máximo desvío → error cuadrático. Sin embargo, v7.3.x interrumpe tanto el greedy como el recocido en cuanto aparece una solución con `hard=0` y `fuera_12=0`. En Run #8 esa primera factibilidad llegó en la iteración 9.038 y se convirtió automáticamente en resultado final, por lo que nunca se comprobó si las iteraciones restantes podían reducir el 11,943 % máximo.\n\n## Cambio mínimo\n1. conservar M05 v7.3.1 en `legacy/`;\n2. publicar M05 v7.4.0;\n3. no detener greedy solo por alcanzar ±12 %;\n4. fijar el ámbito de recocido a las provincias que eran problemáticas al inicio de M05;\n5. no detener recocido al primer ±12 %, sino agotar `anneal_iters`;\n6. conservar siempre la mejor solución según el objetivo canónico;\n7. registrar primera factibilidad y refinamiento posterior.\n\n## Lo que NO cambia\nK=67; reparto 11/7/49; provincia infranqueable; contigüidad; suelo 0,80; techo 1,75; tolerancia ±12 %; atomicidad `ddd_unit_id`; cierres urbanos; semilla 12345; parámetros de recocido; M04 y configuración Aragón.\n\n## Hipótesis\nCon el mismo espacio de búsqueda y el mismo presupuesto de 20.000 iteraciones, permitir que M05 continúe después de la primera factibilidad puede encontrar una solución lexicográficamente mejor que Run #8 sin necesidad de relajar ninguna regla.\n\n## Criterio de aceptación\n- CI R015 PASS;\n- prueba R016 PASS y determinista;\n- nuevo procedimiento territorial PASS;\n- `fuera_12=0`;\n- `objective_final <= objective_first_feasible`;\n- preferentemente `max_rel_dev < 0.119431695687` o, si empata, menor error cuadrático;\n- cero regresiones en provincia, contigüidad, municipio, suelo/techo, secciones o población.\n\nSi no existe mejora real o aparece degradación territorial, R016 se rechaza y M05 v7.3.1/Run #8 continúa como baseline.\n""", encoding="utf-8")


def main() -> None:
    patch_m05()
    write_m05_contract()
    write_r016_test()
    update_readme()
    update_estado()
    update_continuidad()
    update_bitacora()
    update_registro()
    write_round()
    print("R016 preparado: M05 v7.4.0 candidato + legacy + docs + test")


if __name__ == "__main__":
    main()
