#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Adaptador de las autonómicas de la Región de Murcia (28-05-2023) del CREM a votos por sección (T-426).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-20 · ESTADO: candidato
CAMBIOS: 1.0.0: fichero nuevo.
ANTERIOR: ninguna (fichero nuevo)
MOTIVO: aut14 no tenía votos por partido de su elección vigente (ficha T-421). El CREM (econet.carm.es, PU2077) publica
  «Principales resultados según distrito y sección» de mayo de 2023 (excel/sec54.xls, Abanilla a Mazarrón, y sec55.xls,
  Molina a Yecla): son datos por sección, no municipales, así que no hay que repartir nada.
QUÉ HACE: lee los dos .xls (o su volcado CSV fiel, `fuentes/crem_murcia_2023/sec5X.csv`, que no necesita xlrd: la CI no lo instala; `xls_a_csv`
  lo genera), verifica su sha256, y escribe `secciones.csv` (section_id, party, votes; section_id = CUSEC de
  10 cifras: 30 + municipio INE + distrito + sección) y `MANIFEST.json` (huellas, cuadre contra la fila «Región de Murcia»).
  Solo las candidaturas de la tabla (PP, PSOE, VOX, Podemos+IU-Verdes+AV, MC Regional, Cs, Más Región-Verdes Equo);
  el resto de candidaturas no se desglosa en la fuente y se declara en `otros_votos` (= votos a candidaturas − suma).
NO HACE: descargar, ni lanzar, ni publicar.
Uso: python herramientas/adaptador_crem_murcia_2023.py --sec54 f54.(xls|csv) --sec55 f55.(xls|csv) --salida DIR
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FUENTES = {
    "sec54.xls": "62eb0b7bc9774f970ea8f008a06f884e3cb4ab9943d13186b33ef85513f57604",
    "sec55.xls": "dc910666c2941b62e41c06044071cb5e1d3004a19b2966f301de106fd6633846",
}
VOLCADOS = {  # volcado CSV celda a celda de cada hoja (xls_a_csv); el xls original sigue siendo la fuente de la huella oficial
    "sec54.csv": ("sec54.xls", "78d94df52dabee68d1066eaded67d907f79951092296f4b424b96aa11be8d917"),
    "sec55.csv": ("sec55.xls", "1e6cd86b095df5aa7917b0f462ccf4d4ed9b93d84e118e8f7e785a9e2a1c8990"),
}
URL = "https://econet.carm.es/web/crem/inicio/-/crem/sicrem/PU2077/excel/{}"
ELECCION = "28 de mayo de 2023"
PARTIDOS = {
    "Partido Popular (PP)": "PP",
    "Partido Socialista Obrero Español (PSOE)": "PSOE",
    "VOX (VOX)": "VOX",
    "Podemos-Izquierda Unida Verdes-Alianza Verde (Podemos +IU-Verdes + AV)": "PODEMOS-IU-VERDES-AV",
    "MC Regional (MC REG)": "MC REG",
    "Ciudadanos-Partido de la Ciudadanía (Cs)": "Cs",
    "Mas Region-Verdes Equo (MR-VE)": "MR-VE",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFD", s)
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in s if unicodedata.category(c) != "Mn").lower())


def municipios_ine(raiz: Path = ROOT) -> dict[str, str]:
    """{nombre normalizado: código INE de 3 cifras} de Murcia (provincia 30)."""
    out = {}
    with (raiz / "datos/distritos/municipios_ine_2025.csv").open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if r["codigo_ine"].startswith("30"):
                out[_norm(r["nombre_ine"])] = r["codigo_ine"][2:]
    return out


def _codigo(txt: str, muni: dict[str, str], path: Path) -> str:
    n = _norm(txt)
    if n in muni:
        return muni[n]
    cand = [c for k, c in muni.items() if k.startswith(n)]  # el CREM abrevia («Fuente Álamo» por «Fuente Álamo de Murcia»)
    if len(cand) != 1:
        raise ValueError(f"{path.name}: municipio sin código INE único: {txt!r} {cand}")
    return cand[0]


def xls_a_csv(xls: Path, destino: Path) -> None:
    """Vuelca la primera hoja celda a celda (requiere xlrd; solo para regenerar el volcado versionado)."""
    import xlrd
    h = xlrd.open_workbook(str(xls)).sheet_by_index(0)
    with destino.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        for r in range(h.nrows):
            w.writerow(h.row_values(r))


class _Hoja:
    """Hoja en memoria con la interfaz mínima de xlrd (nrows, cell_value, row_values)."""

    def __init__(self, filas):
        self.filas, self.nrows = filas, len(filas)

    def row_values(self, r):
        return self.filas[r]

    def cell_value(self, r, c):
        return self.filas[r][c]


