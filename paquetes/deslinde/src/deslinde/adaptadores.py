#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: motor 2 — adaptador de la composición M06 y el grafo M03 al núcleo de reglas
VERSIÓN: 1.2.1
NOMBRE DE VERSIÓN: Referencia de núcleos desde el M04 · puentes del contrato
FECHA: 2026-11-11
ESTADO: candidato (motor 2; producción no lo importa)
CAMBIOS: 1.2.1 — _puentes_contrato lee modulos.modulo_02_construir_adyacencias (donde los declaran los contratos;
  la raíz queda de respaldo) y normaliza los CUSEC de topology_bridges con zfill(10) (llegan como entero sin cero
  inicial; solo los ids numéricos). Antes devolvía vacío y los puentes solo llegaban por edge_type del grafo M03.
  1.2.0 — referencia_desde_m04(): CSV de referencia de núcleos (sección, district_id) desde el GeoJSON M04, el
  mismo origen que el certificador y que frozen_districts de GerryChain (T-195).
  1.1.0 — nucleos_desde_unidades() y con_nucleos(): el adaptador de núcleos cerrados desde las unidades de
  partición (distrito de referencia y ddd_closed_urban por unidad), sin composición M06; problema_y_plan lo usa.
  1.0.0 — fichero nuevo.
MOTIVO: T-160 / T-132: misma vara para todos los generadores (canónico, GerryChain, árbol, exacto T-136), que
  acaban en la composición M06. Fuera del núcleo, pero solo stdlib (csv + json): corre en la nube sin geopandas.
MOTIVO 1.2.1: T-264 (T-254 §3, duplicado «puentes del contrato»): evaluar y la cadena deben ver la misma contigüidad.
MOTIVO 1.2.0: T-195: la competición juzgaba R-NUCLEO contra la composición del canónico; la regla de producción
  (frozen_districts) y la del certificador parten del distrito inicial del M04.
MOTIVO 1.1.0: T-175: el certificador exacto no aplicaba R-NUCLEO porque solo había adaptador desde la composición.
ANTERIOR: legacy/ddd_motor2/adaptadores_v1.2.0_20261110.py
ENTRADA ÚNICA: problema_y_plan(composicion_m06_csv, grafo_m03_json, cfg) -> (Problema, {unidad: distrito}, avisos)
  - Columnas: CUSEC_KEY, district_id, section_pop, ddd_unit_id, ddd_closed_urban; provincia y partición en
    validation.province_field y municipio en validation.municipality_field del contrato (CPRO/CUMUN si no los declara,
    como validar_ejecucion; en las islas, DDD_PARTITION y DDD_MUNICIPALITY_PARTITION); clave R012 en
    partitioning.partition_unit_field si el contrato usa connected_internal_units. `columnas` las sustituye.
  - `atributos_secciones` (opcional): GeoJSON M06/M01 (.geojson, .json o .zip) cuyas propiedades completan, por sección,
    las columnas que la composición no trae (p. ej. M04_PARTITION_UNIT en Extremadura y Asturias).
  - Una unidad con secciones de varios municipios (grupo atómico, p. ej. Cataluña «25215|25234») lleva `desglose`
    con la población de cada municipio.
  - Unidad = ddd_unit_id (las secciones se agregan); sin la columna, cada sección es su unidad (se avisa).
  - Municipio/provincia/partición son campos: nunca se deducen del identificador. Si una unidad mezcla valores, el
    campo queda vacío y las reglas que lo necesitan fallan con ErrorDatos (nunca se anula una regla en silencio).
  - Una unidad repartida entre distritos rompe la atomicidad: ErrorDatos.
  - Aristas del grafo M03 por sección → aristas entre unidades; las `topology_bridges` del contrato (M02) y las aristas
    con edge_type «*bridge*» van a `puentes`.
  - Núcleos cerrados: distritos formados solo por unidades ddd_closed_urban en la composición de `referencia`
    (por defecto, la propia; como GCP con el plan inicial M04). Sin referencia distinta, R-NUCLEO es trivial: se avisa.
NÚCLEOS DESDE LAS UNIDADES: nucleos_desde_unidades({unidad: distrito de referencia}, {unidad: cerrada}) ->
  {unidad: "nucleo:<distrito>"} para los distritos de referencia formados solo por unidades cerradas (la regla de
  M05 GerryChain: distrito inicial M04 con todas sus unidades ddd_closed_urban queda congelado). con_nucleos(unidades,
  nucleo_de) devuelve las Unidad con nucleo_cerrado rellenado.
