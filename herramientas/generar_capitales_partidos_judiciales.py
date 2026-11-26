#!/usr/bin/env python3
"""Capital de cada partido judicial, extraída de las leyes autonómicas de capitalidad (BOE).

VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Capitales de partido judicial
FECHA: 2026-11-26
ESTADO: activo T-461
MOTIVO: Ley 38/1988 art. 4.4: la capitalidad la fijan las leyes de cada comunidad; partidos_judiciales.csv no la trae.
ANTERIOR: ninguno (herramienta nueva)

Fuente: `configuracion/fuentes/capitalidad_partidos/BOE-A-*.xml` (texto oficial del BOE, sha256 en la salida).
Cubre 12 comunidades; no están en el BOE consolidado Aragón, Baleares, Canarias, Cataluña y Galicia (ni Ceuta y Melilla).
La capital se localiza en el CSV de partidos por nombre y dentro del propio partido; lo que no casa se declara
en CASOS_EXPLICITOS con la cita de la ley, nunca de memoria.
Uso: python herramientas/generar_capitales_partidos_judiciales.py
"""
from __future__ import annotations

import csv
import hashlib
import re
import sys
import unicodedata
from pathlib import Path

VERSION = "1.0.0"
RAIZ = Path(__file__).resolve().parents[1]
FUENTES = RAIZ / "configuracion" / "fuentes" / "capitalidad_partidos"
PARTIDOS = RAIZ / "configuracion" / "partidos_judiciales.csv"
SALIDA = RAIZ / "configuracion" / "capitales_partidos_judiciales.csv"

PROV = {
    "almeria": "04", "cadiz": "11", "cordoba": "14", "granada": "18", "huelva": "21", "jaen": "23", "malaga": "29",
    "sevilla": "41", "albacete": "02", "ciudad real": "13", "cuenca": "16", "guadalajara": "19", "toledo": "45",
    "avila": "05", "burgos": "09", "leon": "24", "palencia": "34", "salamanca": "37", "segovia": "40", "soria": "42",
    "valladolid": "47", "zamora": "49", "badajoz": "06", "caceres": "10", "alicante": "03", "castellon": "12",
    "valencia": "46", "araba": "01", "bizkaia": "48", "gipuzkoa": "20",
}
# Capitales que la ley nombra por una localidad y el partido contiene como municipio de otro nombre.
# clave: (provincia, partido) → nombre del municipio INE; la ley lo dice en el propio texto citado.
CASOS_EXPLICITOS = {
    ("33", 2): ("Lena", "Pola de Lena es la capital del concejo de Lena (Ley 1/1989 Asturias, partido 2)"),
    ("33", 3): ("Cangas de Onís", "Cangas de Onís, concejo del partido 3"),
    ("33", 6): ("Siero", "Pola de Siero es la capital del concejo de Siero (Ley 1/1989 Asturias, partido 6)"),
    ("33", 9): ("Laviana", "Pola de Laviana es la capital del concejo de Laviana (Ley 1/1989 Asturias, partido 9)"),
    ("33", 15): ("Valdés", "Luarca es la capital del concejo de Valdés (Ley 1/1989 Asturias, partido 15)"),
    ("33", 18): ("Piloña", "Infiesto es la capital del concejo de Piloña (Ley 1/1989 Asturias, partido 18)"),
    ("18", 1): ("Loja", "la Ley 3/1989 Andalucía escribe «Laja» (errata evidente de Loja, único municipio del partido 1 de Granada con ese nombre aproximado)"),
}


# Partido creado tras el Anexo I de la Ley 38/1988 (no figura en partidos_judiciales.csv); cita de la ley de Cantabria.
NUEVOS = {"39020": "creado tras la Ley 38/1988: Castro Urdiales, Ley 3/1992 (citada en el preámbulo de la Ley 8/1992 de Cantabria)"}


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def plano(fichero: Path) -> str:
    t = fichero.read_text(encoding="utf-8")
    t = t[t.find("<texto>"):]
    t = re.sub(r"</(p|tr|li|table|td|th)>", " ¶ ", t)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", t)


