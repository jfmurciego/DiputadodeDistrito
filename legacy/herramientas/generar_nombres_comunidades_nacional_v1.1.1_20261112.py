#!/usr/bin/env python3
"""Nombres de distrito (C12) y comarcas partidas (C13) de los distritos nacionales.

VERSIÓN: 1.1.1
NOMBRE DE VERSIÓN: Nombres, comarcas y partidos judiciales
FECHA: 2026-11-10
ESTADO: activo T-64
CAMBIOS 1.1.1 (T-201): `descargar` toma el M06 de la elección por defecto (2023-07-23), no el run_id mayor entre elecciones.
CAMBIOS: C13 usa también los partidos judiciales (configuracion/partidos_judiciales.csv, Ley 38/1988) en toda España; los nombres de distrito no cambian.
MOTIVO: un nombre legible y estable por distrito nacional y la medida de comarcas partidas.
ANTERIOR: legacy/herramientas/generar_nombres_comunidades_nacional_v1.1.0_20261110.py

Reglas de nombre (toponimia solo en español, tabla datos/distritos/toponimos_es.csv):
  1. distrito de un único municipio: «<municipio>»; si ese municipio está repartido entre k>1 distritos
     de un solo municipio, «<municipio> <n>», n por posición (norte a sur y, a igual latitud, oeste a este).
  2. distrito de varios municipios: «<comarca>» si todos sus municipios están en una misma comarca de la
     fuente del repo; si no, «<municipio principal> y entorno» (principal = el más poblado, INE 2025).
  3. colisión de un mismo nombre: « <n>» por posición; último recurso, «(<district_id>)».
Sin votos, partidos ni resultados. Uso:
  python herramientas/generar_nombres_comunidades_nacional.py --m06-dir <dir con congreso_*.zip> [--descargar]
  python herramientas/generar_nombres_comunidades_nacional.py --reconstruir-municipios 65034.csv.zip
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import subprocess
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

VERSION = "1.1.1"
RAIZ = Path(__file__).resolve().parents[1]
SALIDA = "datos/distritos"
POBLACION = "datos/distritos/municipios_ine_2025.csv"  # código, nombre INE y población 2025 por municipio
PARTIDOS = "configuracion/partidos_judiciales.csv"
TOPONIMOS = "datos/distritos/toponimos_es.csv"
REGISTRO = "orchestracion/publicaciones_visor.json"
REPO = "jfmurciego/DiputadodeDistrito"
# Fuentes de comarcas disponibles en el repo (no se infieren comarcas ni partidos judiciales).
FUENTES_COMARCAS = [("inputs/COMARCAS.csv", "Aragón: 33 comarcas")]
PROHIBIDOS = {"party", "partido", "vote", "voto", "votos", "ganador", "escanos", "seats"}

PROVINCIAS_ES = {
    "alava": "Álava", "albacete": "Albacete", "almeria": "Almería", "asturias": "Asturias", "avila": "Ávila",
    "badajoz": "Badajoz", "baleares": "Baleares", "burgos": "Burgos", "caceres": "Cáceres", "cadiz": "Cádiz",
    "cantabria": "Cantabria", "castellon": "Castellón", "ceuta": "Ceuta", "ciudad_real": "Ciudad Real",
    "cordoba": "Córdoba", "cuenca": "Cuenca", "gerona": "Gerona", "granada": "Granada",
    "guadalajara": "Guadalajara", "guipuzcoa": "Guipúzcoa", "huelva": "Huelva", "huesca": "Huesca",
    "jaen": "Jaén", "la_coruna": "La Coruña", "la_rioja": "La Rioja", "las_palmas": "Las Palmas", "leon": "León",
    "lerida": "Lérida", "lugo": "Lugo", "madrid": "Madrid", "melilla": "Melilla", "murcia": "Murcia",
    "navarra": "Navarra", "orense": "Orense", "palencia": "Palencia", "pontevedra": "Pontevedra",
    "salamanca": "Salamanca", "santa_cruz_de_tenerife": "Santa Cruz de Tenerife", "segovia": "Segovia",
    "sevilla": "Sevilla", "soria": "Soria", "tarragona": "Tarragona", "teruel": "Teruel", "toledo": "Toledo",
    "valencia": "Valencia", "valladolid": "Valladolid", "vizcaya": "Vizcaya", "zamora": "Zamora",
    "zaragoza": "Zaragoza",
}
ARTICULOS = ("El", "La", "Los", "Las", "Lo", "A", "O", "As", "Os", "L'", "Les", "Els", "Es", "Sa", "Ses", "Na")


def sha256(path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def romper_articulo(nombre: str) -> str:
    """«Coruña, A» → «A Coruña»; «Escala, L'» → «L'Escala». Sin coma-artículo, igual."""
    m = re.match(r"^(.*), (" + "|".join(re.escape(a) for a in ARTICULOS) + r")$", nombre, re.IGNORECASE)
    if not m:
        return nombre
    art = m.group(2)[0].upper() + m.group(2)[1:]
    return f"{art}{m.group(1)}" if art.endswith("'") else f"{art} {m.group(1)}"


def cargar_toponimos(ruta) -> dict:
    tabla = {}
    if Path(ruta).exists():
        with Path(ruta).open(encoding="utf-8", newline="") as f:
            for fila in csv.DictReader(f):
                tabla[fila["codigo_ine"]] = fila["nombre_es"]
    return tabla


def nombre_es(codigo: str, nombre_ine: str, tabla: dict) -> str:
    if codigo in tabla:
        return tabla[codigo]
    return romper_articulo(nombre_ine.strip())


def pendientes_toponimia(nombre_ine: str, resuelto: str) -> bool:
    """Marca nombres que huelen a otra lengua y no están en la tabla (barra, apóstrofo catalán)."""
    return "/" in resuelto or " / " in resuelto or bool(re.search(r"\b(l'|d'|d’|l’)", resuelto.lower()))


def construir_municipios(zip_ine, destino):
    """Tabla código/nombre/población 2025 desde el INE 65034 (inputs/partes → 65034.csv.zip).
    El M06 lista nombres en orden alfabético y códigos en orden numérico: el nombre se toma de aquí."""
    filas = []
    with zipfile.ZipFile(zip_ine) as z, z.open(z.namelist()[0]) as crudo:
        for linea in io.TextIOWrapper(crudo, encoding="utf-8-sig"):
            p = linea.rstrip("\n").split("\t")
            if len(p) < 8 or p[6] != "2025" or p[4] != "Total" or p[5] != "Todas las edades":
                continue
            m = re.match(r"^(\d{5}) (.*)$", p[2])
            if m and p[3] == "" and p[7]:
                filas.append((m.group(1), m.group(2), int(p[7].replace(".", ""))))
    filas.sort()
    with Path(destino).open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["codigo_ine", "nombre_ine", "poblacion_2025"])
        w.writerows(filas)
    return filas


def cargar_municipios(ruta):
    pob, nombre = {}, {}
    with Path(ruta).open(encoding="utf-8", newline="") as f:
        for fila in csv.DictReader(f):
            pob[fila["codigo_ine"]] = int(fila["poblacion_2025"])
            nombre[fila["codigo_ine"]] = fila["nombre_ine"]
    return pob, nombre


def cargar_comarcas(fuentes, raiz=RAIZ):
    """Devuelve {cod_municipio: nombre_comarca_es}, {cod_provincia} cubiertas y fuente por provincia."""
    comarca, cubiertas = {}, {}
    for relativa, etiqueta in fuentes:
        ruta = Path(raiz) / relativa
        if not ruta.exists():
            continue
        with ruta.open(encoding="utf-8-sig", newline="") as f:
            for fila in csv.DictReader(f):
                comarca[fila["Municipio código"]] = fila["Comarca nombre"].split(" / ")[0].strip()
                cubiertas[fila["Provincia código"].zfill(2)] = etiqueta
    return comarca, cubiertas


def cargar_partidos(ruta=None):
    """{cod_municipio: id de partido judicial} desde configuracion/partidos_judiciales.csv (Ley 38/1988)."""
    ruta = Path(ruta) if ruta else RAIZ / PARTIDOS
    if not ruta.exists():
        return {}
    with ruta.open(encoding="utf-8", newline="") as f:
        return {r["codigo_ine"]: r["id_partido"] for r in csv.DictReader(l for l in f if not l.startswith("#"))}


def leer_m06(ruta, nombre_ine=None):
    """Lee distritos de un ZIP o GeoJSON M06. Devuelve lista de dicts ordenada por district_id."""
    ruta = Path(ruta)
    if ruta.suffix == ".zip":
        with zipfile.ZipFile(ruta) as z:
            nombre = next(n for n in z.namelist() if n.endswith(".geojson"))
            datos = json.loads(z.read(nombre))
    else:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    distritos = []
    for feat in datos["features"]:
        p = feat["properties"]
        campos = {k.lower() for k in p}
        if campos & PROHIBIDOS:
            raise ValueError(f"campos partidistas prohibidos: {sorted(campos & PROHIBIDOS)}")
        codigos = [c.split(":")[0] for c in str(p["municipality_codes"]).split(" | ")]
        nombres_m06 = str(p["municipality_names"]).split(" | ")
        if len(codigos) != len(nombres_m06):
            raise ValueError(f"distrito {p['district_id']}: códigos y nombres desalineados")
        if nombre_ine is None:
            nombres = nombres_m06
        else:
            nombres = [nombre_ine[c] for c in codigos]  # el M06 usa nombres cartográficos abreviados
        distritos.append({
            "district_id": int(p["district_id"]),
            "poblacion": int(float(p["district_pop"])),
            "codigos": codigos,
            "nombres_ine": nombres,
            "cx": float(p["centroid_x"]),
            "cy": float(p["centroid_y"]),
            "provincia": str(p["province_codes"]).split(" | ")[0].split("-")[0][:2],
        })
    return sorted(distritos, key=lambda d: d["district_id"])


def _posicion(d):
    """Norte a sur y, a igual latitud, oeste a este (CRS métrico: y crece hacia el norte)."""
    return (-round(d["cy"], 3), round(d["cx"], 3), d["district_id"])


def nombrar(territorio, distritos, pob_mun, tabla, comarca_de):
    """Asigna nombre a cada distrito. Devuelve lista de filas (dict) ordenadas por district_id."""
    en_distritos = defaultdict(set)
    for d in distritos:
        for c in d["codigos"]:
            en_distritos[c].add(d["district_id"])
    nom = {}
    for d in distritos:
        for c, n in zip(d["codigos"], d["nombres_ine"]):
            nom[c] = nombre_es(c, n, tabla)
    filas = {}
    for d in distritos:
        d["principal"] = max(d["codigos"], key=lambda c: (pob_mun.get(c, 0), c))
        comarcas = sorted({comarca_de[c] for c in d["codigos"] if c in comarca_de})
        completos = all(c in comarca_de for c in d["codigos"])
        if len(d["codigos"]) == 1:
            d["regla"], d["base"] = "MUNICIPIO", nom[d["principal"]]
        elif completos and len(comarcas) == 1:
            d["regla"], d["base"] = "COMARCA", comarcas[0]
        else:
            d["regla"], d["base"] = "PRINCIPAL_Y_ENTORNO", f"{nom[d['principal']]} y entorno"
        d["comarcas"] = comarcas
    grupos = defaultdict(list)
    for d in distritos:
        grupos[d["base"]].append(d)
    for base, lista in grupos.items():
        lista.sort(key=_posicion)
        for i, d in enumerate(lista, 1):
            d["nombre"] = base if len(lista) == 1 else f"{base} {i}"
            d["regla_n"] = "" if len(lista) == 1 else "POSICION_N_S_O_E"
    vistos = defaultdict(list)
    for d in distritos:
        vistos[d["nombre"]].append(d)
    for nombre, lista in vistos.items():
        if len(lista) > 1:
            for d in lista:
                d["nombre"] = f"{nombre} ({d['district_id']})"
                d["regla_n"] = "DESEMPATE_ID"
    for d in distritos:
        filas[d["district_id"]] = {
            "territorio": territorio,
            "district_id": d["district_id"],
            "nombre_distrito": d["nombre"],
            "regla": d["regla"],
            "regla_numeracion": d["regla_n"],
            "municipio_principal_codigo": d["principal"],
            "municipio_principal": nom[d["principal"]],
            "n_municipios": len(d["codigos"]),
            "municipios_divididos": sum(1 for c in d["codigos"] if len(en_distritos[c]) > 1),
            "poblacion_distrito": d["poblacion"],
            "comarcas": " | ".join(d["comarcas"]),
            "n_comarcas": len(d["comarcas"]),
        }
    return [filas[k] for k in sorted(filas)], en_distritos


def comarcas_partidas(distritos, comarca_de, cubiertas, en_distritos):
    """Métrica C13 por provincia evaluable. Una comarca está partida si sus municipios (un municipio
    dividido cuenta en todos sus distritos) tocan más de un distrito."""
    por_comarca = defaultdict(set)
    miembros = defaultdict(set)
    for c, nombre in comarca_de.items():
        if c in en_distritos:
            por_comarca[nombre] |= en_distritos[c]
            miembros[nombre].add(c)
    partidas = {n: sorted(ds) for n, ds in por_comarca.items() if len(ds) > 1}
    return {
        "comarcas_tocadas": len(por_comarca),
        "comarcas_partidas": len(partidas),
        "detalle_partidas": partidas,
        "municipios_divididos_en_comarcas": sorted(c for n in miembros for c in miembros[n] if len(en_distritos[c]) > 1),
    }


def partidos_partidos(distritos, partido_de, pob_mun, en_distritos):
    """C13 con partidos judiciales: misma definición que las comarcas, más la cobertura municipal y poblacional."""
    cods = {c for d in distritos for c in d["codigos"]}
    con = {c for c in cods if c in partido_de}
    m = comarcas_partidas(distritos, {c: partido_de[c] for c in con}, None, en_distritos)
    m["cobertura_municipios"] = len(con) / len(cods)
    total = sum(pob_mun.get(c, 0) for c in cods)
    m["cobertura_poblacion"] = (sum(pob_mun.get(c, 0) for c in con) / total) if total else 0.0
    m["municipios_sin_partido"] = sorted(cods - con)
    return m


CAMPOS = ["territorio", "district_id", "nombre_distrito", "regla", "regla_numeracion", "municipio_principal_codigo",
          "municipio_principal", "n_municipios", "municipios_divididos", "poblacion_distrito", "comarcas",
          "n_comarcas", "n_partidos", "estado_c13", "fuente_comarcas"]


def procesar_territorio(territorio, ruta_m06, pob_mun, nombre_ine, tabla, comarca_de, cubiertas, salida, partido_de=None):
    distritos = leer_m06(ruta_m06, nombre_ine)
    prov = distritos[0]["provincia"]
    partido_de = partido_de or {}
    evaluable = prov in cubiertas
    cd = comarca_de if evaluable else {}
    filas, en_dist = nombrar(territorio, distritos, pob_mun, tabla, cd)
    con_partidos = any(c in partido_de for d in distritos for c in d["codigos"])
    for f, d in zip(filas, sorted(distritos, key=lambda d: d["district_id"])):
        f["estado_c13"] = "EVALUADO" if (evaluable or con_partidos) else "NOT_EVALUABLE"
        f["fuente_comarcas"] = cubiertas.get(prov, "")
        f["n_partidos"] = len({partido_de[c] for c in d["codigos"] if c in partido_de}) if con_partidos else "n/d"
    nombres = [f["nombre_distrito"] for f in filas]
    if len(nombres) != len(set(nombres)):
        raise ValueError(f"{territorio}: nombres repetidos")
    pendientes = sorted({f["municipio_principal"] for f in filas if pendientes_toponimia("", f["municipio_principal"])})
    salida = Path(salida)
    salida.mkdir(parents=True, exist_ok=True)
    csv_ruta = salida / f"nombres_{territorio}.csv"
    with csv_ruta.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS, lineterminator="\n")
        w.writeheader()
        w.writerows(filas)
    metrica = None
    if evaluable:
        metrica = comarcas_partidas(distritos, {c: n for c, n in comarca_de.items() if c.startswith(prov)},
                                    cubiertas, en_dist)
    m_part = partidos_partidos(distritos, partido_de, pob_mun, en_dist) if con_partidos else None
    (salida / f"informe_{territorio}.md").write_text(
        informe(territorio, filas, metrica, cubiertas.get(prov), pendientes, m_part), encoding="utf-8")
    return filas, metrica, pendientes, csv_ruta, m_part


def informe(territorio, filas, metrica, fuente, pendientes, m_part=None):
    reglas = defaultdict(int)
    for f in filas:
        reglas[f["regla"]] += 1
    out = [f"# Nombres y comunidades de interés — {territorio}", "",
           f"Generado por `herramientas/generar_nombres_comunidades_nacional.py` {VERSION}. Sin datos electorales.", "",
           f"- Distritos: {len(filas)} (nombres únicos: {len({f['nombre_distrito'] for f in filas})})",
           "- Reglas: " + ", ".join(f"{k} {v}" for k, v in sorted(reglas.items())),
           f"- Municipios divididos entre distritos (suma por distrito): {sum(f['municipios_divididos'] for f in filas)}",
           ""]
    if m_part is not None:
        out += ["## C13 partidos judiciales partidos", "",
                "Fuente: Ley 38/1988, Anexo I (BOE-A-1988-29622), `configuracion/partidos_judiciales.csv`.",
                f"- Partidos tocados por la provincia: {m_part['comarcas_tocadas']}",
                f"- Partidos partidos entre distritos: {m_part['comarcas_partidas']}",
                f"- Cobertura: {m_part['cobertura_municipios']:.1%} de los municipios, "
                f"{m_part['cobertura_poblacion']:.1%} de la población (sin partido: {len(m_part['municipios_sin_partido'])}, "
                "listados en `configuracion/partidos_judiciales_no_conciliados.csv`).", ""]
        if m_part["detalle_partidas"]:
            out += ["| Partido partido | Distritos |", "|---|---|"]
            out += [f"| {n} | {', '.join(map(str, ds))} |" for n, ds in sorted(m_part["detalle_partidas"].items())]
            out.append("")
    if metrica is None and m_part is None:
        out += ["## C13 comarcas partidas", "",
                "NOT_EVALUABLE: sin comarcas ni partidos judiciales para esta provincia (no se infieren).", ""]
    elif metrica is not None:
        out += ["## C13 comarcas partidas", "", f"Fuente: {fuente}.",
                f"- Comarcas tocadas por la provincia: {metrica['comarcas_tocadas']}",
                f"- Comarcas partidas entre distritos: {metrica['comarcas_partidas']}", ""]
        if metrica["detalle_partidas"]:
            out += ["| Comarca partida | Distritos |", "|---|---|"]
            out += [f"| {n} | {', '.join(map(str, ds))} |" for n, ds in sorted(metrica["detalle_partidas"].items())]
            out.append("")
        out.append("Un municipio dividido cuenta en todos sus distritos; no se asigna población por debajo del municipio.")
        out.append("")
    out += ["## Distritos", "", "| Id | Nombre | Regla | Población | Comarcas |", "|---|---|---|---|---|"]
    out += [f"| {f['district_id']} | {f['nombre_distrito']} | {f['regla']} | {f['poblacion_distrito']} | "
            f"{f['n_comarcas'] if f['fuente_comarcas'] else 'n/d'} |" for f in filas]
    if pendientes:
        out += ["", "Toponimia pendiente de tabla: " + ", ".join(pendientes)]
    return "\n".join(out) + "\n"


def descargar(destino):
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    registro = json.loads((RAIZ / REGISTRO).read_text(encoding="utf-8"))
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import resultados_ligeros as rl
    mejores = rl.vigente_por_eleccion(registro["products"], "canonical_m06", prefijo="congreso_")
    for t, p in sorted(mejores.items()):
        crudo = subprocess.run(
            ["gh", "api", f"repos/{REPO}/git/blobs/{p['blob_sha']}", "-H", "Accept: application/vnd.github.raw"],
            capture_output=True, check=True).stdout
        if hashlib.sha256(crudo).hexdigest() != p["sha256"]:
            raise SystemExit(f"{t}: sha256 del blob no coincide con el registro")
        (destino / f"{t}.zip").write_bytes(crudo)
    return mejores


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--m06-dir")
    ap.add_argument("--reconstruir-municipios", metavar="65034.csv.zip",
                    help="regenera datos/distritos/municipios_ine_2025.csv desde el INE 65034")
    ap.add_argument("--descargar", action="store_true", help="baja los M06 publicados (gh, con sha256)")
    ap.add_argument("--salida", default=SALIDA)
    a = ap.parse_args(argv)
    if a.reconstruir_municipios:
        filas = construir_municipios(a.reconstruir_municipios, RAIZ / POBLACION)
        print(f"municipios={len(filas)} poblacion={sum(f[2] for f in filas)}")
        return 0
    if not a.m06_dir:
        ap.error("falta --m06-dir")
    if a.descargar:
        descargar(a.m06_dir)
    pob, nombre_ine = cargar_municipios(RAIZ / POBLACION)
    tabla = cargar_toponimos(RAIZ / TOPONIMOS)
    comarca_de, cubiertas = cargar_comarcas(FUENTES_COMARCAS)
    partido_de = cargar_partidos()
    salida = RAIZ / a.salida
    resumen, todos_pend = {}, {}
    for z in sorted(Path(a.m06_dir).glob("congreso_*.zip")):
        t = z.stem
        filas, metrica, pend, _, m_part = procesar_territorio(t, z, pob, nombre_ine, tabla, comarca_de, cubiertas, salida, partido_de)
        resumen[t] = {"distritos": len(filas), "sha256_m06": sha256(z),
                      "comarcas_partidas": None if metrica is None else metrica["comarcas_partidas"],
                      "partidos_partidos": None if m_part is None else m_part["comarcas_partidas"]}
        if pend:
            todos_pend[t] = pend
    manifiesto = {
        "schema": "ddd.nombres-comunidades/1.1", "version": VERSION,
        "entradas": {"poblacion": {"path": POBLACION, "sha256": sha256(RAIZ / POBLACION)},
                     "toponimos": {"path": TOPONIMOS, "sha256": sha256(RAIZ / TOPONIMOS)},
                     "comarcas": [{"path": p, "sha256": sha256(RAIZ / p)} for p, _ in FUENTES_COMARCAS],
                     "partidos_judiciales": {"path": PARTIDOS, "sha256": sha256(RAIZ / PARTIDOS)}},
        "territorios": resumen,
    }
    (salida / "MANIFEST.json").write_text(json.dumps(manifiesto, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"territorios={len(resumen)} distritos={sum(v['distritos'] for v in resumen.values())}")
    if todos_pend:
        print("TOPONIMIA PENDIENTE:", json.dumps(todos_pend, ensure_ascii=False))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
