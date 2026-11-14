#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Votos por partido y distrito en git (T-67).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.4.0 · FECHA: 2026-11-10 · ESTADO: candidato
CAMBIOS: 1.4.0 (T-199, hueco 3 del ensayo T-197): la fecha de la elección ya no es solo una constante. ``fecha_generales_2026``
  la lee de configuracion/elecciones_generales_2026.yaml; ``contratos(ruta, fecha)`` y ``generar(..., fecha)`` filtran por
  ella y ``--fecha`` acepta AAAA-MM-DD o «2026». El valor por defecto sigue siendo FECHA = 2023-07-23 (legislatura vigente):
  sin argumentos nada cambia.
  1.3.0 (T-104, decisión del propietario del 08-11): una sección partida cuyas secciones M06 candidatas caen
  todas en el mismo distrito es «contenida_distrito»: el distrito es exacto y no cuenta para el tope D-17 (el reparto
  entre secciones sigue D-13 y queda en el informe). Regla general, no excepción: se retira CASOS_APARTE (Valencia,
  Bétera entera en un distrito, queda en 0 % partido). No se regenera ningún M06.
  1.2.0 (T-103, decisión del propietario del 08-11): cada sección del ZIP sin distrito se clasifica con la
  tabla de equivalencia en «recodificada» (tipo 1:1: misma geometría), «contenida» (una sola sección M06 recibe al
  menos el 95 % de su área: distrito exacto) o «partida» (varias secciones M06). Las dos primeras se asignan 1:1 y no
  cuentan para el tope D-17; solo cuentan las partidas (``votos_partidos``/``pct_partido`` del informe). El tope y el
  reparto D-13 de las partidas no cambian. Valencia (46) queda como caso aparte pendiente del propietario: sigue con
  fallo estricto y el error lo señala (CASOS_APARTE, sin excepción).
  1.1.0 (T-101, D-17): ``agregar`` acepta la tabla de equivalencia de las secciones del ZIP ausentes del M06
  (configuracion/equivalencia_secciones_congreso_2023.csv, herramientas/equivalencia_congreso_2023.py) y la población
  de la composición: si el desajuste de secciones es ≤ 0,5 % de los votos a candidaturas de la provincia, reparte los
  votos (y blancos, nulos y censo) de cada sección del ZIP sin distrito entre los distritos de sus secciones M06 con
  peso de población (D-13; área si no hay población), en enteros por restos mayores, y devuelve la lista de
  desajustes (``agregar_informe``). Por encima del tope, o sin tabla, falla como en 1.0.0.
MOTIVO 1.4.0: con contratos de 2026 ``contratos()`` no habría encontrado ninguno.
MOTIVO 1.1.0: Málaga, Alicante y Barcelona (T-101): el ZIP de Interior y el seccionado INE 2023 del M06 difieren en unas
  pocas secciones (recodificaciones) y el archivista fallaba con PARTIDOS_ORIGEN_FAILED.
ANTERIOR: legacy/herramientas/resultados_partidos_v1.3.0_20261110.py
QUÉ HACE: por cada territorio con composición sección→distrito acreditada (datos/composicion, T-67) y M08 vigente
  (datos/resultados), agrega los votos por partido del ZIP nacional por mesa de Infoelectoral (release
  fuente-infoelectoral-02202307; huella y totales comprobados con herramientas/fuente_infoelectoral_mesas.convert)
  sobre los distritos y escribe datos/resultados/<territorio>_partidos.csv:
  distrito, partido, votos, porcentaje (sobre votos a candidaturas del distrito), blancos, nulos, censo.
  Falla (sin escribir el territorio) si: hay secciones del ZIP sin distrito o distritos con secciones ausentes del ZIP
  (salvo la tolerancia D-17 de ``agregar`` con tabla de equivalencia, que usa el archivista);
  la suma por partido de los distritos no es el total provincial del ZIP; o el ganador de algún distrito no es el del M08
  publicado. Añade la clave ``partidos`` a datos/resultados/MANIFEST.json (sha256 del CSV, de la composición y del ZIP).
  Salida determinista; un CSV que no cambia no se reescribe.
