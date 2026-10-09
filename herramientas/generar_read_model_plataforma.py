#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import yaml

from herramientas.generar_estado_operativo import build as build_operational_state

PHASE = {"green":"READY","yellow":"PENDING","red":"BLOCKED","gray":"PENDING"}


def _yaml(path: Path) -> dict:
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def _catalog_rows(root: Path, edition: str) -> dict[str, dict]:
    data = _yaml(root / "configuracion/catalogo_preparacion.yaml")
    out = {}
    for row in data.get("territories") or []:
        if not isinstance(row, dict) or not row.get("territory_id"):
            continue
        state = (row.get("editions") or {}).get(str(edition)) or {}
        out[str(row["territory_id"])] = state if isinstance(state, dict) else {}
    return out


def _candidate_policies(root: Path) -> dict[str, dict]:
    data = _yaml(root / "configuracion/oleada_c/comunidades_interes_candidatas.yaml")
    rows = data.get("territories") or {}
    return rows if isinstance(rows, dict) else {}


def _manifest_sha(root: Path, rel: str | None) -> str | None:
    if not rel:
        return None
    manifest = root / "inputs/MANIFEST.sha256"
    if not manifest.is_file():
        return None
    rx = re.compile(r"^([0-9a-f]{64})\s+(.+)$")
    for line in manifest.read_text(encoding="utf-8").splitlines():
        m = rx.match(line.strip())
        if m and m.group(2) == rel:
            return m.group(1)
    return None


def _territory_policy(root: Path, state: dict) -> dict:
    rel = state.get("contract_path")
    if not rel:
        return {}
    return _yaml(root / str(rel))


def _community_interest(root: Path, tid: str, state: dict, candidate: dict) -> dict:
    contract = _territory_policy(root, state)
    comarcas = (((contract.get("io") or {}).get("input") or {}).get("comarcas") or {})
    gerry = (((contract.get("modulos") or {}).get("modulo_05_optimizar_distritos") or {}).get("gerrychain") or {})
    source = str(comarcas.get("path") or "") or None
    metrics = list(candidate.get("metrics") or [])
    structural = candidate.get("structural_normalization") or {}
    return {
        "available": bool(source),
        "source_enabled": bool(comarcas.get("enabled", False)),
        "semantics": str(candidate.get("semantics") or "NONE"),
        "integration_status": str(candidate.get("integration_status") or "NOT_CONFIGURED"),
        "source": source,
        "source_sha256": _manifest_sha(root, source),
        "search_weight": float(gerry["comarca_surcharge"]) if "comarca_surcharge" in gerry else None,
        "metrics": metrics,
        "structural_retention_max": float(structural["retention_max"]) if "retention_max" in structural else None,
    }


def _campaigns(root: Path) -> list[dict]:
    out = []
    folder = root / "orchestracion/campanas"
    if not folder.is_dir():
        return out
    for path in sorted(folder.glob("*.yaml")):
        data = _yaml(path)
        if data.get("schema") != "ddd-campaign/1.0":
            continue
        out.append({
            "campaign_id": str(data.get("campaign_id")),
            "environment": str(data.get("environment")),
            "status": "DEFINED",
            "territories": [str(x.get("territory_id")) for x in data.get("territories") or [] if isinstance(x, dict) and x.get("territory_id")],
        })
    return out


def _publications(root: Path) -> list[dict]:
    data = _yaml(root / "configuracion/publicaciones.yaml")
    out = []
    for row in data.get("publications") or []:
        if not isinstance(row, dict) or not row.get("territory_id"):
            continue
        out.append({
            "territory_id": str(row["territory_id"]),
            "kind": str(row.get("kind") or "unknown"),
            "status": str(row.get("status") or "UNKNOWN"),
            "source_commit": row.get("source_commit"),
            "artifact_sha256": row.get("artifact_sha256"),
            "release_tag": row.get("release_tag"),
            "doi": row.get("doi"),
            "attestation_verified": row.get("attestation_verified"),
            "osf_registration": row.get("osf_registration"),
        })
    return out


def _latest_publication(publications: list[dict], tid: str) -> dict:
    rows = [x for x in publications if x["territory_id"] == tid]
    return rows[-1] if rows else {}


def _latest_evidence(row: dict) -> dict:
    ev = row.get("phase_evidence") or {}
    return ev.get("electoral_product") or ev.get("territorial_product") or ev.get("electoral_source") or ev.get("territorial_source") or {}


def build(root: Path, edition: str) -> dict:
    operational = build_operational_state(root, edition)
    catalog = _catalog_rows(root, edition)
    candidates = _candidate_policies(root)
    publications = _publications(root)
    territories = []
    for row in operational["territories"]:
        tid = row["territory_id"]
        state = catalog.get(tid) or {}
        candidate = candidates.get(tid) or {}
        publication = _latest_publication(publications, tid)
        evidence = _latest_evidence(row)
        territories.append({
            "territory_id": tid,
            "name": row["name"],
            "edition": row["edition"],
            "phases": {
                "territorial_sources": PHASE[row["ft"]],
                "district_generation": PHASE[row["g"]],
                "electoral_sources": PHASE[row["fe"]],
                "electoral_incorporation": PHASE[row["re"]],
                "publication": "READY" if publication else "PENDING",
            },
            "community_interest": _community_interest(root, tid, state, candidate),
            "latest_run_id": int(row["run_id"]) if row.get("run_id") else None,
            "certification": row.get("certification"),
            "status": row.get("status"),
            "source_commit": evidence.get("source_commit"),
            "artifact_sha256": str(evidence.get("artifact_sha256") or "").removeprefix("sha256:") or None,
            "release_tag": publication.get("release_tag"),
            "doi": publication.get("doi"),
            "attestation_verified": publication.get("attestation_verified"),
            "osf_registration": publication.get("osf_registration"),
        })
    return {
        "schema":"ddd-platform-read-model/1.0",
        "edition":edition,
        "generated_at":datetime.now(timezone.utc).isoformat(),
        "source_of_truth":[
            "configuracion/catalogo_preparacion.yaml",
            "territorios/*/config/*_2025.yaml",
            "territorios/*/evidencia/catalogo/*.json",
            "inputs/MANIFEST.sha256",
            "configuracion/oleada_c/comunidades_interes_candidatas.yaml",
            "orchestracion/campanas/*.yaml",
            "configuracion/publicaciones.yaml",
        ],
        "territories":territories,
        "campaigns":_campaigns(root),
        "publications":publications,
    }


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--root-dir",type=Path,default=Path("."))
    ap.add_argument("--edition",default="2025")
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    payload=build(args.root_dir,args.edition)
    output=args.output if args.output.is_absolute() else args.root_dir/args.output
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"schema":payload["schema"],"territories":len(payload["territories"]),"campaigns":len(payload["campaigns"]),"publications":len(payload["publications"])},ensure_ascii=False))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
