#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Hemiciclo nacional: suma de escaños por partido de tres maneras.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.3.0 · FECHA: 2026-11-10 · ESTADO: candidato
CAMBIOS: 1.3.0 (T-201): `cargar_m08(cache, m08_dir, eleccion)` elige el M08 por (territorio, elección), por defecto 2023-07-23; interfaz
  pública intacta (parámetro opcional al final).
CAMBIOS: (b) se rellena con el oficial de 2019-11 (BOE-A-2019-18147, T-55) y una tabla explícita de homologación de siglas; lee los ganadores de datos/resultados/*.csv (T-53) cuando el manifiesto acredita el blob vigente; blobs como respaldo.
ANTERIOR: legacy/herramientas/generar_hemiciclo_v1.2.0_20261110.py
QUÉ HACE: lee los M08 registrados (distritos_resultados.csv) de las provincias nacionales completas y suma:
  (a) reparto real 2023 (D'Hondt, umbral 3 %), calculado desde los votos y contrastado escaño a escaño con el oficial;
  (b) elección anterior (generales 2019-11): escaños oficiales del BOE (configuracion/resultados_oficiales_congreso_2019_11.csv),
      con las siglas homologadas a las de 2023 por HOMOLOGACION_2019 (UP→SUMAR es una decisión documentada, no una fusión silenciosa);
  (c) uninominal propio: el ganador de cada distrito DDD (un escaño por distrito).
  Salida JSON y CSV con totales de «Nacional» por partido y la lista de provincias que faltan, calculada de los datos
  (sin M08, o con distritos distintos de los esperados).
FUENTES: M08: blobs inmutables de orchestracion/publicaciones_visor.json (kind=canonical_m08, el run más reciente por
  circunscripción NAC), bajados con `gh api .../git/blobs/<sha>` a una caché local y verificados con su sha256.
  Oficial 2023: ZIP por mesa del release fuente-infoelectoral-02202307 (huella de configuracion/contratos_infoelectoral.yaml),
  votos por candidatura con CERA y votos válidos (candidaturas + blancos) por provincia; el reparto es D'Hondt con barrera del 3 %.
  Verificación de (a): el reparto de cada una de las 52 circunscripciones se contrasta, partido a partido, con el oficial del BOE
  (configuracion/resultados_oficiales_congreso_2023.csv, con URL, fecha y sha256 en su .json); una diferencia falla, salvo un único
  cambio PSOE→PP (CERA final) en una sola provincia, que sale como nota. Partidos: PSOE agrupa sus federadas (PSC, PSE-EE, PSN, PSIB, PSdeG)
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
import re
import io
import subprocess
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import resultados_ligeros as rl  # noqa: E402
from ddd_core import territorio_ids  # noqa: E402  (T-220)

ROOT = Path(__file__).resolve().parents[1]
N06 = ROOT / "docs/ESTUDIOS/N06_DECISION_K_20261012/resultados/reparto_ddd_52.csv"
REPO = "jfmurciego/DiputadodeDistrito"
REGISTRO_VISOR = ROOT / "orchestracion/publicaciones_visor.json"
CONTRATOS = ROOT / "configuracion/contratos_infoelectoral.yaml"
MESA_RELEASE = "fuente-infoelectoral-02202307"
MESA_PREFIJO = "02202307"
UMBRAL = 0.03

# Resultado oficial: Resolución de 30-08-2023 de la Presidencia de la JEC (BOE núm. 210, 01-09-2023, BOE-A-2023-18907).
OFICIAL_CSV = ROOT / "configuracion/resultados_oficiales_congreso_2023.csv"
OFICIAL_META = ROOT / "configuracion/resultados_oficiales_congreso_2023.json"
BOE_ID = "BOE-A-2023-18907"
BOE_URL = f"https://www.boe.es/diario_boe/xml.php?id={BOE_ID}"
ETIQUETA = "Nacional"

# Oficial 2019-11: Resolución de 17-12-2019 de la Presidencia de la JEC, que corrige la de 29-11-2019 (BOE-A-2019-17344,
# cuyo texto solo remite a los cuadros) y publica los cuadros completos (BOE núm. 303, 18-12-2019, BOE-A-2019-18147).
OFICIAL19_CSV = ROOT / "configuracion/resultados_oficiales_congreso_2019_11.csv"
OFICIAL19_META = ROOT / "configuracion/resultados_oficiales_congreso_2019_11.json"
BOE19_ID = "BOE-A-2019-18147"
BOE19_URL = f"https://www.boe.es/diario_boe/xml.php?id={BOE19_ID}"

# Homologación de siglas del BOE 2019 (columna «partido» del CSV, tal cual el BOE) a las etiquetas de 2023. Lo no listado
# conserva su sigla del BOE (Cs, MÁS PAÍS-EQUO, MÉS COMPROMÍS, CUP-PR, NA+, PP-FORO, PRC, ¡TERUEL EXISTE!). Las federadas
# del PSOE (PSC) las agrupa grupo(). La familia Unidas Podemos (PODEMOS-IU, ECP-GUANYEM EL CANVI, PODEMOS-EU) se
# asimila a SUMAR como espacio a la izquierda del PSOE; es una convención de comparación, no una identidad jurídica.
HOMOLOGACION_2019 = {
    "ERC-SOBIRANISTES": "ERC", "JxCAT-JUNTS": "JUNTS", "CCa-PNC-NC": "CCa",
    "PODEMOS-IU": "SUMAR", "ECP-GUANYEM EL CANVI": "SUMAR", "PODEMOS-EU": "SUMAR",
}

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
_POR_ID = {t.id_legacy: t.codigo[3:] for t in territorio_ids.tabla().values() if t.ambito == "NAC"}  # T-220: viejo
_POR_ID.update({t.id: t.codigo[3:] for t in territorio_ids.tabla().values() if t.ambito == "NAC"})  # y nuevo


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


_ALIAS = {"Alicante/Alacant": "03", "Araba/Álava": "01", "Balears (Illes)": "07", "Bizkaia": "48", "Castellón/Castelló": "12",
          "Coruña (A)": "15", "Gipuzkoa": "20", "Girona": "17", "Lleida": "25", "Ourense": "32", "Palmas (Las)": "35",
          "Rioja (La)": "26", "Valencia/València": "46"}


def _sigla(columna: str) -> str:
    s = columna.replace("\xa0", " ").strip().rstrip(".")
    return grupo(re.findall(r"\(([^()]*)\)\s*$", s)[-1].strip())


def extraer_boe(xml: str) -> list[dict]:
    """Escaños oficiales por circunscripción y partido de las tres primeras tablas del Congreso del BOE."""
    i = xml.index("CONGRESO DE LOS DIPUTADOS")
    tablas = re.findall(r"<table.*?</table>", xml[i:xml.index("SENADO", i)], re.S)[:3]
    out = []
    por_cod = {c: n for c, (_, n) in PROVINCIAS.items()}
    for tb in tablas:
        filas = [[re.sub(r"<[^>]+>", "", x).strip() for x in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", r, re.S)]
                 for r in re.findall(r"<tr.*?</tr>", tb, re.S)]
        partidos = [_sigla(x) for x in filas[0][2:]]
        for f in filas[2:]:
            nombre = f[0].rstrip(".").strip()
            if nombre.startswith("Total"):
                continue
            cod = _ALIAS.get(nombre) or next((c for c, n in por_cod.items() if n == nombre), None)
            if cod is None:
                raise ValueError(f"circunscripción del BOE no reconocida: {nombre!r}")
            for k, par in enumerate(partidos):
                v, e = (f[2 + 2 * k:4 + 2 * k] + ["", ""])[:2]
                if e.strip():
                    out.append({"codigo": cod, "provincia": PROVINCIAS[cod][1], "escanos_circunscripcion": int(f[1]),
                                "partido": par, "votos": int(v.replace(".", "") or 0), "escanos": int(e)})
    return out


def guardar_oficial(xml_ruta: Path, fecha_publicacion: str = "2023-09-01") -> None:
    datos = extraer_boe(xml_ruta.read_text(encoding="utf-8"))
    OFICIAL_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OFICIAL_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(datos[0]))
        w.writeheader()
        w.writerows(datos)
    meta = {"fuente": "Resolución de 30-08-2023 de la Presidencia de la Junta Electoral Central: resumen de resultados "
                      "de las elecciones al Congreso y al Senado del 23-07-2023",
            "boe": BOE_ID, "url": BOE_URL, "fecha_publicacion": fecha_publicacion,
            "sha256_xml": _sha256(xml_ruta.read_bytes()), "sha256_csv": _sha256(OFICIAL_CSV.read_bytes())}
    OFICIAL_META.write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def leer_oficial(ruta: Path = OFICIAL_CSV) -> tuple[dict[str, int], dict[str, dict[str, int]]]:
    """(escaños por circunscripción, escaños por circunscripción y partido) del CSV oficial, verificando su hash."""
    if ruta == OFICIAL_CSV and OFICIAL_META.exists():
        if json.loads(OFICIAL_META.read_text(encoding="utf-8"))["sha256_csv"] != _sha256(ruta.read_bytes()):
            raise ValueError("el CSV oficial no coincide con su sha256 registrado")
    esc: dict[str, int] = {}
    por: dict[str, dict[str, int]] = {}
    with open(ruta, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            esc[r["codigo"]] = int(r["escanos_circunscripcion"])
            d = por.setdefault(r["codigo"], {})
            if int(r["escanos"]):
                d[grupo(r["partido"])] = d.get(grupo(r["partido"]), 0) + int(r["escanos"])
    return esc, por


def extraer_boe_2019(xml: str) -> list[dict]:
    """Escaños oficiales 2019-11 por circunscripción y candidatura de las cuatro tablas del Congreso con columna Escaños
    (fila 1 = siglas del BOE; datos desde la fila 3; cada candidatura ocupa un par Votos/Escaños desde la columna 2)."""
    out = []
    por_cod = {c: n for c, (_, n) in PROVINCIAS.items()}
    for tb in re.findall(r"<table.*?</table>", xml, re.S)[:4]:
        filas = [[re.sub(r"<[^>]+>", "", x).replace("\xa0", " ").strip() for x in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", r, re.S)]
                 for r in re.findall(r"<tr.*?</tr>", tb, re.S)]
        if "Escaños" not in filas[2]:
            raise ValueError("tabla del BOE 2019 sin columna Escaños")
        siglas = filas[1]
        for f in filas[3:]:
            nombre = f[0].rstrip(".").strip()
            if nombre.startswith("Total"):
                continue
            cod = _ALIAS.get(nombre) or next((c for c, n in por_cod.items() if n == nombre), None)
            if cod is None:
                raise ValueError(f"circunscripción del BOE no reconocida: {nombre!r}")
            for k, par in enumerate(siglas):
                v, e = (f[2 + 2 * k:4 + 2 * k] + ["", ""])[:2]
                if e.strip():
                    out.append({"codigo": cod, "provincia": PROVINCIAS[cod][1], "escanos_circunscripcion": int(f[1]),
                                "partido": par, "votos": int(v.replace(".", "") or 0), "escanos": int(e)})
    return out


def guardar_oficial_2019(xml_ruta: Path, fecha_publicacion: str = "2019-12-18") -> None:
    datos = extraer_boe_2019(xml_ruta.read_text(encoding="utf-8"))
    with open(OFICIAL19_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(datos[0]))
        w.writeheader()
        w.writerows(datos)
    meta = {"fuente": "Resolución de 17-12-2019 de la Presidencia de la Junta Electoral Central, que corrige la de 29-11-2019 "
                      "(BOE-A-2019-17344): resumen de resultados de las elecciones al Congreso y al Senado del 10-11-2019",
            "boe": BOE19_ID, "boe_corregido": "BOE-A-2019-17344", "url": BOE19_URL, "fecha_publicacion": fecha_publicacion,
            "sha256_xml": _sha256(xml_ruta.read_bytes()), "sha256_csv": _sha256(OFICIAL19_CSV.read_bytes())}
    OFICIAL19_META.write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def leer_oficial_2019(ruta: Path = OFICIAL19_CSV) -> dict[str, dict[str, int]]:
    """(b): provincia → {partido homologado: escaños} del CSV oficial 2019-11, verificando su sha256 y que cada
    circunscripción reparta sus escaños y el total sea 350."""
    if ruta == OFICIAL19_CSV and OFICIAL19_META.exists():
        if json.loads(OFICIAL19_META.read_text(encoding="utf-8"))["sha256_csv"] != _sha256(ruta.read_bytes()):
            raise ValueError("el CSV oficial 2019-11 no coincide con su sha256 registrado")
    esc: dict[str, int] = {}
    por: dict[str, dict[str, int]] = {}
    with open(ruta, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            esc[r["codigo"]] = int(r["escanos_circunscripcion"])
            if int(r["escanos"]):
                p = grupo(HOMOLOGACION_2019.get(r["partido"], r["partido"]))
                d = por.setdefault(r["codigo"], {})
                d[p] = d.get(p, 0) + int(r["escanos"])
    mal = [c for c in esc if sum(por.get(c, {}).values()) != esc[c]]
    if mal or sum(esc.values()) != 350 or set(esc) != set(PROVINCIAS):
        raise ValueError(f"oficial 2019-11 no cuadra: circunscripciones {mal}, total {sum(esc.values())}")
    return por


def reparto_2023(oficial: dict[str, dict], escanos: dict[str, int]) -> dict[str, dict[str, int]]:
    """provincia → {partido nacional: escaños} (D'Hondt por candidatura, luego agrupado)."""
    res = {}
    for cod, d in oficial.items():
        if cod not in escanos:  # filas de ámbito superior (p. ej. 99)
            continue
        r = dhondt(d["votos"], escanos[cod], d["validos"])
        res[cod] = _sumar({etiqueta(k): n for k, n in r.items()})
    return res


NOTA_A = "difiere en 1 escaño PSOE→PP del oficial por el CERA final, que el ZIP no trae"
FUENTE_A = "D'Hondt sobre el escrutinio de Interior (release fuente-infoelectoral-02202307), contrastado con el oficial BOE-A-2023-18907"


def contrastar(reparto: dict[str, dict[str, int]], oficial: dict[str, dict[str, int]],
               escanos: dict[str, int]) -> tuple[list[str], list[str], list[dict]]:
    """Contraste por provincia con el oficial del BOE: (errores, notas, diferencias). Solo se admite como explicada
    una diferencia de un escaño PSOE→PP en una única provincia (CERA final); cualquier otra falla."""
    err = [f"{PROVINCIAS[c][1]}: {sum(r.values())} escaños != {escanos[c]}" for c, r in reparto.items()
           if sum(r.values()) != escanos[c]]
    err += [f"falta la circunscripción {PROVINCIAS[c][1]}" for c in PROVINCIAS if c not in reparto]
    difs = []
    for c, mio in reparto.items():
        of = oficial.get(c, {})
        d = {p: mio.get(p, 0) - of.get(p, 0) for p in set(mio) | set(of) if mio.get(p, 0) != of.get(p, 0)}
        if d:
            difs.append({"codigo": c, "provincia": PROVINCIAS[c][1], "propio_menos_oficial": d})
    if not difs:
        return err, [], []
    if len(difs) == 1 and difs[0]["propio_menos_oficial"] == {"PSOE": 1, "PP": -1}:
        return err, [f"{NOTA_A}; provincia: {difs[0]['provincia']}"], difs
    return err + [f"diferencias con el oficial: {difs}"], [], difs


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


def cargar_m08(cache: Path, m08_dir: Path | None = None, eleccion: str = rl.ELECCION_POR_DEFECTO) -> tuple[dict[str, list[str]], dict[str, str]]:
    """provincia → ganadores por distrito y provincia → run, de los blobs del registro del visor (o de m08_dir)."""
    prods = rl.vigente_por_eleccion(json.loads(REGISTRO_VISOR.read_text(encoding="utf-8"))["products"], "canonical_m08",
                                    eleccion, ambito="NAC")
    gan, runs = {}, {}
    for t, p in sorted(prods.items()):
        if t not in _POR_ID:
            continue
        g = rl.ganadores(rl.SALIDA, t, p) if m08_dir is None else None
        if g is not None:
            gan[_POR_ID[t]], runs[_POR_ID[t]] = g, p["run_id"]
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
                    "b": "sin fuente" if sin_b else f"oficial generales 2019-11 ({BOE19_ID}), siglas homologadas por HOMOLOGACION_2019",
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
    ap.add_argument("--extraer-boe", type=Path, help="XML del BOE ya descargado: regenera el CSV oficial y sale")
    ap.add_argument("--extraer-boe-2019", type=Path, help="XML del BOE-A-2019-18147 ya descargado: regenera el CSV 2019-11 y sale")
    ap.add_argument("--salida", type=Path)
    ap.add_argument("--visor", action="store_true", help="copia también hemiciclo.json a dashboard/")
    a = ap.parse_args(argv)
    if a.extraer_boe:
        guardar_oficial(a.extraer_boe)
        print(f"escrito {OFICIAL_CSV.relative_to(ROOT)}")
        return 0
    if a.extraer_boe_2019:
        guardar_oficial_2019(a.extraer_boe_2019)
        print(f"escrito {OFICIAL19_CSV.relative_to(ROOT)}")
        return 0
    if a.salida is None:
        ap.error("--salida es obligatorio")
    escanos, of_prov = leer_oficial()
    oficial = leer_mesa_zip(a.mesa_zip or mesa_zip(a.cache))
    reparto = reparto_2023(oficial, escanos)
    errores, notas, difs = contrastar(reparto, of_prov, escanos)
    gan, runs = cargar_m08(a.cache, a.m08_dir)
    res = generar(gan, reparto, leer_distritos(a.distritos), leer_oficial_2019(), runs)
    res["errores"] += errores
    res["fuentes"]["a"] = FUENTE_A
    res["notas"] = notas
    res["contraste_oficial"] = {"fuente": json.loads(OFICIAL_META.read_text(encoding="utf-8")), "diferencias": difs}
    res["verificacion_a"] = ("FALLA" if errores else "OK: 52 circunscripciones, 350 escaños y totales oficiales"
                             if not notas else "OK con nota: " + notas[0])
    escribir(res, a.salida)
    if a.visor:
        escribir(res, ROOT / "dashboard")
    print(f"{ETIQUETA}: {res['provincias_incluidas']} provincias; faltan "
          f"{[f['provincia'] for f in res['faltan']]}; (b) {res['fuentes']['b']}; (a) {res['verificacion_a']}")
    for n in notas:
        print(f"::notice::(a) {n}")
    for e in res["errores"]:
        print(f"::error::{e}")
    return 1 if res["errores"] else 0


if __name__ == "__main__":
    sys.exit(main())