def norm(s: str) -> str:
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    s = re.sub(r"\b(el|la|los|las|l|a|o|de|del|d)\b", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def claves_nombre(nombre_ine: str) -> set[str]:
    """«Coruña, A» → «coruna»; «Elx/Elche» → {«elx», «elche»}; sin artículos."""
    out = set()
    for parte in nombre_ine.split("/"):
        out.add(norm(parte))
        if "," in parte:
            out.add(norm(parte.split(",")[0]))
    return out


def _por_provincia(s: str, marca: str, num: str):
    """Itera (prov, numero, capital) en formatos «Provincia de X ... N Capital.»."""
    partes = re.split(marca, s, flags=re.I)
    for parte in partes[1:]:
        nom = norm(re.match(r"\s*([^¶]+?)\s*¶", parte).group(1))
        yield nom, parte


def leer_asturias(s):
    for n, cap in re.findall(r"Partido judicial (\d+), que comprende [^:]+: ([^.]+)\.", s):
        yield "33", int(n), cap.strip()


def leer_cyl(s):
    anexo = s[s.find("ANEXO"):]
    for nom, parte in _por_provincia(anexo, r"Provincia de ", ""):
        parte = re.split(r"¶ Provincia de ", parte)[0]
        for n, cap in re.findall(r"¶ (\d+) (?:¶ )+([^.¶]+)\.", parte):
            yield PROV[nom], int(n), cap.strip()


def leer_clm(s):
    anexo = s[s.find("ANEXOS A LA LEY"):]
    for nom, parte in _por_provincia(anexo, r"Provincia de ", ""):
        for n, cap in re.findall(r"¶ (\d+) ¶ ([^.¶]+)\.", parte):
            yield PROV[nom], int(n), cap.strip()


def leer_articulos(s, prov):
    """Navarra y Cantabria: «Se establecc?e en el municipio de X la capitalidad del partido judicial»."""
    for cap in re.findall(r"Se establecc?e en el municipio de (.+?) la capitalidad", s):
        yield prov, None, cap.strip()


def leer_rioja(s):
    for n, cap in re.findall(r"Partido Judicial (\d+), cuyo [^¶]*?Capitalidad ([^.¶]+)\.", s):
        yield "26", int(n), cap.strip()


def leer_murcia(s):
    for n, cap in re.findall(r"Partido Judicial número (\d+)\. Capitalidad: ([^.¶]+)\.", s):
        yield "30", int(n), cap.strip()


def leer_valencia(s):
    anexo = s[s.find("Artículo único"):]
    for nom, parte in _por_provincia(anexo, r"Provincia de ", ""):
        parte = re.split(r"¶ Provincia de ", parte)[0]
        for n, cap in re.findall(r"Partido Judicial número (\d+), ([^.¶]+)\.", parte):
            yield PROV[nom], int(n), cap.strip()


def leer_andalucia(s):
    anexo = s[s.find("ANEXO"):]
    for nom, parte in _por_provincia(anexo, r"PROVINCIA DE ", ""):
        parte = re.split(r"¶ PROVINCIA DE ", parte)[0]
        for n, cap in re.findall(r"Partido Judicial número (\d+) ¶ Capitalidad:? ([^¶]+?) ¶", parte):
            yield PROV[nom], int(n), cap.strip()


def leer_madrid(s):
    for n, cap in re.findall(r"Partido Judicial número (\d+): ([^.¶]+)\.", s):
        yield "28", int(n), cap.strip()


def leer_extremadura(s):
    cuerpo = s[s.find("Artículo 1.º"):s.find("Artículo 2.º")]
    for nom, parte in _por_provincia(cuerpo, r"Provincia de ", ""):
        parte = re.split(r"¶ Provincia de ", parte)[0]
        for n, cap in re.findall(r"¶ (\d+) (?:¶ )+([^.¶]+)\.", parte):
            yield PROV[nom], int(n), cap.strip()


def leer_paisvasco(s):
    cuerpo = s[s.find("Territorio Histórico de Araba"):]
    for nom, parte in _por_provincia(cuerpo, r"Territorio Histórico de ", ""):
        parte = re.split(r"¶ Territorio Histórico de ", parte)[0]
        for n, cap in re.findall(r"N\.º (\d+): Partido Judicial (?:de nueva creación )?integrado .*?Capitalidad: ([^.¶]+)\.", parte):
            yield PROV[nom], int(n), cap.strip()


LEYES = [
    ("BOE-A-1989-11182", "Ley 1/1989 Asturias", leer_asturias),
    ("BOE-A-1989-13850", "Ley 3/1989 Castilla y León", leer_cyl),
    ("BOE-A-1989-13994", "Ley 3/1989 Castilla-La Mancha", leer_clm),
    ("BOE-A-1989-23274", "Ley Foral 4/1989 Navarra", lambda s: leer_articulos(s, "31")),
    ("BOE-A-1990-1720", "Ley 6/1989 La Rioja", leer_rioja),
    ("BOE-A-1990-2732", "Ley 5/1989 Murcia", leer_murcia),
    ("BOE-A-1990-3265", "Ley 9/1989 Comunidad Valenciana", leer_valencia),
    ("BOE-A-1990-409", "Ley 3/1989 Andalucía", leer_andalucia),
    ("BOE-A-1990-516", "Ley 11/1989 Madrid", leer_madrid),
    ("BOE-A-1990-6061", "Ley 3/1989 Extremadura", leer_extremadura),
    ("BOE-A-1993-4195", "Ley 8/1992 Cantabria", lambda s: leer_articulos(s, "39")),
    ("BOE-A-2012-2855", "Ley 1/1990 País Vasco", leer_paisvasco),
]


def cargar_partidos():
    """→ (municipios por (prov, partido): [(codigo, nombre_ine)], partido de cada código)."""
    por_partido, partido_de = {}, {}
    with open(PARTIDOS, encoding="utf-8", newline="") as f:
        filas = csv.DictReader(l for l in f if not l.startswith("#"))
        for r in filas:
            k = (r["provincia"], int(r["partido_judicial"]))
            por_partido.setdefault(k, []).append((r["codigo_ine"], r["nombre_ine"]))
            partido_de[r["codigo_ine"]] = k
    return por_partido, partido_de


def resolver(cap, candidatos):
    """Municipio INE de `candidatos` cuyo nombre coincide con `cap` (exacto y, si no, por inclusión de palabras)."""
    c = norm(cap)
    exactos = [(cod, n) for cod, n in candidatos if c in claves_nombre(n)]
    if len(exactos) == 1:
        return exactos[0]
    parciales = [(cod, n) for cod, n in candidatos if any(c.startswith(k) or k.startswith(c) for k in claves_nombre(n))]
    return parciales[0] if len(parciales) == 1 else None


def generar():
    por_partido, partido_de = cargar_partidos()
    todos = [(cod, n, k) for k, v in por_partido.items() for cod, n in v]
    filas, problemas = [], []
    for ley_id, ley_nombre, lector in LEYES:
        fichero = FUENTES / f"{ley_id}.xml"
        huella = sha256(fichero)
        for prov, num, cap in lector(plano(fichero)):
            nueva = ""
            if num is None:  # sin número en la ley: el partido es el del municipio capital
                c = norm(cap).replace("viccente", "vicente")  # errata de la ley («San Viccente de la Barquera»)
                hallado = [(cod, n, k) for cod, n, k in todos if k[0] == prov and c in claves_nombre(n)]
                if not hallado:  # «Estella» frente a «Estella-Lizarra»
                    hallado = [(cod, n, k) for cod, n, k in todos if k[0] == prov and
                               any(x.startswith(c + " ") for x in claves_nombre(n))]
                if len(hallado) != 1:
                    problemas.append((ley_id, prov, cap, "sin partido")); continue
                cod, nombre, k = hallado[0]
                num = k[1]
                if cod in NUEVOS:  # partido creado después de la Ley 38/1988: no está en el CSV, que es el Anexo I
                    num = max(x[1] for x in por_partido if x[0] == prov) + 1
                    nueva = NUEVOS[cod]
            else:
                k = (prov, num)
                if k in CASOS_EXPLICITOS:
                    r = resolver(CASOS_EXPLICITOS[k][0], por_partido.get(k, []))
                elif k in por_partido:
                    r = resolver(cap, por_partido[k])
                else:  # partido de nueva creación (País Vasco): el municipio se busca en toda la provincia
                    r = resolver(cap, [(cod, n) for cod, n, kk in todos if kk[0] == prov])
                    nueva = "creado tras la Ley 38/1988 (la ley autonómica lo declara de nueva creación)"
                if r is None:
                    problemas.append((ley_id, prov, f"{num} {cap}", "no casa en el partido")); continue
                cod, nombre = r
            filas.append({"id_partido": f"{prov}-{num:02d}", "provincia": prov, "partido_judicial": num,
                          "capital_ley": cap, "codigo_ine": cod, "nombre_ine": nombre,
                          "nueva_creacion": nueva, "fuente": ley_nombre, "boe": ley_id, "sha256_boe": huella})
    return sorted(filas, key=lambda f: f["id_partido"]), problemas, por_partido


def main():
    filas, problemas, por_partido = generar()
    for p in problemas:
        print("PROBLEMA", p, file=sys.stderr)
    cubiertas = {f["id_partido"] for f in filas}
    cols = ["id_partido", "provincia", "partido_judicial", "capital_ley", "codigo_ine", "nombre_ine", "nueva_creacion", "fuente", "boe", "sha256_boe"]
    with open(SALIDA, "w", encoding="utf-8", newline="") as f:
        f.write("# fuente: leyes autonómicas de capitalidad de partidos judiciales (Ley 38/1988 art. 4.4), texto BOE en "
                "configuracion/fuentes/capitalidad_partidos; no cubre Aragón, Baleares, Canarias, Cataluña, Galicia, Ceuta ni Melilla\n")
        w = csv.DictWriter(f, cols, lineterminator="\n")
        w.writeheader()
        w.writerows(filas)
    print(f"{len(filas)} capitales; partidos del CSV sin capital: "
          f"{sum(1 for k in por_partido if f'{k[0]}-{k[1]:02d}' not in cubiertas)}; problemas: {len(problemas)}")
    return 1 if problemas else 0


if __name__ == "__main__":
    sys.exit(main())
