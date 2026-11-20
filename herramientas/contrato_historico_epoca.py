#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Histórico de las generales por época (T-365, D-125): contrato por elección, contrato M01-M06 por provincia y puerta M07/M08.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.4.1 · FECHA: 2026-11-20 · ESTADO: candidato
ANTERIOR: legacy/herramientas/contrato_historico_epoca_v1.4.0_20261120.py
CAMBIOS: 1.4.1: T-400 (D-185, propietario): exenciones de suelo de partición declaradas en configuracion/historico_epoca/exenciones_suelo_epoca.json (atadas al sha256 del seccionado; 38-G01 de 2011-11): `_reparto_particiones` las admite si coinciden con las que calcula el reparto por componentes y deja constancia en `meta.historico_epoca.reparto_particiones`; una exención de suelo no declarada y no gobernada por la política del contrato base sigue fallando cerrado.
  1.4.0: T-400 (D-185, propietario): `contrato --total-municipal 1mun00.csv` carga el total MUNICIPAL del Censo 2011 (INE, 1-nov-2011; huella en configuracion/historico_epoca/total_municipal_censo_2011.json) y lo usa en `rellenar_sin_poblacion`: las rellenadas se ajustan al residuo municipal (el Padrón 29005 se descartó: otra fecha) y una única sección sin dato en ningún año de un municipio recibe el residuo (mínimo 0; `residuo_municipal_censo`); más de una sigue sin dato (BLOQUEADA_SIN_DATO). Sin la opción, nada cambia.
  1.3.3: T-400 (D-180, propietario): en un territorio con particiones insulares (07, 35, 38) `validation.province_districts` ya no es {provincia: K} sino el reparto por partición de `component_hamilton` (materializar_contrato_generacion) con la población de la época, y la exención de suelo de una partición de un distrito bajo el suelo (`population_floor_exempt_partitions`, p. ej. 35-C02 Fuerteventura 2011) sale de la misma llamada, con `partition_populations` y `partition_apportionment_audit` y el motivo en `meta.historico_epoca.reparto_particiones`. Sin ello M04 fallaba «need=K > unidades abiertas=0».
  1.3.2: T-400: un puente topológico del contrato base cuyo extremo no existe en el seccionado de la época (nac35: La Graciosa 3502401010, que el INE segrega en 2019 de la 3502401005) se omite si una sección de la época ya lo contenía (M02 rechazaría un puente sin desconexión), declarada en configuracion/historico_epoca/puentes_epoca.json (atada al sha256 del seccionado, con la contención medida contra el donante 2019); sin declaración sigue fallando PUENTE_FUERA_DEL_SECCIONADO.
  1.3.1: 1.3.1: T-405: `materializar` emite `validation.topology_accreditation` desde configuracion/historico_epoca/topologia_administrativa.json (municipios no conexos del seccionado de la época; atada al sha256 del seccionado y comprobada contra sus secciones y CUMUN). Sin ella M04 fallaba en nac14 2011-11 (Fuente Palmera 14030).
  1.3.0: T-399 (D-158 B', decisión del propietario (17-11), confirmada en el chat del Planificador): 2011-11 mantiene el seccionado 2012. Las secciones del seccionado SIN fila en
  la tabla se resuelven así: (a) las que parten una sección del Censo (la «hija» cae ≥ 50 % en una sección con población: la «madre») reciben una parte de la población 2011 de la madre repartida entre madre e hijas
  según el Atlas del año más cercano de cada una (restos mayores; se conservan los totales del Censo; origen `repartida_madre`/`repartida_hija`); (b) las que no tienen madre (existen en el Censo sin fila) se
  RELLENAN con el valor de la misma sección en el año más cercano del Atlas (D-126; origen `rellenada_año_cercano`) y ajuste al total municipal oficial del Censo solo si hay fuente con sha256 (hoy no: sin ajuste,
  declarado); sin dato en ningún año → BLOQUEADA_SIN_DATO. Las provincias con votos sin asignar > 0,1 % (2011-11: 03, 24, 27, 32, 33; `votos_fuera_del_seccionado.csv`) quedan APARTADA_VOTOS y declaradas:
  no se toca D-70 ni hay excepciones nuevas en la puerta.
  Misma sección-municipio para la madre (código de 5 cifras); `contrato --censo` + `verificar_madres_censo`: la población declarada de cada madre se verifica contra el Censo acreditado (sha256 de T-357).
  D-161 (propietario, 17-11): para el umbral del 1 % cuenta solo lo movido de la madre a las hijas más lo rellenado (`filas_estimadas`), no madre+hijas enteras. `contrato --atlas`, `informe_poblacion`.
  1.2.0: T-402: `materializar` ya no copia el seccionado crudo: escribe el de la provincia con la normalización auditada de la adquisición
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

VERSION = "1.4.0"
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
VOTOS_FUERA_CSV = "docs/ESTUDIOS/T399_2011_SIN_POBLACION/votos_fuera_del_seccionado.csv"  # votos del Observatorio en secciones fuera del seccionado (2011-11), D-158
APARTADAS_POR_VOTOS = ("2011-11",)  # elecciones con provincias apartadas por votos sin asignar > 0,1 % (D-158)
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

ORIGEN_RELLENADA = "rellenada_año_cercano"
ORIGEN_MADRE, ORIGEN_HIJA = "repartida_madre", "repartida_hija"
SOLAPE_MADRE = 0.5  # una sección del seccionado sin fila es «hija» si cae al menos en esta fracción de su área en una sección del Censo con población
METODO_SIN_POBLACION = ("D-158 B'/D-126 (T-399): sección del seccionado de la época sin fila en la tabla de población. (a) Si cae ≥ 50 % de su área en una sección con "
                        "población del mismo municipio (la madre; mayor solape), la población de la madre se reparte entre madre e hijas según el valor de cada una "
                        "en el año más cercano del Atlas con dato (empate: el anterior; restos mayores): se conservan los totales del Censo y madre e hijas cuentan "
                        "como estimadas (`repartida_madre`/`repartida_hija`); si algún miembro no tiene dato en ningún año, sus hijas quedan sin dato. (b) Si no tiene "
                        "madre, valor de la misma sección en el año más cercano del Atlas con dato (`rellenada_año_cercano`, estimada), con ajuste proporcional al total "
                        "municipal OFICIAL del Censo 2011 solo si el contrato declara esa fuente con sha256; sin ella no se ajusta y queda declarado "
                        "(`sin_ajuste_municipal`, `total_municipal_oficial.fuente` = null). Sin dato en ningún año → la provincia queda BLOQUEADA_SIN_DATO")


def valor_anio_cercano(sec: str, anio: int, atlas: dict) -> tuple[int | None, int | None]:
    """(valor, año) de la sección en el año del Atlas con dato entero más cercano a `anio` (empate: el anterior); (None, None) si no hay."""
    con = sorted((a for a in atlas if isinstance(atlas[a].get(sec), int)), key=lambda a: (abs(a - anio), a))
    return (atlas[con[0]][sec], con[0]) if con else (None, None)


def rellenar_sin_poblacion(sin_pob: list[str], pob: dict[str, dict], atlas: dict, anio: int, total_mun: dict[str, int]) -> dict:
    """Relleno de las secciones de `sin_pob` (del seccionado, sin fila en `pob` {sección: {poblacion, origen}}).

    → {"rellenadas": [{seccion, poblacion, poblacion_atlas, anio_atlas, ajuste}], "sin_dato": [secciones], "cuadre": [fila por municipio]}.
    `ajuste`: ajustada | cuadra | sin_ajuste_municipal (residuo ≤ 0, municipio sin total o con una sección sin dato)."""
    import poblacion_seccion_historica as psh
    por_mun: dict[str, list[str]] = {}
    for s in sorted(sin_pob):
        por_mun.setdefault(s[:5], []).append(s)
    rellenadas, sin_dato, cuadre = [], [], []
    for mun, secs in sorted(por_mun.items()):
        vals = {s: valor_anio_cercano(s, anio, atlas) for s in secs}
        sd = [s for s in secs if vals[s][0] is None]
        sin_dato += sd
        con = [s for s in secs if vals[s][0] is not None]
        suma_dato = sum(x["poblacion"] or 0 for k, x in pob.items() if k[:5] == mun)
        oficial = total_mun.get(mun)
        atlas_sum = sum(vals[s][0] for s in con)
        if sd and oficial is not None and len(sd) == 1 and not con:
            # D-185: única sección del municipio sin dato en ningún año; recibe el residuo del total municipal del Censo (mínimo 0)
            s0 = sd[0]
            sin_dato.remove(s0)
            rellenadas.append({"seccion": s0, "poblacion": max(oficial - suma_dato, 0), "poblacion_atlas": None, "anio_atlas": None,
                               "ajuste": "residuo_municipal_censo"})
            cuadre.append({"municipio": mun, "total_municipal_censo": oficial, "suma_con_dato": suma_dato, "residuo": oficial - suma_dato,
                           "secciones_rellenadas": 1, "rellenado_atlas": 0, "rellenado_final": max(oficial - suma_dato, 0),
                           "estado": "residuo_sin_dato", "suma_municipio": suma_dato + max(oficial - suma_dato, 0),
                           "exceso_sobre_censo": max(suma_dato - oficial, 0)})
            continue
        if sd:
            estado, final = "aviso_sin_dato", [vals[s][0] for s in con]
        elif oficial is None:
            estado, final = "aviso_sin_total_municipal", [vals[s][0] for s in con]
        elif oficial - suma_dato <= 0:
            estado, final = "aviso_residuo_no_positivo", [vals[s][0] for s in con]
        elif oficial - suma_dato == atlas_sum:
            estado, final = "cuadra", [vals[s][0] for s in con]
        else:
            estado, final = "ajustado", psh.reparto([vals[s][0] for s in con], oficial - suma_dato)
        ajuste = {"ajustado": "ajustada", "cuadra": "cuadra"}.get(estado, "sin_ajuste_municipal")
        for s, v in zip(con, final):
            rellenadas.append({"seccion": s, "poblacion": v, "poblacion_atlas": vals[s][0], "anio_atlas": vals[s][1], "ajuste": ajuste})
        cuadre.append({"municipio": mun, "total_municipal_censo": oficial, "suma_con_dato": suma_dato, "residuo": (oficial - suma_dato) if oficial is not None else None,
                       "secciones_rellenadas": len(con), "rellenado_atlas": atlas_sum, "rellenado_final": sum(final), "estado": estado,
                       "suma_municipio": suma_dato + sum(final),
                       "exceso_sobre_censo": (suma_dato + sum(final) - oficial) if oficial is not None else None})
    return {"rellenadas": rellenadas, "sin_dato": sin_dato, "cuadre": cuadre}


def aplicar_relleno(pob: dict[str, dict], rellenadas: list[dict]) -> dict[str, dict]:
    """Añade a la tabla las secciones rellenadas declaradas en el contrato (origen `rellenada_año_cercano`); una que ya tiene fila falla cerrado."""
    out = {k: dict(v) for k, v in pob.items()}
    for x in rellenadas:
        if x["seccion"] in out:
            raise ErrorContrato(f"RELLENADA_CON_FILA {x['seccion']}: la tabla ya la trae")
        out[x["seccion"]] = {"poblacion": x["poblacion"], "origen": ORIGEN_RELLENADA}
    return out


def repartir_madres(sin_pob: list[str], pob: dict[str, dict], geo_sin: dict, geo_censo: dict, atlas: dict, anio: int) -> dict:
    """D-158 (B'): `sin_pob` = secciones del seccionado sin fila en `pob`; `geo_sin` = {sección: geometría en el seccionado del año}; `geo_censo` = {sección: geometría} del Censo.

    La madre de una hija es la sección de `pob` (con población, mismo municipio: código de 5 cifras) de mayor solape con la hija, si cubre ≥ `SOLAPE_MADRE` de su área.
    → {"repartos": [{madre, poblacion_censo_madre, miembros: [{seccion, rol, solape, poblacion_atlas, anio_atlas, poblacion}]}], "sin_madre": [hijas],
       "sin_dato": [hijas de grupos con algún miembro sin dato en ningún año]}. Los totales se conservan: Σ población de los miembros = población de la madre."""
    from shapely.strtree import STRtree
    import poblacion_seccion_historica as psh
    cands = sorted(k for k in geo_censo if (pob.get(k) or {}).get("poblacion"))
    arbol = STRtree([geo_censo[k] for k in cands]) if cands else None
    grupos: dict[str, list[tuple[str, float]]] = {}
    sin_madre = []
    for h in sorted(sin_pob):
        g = geo_sin.get(h)
        mejor, area = None, 0.0
        if g is not None and arbol is not None and g.area > 0:
            for i in arbol.query(g, predicate="intersects"):
                k = cands[i]
                if k[:5] != h[:5]:  # misma provincia y municipio: se conservan los totales por madre, municipio y provincia
                    continue
                a = g.intersection(geo_censo[k]).area
                if a > area or (a == area and mejor is not None and k < mejor):
                    mejor, area = k, a
        if mejor is not None and area / g.area >= SOLAPE_MADRE:
            grupos.setdefault(mejor, []).append((h, round(area / g.area, 4)))
        else:
            sin_madre.append(h)
    repartos, sin_dato = [], []
    for m, hijas in sorted(grupos.items()):
        miembros = [(m, "madre", None)] + [(h, "hija", s) for h, s in hijas]
        vals = {s: valor_anio_cercano(s, anio, atlas) for s, _, _ in miembros}
        if any(v[0] is None or v[0] <= 0 for v in vals.values()):
            sin_dato += [h for h, _ in hijas]
            continue
        total = pob[m]["poblacion"]
        partes = psh.reparto([vals[s][0] for s, _, _ in miembros], total)
        repartos.append({"madre": m, "poblacion_censo_madre": total,
                         "miembros": [{"seccion": s, "rol": rol, "solape": sol, "poblacion_atlas": vals[s][0], "anio_atlas": vals[s][1], "poblacion": p}
                                      for (s, rol, sol), p in zip(miembros, partes)]})
    return {"repartos": repartos, "sin_madre": sin_madre, "sin_dato": sorted(sin_dato)}


def filas_estimadas(filas: list[dict]) -> list[dict]:
    """Filas que cuentan como estimadas en el umbral del 1 % (D-126). D-161 (propietario, 17-11): del reparto madre/hijas cuenta SOLO la población movida de la
    madre a las hijas (las filas `repartida_hija`) más las `rellenada_año_cercano`; la madre (`repartida_madre`) conserva el resto de su dato del Censo y no cuenta
    (D-128 contaba entera a la sucesora `reasignada`, que sigue contando entera)."""
    return [x for x in filas if x["origen"] not in ("dato", ORIGEN_MADRE)]


def verificar_madres_censo(repartos: list[dict], censo: dict) -> None:
    """La población que el contrato declara de cada madre (`poblacion_censo_madre`) debe ser la del Censo 2011 acreditado (`psh.leer_censo`, sha256 de T-357),
    no solo la de la tabla: falla cerrado si difiere."""
    for x in repartos:
        v = censo.get(x["madre"])
        if v != x["poblacion_censo_madre"]:
            raise ErrorContrato(f"REPARTO_MADRE_DISTINTA_DEL_CENSO {x['madre']}: contrato {x['poblacion_censo_madre']} Censo {v!r}")


def aplicar_reparto(pob: dict[str, dict], repartos: list[dict]) -> dict[str, dict]:
    """Tabla tras el reparto madre/hijas declarado en el contrato: la madre debe tener en la tabla la población declarada (si no, falla cerrado), las
    hijas no deben tener fila y la suma de los miembros debe ser la población de la madre."""
    out = {k: dict(v) for k, v in pob.items()}
    for x in repartos:
        m = x["madre"]
        if m not in pob or pob[m]["poblacion"] != x["poblacion_censo_madre"]:
            raise ErrorContrato(f"REPARTO_MADRE_POBLACION_DISTINTA {m}: contrato {x['poblacion_censo_madre']} tabla {(pob.get(m) or {}).get('poblacion')}")
        if sum(y["poblacion"] for y in x["miembros"]) != x["poblacion_censo_madre"]:
            raise ErrorContrato(f"REPARTO_SUMA_DISTINTA {m}")
        for y in x["miembros"]:
            if y["rol"] == "madre":
                out[m] = {"poblacion": y["poblacion"], "origen": ORIGEN_MADRE}
            elif y["seccion"] in out:
                raise ErrorContrato(f"REPARTO_HIJA_CON_FILA {y['seccion']}: la tabla ya la trae")
            else:
                out[y["seccion"]] = {"poblacion": y["poblacion"], "origen": ORIGEN_HIJA}
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


def apartadas_por_votos(eleccion: str, root: Path = ROOT) -> dict[str, dict]:
    """D-158 (B'), solo 2011-11: provincias cuyos votos del Observatorio en secciones que el seccionado 2012 no trae superan el 0,1 % de los votos válidos
    (la puerta M07 solo las pasaría con las excepciones D-70, que no se tocan ni se amplían): quedan APARTADA_VOTOS y declaradas, con su medición y la fuente con sha256."""
    if eleccion not in APARTADAS_POR_VOTOS:
        return {}
    ruta = root / VOTOS_FUERA_CSV
    out = {}
    with open(ruta, encoding="utf-8", newline="") as f:
        for fila in csv.DictReader(f):
            perdidos, total = int(fila["perdidos_con_seccionado2012"]), int(fila["votos_validos_observatorio"])
            if perdidos * 1000 > total:  # > 0,1 % (historico_campana.MAX_PERDIDOS)
                out[fila["provincia"]] = {"votos_fuera_del_seccionado": perdidos, "votos_validos": total, "pct": pct(perdidos, total),
                                          "secciones_fuera": int(fila["secciones_2012"]), "tope_general_pct": "0.1",
                                          "fuente": VOTOS_FUERA_CSV, "fuente_sha256": sha256(ruta)}
    return dict(sorted(out.items()))


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


TOTAL_MUNICIPAL_2011 = "configuracion/historico_epoca/total_municipal_censo_2011.json"


def leer_total_municipal(path: Path, root: Path = ROOT) -> tuple[dict[str, int], dict]:
    """D-185: total municipal del Censo 2011 (INE 1mun00, «Ambos sexos» / «Total», 1-nov-2011) → ({municipio de 5 cifras: población}, declaración).
    Falla cerrado si el sha256 no es el acreditado en `total_municipal_censo_2011.json`."""
    decl = _json(TOTAL_MUNICIPAL_2011, root)
    if sha256(path) != decl["fuente"]["sha256"]:
        raise ErrorContrato(f"TOTAL_MUNICIPAL_HUELLA_DISTINTA {path.name}")
    out: dict[str, int] = {}
    with open(path, encoding="utf-8-sig", newline="") as f:
        for r in csv.reader(f, delimiter=";"):
            if len(r) == 4 and r[1] == "Ambos sexos" and r[2] == "Total" and r[3].strip() and r[0][:5].isdigit():
                out[r[0][:5]] = int(r[3].replace(".", ""))
    if not out:
        raise ErrorContrato("TOTAL_MUNICIPAL_VACIO")
    return out, decl


def construir_contrato(eleccion: str, tabla: Path, tabla_origen: str, version: str = VERSION,
                       anterior: str = "ninguna (fichero nuevo)", root: Path = ROOT, seccionado: Path | None = None,
                       donantes: Path | None = None, atlas: Path | None = None, total_municipal: dict | None = None, censo: Path | None = None,
                       total_municipal_fuente: Path | None = None) -> dict:
    """`seccionado` (zip del año, sha256 contra fuentes_r2.json) da las secciones con población sin geometría en el seccionado del
    año. D-153: se asignan a su sucesora o se excluyen (`asignar_sin_seccionado`, con los seccionados de `donantes`); las que no
    se resuelven (sucesora de otra provincia) quedan en `secciones_sin_seccionado` y la provincia en APARTADA.
    T-399: las secciones del seccionado sin población en la tabla se rellenan (`rellenar_sin_poblacion`; exige `atlas`, con sha256 de T-357; `total_municipal` =
    {municipio: total oficial del Censo 2011} si hay fuente con sha256, y si no se ajusta nada y queda declarado)."""
    e = _eleccion(eleccion, root)
    tm_decl = None
    if total_municipal_fuente is not None:
        total_municipal, tm_decl = leer_total_municipal(total_municipal_fuente, root)
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
    geo_prov: dict[str, set] = {}
    for k in geo:
        geo_prov.setdefault(k[:2], set()).add(k)
    cargas: dict = {}

    def _resolver(sin_pob: list[str], final: dict, anio: int) -> tuple[dict, dict]:
        """(reparto madre/hijas, relleno de las demás) de las secciones del seccionado sin fila en la tabla (D-158 B' y D-126)."""
        if not cargas:
            if atlas is None:
                raise ErrorContrato("ATLAS_REQUERIDO: hay secciones del seccionado sin población en la tabla (--atlas 30832.csv)")
            if sha256(atlas) != sumas.get("30832.csv"):
                raise ErrorContrato("FUENTE_RELLENO_HUELLA_DISTINTA 30832.csv")
            censo_don = next((d for d in don if d["fichero"] == CARTOGRAFIA_CENSO_2011), None)
            if censo_don is None:
                raise ErrorContrato(f"DONANTE_CENSO_REQUERIDO: --donantes DIR con {CARTOGRAFIA_CENSO_2011} para identificar la madre de las secciones sin fila")
            import poblacion_seccion_historica as psh
            if censo is None or sha256(censo) != sumas.get("indicadores_seccion_censal_csv.zip"):
                raise ErrorContrato("CENSO_REQUERIDO: --censo indicadores_seccion_censal_csv.zip con el sha256 de T-357 (verifica la población de las madres)")
            cargas.update(atlas=psh.leer_atlas(atlas), geo_sin=_geometrias_plano(seccionado), geo_censo=_geometrias_plano(censo_don["ruta"]),
                          censo=psh.leer_censo(censo))
        rep = repartir_madres(sin_pob, final, cargas["geo_sin"], cargas["geo_censo"], cargas["atlas"], anio)
        verificar_madres_censo(rep["repartos"], cargas["censo"])
        rell = rellenar_sin_poblacion(rep["sin_madre"], final, cargas["atlas"], anio, total_municipal or {})
        return rep, rell
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
        # provincia sin filas en la tabla (apartada por T-364b): no se rellena entera, sigue BLOQUEADA_SIN_DATO
        sin_pob = sorted(geo_prov.get(c, set()) - set(final)) if pob_c else []
        rep, rp = _resolver(sin_pob, final, e["poblacion_anio"]) if sin_pob else (None, None)
        if rep:
            final = aplicar_reparto(final, rep["repartos"])
            final = aplicar_relleno(final, rp["rellenadas"])
        filas = list(final.values())
        sin_dato = sorted([k for k, x in pob_c.items() if x["poblacion"] is None] + (rp["sin_dato"] + rep["sin_dato"] if rep else []))
        total = sum(x["poblacion"] or 0 for x in filas)
        rell = filas_estimadas(filas)
        prell = sum(x["poblacion"] or 0 for x in rell)
        sin_secc = sorted(x["seccion"] for x in apart)  # sin resolver: la provincia queda APARTADA
        votos_ap = apartadas_por_votos(eleccion, root).get(c)
        estado = ("BLOQUEADA_SIN_DATO" if sin_dato or not filas else "APARTADA" if apart else "APARTADA_VOTOS" if votos_ap else
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
                              "poblacion_excluida": sum(x["poblacion"] for x in excl)}} if rs else {}),
                          **({"sin_poblacion_resuelto": {
                              "anio_atlas_referencia": e["poblacion_anio"], "repartidas": rep["repartos"], "rellenadas": rp["rellenadas"],
                              "sin_dato": sorted(rp["sin_dato"] + rep["sin_dato"]),
                              "habitantes_repartidos_a_hijas": sum(y["poblacion"] for x in rep["repartos"] for y in x["miembros"] if y["rol"] == "hija"),
                              "habitantes_madres_censo": sum(x["poblacion_censo_madre"] for x in rep["repartos"]),
                              "habitantes_atlas": sum(x["poblacion_atlas"] or 0 for x in rp["rellenadas"]),
                              "habitantes_rellenados": sum(x["poblacion"] for x in rp["rellenadas"]),
                              "cuadre_municipal": rp["cuadre"]}} if rep else {}),
                          **({"votos_sin_asignar": votos_ap} if votos_ap else {})},
            "estado": estado,
        }
    return {
        "schema": SCHEMA, "version": version, "anterior": anterior,
        "motivo": "D-125 (opción A: distritos con los datos de cada época), D-126/D-128 (población), T-199 (elección en el registro)",
        "generado_con": f"herramientas/contrato_historico_epoca.py {VERSION}",
        "eleccion": eleccion, "fecha": e["fecha"], "clave_espejo": e["clave_espejo"],
        "seccionado": {"anio": e["seccionado"], "fichero": nombre_secc, "sha256": s["sha256"], "origen_url": s.get("origen_url"),
                       "r2_clave": s["clave"], "campo_seccion": "CUSEC",
                       **({"donantes": [{k: v for k, v in d.items() if k != "ruta"} for d in don]} if (resueltas or cargas) else {})},
        "poblacion": {"fichero": tabla.name, "sha256": sha256(tabla), "origen": tabla_origen, "anio_referencia": e["poblacion_anio"],
                      "fuente": e["poblacion_fuente"],
                      "regla_publicacion": f"> {UMBRAL_RELLENO_PCT} % estimada → BLOQUEADA_RELLENO (D-126/D-128; D-161: del reparto madre/hijas cuenta solo lo movido a las hijas más lo rellenado, no la madre); sin_dato → BLOQUEADA_SIN_DATO",
                      "regla_sin_seccionado": METODO_SIN_SECCIONADO,
                      "regla_sin_poblacion": METODO_SIN_POBLACION,
                      **({"madres_verificadas_contra_censo": {"fuente": "indicadores_seccion_censal_csv.zip", "sha256": sumas.get("indicadores_seccion_censal_csv.zip")}}
                         if "censo" in cargas else {}),
                      "total_municipal_oficial": (
                          {"fuente": tm_decl["fuente"]["nombre"], "url": tm_decl["fuente"]["url"], "sha256": tm_decl["fuente"]["sha256"],
                           "referencia": "1-nov-2011", "decision": "D-185",
                           "regla": "las rellenadas se ajustan al residuo municipal (total del Censo − secciones con dato); una única sección sin dato en ningún año "
                                    "del municipio recibe el residuo (mínimo 0, `residuo_municipal_censo`)"} if tm_decl else
                          {"fuente": None, "sha256": None,
                           "motivo": "sin tabla del INE del total municipal del Censo 2011 con fuente y sha256 (D-158): el relleno no se ajusta"}),
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
                       contrato_sha: str, geometria: dict | None = None, topologia: list | None = None,
                       puentes: list | None = None, reparto: dict | None = None) -> dict:
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
    if topologia:  # T-405: municipios no conexos del seccionado de la época, acreditados contra ESTA fuente
        from ddd_core.topology_preflight import TOPOLOGY_ACCREDITATION_SCHEMA, topology_source_binding
        v["topology_accreditation"] = {"schema": TOPOLOGY_ACCREDITATION_SCHEMA, "source_binding": topology_source_binding(cfg),
                                       "administrative_components": copy.deepcopy(topologia)}
    if reparto:  # T-400 (D-180): cuotas por partición insular en lugar de {provincia: K}
        v["province_districts"] = dict(reparto["cuota"])
        v["partition_populations"] = dict(reparto["poblaciones"])
        v["population_floor_exempt_partitions"] = list(reparto["exentas"])
        v["partition_apportionment_audit"] = reparto["auditoria"]
        tc["population_floor_exempt_partitions"] = list(reparto["exentas"])
        if reparto["exenciones_declaradas"] and not tc.get("small_component_exception_policy"):
            tc["small_component_exception_policy"] = reparto["politica_excepcion"]
        m["historico_epoca"]["reparto_particiones"] = {k2: reparto[k2] for k2 in ("cuota", "exentas", "suelo_ratio", "motivo", "exenciones_declaradas")}
    if puentes is not None:  # T-400: puentes con los extremos que existen en el seccionado de la época
        cfg["modulos"]["modulo_02_construir_adyacencias"]["topology_bridges"] = copy.deepcopy(puentes)
    cfg["generation_state"] = {
        "source_prepared": True, "generation_enabled": True, "package_sha256": paquete,
        "compatibility_identity_sha256": paquete,
        "source_inputs": [{"path": secc_rel, "sha256": huellas["seccionado"], "role": "target_sectioning"},
                          {"path": pob_rel, "sha256": huellas["poblacion"], "role": "population"}]}
    return cfg


def _topologia_declarada(root: Path, c: dict, eleccion: str, cpro: str, secc: Path) -> list[dict]:
    """T-405: acreditaciones de municipios no conexos de la época (topologia_administrativa.json), comprobadas contra el seccionado:
    sha256 de la fuente, secciones existentes y todas del municipio declarado. Sin declaración: lista vacía (el motor decide)."""
    ruta = root / DIR_CONTRATOS / "topologia_administrativa.json"
    if not ruta.exists():
        return []
    e = (json.loads(ruta.read_text(encoding="utf-8")).get("elecciones") or {}).get(eleccion)
    decl = ((e or {}).get("provincias") or {}).get(cpro) or []
    if not decl:
        return []
    if e["seccionado_sha256"] != c["seccionado"]["sha256"]:
        raise ErrorContrato(f"TOPOLOGIA_DE_OTRO_SECCIONADO {eleccion}/{cpro}: re-acreditar para {c['seccionado']['sha256'][:12]}")
    g = _leer_seccionado(secc, cpro)
    mun = {str(a): str(b) for a, b in zip(g["CUSEC"], g["CUMUN"])}
    salida = []
    for d in decl:
        codigo = d["admin_scope"].split(":", 1)[1]
        miembros = [x for comp in d["components"] for x in comp]
        # el municipio del seccionado debe estar entero en la declaración (ni de menos ni de más)
        if set(miembros) != {s for s, m in mun.items() if m == codigo}:
            raise ErrorContrato(f"TOPOLOGIA_NO_CUBRE_EL_MUNICIPIO {eleccion}/{cpro} {d['admin_scope']}")
        salida.append({k: v for k, v in d.items() if k != "municipio"})
    return salida


def _puentes_de_epoca(root: Path, c: dict, eleccion: str, cpro: str, base: dict, geo: set[str], secc: Path) -> list:
    """T-400: puentes del contrato base con un extremo ausente del seccionado de la época. Si hay declaración atada al sha256 del
    seccionado (`puentes_epoca.json`), el puente se omite: la sección declarada (debe existir y ser del mismo municipio) ya
    contiene el extremo y lo une por geometría; sin declaración, FALLA cerrado. Los puentes sin extremo ausente pasan tal cual."""
    ruta = root / DIR_CONTRATOS / "puentes_epoca.json"
    e = {}
    if ruta.exists():
        e = (json.loads(ruta.read_text(encoding="utf-8")).get("elecciones") or {}).get(eleccion) or {}
    decl = {d["seccion_base"]: d for d in (e.get("provincias") or {}).get(cpro, [])}
    if decl and e.get("seccionado_sha256") != c["seccionado"]["sha256"]:
        raise ErrorContrato(f"PUENTES_DE_OTRO_SECCIONADO {eleccion}/{cpro}: re-acreditar para {c['seccionado']['sha256'][:12]}")
    salida = []
    for puente in (base["modulos"]["modulo_02_construir_adyacencias"].get("topology_bridges") or []):
        pu, quitar = copy.deepcopy(puente), False
        for k in ("u", "v"):
            x = str(pu[k]).zfill(10)
            if x in geo:
                continue
            d = decl.get(x)
            if d is None or d["seccion_epoca"] not in geo or d["seccion_epoca"][:5] != x[:5]:
                raise ErrorContrato(f"PUENTE_FUERA_DEL_SECCIONADO {cpro} {puente}")
            quitar = True  # la sección de la época ya contiene el extremo: M02 rechaza un puente sin desconexión que resolver
        if not quitar:
            salida.append(pu)
    return salida


def _exenciones_declaradas(root: Path, eleccion: str | None, cpro: str | None, c: dict | None) -> list[dict]:
    """D-185: exenciones de suelo de partición declaradas para (elección, provincia) en `exenciones_suelo_epoca.json`, atadas al sha256 del seccionado."""
    ruta = root / DIR_CONTRATOS / "exenciones_suelo_epoca.json"
    if not (ruta.exists() and eleccion and cpro and c):
        return []
    e = (json.loads(ruta.read_text(encoding="utf-8")).get("elecciones") or {}).get(eleccion) or {}
    decl = (e.get("provincias") or {}).get(cpro) or []
    if decl and e.get("seccionado_sha256") != c["seccionado"]["sha256"]:
        raise ErrorContrato(f"EXENCIONES_DE_OTRO_SECCIONADO {eleccion}/{cpro}: re-acreditar para {c['seccionado']['sha256'][:12]}")
    return decl


def _reparto_particiones(root: Path, base: dict, territorio: str, k: int, pob: dict[str, dict], eleccion: str | None = None,
                         cpro: str | None = None, c: dict | None = None) -> dict | None:
    """T-400 (D-180): reparto de K por partición insular con la población de la época (Hamilton por componentes, ≥ 1 por partición y
    suelo factible; `component_hamilton` de materializar_contrato_generacion, el mismo criterio que el contrato 2025). Una partición de
    un distrito bajo el suelo queda declarada como exención. None si el contrato base no es de particiones físicas."""
    if not (base.get("validation") or {}).get("hard_partition_mode"):
        return None
    import materializar_contrato_generacion as mcg
    pops = mcg._component_populations(root, territorio, {s: int(f["poblacion"]) for s, f in pob.items()})
    razon = float(base["territory_contract"]["population_floor_ratio"])
    cuota, exentas = mcg.component_hamilton(pops, k, razon)
    politica = base["territory_contract"].get("small_component_exception_policy")
    declaradas = _exenciones_declaradas(root, eleccion, cpro, c)
    if declaradas and not politica:  # D-185: la exención la gobierna la declaración atada al seccionado, no la política del contrato base
        if set(exentas) != {d["particion"] for d in declaradas}:
            raise ErrorContrato(f"EXENCION_DE_SUELO_DISTINTA_DE_LA_DECLARADA {territorio}: calculadas {exentas}, declaradas "
                                f"{[d['particion'] for d in declaradas]}")
        politica = declaradas[0]["politica"]
    auditoria = mcg.component_apportionment_audit(pops, cuota, k, razon, exentas, exception_policy=politica)
    return {"poblaciones": pops, "cuota": cuota, "exentas": exentas, "auditoria": auditoria, "suelo_ratio": razon,
            "exenciones_declaradas": declaradas, "politica_excepcion": politica,
            "motivo": "D-180 (propietario, 19-11): K por partición insular con Hamilton y la población de la época; una partición de un distrito "
                      "bajo el suelo queda exenta (una isla, un distrito)"}


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
    sp = p["poblacion"].get("sin_poblacion_resuelto") or {}  # T-399 (D-158 B'): reparto madre/hijas y rellenadas declarados
    pob = aplicar_relleno(aplicar_reparto(pob, sp.get("repartidas", [])), sp.get("rellenadas", []))
    sin_pob, sin_geo = sorted(geo - set(pob)), sorted(set(pob) - geo)
    if sin_pob or sin_geo:  # las no resueltas (sin sucesora en su provincia) fallan cerrado
        raise ErrorContrato(f"CASADO_POBLACION_SECCIONADO {territorio} {eleccion}: sin población {len(sin_pob)} {sin_pob[:5]}; "
                            f"población sin geometría {len(sin_geo)} {sin_geo[:5]}")
    base = yaml.safe_load(base_path.read_text(encoding="utf-8"))
    puentes = _puentes_de_epoca(root, c, eleccion, cpro, base, geo, secc)
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
    topologia = _topologia_declarada(root, c, eleccion, cpro, secc)
    cfg = contrato_provincia(base, c, cpro, eleccion, rel(secc_local), rel(pob_local), huellas, sha256(cpath), geometria, topologia, puentes, _reparto_particiones(root, base, territorio, p["K"], pob, eleccion, cpro, c))
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


def informe_sin_poblacion(root: Path = ROOT) -> tuple[list[dict], list[dict]]:
    """T-399: por elección y provincia con secciones del seccionado sin población (rellenadas), y por municipio su cuadre (desde el contrato)."""
    prov, mun = [], []
    for e in sorted(ELECCIONES):
        c = json.loads(ruta_contrato(e, root).read_text(encoding="utf-8"))
        for cpro, p in sorted(c["provincias"].items()):
            r = p["poblacion"].get("sin_poblacion_resuelto")
            if not r:
                continue
            cu = r["cuadre_municipal"]
            rep = r.get("repartidas", [])
            prov.append({"eleccion": e, "provincia": cpro, "territorio": p["territorio"], "estado": p["estado"],
                         "madres": len(rep), "hijas": sum(sum(y["rol"] == "hija" for y in x["miembros"]) for x in rep),
                         "habitantes_madres_censo": r.get("habitantes_madres_censo", 0),
                         "habitantes_repartidos_a_hijas": r.get("habitantes_repartidos_a_hijas", 0),
                         "secciones_rellenadas": len(r["rellenadas"]), "secciones_sin_dato": len(r["sin_dato"]),
                         "habitantes_atlas": r["habitantes_atlas"], "habitantes_rellenados": r["habitantes_rellenados"],
                         "pct_estimada": p["poblacion"]["pct_no_dato"], "municipios_sin_ajuste": sum(x["estado"].startswith("aviso") for x in cu),
                         "votos_sin_asignar_pct": (p["poblacion"].get("votos_sin_asignar") or {}).get("pct", "")})
            mun += [{"eleccion": e, "provincia": cpro, **x} for x in cu]
    return prov, mun


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="accion", required=True)
    a1 = sub.add_parser("contrato")
    a1.add_argument("--eleccion", required=True, choices=sorted(ELECCIONES))
    a1.add_argument("--tabla", type=Path, required=True, help="tabla de población por sección (T-358/T-364)")
    a1.add_argument("--tabla-origen", required=True, help="herramienta y versión que produjo la tabla")
    a1.add_argument("--seccionado", type=Path, required=True, help="seccionado INE del año (zip, sha256 de fuentes_r2.json)")
    a1.add_argument("--donantes", type=Path, help="carpeta con seccionado_AAAA.zip de otros años (D-153)")
    a1.add_argument("--censo", type=Path, help="ZIP indicadores_seccion_censal_csv del Censo 2011 (T-399: verifica la población de las madres)")
    a1.add_argument("--atlas", type=Path, help="CSV 30832 del INE (T-399: relleno de secciones sin población)")
    a1.add_argument("--total-municipal", type=Path, help="D-185: 1mun00.csv del INE (total municipal del Censo 2011, sha256 en total_municipal_censo_2011.json)")
    a1.add_argument("--version", default=VERSION)
    a1.add_argument("--anterior", default="ninguna (fichero nuevo)")
    a1.add_argument("--salida", type=Path)
    a3 = sub.add_parser("geometria", help="T-402: informe de secciones corregidas por provincia (área antes/después)")
    a3.add_argument("--eleccion", required=True, choices=sorted(ELECCIONES))
    a3.add_argument("--fuentes", type=Path, required=True)
    a3.add_argument("--salida", type=Path)
    a2 = sub.add_parser("informe")
    a2.add_argument("--salida", type=Path)
    a3 = sub.add_parser("informe_poblacion")
    a3.add_argument("--salida", type=Path, help="CSV por provincia")
    a3.add_argument("--salida-municipios", type=Path, help="CSV por municipio (cuadre)")
    for nombre in ("materializar", "electoral", "cadena"):
        s = sub.add_parser(nombre)
        s.add_argument("--eleccion", required=True, choices=sorted(ELECCIONES))
        s.add_argument("--territorio", required=True)
        s.add_argument("--fuentes", type=Path, required=True, help="carpeta con las fuentes locales (bajar_fuentes.sh)")
        s.add_argument("--salida", type=Path, default=ROOT / "salida_historico_epoca")
    a = ap.parse_args(argv)
    if a.accion == "contrato":
        c = construir_contrato(a.eleccion, a.tabla, a.tabla_origen, a.version, a.anterior, seccionado=a.seccionado,
                               donantes=a.donantes, atlas=a.atlas, censo=a.censo,
                               total_municipal_fuente=a.total_municipal)
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
    if a.accion == "informe_poblacion":
        prov, mun = informe_sin_poblacion()
        for filas, destino in ((prov, a.salida), (mun, a.salida_municipios)):
            with (open(destino, "w", encoding="utf-8", newline="") if destino else sys.stdout) as f:
                w = csv.DictWriter(f, list(filas[0]) if filas else ["eleccion"], lineterminator="\n")
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
