"""Genera tests/fixtures/previo_r3_canonico a partir de previo_r3 (T-349, D-102). Se ejecuta una vez; el resultado se versiona.

Estado equivalente al de regenerar con id canónico: en los recibos (JSON) el `territory_id` y el id dentro de `artifact_name`
pasan del id viejo al canónico, y en el catálogo los nombres de artefacto. NO se tocan hashes de contenido, runs ni digests
(el recibo regenerado diferiría solo en ellos); los pares (sellados con pair_sha256) no se reescriben.
Uso: python tests/fixtures/_generar_previo_r3_canonico.py
"""
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from ddd_core import territorio_ids  # noqa: E402

ORIGEN = ROOT / "tests/fixtures/previo_r3"
DESTINO = ROOT / "tests/fixtures/previo_r3_canonico"
LEGACY = {t.id_legacy: k for k, t in territorio_ids.tabla().items() if t.id_legacy != k}
NOMBRE = re.compile(r"(ddd-(?:source|electoral)-package-)([a-z0-9_]+?)(-20\d\d-)")


def nombre(s):
    return NOMBRE.sub(lambda m: m.group(1) + LEGACY.get(m.group(2), m.group(2)) + m.group(3), s)


def cadenas(obj):
    """Nombres de artefacto con id viejo → canónico en cualquier cadena anidada."""
    if isinstance(obj, dict):
        return {k: cadenas(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [cadenas(x) for x in obj]
    return nombre(obj) if isinstance(obj, str) else obj


def receipt(obj):
    if isinstance(obj, dict):
        if str(obj.get("schema", "")).startswith("ddd.prepared-source-pair"):
            return obj
        out = {k: receipt(v) for k, v in obj.items()}
        for clave in ("territory_id",):
            if isinstance(out.get(clave), str) and out[clave] in LEGACY and ("run_id" in out or "artifact_name" in out or "workflow_run_id" in out or "phases" in out):
                out[clave] = LEGACY[out[clave]]
        if isinstance(out.get("identity"), dict) and out["identity"].get("territory_id") in LEGACY:
            out["identity"]["territory_id"] = LEGACY[out["identity"]["territory_id"]]
        if isinstance(out.get("artifact_name"), str):
            out["artifact_name"] = nombre(out["artifact_name"])
        if "phases" in out or "artifacts" in out:
            out = cadenas(out)
        return out
    if isinstance(obj, list):
        return [receipt(x) for x in obj]
    return obj


def sellar(obj):
    """Recalcula manifest_sha256 (mismo algoritmo que resolver_activos_durables._canonical_manifest_sha)."""
    if isinstance(obj, dict) and "manifest_sha256" in obj:
        cuerpo = {k: v for k, v in obj.items() if k != "manifest_sha256"}
        obj["manifest_sha256"] = hashlib.sha256(json.dumps(cuerpo, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return obj


if DESTINO.exists():
    shutil.rmtree(DESTINO)
files = {}
for src in sorted(ORIGEN.rglob("*")):
    if not src.is_file() or src.name == "MANIFEST.json":
        continue
    rel = src.relative_to(ORIGEN)
    dst = DESTINO / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.suffix == ".json":
        dst.write_text(json.dumps(sellar(receipt(json.loads(src.read_text(encoding="utf-8")))), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    elif src.name == "catalogo_preparacion.yaml":
        dst.write_text(nombre(src.read_text(encoding="utf-8")), encoding="utf-8")
    else:
        shutil.copy2(src, dst)
    files[rel.as_posix()] = hashlib.sha256(dst.read_bytes()).hexdigest()
(DESTINO / "MANIFEST.json").write_text(json.dumps({"origen": "tests/fixtures/previo_r3", "files": files}, indent=1, sort_keys=True) + "\n", encoding="utf-8")
