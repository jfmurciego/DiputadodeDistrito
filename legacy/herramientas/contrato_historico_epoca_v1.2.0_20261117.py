#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Histórico de las generales por época (T-365, D-125): contrato por elección, contrato M01-M06 por provincia y puerta M07/M08.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.2.0 · FECHA: 2026-11-17 · ESTADO: candidato
ANTERIOR: legacy/herramientas/contrato_historico_epoca_v1.1.0_20261117.py
CAMBIOS: 1.2.0: T-402: `materializar` ya no copia el seccionado crudo: escribe el de la provincia con la normalización auditada de la adquisición
  (ddd_core.official_geometry.normalize_official_geometry, política configuracion/politica_normalizacion_geometrica.yaml; nada nuevo): las
  secciones válidas pasan byte a byte, las inválidas se reparan solo si la política lo permite (si no, FALLA cerrado). La huella del resultado
  (geometrías + política) queda en `meta.historico_epoca.geometria` y en `source_inputs`; acción `geometria` = informe por elección y provincia.
  1.1.0: T-396 (D-153; reglas declaradas fuera de D-153: punto representativo, exclusión por sucesora sin fila, dato+dato=dato): las secciones con población sin geometría en el seccionado del año se ASIGNAN a la sección del seccionado
  que contiene su centroide (geometría del seccionado más cercano en años que la tenga; misma provincia) o se EXCLUYEN declarando su
  población; con sucesora de otra provincia la provincia queda APARTADA. `contrato --donantes`, `informe`. 1.0.0: fichero nuevo.
MOTIVO: D-125 (propietario, 15-11): distritos generados con los datos de cada época (seccionado y población por sección del año,
  votos por sección de esa elección y K = escaños oficiales de esa elección según el BOE), sin traslado al mapa 2023.
  D-126/D-128: población por sección (tabla de T-358/T-364). Sin tocar el motor (modulos/01-08 y ddd_core se ejecutan tal cual).
QUÉ HACE (determinista, sin reloj, sin red):
  `contrato`    escribe configuracion/historico_epoca/contrato_<AAAA_MM>.json desde ficheros con sha256: seccionado del año
                (orchestracion/fuentes_r2.json), tabla de población (sha256 medido del fichero dado), escaños oficiales (CSV de T-330,
                sha256 contra su JSON), votos del Observatorio (orchestracion/fuente_nazioenbehatokia.json) y contrato base de cada
                provincia (territorios/nacNN/config/nacNN_2025.yaml, sha256). Por provincia: territorio nacNN, K del BOE, población,
                % estimado, `secciones_sin_dato`, `secciones_sin_seccionado` (con población y sin geometría en el seccionado del año;
                exige --seccionado) y `estado`: LISTA, BLOQUEADA_RELLENO (> 1 % estimada, D-126/D-128) o BLOQUEADA_SIN_DATO.
  `materializar` (una provincia) verifica el sha256 de cada fuente local contra el contrato, casa seccionado y población
                (cualquier diferencia FALLA, cerrado) y escribe territorios/<t>/config/<t>_h<AAAA_MM>.yaml (no versionado) con K del BOE,
                años de la época y `generation_state.source_inputs` con sha256; el resto (límites, atomicidad, reparto) es el del
                contrato base. Un puente topológico con una sección inexistente en el seccionado del año FALLA.
  `electoral`   paquete M07 (votos del Observatorio por sección del mismo seccionado: sin tabla de equivalencia), M07 y M08 tal cual, y
                PUERTA_<t>_<AAAA_MM>.json: M07 PASS (o PASS_WITH_DECLARED_EXCEPTIONS con votos sin asignar ≤ 0,1 %; 2011: D-70),
                contraste por partido con el BOE (historico_campana.contraste_boe, cobertura total) y K = escaños BOE = distritos M08.
                Falla cerrado. MANIFEST.json con election_date/election_id (dimensión de elección del registro, T-199).
  `cadena`      materializar + admisión del contrato (ddd_core.territory_contract ≥ 1.5.0: K contra el contrato de su elección)
                + modulos/01..06 + electoral (piloto local).
NO HACE: descargar (las fuentes las baja quien ejecuta: docs/ESTUDIOS/T365_HISTORICO_POR_EPOCA/bajar_fuentes.sh), publicar ni
  escribir en el registro del visor (T-355).
Uso: python herramientas/contrato_historico_epoca.py contrato --eleccion 2019-11 --tabla poblacion.csv --tabla-origen "T-358 …"
     python herramientas/contrato_historico_epoca.py cadena --eleccion 2019-11 --territorio nac22 --fuentes DIR --salida DIR
