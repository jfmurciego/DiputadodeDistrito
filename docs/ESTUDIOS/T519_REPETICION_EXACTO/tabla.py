#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: estudio T-519 (repetición del exacto de Deslinde) — tabla de resultados
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Tabla de la repetición
FECHA: 2026-11-28
ESTADO: estudio (no cambia el motor ni lanza nada)
CAMBIOS: fichero nuevo.
MOTIVO: T-509, hallazgo A1-4: comprobar si el mapa y la huella del exacto se repiten cuando cambia la velocidad de la máquina.
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE: junta las ejecuciones de repetir.sh en RESULTADOS.json y TABLA.md.
USO: tabla.py <carpeta runs> <carpeta de salida>. Lee <runs>/<t>_<cond>/competicion/<t>/COMPETICION.json y reloj.json."""
import json
import sys
from pathlib import Path

COND = {"a1": "reposo 1", "a2": "reposo 2", "b": "un núcleo", "c": "con carga"}
ESTADO = {"OPTIMO": "óptimo demostrado", "MEJOR_VALIDO": "mejor válido"}


def leer(d: Path) -> dict | None:
    t, cond = d.name.rsplit("_", 1)
    f = d / "competicion" / t / "COMPETICION.json"
    reloj = json.loads((d / "reloj.json").read_text()) if (d / "reloj.json").is_file() else {}
    if not f.is_file():
        return {"territorio": t, "condicion": cond, "error": "sin COMPETICION.json", **reloj} if reloj else None
    c = json.loads(f.read_text(encoding="utf-8"))
    cands = {x["id"]: x for x in c["candidatos"]}
    g, e, ex = cands[c["ganador"]], cands.get("exacto") or {}, c.get("exacto") or {}
    return {"territorio": t, "condicion": cond, "ganador": c["ganador"],
            "clave_d8": (g.get("clave_naturalidad") or [])[:5],
            "ganador_huella_plan": g.get("huella_plan"),
            "exacto_estado": ex.get("estado"), "exacto_etapas": ex.get("etapas"),
            "exacto_huella_plan": e.get("huella_plan"), "exacto_composicion_sha256": e.get("composicion_sha256"),
            "huella_resultado": c["huella_resultado"], "composicion_sha256": g.get("composicion_sha256"),
            "ortools": ex.get("ortools"), "tiempo_total_s": c.get("tiempo_total_s"), **reloj}


def main(runs: str, salida: str) -> int:
    filas = [f for f in (leer(d) for d in sorted(Path(runs).iterdir()) if d.is_dir()) if f]
    filas.sort(key=lambda f: (f["territorio"], f["condicion"]))
    Path(salida, "RESULTADOS.json").write_text(json.dumps(filas, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    lin = ["| Territorio | Condición | Ganador | Clave D8 (fuera · exceso · partidas · frontera km · desvío) | Exacto | "
           "`huella_resultado` | sha256 de la composición | Reloj (s) |", "|---|---|---|---|---|---|---|---|"]
    resumen = []
    for f in filas:
        if "error" in f:
            lin.append(f"| {f['territorio']} | {COND.get(f['condicion'], f['condicion'])} | ERROR | — | — | — | — | {f.get('reloj_s', '—')} |")
            continue
        k = f["clave_d8"]
        clave = f"{k[0]} · {k[1]:.4f} · {k[2]} · {k[3]:.1f} · {k[4]:.4f}" if len(k) == 5 else "—"
        lin.append(f"| {f['territorio']} | {COND.get(f['condicion'], f['condicion'])} | {f['ganador']} | {clave} | "
                   f"{ESTADO.get(f['exacto_estado'], f['exacto_estado'])} | `{f['huella_resultado'][:16]}` | "
                   f"`{(f['composicion_sha256'] or '')[:16]}` | {f.get('reloj_s', '—')} |")
    for t in sorted({f["territorio"] for f in filas}):
        del_t = [f for f in filas if f["territorio"] == t and "error" not in f]
        campos = ("ganador", "huella_resultado", "composicion_sha256", "exacto_huella_plan", "exacto_estado")
        distintos = {c: len({json.dumps(f[c]) for f in del_t}) for c in campos}
        etapas = len({json.dumps([e[:3] for e in (f["exacto_etapas"] or [])]) for f in del_t})
        cotas = len({json.dumps(f["exacto_etapas"]) for f in del_t})
        resumen.append(f"- {t}: {len(del_t)} ejecuciones; valores distintos: " + ", ".join(
            f"{c} {n}" for c, n in distintos.items()) + f", etapas (estado y valor) {etapas}, etapas con cota {cotas}.")
    Path(salida, "TABLA.md").write_text("\n".join(lin + ["", "Valores distintos por territorio (1 = se repite):"]
                                                   + resumen) + "\n", encoding="utf-8")
    print("\n".join(resumen))
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:3]))
