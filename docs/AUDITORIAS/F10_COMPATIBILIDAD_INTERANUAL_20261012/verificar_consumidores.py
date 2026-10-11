#!/usr/bin/env python3
"""F10 consumidores v1.0.0, 2026-10-12; estado: candidato.

Alcance: 19 consumidores offline y preservación del linaje de Extremadura.
Cambios: nueva comprobación; motivo: compatibilidad interanual sin promoción.
Origen: main@cb3927b93edc9dd67703316d3fa47d769a42dc5e; predecesor: ninguno.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
import socket
import subprocess
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]


def verify(store: Path) -> dict:
    protected = [
        "configuracion/catalogo_preparacion.yaml",
        "territorios/extremadura/evidencia/ejecuciones_completas/36472516474.json",
        "territorios/extremadura/evidencia/fuentes_territoriales/2025/"
        "70d7a964b7b837555ce03d5874c5fa04a74a80d5d724947b89fa9107684fd084/"
        "38091144559/receipt.json",
        "docs/AUDITORIAS/CIERRE_REAL_FUENTES_20261011/registro-autenticos.json",
    ]
    lineage = []
    for rel in protected:
        current = (ROOT / rel).read_bytes()
        baseline = subprocess.run(
            ["git", "show", f"cb3927b93edc9dd67703316d3fa47d769a42dc5e:{rel}"],
            cwd=ROOT, check=True, capture_output=True,
        ).stdout
        if current != baseline:
            raise ValueError(f"HISTORICAL_LINEAGE_CHANGED: {rel}")
        lineage.append({"path": rel, "sha256": hashlib.sha256(current).hexdigest()})
    verifier = runpy.run_path(str(
        ROOT / "docs/AUDITORIAS/CIERRE_FUENTES_20261011/verificar_cierre.py"
    ))
    with patch.object(socket, "create_connection", side_effect=AssertionError("OFFLINE")), \
         patch.object(socket.socket, "connect", side_effect=AssertionError("OFFLINE")), \
         patch.object(socket, "getaddrinfo", side_effect=AssertionError("OFFLINE")):
        rows = verifier["verify_national"](store)
    if len(rows) != 19 or len({row["territory_id"] for row in rows}) != 19:
        raise ValueError("CONSUMER_MATRIX_INCOMPLETE")
    return {
        "version": "1.0.0", "date": "2026-10-12", "status": "PENDING",
        "scope": "19 consumidores reales offline; ninguna promoción",
        "base_sha": "cb3927b93edc9dd67703316d3fa47d769a42dc5e",
        "historical_lineage": lineage,
        "counts": {status: sum(row["territorial_consumer"]["decision"] == status
                              for row in rows) for status in ("PASS", "BLOCKED")},
        "rows": rows,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("OUTPUT_ALREADY_EXISTS")
    result = verify(args.store)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result["counts"]))