"""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from dataclasses import replace
from pathlib import Path
from typing import Any, Iterable, Mapping

from .reglas.modelo import ErrorDatos, Problema, Unidad

COLUMNAS = {
    "seccion": "CUSEC_KEY", "distrito": "district_id", "poblacion": "section_pop", "provincia": "CPRO",
    "municipio": "CUMUN", "unidad": "ddd_unit_id", "cerrado": "ddd_closed_urban",
}


def nucleos_desde_unidades(distrito_de: Mapping[str, Any], cerrada: Mapping[str, bool]) -> dict[str, str]:
    """Núcleos cerrados desde las unidades: cada distrito de referencia cuyas unidades son TODAS cerradas es un núcleo
    («nucleo:<distrito>»). Una unidad sin distrito de referencia no forma núcleo."""
    miembros: dict[str, set[str]] = defaultdict(set)
    for u, d in distrito_de.items():
        if d is not None and str(d).strip() != "":
            miembros[str(d).strip()].add(str(u))
    return {u: f"nucleo:{d}" for d, us in sorted(miembros.items())
            if us and all(bool(cerrada.get(u, False)) for u in us) for u in us}


def con_nucleos(unidades: Iterable[Unidad], nucleo_de: Mapping[str, str]) -> tuple[Unidad, ...]:
    """Las unidades con `nucleo_cerrado` según `nucleo_de` (las demás quedan sin núcleo)."""
    return tuple(replace(u, nucleo_cerrado=nucleo_de.get(u.id)) for u in unidades)


def referencia_desde_m04(m04_geojson: str | Path, destino: str | Path, cfg: Mapping | None = None,
                         campo_id: str = "CUSEC_KEY") -> Path:
    """CSV de referencia de núcleos (sección, district_id) desde el GeoJSON M04: el distrito inicial de cada sección,
    como `frozen_districts` de GerryChain y el certificador (T-175). Sin district_id en alguna sección: ErrorDatos."""
    col = {**COLUMNAS, **columnas_de_contrato(cfg or {})}
    atributos = leer_atributos(m04_geojson, campo_id)
    sin = sorted(s for s, p in atributos.items() if _vacio(p.get(col["distrito"])))
    if sin:
        raise ErrorDatos(f"{m04_geojson}: {len(sin)} secciones sin {col['distrito']} (p. ej. {sin[0]})")
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    with open(destino, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow([col["seccion"], col["distrito"], col["poblacion"]])
        for s in sorted(atributos):
            w.writerow([s, str(atributos[s][col["distrito"]]).strip(), atributos[s].get(col["poblacion"], 0)])
    return destino


def columnas_de_contrato(cfg: Mapping) -> dict[str, str]:
    """Nombres de columna según el contrato (misma precedencia que validar_ejecucion)."""
    val = (cfg or {}).get("validation") or {}
    col = dict(COLUMNAS)
    col["provincia"] = str(val.get("province_field") or "CPRO")
    col["municipio"] = str(val.get("municipality_field") or "CUMUN")
    # validar_ejecucion 1.3.5, floor_exempt_districts: la partición exenta se busca en
    # step6_export_final.province_field o, si falta, validation.province_field (CPRO); no hay columna propia.
    s6 = (((cfg or {}).get("modulo_06_consolidar_distritos") or {}).get("step6_export_final") or {})
    col["particion"] = str(s6.get("province_field") or col["provincia"])
    return col


def leer_atributos(ruta: str | Path, campo_id: str) -> dict[str, dict]:
    """Propiedades por sección de un GeoJSON (sin geopandas)."""
    import zipfile
    ruta = Path(ruta)
    if ruta.suffix == ".zip":
        with zipfile.ZipFile(ruta) as z:
            nombre = next((n for n in z.namelist() if n.endswith((".geojson", ".json"))), None)
            if nombre is None:
                raise ErrorDatos(f"{ruta}: el ZIP no trae ningún .geojson ni .json")
            datos = json.loads(z.read(nombre))
    else:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    out = {}
    for f in datos.get("features", []):
        props = f.get("properties") or {}
        if campo_id not in props:
            raise ErrorDatos(f"{ruta}: propiedades sin {campo_id}")
        out[str(props[campo_id]).strip()] = props
    return out
VERDADEROS = {"1", "true", "t", "yes", "si", "sí", "y"}


def _entero(texto: str, donde: str) -> int:
    try:
        x = float(texto)
    except (TypeError, ValueError) as exc:
        raise ErrorDatos(f"{donde}: población no numérica {texto!r}") from exc
    if not x.is_integer() or x < 0:
        raise ErrorDatos(f"{donde}: población no entera {texto!r}")
    return int(x)


def _vacio(v) -> bool:
    return v is None or str(v).strip() == "" or str(v).strip().lower() in {"nan", "none", "null"}


def _cusec(x) -> str:
    """CUSEC de topology_bridges: llega como entero sin cero inicial; los ids no numéricos quedan igual."""
    t = str(x).strip()
    return t.zfill(10) if t.isdigit() else t


def _puentes_contrato(cfg: Mapping) -> set[tuple[str, str]]:
    out = set()

    def buscar(x):
        if isinstance(x, Mapping):
            for k, v in x.items():
                if k == "topology_bridges" and isinstance(v, list):
                    for b in v:
                        if isinstance(b, Mapping) and b.get("u") is not None and b.get("v") is not None:
                            out.add(tuple(sorted((_cusec(b["u"]), _cusec(b["v"])))))
                else:
                    buscar(v)

    cfg = cfg or {}
    buscar((cfg.get("modulos") or {}).get("modulo_02_construir_adyacencias")
           or cfg.get("modulo_02_construir_adyacencias") or {})
    return out


def leer_composicion(ruta: str | Path, columnas: Mapping[str, str] | None = None) -> list[dict]:
    col = {**COLUMNAS, **(columnas or {})}
    with open(ruta, encoding="utf-8", newline="") as fh:
        filas = list(csv.DictReader(fh))
    if not filas:
        raise ErrorDatos(f"{ruta}: composición vacía")
    for clave in ("seccion", "distrito", "poblacion"):
        if col[clave] not in filas[0]:
            raise ErrorDatos(f"{ruta}: falta la columna {col[clave]}")
    return filas


def problema_y_plan(composicion_m06_csv: str | Path, grafo_m03_json: str | Path, cfg: Mapping[str, Any], *,
                    columnas: Mapping[str, str] | None = None,
                    referencia_nucleos: str | Path | None = None,
                    atributos_secciones: str | Path | None = None,
                    respaldo_municipio_cusec: bool = False) -> tuple[Problema, dict[str, str], list[str]]:
    """`respaldo_municipio_cusec` (perfil Criterio.compatibilidad_produccion): si una sección no trae municipio, se toma
    CUSEC[:5], como validar_ejecucion 1.3.4. Por defecto no: el municipio es un campo."""
    col = {**columnas_de_contrato(cfg), **(columnas or {})}
    part = (cfg or {}).get("partitioning") or {}
    campo_r012 = (str(part.get("partition_unit_field") or "")
                  if part.get("enabled") and part.get("strategy") == "connected_internal_units" else "")
    filas = leer_composicion(composicion_m06_csv, col)
    avisos: list[str] = []
    if atributos_secciones is not None:
        extra = leer_atributos(atributos_secciones, col["seccion"])
        sin = 0
        for f in filas:
            props = extra.get(str(f[col["seccion"]]).strip())
            if props is None:
                sin += 1
                continue
            for k, v in props.items():
                if k not in f or _vacio(f[k]):
                    f[k] = "" if v is None else str(v)
        if sin:
            avisos.append(f"{sin} secciones sin atributos en {Path(atributos_secciones).name}")
    con_unidad = col["unidad"] in filas[0]
    if not con_unidad:
        avisos.append(f"sin columna {col['unidad']}: cada sección es su unidad")

    seccion_a_unidad: dict[str, str] = {}
    acum: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"pob": 0, "valores": defaultdict(set), "vacios": defaultdict(int), "distritos": set(),
                 "pob_mun": defaultdict(int)})
    respaldos = 0
    for i, f in enumerate(filas, start=2):
        s = str(f[col["seccion"]]).strip()
        if s in seccion_a_unidad:
            raise ErrorDatos(f"sección repetida en la composición: {s}")
        if con_unidad and _vacio(f.get(col["unidad"])):
            raise ErrorDatos(f"línea {i}: sección {s} sin {col['unidad']}")
        uid = str(f[col["unidad"]]).strip() if con_unidad else s
        seccion_a_unidad[s] = uid
        a = acum[uid]
        if respaldo_municipio_cusec and _vacio(f.get(col["municipio"])):
            if not (len(s) >= 5 and s[:5].isdigit()):
                raise ErrorDatos(f"línea {i}: sin municipio y la sección {s} no empieza por un código INE")
            f[col["municipio"]] = s[:5]
            respaldos += 1
        pob = _entero(f[col["poblacion"]], f"línea {i}")
        a["pob"] += pob
        if col["municipio"] in f and not _vacio(f[col["municipio"]]):
            a["pob_mun"][str(f[col["municipio"]]).strip()] += pob
        a["distritos"].add(str(f[col["distrito"]]).strip())
        for campo, nombre in (("municipio", col["municipio"]), ("provincia", col["provincia"]),
                              ("particion", col["particion"]), ("unidad_r012", campo_r012)):
            if nombre and nombre in f:
                if _vacio(f[nombre]):
                    a["vacios"][campo] += 1
                else:
                    a["valores"][campo].add(str(f[nombre]).strip())
        if col["cerrado"] in f and str(f[col["cerrado"]]).strip().lower() in VERDADEROS:
            a["valores"]["cerrado"].add("1")

    if respaldos:
        avisos.append(f"{respaldos} secciones sin municipio: CUSEC[:5] (respaldo de compatibilidad)")
    partidas = sorted(u for u, a in acum.items() if len(a["distritos"]) != 1)
    if partidas:
        raise ErrorDatos(f"unidades repartidas entre distritos (atomicidad): {len(partidas)} (p. ej. {partidas[0]})")
    plan = {u: next(iter(a["distritos"])) for u, a in acum.items()}

    # Núcleos cerrados (como GCP): distritos de la referencia formados solo por unidades cerradas.
    if referencia_nucleos is None:
        ref_plan = plan
        if any(a["valores"].get("cerrado") for a in acum.values()):
            avisos.append("núcleos cerrados tomados de la propia composición: R-NUCLEO se cumple por construcción")
    else:
        ref_plan = {}
        for f in leer_composicion(referencia_nucleos, col):
            uid = seccion_a_unidad.get(str(f[col["seccion"]]).strip())
            if uid is not None:
                ref_plan[uid] = str(f[col["distrito"]]).strip()
    nucleo_de = nucleos_desde_unidades(ref_plan, {u: bool(a["valores"].get("cerrado")) for u, a in acum.items()})

    unidades = []
    mezcladas: dict[str, int] = defaultdict(int)
    vacias: dict[str, int] = defaultdict(int)
    desgloses = 0
    for uid, a in acum.items():
        campos = {}
        for campo in ("municipio", "provincia", "particion", "unidad_r012"):
            vals = a["valores"].get(campo, set())
            if vals and a["vacios"].get(campo):
                vacias[campo] += 1  # mezcla de vacío y valor: el campo queda vacío y la regla que lo exige falla
                vals = set()
            elif len(vals) > 1 and campo != "municipio":
                mezcladas[campo] += 1
            campos[campo] = next(iter(vals)) if len(vals) == 1 else None
        desglose = ()
        if len(a["valores"].get("municipio", ())) > 1 and not a["vacios"].get("municipio"):
            desglose = tuple(sorted(a["pob_mun"].items()))
            desgloses += 1
        unidades.append(Unidad(uid, a["pob"], nucleo_cerrado=nucleo_de.get(uid), desglose=desglose, **campos))
    for campo, n in sorted(mezcladas.items()):
        if n:
            avisos.append(f"{n} unidades con varios valores de {campo}: el campo queda vacío")
    for campo, n in sorted(vacias.items()):
        avisos.append(f"{n} unidades mezclan secciones con y sin {campo}: el campo queda vacío")
    if desgloses:
        avisos.append(f"{desgloses} unidades con varios municipios: desglose por municipio")

    g = json.loads(Path(grafo_m03_json).read_text(encoding="utf-8"))
    puentes_cfg = _puentes_contrato(cfg)
    aristas, puentes, fuera = set(), set(), 0
    for e in g.get("edges", []):
        su, sv = str(e["u"]), str(e["v"])
        if su not in seccion_a_unidad or sv not in seccion_a_unidad:
            fuera += 1
            continue
        a, b = seccion_a_unidad[su], seccion_a_unidad[sv]
        if a == b:
            continue
        par = tuple(sorted((a, b)))
        if tuple(sorted((su, sv))) in puentes_cfg or "bridge" in str(e.get("edge_type") or ""):
            puentes.add(par)
        else:
            aristas.add(par)
    for su, sv in puentes_cfg:
        if su in seccion_a_unidad and sv in seccion_a_unidad and seccion_a_unidad[su] != seccion_a_unidad[sv]:
            puentes.add(tuple(sorted((seccion_a_unidad[su], seccion_a_unidad[sv]))))
    if fuera:
        avisos.append(f"{fuera} aristas del grafo con secciones ajenas a la composición")
    nodos = {str(n["id"]) if isinstance(n, Mapping) else str(n) for n in g.get("nodes", [])}
    sin_nodo = set(seccion_a_unidad) - nodos if nodos else set()
    if sin_nodo:
        avisos.append(f"{len(sin_nodo)} secciones de la composición sin nodo en el grafo")
    puentes -= aristas
    return Problema(tuple(unidades), tuple(sorted(aristas)), tuple(sorted(puentes))), plan, avisos
