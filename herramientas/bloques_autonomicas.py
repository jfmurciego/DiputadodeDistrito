#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tabla APROBADA de bloques y alias de la doble vuelta para las elecciones autonómicas vigentes (T-421, D-167, D-168, D-170).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.2.0 · FECHA: 2026-11-20 · ESTADO: candidato
CAMBIOS: 1.2.0 (T-426): aut03 (Asturias) y aut14 (Murcia) entran con sus votos por distrito de datos/resultados/doble_vuelta_autonomicas/<aut>/<AAAAMM>/<aut>_partidos.csv (distrito, partido, votos; formato T-427); VIGENTES admite una ruta propia.
CAMBIOS: 1.1.0 (T-421, lista cerrada del propietario 19-11): ALIANÇA.CAT, UXGC, ANDALUCISTAS y ALHORA → Nacionalistas; SALF → Patriotas; DVC → Izquierdas; el resto de menores, sin bloque; la tabla pasa a configuracion/bloques_partidos_autonomicas_2026-11-19.csv (aprobada, sin PROPUESTA).
CAMBIOS: 1.0.1 (T-421, Planificador y revisor): CONTIGO-ZUREKIN, DO y 100x100 → Nacionalistas (propietario, 19-11); JUNTS+ → Nacionalistas (no es el JXC de D-170); la tabla va por partido tras el alias (como en el nacional) y el alias lleva una fila por sigla; una regla sin socio aprobado conserva la sigla como id.
CAMBIOS: 1.0.0 (T-421): fichero nuevo.
ANTERIOR: legacy/herramientas/bloques_autonomicas_v1.1.0_20261119.py
MOTIVO: la segunda tanda de la V4 (D-179) lleva los territorios `aut`; sus partidos deben tener bloque con las mismas reglas que las generales.
QUÉ HACE: lee los votos por partido de la elección vigente de cada comunidad (datos/resultados/historico/autonomicas/<c>/<AAAAMM>/<c>_partidos.csv,
  sha256 en la tabla) y escribe configuracion/bloques_partidos_autonomicas_2026-11-19.csv y configuracion/alias_partidos_autonomicas.csv.
  Bloque: (1) sigla ya en la tabla aprobada (bloques_partidos_2026-11-17.csv) → su bloque; (2) variante federada o coalición de un partido
  aprobado (REGLAS) → el mismo bloque; (3) sin bloque decidido en D-168/D-170 → vacío con motivo; (4) resto → sin bloque (propietario, 19-11: «el resto de menores, sin bloque»).
  Alias: reglas de sigla de datos/homologacion_siglas, tabla de homologación autonómica y variantes propuestas.
NO HACE: inventar votos, publicar ni tocar la tabla aprobada. Uso: python herramientas/bloques_autonomicas.py [--dudosos N]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import homologacion_siglas_autonomicas as ha  # noqa: E402

APROBADA = "configuracion/bloques_partidos_2026-11-17.csv"
HOMOLOG = "datos/homologacion_siglas/homologacion_siglas_autonomicas.csv"
SAL_BLOQUES = "configuracion/bloques_partidos_autonomicas_2026-11-19.csv"
SAL_ALIAS = "configuracion/alias_partidos_autonomicas.csv"
HIST = "datos/resultados/historico/autonomicas"

