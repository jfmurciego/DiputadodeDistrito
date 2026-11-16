#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P74 listar (T-368, D-131): tamaño de R2 por carpeta y total frente al límite gratuito de 10 GB. Solo lectura.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Listado de R2 por carpeta
FECHA: 2026-11-16
ESTADO: candidato
CAMBIOS: 1.0.0: fichero nuevo (T-368).
USO: python herramientas/listar_r2.py   (R2_BUCKET, R2_ACCOUNT_ID y credenciales AWS_* en el entorno; solo `list-objects-v2`)
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

LIMITE = 10 * 10**9  # 10 GB gratuitos (decimales, como los factura Cloudflare)


def resumir(objetos: list[dict]) -> dict:
    """Bytes y objetos por carpeta de primer nivel (clave sin «/» = «(raíz)») y total."""
    carpetas: dict[str, list[int]] = {}
    for o in objetos:
        clave = str(o["Key"])
        c = clave.split("/", 1)[0] if "/" in clave else "(raíz)"
        fila = carpetas.setdefault(c, [0, 0])
        fila[0] += int(o["Size"])
        fila[1] += 1
    total = sum(f[0] for f in carpetas.values())
    return {"carpetas": {c: {"bytes": f[0], "objetos": f[1]} for c, f in sorted(carpetas.items(), key=lambda kv: -kv[1][0])},
            "total_bytes": total, "limite_bytes": LIMITE, "porcentaje": round(100 * total / LIMITE, 1)}


def tabla(r: dict) -> str:
    gb = lambda b: f"{b / 10**9:.3f} GB"  # noqa: E731
    filas = ["| Carpeta | Tamaño | Objetos |", "|---|---:|---:|"]
    filas += [f"| {c} | {gb(v['bytes'])} | {v['objetos']} |" for c, v in r["carpetas"].items()]
    filas.append(f"| **Total** | **{gb(r['total_bytes'])}** ({r['porcentaje']} % de 10 GB) | |")
    return "\n".join(filas)


def listar(bucket: str, cuenta: str) -> list[dict]:
    p = subprocess.run(["aws", "s3api", "list-objects-v2", "--bucket", bucket, "--endpoint-url",
                        f"https://{cuenta}.r2.cloudflarestorage.com", "--query", "Contents[].{Key:Key,Size:Size}", "--output", "json"],
                       capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"P74_LISTADO_FALLIDO: {p.stderr.strip()[:300]}")
    return json.loads(p.stdout or "null") or []


def main() -> int:
    bucket, cuenta = os.environ.get("R2_BUCKET", ""), os.environ.get("R2_ACCOUNT_ID", "")
    if not bucket or not cuenta:
        print("::error::P74_SIN_CREDENCIALES (R2_BUCKET/R2_ACCOUNT_ID)")
        return 2
    try:
        r = resumir(listar(bucket, cuenta))
    except RuntimeError as exc:
        print(f"::error::{exc}")
        return 1
    print(tabla(r))
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as fh:
            fh.write(tabla(r) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
