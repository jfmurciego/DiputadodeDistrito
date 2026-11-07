#!/usr/bin/env python3
"""Huella del motor para checkpoints reutilizables (T-51).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Huella de motor, contrato y política
FECHA: 2026-11-07
ESTADO: candidato
CAMBIOS: versión inicial.
MOTIVO: «Reutilizar progreso existente» restauraba checkpoints M04/M05/M06 hechos con otro motor, otro contrato u
  otra política (causa raíz nº 1 del catálogo: Las Palmas, run 41432561787; Murcia, CHECKPOINT_RUN_ID antiguo).
QUÉ HACE: calcula una huella por capas y la compara con la guardada en el checkpoint (compatibility/motor.json):
  - capa M04: sha256 del motor M04 (modulos/04_generar_semillas.py, ddd_core/m04_*.py, configuracion/m04_engine.json),
    de las secciones del contrato materializado que gobiernan M04 (meta.territory_id, territory_contract, validation,
    modulos.modulo_04_generar_semillas) y de los population_limits del territorio en la política;
  - capa M05: la huella de herramientas/huella_checkpoint_m05.py (ENGINE_FILES y configuración M05).
  `comparar` devuelve MATCH, CHECKPOINT_ENGINE_MISMATCH (con la etapa desde la que hay que rehacer: M04 o M05 y qué
  componente cambió) o CHECKPOINT_ENGINE_UNVERIFIED (checkpoint anterior a esta huella).
NO HACE: decidir qué checkpoint se usa (lo hace seleccionar_checkpoint_productivo.py).
ANTERIOR: ninguna (fichero nuevo)

Uso: python herramientas/huella_checkpoint_motor.py --params CONTRATO [--root-dir .] [--output compatibility/motor.json]
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import yaml

from herramientas.huella_checkpoint_m05 import build_fingerprint as build_m05_fingerprint

ESQUEMA = "ddd.checkpoint-engine/1.0"
POLITICA = "configuracion/politica_generacion_territorial_2025.yaml"
M04_FICHEROS_FIJOS = ("modulos/04_generar_semillas.py", "configuracion/m04_engine.json")
M04_GLOB = "ddd_core/m04_*.py"
MATCH = "MATCH"
MISMATCH = "CHECKPOINT_ENGINE_MISMATCH"
UNVERIFIED = "CHECKPOINT_ENGINE_UNVERIFIED"


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canon(data) -> bytes:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def ficheros_motor_m04(root_dir: Path) -> list[str]:
    rels = [r for r in M04_FICHEROS_FIJOS if (root_dir / r).is_file()]
    rels += sorted(p.relative_to(root_dir).as_posix() for p in root_dir.glob(M04_GLOB) if p.is_file())
    return rels


def _limites_politica(root_dir: Path, territory_id: str | None, politica: str) -> dict | None:
    ruta = root_dir / politica
    if not territory_id or not ruta.is_file():
        return None
    datos = yaml.safe_load(ruta.read_text(encoding="utf-8")) or {}
    return ((datos.get("territories") or {}).get(territory_id) or {}).get("population_limits")


def build_fingerprint(*, params: Path, root_dir: Path = Path("."), politica: str = POLITICA) -> dict:
    root_dir = root_dir.resolve()
    params_path = params if params.is_absolute() else root_dir / params
    cfg = yaml.safe_load(params_path.read_text(encoding="utf-8")) or {}
    tid = (cfg.get("meta") or {}).get("territory_id")
    contrato_m04 = {
        "territory_id": tid,
        "territory_contract": cfg.get("territory_contract") or {},
        "validation": cfg.get("validation") or {},
        "modulo_04_generar_semillas": (cfg.get("modulos") or {}).get("modulo_04_generar_semillas") or {},
    }
    m04 = {
        "engine_files": {rel: _sha((root_dir / rel).read_bytes()) for rel in ficheros_motor_m04(root_dir)},
        "contract_sha256": _sha(_canon(contrato_m04)),
        "policy_population_limits_sha256": _sha(_canon(_limites_politica(root_dir, tid, politica))),
    }
    m04["fingerprint"] = _sha(_canon(m04))
    m05 = build_m05_fingerprint(params=params, root_dir=root_dir)
    payload = {"schema": ESQUEMA, "territory_id": tid, "m04": m04,
               "m05": {"fingerprint": m05["fingerprint"], "engine_files": m05["engine_files"],
                       "m05_config_sha256": m05["m05_config_sha256"]}}
    payload["fingerprint"] = _sha(_canon({"m04": m04["fingerprint"], "m05": m05["fingerprint"]}))
    return payload


def _diferencias_m04(guardada: dict, actual: dict) -> list[str]:
    g, a = guardada.get("m04") or {}, actual["m04"]
    out = []
    if (g.get("engine_files") or {}) != a["engine_files"]:
        cambiados = sorted(set(g.get("engine_files") or {}) ^ set(a["engine_files"]) | {
            k for k in a["engine_files"] if (g.get("engine_files") or {}).get(k) not in (None, a["engine_files"][k])})
        out.append("motor M04 (" + ", ".join(cambiados[:6]) + ")")
    if g.get("contract_sha256") != a["contract_sha256"]:
        out.append("contrato materializado")
    if g.get("policy_population_limits_sha256") != a["policy_population_limits_sha256"]:
        out.append("population_limits de la política")
    return out or ["huella M04"]


def comparar(guardada: dict | None, actual: dict, etapa: int) -> dict:
    """Compara la huella guardada en un checkpoint de la etapa `etapa` (4, 5 o 6) con la actual."""
    if etapa < 4:
        return {"status": MATCH, "detail": "checkpoint anterior a M04: sin huella de motor"}
    if not guardada or guardada.get("schema") != ESQUEMA:
        return {"status": UNVERIFIED, "invalidate_from": None,
                "detail": "checkpoint sin compatibility/motor.json (anterior a T-51): motor no verificable"}
    if (guardada.get("m04") or {}).get("fingerprint") != actual["m04"]["fingerprint"]:
        return {"status": MISMATCH, "invalidate_from": "M04", "differences": _diferencias_m04(guardada, actual),
                "detail": "M04 hecho con otro motor, contrato o política: se rehace desde M04"}
    if etapa >= 5 and (guardada.get("m05") or {}).get("fingerprint") != actual["m05"]["fingerprint"]:
        return {"status": MISMATCH, "invalidate_from": "M05", "differences": ["motor o configuración M05"],
                "detail": "M05/M06 hechos con otro motor M05: se reutiliza M04 y se rehace desde M05"}
    return {"status": MATCH, "invalidate_from": None}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--params", required=True, type=Path)
    ap.add_argument("--root-dir", default=".", type=Path)
    ap.add_argument("--output", type=Path)
    a = ap.parse_args()
    texto = json.dumps(build_fingerprint(params=a.params, root_dir=a.root_dir), ensure_ascii=False, indent=2) + "\n"
    if a.output:
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(texto, encoding="utf-8")
    else:
        print(texto, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
