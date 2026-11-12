#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Histórico de generales 2011-2023 por la cadena M07/M08 sobre los distritos vigentes (T-83, paso A).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.1 · FECHA: 2026-11-12 · ESTADO: candidato
CAMBIOS: 1.0.0: fichero nuevo.
MOTIVO: D-10 y D-12 del propietario: los resultados históricos pasan por el mismo agregado electoral que 2023
  (M07/M08); la puerta 04 queda solo para publicar.
CAMBIOS 1.0.1 (T-220): ids de territorio nuevos de la tabla maestra (aut01…nac52, D-61); el id viejo se lee vía ddd_core.territorio_ids.
ANTERIOR: legacy/herramientas/historico_m07m08_v1.0.0_20261112.py
QUÉ HACE: fuera de línea (no lanza ni publica; no toca M01-M06). Por territorio y elección: (1) secciones M06 desde la
  composición publicada (`datos/composicion/<t>.csv`, sección→distrito exacto del M06) y la geometría del seccionado
  INE 2025 (las secciones 2025 recodificadas frente al M06, p. ej. 6 en Badajoz, van al distrito de mayor solape); (2) params temporal con el contrato del paquete de `reagregacion_historico.py --paquete`; (3) ejecuta
  `modulos/07_agregar_resultados_electorales.py` y `modulos/08_integrar_resultados.py` tal cual; (4) copia a
  `<salida>/<elección>/<t>/` el resumen y los votos por partido de M07, la participación por distrito y la
  reconciliación; (5) `rotacion/<t>.csv` (ganador por elección y cambios) y `MANIFEST_M07.json` con huellas y el
  contraste con el paso B (misma provincia: votos idénticos; por distrito solo difiere el redondeo).
Uso: python herramientas/historico_m07m08.py --paquete DIR --territorio nac22 --seccionado ZIP
       --distritos M06.zip [--padron ZIP] [--trabajo DIR] [--salida datos/resultados/historico]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "ddd.historico-m07m08/1.0"
CAMPOS = ("censo", "votantes", "votos_candidaturas")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def leer_composicion(path: Path) -> dict[str, tuple[str, int]]:
    """{sección: (distrito, población)} de `datos/composicion/<t>.csv`."""
    with open(path, encoding="utf-8", newline="") as f:
        return {r["seccion"]: (r["distrito"], int(r["poblacion"])) for r in csv.DictReader(f)}