"""
from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT, ROOT / "herramientas"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

VERSION = "1.2.0"
SCHEMA = "ddd.contrato-historico-epoca/1.0"
DIR_CONTRATOS = "configuracion/historico_epoca"
FUENTES_R2 = "orchestracion/fuentes_r2.json"
ESPEJO = "orchestracion/fuente_nazioenbehatokia.json"
SUMAS_T357 = "docs/ESTUDIOS/T357_PADRON_SECCION_2011_2020/SHA256SUMS.txt"
CARTOGRAFIA_CENSO_2011 = "cartografia_censo2011_nacional.zip"  # secciones del Censo 2011 (T-357, sha256 acreditado): donante de 2011
SUMAS_T364 = "docs/ESTUDIOS/T364_POBLACION_SECCION_INTERPOLADA/SHA256SUMS.txt"
LEGISLATURA = "configuracion/legislatura_vigente.yaml"
# elección → clave del espejo, fecha (reagregacion_historico.FECHAS), CSV BOE (historico_campana.OFICIAL_BOE) y año de referencia
# de la población (D-126, poblacion_seccion_historica.ELECCIONES). Se comprueban contra esos módulos en `_eleccion`.
ELECCIONES = {"2011-11": "201111", "2015-12": "201512", "2016-06": "201606", "2019-04": "201904", "2019-11": "201911"}
UMBRAL_RELLENO_PCT = 1  # D-126: > 1 % de población rellenada → la provincia no se publica sin decisión del propietario


class ErrorContrato(SystemExit):
    pass


METODO_SIN_SECCIONADO = ("D-153/T-396: sección con población sin geometría en el seccionado del año → sección del seccionado del año que "
                         "contiene su centroide (punto representativo si el centroide cae fuera de todas), con la geometría del seccionado "
                         "más cercano en años que la tenga (empate: el anterior); misma provincia (otra → APARTADA); sin geometría en "
                         "ningún año, punto fuera de todo el seccionado o sucesora sin fila en la tabla → excluida con su población "
                         "declarada. Reglas que D-153 no cita y declara este contrato: punto representativo si el centroide cae fuera; "
                         "exclusión si la sucesora no tiene fila; origen dato+dato = dato (no cuenta como estimada)")


def asignar_sin_seccionado(sin_geo: list[str], pob: dict[str, int], geo_anio: dict, donantes: list,
                           con_fila: set | None = None) -> dict[str, dict]:
    """Resuelve cada sección de `sin_geo` (con población, sin geometría en `geo_anio` {CUSEC: geometría}).

    `donantes` = [(año, función → {CUSEC: geometría})] ya ordenada por cercanía al año del seccionado (la primera que tenga la
    sección da la geometría). → {sección: {"destino": "asignada"|"excluida"|"apartada", "poblacion", "motivo", ...}}:
    asignada (sucesora de su provincia, `donante_anio`, `mismo_municipio`, `punto`), excluida (sin geometría en ningún año o
    punto fuera de todo el seccionado, o sucesora sin fila en la tabla de población si se da `con_fila`) o apartada (la sucesora es de otra provincia: la provincia no se genera)."""
    from shapely.strtree import STRtree
    claves = sorted(geo_anio)
    arbol = STRtree([geo_anio[k] for k in claves])
    cargados: dict[int, dict] = {}
    out: dict[str, dict] = {}
    for sec in sorted(sin_geo):
        fila = {"poblacion": int(pob.get(sec) or 0)}
        geom, anio = None, None
        for y, carga in donantes:
            if y not in cargados:
                cargados[y] = carga()
            if sec in cargados[y]:
                geom, anio = cargados[y][sec], y
                break
        if geom is None:
            out[sec] = {**fila, "destino": "excluida", "motivo": "sin geometría en ningún seccionado"}
            continue
        suc, punto = None, "centroide"
        for punto, pt in (("centroide", geom.centroid), ("punto_representativo", geom.representative_point())):
            cand = sorted(claves[i] for i in arbol.query(pt, predicate="intersects") if geo_anio[claves[i]].contains(pt))
            if cand:
                suc = cand[0]
                break
        if suc is None:
            out[sec] = {**fila, "destino": "excluida", "donante_anio": anio, "motivo": "el punto de la sección cae fuera del seccionado"}
        elif suc[:2] != sec[:2]:
            out[sec] = {**fila, "destino": "apartada", "sucesora": suc, "donante_anio": anio,
                        "motivo": f"la sucesora {suc} es de otra provincia"}
        elif con_fila is not None and suc not in con_fila:
            out[sec] = {**fila, "destino": "excluida", "donante_anio": anio,
                        "motivo": f"la sucesora {suc} no tiene fila en la tabla de población"}
        else:
            out[sec] = {**fila, "destino": "asignada", "sucesora": suc, "donante_anio": anio, "punto": punto,
                        "mismo_municipio": suc[:5] == sec[:5]}
    return out


def aplicar_asignacion(pob: dict[str, dict], asignadas: list[dict], excluidas: list[dict]) -> dict[str, dict]:
    """Tabla de población ({sección: {poblacion, origen}}) tras asignar y excluir (D-153). Las poblaciones declaradas deben ser las
    de la tabla (si no, falla cerrado); la sucesora suma y conserva el origen `dato` si ambas lo eran (población real de la misma
    zona: no cuenta como estimada) o pasa a `reasignada` (cuenta como estimada, D-126); la excluida desaparece."""
    out = {k: dict(v) for k, v in pob.items()}
    for x in list(asignadas) + list(excluidas):
        sec = x["seccion"]
        if sec not in pob or (pob[sec]["poblacion"] or 0) != x["poblacion"]:
            raise ErrorContrato(f"SIN_SECCIONADO_POBLACION_DISTINTA {sec}: contrato {x['poblacion']} tabla "
                                f"{(pob.get(sec) or {}).get('poblacion')}")
        out.pop(sec, None)
    for x in asignadas:
        s = out.get(x["sucesora"])
        if s is None or s["poblacion"] is None:
            raise ErrorContrato(f"SUCESORA_SIN_FILA {x['sucesora']} (de {x['seccion']})")
        s["poblacion"] += x["poblacion"]
        if not (s["origen"] == "dato" and pob[x["seccion"]]["origen"] == "dato"):
            s["origen"] = "reasignada"
    return out


def _sumas_donantes(root: Path) -> dict:
    """sha256 de los seccionados con huella acreditada fuera de fuentes_r2.json: T-357 (2012-2020) y T-364b (2021-2022)."""
    out = dict(_sumas_t357(root))
    for linea in (root / SUMAS_T364).read_text(encoding="utf-8").splitlines():
        p = linea.split()
        if len(p) >= 3 and len(p[0]) == 64:
            out[p[2].rsplit("/", 1)[-1]] = p[0]
    return out


def _donantes(e: dict, fr2: dict, dir_donantes: Path | None, root: Path = ROOT) -> list[dict]:
    """Seccionados donantes (otros años con sha256 acreditado y fichero en `dir_donantes`; incluye la cartografía del Censo 2011), por cercanía al del año (empate: el
    anterior). Los mismos que usa T-364b para la geometría de las secciones que el seccionado del año no tiene."""
    if dir_donantes is None:
        return []
    sumas = _sumas_donantes(root)
    out = []
    for f in sorted(dir_donantes.glob("seccionado_*.zip")) + sorted(dir_donantes.glob(CARTOGRAFIA_CENSO_2011)):
        nombre = f.name
        m = fr2.get(nombre) or {}
        y = 2011 if nombre == CARTOGRAFIA_CENSO_2011 else int(nombre.split("_")[1].split(".")[0])  # el Censo 2011 es de noviembre de 2011
        esperado = m.get("sha256") or sumas.get(nombre)
        if y == e["seccionado"] or not esperado:
            continue
        if sha256(f) != esperado:
            raise ErrorContrato(f"DONANTE_HUELLA_DISTINTA {nombre}")
        out.append({"anio": y, "fichero": nombre, "sha256": esperado,
                    "origen_url": m.get("origen_url") or ("https://www.ine.es/censos2011_datos/" if y == 2011 else
                                                          "https://www.ine.es/prodyser/cartografia/") + nombre, "ruta": f})
    return sorted(out, key=lambda d: (abs(d["anio"] - e["seccionado"]), d["anio"]))


def _geometrias_plano(zip_path: Path) -> dict:
    import equivalencia_seccionados as eqs
    return {c: g for prov in eqs.leer_seccionado(zip_path).values() for c, g in prov.items()}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _json(rel: str, root: Path = ROOT) -> dict:
    return json.loads((root / rel).read_text(encoding="utf-8"))


def _eleccion(eleccion: str, root: Path = ROOT) -> dict:
    if eleccion not in ELECCIONES:
        raise ErrorContrato(f"ELECCION_NO_SOPORTADA {eleccion}: {sorted(ELECCIONES)}")
    import poblacion_seccion_historica as psh
    import historico_campana as hc
    from reagregacion_historico import FECHAS
    clave = ELECCIONES[eleccion]
    anio_secc = {e["clave"]: e["seccionado"] for e in _json(ESPEJO, root)["elecciones"]}[clave]
    tipo, anio_pob = psh.ELECCIONES[eleccion]
    return {"eleccion": eleccion, "clave_espejo": clave, "fecha": FECHAS[clave], "seccionado": int(anio_secc),
            "poblacion_anio": int(anio_pob), "poblacion_fuente": tipo, "csv_boe": f"configuracion/resultados_oficiales_congreso_{hc.OFICIAL_BOE[clave]}.csv"}


def _sumas_t357(root: Path) -> dict:
    out = {}
    for linea in (root / SUMAS_T357).read_text(encoding="utf-8").splitlines():
        p = linea.split()
        if len(p) >= 3 and len(p[0]) == 64:
            out[p[2].rsplit("/", 1)[-1]] = p[0]
    return out


def leer_tabla(path: Path, eleccion: str) -> dict[str, dict]:
    """{sección: {poblacion, origen}} de la tabla de población por sección: la única de T-358 (columna `elección`) o la de
    T-364 por elección (`poblacion_seccion_<AAAA-MM>.csv`, sin columna de elección: va en el nombre del fichero)."""
    out: dict[str, dict] = {}
    with open(path, encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        n = {k.replace("ó", "o").replace("í", "i"): k for k in (r.fieldnames or [])}
        for falta in ("seccion", "poblacion", "origen"):
            if falta not in n:
                raise ErrorContrato(f"TABLA_SIN_COLUMNA {falta} en {path.name}")
        if "eleccion" not in n and path.name != f"poblacion_seccion_{eleccion}.csv":
            raise ErrorContrato(f"TABLA_DE_OTRA_ELECCION {path.name} (se espera poblacion_seccion_{eleccion}.csv)")
        for fila in r:
            if "eleccion" in n and fila[n["eleccion"]] != eleccion:
                continue
            s, p = fila[n["seccion"]], fila[n["poblacion"]]
            if len(s) != 10 or not s.isdigit() or s in out:
                raise ErrorContrato(f"TABLA_SECCION_INVALIDA {s!r}")
            origen = fila[n["origen"]]
            if origen == "sin_dato" and p == "":  # nunca se convierte en 0: la provincia queda BLOQUEADA_SIN_DATO
                out[s] = {"poblacion": None, "origen": origen}
                continue
            if not p.isdigit():
                raise ErrorContrato(f"TABLA_POBLACION_INVALIDA {s} {p!r} ({origen})")
            out[s] = {"poblacion": int(p), "origen": origen}
    if not out:
        raise ErrorContrato(f"TABLA_SIN_ELECCION {eleccion} en {path.name}")
    return out


def escanos_boe(ruta: Path) -> dict[str, dict]:
    """{cpro: {provincia, K, suma_escanos, votos}} del CSV del BOE (T-330); K = escanos_circunscripcion (único por provincia)."""
    out: dict[str, dict] = {}
    with open(ruta, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            e = out.setdefault(r["codigo"], {"provincia": r["provincia"], "K": set(), "suma_escanos": 0})
            e["K"].add(int(r["escanos_circunscripcion"]))
            e["suma_escanos"] += int(r["escanos"])
    for c, e in out.items():
        if len(e["K"]) != 1:
            raise ErrorContrato(f"BOE_K_AMBIGUO {c}: {sorted(e['K'])}")
        e["K"] = e["K"].pop()
        if e["suma_escanos"] != e["K"]:
            raise ErrorContrato(f"BOE_ESCANOS_NO_SUMAN_K {c}: {e['suma_escanos']} != {e['K']}")
    return out


def _territorios(root: Path) -> dict[str, str]:
    import yaml
    cfg = yaml.safe_load((root / LEGISLATURA).read_text(encoding="utf-8"))
    return {str(r["codigo"]): str(r["territory_id"]) for r in cfg["territorios"]
            if str(r.get("territory_id") or "").startswith("nac")}


def pct(parte: int, total: int) -> str:
    """% con 4 decimales en aritmética entera (como T-358)."""
    if total == 0:
        return "0.0000"
    n = (parte * 1_000_000 + total // 2) // total
    return f"{n // 10000}.{n % 10000:04d}"


def construir_contrato(eleccion: str, tabla: Path, tabla_origen: str, version: str = VERSION,
                       anterior: str = "ninguna (fichero nuevo)", root: Path = ROOT, seccionado: Path | None = None,
                       donantes: Path | None = None) -> dict:
    """`seccionado` (zip del año, sha256 contra fuentes_r2.json) da las secciones con población sin geometría en el seccionado del
    año. D-153: se asignan a su sucesora o se excluyen (`asignar_sin_seccionado`, con los seccionados de `donantes`); las que no
    se resuelven (sucesora de otra provincia) quedan en `secciones_sin_seccionado` y la provincia en APARTADA."""
    e = _eleccion(eleccion, root)
    fr2 = _json(FUENTES_R2, root)["fuentes"]
    nombre_secc = f"seccionado_{e['seccionado']}.zip"
    s = fr2.get(nombre_secc) or {}
    sumas = _sumas_t357(root)
    if not s.get("sha256") or not s.get("clave"):
        raise ErrorContrato(f"SECCIONADO_SIN_HUELLA_R2 {nombre_secc}")
    if nombre_secc in sumas and sumas[nombre_secc] != s["sha256"]:
        raise ErrorContrato(f"SECCIONADO_HUELLA_DISTINTA {nombre_secc}: R2 {s['sha256']} != T-357 {sumas[nombre_secc]}")
    csv_boe = root / e["csv_boe"]
    meta_boe = json.loads(csv_boe.with_suffix(".json").read_text(encoding="utf-8"))
    if sha256(csv_boe) != meta_boe["sha256_csv"]:
        raise ErrorContrato(f"CSV_BOE_HUELLA_DISTINTA {e['csv_boe']}")
    boe = escanos_boe(csv_boe)
    espejo = _json(ESPEJO, root)
    pob = leer_tabla(tabla, eleccion)
    if seccionado is None or sha256(seccionado) != s["sha256"]:
        raise ErrorContrato(f"SECCIONADO_REQUERIDO {nombre_secc} con sha256 {s['sha256']}")
    geo = _secciones_seccionado(seccionado, None)
    don = _donantes(e, fr2, donantes, root)
    if any(k not in geo for k in pob) and not don:
        raise ErrorContrato("DONANTES_REQUERIDOS: hay secciones sin geometría en el seccionado del año (--donantes DIR con "
                            "seccionado_AAAA.zip de otros años)")
    resueltas: dict[str, dict] = {}
    sin_geo_todas = sorted(k for k in pob if k not in geo)
    if sin_geo_todas:
        resueltas = asignar_sin_seccionado(
            sin_geo_todas, {k: pob[k]["poblacion"] for k in sin_geo_todas}, _geometrias_plano(seccionado),
            [(d["anio"], (lambda r=d["ruta"]: _geometrias_plano(r))) for d in don], set(pob))
    terr = _territorios(root)
    provincias = {}
    for c in sorted(boe):
        t = terr.get(c)
        if t is None:
            raise ErrorContrato(f"PROVINCIA_SIN_TERRITORIO {c}")
        ruta = f"data/{e['clave_espejo']}/sekzioa/{c}.json"
        fv = espejo["ficheros"].get(ruta)
        rv = fr2.get(f"nazioenbehatokia/{ruta}") or {}
        if not fv or not fv.get("sha256"):
            raise ErrorContrato(f"VOTOS_SIN_HUELLA {ruta}")
        if rv.get("sha256") not in (None, fv["sha256"]):
            raise ErrorContrato(f"VOTOS_HUELLA_R2_DISTINTA {ruta}")
        base = root / f"territorios/{t}/config/{t}_2025.yaml"
        pob_c = {k: x for k, x in pob.items() if k[:2] == c}
        rs = {k: r for k, r in resueltas.items() if k[:2] == c}
        asig = [{"seccion": k, "sucesora": r["sucesora"], "donante_anio": r["donante_anio"], "punto": r["punto"],
                 "mismo_municipio": r["mismo_municipio"], "poblacion": r["poblacion"]} for k, r in rs.items() if r["destino"] == "asignada"]
        excl = [{"seccion": k, "poblacion": r["poblacion"], "motivo": r["motivo"]} for k, r in rs.items() if r["destino"] == "excluida"]
        apart = [{"seccion": k, "poblacion": r["poblacion"], "motivo": r["motivo"]} for k, r in rs.items() if r["destino"] == "apartada"]
        final = aplicar_asignacion(pob_c, asig, excl)
        filas = list(final.values())
        sin_dato = sorted(k for k, x in pob_c.items() if x["poblacion"] is None)
        total = sum(x["poblacion"] or 0 for x in filas)
        rell = [x for x in filas if x["origen"] != "dato"]
        prell = sum(x["poblacion"] or 0 for x in rell)
        sin_secc = sorted(x["seccion"] for x in apart)  # sin resolver: la provincia queda APARTADA
        estado = ("BLOQUEADA_SIN_DATO" if sin_dato or not filas else "APARTADA" if apart else
                  "BLOQUEADA_RELLENO" if prell * 100 > total * UMBRAL_RELLENO_PCT else "LISTA")
        provincias[c] = {
            "territorio": t, "provincia": boe[c]["provincia"], "K": boe[c]["K"], "k_source": "norma",
            # sin «/» ni extensión: ddd_core.config.load_params_yaml lo tomaría por ruta en el contrato de provincia
            "k_rationale": f"D-125: K = escaños oficiales de {t} en la elección {eleccion} según {meta_boe.get('boe')} "
                           f"(CSV de T-330, sha256 {meta_boe['sha256_csv'][:12]})",
            "contrato_base": {"ruta": base.relative_to(root).as_posix(), "sha256": sha256(base)},
            "votos": {"ruta": ruta, "sha256": fv["sha256"], "bytes": fv.get("bytes"), "r2_clave": rv.get("clave")},
            "poblacion": {"secciones": len(filas), "total": total, "secciones_no_dato": len(rell),
                          "poblacion_no_dato": prell, "pct_no_dato": pct(prell, total), "secciones_sin_dato": sin_dato,
                          "secciones_sin_seccionado": sin_secc,
                          "poblacion_sin_seccionado": sum(x["poblacion"] for x in apart),
                          **({"sin_seccionado_resuelto": {
                              "asignadas": asig, "excluidas": excl, "apartadas": apart,
                              "poblacion_asignada": sum(x["poblacion"] for x in asig),
                              "poblacion_excluida": sum(x["poblacion"] for x in excl)}} if rs else {})},
            "estado": estado,
        }
    return {
        "schema": SCHEMA, "version": version, "anterior": anterior,
        "motivo": "D-125 (opción A: distritos con los datos de cada época), D-126/D-128 (población), T-199 (elección en el registro)",
        "generado_con": f"herramientas/contrato_historico_epoca.py {VERSION}",
        "eleccion": eleccion, "fecha": e["fecha"], "clave_espejo": e["clave_espejo"],
        "seccionado": {"anio": e["seccionado"], "fichero": nombre_secc, "sha256": s["sha256"], "origen_url": s.get("origen_url"),
                       "r2_clave": s["clave"], "campo_seccion": "CUSEC",
                       **({"donantes": [{k: v for k, v in d.items() if k != "ruta"} for d in don]} if resueltas else {})},
        "poblacion": {"fichero": tabla.name, "sha256": sha256(tabla), "origen": tabla_origen, "anio_referencia": e["poblacion_anio"],
                      "fuente": e["poblacion_fuente"],
                      "regla_publicacion": f"> {UMBRAL_RELLENO_PCT} % estimada → BLOQUEADA_RELLENO (D-126/D-128); sin_dato → BLOQUEADA_SIN_DATO",
                      "regla_sin_seccionado": METODO_SIN_SECCIONADO,
                      "fuentes": {k: sumas.get(k) for k in ("30832.csv", "indicadores_seccion_censal_csv.zip")}},
        "escanos": {"csv": e["csv_boe"], "sha256": meta_boe["sha256_csv"], "boe": meta_boe.get("boe"),
                    "regla": "K de la provincia = escanos_circunscripcion del BOE de la elección (D-125)"},
        "votos": {"fuente": "nazioenbehatokia", "manifiesto": ESPEJO, "manifiesto_sha256": sha256(root / ESPEJO)},
        "puerta": {"m07": "PASS o PASS_WITH_DECLARED_EXCEPTIONS con votos sin asignar ≤ 0,1 % (2011: D-70)",
                   "contraste_boe": "historico_campana.contraste_boe (por partido, cobertura total, TOLERANCIA de cuadre_historico_espana)",
                   "escanos": "K del contrato = escaños BOE = distritos del M08"},
        "provincias": provincias,
    }


def escribir_json(path: Path, data: dict) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1, sort_keys=False) + "\n", encoding="utf-8")
    return sha256(path)


def ruta_contrato(eleccion: str, root: Path = ROOT) -> Path:
    return root / DIR_CONTRATOS / f"contrato_{eleccion.replace('-', '_')}.json"


def run_name(territorio: str, eleccion: str) -> str:
    return f"{territorio}_h{eleccion.replace('-', '_')}"


def _fuente(fuentes: Path, nombre: str, esperado: str) -> Path:
    p = fuentes / nombre
    if not p.is_file():
        raise ErrorContrato(f"FUENTE_AUSENTE {p}")
    if sha256(p) != esperado:
        raise ErrorContrato(f"FUENTE_HUELLA_DISTINTA {p}")
    return p


def _secciones_seccionado(zip_path: Path, cpro: str | None) -> set[str]:
    import zipfile
    import geopandas as gpd
    with zipfile.ZipFile(zip_path) as z:
        shp = next(n for n in z.namelist() if n.lower().endswith(".shp"))
    g = gpd.read_file(f"zip://{zip_path}!{shp}", columns=["CUSEC"], ignore_geometry=True)
    return {str(x) for x in g["CUSEC"] if cpro is None or str(x)[:2] == cpro}


def _leer_seccionado(zip_path: Path, cpro: str | None):
    """GeoDataFrame del seccionado (solo la provincia `cpro`, o todo si None), con su CRS y columnas originales."""
    import geopandas as gpd
    import zipfile
    with zipfile.ZipFile(zip_path) as z:
        shp = next(n for n in z.namelist() if n.lower().endswith(".shp"))
    g = gpd.read_file(f"zip://{zip_path}!{shp}")
    if cpro is not None:
        g = g[g["CUSEC"].astype(str).str[:2] == cpro].reset_index(drop=True)
    return g


def normalizar_geometrias(g) -> tuple[object, list[dict], dict]:
    """T-402: normalización auditada de la adquisición, sección a sección. Válidas intactas; inválidas reparadas o FALLA cerrado.

    Devuelve (GeoDataFrame, correcciones, política). Cada corrección: sección, método, motivo antes y área (m², EPSG de la política)
    antes/después. El área de un polígono inválido no es evidencia de equivalencia (política): se informa, no se acepta con ella.
    """
    import geopandas as gpd
    from ddd_core.official_geometry import load_geometry_policy, normalize_official_geometry
    pol, pol_sha, pol_ruta = load_geometry_policy()
    crs = str(g.crs) if g.crs is not None else "EPSG:4326"
    metrica = str(pol["metric_crs"])

    def area(geom):
        return float(gpd.GeoSeries([geom], crs=crs).to_crs(metrica).area.iloc[0])

    geoms, correcciones = list(g.geometry), []
    for i, (sec, geom) in enumerate(zip(g["CUSEC"].astype(str), geoms)):
        if geom is not None and not geom.is_empty and geom.is_valid:
            continue
        nueva, aud = normalize_official_geometry(sec, geom, source_crs=crs, policy=pol)
        if aud["status"] != "NORMALIZED":
            raise ErrorContrato(f"GEOMETRIA_NO_NORMALIZABLE {sec}: {aud.get('reason')}")
        geoms[i] = nueva
        correcciones.append({"seccion": sec, "metodo": aud.get("method"), "motivo": aud["before"].get("validity_reason"),
                             "area_antes_m2": round(area(geom), 3), "area_despues_m2": round(area(nueva), 3)})
    out = g.copy()
    out["geometry"] = gpd.GeoSeries(geoms, index=g.index, crs=g.crs)
    return out, correcciones, {"ruta": pol_ruta, "sha256": pol_sha, "version": pol.get("version")}


def _huella_geometrias(g) -> str:
    h = hashlib.sha256()
    for sec, geom in sorted(zip(g["CUSEC"].astype(str), g.geometry), key=lambda x: x[0]):
        h.update(sec.encode() + b"\0" + (geom.wkb if geom is not None else b"") + b"\n")
    return h.hexdigest()


def _normalizar_seccionado(secc: Path, cpro: str, cache: Path, sha_origen: str) -> tuple[Path, dict]:
    """Escribe en `cache` el seccionado normalizado de la provincia (zip de shapefile) y devuelve (ruta, informe con huellas)."""
    import tempfile
    import zipfile
    g, correcciones, pol = normalizar_geometrias(_leer_seccionado(secc, cpro))
    destino = cache / f"seccionado_normalizado_{cpro}.zip"
    with tempfile.TemporaryDirectory() as t:
        g.to_file(Path(t) / f"seccionado_{cpro}.shp")
        with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as z:  # fecha fija: zip reproducible
            for f in sorted(Path(t).iterdir()):
                z.writestr(zipfile.ZipInfo(f.name, (1980, 1, 1, 0, 0, 0)), f.read_bytes(), zipfile.ZIP_DEFLATED)
    return destino, {"origen_sha256": sha_origen, "politica": pol, "secciones": len(g), "corregidas": correcciones,
                     "huella_geometrias_sha256": _huella_geometrias(g), "normalizado_sha256": sha256(destino)}


def informe_geometria(eleccion: str, fuentes: Path, root: Path = ROOT, contrato: Path | None = None) -> dict:
    """T-402: secciones corregidas por provincia (área antes/después) para una elección; no escribe contratos ni cache."""
    c = json.loads((contrato or ruta_contrato(eleccion, root)).read_text(encoding="utf-8"))
    secc = _fuente(fuentes, c["seccionado"]["fichero"], c["seccionado"]["sha256"])
    _, correcciones, pol = normalizar_geometrias(_leer_seccionado(secc, None))
    prov = {cpro: [x for x in correcciones if x["seccion"][:2] == cpro] for cpro in sorted(c["provincias"])}
    return {"eleccion": eleccion, "seccionado_sha256": c["seccionado"]["sha256"], "politica": pol,
            "provincias": {k: {"corregidas": v, "n": len(v)} for k, v in prov.items() if v},
            "total_corregidas": len(correcciones)}


def _reemplazar(obj, viejo: str, nuevo: str):
    if isinstance(obj, dict):
        return {k: _reemplazar(v, viejo, nuevo) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_reemplazar(v, viejo, nuevo) for v in obj]
    return obj.replace(viejo, nuevo) if isinstance(obj, str) else obj


def contrato_provincia(base: dict, c: dict, cpro: str, eleccion: str, secc_rel: str, pob_rel: str, huellas: dict,
                       contrato_sha: str, geometria: dict | None = None) -> dict:
    """Contrato M01-M06 de la época desde el contrato base: cambian fuentes, años, K y rutas; nada más."""
    p = c["provincias"][cpro]
    t, k = p["territorio"], p["K"]
    rn = run_name(t, eleccion)
    anio_p, anio_s = c["poblacion"]["anio_referencia"], c["seccionado"]["anio"]
    pop_viejo = f"POP_{base['meta']['source_population_year']}"
    cfg = copy.deepcopy(base)
    for clave in ("resolved_source_contract",):
        cfg.pop(clave, None)
    cfg["modulos"] = _reemplazar(cfg["modulos"], f"{base['meta']['run_name']}_", f"{rn}_")
    cfg["modulos"] = _reemplazar(cfg["modulos"], pop_viejo, f"POP_{anio_p}")
    m = cfg["meta"]
    m.update({"run_name": rn, "year": int(eleccion[:4]), "source_population_year": anio_p, "source_section_year": anio_s,
              "status": "generation_ready",
              "historico_epoca": {"eleccion": eleccion, "election_date": c["fecha"], "election_id": f"{t}_{c['fecha']}",
                                  "contrato": ruta_contrato(eleccion, Path("")).as_posix(), "contrato_sha256": contrato_sha,
                                  "contrato_base_sha256": p["contrato_base"]["sha256"], "decision": "D-125",
                                  **({"geometria": geometria} if geometria else {})}})
    cfg["io"]["input"]["seccionado"].update({"path": secc_rel, "container": "zip", "materialized_format": "shapefile",
                                             "archive_member": "", "layer": "", "section_key_col": "CUSEC"})
    cfg["io"]["input"]["population_cip"] = {
        "paths": [pob_rel], "sep": ",", "section_key_col": "Secciones", "pop_col": "Total",
        "filters": {"year_col": "Periodo", "year_value": anio_p}, "container": "file", "materialized_format": "csv",
        "archive_member": "", "encoding": "utf-8"}
    tc = cfg["territory_contract"]
    tc.update({"k_districts": k, "k_source": p["k_source"], "k_reference_source": c["escanos"]["boe"],
               "k_reference_scope": "escanos_oficiales_eleccion", "k_rationale": p["k_rationale"]})
    cfg["modulos"]["modulo_04_generar_semillas"]["k_districts"] = k
    cfg["modulos"]["modulo_06_consolidar_distritos"]["expected_districts"] = k
    v = cfg["validation"]
    v["expected_districts"] = k
    v["province_districts"] = {cpro: k}
    if v.get("topology_accreditation"):
        raise ErrorContrato(f"TOPOLOGIA_ACREDITADA_CON_OTRA_FUENTE {t}: re-acreditar para el seccionado {anio_s}")
    paquete = hashlib.sha256(json.dumps(huellas, sort_keys=True).encode()).hexdigest()
    v["source_baseline"] = {"schema": "ddd.source-baseline/1.0", "edition": eleccion, "population_year": anio_p,
                            "section_year": anio_s, "population_total": p["poblacion"]["total"],
                            "target_section_count": p["poblacion"]["secciones"], "package_sha256": paquete,
                            "compatibility_report_sha256": None, "compatibility_identity_sha256": paquete}
    cfg["generation_state"] = {
        "source_prepared": True, "generation_enabled": True, "package_sha256": paquete,
        "compatibility_identity_sha256": paquete,
        "source_inputs": [{"path": secc_rel, "sha256": huellas["seccionado"], "role": "target_sectioning"},
                          {"path": pob_rel, "sha256": huellas["poblacion"], "role": "population"}]}
    return cfg


def _exigir_lista(p: dict, territorio: str, eleccion: str) -> None:
    """D-126: una provincia con > 1 % de población estimada no se genera sin decisión del propietario (fallo cerrado)."""
    if p.get("estado") != "LISTA":
        raise ErrorContrato(f"PROVINCIA_NO_LISTA {territorio} {eleccion}: {p.get('estado')} (D-126: decisión del propietario)")


def materializar(eleccion: str, territorio: str, fuentes: Path, root: Path = ROOT, contrato: Path | None = None) -> Path:
    import yaml
    cpath = contrato or ruta_contrato(eleccion, root)
    c = json.loads(cpath.read_text(encoding="utf-8"))
    cpro = next((k for k, p in c["provincias"].items() if p["territorio"] == territorio), None)
    if cpro is None:
        raise ErrorContrato(f"TERRITORIO_FUERA_DEL_CONTRATO {territorio}")
    p = c["provincias"][cpro]
    _exigir_lista(p, territorio, eleccion)
    base_path = root / p["contrato_base"]["ruta"]
    if sha256(base_path) != p["contrato_base"]["sha256"]:
        raise ErrorContrato(f"CONTRATO_BASE_HUELLA_DISTINTA {base_path}")
    secc = _fuente(fuentes, c["seccionado"]["fichero"], c["seccionado"]["sha256"])
    tabla = _fuente(fuentes, c["poblacion"]["fichero"], c["poblacion"]["sha256"])
    pob = {s: x for s, x in leer_tabla(tabla, eleccion).items() if s[:2] == cpro}
    geo = _secciones_seccionado(secc, cpro)
    sin_geo_tabla = sorted(set(pob) - geo)
    res = p["poblacion"].get("sin_seccionado_resuelto") or {}
    asig, excl = res.get("asignadas", []), res.get("excluidas", [])
    declaradas = sorted(set(p["poblacion"].get("secciones_sin_seccionado", sin_geo_tabla)) | {x["seccion"] for x in asig + excl})
    if sin_geo_tabla != declaradas:
        raise ErrorContrato(f"SIN_SECCIONADO_DISTINTO_DEL_CONTRATO {territorio} {eleccion}")
    pob = aplicar_asignacion(pob, asig, excl)  # D-153: asignadas a su sucesora, excluidas fuera (declaradas en el contrato)
    sin_pob, sin_geo = sorted(geo - set(pob)), sorted(set(pob) - geo)
    if sin_pob or sin_geo:  # las no resueltas (sin sucesora en su provincia) fallan cerrado
        raise ErrorContrato(f"CASADO_POBLACION_SECCIONADO {territorio} {eleccion}: sin población {len(sin_pob)} {sin_pob[:5]}; "
                            f"población sin geometría {len(sin_geo)} {sin_geo[:5]}")
    base = yaml.safe_load(base_path.read_text(encoding="utf-8"))
    for puente in (base["modulos"]["modulo_02_construir_adyacencias"].get("topology_bridges") or []):
        extremos = [puente.get(k) for k in ("u", "v")] if isinstance(puente, dict) else list(puente)
        if len(extremos) != 2 or any(x is None or str(x).zfill(10) not in geo for x in extremos):
            raise ErrorContrato(f"PUENTE_FUERA_DEL_SECCIONADO {territorio} {puente}")
    rn = run_name(territorio, eleccion)
    cache = root / f"territorios/{territorio}/.cache/ddd/historico_epoca/{rn}"
    cache.mkdir(parents=True, exist_ok=True)
    # T-402: no se copia el crudo; se escribe el de la provincia con la normalización auditada de la adquisición
    secc_local, geometria = _normalizar_seccionado(secc, cpro, cache, c["seccionado"]["sha256"])
    pob_local = cache / f"poblacion_{cpro}.csv"
    with open(pob_local, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["Periodo", "Secciones", "Total", "origen"])
        for s in sorted(pob):
            w.writerow([c["poblacion"]["anio_referencia"], s, pob[s]["poblacion"], pob[s]["origen"]])
    rel = lambda q: q.relative_to(root).as_posix()  # noqa: E731
    huellas = {"seccionado": geometria["normalizado_sha256"], "poblacion": sha256(pob_local), "tabla": c["poblacion"]["sha256"],
               "contrato_base": p["contrato_base"]["sha256"], "votos": p["votos"]["sha256"], "escanos": c["escanos"]["sha256"]}
    cfg = contrato_provincia(base, c, cpro, eleccion, rel(secc_local), rel(pob_local), huellas, sha256(cpath), geometria)
    out = root / f"territorios/{territorio}/config/{rn}.yaml"
    out.write_text("# Generado por herramientas/contrato_historico_epoca.py (T-365, D-125); no versionado: se regenera desde "
                   f"{rel(cpath)}.\n" + yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return out


def _m07_params(t: str, trabajo: Path, m06: dict, contrato_el: Path) -> Path:
    import yaml
    cfg = {"meta": {"territory_id": t, "run_name": f"{t}_historico_epoca"}, "io": {"project_root": {"path": str(ROOT)}},
           "modulos": {
               "modulo_06_consolidar_distritos": {"out_geojson": m06["out_geojson"], "out_district_geojson": m06["out_district_geojson"],
                                                  "id_field": m06["id_field"], "district_field": m06["district_field"],
                                                  "pop_field": m06["pop_field"]},
               "modulo_07_agregar_resultados_electorales": {
                   "in_geojson": m06["out_geojson"], "section_id_field": m06["id_field"], "district_field": m06["district_field"],
                   "population_field": m06["pop_field"], "election_contract": str(contrato_el),
                   "out_district_party_csv": str(trabajo / "m07_resultados_partido.csv"),
                   "out_district_summary_csv": str(trabajo / "m07_resumen_electoral.csv"),
                   "out_reconciliation_report": str(trabajo / "m07_reconciliacion.json")},
               "modulo_08_integrar_resultados": {
                   "in_district_geojson": m06["out_district_geojson"],
                   "in_district_summary_csv": str(trabajo / "m07_resumen_electoral.csv"),
                   "out_districts_with_results_geojson": str(trabajo / "m08_distritos_resultados.geojson.zip"),
                   "allow_declared_map_only_districts": False}}}
    p = trabajo / "params_m07_m08.yaml"
    p.write_text(yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return p


def participacion(path: Path, asign: dict) -> tuple[dict, list[str]]:
    """Como historico_m07m08.participacion, pero una sección de votos sin distrito no rompe: se lista (sus votos ya cuentan
    como no asignados en la reconciliación de M07 y la puerta los limita)."""
    from collections import defaultdict
    import reagregacion_historico as rh
    out: dict = defaultdict(Counter)
    fuera = []
    with open(path, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            d = asign.get(r["section_id"])
            if d is None:
                fuera.append(r["section_id"])
                continue
            out[d].update({k: int(r[k]) for k in rh.CAMPOS})
    return out, fuera


def puerta(c: dict, cpro: str, rec: dict, contraste: dict, distritos_m08: int) -> dict:
    import historico_campana as hc
    clave, k = c["clave_espejo"], c["provincias"][cpro]["K"]
    perdidos, fuente = rec.get("ddd_unassigned_votes"), rec.get("source_votes")
    pct_p = perdidos / fuente if isinstance(perdidos, int) and isinstance(fuente, int) and fuente > 0 else None
    d70 = cpro in hc.D70.get(clave, {})
    tope = hc.D70[clave][cpro] if d70 else hc.MAX_PERDIDOS
    m07_ok = rec.get("status") in ("PASS", "PASS_WITH_DECLARED_EXCEPTIONS") and pct_p is not None \
        and (perdidos <= tope if d70 else pct_p <= tope)
    escanos_ok = distritos_m08 == k
    out = {"territorio": c["provincias"][cpro]["territorio"], "eleccion": c["eleccion"], "election_date": c["fecha"],
           "mapa": "epoca", "m07": rec.get("status"), "perdidos": perdidos, "perdidos_pct": pct_p, "tope_perdidos": tope,
           "excepcion_d70": d70, "K_boe": k, "distritos_m08": distritos_m08, "escanos_ok": escanos_ok,
           "contraste_boe": contraste, "estado_provincia": c["provincias"][cpro]["estado"]}
    return {**out, "estado": "PASS" if m07_ok and escanos_ok and contraste.get("ok") else "FAIL"}


def electoral(eleccion: str, territorio: str, fuentes: Path, salida: Path, root: Path = ROOT) -> int:
    import yaml
    import historico_campana as hc
    import historico_m07m08 as hm
    import reagregacion_historico as rh
    import fuente_nazioenbehatokia as fnb
    cpath = ruta_contrato(eleccion, root)
    c = json.loads(cpath.read_text(encoding="utf-8"))
    cpro = next((k for k, p in c["provincias"].items() if p["territorio"] == territorio), None)
    if cpro is None:
        raise ErrorContrato(f"TERRITORIO_FUERA_DEL_CONTRATO {territorio}")
    p = c["provincias"][cpro]
    _exigir_lista(p, territorio, eleccion)
    espejo = _fuente(fuentes, f"nazioenbehatokia/{p['votos']['ruta']}", p["votos"]["sha256"])
    rn = run_name(territorio, eleccion)
    params = root / f"territorios/{territorio}/config/{rn}.yaml"
    from ddd_core.config import load_params_yaml
    m06 = load_params_yaml(str(params))["modulos"]["modulo_06_consolidar_distritos"]
    trabajo = root / f"territorios/{territorio}/.cache/ddd/historico_epoca/{rn}/m07"
    trabajo.mkdir(parents=True, exist_ok=True)
    votos = fnb.leer_provincia(json.loads(espejo.read_text(encoding="utf-8")))
    sec = {s: {"votos": r["votos"], **{k: int(r[k]) for k in rh.CAMPOS}} for s, r in votos.items()}
    paq = trabajo / "paquete"
    rh.escribir_paquete(paq, territorio, c["clave_espejo"], sec, rh.leer_oficial(c["clave_espejo"], cpro),
                        {"path": f"nazioenbehatokia/{p['votos']['ruta']}", "sha256": p["votos"]["sha256"], "manifest": ESPEJO})
    con = paq / "contrato.json"
    ce = json.loads(con.read_text(encoding="utf-8"))
    ce["title"] = f"Congreso de los Diputados {c['fecha'][:4]} — histórico por época (D-125, T-365)"
    ce["historico_epoca"] = {"contrato": cpath.relative_to(root).as_posix(), "contrato_sha256": sha256(cpath)}
    con.write_text(json.dumps(ce, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    pm = _m07_params(territorio, trabajo, m06, con)
    hm.ejecutar("07_agregar_resultados_electorales.py", pm)
    hm.ejecutar("08_integrar_resultados.py", pm)
    rec = json.loads((trabajo / "m07_reconciliacion.json").read_text(encoding="utf-8"))
    resumen = hm.leer_resumen(trabajo / "m07_resumen_electoral.csv")
    contraste = hc.contraste_boe(c["clave_espejo"], cpro, espejo, root)
    pu = puerta(c, cpro, rec, contraste, len(resumen))
    dest = salida / eleccion / territorio
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copy(trabajo / "m07_resumen_electoral.csv", dest / "resumen_electoral.csv")
    shutil.copy(trabajo / "m07_resultados_partido.csv", dest / "resultados_partido.csv")
    with open(m06["out_composition_csv"], encoding="utf-8", newline="") as f:
        filas = list(csv.DictReader(f))
    campo_s = next(k for k in filas[0] if k in (m06["id_field"], "CUSEC_KEY", "section_id"))
    asign = {r[campo_s]: str(r[m06["district_field"]]) for r in filas}
    part, fuera = participacion(paq / "participacion.csv", asign)
    hm.escribir_participacion(dest / "participacion.csv", part)
    (dest / "reconciliacion.json").write_text(json.dumps(
        {k: rec.get(k) for k in ("status", "source_votes", "incorporated_votes", "ddd_unassigned_votes", "ddd_loss_ratio",
                                 "source_gap_to_definitive_votes", "source_gap_to_definitive_ratio", "errors", "warnings")},
        ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    escribir_json(salida / f"PUERTA_{territorio}_{eleccion.replace('-', '_')}.json", pu)
    m08 = trabajo / "m08_distritos_resultados.geojson.zip"
    man = {"schema": "ddd.historico-epoca-manifiesto/1.0", "territorio": territorio, "eleccion": eleccion,
           "election_date": c["fecha"], "election_id": f"{territorio}_{c['fecha']}", "kind": "historico_epoca",
           "contrato": {"ruta": cpath.relative_to(root).as_posix(), "sha256": sha256(cpath)},
           "contrato_provincia": {"ruta": params.relative_to(root).as_posix(), "sha256": sha256(params)},
           "m06": {"composicion_sha256": sha256(Path(m06["out_composition_csv"])),
                   "distritos_sha256": sha256(Path(m06["out_district_geojson"]))},
           "m08": {"sha256": sha256(m08)}, "votos_sha256": p["votos"]["sha256"], "secciones_votos_sin_distrito": fuera,
           "ganadores": {d: r["winner_party"] for d, r in sorted(resumen.items())}, "puerta": pu["estado"]}
    escribir_json(dest / "MANIFEST.json", man)
    print(json.dumps(pu, ensure_ascii=False), flush=True)
    return 0 if pu["estado"] == "PASS" else 1


def cadena(eleccion: str, territorio: str, fuentes: Path, salida: Path, root: Path = ROOT) -> int:
    from ddd_core.territory_contract import validate_production_contract
    params = materializar(eleccion, territorio, fuentes, root)
    adm = validate_production_contract(params, expected_territory=territorio)  # K contra el contrato de SU elección (1.5.0)
    if adm["status"] != "ADMITTED":
        raise ErrorContrato(f"CONTRATO_NO_ADMITIDO {params}: {adm['errors']}")
    for n in range(1, 7):
        mod = sorted((root / "modulos").glob(f"0{n}_*.py"))[0]
        r = subprocess.run([sys.executable, str(mod), "--params", str(params)], cwd=root, capture_output=True, text=True)
        if r.returncode != 0:
            sys.stderr.write(r.stdout[-3000:] + r.stderr[-3000:])
            raise ErrorContrato(f"MODULO_FALLA {mod.name} rc={r.returncode}")
        print(f"[T-365] {mod.name} OK", flush=True)
    return electoral(eleccion, territorio, fuentes, salida, root)


def informe_sin_seccionado(root: Path = ROOT) -> list[dict]:
    """Por elección y provincia con secciones sin geometría: asignadas, excluidas, apartadas y habitantes (desde el contrato)."""
    filas = []
    for e in sorted(ELECCIONES):
        c = json.loads(ruta_contrato(e, root).read_text(encoding="utf-8"))
        for cpro, p in sorted(c["provincias"].items()):
            r = p["poblacion"].get("sin_seccionado_resuelto")
            if not r and not p["poblacion"]["secciones_sin_seccionado"]:
                continue
            r = r or {"asignadas": [], "excluidas": [], "apartadas": [], "poblacion_asignada": 0, "poblacion_excluida": 0}
            filas.append({"eleccion": e, "provincia": cpro, "territorio": p["territorio"], "estado": p["estado"],
                          "asignadas": len(r["asignadas"]), "habitantes_asignados": r["poblacion_asignada"],
                          "asignadas_por_punto_representativo": sum(x["punto"] == "punto_representativo" for x in r["asignadas"]),
                          "excluidas": len(r["excluidas"]), "habitantes_excluidos": r["poblacion_excluida"],
                          "excluidas_por_sucesora_sin_fila": sum("no tiene fila" in x["motivo"] for x in r["excluidas"]),
                          "apartadas": len(r["apartadas"]), "habitantes_apartados": sum(x["poblacion"] for x in r["apartadas"])})
    return filas


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="accion", required=True)
    a1 = sub.add_parser("contrato")
    a1.add_argument("--eleccion", required=True, choices=sorted(ELECCIONES))
    a1.add_argument("--tabla", type=Path, required=True, help="tabla de población por sección (T-358/T-364)")
    a1.add_argument("--tabla-origen", required=True, help="herramienta y versión que produjo la tabla")
    a1.add_argument("--seccionado", type=Path, required=True, help="seccionado INE del año (zip, sha256 de fuentes_r2.json)")
    a1.add_argument("--donantes", type=Path, help="carpeta con seccionado_AAAA.zip de otros años (D-153)")
    a1.add_argument("--version", default=VERSION)
    a1.add_argument("--anterior", default="ninguna (fichero nuevo)")
    a1.add_argument("--salida", type=Path)
    a3 = sub.add_parser("geometria", help="T-402: informe de secciones corregidas por provincia (área antes/después)")
    a3.add_argument("--eleccion", required=True, choices=sorted(ELECCIONES))
    a3.add_argument("--fuentes", type=Path, required=True)
    a3.add_argument("--salida", type=Path)
    a2 = sub.add_parser("informe")
    a2.add_argument("--salida", type=Path)
    for nombre in ("materializar", "electoral", "cadena"):
        s = sub.add_parser(nombre)
        s.add_argument("--eleccion", required=True, choices=sorted(ELECCIONES))
        s.add_argument("--territorio", required=True)
        s.add_argument("--fuentes", type=Path, required=True, help="carpeta con las fuentes locales (bajar_fuentes.sh)")
        s.add_argument("--salida", type=Path, default=ROOT / "salida_historico_epoca")
    a = ap.parse_args(argv)
    if a.accion == "contrato":
        c = construir_contrato(a.eleccion, a.tabla, a.tabla_origen, a.version, a.anterior, seccionado=a.seccionado,
                               donantes=a.donantes)
        out = a.salida or ruta_contrato(a.eleccion)
        print(out, escribir_json(out, c), Counter(p["estado"] for p in c["provincias"].values()))
        return 0
    if a.accion == "informe":
        filas = informe_sin_seccionado()
        cols = list(filas[0]) if filas else ["eleccion"]
        w = csv.DictWriter(open(a.salida, "w", encoding="utf-8", newline="") if a.salida else sys.stdout, cols, lineterminator="\n")
        w.writeheader()
        w.writerows(filas)
        return 0
    if a.accion == "geometria":
        inf = informe_geometria(a.eleccion, a.fuentes)
        if a.salida:
            escribir_json(a.salida, inf)
        print(json.dumps({k: v for k, v in inf.items() if k != "provincias"} | {"provincias": {k: v["n"] for k, v in inf["provincias"].items()}},
                         ensure_ascii=False))
        return 0
    if a.accion == "materializar":
        print(materializar(a.eleccion, a.territorio, a.fuentes))
        return 0
    if a.accion == "electoral":
        return electoral(a.eleccion, a.territorio, a.fuentes, a.salida)
    return cadena(a.eleccion, a.territorio, a.fuentes, a.salida)


if __name__ == "__main__":
    sys.exit(main())
