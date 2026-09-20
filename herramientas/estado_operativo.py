#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import yaml

START_MARKER = "<!-- DDD:ESTADO-OPERATIVO:INICIO -->"
END_MARKER = "<!-- DDD:ESTADO-OPERATIVO:FIN -->"

EMOJI = {"green": "🟢", "yellow": "🟡", "red": "🔴", "gray": "⚪"}


def load_yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML inválido: {path}")
    return data


def modern_evidence(state: dict, territory_id: str, key: str) -> bool:
    path = str((state.get("evidence") or {}).get(key) or "")
    return path.startswith(f"territorios/{territory_id}/evidencia/catalogo/")


def derive(row: dict, edition: str) -> dict:
    tid = row["territory_id"]
    name = row.get("name", tid)
    state = (row.get("editions") or {}).get(edition) or {}
    contract = bool(state.get("contract_path"))

    ft = "green" if state.get("territorial_sources_prepared") else (
        "yellow" if state.get("territorial_source_declaration") else ("red" if not contract else "gray")
    )
    fe = "green" if state.get("electoral_source_prepared") else (
        "yellow" if state.get("electoral_source_declaration") else ("red" if not contract else "gray")
    )

    product = bool(state.get("territorial_product_available"))
    fresh_product = modern_evidence(state, tid, "territorial_product")
    cert = str(state.get("territorial_certification") or "")
    if product and fresh_product and cert in {"PASS", "PASS_WITH_EXCEPTIONS", "PASS_WITH_GOVERNED_EXCEPTIONS"}:
        generation = "green"
    elif product or state.get("production_authorization") in {"AUTHORIZED", "PREFLIGHT"}:
        generation = "yellow"
    elif not contract:
        generation = "red"
    else:
        generation = "gray"

    electoral = bool(state.get("electoral_product_available"))
    fresh_electoral = modern_evidence(state, tid, "electoral_product")
    if electoral and fresh_electoral:
        results = "green"
    elif state.get("electoral_source_prepared") and product:
        results = "yellow"
    elif not contract:
        results = "red"
    else:
        results = "gray"

    if not contract:
        status = "No incorporado"
    elif all(value == "green" for value in (ft, fe, generation, results)):
        status = "Cadena completa"
    elif results == "green":
        status = "Producto electoral incorporado"
    elif generation == "green" and fe == "green":
        status = "Listo para incorporar resultados electorales"
    elif generation == "green":
        status = "Generación territorial validada"
    elif ft == "green":
        status = "Fuentes territoriales preparadas"
    elif state.get("production_authorization") == "PREFLIGHT":
        status = "Puerta de validación pendiente"
    elif generation == "yellow":
        status = "Revalidación pendiente"
    else:
        status = "Pendiente de preparación"

    cp = state.get("last_valid_checkpoint") or {}
    return {
        "territory_id": tid,
        "name": name,
        "ft": ft,
        "fe": fe,
        "g": generation,
        "re": results,
        "status": status,
        "certification": cert or "NOT_CERTIFIED",
        "run_id": cp.get("run_id"),
        "stage": cp.get("stage"),
        "edition": edition,
    }


def build(root: Path, edition: str = "2025", *, generated_at: str | None = None) -> dict:
    catalog = load_yaml(root / "configuracion/catalogo_preparacion.yaml")
    rows = [derive(row, edition) for row in catalog.get("territories") or []]
    rows.sort(key=lambda row: row["name"].casefold())

    complete = [r for r in rows if all(r[key] == "green" for key in ("ft", "fe", "g", "re"))]
    validated = [r for r in rows if r["g"] == "green"]
    ready = [r for r in rows if r["ft"] == "green" and r["g"] != "green"]
    pending = [r for r in rows if r["g"] == "yellow" and r not in ready]
    blocked = [r for r in rows if r["ft"] in {"gray", "red"} and r not in pending]

    latest_validated = max(
        (r for r in validated if r.get("run_id")),
        key=lambda r: int(r["run_id"]),
        default=None,
    )
    latest_complete = max(
        (r for r in complete if r.get("run_id")),
        key=lambda r: int(r["run_id"]),
        default=None,
    )

    alerts = []
    next_actions = []
    for r in rows:
        if r["re"] == "yellow":
            alerts.append({"territory": r["name"], "action": "incorporar resultados electorales"})
        elif r["g"] == "yellow":
            action = "completar puerta de validación" if r["status"] == "Puerta de validación pendiente" else "revalidar generación territorial"
            alerts.append({"territory": r["name"], "action": action})
        elif r["ft"] == "red":
            alerts.append({"territory": r["name"], "action": "incorporación territorial pendiente"})

        if r["ft"] == "green" and r["fe"] != "green":
            next_actions.append({"territory": r["name"], "action": "preparar fuentes electorales"})
        elif r["g"] == "green" and r["re"] != "green":
            next_actions.append({"territory": r["name"], "action": "incorporar resultados electorales"})
        elif r["g"] == "yellow":
            next_actions.append({"territory": r["name"], "action": "revalidar cadena automática"})

    def latest_payload(row: dict | None) -> dict | None:
        if row is None:
            return None
        return {
            "territory_id": row["territory_id"],
            "name": row["name"],
            "run_id": row["run_id"],
            "stage": row["stage"],
            "certification": row["certification"],
            "edition": row["edition"],
        }

    return {
        "schema": "ddd-operational-state/1.0",
        "edition": edition,
        "generated_at": generated_at or datetime.now(timezone.utc).isoformat(),
        "territories": rows,
        "kpis": {
            "complete": len(complete),
            "complete_names": [r["name"] for r in complete],
            "validated": len(validated),
            "validated_names": [r["name"] for r in validated],
            "ready": len(ready),
            "ready_names": [r["name"] for r in ready],
            "pending": len(pending),
            "pending_names": [r["name"] for r in pending],
            "blocked": len(blocked),
            "blocked_names": [r["name"] for r in blocked],
        },
        "latest_validated": latest_payload(latest_validated),
        "latest_complete": latest_payload(latest_complete),
        "alerts": alerts[:8],
        "next_actions": next_actions[:8],
    }


