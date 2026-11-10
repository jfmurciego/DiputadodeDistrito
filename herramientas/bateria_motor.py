#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Batería del motor (T-132): entradas reproducibles desde fuente, M04-M06 en local y matriz territorio × regla.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Batería del motor
FECHA: 2026-11-09
ESTADO: candidato
CAMBIOS: fichero nuevo.
MOTIVO: responder en minutos y sin lanzar nada si el motor vigente produce distritos válidos en los 71 territorios
  (52 circunscripciones del Congreso + 19 comunidades) y qué cambia entre versiones del motor (decisión del
  propietario: opción B, batería primero).
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE: subcomandos
  nacionales  copias nacionales oficiales con sha256 en inputs/_nacional/: seccionado INE 2023/2024/2025 (shapefile
              nacional; el 2025 sale de inputs/partes) y la tabla INE 65034 (de inputs/partes, convertida a «;» como
              la descarga en vivo y reducida a Sexo=Total y Edad=Todas las edades, que es lo único que usa el filtro).
  entradas    por territorio: adquisición oficial (herramientas/ejecutar_fuentes_workflow) por la ruta de producción,
              official_live con el seccionado del OGC del INE y la 65034 servida desde la copia nacional
              (--seccionado shapefile: verified_snapshot sobre el shapefile nacional, sin red), M01-M03 y preparar_unidades_internas, como procedimiento.sh;
              guarda en <out>/entradas/<t>/ los ficheros materializados y M01-M03 con su sha256 (ENTRADAS.json) y
              compara la huella de población y seccionado con la del contrato.
  motor       por territorio: restaura las entradas, ejecuta M04, M05 canónico (o el motor base M05 de una versión
              legacy con --m05) y M06, y la validación de producción herramientas/validar_ejecucion.py (la misma
              regla, sin reglas paralelas); compara la partición con datos/composicion/<t>.csv.
  matriz      junta los resultados en <out>/MATRIZ.csv y <out>/MATRIZ.md (territorio × regla, tiempos, semilla,
              igualdad con lo publicado y entre versiones del motor).
              Con --desde-r2 reutiliza antes el estado ddd-state-<run>-M03 archivado en R2 (orchestracion/archivo_r2.json)
              si su sha256 cuadra y lleva la identidad del contrato vigente. Solo se conserva la entrada mínima
              (M01 secciones + grafo M03, ENTRADA_MINIMA) y ENTRADAS.json con el sha256 de todo lo demás.
  archivar    sube a R2 la entrada mínima de las reconstruidas desde fuente: bateria/entradas/<t>/<huella>.zip
              (cliente de herramientas/archivar_artefactos_r2.py; R2_BUCKET y R2_ACCOUNT_ID).
USO: python herramientas/bateria_motor.py nacionales
     python herramientas/bateria_motor.py entradas --todos
     python herramientas/bateria_motor.py motor --todos [--m05 7.4.2]
     python herramientas/bateria_motor.py matriz
No escribe en el contrato ni en el motor: la declaración temporal de fuentes va a territorios/<t>/config/ (las rutas
se resuelven respecto al contrato) y se borra al terminar.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import yaml  # noqa: E402

NACIONAL = ROOT / "inputs" / "_nacional"
OUT = ROOT / "bateria"
URL_SECCIONADO = "https://www.ine.es/prodyser/cartografia/seccionado_{}.zip"
URL_65034 = "https://www.ine.es/jaxiT3/files/t/csv_bdsc/65034.csv"
EDICIONES = (2023, 2024, 2025)
REGLAS = ("K", "atomicidad", "poblacion", "contiguidad", "provincia", "municipal", "otras")
M05_BASE = {
    "7.4.4": ROOT / "ddd_core" / "m05_opt_engine_v741.py",
    "7.4.3": ROOT / "legacy" / "ddd_core" / "m05_opt_engine_v7.4.3_20261108.py",
    "7.4.2": ROOT / "legacy" / "ddd_core" / "m05_opt_engine_v7.4.2_20261108.py",
}
FECHA_ZIP = (2025, 1, 1, 0, 0, 0)
# Entrada mínima de M04 (orden del propietario, 10-11): M01 secciones con población y grafo M03; con ellas M04-M06 dan la
# misma partición (comprobado en Congreso Madrid, con unidades internas). Lo demás queda solo como sha256 en ENTRADAS.json.
ENTRADA_MINIMA = ("_m01_secciones_poblacion.geojson.zip", "_m03_grafo.json")
ARCHIVO_R2 = ROOT / "orchestracion" / "archivo_r2.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def territorios() -> list[str]:
    out = []
    for d in sorted((ROOT / "territorios").iterdir()):
        t = d.name
        if t == "congreso" or t.startswith("congreso350_"):
            continue
        if (d / "config" / f"{t}_2025.yaml").is_file() and (d / "config" / "fuentes_oficiales.yaml").is_file():
            out.append(t)
    return out