# territorio → (carpeta de resultados, elección AAAAMM[, ruta propia del CSV]). Extremadura (aut11, D-183) y Castilla-La Mancha (aut08,
# a la espera del fichero oficial) no tienen votos por partido de su elección vigente en el repositorio; Ceuta y Melilla (aut18, aut19) no tienen autonómicas.
DV = "datos/resultados/doble_vuelta_autonomicas/{0}/{1}/{0}_partidos.csv"  # T-426/T-427: votos por distrito (distrito, partido, votos)
VIGENTES = {
    "aut01": ("andalucia", "202605"), "aut03": ("asturias", "202305", DV.format("aut03", "202305")),
    "aut14": ("region_de_murcia", "202305", DV.format("aut14", "202305")), "aut02": ("aragon", "202602"), "aut04": ("illes_balears", "202305"),
    "aut05": ("canarias", "202305"), "aut06": ("cantabria", "202305"), "aut07": ("castilla_y_leon", "202603"),
    "aut09": ("cataluna", "202405"), "aut10": ("comunidad_valenciana", "202305"), "aut12": ("galicia", "202402"),
    "aut13": ("madrid", "202305"), "aut15": ("comunidad_foral_de_navarra", "202305"), "aut16": ("pais_vasco", "202404"),
    "aut17": ("la_rioja", "202305"),
}
IZQ, NAC, PAT = "Izquierdas", "Nacionalistas", "Patriotas"
# sigla de la fuente → (partido aprobado al que se suma o None, bloque, motivo). Variantes federadas y coaliciones; criterio: mismo partido, mismo bloque (D-168).
PROP = "decisión del propietario (19-11) "
PSOE = "variante federada del PSOE → Izquierdas (mismo partido, D-168)"
CPS = "coalición con Podemos/IU/Sumar → Izquierdas (criterio Podemos–Sumar e IU, D-168)"
REGLAS = {
    "PSOE-A": ("PSOE", IZQ, PSOE), "PSIB-PSOE": ("PSOE", IZQ, PSOE), "PSC-PSOE": ("PSOE", IZQ, PSOE), "PSC": ("PSOE", IZQ, PSOE),
    "PSN-PSOE": ("PSOE", IZQ, PSOE), "PSE-EE/PSOE": ("PSOE", IZQ, PSOE),
    "PPN": ("PP", PAT, "Partido Popular de Navarra = PP → Patriotas (D-168)"),
    "CCA": ("CCa", NAC, "grafía de CCa → Nacionalistas"), "NC-BC": ("NC", NAC, "Nueva Canarias (con BC) → Nacionalistas"),
    "El Pi": ("EL PI", NAC, "grafía de EL PI → Nacionalistas"), "P.C.P.E": ("PCPE", IZQ, "grafía de PCPE → Izquierdas"),
    "PCTE / ELAK": ("PCTE", IZQ, "PCTE → Izquierdas"), "PCAS-TC": ("PCAS", IZQ, "PCAS con TC → Izquierdas"),
    "FE DE LAS JONS": ("FE de las JONS", PAT, "grafía de FE de las JONS → Patriotas (D-168)"),
    "CUP - DT": ("CUP", NAC, "CUP con DT → Nacionalistas (izquierda nacionalista, D-167)"),
    "PODEMOS-IU": (None, IZQ, CPS), "PODEMOS-I.U.": (None, IZQ, CPS), "IU-SUMAR": (None, IZQ, CPS), "UNIDES PODEM-EUPV": (None, IZQ, CPS),
    "UNIDAS SÍ PODEMOS": (None, IZQ, CPS), "EUIB-PODEMOS": (None, IZQ, CPS), "PODEMOS-AV": (None, IZQ, CPS),
    "PODEMOS-AHAL DUGU - ALIANZA VERDE": (None, IZQ, CPS), "POR ANDALUCÍA": (None, IZQ, CPS), "COMUNS SUMAR": (None, IZQ, CPS),
    "SUMAR": (None, IZQ, CPS), "PODEMOS-IU-VERDES-AV": (None, IZQ, CPS), "IU-MÁS PAÍS-IAS": (None, IZQ, CPS),
    "PODEMOS ASTURIES": (None, IZQ, "variante regional de Podemos (Podemos–Sumar) → Izquierdas (Planificador, D-168/D-182: marca de partido ya aprobado)"),
    "V-Q": ("EQUO", IZQ, "Verdes-Equo = EQUO → Izquierdas (Planificador, D-168/D-182: marca de partido ya aprobado)"),
    "MR-VE": (None, IZQ, "Más Región (rama de Más País) con Verdes Equo → Izquierdas (Planificador, D-168/D-182: marca de partido ya aprobado)"), "EB-AZ": (None, IZQ, "Ezker Batua-Berdeak (IU) con Alianza Verde → Izquierdas (IU, D-168)"),
    "PAR-ES.C.": (None, "", "sin bloque (D-168: PAR)"), "Cs": (None, "", "sin bloque (D-168: Cs)"), "PACMA": (None, "", "sin bloque (D-168: PACMA)"),
    "CONTIGO-ZUREKIN": (None, NAC, "decisión del propietario (19-11, vía Planificador): nacionalistas antes que izquierdistas → Nacionalistas"),
    "DO": (None, NAC, "decisión del propietario (19-11, vía Planificador): → Nacionalistas"), "100x100": (None, NAC, "decisión del propietario (19-11, vía Planificador): → Nacionalistas"),
    "JUNTS+": (None, NAC, "Junts = CiU–Junts de la tabla aprobada → Nacionalistas (no es el JXC de 2016 de D-170)"), "SALF": (None, PAT, PROP + "→ Patriotas"),
    "ALIANÇA.CAT": (None, NAC, PROP + "→ Nacionalistas"), "UXGC": (None, NAC, PROP + "→ Nacionalistas"),
    "ANDALUCISTAS": (None, NAC, PROP + "→ Nacionalistas"), "ALHORA": (None, NAC, PROP + "→ Nacionalistas"), "DVC": (None, IZQ, PROP + "→ Izquierdas"),
}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def aprobada() -> dict[str, str]:
    out: dict[str, str] = {}
    for f in csv.DictReader((ROOT / APROBADA).open(encoding="utf-8", newline="")):
        out[f["siglas"]] = out.get(f["siglas"]) or f["bloque_propuesto"]
    return out


