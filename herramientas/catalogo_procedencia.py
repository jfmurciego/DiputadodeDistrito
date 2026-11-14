#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Catálogo de procedencia único, derivado de los registros existentes (T-74).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.4.1 · FECHA: 2026-11-14 · ESTADO: candidato
CAMBIOS: 1.4.1 (T-203): _nuevo captura solo IdTerritorioDesconocido; «eleccion_declarada» distingue election_date del registro de la elección por defecto.
  1.4.0 (T-203): cada producto lleva «eleccion» (election_date, por defecto 2023-07-23); la fuente (catalogo_preparacion, ids nuevos aut/nac tras T-220) se busca
  por id nuevo o viejo (resolver_id), antes las 71 fuentes salían vacías; ids de salida sin cambio.
  1.3.1 (T-203): la constante viene de eleccion_por_defecto (ligero), no del registro (pyproj).
  1.3.0 (T-203): los avisos ORIGEN_M06/M08_NO_PUBLICADO y RESULTADOS_M08_NO_PUBLICADO comparan por (territorio, elección), no solo por territorio;
  el literal 2023-07-23 pasa a ELECCION_POR_DEFECTO (registro_publicaciones_visor). Entradas sin election_date = 2023: salida idéntica.
  1.2.0 (T-201): «vigente» se calcula por (territorio, tipo, elección), no por el run_id mayor entre elecciones; sin election_date, 2023-07-23.
  1.1.0 (T-89): sección «fuentes_secundarias» (manifiesto sha256 y contraste de nazioenbehatokia).
  1.0.0: fichero nuevo.
MOTIVO: la procedencia estaba repartida en cinco registros; este índice la junta por territorio y producto sin migrar
  a sus escritores.
ANTERIOR: legacy/herramientas/catalogo_procedencia_v1.4.0_20261114.py
QUÉ HACE: lee (solo lectura) orchestracion/publicaciones_visor.json, orchestracion/archivo_r2.json,
  datos_abiertos/INDEX.json, orchestracion/productos_publicos.json, fuentes/catalogo_oficial.yaml,
  configuracion/catalogo_preparacion.yaml, configuracion/publicaciones.yaml (DOI) y los MANIFEST de datos/composicion y
  datos/resultados, y escribe orchestracion/catalogo_procedencia.json: por territorio, la fuente (paquete territorial y
  recibo electoral) y cada producto (M06, M08, estático, ensemble, composición, resultados, datos abiertos) con sha256,
  run, blob git, copias R2, publicación y DOI. Las incoherencias se listan en el propio catálogo; no se arreglan.
  Nivel ERROR: producto publicado sin sha256 o sin copia (git, release o R2). Nivel AVISO: el resto.
Uso: python herramientas/catalogo_procedencia.py [--comprobar] [--informe] [--raiz DIR]
  --comprobar: sale con 1 si el catálogo versionado no coincide con el regenerado o hay incoherencias ERROR.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from herramientas.eleccion_por_defecto import ELECCION_POR_DEFECTO  # noqa: E402
from ddd_core.territorio_ids import IdTerritorioDesconocido, resolver_id  # noqa: E402

SALIDA = "orchestracion/catalogo_procedencia.json"
SCHEMA = "ddd.catalogo-procedencia/1.0"
ENTRADAS = {
    "visor": "orchestracion/publicaciones_visor.json",
    "r2": "orchestracion/archivo_r2.json",
    "datos_abiertos": "datos_abiertos/INDEX.json",
    "productos_publicos": "orchestracion/productos_publicos.json",
    "fuentes_oficiales": "fuentes/catalogo_oficial.yaml",
    "preparacion": "configuracion/catalogo_preparacion.yaml",
    "publicaciones": "configuracion/publicaciones.yaml",
    "composicion": "datos/composicion/MANIFEST.json",
    "resultados": "datos/resultados/MANIFEST.json",
    "fuente_secundaria": "orchestracion/fuente_nazioenbehatokia.json",
}
PUBLICADO = {"PUBLICABLE"}
_SHA_EN_RUTA = re.compile(r"/([0-9a-f]{64})/")


