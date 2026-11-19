#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P74 listar (T-368, D-131): tamaño de R2 por carpeta y total frente al límite gratuito de 10 GB. Solo lectura.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.1.0
NOMBRE DE VERSIÓN: Listado de R2 por carpeta y duplicidades
FECHA: 2026-11-19
ESTADO: candidato
ANTERIOR: legacy/herramientas/listar_r2_v1.0.0_20261119.py
CAMBIOS: 1.1.0 (T-420): `--duplicados [--json RUTA] [--verificar-indices]`: agrupa por (ETag, tamaño) todo el bucket; grupos, sobrantes, bytes recuperables y claves (arc-e primero). Sin banderas, salida idéntica a la 1.0.0.
CAMBIOS 1.0.0: fichero nuevo (T-368).
USO: python herramientas/listar_r2.py [--duplicados [--json RUTA] [--verificar-indices]]
     (R2_BUCKET, R2_ACCOUNT_ID y credenciales AWS_* en el entorno; solo `list-objects-v2` y, con --verificar-indices, `get-object` de JSON pequeños.)
DUPLICADOS: ETag sin «-» = md5 del contenido (verificado). ETag multiparte («-N») NO es md5: se compara el sha256 de los
  índices/metadatos (*.json, INDEX*, manifiestos) y el resto queda «no_verificable». Solo lectura: no borra ni mueve nada.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import hashlib
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
                        f"https://{cuenta}.r2.cloudflarestorage.com", "--query", "Contents[].{Key:Key,Size:Size,ETag:ETag}", "--output", "json"],
                       capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"P74_LISTADO_FALLIDO: {p.stderr.strip()[:300]}")
    return json.loads(p.stdout or "null") or []


TOPE_META = 50 * 10**6  # solo se descargan metadatos de hasta 50 MB


def es_multiparte(etag: str) -> bool:
    return "-" in etag.strip('"')


def es_metadato(clave: str, tam: int) -> bool:
    b = clave.rsplit("/", 1)[-1].lower()
    return tam <= TOPE_META and (b.endswith(".json") or b.startswith("index") or "manifiesto" in b)


def carpeta_de(clave: str) -> str:
    return clave.split("/", 1)[0] if "/" in clave else "(raíz)"


def descargar_sha256(bucket: str, cuenta: str, clave: str) -> str:
    p = subprocess.run(["aws", "s3", "cp", f"s3://{bucket}/{clave}", "-", "--endpoint-url", f"https://{cuenta}.r2.cloudflarestorage.com"],
                       capture_output=True)
    if p.returncode != 0:
        raise RuntimeError(f"P74_LECTURA_FALLIDA: {clave}: {p.stderr.decode(errors='replace').strip()[:200]}")
    return hashlib.sha256(p.stdout).hexdigest()


