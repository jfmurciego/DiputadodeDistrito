#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
Módulo 04 — Generar distritos iniciales
VERSIÓN: 7.5.7
NOMBRE DE VERSIÓN: Punto de entrada M04 canónico
FECHA: 2026-09-13
ESTADO: activo; composición territorial sin cambios, pendiente de certificación CI de C-08.
FUNCIÓN: ejecutar el motor M04 v7.5.1, que permite `gateway_policy: preserve_component_gateways`, y después exponer una micro-unidad residual flexible solo cuando sea matemáticamente imprescindible para M05.
ENTRADAS: grafo M03, geometría M01 y configuración territorial.
SALIDAS: K distritos iniciales, unidades DDD y diagnóstico M04.
REGLAS DURAS: provincia, K, cuotas, población y contigüidad invariantes; no se crean pasarelas; la política de componentes conserva el mínimo de puertas que mantiene conectada cada componente provincial exterior; la micro-unidad :F no cambia asignación M04.
COMPATIBILIDAD: sin `gateway_policy`, el motor usa `legacy`, preservando el comportamiento validado de Aragón/CYL.
CAMBIOS: importa estáticamente el único motor declarado y elimina la carga por ruta.
MOTIVO: hacer inequívoca y auditable la implementación M04 vigente.
ANTERIOR: legacy/modulo04/04_generar_semillas_v7.5.6.py
"""
from __future__ import annotations

import argparse
import io
import json
import sys
import zipfile
from pathlib import Path

import geopandas as gpd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from ddd_core.config import load_params_yaml, module_cfg, require, hard_limits
from ddd_core import m04_seed_engine


def load_geo(path):
    p = Path(path)
    if p.suffix.lower() == ".zip":
        with zipfile.ZipFile(p) as z:
            name = next(n for n in z.namelist() if n.lower().endswith((".geojson", ".json")) and not n.endswith("/"))
            data = json.loads(z.read(name).decode("utf-8"))
            gdf = gpd.GeoDataFrame.from_features(data.get("features", []), crs=(data.get("crs") or {}).get("properties", {}).get("name"))
            if "ddd_unit_id" in gdf.columns:
                def scalar_unit(value):
                    if isinstance(value, str):
                        return value
                    if hasattr(value, "tolist"):
                        value = value.tolist()
                    if isinstance(value, (list, tuple)) and len(value) == 1:
                        return str(value[0])
                    raise SystemExit(f"M04 v7.5.6: ddd_unit_id no escalar: {value!r}")
                gdf["ddd_unit_id"] = gdf["ddd_unit_id"].map(scalar_unit).astype(str)
            return gdf
    return gpd.read_file(p)


def write_geo(gdf, path):
    out = Path(path)
    tmp = out.parent / (out.stem.replace(".geojson", "") + ".geojson")
    gdf.to_file(tmp, driver="GeoJSON")
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.write(tmp, arcname=tmp.name)
    tmp.unlink(missing_ok=True)


def connected(nodes, adj):
    nodes = set(nodes)
    if not nodes:
        return False
    seen = {next(iter(nodes))}
    stack = list(seen)
    while stack:
        u = stack.pop()
        for v in adj.get(u, set()):
            if v in nodes and v not in seen:
                seen.add(v); stack.append(v)
    return len(seen) == len(nodes)


def expose_flexible_residual_units(params_path):
    cfg = load_params_yaml(params_path)
    s4 = module_cfg(cfg, "modulo_04_generar_semillas", "step4_seed_districts")
    s2 = module_cfg(cfg, "modulo_02_construir_adyacencias", "step2_export_edges")
    val = cfg.get("validation", {}) or {}
    ing = require(s4.get("in_graph_json"), "Falta M04 grafo")
    out = require(s4.get("out_geojson"), "Falta salida M04")
    report_path = s4.get("out_report", "")
    idf = require(s4.get("id_field"), "Falta id")
    provf = s4.get("province_field", "CPRO")
    did = "district_id"

    G = json.loads(Path(ing).read_text(encoding="utf-8"))
    pop = {str(n["id"]): int(n.get("pop", 0)) for n in G["nodes"]}
    adj = {n: set() for n in pop}
    for e in G["edges"]:
        u, v = str(e["u"]), str(e["v"])
        if u in adj and v in adj:
            adj[u].add(v); adj[v].add(u)

    bridge_nodes = set()
    for b in s2.get("topology_bridges", []) or []:
        bridge_nodes |= {str(x) for x in (b.get("u"), b.get("v")) if x is not None}

    g = load_geo(out)
    g[idf] = g[idf].astype(str)
    g[provf] = g[provf].astype(str).str.zfill(2)
    g[did] = g[did].astype(int)
    g["ddd_unit_id"] = g["ddd_unit_id"].astype(str)
    total = sum(pop.values()); K = int(g[did].nunique()); target = total / K
    _, _, _, tol = hard_limits(cfg, k=K, total_pop=total); lo, hi = target - tol, target + tol

    def dnodes(d): return set(g.loc[g[did] == d, idf])
    def dpop(d): return int(g.loc[g[did] == d, "district_pop_section"].sum())

    created = []
    for prov in sorted(g[provf].unique()):
        pids = sorted(g.loc[g[provf] == prov, did].unique())
        closed = {d for d in pids if bool(g.loc[g[did] == d, "ddd_closed_urban"].all())}
        for d in pids:
            if d in closed:
                continue
            x = g[g[did] == d]
            units = sorted(set(x["ddd_unit_id"]))
            if len(units) != 1 or not units[0].endswith(":R"):
                continue
            rid = units[0]
            other = [q for q in pids if q not in closed and q != d]
            if not other:
                continue
            other_pop = sum(dpop(q) for q in other)
            deficit = len(other) * lo - other_pop
            if deficit <= 1e-9:
                continue
            donor_pop = dpop(d)
            donor_slack = donor_pop - lo
            if donor_slack + 1e-9 < deficit:
                raise SystemExit(
                    f"M04 v7.5.1: residual {rid} bloquea provincia {prov} y no tiene slack suficiente; "
                    f"deficit={deficit:.2f} slack={donor_slack:.2f}"
                )
            donor_nodes = dnodes(d)
            candidates = []
            for n in sorted(donor_nodes - bridge_nodes):
                pn = pop[n]
                if pn < deficit - 1e-9 or pn > donor_slack + 1e-9:
                    continue
                new_donor = donor_nodes - {n}
                if not connected(new_donor, adj):
                    continue
                for q in other:
                    recv_nodes = dnodes(q)
                    if not any(nb in recv_nodes for nb in adj.get(n, set())):
                        continue
                    if dpop(q) + pn > hi + 1e-9:
                        continue
                    score = (pn - deficit, pn, str(n), int(q))
                    candidates.append((score, n, q, pn))
            if not candidates:
                raise SystemExit(
                    f"M04 v7.5.1: residual {rid} bloquea provincia {prov}; deficit={deficit:.2f} "
                    f"pero no existe sección fronteriza individual transferible"
                )
            _, n, q, pn = min(candidates, key=lambda z: z[0])
            base = rid[:-2] if rid.endswith(":R") else rid
            seq = 1
            fid = f"{base}:F{seq}"
            existing = set(g["ddd_unit_id"])
            while fid in existing:
                seq += 1; fid = f"{base}:F{seq}"
            g.loc[g[idf] == n, "ddd_unit_id"] = fid
            created.append({
                "province": prov, "source_district": int(d), "candidate_receiver": int(q),
                "residual_unit": rid, "flex_unit": fid, "sections": [str(n)],
                "population": int(pn), "locked_remainder_deficit": float(deficit),
                "donor_population_if_moved": int(donor_pop - pn),
                "receiver_population_if_moved": int(dpop(q) + pn)
            })

    for d, x in g.groupby(did):
        if not connected(set(x[idf]), adj):
            raise SystemExit(f"M04 v7.5.1: distrito {d} desconectado")

    write_geo(g, out)
    rep = json.loads(Path(report_path).read_text(encoding="utf-8")) if report_path and Path(report_path).exists() else {}
    rep["version"] = "7.5.1"
    rep["gateway_policy"] = str(s4.get("gateway_policy", "legacy"))
    rep["flexible_residual_units"] = created
    rep.setdefault("rules", {})["monolithic_residuals_may_expose_minimal_transferable_frontier_unit"] = True
    rep["rules"]["flex_units_do_not_change_m04_district_assignment"] = True
    rep["rules"]["component_gateway_policy_is_opt_in"] = True
    if report_path:
        Path(report_path).write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[Módulo 4] OK v7.5.1 gateway_policy={rep['gateway_policy']} flex_units={len(created)} outside_tol={rep.get('outside_target_tolerance')} out={out}")


def normalize_unit_property_for_ogr(path):
    """Convierte listas unitarias ddd_unit_id en escalares sin pasar por OGR."""
    p = Path(path)
    if p.suffix.lower() != ".zip":
        return 0
    with zipfile.ZipFile(p) as z:
        name = next(n for n in z.namelist() if n.lower().endswith((".geojson", ".json")) and not n.endswith("/"))
        data = json.loads(z.read(name).decode("utf-8"))
    changed = 0
    for feature in data.get("features", []):
        props = feature.setdefault("properties", {})
        value = props.get("ddd_unit_id")
        if isinstance(value, list):
            if len(value) != 1:
                raise SystemExit(f"M04 v7.5.2: ddd_unit_id multivaluado no normalizable: {value!r}")
            props["ddd_unit_id"] = str(value[0])
            changed += 1
    if changed:
        with zipfile.ZipFile(p, "w", compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr(name, json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    return changed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--params", required=True)
    args = ap.parse_args()
    m04_seed_engine.main()
    cfg = load_params_yaml(args.params)
    s4 = module_cfg(cfg, "modulo_04_generar_semillas", "step4_seed_districts")
    changed = normalize_unit_property_for_ogr(require(s4.get("out_geojson"), "Falta salida M04"))
    if changed:
        print(f"[Módulo 4] normalizados ddd_unit_id OGR-safe={changed}")
    expose_flexible_residual_units(args.params)
    changed_after = normalize_unit_property_for_ogr(require(s4.get("out_geojson"), "Falta salida M04"))
    if changed_after:
        print(f"[Módulo 4] normalización final OGR-safe={changed_after}")


if __name__ == "__main__":
    main()