def _abrir(path: Path):
    if path.suffix.lower() != ".csv":
        import xlrd
        return xlrd.open_workbook(str(path)).sheet_by_index(0)
    filas = []
    with path.open(encoding="utf-8", newline="") as f:
        for fila in csv.reader(f):
            # columna 0 es texto (rótulos, «001»); el resto son números o vacío, como en el xls
            filas.append([fila[0]] + [float(c) if re.fullmatch(r"-?\d+(\.\d+)?(e[+-]?\d+)?", c, re.I) else c for c in fila[1:]])
    return _Hoja(filas)


def leer_xls(path: Path, muni: dict[str, str]) -> tuple[dict, dict, dict]:
    """(votos por CUSEC → {sigla: votos}, total regional de la hoja si lo trae)."""
    hoja = _abrir(path)
    cab = next(r for r in range(hoja.nrows) if str(hoja.cell_value(r, 0)).strip() == "" and "CENSO" in [str(c).strip() for c in hoja.row_values(r)])
    nombres = [str(c).strip() for c in hoja.row_values(cab) if str(c).strip()]
    # tras el rótulo de la fila de encabezado, cada magnitud ocupa dos columnas (electores, porcentaje)
    pos = {n: 1 + 2 * i for i, n in enumerate(nombres)}
    faltan = [n for n in PARTIDOS if n not in pos]
    if faltan:
        raise ValueError(f"{path.name}: candidaturas ausentes {faltan}")
    if not any(ELECCION in str(c) for r in range(cab) for c in hoja.row_values(r)):
        raise ValueError(f"{path.name}: no es la elección del {ELECCION}")
    votos, valid, cera = {}, {}, {}
    cod = dist = None
    for r in range(cab + 2, hoja.nrows):
        fila = hoja.row_values(r)
        crudo = str(fila[0])
        txt = crudo.strip()
        if not txt or not isinstance(fila[1], float):
            continue
        sangria = len(crudo) - len(crudo.lstrip())
        if txt.startswith("Región"):
            continue
        if sangria <= 4 and not txt.isdigit():
            if txt.upper().startswith("C.E.R.A"):  # voto exterior: sin sección; se declara, no se reparte
                cod = None
                cera[path.name] = int(fila[pos["Votos a candidaturas"]])
                continue
            cod, dist = _codigo(txt, muni, path), None
        elif cod is None:
            continue
        elif txt.isdigit() and len(txt) == 2:
            dist = txt
        elif txt.isdigit() and len(txt) == 3:
            cusec = "30" + cod + dist + txt
            votos[cusec] = {PARTIDOS[n]: int(fila[pos[n]]) for n in PARTIDOS}
            valid[cusec] = int(fila[pos["Votos a candidaturas"]])
    return votos, valid, cera


def construir(sec54: Path, sec55: Path, salida: Path, raiz: Path = ROOT) -> dict:
    muni = municipios_ine(raiz)
    huellas = {}
    todos, valid, cera = {}, {}, {}
    for nombre, ruta in (("sec54.xls", sec54), ("sec55.xls", sec55)):
        h = sha256(ruta)
        if ruta.suffix.lower() == ".csv":  # volcado versionado: su huella y la del xls original que reproduce
            volc = VOLCADOS.get(ruta.name)
            if volc is None or volc[0] != nombre or h != volc[1]:
                raise ValueError(f"sha256 del volcado {ruta.name} no coincide: {h}")
            huellas[nombre] = FUENTES[nombre]
            huellas[ruta.name] = h
        else:
            if h != FUENTES[nombre]:
                raise ValueError(f"sha256 de {nombre} no coincide: {h}")
            huellas[nombre] = h
        v, c, ce = leer_xls(ruta, muni)
        cera.update(ce)
        if set(v) & set(todos):
            raise ValueError("sección repetida entre las dos hojas")
        todos.update(v)
        valid.update(c)
    salida.mkdir(parents=True, exist_ok=True)
    with (salida / "secciones.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["section_id", "party", "votes"])
        for s in sorted(todos):
            for p, n in sorted(todos[s].items()):
                w.writerow([s, p, n])
    suma = {p: sum(v[p] for v in todos.values()) for p in PARTIDOS.values()}
    otros = sum(valid.values()) - sum(suma.values())
    man = {"schema": "ddd-crem-murcia-2023/1.0", "territory_id": "aut14", "election_date": "2023-05-28",
           "fuentes": {n: {"url": URL.format(n), "sha256": h} for n, h in huellas.items()},
           "secciones": len(todos), "votos_por_partido": suma, "votos_a_candidaturas": sum(valid.values()),
           "otros_votos": otros, "cera_votos_a_candidaturas_excluidos": sum(cera.values()), "nota": "las candidaturas menores no se desglosan en la fuente (otros_votos)"}
    (salida / "MANIFEST.json").write_text(json.dumps(man, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return man


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--sec54", type=Path, required=True)
    ap.add_argument("--sec55", type=Path, required=True)
    ap.add_argument("--salida", type=Path, required=True)
    a = ap.parse_args(argv)
    m = construir(a.sec54, a.sec55, a.salida)
    print(json.dumps({k: m[k] for k in ("secciones", "votos_por_partido", "votos_a_candidaturas", "otros_votos")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
