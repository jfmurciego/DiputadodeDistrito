#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import urllib.request

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from herramientas.resolver_adquisicion_electoral_especial import resolve

UA = {"User-Agent": "DDD-Electoral-Official-Snapshot/1.0"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def download(url: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=120) as response:
        if getattr(response, "status", 200) != 200:
            raise RuntimeError(f"HTTP inesperado al descargar locator: {getattr(response, 'status', None)}")
        target.write_bytes(response.read())


def _prepare_siel(
    contract: dict,
    *,
    snapshot_out: Path,
    package_out: Path,
    edition: str,
    workers: int | None,
    resume: bool,
) -> dict:
    from herramientas import adquirir_siel_andalucia_2026 as siel
    from herramientas import adaptador_siel_andalucia_2026 as adapter

    cfg = contract["provider_config"]
    locator = cfg.get("locator") or {}
    expected = {
        "election_key": siel.ELECTION_KEY,
        "expected_sections": siel.EXPECTED_SECTIONS,
        "official_candidate_votes": siel.OFFICIAL_CANDIDATE_VOTES,
    }
    for key, value in expected.items():
        if int(cfg.get(key) or 0) != int(value):
            raise ValueError(f"Contrato SIEL inconsistente {key}: {cfg.get(key)!r} != {value!r}")
    if str(locator.get("sha256") or "") != siel.SECTION_LOCATOR_SHA256:
        raise ValueError("Contrato SIEL con SHA del locator distinto del extractor gobernado")
    if str(locator.get("url") or "") != siel.SECTION_LOCATOR_URL:
        raise ValueError("Contrato SIEL con URL del locator distinta del extractor gobernado")

    locator_path = snapshot_out.parent / ".ddd-official-section-locator.csv"
    if not resume or not locator_path.is_file():
        download(str(locator["url"]), locator_path)
    actual_locator_sha = sha256(locator_path)
    if actual_locator_sha != str(locator["sha256"]):
        raise ValueError("Huella del locator electoral oficial no coincide con el contrato")

    selected_workers = int(workers or cfg.get("workers") or 16)
    snapshot = siel.build(
        snapshot_out,
        selected_workers,
        section_index=locator_path,
        expected_locator_sha256=str(locator["sha256"]),
        resume=resume,
    )
    if int(snapshot.get("sections") or 0) != int(cfg["expected_sections"]):
        raise ValueError("Snapshot oficial no alcanza las secciones esperadas")
    if int(snapshot.get("candidate_votes_official") or 0) != int(cfg["official_candidate_votes"]):
        raise ValueError("Snapshot oficial no reconcilia el total electoral esperado")
    expected_snapshot = cfg.get("expected_snapshot") or {}
    expected_sections_sha = str(expected_snapshot.get("sections_sha256") or "")
    expected_cera_sha = str(expected_snapshot.get("cera_sha256") or "")
    if not expected_sections_sha or not expected_cera_sha:
        raise ValueError("Contrato oficial sin huellas gobernadas del snapshot")
    if str(snapshot.get("sections_sha256") or "") != expected_sections_sha:
        raise ValueError("Snapshot oficial de secciones difiere de la copia validada")
    if str(snapshot.get("cera_sha256") or "") != expected_cera_sha:
        raise ValueError("Snapshot oficial CERA difiere de la copia validada")

    package = adapter.build(
        snapshot_out,
        package_out,
        expected_sections_sha256=expected_sections_sha,
        expected_cera_sha256=expected_cera_sha,
        edition=str(edition),
    )
    manifest_path = package_out / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["production_eligible"] = True
    manifest["acquisition"] = {
        "kind": contract["kind"],
        "provider": contract["provider"],
        "contract_schema": contract["schema"],
        "source_status": contract["source_status"],
        "official_reference": cfg.get("official_reference"),
        "locator_sha256": actual_locator_sha,
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def prepare(
    *,
    root_dir: Path,
    election_id: str,
    territory_id: str,
    election_date: str,
    edition: str,
    snapshot_out: Path,
    package_out: Path,
    workers: int | None = None,
    resume: bool = False,
) -> dict:
    contract = resolve(
        root_dir=root_dir,
        election_id=election_id,
        territory_id=territory_id,
        election_date=election_date,
    )
    if contract is None:
        raise ValueError(f"No existe adquisición electoral especializada para {election_id}")
    provider = str(contract.get("provider") or "")
    if provider == "siel":
        return _prepare_siel(
            contract,
            snapshot_out=snapshot_out,
            package_out=package_out,
            edition=edition,
            workers=workers,
            resume=resume,
        )
    raise ValueError(f"Proveedor electoral especializado no soportado: {provider}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root-dir", type=Path, default=Path("."))
    ap.add_argument("--election-id", required=True)
    ap.add_argument("--territory-id", required=True)
    ap.add_argument("--election-date", required=True)
    ap.add_argument("--edition", required=True)
    ap.add_argument("--snapshot-out", type=Path, required=True)
    ap.add_argument("--package-out", type=Path, required=True)
    ap.add_argument("--workers", type=int)
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()
    result = prepare(
        root_dir=args.root_dir,
        election_id=args.election_id,
        territory_id=args.territory_id,
        election_date=args.election_date,
        edition=args.edition,
        snapshot_out=args.snapshot_out,
        package_out=args.package_out,
        workers=args.workers,
        resume=args.resume,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