def _leer(raiz: Path, rel: str):
    ruta = raiz / rel
    if not ruta.exists():
        return None
    texto = ruta.read_text(encoding="utf-8")
    return yaml.safe_load(texto) if rel.endswith((".yaml", ".yml")) else json.loads(texto)


def _copias_r2(r2: dict, territorio: str, run_id, sufijo: str) -> list[dict]:
    if not run_id:
        return []
    clave = f"{territorio}/{run_id}/ddd-state-{run_id}-{sufijo}.zip"
    a = r2.get(clave)
    return [{"url": a["url"], "sha256": a.get("sha256")}] if a else []


def _fuentes(preparacion: dict | None) -> dict:
    out: dict = {}
    if not preparacion:
        return out
    edicion = str(preparacion.get("default_edition", ""))
    for t in preparacion.get("territories", []):
        ed = (t.get("editions") or {}).get(edicion) or {}
        pe = ed.get("preparation_evidence") or {}
        ev = ed.get("evidence") or {}
        territorial = None
        if pe:
            territorial = {
                "run_id": str(pe.get("run_id")),
                "package_sha256": pe.get("package_sha256"),
                "artifact_sha256": pe.get("artifact_sha256"),
                "territorial_identity_sha256": pe.get("territorial_identity_sha256"),
                "receipt_path": pe.get("receipt_path"),
                "population_year": pe.get("population_year"),
                "section_year": pe.get("section_year"),
            }
        electoral = None
        if ev.get("electoral_source"):
            m = _SHA_EN_RUTA.search(ev["electoral_source"])
            electoral = {"receipt_path": ev["electoral_source"], "identity_sha256": m.group(1) if m else None}
        out[t["territory_id"]] = {"edicion": edicion, "territorial": territorial, "electoral": electoral}
    return out


def _nuevo(tid: str) -> str:
    try:
        return resolver_id(tid)
    except IdTerritorioDesconocido:  # solo el id desconocido; cualquier otro error debe verse
        return tid