def secciones_m06(composicion: dict, seccionado: Path, destino: Path, distritos: Path | None = None,
                  padron: dict | None = None) -> tuple[Path, dict, dict]:
    """GeoJSON (zip) de secciones con CUSEC_KEY, district_id y POB, como el `out_geojson` de M06. Las secciones del
    seccionado 2025 de la provincia que no están en la composición (recodificadas frente al seccionado del M06) se
    asignan al distrito M06 de mayor solape, como en el paso B. Devuelve (ruta, {sección: distrito}, informe)."""
    import geopandas as gpd
    with zipfile.ZipFile(seccionado) as z:
        shp = next(n for n in z.namelist() if n.lower().endswith(".shp"))
    provincias = {c[:2] for c in composicion}
    gdf = gpd.read_file(f"zip://{seccionado}!{shp}", columns=["CUSEC"])
    gdf = gdf[gdf["CUSEC"].str[:2].isin(provincias)].copy()
    gdf["CUSEC_KEY"] = gdf["CUSEC"].astype(str)
    faltan = sorted(set(composicion) - set(gdf["CUSEC_KEY"]))
    extra = sorted(set(gdf["CUSEC_KEY"]) - set(composicion))
    asign = {c: composicion[c][0] for c in gdf["CUSEC_KEY"] if c in composicion}
    pob = {c: composicion[c][1] for c in asign}
    if extra:
        if distritos is None:
            raise SystemExit(f"COMPOSICION_SIN_GEOMETRIA {len(faltan)}: {faltan[:5]}; 2025 sin composición {extra[:5]}")
        dist = gpd.read_file(f"zip://{distritos}" if str(distritos).endswith(".zip") else distritos).to_crs(25830)
        g25 = gdf.set_index("CUSEC_KEY").geometry.to_crs(25830)
        for c in extra:
            g = g25[c]
            areas = [(g.intersection(dg).area, str(int(d))) for d, dg in zip(dist["district_id"], dist.geometry)]
            area, d = max(areas)
            if area <= 0:
                raise SystemExit(f"SECCION_FUERA_DE_DISTRITOS {c}")
            asign[c] = d
            pob[c] = int((padron or {}).get(c) or 0)
    gdf["district_id"] = [asign[c] for c in gdf["CUSEC_KEY"]]
    gdf["POB"] = [pob[c] for c in gdf["CUSEC_KEY"]]
    gdf = gdf[["CUSEC_KEY", "district_id", "POB", "geometry"]].to_crs(4326)
    destino.parent.mkdir(parents=True, exist_ok=True)
    tmp = destino.with_suffix("")
    gdf.to_file(tmp, driver="GeoJSON")
    with zipfile.ZipFile(destino, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.write(tmp, arcname=tmp.name)
    tmp.unlink()
    informe = {"secciones": len(asign), "composicion_exacta": len(asign) - len(extra),
               "composicion_sin_seccion_2025": faltan, "secciones_2025_por_solape": {c: asign[c] for c in extra}}
    return destino, asign, informe


def params(territorio: str, trabajo: Path, secciones: Path, distritos: Path, contrato: Path) -> Path:
    import yaml
    run = f"{territorio}_historico"
    cfg = {
        "meta": {"territory_id": territorio, "run_name": run},
        "io": {"project_root": {"path": str(ROOT)}},
        "modulos": {
            "modulo_06_consolidar_distritos": {"out_geojson": str(secciones), "out_district_geojson": str(distritos),
                                               "id_field": "CUSEC_KEY", "district_field": "district_id",
                                               "pop_field": "POB"},
            "modulo_07_agregar_resultados_electorales": {
                "in_geojson": str(secciones), "section_id_field": "CUSEC_KEY", "district_field": "district_id",
                "population_field": "POB", "election_contract": str(contrato),
                "out_district_party_csv": str(trabajo / "m07_resultados_partido.csv"),
                "out_district_summary_csv": str(trabajo / "m07_resumen_electoral.csv"),
                "out_reconciliation_report": str(trabajo / "m07_reconciliacion.json")},
            "modulo_08_integrar_resultados": {
                "in_district_geojson": str(distritos),
                "in_district_summary_csv": str(trabajo / "m07_resumen_electoral.csv"),
                "out_districts_with_results_geojson": str(trabajo / "m08_distritos_resultados.geojson.zip"),
                "allow_declared_map_only_districts": False}},
    }
    p = trabajo / "params.yaml"
    p.write_text(yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return p


def ejecutar(modulo: str, p: Path) -> None:
    r = subprocess.run([sys.executable, str(ROOT / "modulos" / modulo), "--params", str(p)],
                       capture_output=True, text=True, cwd=ROOT)
    if r.returncode:
        raise SystemExit(f"{modulo} FALLA:\n{r.stdout[-2000:]}\n{r.stderr[-3000:]}")
    print(r.stdout.strip().splitlines()[-1], flush=True)


def participacion(path: Path, asign: dict) -> dict:
    """{distrito: {censo, votantes, votos_candidaturas}} sumando las secciones del paquete por la asignación."""
    out: dict = defaultdict(Counter)
    with open(path, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            d = asign[r["section_id"]]
            out[d].update({c: int(r[c]) for c in CAMPOS})
    return out


def escribir_participacion(path: Path, part: dict) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["district_id", *CAMPOS, "participacion"])
        for d in sorted(part, key=int):
            r = part[d]
            w.writerow([d, *(r[c] for c in CAMPOS),
                        round(100 * r["votantes"] / r["censo"], 4) if r["censo"] else 0.0])


def leer_resumen(path: Path) -> dict:
    with open(path, encoding="utf-8", newline="") as f:
        return {str(int(float(r["district_id"]))): r for r in csv.DictReader(f)}


def contraste_b(salida: Path, clave: str, territorio: str, resumen: dict) -> dict:
    """Paso B frente a M07: ganador y votos por distrito (el redondeo de B es por distrito y el del paquete por
    sección, así que el total provincial es idéntico y por distrito solo cabe una diferencia de redondeo)."""
    pb = salida / clave / f"{territorio}.csv"
    if not pb.exists():
        return {"estado": "sin paso B"}
    with open(pb, encoding="utf-8", newline="") as f:
        b = {r["distrito"]: r for r in csv.DictReader(f)}
    dif = {d: int(resumen[d]["total_votes"]) - int(b[d]["votos_candidaturas"]) for d in b if d in resumen}
    return {"distritos_b": len(b), "distritos_m07": len(resumen), "dif_total": sum(dif.values()),
            "dif_max_distrito": max((abs(x) for x in dif.values()), default=0),
            "ganador_distinto": sorted(d for d in b if d in resumen and b[d]["ganador"] != resumen[d]["winner_party"])}


def escribir_rotacion(path: Path, ganadores: dict) -> None:
    claves = sorted(ganadores)
    distritos = sorted({d for g in ganadores.values() for d in g}, key=int)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["district_id", *claves, "cambios"])
        for d in distritos:
            serie = [ganadores[k].get(d, "") for k in claves]
            w.writerow([d, *serie, sum(1 for a, b in zip(serie, serie[1:]) if a and b and a != b)])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--paquete", type=Path, required=True, help="raíz de `reagregacion_historico.py --paquete`")
    ap.add_argument("--territorio", required=True)
    ap.add_argument("--seccionado", type=Path, required=True, help="seccionado INE 2025 (zip)")
    ap.add_argument("--distritos", type=Path, required=True, help="M06 de distritos publicado (zip del blob)")
    ap.add_argument("--composicion", type=Path)
    ap.add_argument("--padron", type=Path, help="INE 65034 (zip): población de las secciones asignadas por solape")
    ap.add_argument("--trabajo", type=Path)
    ap.add_argument("--salida", type=Path, default=ROOT / "datos/resultados/historico")
    a = ap.parse_args(argv)
    t = a.territorio
    indice = json.loads((ROOT / "datos_abiertos/INDEX.json").read_text(encoding="utf-8"))["territorios"][t]
    if sha256(a.distritos) != indice["sha256_origen"]:
        raise SystemExit(f"HUELLA_M06_DISTINTA {a.distritos}")
    comp_path = a.composicion or ROOT / f"datos/composicion/{t}.csv"
    comp = leer_composicion(comp_path)
    trabajo = a.trabajo or ROOT / f".cache/ddd/historico/{t}"
    pad = None
    if a.padron:
        sys.path.insert(0, str(ROOT / "herramientas"))
        import equivalencia_seccionados as eqs
        pad = eqs.leer_padron(a.padron)
    secc, asign, inf_secc = secciones_m06(comp, a.seccionado, trabajo / "secciones_m06.geojson.zip", a.distritos, pad)
    ganadores, informe = {}, {}
    for carpeta in sorted(p for p in a.paquete.iterdir() if (p / t / "contrato.json").exists()):
        clave, paq = carpeta.name, carpeta / t
        tr = trabajo / clave
        tr.mkdir(parents=True, exist_ok=True)
        p = params(t, tr, secc, a.distritos, paq / "contrato.json")
        ejecutar("07_agregar_resultados_electorales.py", p)
        ejecutar("08_integrar_resultados.py", p)
        rec = json.loads((tr / "m07_reconciliacion.json").read_text(encoding="utf-8"))
        dest = a.salida / clave / t
        dest.mkdir(parents=True, exist_ok=True)
        shutil.copy(tr / "m07_resumen_electoral.csv", dest / "resumen_electoral.csv")
        shutil.copy(tr / "m07_resultados_partido.csv", dest / "resultados_partido.csv")
        escribir_participacion(dest / "participacion.csv", participacion(paq / "participacion.csv", asign))
        (dest / "reconciliacion.json").write_text(json.dumps(
            {k: rec.get(k) for k in ("status", "source_votes", "incorporated_votes", "ddd_unassigned_votes",
                                     "ddd_loss_ratio", "max_ddd_loss_ratio", "source_gap_to_definitive_votes",
                                     "source_gap_to_definitive_ratio", "errors", "warnings")},
            ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        resumen = leer_resumen(dest / "resumen_electoral.csv")
        ganadores[clave] = {d: r["winner_party"] for d, r in resumen.items()}
        informe[clave] = {"m07": rec.get("status"), "m08": "OK", "distritos": len(resumen),
                          "votos": rec.get("incorporated_votes"), "perdidos": rec.get("ddd_unassigned_votes"),
                          "hueco_oficial": rec.get("source_gap_to_definitive_ratio"),
                          "paso_b": contraste_b(a.salida, clave, t, resumen),
                          "huellas": {"contrato": sha256(paq / "contrato.json"),
                                      "secciones": sha256(paq / "secciones.csv")}}
        print(t, clave, informe[clave]["m07"], informe[clave]["paso_b"], flush=True)
    if not informe:
        raise SystemExit(f"SIN_PAQUETE {t} en {a.paquete}")
    escribir_rotacion(a.salida / "rotacion" / f"{t}.csv", ganadores)
    mp = a.salida / "MANIFEST_M07.json"
    man = json.loads(mp.read_text(encoding="utf-8")) if mp.exists() else {"schema": SCHEMA, "territorios": {}}
    man["territorios"][t] = {"distritos_m06": {"sha256": indice["sha256_origen"], "run_id": indice["run_id"]},
                             "composicion": {"path": str(comp_path.relative_to(ROOT)), "sha256": sha256(comp_path)},
                             "seccionado_2025": sha256(a.seccionado), "secciones": inf_secc,
                             "elecciones": informe}
    mp.write_text(json.dumps(man, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    ok = all(x["m07"] in {"PASS", "PASS_WITH_DECLARED_EXCEPTIONS"} and not x["paso_b"].get("ganador_distinto")
             for x in informe.values())
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
