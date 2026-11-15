#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inventario (solo lectura) de objetos registrados con id de territorio NO canónico.

PROYECTO: Diputado de Distrito
FICHERO: inventario_ids_no_canonicos.py
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Inventario de ids no canónicos por rama de reutilización
FECHA: 2026-11-15
ESTADO: candidato
QUÉ HACE: recorre el catálogo, los registros, orchestracion/ y territorios/*/evidencia y lista, por territorio y rama de
  reutilización, el objeto registrado (id, run/artefacto, fecha) y el resultado esperado según el código de esta rama.
CAMBIOS: fichero nuevo (T-349).
MOTIVO: cero sorpresas antes de reanudar la r4: saber qué se reutilizaría y qué se prepararía de nuevo.
ANTERIOR: ninguna (fichero nuevo)

Salida determinista (orden por id canónico y rama; sin fechas de generación). No consulta Actions: lo que solo existe como
artefacto se marca «no verificable desde el repo» con el comando de comprobación.
Uso: python -m herramientas.inventario_ids_no_canonicos --out docs/diagnostico/inventario_ids_no_canonicos
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ddd_core import territorio_ids  # noqa: E402
from herramientas import resolver_preparacion_legislatura as rpl  # noqa: E402

# Rama de reutilización → política del código de esta rama. ESTRICTA: igualdad exacta con el id canónico (rechaza y prepara
# de nuevo). ALIAS: compara con `mismo_territorio` (acepta el id viejo): objeto aceptado tal cual (sorpresa a decidir).
RAMAS = {
    "fuentes_territoriales": ("ESTRICTA", "Activación, P10, P00, puertas y preflight comparan el id exacto (T-336, T-349)"),
    "electoral_fuente": ("ESTRICTA", "Activación, P12, puertas y elegibilidad comparan el id exacto (T-349)"),
    "poblacion": ("ESTRICTA", "la población y el seccionado viajan dentro del paquete de fuentes territorial (misma rama)"),
    "par_fuentes": ("ALIAS", "consumir_par/registrar_par usan mismo_territorio; el par se reescribe al registrar el par nuevo"),
    "producto_M06": ("ALIAS", "resolver_ejecucion_completa/_core y catálogo usan mismo_territorio sobre el territory_id del recibo"),
    "producto_M08": ("ALIAS", "resolver_ejecucion_completa/_core, detectar M08 y catálogo usan mismo_territorio"),
    "composicion_datos": ("ALIAS", "ddd_core.territorio_ids.fichero_por_id: el fichero con el id viejo es válido (D-61)"),
    "registro_visor": ("ALIAS", "publicaciones_visor.json: legislatura_vigente/linaje usan mismo_territorio"),
}
NO_VERIFICABLE = (
    "Artefactos de Actions (ddd-source-package-*, ddd-electoral-package-*, ddd-state-<run>-M0x): solo el nombre y el digest están "
    "en el repo. Comprobar vigencia con: gh api repos/<repo>/actions/runs/<run>/artifacts --jq '.artifacts[]|{name,expired,digest}'"
)


def _json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _base_commit() -> str:
    try:
        return subprocess.check_output(["git", "merge-base", "HEAD", "origin/main"], cwd=ROOT, text=True).strip()
    except Exception:
        return "desconocido"


def _fecha(doc: dict) -> str:
    for k in ("retrieved_at", "generated_at", "created_at", "registered_at"):
        if isinstance(doc, dict) and doc.get(k):
            return str(doc[k])
    return "—"


def _fila(tid, rama, objeto, ident, run, fecha, canonico, politica):
    if canonico:
        resultado = "REUSE (id canónico)"
    elif politica == "ESTRICTA":
        resultado = "RECHAZA → ACQUIRE/prepara de nuevo"
    else:
        resultado = "ACEPTA con alias (sorpresa)"
    return {"territorio": tid, "rama": rama, "objeto": objeto, "id": ident, "run_o_artefacto": run, "fecha": fecha,
            "canonico": canonico, "politica": politica, "resultado": resultado}


def construir(root: Path = ROOT) -> dict:
    tabla = territorio_ids.tabla()
    catalogo = yaml.safe_load((root / "configuracion/catalogo_preparacion.yaml").read_text(encoding="utf-8"))
    estados = {r["territory_id"]: (r.get("editions") or {}).get("2025") or {} for r in catalogo["territories"]}
    visor = _json(root / "orchestracion/publicaciones_visor.json") or {}
    filas = []
    for tid in sorted(tabla):
        legacy = tabla[tid].id_legacy
        st = estados.get(tid, {})
        ev = st.get("evidence") or {}
        # Fuentes territoriales y población (mismo objeto): evidencia de preparación del catálogo.
        prep = st.get("preparation_evidence") or {}
        if prep.get("artifact_name"):
            nombre = str(prep["artifact_name"])
            rec = _json(root / prep["receipt_path"]) if prep.get("receipt_path") else None
            rid = (rec or {}).get("territory_id", "—")
            canon = nombre == f"ddd-source-package-{tid}-2025-{prep.get('run_id')}" and rid in (tid, "—")
            for rama in ("fuentes_territoriales", "poblacion"):
                filas.append(_fila(tid, rama, "preparation_evidence", f"recibo={rid}", nombre, _fecha(rec or {}), canon, RAMAS[rama][0]))
        # Fuente electoral.
        if ev.get("electoral_source"):
            rec = _json(root / ev["electoral_source"]) or {}
            nombre = str(rec.get("artifact_name") or "—")
            canon = rec.get("territory_id") == tid and nombre == f"ddd-electoral-package-{tid}-2025-{rec.get('run_id')}"
            filas.append(_fila(tid, "electoral_fuente", "evidence.electoral_source", f"recibo={rec.get('territory_id')}", nombre, _fecha(rec), canon, "ESTRICTA"))
        # Par.
        if ev.get("prepared_source_pair"):
            rec = _json(root / ev["prepared_source_pair"]) or {}
            filas.append(_fila(tid, "par_fuentes", "evidence.prepared_source_pair", f"par={rec.get('territory_id')}", Path(ev["prepared_source_pair"]).name[:12], _fecha(rec), rec.get("territory_id") == tid, "ALIAS"))
        # Productos M06 / M08.
        for clave, rama in (("territorial_product", "producto_M06"), ("electoral_product", "producto_M08")):
            if ev.get(clave):
                rec = _json(root / ev[clave]) or {}
                filas.append(_fila(tid, rama, f"evidence.{clave}", f"recibo={rec.get('territory_id')}", str(rec.get("artifact_name") or "—"), _fecha(rec), rec.get("territory_id") == tid, "ALIAS"))
        # Datos derivados con nombre por id.
        for carpeta in ("composicion", "resultados"):
            viejo, nuevo = root / "datos" / carpeta / f"{legacy}.csv", root / "datos" / carpeta / f"{tid}.csv"
            if viejo.is_file() or nuevo.is_file():
                filas.append(_fila(tid, "composicion_datos", f"datos/{carpeta}", f"fichero={(nuevo if nuevo.is_file() else viejo).name}", "—", "—", nuevo.is_file(), "ALIAS"))
        # Registro del visor: productos con id viejo.
        propios = [p for p in visor.get("products", []) if territorio_ids.mismo_territorio(str(p.get("territory_id") or ""), tid)]
        for tipo in sorted({p.get("kind") for p in propios}):
            xs = [p for p in propios if p.get("kind") == tipo]
            viejos = [p for p in xs if p.get("territory_id") != tid]
            if viejos:
                filas.append(_fila(tid, "registro_visor", f"publicaciones_visor/{tipo}", f"{len(viejos)} de {len(xs)} con id viejo",
                                   ",".join(sorted(str(p.get("run_id")) for p in viejos)[:3]) + ("…" if len(viejos) > 3 else ""), "—", False, "ALIAS"))
    # Resultado real del resolutor de la Activación (código de esta rama) por territorio.
    plan = {p["territory_id"]: p for p in rpl.resolve(root, "Todos")["plans"] if p["territory_id"] in tabla}
    activacion = [{"territorio": t, "territorial_action": plan[t]["territorial_action"], "territorial_reason": plan[t]["territorial_reason"],
                   "electoral_action": plan[t]["electoral_action"], "electoral_reason": plan[t]["electoral_reason"]} for t in sorted(plan)]
    return {"base_commit": _base_commit(), "ramas": {k: {"politica": v[0], "motivo": v[1]} for k, v in RAMAS.items()},
            "no_verificable": NO_VERIFICABLE, "filas": filas, "activacion": activacion}


def a_markdown(d: dict) -> str:
    out = ["# Inventario de ids de territorio no canónicos por rama de reutilización (T-349)", "",
           f"Base: `{d['base_commit']}`. Generado con `python -m herramientas.inventario_ids_no_canonicos`. Solo lectura, orden determinista.", "",
           "## Ramas y política del código", "", "| Rama | Política | Motivo |", "|---|---|---|"]
    out += [f"| {k} | {v['politica']} | {v['motivo']} |" for k, v in d["ramas"].items()]
    out += ["", "## Resumen por rama (objetos no canónicos)", "", "| Rama | Objetos | No canónicos | Resultado |", "|---|---|---|---|"]
    for rama in d["ramas"]:
        fs = [f for f in d["filas"] if f["rama"] == rama]
        nc = [f for f in fs if not f["canonico"]]
        res = "RECHAZA → prepara de nuevo" if d["ramas"][rama]["politica"] == "ESTRICTA" else "ACEPTA con alias"
        out.append(f"| {rama} | {len(fs)} | {len(nc)} | {res if nc else 'sin objetos no canónicos'} |")
    out += ["", "## Activación (resultado real de `resolver_preparacion_legislatura`)", "", "| Territorio | Territorial | Motivo | Electoral | Motivo |", "|---|---|---|---|---|"]
    out += [f"| {a['territorio']} | {a['territorial_action']} | {a['territorial_reason']} | {a['electoral_action']} | {a['electoral_reason']} |" for a in d["activacion"]]
    out += ["", "## Objetos no canónicos (territorio × rama × objeto)", "", "| Territorio | Rama | Objeto | Id | Run/artefacto | Fecha | Resultado esperado |", "|---|---|---|---|---|---|---|"]
    out += [f"| {f['territorio']} | {f['rama']} | {f['objeto']} | {f['id']} | {f['run_o_artefacto']} | {f['fecha']} | {f['resultado']} |"
            for f in d["filas"] if not f["canonico"]]
    out += ["", "## No verificable desde el repo", "", d["no_verificable"], ""]
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, required=True, help="prefijo de salida (.md y .json)")
    a = ap.parse_args()
    d = construir()
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.with_suffix(".json").write_text(json.dumps(d, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    a.out.with_suffix(".md").write_text(a_markdown(d), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
