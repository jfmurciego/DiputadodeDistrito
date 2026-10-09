#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Ejecuta o reutiliza la frontera M04 configurada")
    parser.add_argument("--config", required=True)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    config_path = Path(args.config).resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    base = config_path.parent
    raw_output = Path(config["inputs"]["m04_initial_geojson"])
    output = raw_output if raw_output.is_absolute() else (base / raw_output).resolve()
    if output.is_file() and not args.force:
        print(json.dumps({"status": "REUSED", "output": str(output)}))
        return
    command = config.get("m04", {}).get("command")
    if not isinstance(command, list) or not command or not all(isinstance(item, str) for item in command):
        raise SystemExit(
            "Falta m04.command: Business debe enlazar aquí el M04 activo del repositorio"
        )
    substitutions = {
        "{territory}": config["territory_id"],
        "{output}": str(output),
        "{config}": str(config_path),
    }
    resolved = []
    for item in command:
        for token, value in substitutions.items():
            item = item.replace(token, value)
        resolved.append(item)
    output.parent.mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    run_id = str(config.get("m04", {}).get("run_id", "ensemble-base"))
    environment["DDD_RUN_ID"] = run_id
    subprocess.run(
        resolved, cwd=config_path.parents[2], check=True, shell=False, env=environment
    )
    if not output.is_file():
        raise SystemExit("M04 terminó sin crear la salida declarada")
    receipt = output.with_suffix(output.suffix + ".receipt.json")
    receipt.write_text(json.dumps({
        "schema": "ddd.m04-invocation/1.0",
        "territory_id": config["territory_id"],
        "command": resolved,
        "run_id": run_id,
        "output": str(output),
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": "CREATED", "output": str(output), "receipt": str(receipt)}))


if __name__ == "__main__":
    main()