def duplicados(objetos: list[dict], sha256_de=None) -> dict:
    """Grupos de objetos con el mismo (ETag, tamaño). `sha256_de(clave)` verifica los multiparte de metadatos (None = no verificar)."""
    grupos: dict[tuple[str, int], list[str]] = {}
    for o in objetos:
        grupos.setdefault((str(o["ETag"]).strip('"'), int(o["Size"])), []).append(str(o["Key"]))
    salida = []
    for (etag, tam), claves in grupos.items():
        if len(claves) < 2:
            continue
        claves = sorted(claves)
        if not es_multiparte(etag):
            estado, ok = "verificado_md5", True
        elif sha256_de is not None and all(es_metadato(k, tam) for k in claves):
            huellas = {k: sha256_de(k) for k in claves}
            ok = len(set(huellas.values())) == 1
            estado = "verificado_sha256" if ok else "discrepante"
        else:
            estado, ok = "no_verificable", False
        salida.append({"etag": etag, "bytes": tam, "estado": estado, "objetos": len(claves), "sobran": len(claves) - 1,
                       "bytes_recuperables": tam * (len(claves) - 1) if ok else 0,
                       "bytes_no_verificables": tam * (len(claves) - 1) if estado == "no_verificable" else 0,
                       "carpetas": sorted({carpeta_de(k) for k in claves}), "claves": claves})
    salida.sort(key=lambda g: ("arc-e" not in g["carpetas"], -(g["bytes_recuperables"] + g["bytes_no_verificables"]), g["claves"][0]))
    por_estado: dict[str, dict] = {}
    por_carpeta: dict[str, dict] = {}
    for g in salida:
        e = por_estado.setdefault(g["estado"], {"grupos": 0, "sobran": 0, "bytes": 0})
        e["grupos"] += 1
        e["sobran"] += g["sobran"]
        e["bytes"] += g["bytes"] * g["sobran"]
        for c in g["carpetas"]:
            f = por_carpeta.setdefault(c, {"grupos": 0, "bytes_recuperables": 0})
            f["grupos"] += 1
            f["bytes_recuperables"] += g["bytes_recuperables"]
    return {"grupos": salida, "grupos_total": len(salida), "sobran_total": sum(g["sobran"] for g in salida),
            "bytes_recuperables": sum(g["bytes_recuperables"] for g in salida),
            "bytes_no_verificables": sum(g["bytes_no_verificables"] for g in salida),
            "por_estado": por_estado, "por_carpeta": por_carpeta}


def resumen_duplicados(d: dict, max_grupos: int = 15) -> str:
    gb = lambda b: f"{b / 10**9:.3f} GB"  # noqa: E731
    out = [f"Duplicados: {d['grupos_total']} grupos, {d['sobran_total']} objetos sobrantes; "
           f"recuperables verificados {gb(d['bytes_recuperables'])}; no verificables {gb(d['bytes_no_verificables'])}."]
    out += [f"- {e}: {v['grupos']} grupos, {v['sobran']} sobran, {gb(v['bytes'])}" for e, v in sorted(d["por_estado"].items())]
    out += [f"- carpeta {c}: {v['grupos']} grupos, {gb(v['bytes_recuperables'])} recuperables" for c, v in
            sorted(d["por_carpeta"].items(), key=lambda kv: (kv[0] != "arc-e", -kv[1]["bytes_recuperables"]))[:10]]
    for g in d["grupos"][:max_grupos]:
        out.append(f"\n[{g['estado']}] {g['objetos']} x {gb(g['bytes'])} (etag {g['etag']})")
        out += [f"    {k}" for k in g["claves"]]
    if d["grupos_total"] > max_grupos:
        out.append(f"\n… {d['grupos_total'] - max_grupos} grupos más en el JSON.")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or '').splitlines()[0])
    ap.add_argument("--duplicados", action="store_true", help="agrupa por ETag y tamaño (solo lectura)")
    ap.add_argument("--json", default="", help="ruta del JSON de duplicados")
    ap.add_argument("--verificar-indices", action="store_true", help="descarga metadatos multiparte para comparar su sha256")
    a = ap.parse_args(argv)
    bucket, cuenta = os.environ.get("R2_BUCKET", ""), os.environ.get("R2_ACCOUNT_ID", "")
    if not bucket or not cuenta:
        print("::error::P74_SIN_CREDENCIALES (R2_BUCKET/R2_ACCOUNT_ID)")
        return 2
    try:
        objs = listar(bucket, cuenta)
        r = resumir(objs)
        d = duplicados(objs, (lambda k: descargar_sha256(bucket, cuenta, k)) if a.verificar_indices else None) if a.duplicados else None
    except RuntimeError as exc:
        print(f"::error::{exc}")
        return 1
    texto = tabla(r) + (("\n\n" + resumen_duplicados(d)) if d else "")
    print(texto)
    if d and a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump({"resumen": r, "duplicados": d}, fh, ensure_ascii=False, indent=1)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as fh:
            fh.write(texto + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
