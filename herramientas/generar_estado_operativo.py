#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import yaml

from herramientas.catalogo_territorios import format_territory_label, load_master

START = "<!-- DDD:ESTADO:INICIO -->"
END = "<!-- DDD:ESTADO:FIN -->"
PASS_CERTIFICATIONS = {"PASS", "PASS_WITH_EXCEPTIONS", "PASS_WITH_GOVERNED_EXCEPTIONS"}


def load_yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML inválido: {path}")
    return data


def _load_receipt(root: Path, state: dict, territory_id: str, edition: str, key: str) -> dict:
    rel = str((state.get("evidence") or {}).get(key) or "")
    prefix = f"territorios/{territory_id}/evidencia/catalogo/"
    if not rel.startswith(prefix):
        return {}
    path = root / rel
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(payload, dict):
        return {}
    if str(payload.get("territory_id") or "") != territory_id or str(payload.get("edition") or "") != str(edition):
        return {}
    digest = str(payload.get("artifact_sha256") or "").removeprefix("sha256:").lower()
    if not re.fullmatch(r"[0-9a-f]{64}", digest):
        return {}
    if not payload.get("run_id") or not payload.get("artifact_name"):
        return {}
    return payload


def _prep_evidence(state: dict, territory_id: str, edition: str) -> dict:
    prep = state.get("preparation_evidence") or {}
    digest = str(prep.get("artifact_sha256") or "").removeprefix("sha256:").lower()
    artifact = str(prep.get("artifact_name") or "")
    match = re.search(r"-(\d+)$", artifact)
    try:
        run_id = int(match.group(1)) if match else int(prep.get("run_id"))
    except (TypeError, ValueError):
        run_id = None
    if not run_id or not artifact or not re.fullmatch(r"[0-9a-f]{64}", digest):
        return {}
    return {
        "territory_id": territory_id,
        "edition": str(edition),
        "run_id": run_id,
        "artifact_name": artifact,
        "artifact_sha256": digest,
        "decision": "VALIDADO",
    }


def derive(root: Path, row: dict, edition: str) -> dict:
    tid = row["territory_id"]
    name = row.get("name", tid)
    state = (row.get("editions") or {}).get(edition) or {}
    contract = bool(state.get("contract_path"))

    source = _prep_evidence(state, tid, edition)
    territorial = _load_receipt(root, state, tid, edition, "territorial_product")
    electoral_source = _load_receipt(root, state, tid, edition, "electoral_source")
    electoral_product = _load_receipt(root, state, tid, edition, "electoral_product")

    ft_ok = bool(state.get("territorial_sources_prepared") and source)
    fe_ok = bool(state.get("electoral_source_prepared") and electoral_source)
    cert = str(state.get("territorial_certification") or "")
    g_ok = bool(state.get("territorial_product_available") and territorial and cert in PASS_CERTIFICATIONS)
    re_ok = bool(state.get("electoral_product_available") and electoral_product)

    ft = "green" if ft_ok else ("yellow" if state.get("territorial_sources_prepared") or state.get("territorial_source_declaration") else ("red" if not contract else "gray"))
    fe = "green" if fe_ok else ("yellow" if state.get("electoral_source_prepared") or state.get("electoral_source_declaration") else ("red" if not contract else "gray"))
    if g_ok:
        g = "green"
    elif state.get("territorial_product_available") or state.get("production_authorization") in {"AUTHORIZED", "PREFLIGHT"}:
        g = "yellow"
    elif not contract:
        g = "red"
    else:
        g = "gray"
    if re_ok:
        re_state = "green"
    elif state.get("electoral_product_available") or (state.get("electoral_source_prepared") and state.get("territorial_product_available")):
        re_state = "yellow"
    elif not contract:
        re_state = "red"
    else:
        re_state = "gray"

    if not contract:
        status = "No incorporado"
    elif ft_ok and g_ok and fe_ok and re_ok:
        status = "Cadena completa validada"
    elif g_ok and fe_ok:
        status = "Listo para incorporar resultados electorales"
    elif g_ok:
        status = "Generación territorial validada"
    elif ft_ok:
        status = "Fuentes territoriales preparadas"
    elif state.get("production_authorization") == "PREFLIGHT":
        status = "Puerta de validación pendiente"
    elif g == "yellow" or ft == "yellow":
        status = "Validación pendiente"
    else:
        status = "Pendiente de preparación"

    cp = state.get("last_valid_checkpoint") or {}
    latest = electoral_product if re_ok else territorial if g_ok else {}
    run_id = latest.get("run_id") or cp.get("run_id")
    stage = "M08" if re_ok else "M06" if g_ok else cp.get("stage")
    return {
        "territory_id": tid, "name": name, "ft": ft, "g": g, "fe": fe, "re": re_state,
        "status": status, "certification": cert or "NOT_CERTIFIED", "run_id": run_id,
        "stage": stage, "edition": edition,
        "phase_evidence": {
            "territorial_source": source or None,
            "territorial_product": territorial or None,
            "electoral_source": electoral_source or None,
            "electoral_product": electoral_product or None,
        },
    }