def contrato(t: str) -> Path:
    return ROOT / "territorios" / t / "config" / f"{t}_2025.yaml"


# --------------------------------------------------------------------------- nacionales
def nacionales(args) -> int:
    NACIONAL.mkdir(parents=True, exist_ok=True)
    partes = ROOT / "inputs" / "partes"
    if not (ROOT / "inputs" / "65034.csv.zip").is_file() and not (NACIONAL / "65034.csv.zip").is_file():
        subprocess.run(["bash", str(partes / "reconstruir_fuentes.sh")], check=True)
    for nombre in ("65034.csv.zip", "seccionado_2025.zip"):
        if (ROOT / "inputs" / nombre).is_file() and not (NACIONAL / nombre).is_file():
            shutil.move(str(ROOT / "inputs" / nombre), NACIONAL / nombre)
    for ed in EDICIONES:
        dest = NACIONAL / f"seccionado_{ed}.zip"
        if not dest.is_file():
            tmp = dest.with_suffix(".part")
            urllib.request.urlretrieve(URL_SECCIONADO.format(ed), tmp)
            tmp.rename(dest)
    totales = NACIONAL / "65034_totales.csv.zip"
    if not totales.is_file():
        buf = io.StringIO()
        with zipfile.ZipFile(NACIONAL / "65034.csv.zip") as zf, zf.open("65034.csv") as raw:
            reader = csv.reader(io.TextIOWrapper(raw, encoding="utf-8-sig", newline=""), delimiter="\t")
            w = csv.writer(buf, delimiter=";", lineterminator="\n")
            cab = next(reader)
            w.writerow(cab)
            i_sexo, i_edad = cab.index("Sexo"), cab.index("Edad")
            for row in reader:
                if row[i_sexo] == "Total" and row[i_edad] == "Todas las edades":
                    w.writerow(row)
        with zipfile.ZipFile(totales, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(zipfile.ZipInfo("65034.csv", FECHA_ZIP), buf.getvalue().encode("utf-8"))
    manifest = {
        "schema": "ddd.bateria-nacionales/1.0",
        "ficheros": {p.name: {"sha256": sha256(p), "bytes": p.stat().st_size} for p in sorted(NACIONAL.glob("*.zip"))},
        "origen": {"seccionado": URL_SECCIONADO, "65034": URL_65034 + " (copia en inputs/partes)"},
    }
    (NACIONAL / "NACIONALES.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(manifest["ficheros"], indent=1))
    return 0


# --------------------------------------------------------------------------- entradas
def _declaracion_temporal(t: str, nac: dict, seccionado: str) -> Path:
    base = ROOT / "territorios" / t / "config"
    d = yaml.safe_load((base / "fuentes_oficiales.yaml").read_text(encoding="utf-8"))
    terr = d.setdefault("territory", {})
    if not terr.get("section_year") or not terr.get("population_year"):
        # Declaración incompleta (p. ej. esquema 1.1): años y seccionado del contrato; queda anotado.
        meta = (_cfg(t).get("meta") or {})
        terr["population_year"] = int(meta.get("source_population_year") or terr.get("edition"))
        terr["section_year"] = int(meta.get("source_section_year") or terr.get("edition"))
        d["source_bindings"]["secciones_censales"]["materialized_path"] = f"inputs/seccionado_{terr['section_year']}.zip"
        d["_bateria_declaracion_completada_desde_contrato"] = True
    ed_sec = int(terr.get("section_year") or terr.get("edition"))
    ed_pob = int(terr.get("population_year") or terr.get("edition"))
    b = d["source_bindings"]
    tmp = base / "_bateria_fuentes.yaml"
    if seccionado == "ogc":
        tmp.write_text(yaml.safe_dump(d, allow_unicode=True, sort_keys=False), encoding="utf-8")
        return tmp
    pob = "65034_totales.csv.zip"
    sec = f"seccionado_{ed_sec}.zip"
    b["poblacion_por_sexo_y_edad"]["snapshot"] = {
        "path": f"inputs/_nacional/{pob}", "expected_sha256": nac[pob]["sha256"],
        "official_origin_url": URL_65034, "edition": ed_pob, "acquired_at": "2026-02-16"}
    b["secciones_censales"]["snapshot"] = {
        "path": f"inputs/_nacional/{sec}", "expected_sha256": nac[sec]["sha256"],
        "official_origin_url": URL_SECCIONADO.format(ed_sec), "edition": ed_sec, "acquired_at": "2026-11-09"}
    if ed_pob != ed_sec:
        origen = f"seccionado_{ed_pob}.zip"
        b["secciones_censales"]["population_sectioning_snapshot"] = {
            "path": f"inputs/_nacional/{origen}", "expected_sha256": nac[origen]["sha256"],
            "official_origin_url": URL_SECCIONADO.format(ed_pob), "edition": ed_pob, "acquired_at": "2026-11-09"}
    pol = d.setdefault("environment_policy", {})
    for env in ("development", "test", "production"):
        pol[env] = sorted(set(pol.get(env) or []) | {"verified_snapshot"})
    tmp.write_text(yaml.safe_dump(d, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return tmp


def _cfg(t: str) -> dict:
    return yaml.safe_load(contrato(t).read_text(encoding="utf-8"))


def _cache(t: str) -> Path:
    os.environ.setdefault("DDD_RUN_ID", f"bateria-{t}")
    from ddd_core.config import load_params_yaml, module_cfg
    cfg = load_params_yaml(str(contrato(t)))
    return Path(module_cfg(cfg, "modulo_03_construir_grafo", "step3_build_graph")["out_graph_json"]).parent


def _huellas_contrato(cfg: dict) -> dict:
    out = {}
    for item in ((cfg.get("generation_state") or {}).get("source_inputs") or []):
        if isinstance(item, dict) and item.get("path"):
            out[str(item["path"])] = str(item.get("sha256") or "")
    srcs = ((cfg.get("resolved_source_contract") or {}).get("sources") or {})
    for s in srcs.values():
        art = (s or {}).get("artifact") or {}
        if art.get("path"):
            out.setdefault(str(art["path"]), str(art.get("sha256") or ""))
    return out


def _run(cmd: list[str], log: Path, env: dict) -> tuple[int, float]:
    t0 = time.time()
    with open(log, "a", encoding="utf-8") as fh:
        fh.write(f"\n$ {' '.join(cmd)}\n")
        fh.flush()
        rc = subprocess.run(cmd, cwd=ROOT, stdout=fh, stderr=subprocess.STDOUT, env=env).returncode
    return rc, round(time.time() - t0, 1)


# Ruta de producción (official_live): el seccionado llega del OGC del INE como en la 00; solo la tabla 65034 se sirve
# desde la copia nacional (su descarga en vivo, de 1,6 GB, no termina en 15 min desde la sesión cloud).
ADQUISICION_OGC = (
    "import runpy,sys;from pathlib import Path;sys.path.insert(0,str(Path.cwd()))\n"
    "import herramientas.adquirir_fuentes_oficiales as a\n"
    "orig=a.live_fetch;local=Path('inputs/_nacional/65034_totales.csv.zip').read_bytes()\n"
    "a.live_fetch=lambda url,*x,**k: local if '65034' in url else orig(url,*x,**k)\n"
    "sys.argv=['ejecutar_fuentes_workflow']+sys.argv[1:]\n"
    "runpy.run_module('herramientas.ejecutar_fuentes_workflow',run_name='__main__')\n"
)


def entradas_uno(t: str, out: Path, nac: dict, seccionado: str = "ogc") -> dict:
    dest = out / "entradas" / t
    shutil.rmtree(dest, ignore_errors=True)
    dest.mkdir(parents=True)
    log = dest / "log.txt"
    env = dict(os.environ, DDD_RUN_ID=f"bateria-{t}", PYTHONHASHSEED="0")
    res: dict = {"territorio": t, "tiempos": {}}
    decl = _declaracion_temporal(t, nac, seccionado)
    res["seccionado"] = seccionado
    completada = "_bateria_declaracion_completada_desde_contrato" in decl.read_text(encoding="utf-8")
    work = out / "_trabajo" / t
    shutil.rmtree(work, ignore_errors=True)
    try:
        modo = ["official_live"] if seccionado == "ogc" else ["verified_snapshot"]
        rc, s = _run([sys.executable, "-c", ADQUISICION_OGC, "--declaration", str(decl),
                      "--working", str(work / "pkg"), "--checkpoint-out", str(work / "ckpt"),
                      "--acquisition-evidence", str(work / "ev"), "--environment", "production",
                      "--acquisition-mode", *modo, "--root-dir", str(ROOT)], log, env)
    finally:
        decl.unlink(missing_ok=True)
    res["tiempos"]["adquisicion"] = s
    res["declaracion_completada_desde_contrato"] = completada
    mat = work / "ev" / "materialized" / "inputs"
    if rc != 0 or not mat.is_dir():
        res.update(estado="FALLO_ADQUISICION", rc=rc)
        return res
    contrato_sha = _huellas_contrato(_cfg(t))
    res["fuentes"] = {}
    for f in sorted(mat.iterdir()):
        shutil.copy2(f, ROOT / "inputs" / f.name)
        shutil.copy2(f, dest / f.name)
        h = sha256(f)
        esperado = contrato_sha.get(f"inputs/{f.name}", "")
        res["fuentes"][f.name] = {"sha256": h, "contrato_sha256": esperado, "igual_contrato": h == esperado}
    cache = _cache(t)
    shutil.rmtree(cache, ignore_errors=True)
    for n, script in ((1, "01_preparar_base_territorial"), (2, "02_construir_adyacencias"), (3, "03_construir_grafo")):
        rc, s = _run([sys.executable, f"modulos/{script}.py", "--params", str(contrato(t).relative_to(ROOT))], log, env)
        res["tiempos"][f"M0{n}"] = s
        if rc != 0:
            res.update(estado=f"FALLO_M0{n}", rc=rc)
            return res
    res["estado"] = "OK"
    res["origen"] = "fuente"
    res["salidas"] = {}
    for f in sorted(cache.iterdir()):
        if f.is_file() and any(f"_m0{n}_" in f.name for n in (1, 2, 3)):
            res["salidas"][f.name] = sha256(f)
    _guardar_minima(t, cache, dest, res)
    return res


def _identidad_contrato(t: str) -> dict:
    cfg = _cfg(t)
    gs = cfg.get("generation_state") or {}
    return {"contrato": str(contrato(t).relative_to(ROOT)), "contrato_sha256": sha256(contrato(t)),
            "package_sha256": gs.get("package_sha256"), "compatibility_identity_sha256": gs.get("compatibility_identity_sha256")}


def _guardar_minima(t: str, cache: Path, dest: Path, res: dict) -> None:
    """Deja en ``dest`` solo la entrada mínima y ENTRADAS.json (sha256 de todo, identidad del contrato)."""
    for f in dest.iterdir():
        if f.is_file() and f.name not in ("log.txt",):
            f.unlink()
    res["entrada_minima"] = {}
    for suf in ENTRADA_MINIMA:
        f = next(cache.glob(f"*{suf}"), None)
        if f is None:
            res["estado"] = f"FALTA_ENTRADA_MINIMA{suf}"
            continue
        shutil.copy2(f, dest / f.name)
        res["entrada_minima"][f.name] = sha256(f)
    res["identidad_contrato"] = _identidad_contrato(t)
    (dest / "ENTRADAS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _r2_cp(origen: str, destino: str) -> None:
    ep = f"https://{os.environ['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com"
    subprocess.run(["aws", "s3", "cp", origen, destino, "--endpoint-url", ep, "--only-show-errors"], check=True)


def estados_r2(t: str) -> list[dict]:
    """Estados ddd-state-<run>-M03/M03U del territorio en orchestracion/archivo_r2.json, del más reciente al más antiguo."""
    if not ARCHIVO_R2.is_file():
        return []
    d = json.loads(ARCHIVO_R2.read_text(encoding="utf-8"))
    arts = d.get("artefactos") or {}
    arts = list(arts.values()) if isinstance(arts, dict) else arts
    sel = [a for a in arts if a.get("territorio") == t and str(a.get("artefacto", "")).endswith(("-M03", "-M03U"))]
    return sorted(sel, key=lambda a: (int(a.get("run_id") or 0), str(a["artefacto"]).endswith("-M03")), reverse=True)


def entradas_r2_uno(t: str, out: Path) -> dict | None:
    """Reutiliza la entrada mínima de un estado M03 archivado en R2 si su sha256 cuadra con archivo_r2.json y el
    estado lleva la identidad del contrato vigente (package_sha256 o compatibility_identity_sha256). None si no hay."""
    ident = _identidad_contrato(t)
    claves = [x for x in (ident["package_sha256"], ident["compatibility_identity_sha256"]) if x]
    for art in estados_r2(t):
        res: dict = {"territorio": t, "origen": "r2", "estado_r2": art["artefacto"], "url": art["url"], "tiempos": {}}
        work = out / "_trabajo" / t
        shutil.rmtree(work, ignore_errors=True)
        work.mkdir(parents=True)
        zpath = work / "estado.zip"
        t0 = time.time()
        bucket_key = art["url"].replace("r2://", "s3://", 1)
        try:
            _r2_cp(bucket_key, str(zpath))
        except (subprocess.CalledProcessError, KeyError) as exc:
            res["error"] = f"descarga: {exc}"
            continue
        res["tiempos"]["descarga_r2"] = round(time.time() - t0, 1)
        if sha256(zpath) != art.get("sha256"):
            res["error"] = "sha256 distinto de archivo_r2.json"
            continue
        with zipfile.ZipFile(zpath) as zf:
            nombres = zf.namelist()
            texto = [n for n in nombres if n.endswith((".json", ".yaml", ".yml")) and zf.getinfo(n).file_size < 5_000_000]
            vigente = any(any(c in zf.read(n).decode("utf-8", "ignore") for c in claves) for n in texto) if claves else False
            res["contrato_vigente"] = vigente
            if not vigente:
                res["error"] = "el estado no lleva la identidad del contrato vigente"
                print(f"{t}: {art['artefacto']} no corresponde al contrato vigente", flush=True)
                continue
            cache = _cache(t)
            shutil.rmtree(cache, ignore_errors=True)
            cache.mkdir(parents=True)
            for suf in ENTRADA_MINIMA:
                miembro = next((n for n in nombres if n.endswith(suf)), None)
                if miembro is None:
                    res["error"] = f"sin {suf}"
                    break
                (cache / Path(miembro).name).write_bytes(zf.read(miembro))
            else:
                dest = out / "entradas" / t
                shutil.rmtree(dest, ignore_errors=True)
                dest.mkdir(parents=True)
                res["estado"] = "OK"
                _guardar_minima(t, cache, dest, res)
                shutil.rmtree(work, ignore_errors=True)
                return res
    return None


def entradas(args) -> int:
    nac = json.loads((NACIONAL / "NACIONALES.json").read_text(encoding="utf-8"))["ficheros"]
    out = Path(args.out)
    fallos = 0
    for t in (territorios() if args.todos else args.territorios):
        r = entradas_r2_uno(t, out) if args.desde_r2 else None
        if r is not None:
            print(f"{t}: OK reutilizada de R2 {r['estado_r2']}", flush=True)
            continue
        r = entradas_uno(t, out, nac, args.seccionado)
        iguales = {k: v["igual_contrato"] for k, v in (r.get("fuentes") or {}).items()}
        print(f"{t}: {r['estado']} {r['tiempos']} huella=contrato {iguales}", flush=True)
        fallos += r["estado"] != "OK"
    return 1 if fallos else 0


# --------------------------------------------------------------------------- motor
M05_PARCHE = (
    "import importlib.util,sys;from pathlib import Path\n"
    "spec=importlib.util.spec_from_file_location('m05',Path('modulos/05_optimizar_distritos.py'))\n"
    "m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)\n"
    "m.BASE_ENGINE=Path(sys.argv[1]);sys.argv=['05_optimizar_distritos.py']+sys.argv[2:];m.main()\n"
)


def _reglas(val: dict) -> dict:
    f = [str(x) for x in val.get("failures") or []]
    r = {
        "K": not any(x.startswith(("distritos=", "geometrías distritales")) for x in f),
        "atomicidad": not any(("nulo" in x or "duplicados" in x or "no conservada" in x) for x in f),
        "poblacion": not val.get("below_floor") and not val.get("above_cap"),
        "contiguidad": not val.get("graph_disconnected"),
        "provincia": not val.get("province_crossings") and not any(x.startswith(("provincia ", "falta campo provincial")) for x in f),
        "municipal": not val.get("municipality_violations") and not any("disciplina municipal" in x for x in f),
    }
    conocidas = ("distritos=", "geometrías", "nulo", "duplicados", "no conservada", "bajo límite", "sobre límite",
                 "desconectados", "interprovinciales", "provincia ", "falta campo", "municipios con fragmentación")
    r["otras"] = not any(not any(k in x for k in conocidas) for x in f)
    return r


def composicion_publicada(t: str) -> tuple[Path | None, str | None]:
    """Composición del M06 vigente en el visor (canonical_m06 más reciente de orchestracion/publicaciones_visor.json):
    datos/composicion/runs/<t>_<run>.csv si existe; si no, la canónica datos/composicion/<t>.csv (puede ser de otro run)."""
    runs = []
    pv = ROOT / "orchestracion" / "publicaciones_visor.json"
    if pv.is_file():
        for p in json.loads(pv.read_text(encoding="utf-8")).get("products") or []:
            if p.get("kind") == "canonical_m06" and p.get("territory_id") == t and str(p.get("run_id") or "").isdigit():
                runs.append(int(p["run_id"]))
    if runs:
        f = ROOT / "datos" / "composicion" / "runs" / f"{t}_{max(runs)}.csv"
        if f.is_file():
            return f, str(max(runs))
    canon = ROOT / "datos" / "composicion" / f"{t}.csv"
    if not canon.is_file():
        return None, None
    man = ROOT / "datos" / "composicion" / "MANIFEST.json"
    run = ((json.loads(man.read_text(encoding="utf-8")).get("territorios") or {}).get(t) or {}).get("run_id") if man.is_file() else None
    return canon, str(run) if run else None


def _comparar_publicado(t: str, comp: Path) -> dict:
    pub, run = composicion_publicada(t)
    if pub is None or not comp.is_file():
        return {"publicado": pub is not None, "igual": None}
    import pandas as pd
    a = pd.read_csv(pub, dtype=str)
    b = pd.read_csv(comp, dtype=str)
    sid = "CUSEC_KEY" if "CUSEC_KEY" in b.columns else b.columns[0]
    pa = {frozenset(g["seccion"]) for _, g in a.groupby("distrito")}
    pb = {frozenset(g[sid]) for _, g in b.groupby("district_id")}
    sa, sb = set(a["seccion"]), set(b[sid])
    return {"publicado": True, "run_publicado": run, "fichero": str(pub.relative_to(ROOT)), "igual": pa == pb,
            "distritos_iguales": len(pa & pb), "distritos_publicados": len(pa),
            "secciones_solo_publicado": len(sa - sb), "secciones_solo_bateria": len(sb - sa)}


def restaurar(t: str, out: Path) -> Path | None:
    """Copia las entradas archivadas de ``t`` a su caché y a inputs/; devuelve la caché o None si faltan."""
    src = out / "entradas" / t
    if not (src / "ENTRADAS.json").is_file():
        return None
    cache = _cache(t)
    shutil.rmtree(cache, ignore_errors=True)
    cache.mkdir(parents=True)
    for f in src.iterdir():
        if "_m0" in f.name:
            shutil.copy2(f, cache / f.name)
        elif f.suffix == ".zip":
            shutil.copy2(f, ROOT / "inputs" / f.name)
    return cache


def pasos_m04(p: str, run_id: str, dest: Path) -> list:
    return [("unidades", [sys.executable, "herramientas/preparar_unidades_internas.py", "--params", p, "--run-id", run_id,
                          "--job-report", str(dest / "preparacion_unidades_internas.json")]),
            ("M04", [sys.executable, "modulos/04_generar_semillas.py", "--params", p])]


def metricas(t: str, comp: Path | None, val: dict) -> dict:
    """Desvío máximo, distritos fuera de la tolerancia del contrato y municipios partidos (de la composición M06)."""
    if comp is None or not comp.is_file() or not val.get("target_population"):
        return {}
    import pandas as pd
    c = pd.read_csv(comp, dtype={"CUMUN": str})
    pop = next(x for x in ("section_pop", "poblacion") if x in c.columns)
    tol = float(((_cfg(t).get("validation") or {}).get("target_tolerance_ratio")) or 0.12)
    dev = (c.groupby("district_id")[pop].sum() / float(val["target_population"]) - 1).abs()
    partidos = int((c.groupby("CUMUN")["district_id"].nunique() > 1).sum()) if "CUMUN" in c.columns else None
    return {"desvio_max": round(float(dev.max()), 4), "fuera_tolerancia": int((dev > tol + 1e-9).sum()),
            "tolerancia": tol, "municipios_partidos": partidos}


def validar_y_resumir(t: str, p: str, run_id: str, dest: Path, res: dict, cache: Path, log: Path, env: dict) -> dict:
    """M06 ya ejecutado: validación de producción, reglas, métricas y comparación con lo publicado."""
    rc, s = _run([sys.executable, "herramientas/validar_ejecucion.py", "--params", p, "--run-id", run_id], log, env)
    res["tiempos"]["validacion"] = s
    vpath = ROOT / "ejecuciones" / run_id / "VALIDACION.json"
    val = json.loads(vpath.read_text(encoding="utf-8")) if vpath.is_file() else {"estado": "FAIL", "failures": ["sin VALIDACION"]}
    shutil.rmtree(ROOT / "ejecuciones" / run_id, ignore_errors=True)
    (dest / "VALIDACION.json").write_text(json.dumps(val, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    res["validacion"] = val.get("estado")
    res["fallos"] = val.get("failures") or []
    res["reglas"] = _reglas(val) if val.get("estado") in ("PASS", "FAIL") and "districts_found" in val else {r: False for r in REGLAS}
    res["K"] = val.get("districts_found")
    res["K_esperado"] = val.get("expected_districts")
    for informe, clave in (("_m04_informe.json", "m04"), ("_m05_informe.json", "m05_informe")):
        f = next(cache.glob(f"*{informe}"), None)
        if f:
            d = json.loads(f.read_text(encoding="utf-8"))
            res[clave] = {k: d.get(k) for k in ("version", "engine_version", "seed", "population_baseline_status")}
    comp = next(cache.glob("*_m06_composicion_distritos.csv"), None)
    if comp:
        shutil.copy2(comp, dest / comp.name)
        res["composicion_sha256"] = sha256(comp)
    res["metricas"] = metricas(t, comp, val)
    res["publicado"] = _comparar_publicado(t, comp) if comp else {"igual": None}
    (dest / "RESULTADO.json").write_text(json.dumps(res, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return res


def motor_uno(t: str, out: Path, version: str) -> dict:
    res: dict = {"territorio": t, "m05": version, "tiempos": {}}
    cache = restaurar(t, out)
    if cache is None:
        res["estado"] = "SIN_ENTRADAS"
        return res
    dest = out / "motor" / version / t
    shutil.rmtree(dest, ignore_errors=True)
    dest.mkdir(parents=True)
    log = dest / "log.txt"
    run_id = f"bateria-{t}-{version}"
    env = dict(os.environ, DDD_RUN_ID=run_id, PYTHONHASHSEED="0", DDD_OPTIMIZATION_ALGORITHM="Canónico")
    p = str(contrato(t).relative_to(ROOT))
    pasos = pasos_m04(p, run_id, dest) + [
             ("M05", [sys.executable, "modulos/05_optimizar_distritos.py", "--params", p] if version == "7.4.4"
              else [sys.executable, "-c", M05_PARCHE, str(M05_BASE[version]), "--params", p]),
             ("M06", [sys.executable, "modulos/06_consolidar_distritos.py", "--params", p])]
    res["estado"] = "OK"
    for nombre, cmd in pasos:
        rc, s = _run(cmd, log, env)
        res["tiempos"][nombre] = s
        if rc != 0:
            res.update(estado=f"FALLO_{nombre}", rc=rc)
            break
    return validar_y_resumir(t, p, run_id, dest, res, cache, log, env)


def motor(args) -> int:
    out = Path(args.out)
    fallos = 0
    for t in (territorios() if args.todos else args.territorios):
        r = motor_uno(t, out, args.m05)
        malas = [k for k, v in (r.get("reglas") or {}).items() if not v]
        print(f"{t} [{args.m05}]: {r['estado']} validación={r.get('validacion')} FAIL={malas} "
              f"publicado={r.get('publicado', {}).get('igual')} t={sum(r['tiempos'].values()):.1f}s", flush=True)
        fallos += r.get("validacion") != "PASS"
    return 1 if fallos else 0


# --------------------------------------------------------------------------- matriz
def matriz(args) -> int:
    out = Path(args.out)
    filas = []
    versiones = sorted(p.name for p in (out / "motor").iterdir()) if (out / "motor").is_dir() else []
    por_t: dict = {}
    for v in versiones:
        for f in sorted((out / "motor" / v).glob("*/RESULTADO.json")):
            r = json.loads(f.read_text(encoding="utf-8"))
            comp = next(f.parent.glob("*_m06_composicion_distritos.csv"), None)
            if comp is not None:  # siempre contra el M06 vigente del visor, aunque el resultado sea anterior
                r["publicado"] = _comparar_publicado(r["territorio"], comp)
                if not r.get("metricas"):
                    vf = f.parent / "VALIDACION.json"
                    r["metricas"] = metricas(r["territorio"], comp, json.loads(vf.read_text(encoding="utf-8")) if vf.is_file() else {})
            por_t.setdefault(r["territorio"], {})[v] = r
    for t in sorted(por_t):
        for v, r in sorted(por_t[t].items()):
            reglas = r.get("reglas") or {}
            otras = {w: x.get("composicion_sha256") == r.get("composicion_sha256") for w, x in por_t[t].items() if w != v}
            filas.append({
                "territorio": t, "m05": v, "estado": r.get("estado"), "validacion": r.get("validacion"),
                **{f"regla_{k}": "PASS" if reglas.get(k) else "FAIL" for k in REGLAS},
                "K": r.get("K"), "K_esperado": r.get("K_esperado"),
                "semilla": (r.get("m05_informe") or {}).get("seed"),
                "tiempo_s": round(sum((r.get("tiempos") or {}).values()), 1),
                "igual_publicado": (r.get("publicado") or {}).get("igual"),
                "run_publicado": (r.get("publicado") or {}).get("run_publicado"),
                "desvio_max": (r.get("metricas") or {}).get("desvio_max"),
                "fuera_tolerancia": (r.get("metricas") or {}).get("fuera_tolerancia"),
                "municipios_partidos": (r.get("metricas") or {}).get("municipios_partidos"),
                "distritos_iguales_publicado": (r.get("publicado") or {}).get("distritos_iguales"),
                "igual_otras_versiones": json.dumps(otras, sort_keys=True),
                "fallos": " | ".join(r.get("fallos") or []),
            })
    if not filas:
        print("sin resultados")
        return 1
    with open(out / "MATRIZ.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(filas[0]))
        w.writeheader()
        w.writerows(filas)
    lineas = ["| territorio | M05 | " + " | ".join(REGLAS) + " | K | s | = publicado |", "|" + "---|" * (len(REGLAS) + 5)]
    for f in filas:
        lineas.append(f"| {f['territorio']} | {f['m05']} | " + " | ".join("✓" if f[f'regla_{k}'] == "PASS" else "✗" for k in REGLAS)
                      + f" | {f['K']}/{f['K_esperado']} | {f['tiempo_s']} | {f['igual_publicado']} |")
    for v in versiones:
        sub = [f for f in filas if f["m05"] == v]
        lineas.append(f"\n{v}: PASS {sum(f['validacion'] == 'PASS' for f in sub)}/{len(sub)}; "
                      f"igual al publicado {sum(f['igual_publicado'] is True for f in sub)}/{sum(f['igual_publicado'] is not None for f in sub)}")
    (out / "MATRIZ.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print(lineas[-len(versiones):] if versiones else "")
    return 0


# --------------------------------------------------------------------------- archivar
def archivar(args) -> int:
    """Sube a R2 la entrada mínima de cada territorio reconstruido desde fuente (las reutilizadas de R2 ya están):
    clave bateria/entradas/<territorio>/<sha256[:16] de la entrada>.zip con ENTRADAS.json + M01 + grafo M03."""
    from herramientas.archivar_artefactos_r2 import r2_cliente
    bucket, cuenta = os.environ.get("R2_BUCKET", ""), os.environ.get("R2_ACCOUNT_ID", "")
    if not bucket or not cuenta:
        print("::error::BATERIA_R2_SIN_CREDENCIALES (R2_BUCKET/R2_ACCOUNT_ID)")
        return 2
    out = Path(args.out)
    sha_remoto, subir = r2_cliente(bucket, cuenta)
    indice = {}
    for ent in sorted((out / "entradas").glob("*/ENTRADAS.json")):
        r = json.loads(ent.read_text(encoding="utf-8"))
        if r.get("origen") != "fuente" or r.get("estado") != "OK":
            continue
        huella = hashlib.sha256(json.dumps(r["entrada_minima"], sort_keys=True).encode()).hexdigest()[:16]
        paquete = out / "_trabajo" / f"{r['territorio']}-{huella}.zip"
        paquete.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(paquete, "w", zipfile.ZIP_DEFLATED) as zf:
            for nombre in ["ENTRADAS.json", *r["entrada_minima"]]:
                info = zipfile.ZipInfo(nombre, FECHA_ZIP)
                info.compress_type = zipfile.ZIP_DEFLATED
                zf.writestr(info, (ent.parent / nombre).read_bytes())
        clave = f"bateria/entradas/{r['territorio']}/{huella}.zip"
        h = sha256(paquete)
        if sha_remoto(clave) != h:
            subir(clave, paquete, h)
        indice[r["territorio"]] = {"url": f"r2://{bucket}/{clave}", "sha256": h, "bytes": paquete.stat().st_size,
                                   "entrada_minima": r["entrada_minima"], "identidad_contrato": r.get("identidad_contrato")}
    (out / "ARCHIVO_ENTRADAS.json").write_text(json.dumps(indice, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"archivadas": len(indice)}))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("nacionales")
    for nombre in ("entradas", "motor"):
        p = sub.add_parser(nombre)
        p.add_argument("territorios", nargs="*")
        p.add_argument("--todos", action="store_true")
        p.add_argument("--out", default=str(OUT))
        if nombre == "entradas":
            p.add_argument("--desde-r2", action="store_true",
                           help="reutiliza el estado M03 archivado en R2 (archivo_r2.json) si es del contrato vigente")
            p.add_argument("--seccionado", default="ogc", choices=("ogc", "shapefile"),
                           help="ogc: ruta de producción (OGC del INE); shapefile: copia nacional verificada, sin red")
        if nombre == "motor":
            p.add_argument("--m05", default="7.4.4", choices=sorted(M05_BASE))
    for nombre in ("matriz", "archivar"):
        sub.add_parser(nombre).add_argument("--out", default=str(OUT))
    a = ap.parse_args(argv)
    return {"nacionales": nacionales, "entradas": entradas, "motor": motor, "matriz": matriz, "archivar": archivar}[a.cmd](a)


if __name__ == "__main__":
    raise SystemExit(main())