def generar(raiz: Path = ROOT) -> dict:
    d = {k: _leer(raiz, v) for k, v in ENTRADAS.items()}
    visor = d["visor"] or {"products": [], "ensembles": []}
    r2 = (d["r2"] or {}).get("artefactos", {})
    fuentes = _fuentes(d["preparacion"])
    dois = {}
    for p in (d["publicaciones"] or {}).get("publications", []) or []:
        if p.get("doi"):
            dois.setdefault(p["territory_id"], []).append(p["doi"])
    territorios: dict[str, dict] = {}
    incoherencias: list[dict] = []

    def ter(tid: str) -> dict:
        if tid not in territorios:
            f = fuentes.get(tid) or fuentes.get(_nuevo(tid)) or {}
            territorios[tid] = {
                "fuente_territorial": f.get("territorial"),
                "fuente_electoral": f.get("electoral"),
                "doi": sorted(dois.get(tid, [])) or None,
                "productos": [],
            }
        return territorios[tid]

    def inco(nivel: str, tid: str, producto: str, codigo: str, detalle: str) -> None:
        incoherencias.append({"nivel": nivel, "territorio": tid, "producto": producto, "codigo": codigo,
                              "detalle": detalle})

    # Productos del visor (M06, M08, estáticos): el vigente es el run más reciente por territorio y tipo.
    def _eleccion(p: dict) -> str:
        return str(p.get("election_date") or ELECCION_POR_DEFECTO)

    def _declarada(p: dict) -> bool:
        return bool(p.get("election_date"))

    vigente: dict[tuple, int] = {}
    for p in visor.get("products", []):
        if p.get("run_id"):
            k = (p["territory_id"], p["kind"], _eleccion(p))
            vigente[k] = max(vigente.get(k, 0), int(p["run_id"]))
    sha_m06: dict[tuple, set] = {}
    m08: dict[tuple, set] = {}
    for p in visor.get("products", []):
        tid, kind, run = p["territory_id"], p["kind"], p.get("run_id")
        producto = {"canonical_m06": "M06", "canonical_m08": "M08"}.get(kind, kind)
        if kind == "canonical_m06":
            sha_m06.setdefault((tid, _eleccion(p)), set()).add(p.get("sha256"))
        if kind == "canonical_m08":
            m08.setdefault((tid, _eleccion(p)), set()).add((str(run), p.get("blob_sha"), p.get("sha256")))
        ter(tid)["productos"].append({
            "producto": producto,
            "id": p["id"],
            "eleccion": _eleccion(p),
            "eleccion_declarada": _declarada(p),
            "run_id": str(run) if run else None,
            "vigente": bool(run) and int(run) == vigente.get((tid, kind, _eleccion(p))),
            "sha256": p.get("sha256"),
            "copia_git": {"blob_sha": p["blob_sha"], "ruta": p.get("source_path")} if p.get("blob_sha") else None,
            "copias_r2": _copias_r2(r2, tid, run, producto) if producto in ("M06", "M08") else [],
            "publicacion": p.get("publication_status"),
        })
    for e in visor.get("ensembles", []):
        ter(e["territory_id"])["productos"].append({
            "producto": "ensemble",
            "id": e["id"],
            "eleccion": _eleccion(e),
            "eleccion_declarada": _declarada(e),
            "run_id": None,
            "vigente": True,
            "sha256": e.get("sha256"),
            "copia_git": None,
            "copia_release": {"tag": e.get("release_tag"), "asset_id": e.get("asset_id")} if e.get("asset_id") else None,
            "copias_r2": [],
            "publicacion": e.get("publication_status"),
        })

    # Productos derivados versionados en git: composición, resultados ligeros y datos abiertos.
    for tid, c in sorted(((d["composicion"] or {}).get("territorios") or {}).items()):
        ter(tid)["productos"].append({
            "producto": "composicion", "id": f"composicion-{tid}", "eleccion": _eleccion(c), "eleccion_declarada": _declarada(c), "run_id": str(c.get("run_id")), "vigente": True,
            "sha256": c.get("sha256_csv"), "copia_git": {"blob_sha": None, "ruta": f"datos/composicion/{tid}.csv"},
            "copias_r2": [], "publicacion": "DATOS_ABIERTOS", "origen_sha256": c.get("sha256_m06"),
        })
        if c.get("sha256_m06") not in sha_m06.get((tid, _eleccion(c)), set()):
            inco("AVISO", tid, "composicion", "ORIGEN_M06_NO_PUBLICADO",
                 f"sha256_m06 {c.get('sha256_m06')} no es un canonical_m06 del visor")
    for tid, r in sorted(((d["resultados"] or {}).get("territorios") or {}).items()):
        ter(tid)["productos"].append({
            "producto": "resultados", "id": f"resultados-{tid}", "eleccion": _eleccion(r), "eleccion_declarada": _declarada(r), "run_id": str(r.get("run_id")), "vigente": True,
            "sha256": r.get("sha256_csv"), "copia_git": {"blob_sha": None, "ruta": f"datos/resultados/{tid}.csv"},
            "copias_r2": [], "publicacion": "DATOS_ABIERTOS", "origen_sha256": r.get("sha256_origen"),
        })
        if (str(r.get("run_id")), r.get("blob_sha"), r.get("sha256_origen")) not in m08.get((tid, _eleccion(r)), set()):
            inco("AVISO", tid, "resultados", "ORIGEN_M08_NO_PUBLICADO",
                 f"run {r.get('run_id')} / blob {r.get('blob_sha')} no es un canonical_m08 del visor")
    for tid, x in sorted(((d["datos_abiertos"] or {}).get("territorios") or {}).items()):
        g = x.get("geojson") or {}
        ter(tid)["productos"].append({
            "producto": "datos_abiertos", "id": f"datos-abiertos-{tid}", "eleccion": _eleccion(x), "eleccion_declarada": _declarada(x), "run_id": str(x.get("run_id")),
            "vigente": True, "sha256": g.get("sha256"),
            "copia_git": {"blob_sha": x.get("blob_sha"), "ruta": f"datos_abiertos/{g.get('ruta')}"},
            "copias_r2": [], "publicacion": "DATOS_ABIERTOS", "origen_sha256": x.get("sha256_origen"),
        })
        if x.get("sha256_origen") not in sha_m06.get((tid, _eleccion(x)), set()):
            inco("AVISO", tid, "datos_abiertos", "ORIGEN_M06_NO_PUBLICADO",
                 f"sha256_origen {x.get('sha256_origen')} no es un canonical_m06 del visor")
        res = x.get("resultados") or {}
        if res and (str(res.get("run_id")), res.get("blob_sha_m08")) not in {(a, b) for a, b, _ in m08.get((tid, _eleccion(x)), set())}:
            inco("AVISO", tid, "datos_abiertos", "RESULTADOS_M08_NO_PUBLICADO",
                 f"run {res.get('run_id')} / blob {res.get('blob_sha_m08')} no es un canonical_m08 del visor")

    # Registro técnico de productos públicos: debe coincidir con el estático del visor.
    estaticos = {p["territory_id"]: p for p in visor.get("products", []) if p.get("kind") == "static"}
    for p in (d["productos_publicos"] or {}).get("products", []):
        if p["id"] not in estaticos:
            inco("AVISO", p["id"], "static", "SIN_REGISTRO_VISOR", "productos_publicos.json sin producto estático")
        elif p.get("source_path") != estaticos[p["id"]].get("source_path"):
            inco("AVISO", p["id"], "static", "RUTA_DISTINTA", "source_path distinto en productos_publicos.json")

    # Reglas por producto publicado.
    for tid, t in territorios.items():
        for p in t["productos"]:
            publicado = p["publicacion"] in PUBLICADO or p["publicacion"] == "DATOS_ABIERTOS"
            if not publicado:
                continue
            if not p.get("sha256"):
                inco("ERROR", tid, p["producto"], "SIN_SHA256", p["id"])
            if not (p.get("copia_git") or p.get("copia_release") or p.get("copias_r2")):
                inco("ERROR", tid, p["producto"], "SIN_COPIA", p["id"])
            if p["producto"] in ("M06", "M08") and p["vigente"] and not p["copias_r2"]:
                inco("AVISO", tid, p["producto"], "SIN_COPIA_R2", f"run {p['run_id']}: solo copia git")
        if any(p["publicacion"] in PUBLICADO for p in t["productos"]) and not t["fuente_territorial"]:
            inco("AVISO", tid, "fuente", "SIN_FUENTE_TERRITORIAL", "sin preparation_evidence en catalogo_preparacion")
        if any(p["producto"] == "M08" and p["publicacion"] in PUBLICADO for p in t["productos"]) \
                and not t["fuente_electoral"]:
            inco("AVISO", tid, "fuente", "SIN_FUENTE_ELECTORAL", "M08 publicado sin recibo electoral en catálogo")
    for clave, a in sorted(r2.items()):
        if a.get("territorio") not in territorios:
            inco("AVISO", a.get("territorio"), "r2", "R2_SIN_PRODUCTO", clave)

    for t in territorios.values():
        t["productos"].sort(key=lambda p: (p["producto"], p["run_id"] or "", p["id"]))
    incoherencias.sort(key=lambda i: (i["nivel"], i["codigo"], i["territorio"] or "", i["producto"], i["detalle"]))
    oficiales = {k: {"proveedor": v.get("provider_abbreviation"), "url": v.get("url") or v.get("current_endpoint")}
                 for k, v in ((d["fuentes_oficiales"] or {}).get("sources") or {}).items()}
    secundarias = {}
    fs = d["fuente_secundaria"]
    if fs:
        huella = hashlib.sha256(json.dumps(fs["ficheros"], sort_keys=True).encode()).hexdigest()
        contraste = fs.get("contraste") or {}
        secundarias[fs["id"]] = {
            "proveedor": fs["proveedor"], "url": fs["url"], "rol": fs["rol"], "contenido": fs["contenido"],
            "ficheros": len(fs["ficheros"]), "sha256_ficheros": huella, "copia_r2_prefijo": fs["copia_r2_prefijo"],
            "contraste": {k: {"comparadas": v["comparadas"], "errores": len(v["errores"]),
                              "defecto_max": v["defecto_max"]} for k, v in sorted(contraste.items())},
        }
        for k, v in sorted(contraste.items()):
            if v["errores"]:
                inco("ERROR", fs["id"], k, "CONTRASTE_OFICIAL", f"{len(v['errores'])} partidos con más votos que la oficial")
        for e in fs["elecciones"]:
            if e["clave"] not in contraste:
                inco("AVISO", fs["id"], e["clave"], "SIN_CONTRASTE_OFICIAL", "sin fuente oficial local para contrastar")
        incoherencias.sort(key=lambda i: (i["nivel"], i["codigo"], i["territorio"] or "", i["producto"], i["detalle"]))
    niveles = [i["nivel"] for i in incoherencias]
    return {
        "schema": SCHEMA,
        "generado_por": "herramientas/catalogo_procedencia.py",
        "entradas": dict(sorted(ENTRADAS.items())),
        "fuentes_oficiales": oficiales,
        "fuentes_secundarias": secundarias,
        "resumen": {
            "territorios": len(territorios),
            "productos": sum(len(t["productos"]) for t in territorios.values()),
            "errores": niveles.count("ERROR"),
            "avisos": niveles.count("AVISO"),
        },
        "territorios": dict(sorted(territorios.items())),
        "incoherencias": incoherencias,
    }