def render_readme_state(payload: dict) -> str:
    kpis = payload["kpis"]
    rows = payload["territories"]
    lines = [
        START_MARKER,
        "# Estado operativo del proyecto",
        "",
        "**Fuente de verdad:** catálogo y evidencias durables del repositorio. Este bloque se genera automáticamente.",
        "",
        "**Semáforo:** 🟢 completo · 🟡 parcial / pendiente de validación · 🔴 no incorporado / bloqueado · ⚪ no iniciado",
        "",
        "## Resumen",
        "",
        "| Indicador | Estado | Territorios |",
        "|---|---:|---|",
        f"| **Cadenas completas** | 🟢 **{kpis['complete']}** | {' · '.join(kpis['complete_names']) or '—'} |",
        f"| **Generación territorial validada** | 🟢 **{kpis['validated']}** | {' · '.join(kpis['validated_names']) or '—'} |",
        f"| **Preparados para continuar** | 🔵 **{kpis['ready']}** | {' · '.join(kpis['ready_names']) or '—'} |",
        f"| **Revalidación / validación pendiente** | 🟡 **{kpis['pending']}** | {' · '.join(kpis['pending_names']) or '—'} |",
        f"| **Pendientes o bloqueados** | ⚪/🔴 **{kpis['blocked']}** | {' · '.join(kpis['blocked_names']) or '—'} |",
        "",
        "## Estado actual por territorio",
        "",
        "FT = **fuentes territoriales** · FE = **fuentes electorales** · G = **generación territorial** · RE = **incorporación de resultados electorales**",
        "",
        "| Territorio | FT | FE | G | RE | Estado |",
        "|---|:---:|:---:|:---:|:---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| **{row['name']}** | {EMOJI[row['ft']]} | {EMOJI[row['fe']]} | {EMOJI[row['g']]} | {EMOJI[row['re']]} | {row['status']} |"
        )

    lines += [
        "",
        "## Cadena automática",
        "",
        "01 Preparación de Datos Territoriales → **Puerta de validación territorial** → "
        "02 Generación de Distritos Autonómicos → **Puerta de validación de generación** → "
        "03 Preparación de Resultados Electorales → **Puerta de validación electoral** → "
        "04 Incorporación de Resultados Electorales → **Puerta de validación del producto** → "
        "05 Publicación del Visor.",
        "",
        "**Regla estructural:** la geometría de los distritos nunca depende de los resultados electorales. "
        "La publicación es una operación de despliegue y no añade un estado territorial adicional.",
        "",
    ]

    latest = payload.get("latest_complete") or payload.get("latest_validated")
    lines += ["## Última cadena validada", ""]
    if latest:
        lines += [
            f"### 🟢 {latest['name']}",
            "",
            "| Métrica | Valor |",
            "|---|---|",
            f"| **Run** | {latest['run_id'] or '—'} |",
            f"| **Etapa** | {latest['stage'] or '—'} |",
            f"| **Certificación** | {latest['certification']} |",
            f"| **Edición** | {latest['edition']} |",
        ]
    else:
        lines.append("Aún no existe una cadena validada con evidencia durable.")

    lines += ["", END_MARKER]
    return "\n".join(lines) + "\n"


def update_readme(path: Path, payload: dict) -> None:
    generated = render_readme_state(payload).rstrip("\n")
    text = path.read_text(encoding="utf-8")
    if START_MARKER in text and END_MARKER in text:
        before, rest = text.split(START_MARKER, 1)
        _, after = rest.split(END_MARKER, 1)
        text = before.rstrip() + "\n\n" + generated + after
    else:
        start = text.find("# Estado operativo del proyecto")
        end = text.find("## Arquitectura")
        if start < 0 or end < 0 or end <= start:
            raise ValueError("README sin bloque operativo reconocible")
        text = text[:start].rstrip() + "\n\n" + generated + "\n\n" + text[end:]
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def write_state(
    *,
    root: Path,
    edition: str = "2025",
    canonical_path: Path | None = None,
    dashboard_path: Path | None = None,
    readme_path: Path | None = None,
    generated_at: str | None = None,
) -> dict:
    payload = build(root, edition, generated_at=generated_at)
    for path in (canonical_path, dashboard_path):
        if path is None:
            continue
        absolute = path if path.is_absolute() else root / path
        absolute.parent.mkdir(parents=True, exist_ok=True)
        absolute.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if readme_path is not None:
        absolute = readme_path if readme_path.is_absolute() else root / readme_path
        update_readme(absolute, payload)
    return payload