def homologadas() -> dict[tuple, str]:
    return {(f["comunidad"], f["eleccion"], f["sigla_fuente"]): f["partido_homologado"]
            for f in csv.DictReader((ROOT / HOMOLOG).open(encoding="utf-8", newline=""))}


def construir(max_dudosos: int = 15):
    ap, hom, reglas = aprobada(), homologadas(), ha.reglas()
    bloques, alias, dud, cob = [], [], [], {}
    for aut, (com, ele, *otra) in VIGENTES.items():
        ruta = Path(otra[0]) if otra else Path(HIST) / com / ele / f"{com}_partidos.csv"
        votos: Counter = Counter()
        for f in csv.DictReader((ROOT / ruta).open(encoding="utf-8", newline="")):
            votos[f["partido"]] += int(f["votos"])
        fsha = sha(ROOT / ruta)
        c = Counter()
        agr: dict = {}  # id tras el alias → [votos, fuentes, bloque, motivo]; la tabla va por partido homologado, como en el nacional
        for s, v in sorted(votos.items(), key=lambda t: (-t[1], t[0])):
            h, origen, fuente = hom.get((com, ele, s)), "HOMOLOGACION", HOMOLOG
            if h is None:
                h, _n, rid = ha.resolver(reglas, com, ele, s, "")
                origen, fuente = ("REGLAS", "datos/homologacion_siglas/reglas_generales.json") if rid != "IDENTIDAD" else ("IDENTIDAD", "")
            bloque, motivo = "", ""
            r = REGLAS.get(s)
            if r:
                if r[0]:
                    h, origen, fuente = r[0], "PROPUESTA", "herramientas/bloques_autonomicas.py"
                else:  # sin socio aprobado: el id sigue siendo la sigla (la tabla se decide por ella, no por la homologación general)
                    h, origen, fuente = s, "IDENTIDAD", ""
                bloque, motivo = r[1], r[2]
            elif h in ap:
                bloque = ap[h]
                motivo = f"misma sigla «{h}» en la tabla aprobada (D-168/D-170)" if bloque else f"sin bloque en la tabla aprobada («{h}»)"
            else:
                motivo = "sin bloque (propietario 19-11: resto de menores sin bloque)"
            alias.append({"comunidad": aut, "eleccion": ele, "id_fuente": s, "partido_homologado": h, "origen": origen, "fuente": fuente})
            g = agr.setdefault(h, [0, [], bloque, motivo])
            if g[2] != bloque:
                raise ValueError(f"{aut} {h}: dos bloques ({g[2]!r} / {bloque!r}) por {s}")
            g[0] += v
            g[1].append(s)
        for h, (v, fuentes, bloque, motivo) in sorted(agr.items(), key=lambda t: (-t[1][0], t[0])):
            decidido = bool(bloque) or motivo.startswith("sin bloque")
            c["con_bloque" if bloque else "sin_bloque_decidido" if decidido else "dudoso"] += v
            c["total"] += v
            bloques.append({"comunidad": aut, "eleccion": f"{ele[:4]}-{ele[4:]}", "siglas": h, "denominacion": " + ".join(fuentes), "bloque_propuesto": bloque,
                            "motivo": motivo, "votos": v, "fuente_sha256": fsha})
            if not decidido:
                dud.append((v, aut, f"{ele[:4]}-{ele[4:]}", h))
        cob[aut] = c
    dud.sort(key=lambda t: (-t[0], t[1], t[3]))
    return bloques, alias, dud[:max_dudosos], dud, cob


def escribir(ruta: str, filas: list[dict], campos: list[str]) -> None:
    with (ROOT / ruta).open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, campos, lineterminator="\n")
        w.writeheader()
        w.writerows(filas)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dudosos", type=int, default=15)
    a = ap.parse_args(argv)
    bloques, alias, top, todos, cob = construir(a.dudosos)
    escribir(SAL_BLOQUES, bloques, ["comunidad", "eleccion", "siglas", "denominacion", "bloque_propuesto", "motivo", "votos", "fuente_sha256"])
    escribir(SAL_ALIAS, alias, ["comunidad", "eleccion", "id_fuente", "partido_homologado", "origen", "fuente"])
    print("cobertura (% votos): comunidad con_bloque sin_bloque_decidido dudoso")
    T: Counter = Counter()
    for k, c in cob.items():
        T.update(c)
        print(k, *(f"{100 * c[x] / c['total']:.1f}" for x in ("con_bloque", "sin_bloque_decidido", "dudoso")))
    print("TOTAL", *(f"{100 * T[x] / T['total']:.1f}" for x in ("con_bloque", "sin_bloque_decidido", "dudoso")))
    print(f"dudosos (de {len(todos)}; mostrados {len(top)}):")
    for v, aut, ele, s in top:
        print(f"  {aut} {ele} {s} {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