def serializar(cat: dict) -> str:
    return json.dumps(cat, ensure_ascii=False, indent=1, sort_keys=False) + "\n"


def informe(cat: dict) -> str:
    r = cat["resumen"]
    lineas = [f"Catálogo de procedencia: {r['territorios']} territorios, {r['productos']} productos, "
              f"{r['errores']} errores, {r['avisos']} avisos."]
    por_codigo: dict[tuple, list] = {}
    for i in cat["incoherencias"]:
        por_codigo.setdefault((i["nivel"], i["codigo"], i["producto"]), []).append(i["territorio"])
    for (nivel, codigo, producto), ts in sorted(por_codigo.items()):
        lineas.append(f"- {nivel} {codigo} ({producto}): {len(ts)} · {', '.join(sorted(set(map(str, ts))))}")
    return "\n".join(lineas)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--raiz", type=Path, default=ROOT)
    ap.add_argument("--comprobar", action="store_true")
    ap.add_argument("--informe", action="store_true")
    a = ap.parse_args(argv)
    cat = generar(a.raiz)
    texto = serializar(cat)
    destino = a.raiz / SALIDA
    if a.informe:
        print(informe(cat))
    if a.comprobar:
        fallos = []
        if not destino.exists() or destino.read_text(encoding="utf-8") != texto:
            fallos.append(f"{SALIDA} no coincide con el regenerado: python herramientas/catalogo_procedencia.py")
        if cat["resumen"]["errores"]:
            fallos.append(f"{cat['resumen']['errores']} productos publicados sin sha256 o sin copia")
        for f in fallos:
            print(f"::error::{f}", file=sys.stderr)
        return 1 if fallos else 0
    destino.write_text(texto, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
