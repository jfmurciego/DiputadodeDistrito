#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: motor 2 — informe por territorio de la competición
VERSIÓN: 1.1.0
NOMBRE DE VERSIÓN: Competición · informe con función de calidad
FECHA: 2026-11-10
ESTADO: candidato (motor 2; producción no lo importa)
CAMBIOS: 1.1.0 (T-205) — el motivo usa los criterios de la función de la competición (A o naturalidad C/D5/D8);
  «mejora al canónico» compara la clave sin huella ni orden. 1.0.0 — fichero nuevo.
MOTIVO: T-163 / D-48: decir qué candidato ganó, por qué, y la tabla de todos (germen del «universo de mapas»).
ANTERIOR: legacy/ddd_motor2/informe_v1.0.0_20261110.py
SALIDA: escribir(resultado, carpeta) -> (COMPETICION.json, COMPETICION.md). El JSON es Resultado.a_dict() más
  «motivo»; el resumen legible repite ganador, motivo, semillas públicas y la tabla ordenada por calidad.
"""
from __future__ import annotations

import json
from pathlib import Path

from .competicion import Candidato, Resultado

CRITERIOS = (  # mismo orden que Candidato.clave()
    ("evaluable", "es evaluable (los otros fallaron al generar o con los datos)"),
    ("violaciones_duras", "tiene menos violaciones duras"),
    ("fuera_tolerancia", "tiene menos distritos fuera de tolerancia"),
    ("desvio_max", "tiene menor desvío máximo"),
    ("ecm", "tiene menor error cuadrático medio"),
    ("huella_plan", "desempate determinista por huella del plan"),
    ("orden", "mismo plan: se queda el primero (el canónico)"),
)

CRITERIOS_NATURAL = (  # Candidato.clave() con funcion C/D5/D8
    ("evaluable", "es evaluable (los otros fallaron al generar o con los datos)"),
    ("violaciones_duras", "tiene menos violaciones duras"),
    ("fuera_tolerancia", "tiene menos distritos fuera de tolerancia"),
    ("exceso_tope", "se pasa menos del tope de desvío (solo para elegir)"),
    ("demarcaciones_partidas", "parte menos partidos judiciales y comarcas agrarias"),
    ("frontera_cortada_km", "corta menos frontera"),
    ("desvio_max", "tiene menor desvío máximo"),
    ("huella_plan", "desempate determinista por huella del plan"),
    ("orden", "mismo plan: se queda el primero (el canónico)"),
)


def motivo(ganador: Candidato, otro: Candidato | None) -> str:
    """Primer criterio de la clave lexicográfica en que el ganador supera a `otro`."""
    if otro is None:
        return "único candidato"
    crit = CRITERIOS_NATURAL if ganador.natural is not None or otro.natural is not None else CRITERIOS
    for (nombre, texto), a, b in zip(crit, ganador.clave(), otro.clave()):
        if a != b:
            return f"frente a {otro.id}: {texto} ({nombre})"
    return f"frente a {otro.id}: idéntico"


def _num(x, fmt="{:.4f}"):
    return "—" if x is None else fmt.format(x)


def escribir(resultado: Resultado, carpeta: Path) -> tuple[Path, Path]:
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    orden = sorted(resultado.candidatos, key=Candidato.clave)
    g = resultado.ganador
    segundo = orden[1] if len(orden) > 1 else None
    d = resultado.a_dict()
    d["motivo"] = motivo(g, segundo)
    d["motivo_frente_al_canonico"] = "es el canónico" if g is resultado.canonico else motivo(g, resultado.canonico)
    d["mejora_al_canonico"] = g.clave()[:-2] < resultado.canonico.clave()[:-2]
    fj = carpeta / "COMPETICION.json"
    fj.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    sp = resultado.semilla_publica or {}
    lineas = [
        f"# Competición · {resultado.territorio}",
        "",
        f"- Ganador: **{g.id}** ({g.estado}). {d['motivo']}.",
        f"- Frente al canónico: {d['motivo_frente_al_canonico']}"
        f"{' (mejora)' if d['mejora_al_canonico'] else ''}.",
        f"- Huella del resultado: `{d['huella_resultado']}`; reglas: `{resultado.huella_reglas[:16]}`.",
    ]
    if sp:
        lineas.append(f"- Semillas públicas ({sp.get('esquema')}): {', '.join(map(str, sp.get('semillas', [])))}; "
                      f"ancla: " + ", ".join(f"{k} `{v[:12]}…`" for k, v in sp.get("ancla", {}).items()) + ".")
    lineas.append(f"- Tiempo total: {resultado.tiempo_total_s:.1f} s.")
    lineas += ["", "| # | Candidato | Semilla | Estado | Duras | Fuera tol. | Desvío máx. | ECM | Plan | Tiempo (s) |",
               "|---|---|---|---|---|---|---|---|---|---|"]
    for i, c in enumerate(orden, start=1):
        t = sum(v for v in c.tiempos.values() if isinstance(v, (int, float)))
        lineas.append(
            f"| {i} | {c.id} | {'—' if c.semilla is None else c.semilla} | {c.estado} | {_num(c.duras, '{}')} | "
            f"{_num(c.fuera_tolerancia, '{}')} | {_num(None if c.desvio_max is None else float(c.desvio_max))} | "
            f"{_num(None if c.ecm is None else float(c.ecm), '{:.6f}')} | "
            f"{c.huella_plan[:10] or '—'} | {t:.1f} |")
    malos = [c for c in orden if c.violaciones or c.detalle]
    if malos:
        lineas += ["", "## Incidencias"]
        for c in malos:
            regl = sorted({v["regla"] for v in c.violaciones})
            lineas.append(f"- {c.id}: {c.detalle or ''}{'; ' if c.detalle and regl else ''}{', '.join(regl)}")
    fm = carpeta / "COMPETICION.md"
    fm.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    return fj, fm
