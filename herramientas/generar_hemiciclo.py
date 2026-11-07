#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Hemiciclo nacional: suma de escaños por partido de tres maneras.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-07 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE: lee los M08 registrados (distritos_resultados.csv) de las provincias nacionales completas y suma:
  (a) reparto real 2023 (D'Hondt, umbral 3 %), calculado desde los votos y contrastado escaño a escaño con el oficial;
  (b) elección anterior (generales 2019-11): solo si se aporta --generales-2019; si no, «sin fuente»;
  (c) uninominal propio: el ganador de cada distrito DDD (un escaño por distrito).
  Salida JSON y CSV con totales de «Nacional» por partido y la lista de provincias que faltan, calculada de los datos
  (sin M08, o con distritos distintos de los esperados).
FUENTES: M08: blobs inmutables de orchestracion/publicaciones_visor.json (kind=canonical_m08, el run más reciente por
  territorio congreso_*), bajados con `gh api .../git/blobs/<sha>` a una caché local y verificados con su sha256.
  Oficial 2023: ZIP por mesa del release fuente-infoelectoral-02202307 (huella de configuracion/contratos_infoelectoral.yaml),
  votos por candidatura con CERA y votos válidos (candidaturas + blancos) por provincia; el reparto es D'Hondt con barrera del 3 %.
  Verificación de (a): los escaños de las 52 circunscripciones suman los 350 y los totales por partido igualan el resultado
  oficial nacional (JEC, 30-08-2023); ver OFICIAL_2023_NACIONAL. Partidos: PSOE agrupa sus federadas (PSC, PSE-EE, PSN, PSIB, PSdeG)
  y SUMAR sus marcas territoriales.
ENTRADAS: --cache DIR (por defecto .cache/ddd/hemiciclo); --m08-dir DIR y --mesa-zip ZIP para trabajar sin red;
          --generales-2019 ZIP o CSV (opcional); --distritos CSV (province_code,k_province; por defecto el reparto N06)
Uso: python herramientas/generar_hemiciclo.py --salida DIR [--visor]
Salida: 0 si todo cuadra; 1 si (a) difiere del oficial o (c) no suma un escaño por distrito.
"""
from __future__ import annotations

import argparse
import csv
import json
import hashlib
import io
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
N06 = ROOT / "docs/ESTUDIOS/N06_DECISION_K_20261012/resultados/reparto_ddd_52.csv"
REPO = "jfmurciego/DiputadodeDistrito"
REGISTRO_VISOR = ROOT / "orchestracion/publicaciones_visor.json"
CONTRATOS = ROOT / "configuracion/contratos_infoelectoral.yaml"
MESA_RELEASE = "fuente-infoelectoral-02202307"
MESA_PREFIJO = "02202307"
UMBRAL = 0.03

# Escaños por circunscripción en 2023 (350 en total) y resultado oficial nacional (JEC, resolución de 30-08-2023).
ESCANOS_2023 = {
    "01": 4, "02": 4, "03": 12, "04": 6, "05": 3, "06": 6, "07": 8, "08": 32, "09": 4, "10": 4, "11": 9, "12": 5,
    "13": 5, "14": 6, "15": 8, "16": 3, "17": 6, "18": 7, "19": 3, "20": 6, "21": 5, "22": 3, "23": 5, "24": 4,
    "25": 4, "26": 4, "27": 4, "28": 37, "29": 11, "30": 10, "31": 5, "32": 4, "33": 7, "34": 3, "35": 8, "36": 7,
    "37": 4, "38": 7, "39": 5, "40": 3, "41": 12, "42": 2, "43": 6, "44": 3, "45": 6, "46": 15, "47": 5, "48": 8,
    "49": 3, "50": 7, "51": 1, "52": 1,
}
OFICIAL_2023_NACIONAL = {"PP": 137, "PSOE": 121, "VOX": 33, "SUMAR": 31, "ERC": 7, "JUNTS": 7, "EH Bildu": 6,
                         "EAJ-PNV": 5, "BNG": 1, "CCa": 1, "UPN": 1}
ETIQUETA = "Nacional"

# Código INE → (id de territorio, topónimo en español)
PROVINCIAS = {
    "01": ("alava", "Álava"), "02": ("albacete", "Albacete"), "03": ("alicante", "Alicante"),
    "04": ("almeria", "Almería"), "05": ("avila", "Ávila"), "06": ("badajoz", "Badajoz"),
    "07": ("baleares", "Baleares"), "08": ("barcelona", "Barcelona"), "09": ("burgos", "Burgos"),
    "10": ("caceres", "Cáceres"), "11": ("cadiz", "Cádiz"), "12": ("castellon", "Castellón"),
    "13": ("ciudad_real", "Ciudad Real"), "14": ("cordoba", "Córdoba"), "15": ("la_coruna", "La Coruña"),
    "16": ("cuenca", "Cuenca"), "17": ("gerona", "Gerona"), "18": ("granada", "Granada"),
    "19": ("guadalajara", "Guadalajara"), "20": ("guipuzcoa", "Guipúzcoa"), "21": ("huelva", "Huelva"),
    "22": ("huesca", "Huesca"), "23": ("jaen", "Jaén"), "24": ("leon", "León"), "25": ("lerida", "Lérida"),
    "26": ("la_rioja", "La Rioja"), "27": ("lugo", "Lugo"), "28": ("madrid", "Madrid"),
    "29": ("malaga", "Málaga"), "30": ("murcia", "Murcia"), "31": ("navarra", "Navarra"),
    "32": ("orense", "Orense"), "33": ("asturias", "Asturias"), "34": ("palencia", "Palencia"),
    "35": ("las_palmas", "Las Palmas"), "36": ("pontevedra", "Pontevedra"), "37": ("salamanca", "Salamanca"),
    "38": ("santa_cruz_de_tenerife", "Santa Cruz de Tenerife"), "39": ("cantabria", "Cantabria"),
    "40": ("segovia", "Segovia"), "41": ("sevilla", "Sevilla"), "42": ("soria", "Soria"),
    "43": ("tarragona", "Tarragona"), "44": ("teruel", "Teruel"), "45": ("toledo", "Toledo"),
    "46": ("valencia", "Valencia"), "47": ("valladolid", "Valladolid"), "48": ("vizcaya", "Vizcaya"),
    "49": ("zamora", "Zamora"), "50": ("zaragoza", "Zaragoza"), "51": ("ceuta", "Ceuta"), "52": ("melilla", "Melilla"),
}
_POR_ID = {f"congreso_{v[0]}": k for k, v in PROVINCIAS.items()}


def codigo(valor: str) -> str:
    v = valor.strip()
    if v in PROVINCIAS:
        return v
    if v.zfill(2) in PROVINCIAS:
        return v.zfill(2)
    if v in _POR_ID:
        return _POR_ID[v]
    raise ValueError(f"provincia no reconocida: {valor!r}")


def grupo(etiqueta: str) -> str:
    """Partido nacional de una etiqueta de candidatura (federadas del PSOE y marcas de SUMAR se agrupan)."""
    e = etiqueta.strip()
    if "PSOE" in e or e in ("PSC", "PSE-EE"):
        return "PSOE"
    if "SUMAR" in e.upper():
        return "SUMAR"
    return {"JxCAT - JUNTS": "JUNTS", "B.N.G.": "BNG", "U.P.N.": "UPN"}.get(e, e)


def dhondt(votos: dict[str, int], escanos: int, votos_validos: int | None = None) -> dict[str, int]:
    """D'Hondt con barrera del 3 % de los votos válidos de la provincia. Desempate: más votos, luego nombre."""
    total = votos_validos if votos_validos else sum(votos.values())
    aptos = {p: v for p, v in votos.items() if v >= UMBRAL * total and v > 0}
    res = {p: 0 for p in aptos}
    for _ in range(escanos):
        p = max(aptos, key=lambda q: (aptos[q] / (res[q] + 1), aptos[q], q))
        res[p] += 1
    return {p: n for p, n in res.items() if n}


def _sumar(d: dict[str, int], por_grupo: bool = True) -> dict[str, int]:
    out: dict[str, int] = {}
    for p, n in d.items():
        k = grupo(p) if por_grupo else p
        out[k] = out.get(k, 0) + n
    return out


def _sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _gh_raw(ruta: str, accept: str) -> bytes:
    r = subprocess.run(["gh", "api", ruta, "-H", f"Accept: {accept}"], capture_output=True)
    if r.returncode:
        raise RuntimeError(f"gh api {ruta}: {r.stderr.decode(errors='replace')[:200]}")
    return r.stdout


def mesa_zip(cache: Path) -> Path:
    """ZIP oficial por mesa (espejo en release del repositorio), con la huella del contrato Infoelectoral."""
    ruta = cache / "02202307_MESA.zip"
    esperado = next(iter(__import__("re").findall(r"source_sha256: ([0-9a-f]{64})", CONTRATOS.read_text(encoding="utf-8"))))
    if not ruta.exists():
        cache.mkdir(parents=True, exist_ok=True)
        a = json.loads(_gh_raw(f"repos/{REPO}/releases/tags/{MESA_RELEASE}", "application/json"))["assets"][0]["id"]
        ruta.write_bytes(_gh_raw(f"repos/{REPO}/releases/assets/{a}", "application/octet-stream"))
    if _sha256(ruta.read_bytes()) != esperado:
        raise ValueError(f"SHA-256 del ZIP Infoelectoral no coincide con el contrato: {ruta}")
    return ruta


def leer_mesa_zip(ruta: Path) -> dict[str, dict]:
    """provincia → {'votos': {siglas: v}, 'validos': candidaturas+blancos} con CERA; una candidatura por código."""
    def lineas(z, nombre):
        with z.open(nombre) as fh:
            for raw in fh:
                s = raw.decode("iso-8859-1").rstrip("\r\n")
                if s.startswith(MESA_PREFIJO):
                    yield s
    out: dict[str, dict] = {}
    with zipfile.ZipFile(ruta) as z:
        nombres = {s[8:14]: s[14:64].strip() for s in lineas(z, "03022307.DAT")}
        for s in lineas(z, "09022307.DAT"):
            d = out.setdefault(s[11:13], {"votos": {}, "validos": 0, "_c": {}})
            d["validos"] += int(s[65:72] or 0) + int(s[79:86] or 0)  # blancos + candidaturas
        for s in lineas(z, "10022307.DAT"):
            d = out.setdefault(s[11:13], {"votos": {}, "validos": 0, "_c": {}})
            d["_c"][s[23:29]] = d["_c"].get(s[23:29], 0) + int(s[29:36] or 0)
    for d in out.values():
        d["votos"] = {f"{nombres[c]}#{c}": v for c, v in d.pop("_c").items()}
    return out


def etiqueta(clave: str) -> str:
    return clave.split("#")[0]


def reparto_2023(oficial: dict[str, dict]) -> dict[str, dict[str, int]]:
    """provincia → {partido nacional: escaños} (D'Hondt por candidatura, luego agrupado)."""
    res = {}
    for cod, d in oficial.items():
        if cod not in ESCANOS_2023:  # filas de ámbito superior (p. ej. 99)
            continue
        r = dhondt(d["votos"], ESCANOS_2023[cod], d["validos"])
        res[cod] = _sumar({etiqueta(k): n for k, n in r.items()})
    return res


def verificar_oficial(reparto: dict[str, dict[str, int]]) -> list[str]:
    """Contrasta con el resultado oficial: escaños por circunscripción y totales nacionales por partido."""
    err = [f"{PROVINCIAS[c][1]}: {sum(r.values())} escaños != {ESCANOS_2023[c]}" for c, r in reparto.items()
           if sum(r.values()) != ESCANOS_2023[c]]
    err += [f"falta la circunscripción {PROVINCIAS[c][1]}" for c in PROVINCIAS if c not in reparto]
    tot = _sumar(reparto_flat(reparto), por_grupo=False)
    if tot != OFICIAL_2023_NACIONAL:
        err.append(f"totales 2023 {tot} != oficiales {OFICIAL_2023_NACIONAL}")
    return err


def reparto_flat(reparto):
    out: dict[str, int] = {}
    for r in reparto.values():
        for p, n in r.items():
            out[p] = out.get(p, 0) + n
    return out


def leer_distritos(ruta: Path) -> dict[str, int]:
    with open(ruta, encoding="utf-8", newline="") as f:
        return {r["province_code"].zfill(2): int(r["k_province"]) for r in csv.DictReader(f)}


def ganadores_geojson(datos: bytes) -> list[str]:
    z = zipfile.ZipFile(io.BytesIO(datos))
    gj = json.loads(z.read(next(n for n in z.namelist() if n.endswith(".geojson"))))
    filas = sorted(gj["features"], key=lambda f: int(f["properties"]["district_id"]))
    return [f["properties"]["winner_party"] for f in filas]


def cargar_m08(cache: Path, m08_dir: Path | None = None) -> tuple[dict[str, list[str]], dict[str, str]]:
    """provincia → ganadores por distrito y provincia → run, de los blobs del registro del visor (o de m08_dir)."""
    prods: dict[str, dict] = {}
    for p in json.loads(REGISTRO_VISOR.read_text(encoding="utf-8"))["products"]:
        if p.get("kind") == "canonical_m08" and str(p.get("territory_id", "")).startswith("congreso_"):
            t = p["territory_id"]
            if t not in prods or int(p["run_id"]) > int(prods[t]["run_id"]):
                prods[t] = p
    gan, runs = {}, {}
    for t, p in sorted(prods.items()):
        if t not in _POR_ID:
            continue
        f = (m08_dir or cache) / f"{t}_{p['run_id']}.zip"
        if not f.exists():
            if m08_dir:
                continue
            cache.mkdir(parents=True, exist_ok=True)
            f.write_bytes(_gh_raw(f"repos/{REPO}/git/blobs/{p['blob_sha']}", "application/vnd.github.raw"))
        datos = f.read_bytes()
        if _sha256(datos) != p["sha256"]:
            raise ValueError(f"SHA-256 del M08 de {t} no coincide con el registro: {f}")
        gan[_POR_ID[t]] = ganadores_geojson(datos)
        runs[_POR_ID[t]] = p["run_id"]
    return gan, runs


def generar(ganadores: dict[str, list[str]], reparto: dict[str, dict[str, int]], esperados: dict[str, int],
            b: dict[str, dict[str, int]] | None = None, runs: dict[str, str] | None = None) -> dict:
    provincias, faltan, errores = [], [], []
    for cod, (slug, nombre) in PROVINCIAS.items():
        k, g = esperados.get(cod), ganadores.get(cod)
        if g is None:
            faltan.append({"codigo": cod, "provincia": nombre, "motivo": "sin M08 registrado"})
        elif k is not None and len(g) != k:
            faltan.append({"codigo": cod, "provincia": nombre, "motivo": f"M08 con {len(g)} distritos de {k} esperados"})
        elif cod not in reparto:
            faltan.append({"codigo": cod, "provincia": nombre, "motivo": "sin resultados oficiales 2023"})
        else:
            c = _sumar({p: g.count(p) for p in set(g)})
            if sum(c.values()) != len(g):
                errores.append(f"{nombre}: (c) no suma un escaño por distrito")
            provincias.append({"codigo": cod, "provincia": nombre, "distritos": len(g), "run_m08": (runs or {}).get(cod),
                               "escanos_2023": sum(reparto[cod].values()), "a": reparto[cod],
                               "b": (b or {}).get(cod), "c": c})
    def total(clave):
        t: dict[str, int] = {}
        for p in provincias:
            for par, n in (p[clave] or {}).items():
                t[par] = t.get(par, 0) + n
        return dict(sorted(t.items(), key=lambda x: (-x[1], x[0])))
    sin_b = b is None or any(p["b"] is None for p in provincias)
    return {
        "schema": "ddd.hemiciclo/1.0", "version": "1.0.0", "ambito": ETIQUETA,
        "provincias_incluidas": len(provincias), "faltan": faltan,
        "fuentes": {"a": "reparto real 2023: D'Hondt con barrera del 3 % sobre el ZIP oficial por mesa (Interior)",
                    "b": "sin fuente" if sin_b else "generales 2019-11",
                    "c": "uninominal propio: ganador de cada distrito DDD (M08 registrado)"},
        "totales": {"a": total("a"), "b": None if sin_b else total("b"), "c": total("c")},
        "escanos": {"a": sum(p["escanos_2023"] for p in provincias), "c": sum(p["distritos"] for p in provincias)},
        "provincias": provincias, "errores": errores,
    }


def escribir(res: dict, salida: Path) -> None:
    salida.mkdir(parents=True, exist_ok=True)
    (salida / "hemiciclo.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    with open(salida / "hemiciclo.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ambito", "provincia", "partido", "a_real_2023", "b_2019", "c_uninominal"])
        def fila(ambito, prov, a, b, c):
            for p in sorted(set(a) | set(b or {}) | set(c)):
                w.writerow([ambito, prov, p, a.get(p, 0), "sin fuente" if b is None else b.get(p, 0), c.get(p, 0)])
        for pr in res["provincias"]:
            fila(ETIQUETA, pr["provincia"], pr["a"], pr["b"], pr["c"])
        fila(ETIQUETA, ETIQUETA, res["totales"]["a"], res["totales"]["b"], res["totales"]["c"])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--cache", type=Path, default=ROOT / ".cache/ddd/hemiciclo")
    ap.add_argument("--m08-dir", type=Path, help="ZIP <territorio>_<run>.zip ya descargados (sin red)")
    ap.add_argument("--mesa-zip", type=Path, help="ZIP oficial por mesa ya descargado (sin red)")
    ap.add_argument("--distritos", type=Path, default=N06)
    ap.add_argument("--salida", required=True, type=Path)
    ap.add_argument("--visor", action="store_true", help="copia también hemiciclo.json a dashboard/")
    a = ap.parse_args(argv)
    oficial = leer_mesa_zip(a.mesa_zip or mesa_zip(a.cache))
    reparto = reparto_2023(oficial)
    errores = verificar_oficial(reparto)
    gan, runs = cargar_m08(a.cache, a.m08_dir)
    res = generar(gan, reparto, leer_distritos(a.distritos), None, runs)
    res["errores"] += errores
    res["verificacion_a"] = "OK: 52 circunscripciones, 350 escaños y totales nacionales oficiales" if not errores else "FALLA"
    escribir(res, a.salida)
    if a.visor:
        escribir(res, ROOT / "dashboard")
    print(f"{ETIQUETA}: {res['provincias_incluidas']} provincias; faltan "
          f"{[f['provincia'] for f in res['faltan']]}; (b) {res['fuentes']['b']}; (a) {res['verificacion_a']}")
    for e in res["errores"]:
        print(f"::error::{e}")
    return 1 if res["errores"] else 0


if __name__ == "__main__":
    sys.exit(main())