def build(root: Path, edition: str) -> dict:
    catalog = load_yaml(root / "configuracion/catalogo_preparacion.yaml")
    master = {row["territory_id"]: row for row in load_master(root / "configuracion/catalogo_territorios_espana_2025.yaml")}
    rows = []
    for source_row in catalog.get("territories") or []:
        canonical = master.get(source_row["territory_id"])
        if canonical is None:
            raise ValueError(f"{source_row['territory_id']}: ausente del catálogo territorial maestro")
        row = derive(root, {**source_row, "name": canonical["name"]}, edition)
        row["autonomous_community_code_ine"] = canonical["autonomous_community_code_ine"]
        row["display_name"] = format_territory_label(canonical)
        rows.append(row)
    rows.sort(key=lambda r: r["autonomous_community_code_ine"])
    complete = [r for r in rows if all(r[k] == "green" for k in ("ft", "g", "fe", "re"))]
    territorial = [r for r in rows if r["g"] == "green"]
    ready = [r for r in rows if r["ft"] == "green" and r["g"] != "green"]
    pending = [r for r in rows if (r["g"] == "yellow" or r["ft"] == "yellow") and r not in ready]
    blocked = [r for r in rows if r not in complete and r not in ready and r not in pending and r["g"] != "green"]
    latest_pool = complete or territorial
    latest = max((r for r in latest_pool if r.get("run_id")), key=lambda r: int(r["run_id"]), default=None)

    alerts, next_actions = [], []
    for r in rows:
        if r["re"] == "yellow":
            alerts.append({"territory": r["display_name"], "territory_id": r["territory_id"], "autonomous_community_code_ine": r["autonomous_community_code_ine"], "action": "incorporar resultados electorales"})
        elif r["g"] == "yellow":
            alerts.append({"territory": r["display_name"], "territory_id": r["territory_id"], "autonomous_community_code_ine": r["autonomous_community_code_ine"], "action": "completar puerta de validación territorial"})
        elif r["ft"] == "red":
            alerts.append({"territory": r["display_name"], "territory_id": r["territory_id"], "autonomous_community_code_ine": r["autonomous_community_code_ine"], "action": "incorporación territorial pendiente"})
        if r["ft"] == "green" and r["g"] != "green":
            next_actions.append({"territory": r["display_name"], "territory_id": r["territory_id"], "autonomous_community_code_ine": r["autonomous_community_code_ine"], "action": "generar y validar distritos"})
        elif r["g"] == "green" and r["fe"] != "green":
            next_actions.append({"territory": r["display_name"], "territory_id": r["territory_id"], "autonomous_community_code_ine": r["autonomous_community_code_ine"], "action": "preparar fuentes electorales"})
        elif r["g"] == "green" and r["re"] != "green":
            next_actions.append({"territory": r["display_name"], "territory_id": r["territory_id"], "autonomous_community_code_ine": r["autonomous_community_code_ine"], "action": "incorporar resultados electorales"})

    return {
        "schema": "ddd-estado-operativo/2.1",
        "edition": edition,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_of_truth": "configuracion/catalogo_territorios_espana_2025.yaml + configuracion/catalogo_preparacion.yaml + territorios/*/evidencia/catalogo/*.json",
        "pipeline": [
            "01 · Preparación de Datos Territoriales", "Puerta de validación · 01 → 02",
            "02 · Generación de Distritos Autonómicos", "Puerta de validación · 02 → 03",
            "03 · Preparación de Resultados Electorales", "Puerta de validación · 03 → 04",
            "04 · Incorporación de Resultados Electorales", "Puerta de validación · 04 → estado operativo",
            "05 · Publicación opcional",
        ],
        "territories": rows,
        "kpis": {
            "complete": len(complete), "complete_names": [r["name"] for r in complete],
            "territorial_validated": len(territorial), "territorial_validated_names": [r["name"] for r in territorial],
            "validated": len(territorial), "validated_names": [r["name"] for r in territorial],
            "ready": len(ready), "ready_names": [r["name"] for r in ready],
            "pending": len(pending), "pending_names": [r["name"] for r in pending],
            "blocked": len(blocked), "blocked_names": [r["name"] for r in blocked],
        },
        "latest_validated": None if latest is None else {
            "territory_id": latest["territory_id"], "name": latest["name"],
            "autonomous_community_code_ine": latest["autonomous_community_code_ine"],
            "display_name": latest["display_name"], "run_id": latest["run_id"],
            "stage": latest["stage"], "certification": latest["certification"], "edition": latest["edition"],
        },
        "alerts": alerts[:8], "next_actions": next_actions[:8],
    }


ICON = {"green": "🟢", "yellow": "🟡", "red": "🔴", "gray": "⚪"}


def render_readme_block(state: dict) -> str:
    k = state["kpis"]
    rows = [
        START, "# Estado operativo del proyecto", "",
        "**Estado generado automáticamente desde el catálogo y las evidencias durables. No editar manualmente este bloque.**", "",
        f"Actualizado: {state['generated_at']} · Edición: **{state['edition']}**", "",
        "## Resumen", "", "| Indicador | Estado | Territorios |", "|---|---:|---|",
        f"| **Cadena completa validada** | 🟢 **{k['complete']}** | {' · '.join(k['complete_names']) or '—'} |",
        f"| **Generación territorial validada** | 🟢 **{k['territorial_validated']}** | {' · '.join(k['territorial_validated_names']) or '—'} |",
        f"| **Preparados para continuar** | 🔵 **{k['ready']}** | {' · '.join(k['ready_names']) or '—'} |",
        f"| **Validación pendiente** | 🟡 **{k['pending']}** | {' · '.join(k['pending_names']) or '—'} |",
        f"| **Pendientes o no incorporados** | ⚪/🔴 **{k['blocked']}** | {' · '.join(k['blocked_names']) or '—'} |",
        "", "## Estado actual por territorio", "",
        "FT = **fuentes territoriales** · G = **generación territorial** · FE = **fuentes electorales** · RE = **incorporación de resultados electorales**", "",
        "| Territorio | FT | G | FE | RE | Estado |", "|---|:---:|:---:|:---:|:---:|---|",
    ]
    for r in state["territories"]:
        rows.append(f"| **{r['display_name']}** | {ICON[r['ft']]} | {ICON[r['g']]} | {ICON[r['fe']]} | {ICON[r['re']]} | {r['status']} |")
    rows += [
        "", "## Cadena automática", "",
        "01 Preparación territorial → **Puerta de validación** → 02 Generación territorial → **Puerta de validación** → 03 Preparación electoral → **Puerta de validación** → 04 Incorporación electoral → **Puerta de validación** → 05 Publicación opcional", "",
        "**Regla estructural:** la geometría de los distritos nunca depende de los resultados electorales.", "", END,
    ]
    return "\n".join(rows)


def update_readme(path: Path, state: dict) -> None:
    text = path.read_text(encoding="utf-8")
    if START not in text or END not in text:
        raise ValueError("README sin marcadores de estado operativo")
    block = render_readme_block(state)
    path.write_text(text.split(START, 1)[0] + block + text.split(END, 1)[1], encoding="utf-8")


def write_state(state: dict, *paths: Path) -> None:
    payload = json.dumps(state, ensure_ascii=False, indent=2) + "\n"
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root-dir", type=Path, default=Path("."))
    ap.add_argument("--edition", default="2025")
    ap.add_argument("--json-output", type=Path, default=Path("orchestracion/estado_operativo.json"))
    ap.add_argument("--dashboard-output", type=Path, default=Path("publicado/dashboard/status.json"))
    ap.add_argument("--readme", type=Path, default=Path("README.md"))
    ap.add_argument("--no-readme", action="store_true")
    args = ap.parse_args()
    state = build(args.root_dir, args.edition)
    write_state(state, args.root_dir / args.json_output, args.root_dir / args.dashboard_output)
    if not args.no_readme:
        update_readme(args.root_dir / args.readme, state)
    print(json.dumps({"schema": state["schema"], "territories": len(state["territories"]), "complete": state["kpis"]["complete"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