Uso: python herramientas/resultados_partidos.py [--zip ZIP] [--salida DIR] [--composicion DIR] [--registro JSON]
  [--territorios t1,t2|todos]   (sin --zip lo baja del release con gh y comprueba su sha256)
"""
from __future__ import annotations

import argparse
import csv
import datetime
import hashlib
import io
import json
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import fuente_infoelectoral_mesas as fim  # noqa: E402
import resultados_ligeros as rl  # noqa: E402

SALIDA = ROOT / "datos/resultados"
COMPOSICION = ROOT / "datos/composicion"
CONTRATOS = ROOT / "configuracion/contratos_infoelectoral.yaml"
FECHA = "2023-07-23"  # elección por defecto (legislatura vigente); ver fecha_generales_2026
ELECCIONES_2026 = ROOT / "configuracion/elecciones_generales_2026.yaml"
EQUIVALENCIA = ROOT / "configuracion/equivalencia_secciones_congreso_2023.csv"
EQUIVALENCIA_META = ROOT / "configuracion/equivalencia_secciones_congreso_2023.json"
EQUIVALENCIA_MAYORIA = ROOT / "configuracion/equivalencia_seccionado_ine_2026_a_2023.csv"  # T-291, elecciones ≠ FECHA
TOPE_DESAJUSTE = 0.005  # D-17: fracción de los votos a candidaturas de la provincia
CONTENIDA_MIN = 0.95  # T-103: parte mínima del área de la sección del ZIP en una sola sección M06 (UMBRAL de T-85)
CABECERA = ["distrito", "partido", "votos", "porcentaje", "blancos", "nulos", "censo"]


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _fecha_valida(valor: str, origen: str) -> str:
    try:
        if len(valor) != 10 or valor[4] != "-" or valor[7] != "-":
            raise ValueError
        datetime.date.fromisoformat(valor)
    except ValueError:
        raise ValueError(f"{origen}: fecha no válida {valor!r} (se espera AAAA-MM-DD real)") from None
    return valor


def fecha_generales_2026(ruta: Path = ELECCIONES_2026) -> str:
    """election_date (AAAA-MM-DD) del universo de las generales de 2026; error claro si falta o no es una fecha real."""
    try:
        datos = yaml.safe_load(ruta.read_text(encoding="utf-8"))
    except OSError as e:
        raise ValueError(f"{ruta.name}: no se puede leer {ruta} ({e})") from None
    valor = datos.get("election_date") if isinstance(datos, dict) else None
    if valor in (None, ""):
        raise ValueError(f"{ruta.name}: falta la clave election_date en {ruta}")
    return _fecha_valida(str(valor), f"{ruta.name}: election_date")


def resolver_fecha(valor: str | None) -> str:
    """None → FECHA; «2026» → la del YAML de 2026; cualquier otra cosa debe ser una fecha real AAAA-MM-DD."""
    if valor in (None, ""):
        return FECHA
    if valor == "2026":
        return fecha_generales_2026()
    return _fecha_valida(valor, "--fecha")


def contratos(ruta: Path = CONTRATOS, fecha: str = FECHA) -> dict[str, dict]:
    """territorio → contrato Infoelectoral de la elección `fecha` (por defecto FECHA)."""
    raw = yaml.safe_load(ruta.read_text(encoding="utf-8"))["contracts"]
    return {r["territory_id"]: {"election_id": k, **r} for k, r in raw.items() if str(r.get("election_date")) == fecha}


def vigentes_eleccion(registro: Path, fecha: str = FECHA) -> dict[str, dict]:
    """Como rl.vigentes, pero solo los canonical_m08 de la elección `fecha` (sin election_date → FECHA, T-199)."""
    prods: dict[str, dict] = {}
    for p in json.loads(registro.read_text(encoding="utf-8"))["products"]:
        if p.get("kind") == "canonical_m08" and str(p.get("election_date") or FECHA) == fecha:
            t = p["territory_id"]
            if t not in prods or int(p["run_id"]) > int(prods[t]["run_id"]):
                prods[t] = p
    return dict(sorted(prods.items()))


def bajar_zip(contrato: dict, destino: Path) -> Path:
    m = contrato["mirror"]
    asset = subprocess.run(["gh", "api", f"repos/{rl.REPO}/releases/tags/{m['release_tag']}", "--jq",
                            f".assets[]|select(.name==\"{m['asset']}\")|.id"], capture_output=True, text=True, check=True).stdout.strip()
    r = subprocess.run(["gh", "api", f"repos/{rl.REPO}/releases/assets/{asset}", "-H", "Accept: application/octet-stream"],
                       capture_output=True, check=True)
    destino.write_bytes(r.stdout)
    return destino


def leer_composicion(ruta: Path) -> dict[str, int]:
    return {r["seccion"]: int(r["distrito"]) for r in csv.DictReader(io.StringIO(ruta.read_text(encoding="utf-8")))}


def leer_poblacion(ruta: Path) -> dict[str, int]:
    return {r["seccion"]: int(r.get("poblacion") or 0) for r in csv.DictReader(io.StringIO(ruta.read_text(encoding="utf-8")))}


def leer_equivalencia(ruta: Path = EQUIVALENCIA) -> dict[str, list[dict]]:
    """seccion_zip → [{seccion_m06, tipo, peso_area, frac_m06}]; comprueba el sha256 del CSV contra su JSON hermano."""
    cuerpo = ruta.read_bytes()
    meta = ruta.with_suffix(".json")
    if meta.is_file():
        esperado = json.loads(meta.read_text(encoding="utf-8"))["csv"]["sha256"]
        if sha256(cuerpo) != esperado:
            raise ValueError(f"sha256 de {ruta.name} no coincide con {meta.name}")
    out: dict[str, list[dict]] = defaultdict(list)
    for r in csv.DictReader(io.StringIO(cuerpo.decode("utf-8"))):
        out[r["seccion_zip"]].append({"seccion_m06": r["seccion_m06"], "tipo": r["tipo"],
                                      "peso_area": float(r["peso_area"]), "frac_m06": float(r["frac_m06"])})
    return dict(out)


def leer_equivalencia_mayoria(ruta: Path = EQUIVALENCIA_MAYORIA) -> dict[str, dict]:
    """seccion_2026 → {"tipo", "pesos": [(seccion_2023, peso_poblacion)]}; sha256 del CSV contra su JSON hermano."""
    cuerpo = ruta.read_bytes()
    esperado = json.loads(ruta.with_suffix(".json").read_text(encoding="utf-8"))["csv"]["sha256"]
    if sha256(cuerpo) != esperado:
        raise ValueError(f"sha256 de {ruta.name} no coincide con su JSON")
    out: dict[str, dict] = {}
    filas = csv.reader(io.StringIO(cuerpo.decode("utf-8")))
    cab = next(filas)
    i_tipo, i_peso = cab.index("tipo"), cab.index("peso_poblacion")
    for r in filas:
        e = out.setdefault(r[0], {"tipo": r[i_tipo], "pesos": []})
        if r[i_tipo] != "sin_vigente":
            e["pesos"].append((r[1], float(r[i_peso])))
    return out


def destino_por_mayoria(entrada: dict, comp: dict[str, int]) -> str | None:
    """Regla de M07 7.4.0: la sección va entera al distrito con más peso de población (la parte sin distrito cuenta como
    bloque propio y, si gana, devuelve None) y, dentro de él, a su sección de más peso; empates por código."""
    if entrada["tipo"] == "sin_vigente" or not entrada["pesos"]:
        return None
    falta = "\x00MISSING_IN_MAP"
    por_d: dict[str, float] = defaultdict(float)
    for v, w in entrada["pesos"]:
        por_d[str(comp[v]) if v in comp else falta] += w
    d = min(por_d, key=lambda k: (-por_d[k], k == falta, k))
    if d == falta:
        return None
    return min(((v, w) for v, w in entrada["pesos"] if v in comp and str(comp[v]) == d), key=lambda x: (-x[1], x[0]))[0]


def aplicar_mayoria(por_seccion: dict, extra09: dict, comp: dict[str, int], tabla: dict) -> tuple[dict, dict, dict]:
    """Mueve votos, censo, blancos y nulos de cada sección de la tabla a su destino (todas a la vez, sin encadenar)."""
    alias, filas = {}, []
    for s in sorted(set(por_seccion) | set(extra09)):
        if s not in tabla:
            continue
        v = destino_por_mayoria(tabla[s], comp)
        if v is None:
            continue
        alias[s] = v
        distritos = {comp[t] for t, _ in tabla[s]["pesos"] if t in comp}
        filas.append({"seccion": s, "clase": tabla[s]["tipo"], "destino": v, "distrito": comp[v],
                      "votos": sum(por_seccion.get(s, {}).values()), "entre_distritos": len(distritos) > 1})
    votos: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for s, d in por_seccion.items():
        for p, n in d.items():
            votos[alias.get(s, s)][p] += n
    meta: dict[str, dict[str, int]] = defaultdict(lambda: {"censo": 0, "blancos": 0, "nulos": 0})
    for s, d in extra09.items():
        for k, n in d.items():
            meta[alias.get(s, s)][k] += n
    informe = {"decision": "D-65; regla de M07 7.4.0 (partida entera al distrito de mayor población)",
               "tabla": EQUIVALENCIA_MAYORIA.relative_to(ROOT).as_posix(), "asignaciones": filas,
               "votos_por_mayoria_entre_distritos": sum(f["votos"] for f in filas if f["entre_distritos"])}
    return votos, dict(meta), informe


def repartir(n: int, pesos: dict[int, float]) -> dict[int, int]:
    """Reparte el entero n según pesos (suman 1) por restos mayores; desempate por distrito."""
    base = {d: int(n * w) for d, w in pesos.items()}
    resto = n - sum(base.values())
    for d in sorted(pesos, key=lambda d: (-(n * pesos[d] - base[d]), d))[:resto]:
        base[d] += 1
    return base


def mesas_09(zip_path: Path, contrato: dict) -> dict[str, dict[str, int]]:
    """sección (10 dígitos) → censo, blancos y nulos de las mesas de la provincia (sin CERA)."""
    import zipfile
    prefijo, prov = str(contrato["election_prefix"]), str(contrato["province"]).zfill(2)
    out: dict[str, dict[str, int]] = defaultdict(lambda: {"censo": 0, "blancos": 0, "nulos": 0})
    with zipfile.ZipFile(zip_path) as z:
        for line in fim._records(z, contrato["files"]["mesas"]):
            if not line.startswith(prefijo) or line[11:13] != prov or line[13:16] == fim.CERA_MUNICIPALITY:
                continue
            s = out[line[11:13] + line[13:16] + line[16:18] + f"{int(line[18:22].strip()):03d}"]
            s["censo"] += fim._int(line, 24, 30)
            s["blancos"] += fim._int(line, 66, 72)
            s["nulos"] += fim._int(line, 73, 79)
    return dict(out)


def agregar(zip_path: Path, contrato: dict, comp: dict[str, int], m08_ganadores: list[str], **kw) -> bytes:
    """CSV de votos por partido y distrito; ValueError si algo no cuadra (ver módulo)."""
    return agregar_informe(zip_path, contrato, comp, m08_ganadores, **kw)[0]


def clasificar(destinos: list[dict], comp: dict[str, int] | None = None) -> str:
    """T-103: «recodificada» (1:1), «contenida» (≥ CONTENIDA_MIN del área en una sola sección M06) o «partida».
    T-104: con la composición, una partida cuyas secciones M06 están todas en el mismo distrito es «contenida_distrito»."""
    if any(e["tipo"] == "1:1" for e in destinos):
        return "recodificada"
    if len(destinos) == 1 and destinos[0]["peso_area"] >= CONTENIDA_MIN:
        return "contenida"
    if comp is not None and len({comp.get(e["seccion_m06"]) for e in destinos}) == 1 and destinos[0]["seccion_m06"] in comp:
        return "contenida_distrito"
    return "partida"


def _desajustes(por_seccion, extra09, comp, equivalencia, poblacion, total, tope):
    """D-17: {sección del ZIP sin distrito: {distrito: peso}} y el informe; ValueError por encima del tope.
    Solo las secciones partidas cuentan para el tope (T-103); recodificadas y contenidas van 1:1; las contenidas en un
    distrito (T-104) se reparten entre secciones con D-13 pero su distrito es exacto."""
    zsec = set(extra09)
    falta, sobra = sorted(zsec - set(comp)), sorted(set(comp) - zsec)
    msg = (f"secciones del ZIP sin distrito {len(falta)} (p. ej. {falta[:3]}); "
           f"secciones de la composición ausentes del ZIP {len(sobra)} (p. ej. {sobra[:3]})")
    if equivalencia is None:
        raise ValueError(msg)
    destinos, clase = {}, {}
    for s in falta:
        destinos[s] = [e for e in equivalencia.get(s, []) if e["seccion_m06"] in comp]
        if not destinos[s]:
            raise ValueError(f"{msg}; la sección {s} del ZIP no tiene equivalencia con secciones del M06 (D-17)")
        clase[s] = clasificar(destinos[s], comp)
    votos_s = {s: sum(por_seccion.get(s, {}).values()) for s in falta}
    v_des = sum(votos_s.values())
    partidas = [s for s in falta if clase[s] == "partida"]
    v_par = sum(votos_s[s] for s in partidas)
    pct = 100 * v_des / total if total else 100.0
    pct_par = 100 * v_par / total if total else 100.0
    if pct_par > 100 * tope:
        prov = falta[0][:2]
        lista = ", ".join(f"{s}={votos_s[s]}" for s in partidas)
        raise ValueError(f"{msg}; desajuste partido {pct_par:.4f} % de los votos de la provincia > tope {100 * tope:g} %"
                         f" (D-17) [secciones partidas: {lista}] (provincia {prov})")
    reparto, filas = {}, []
    for s in falta:
        if clase[s] in ("partida", "contenida_distrito"):
            bruto = {e["seccion_m06"]: e["frac_m06"] * poblacion.get(e["seccion_m06"], 0) for e in destinos[s]}
            regla = "D-17: partida; reparto por población de la sección M06 (D-13) con la tabla de T-85"
            if sum(bruto.values()) <= 0:
                bruto = {e["seccion_m06"]: e["peso_area"] for e in destinos[s]}
                regla = "D-17: partida; reparto por área (sin población) con la tabla de T-85"
            if clase[s] == "contenida_distrito":
                regla = f"T-104: contenida en el distrito {comp[destinos[s][0]['seccion_m06']]}, fuera del tope D-17; " + regla.split("; ", 1)[1]
        else:
            v = next((e for e in destinos[s] if e["tipo"] == "1:1"), destinos[s][0])["seccion_m06"]
            bruto = {v: 1.0}
            regla = (f"T-103: {clase[s]}; asignación 1:1 a {v} con la tabla de T-85, fuera del tope D-17")
        tot = sum(bruto.values())
        pesos: dict[int, float] = defaultdict(float)
        for v, x in bruto.items():
            pesos[comp[v]] += x / tot
        reparto[s] = dict(pesos)
        filas.append({"seccion": s, "origen": "zip_sin_m06", "clase": clase[s], "votos": votos_s[s],
                      "secciones_m06": {v: round(x / tot, 6) for v, x in sorted(bruto.items())},
                      "distritos": {str(d): round(w, 6) for d, w in sorted(pesos.items())}, "regla": regla})
    for s in sobra:
        filas.append({"seccion": s, "origen": "m06_sin_zip", "votos": 0, "secciones_m06": {s: 1.0},
                      "distritos": {str(comp[s]): 1.0}, "regla": "D-17: sección del M06 sin mesas en el ZIP; 0 votos"})
    informe = {"decision": "D-17; T-103 y T-104 (solo las partidas entre distritos cuentan para el tope)", "tope_pct": 100 * tope,
               "votos_candidaturas": total, "votos_desajustados": v_des, "pct_desajuste": round(pct, 4),
               "votos_partidos": v_par, "pct_partido": round(pct_par, 4), "desajustes": filas}
    return reparto, informe


def agregar_informe(zip_path: Path, contrato: dict, comp: dict[str, int], m08_ganadores: list[str],
                    equivalencia: dict | None = None, poblacion: dict[str, int] | None = None,
                    tope: float = TOPE_DESAJUSTE, mayoria: dict | None = None) -> tuple[bytes, dict]:
    """Como ``agregar`` y además el informe de desajustes D-17 (vacío si las secciones coinciden)."""
    with tempfile.TemporaryDirectory() as tmp:
        resumen = fim.convert(zip_path, contrato, Path(tmp) / "mesas.csv")  # huella y totales del contrato
        filas = list(csv.DictReader(open(Path(tmp) / "mesas.csv", encoding="utf-8")))
    por_seccion: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for r in filas:
        sec = r["codigo_provincia"] + r["codigo_municipio"] + r["codigo_distrito"] + r["codigo_seccion"]
        por_seccion[sec][r["partido"]] += int(r["votos"])
    extra09 = mesas_09(zip_path, contrato)
    reparto, informe = {}, {}
    if mayoria is not None:
        por_seccion, extra09, informe = aplicar_mayoria(por_seccion, extra09, comp, mayoria)
        falta = sorted(set(extra09) - set(comp))
        if falta:
            raise ValueError(f"secciones del ZIP sin distrito tras la equivalencia {len(falta)} (p. ej. {falta[:3]})")
    elif set(extra09) != set(comp):
        reparto, informe = _desajustes(por_seccion, extra09, comp, equivalencia, poblacion or {},
                                       resumen["candidate_votes"], tope)
    votos: dict[int, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    meta: dict[int, dict[str, int]] = defaultdict(lambda: {"censo": 0, "blancos": 0, "nulos": 0})
    for sec, d in comp.items():
        for p, v in por_seccion.get(sec, {}).items():
            votos[d][p] += v
        for k, v in extra09.get(sec, {}).items():
            meta[d][k] += v
    for sec, pesos in reparto.items():
        for p, v in por_seccion.get(sec, {}).items():
            for d, x in repartir(v, pesos).items():
                if x:
                    votos[d][p] += x
        for k, v in extra09[sec].items():
            for d, x in repartir(v, pesos).items():
                meta[d][k] += x
    total_zip: dict[str, int] = defaultdict(int)
    for s in por_seccion.values():
        for p, v in s.items():
            total_zip[p] += v
    total_dist: dict[str, int] = defaultdict(int)
    for d in votos.values():
        for p, v in d.items():
            total_dist[p] += v
    if dict(total_dist) != dict(total_zip) or sum(total_dist.values()) != resumen["candidate_votes"]:
        raise ValueError("la suma por partido de los distritos no coincide con el total provincial del ZIP")
    distritos = sorted(set(comp.values()))
    if len(distritos) != len(m08_ganadores):
        raise ValueError(f"distritos {len(distritos)} != distritos del M08 {len(m08_ganadores)}")
    s = io.StringIO()
    w = csv.writer(s, lineterminator="\n")
    w.writerow(CABECERA)
    for d, g_m08 in zip(distritos, m08_ganadores):
        orden = sorted(votos[d].items(), key=lambda kv: (-kv[1], kv[0]))
        if not orden or orden[0][0] != g_m08:
            raise ValueError(f"distrito {d}: ganador {orden[0][0] if orden else None} != M08 {g_m08}")
        tot = sum(v for _, v in orden)
        for p, v in orden:
            w.writerow([d, p, v, f"{v * 100 / tot:.4f}" if tot else "", meta[d]["blancos"], meta[d]["nulos"], meta[d]["censo"]])
    return s.getvalue().encode("utf-8"), informe


def generar(salida: Path = SALIDA, registro: Path = rl.REGISTRO_VISOR, composicion: Path = COMPOSICION,
            zip_path: Path | None = None, territorios: list[str] | None = None, contratos_yaml: Path = CONTRATOS,
            fecha: str = FECHA) -> dict:
    ctr = contratos(contratos_yaml, fecha)
    m08 = vigentes_eleccion(registro, fecha)
    ruta_man = composicion / "MANIFEST.json"
    comps = json.loads(ruta_man.read_text(encoding="utf-8"))["territorios"] if ruta_man.exists() else {}
    ruta_sal = salida / "MANIFEST.json"
    man = json.loads(ruta_sal.read_text(encoding="utf-8")) if ruta_sal.exists() else {"schema": "ddd.resultados-ligeros/1.0", "territorios": {}}
    previo = man.get("partidos", {})
    nuevo: dict[str, dict] = {}
    omitidos: list[str] = []
    tmp = tempfile.TemporaryDirectory()
    try:
        for t in sorted(m08):
            if territorios is not None and t not in territorios:
                if t in previo:
                    nuevo[t] = previo[t]
                continue
            cm, rutac = comps.get(t), composicion / f"{t}.csv"
            if t not in ctr or not cm or not rutac.exists() or sha256(rutac.read_bytes()) != cm["sha256_csv"]:
                omitidos.append(t)
                continue
            gan = rl.ganadores(salida, t, m08[t])
            if gan is None:
                omitidos.append(t)
                continue
            ant, rutap = previo.get(t), salida / f"{t}_partidos.csv"
            if (ant and ant["blob_sha_m08"] == m08[t]["blob_sha"] and ant["sha256_composicion"] == cm["sha256_csv"]
                    and rutap.exists() and sha256(rutap.read_bytes()) == ant["sha256_csv"]):
                nuevo[t] = ant
                continue
            if zip_path is None:
                zip_path = bajar_zip(ctr[t], Path(tmp.name) / "mesa.zip")
            cuerpo = agregar_informe(zip_path, ctr[t], leer_composicion(rutac), gan,
                                     mayoria=None if fecha == FECHA else leer_equivalencia_mayoria())[0]
            if not rutap.exists() or rutap.read_bytes() != cuerpo:
                rutap.write_bytes(cuerpo)
            nuevo[t] = {"blob_sha_m08": m08[t]["blob_sha"], "sha256_composicion": cm["sha256_csv"],
                        "sha256_zip": ctr[t]["source_sha256"], "sha256_csv": sha256(cuerpo)}
    finally:
        tmp.cleanup()
    man["partidos"] = dict(sorted(nuevo.items()))
    texto = json.dumps(man, ensure_ascii=False, indent=1) + "\n"
    if not ruta_sal.exists() or ruta_sal.read_text(encoding="utf-8") != texto:
        ruta_sal.write_text(texto, encoding="utf-8")
    for viejo in salida.glob("*_partidos.csv"):
        if viejo.name[:-len("_partidos.csv")] not in nuevo:
            viejo.unlink()
    return {"hechos": sorted(nuevo), "omitidos": omitidos}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--zip", type=Path)
    ap.add_argument("--salida", type=Path, default=None,
                    help="por defecto datos/resultados (2023) o datos/resultados/<elección>/")
    ap.add_argument("--composicion", type=Path, default=COMPOSICION)
    ap.add_argument("--registro", type=Path, default=rl.REGISTRO_VISOR)
    ap.add_argument("--territorios", default="todos")
    ap.add_argument("--fecha", default=None, help="elección de los contratos: AAAA-MM-DD o «2026» (por defecto 2023-07-23)")
    a = ap.parse_args(argv)
    ts = None if a.territorios.strip() in ("", "todos") else [t.strip() for t in a.territorios.split(",")]
    fecha = resolver_fecha(a.fecha)
    r = generar(rl.salida_de(fecha, a.salida), a.registro, a.composicion, a.zip, ts, fecha=fecha)
    print(f"partidos: {len(r['hechos'])} territorios; sin composición/M08: {len(r['omitidos'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
