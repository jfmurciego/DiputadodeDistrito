#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: motor 2 — adaptadores de generador para la competición (canónico y GerryChain)
VERSIÓN: 1.2.0
NOMBRE DE VERSIÓN: Competición · vigente y piezas finas
FECHA: 2026-11-10
ESTADO: candidato (motor 2; producción no lo importa)
CAMBIOS: 1.2.0 — (T-217) generador «Vigente»: el mapa publicado (datos/composicion/<t>.csv) como composición M06 sobre
  las filas del canónico (población de la entrada; si las secciones no coinciden, o el mapa parte un municipio que el
  contrato declara atómico, no es representable y no compite); el «Ponderado» parte del vigente con las semillas que le
  diga el contexto («semillas_desde_vigente»; la competición le da la mitad). Si el publicado incumple el núcleo
  (hecho con otro M04: R-NUCLEO; o R-MUN-MIXTOS como Ávila), «vigente reparado» (D-66): reparación mínima y
  determinista (`reparar`), que se juzga de nuevo; lo publicado (fuera de tolerancia, validez, infracciones) queda en
  extra["publicado"] y los pasos en extra["reparacion"]. Las cadenas del Ponderado usan la clave de naturalidad_clave
  1.1.0 (primer término = fuera de tolerancia del contrato), así que con varias circunscripciones su recorrido cambia. (T-218, D-79) «piezas_finas»: fuera
  del Congreso, la unidad de la cadena es la sección en los municipios de más de municipality_atomicity_limit_ratio ×
  objetivo (la atomicidad que declara el contrato, como el laboratorio) y el municipio entero en los demás; no cambia
  suelo, techo, K, tolerancia ni la regla de distritos mixtos (el núcleo las juzga igual). Sin piezas finas en el
  Congreso ni con partitioning connected_internal_units (Extremadura, Principado de Asturias).
  1.1.0 — generador «Ponderado» (T-205): las cadenas ReCom del laboratorio de naturalidad (árbol de expansión
  con recargo por partido judicial, comarca agraria, área de movilidad y frontera corta;
  naturalidad_competicion.cadena) sobre las unidades M04 y el grafo M03 de la composición canónica, con el núcleo
  como restricción en cada paso; devuelve el mejor estado según la función de la competición (D8 por defecto) como
  composición M06 con las filas de la canónica. Solo ddd_motor2: producción (M04/M05/ddd_core) intacta.
  1.0.2 — GeoJSON de secciones con extensión fija (.geojson.zip, si no .geojson) y orden estable;
  1.0.1 — los atributos se toman del GeoJSON M06 de SECCIONES (*_m06_secciones.geojson*), no del de
  distritos (Congreso Huesca daba ERROR_DATOS «propiedades sin CUSEC_KEY» en los 6 candidatos).
MOTIVO: T-163: que el orquestador (competicion.py) llame a los generadores reales sin tocarlos, con las mismas
  entradas y pasos que la batería T-132 (herramientas/bateria_motor.py y banco_generadores.py), que se importan en
  diferido y no se modifican.
ANTERIOR: legacy/ddd_motor2/generadores_v1.1.0_20261110.py
GENERADORES:
  Canonico    M04 + M05 canónico vigente (7.4.4, semilla fija) + M06 = bateria_motor.motor_uno(t, out, "7.4.4").
  GerryChain  M04 + M05 GerryChain de producción ddd_core/m05_gerrychain_strategy.py (ReCom, --seed-count 1
              --seed-base <semilla>; si la Formación M04 no es admisible, desde la semilla canónica) + M06
              = banco_generadores.ejecutar_uno(t, out, "gerrychain", semilla).
  Se elige m05_gerrychain_strategy entre las tres implementaciones (strategy, engine, ddd_ensemble) porque es la de
  producción y la única con evidencia en los 71 (T-132: válido 355/355, mejor de 5 mejora 19, empata 45); engine y
  ddd_ensemble son para muestrear ensembles (diagnóstico estadístico), no para optimizar un plan.
  Ambos escriben donde la batería (<out>/motor/7.4.4/<t>, <out>/banco/gerrychain-s<n>/<t>); la composición M06 y el
  GeoJSON M06 se copian al destino del candidato. Requiere las entradas de la batería (<out>/entradas/<t>) y, para
  GerryChain, el entorno /opt/ddd-gerrychain (DDD_GERRYCHAIN_PYTHON).
"""
from __future__ import annotations

import csv
import hashlib
import shutil
import sys
from collections import defaultdict
from fractions import Fraction
from pathlib import Path

from .competicion import EntradaTerritorio, Salida

ROOT = Path(__file__).resolve().parents[1]
M05_CANONICO = "7.4.4"


def _bateria():
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from herramientas import bateria_motor as bm
    return bm


def entrada_bateria(t: str, out: Path) -> EntradaTerritorio:
    """Entrada de la competición desde las entradas archivadas de la batería (<out>/entradas/<t>)."""
    bm = _bateria()
    src = Path(out) / "entradas" / t
    grafo = next(src.glob("*_m03_grafo.json"), None)
    if grafo is None:
        raise FileNotFoundError(f"{src}: sin grafo M03 (¿faltan las entradas de la batería?)")
    return EntradaTerritorio(t, bm._cfg(t), grafo, contexto={"out": str(out)})


def _salida(res: dict, dir_bateria: Path, destino: Path) -> Salida:
    destino.mkdir(parents=True, exist_ok=True)
    comp = next(dir_bateria.glob("*_m06_composicion_distritos.csv"), None) if dir_bateria.is_dir() else None
    if comp is None:
        return Salida(None, str(res.get("estado")), f"sin composición M06 ({res.get('estado')})", extra=res)
    copia = destino / comp.name
    shutil.copy2(comp, copia)
    atributos = None
    cache = _bateria()._cache(res["territorio"])
    geos = sorted(cache.glob("*_m06_secciones.geojson.zip")) or sorted(cache.glob("*_m06_secciones.geojson"))
    geo = geos[0] if geos else None
    if geo is not None:
        atributos = destino / geo.name
        shutil.copy2(geo, atributos)
    resumen = {k: res.get(k) for k in ("estado", "validacion", "fallos", "tiempos", "m04_admisible",
                                       "semilla_inicial", "m05_informe", "metricas") if k in res}
    return Salida(copia, str(res.get("estado")), atributos_secciones=atributos, extra=resumen)


class Canonico:
    nombre = "canonico"

    def generar(self, entrada: EntradaTerritorio, semilla: int | None, destino: Path) -> Salida:
        out = Path(entrada.contexto["out"])
        res = _bateria().motor_uno(entrada.territorio, out, M05_CANONICO)
        return _salida(res, out / "motor" / M05_CANONICO / entrada.territorio, destino)


class GerryChain:
    nombre = "gerrychain"

    def generar(self, entrada: EntradaTerritorio, semilla: int | None, destino: Path) -> Salida:
        if semilla is None:
            raise ValueError("GerryChain exige semilla")
        out = Path(entrada.contexto["out"])
        _bateria()  # pone ROOT en sys.path
        from herramientas import banco_generadores as bg
        res = bg.ejecutar_uno(entrada.territorio, out, "gerrychain", int(semilla))
        return _salida(res, out / "banco" / f"gerrychain-s{int(semilla)}" / entrada.territorio, destino)


def _ratio_atomicidad(cfg) -> Fraction | None:
    """municipality_atomicity_limit_ratio del contrato (validation, territory_contract o el M04)."""
    for sec in ((cfg or {}).get("validation"), (cfg or {}).get("territory_contract"),
                ((cfg or {}).get("modulos") or {}).get("modulo_04_generar_semillas")):
        if isinstance(sec, dict) and sec.get("municipality_atomicity_limit_ratio") is not None:
            return Fraction(str(sec["municipality_atomicity_limit_ratio"]))
    return None


def municipios_divisibles(problema, reglas, cfg) -> tuple[set[str], Fraction | None]:
    """Municipios de más de ratio × objetivo regional (los que el contrato deja partir) y el límite."""
    ratio = _ratio_atomicidad(cfg)
    if ratio is None:
        return set(), None
    limite = reglas.limites(problema.poblacion_total)[0] * ratio
    pm: dict[str, int] = defaultdict(int)
    for u in problema.unidades:
        if u.municipio and not u.desglose:
            pm[u.municipio] += u.poblacion
    return {m for m, p in pm.items() if p > limite}, limite


def _filas(comp: Path) -> tuple[list[str], list[dict]]:
    with open(comp, encoding="utf-8", newline="") as fh:
        rd = csv.DictReader(fh)
        return list(rd.fieldnames or []), list(rd)


def _escribir(campos: list[str], filas: list[dict], destino: Path) -> Path:
    destino.parent.mkdir(parents=True, exist_ok=True)
    with open(destino, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=campos)
        w.writeheader()
        w.writerows(filas)
    return destino


def piezas_finas(comp: Path, entrada: EntradaTerritorio, destino: Path, atributos=None, criterio=None) -> tuple[Path, dict]:
    """T-218: copia de la composición con una unidad por sección en los municipios divisibles según el contrato
    («<unidad M04>~<sección>»); los demás municipios siguen enteros. Sin cambios en el Congreso y con unidades internas
    (partitioning connected_internal_units): devuelve la misma composición."""
    from .adaptadores import columnas_de_contrato, problema_y_plan
    from .reglas import Criterio, Reglas
    cfg = entrada.cfg
    part = cfg.get("partitioning") or {}
    if entrada.territorio.startswith("congreso_"):
        return Path(comp), {"aplicadas": False, "motivo": "Congreso: unidades M04"}
    if part.get("enabled") and part.get("strategy") == "connected_internal_units":
        return Path(comp), {"aplicadas": False, "motivo": "unidades internas del contrato (connected_internal_units)"}
    criterio = criterio or Criterio()
    problema, _, _ = problema_y_plan(comp, entrada.grafo_m03, cfg, atributos_secciones=atributos,
                                     respaldo_municipio_cusec=criterio.respaldo_municipio_cusec)
    grandes, limite = municipios_divisibles(problema, Reglas.desde_contrato(cfg, criterio), cfg)
    if limite is None:
        return Path(comp), {"aplicadas": False, "motivo": "el contrato no declara municipality_atomicity_limit_ratio"}
    mun = {u.id: u.municipio for u in problema.unidades if not u.desglose}
    col = columnas_de_contrato(cfg)
    campos, filas = _filas(Path(comp))
    n = 0
    for f in filas:
        uid = str(f.get(col["unidad"]) or f[col["seccion"]]).strip()
        if mun.get(uid) in grandes:
            f[col["unidad"]] = f"{uid}~{str(f[col['seccion']]).strip()}"
            n += 1
    if col["unidad"] not in campos:
        campos.append(col["unidad"])
    salida = _escribir(campos, filas, Path(destino))
    return salida, {"aplicadas": True, "limite": float(limite), "municipios_divisibles": len(grandes),
                    "secciones_sueltas": n, "unidades_antes": len(problema.unidades)}


def reparar(problema, reglas, plan: dict[str, str], max_pasos: int = 20) -> tuple[dict[str, str], list[str]]:
    """Vigente reparado (D-66, T-217): reparación mínima y determinista de las infracciones del núcleo que deja un mapa
    hecho con otro M04. Cada paso arregla una infracción sin crear ninguna nueva (de otra regla o ámbito):
      R-NUCLEO   las unidades del núcleo cerrado pasan al distrito que ya tiene más población del núcleo (empate: la
                 etiqueta menor); si ese distrito tiene unidades ajenas al núcleo, cada una pasa al distrito de una
                 vecina que no sea del núcleo (el de etiqueta menor).
      R-MUN-MIXTOS las unidades del municipio en el distrito mixto con menos población del municipio pasan a otro distrito
                 del mismo municipio (como el «vigente reparado» del laboratorio).
    Devuelve (plan, notas); plan vacío si no se repara."""
    from .reglas import evaluar
    pob = {u.id: u.poblacion for u in problema.unidades}
    nucleo = {u.id: u.nucleo_cerrado for u in problema.unidades if u.nucleo_cerrado is not None}
    mun = {u.id: u.municipio for u in problema.unidades}
    vecinos: dict[str, set] = defaultdict(set)
    for a, b in tuple(problema.aristas) + tuple(problema.puentes):
        vecinos[a].add(b)
        vecinos[b].add(a)
    plan, notas = dict(plan), []

    def clave_v(v):
        return (v.regla, v.ambito)

    for _ in range(max_pasos):
        inf = evaluar(problema, reglas, plan)
        if inf.valido:
            return plan, notas
        antes = {clave_v(v) for v in inf.violaciones}
        v = next((x for x in inf.violaciones if x.regla in ("R-NUCLEO", "R-MUN-MIXTOS")), None)
        if v is None:
            notas.append(f"sin reparación para {sorted(antes)[:5]}")
            return {}, notas
        intentos = []
        if v.regla == "R-NUCLEO":
            nuc = sorted(u for u, n in nucleo.items() if str(n) == v.ambito)  # ámbito = «nucleo:<distrito>»
            if not nuc:
                notas.append(f"{v.ambito}: sin unidades del núcleo")
                return {}, notas
            por_d: dict[str, int] = defaultdict(int)
            for u in nuc:
                por_d[plan[u]] += pob[u]
            dest = min(por_d, key=lambda d: (-por_d[d], d))
            prueba = {**plan, **{u: dest for u in nuc}}
            ajenas = sorted(u for u, d in prueba.items() if d == dest and u not in set(nuc))
            for u in ajenas:
                otros = sorted({prueba[w] for w in vecinos[u] if w not in set(nuc) and prueba[w] != dest})
                if otros:
                    prueba[u] = otros[0]
            movidas = [u for u in plan if plan[u] != prueba[u]]
            intentos.append((prueba, f"{v.ambito}: {len(movidas)} unidades ({sum(pob[u] for u in movidas)} hab.) "
                                     f"al distrito {dest} o a vecinos"))
        else:
            m = v.ambito
            de_m: dict[str, list[str]] = defaultdict(list)
            otros_m: dict[str, int] = defaultdict(int)
            for u, d in plan.items():
                if mun.get(u) == m:
                    de_m[d].append(u)
                else:
                    otros_m[d] += 1
            mixtos = sorted((d for d in de_m if otros_m.get(d)), key=lambda d: (sum(pob[u] for u in de_m[d]), d))
            for d in mixtos:
                for dest in sorted(x for x in de_m if x != d):
                    intentos.append(({**plan, **{u: dest for u in de_m[d]}},
                                     f"{m}: {len(de_m[d])} unidades ({sum(pob[u] for u in de_m[d])} hab.) del "
                                     f"distrito {d} al {dest}"))
        hecho = False
        for prueba, nota in intentos:
            despues = {clave_v(x) for x in evaluar(problema, reglas, prueba).violaciones}
            if clave_v(v) not in despues and despues <= antes:
                plan, hecho = prueba, True
                notas.append(nota)
                break
        if not hecho:
            notas.append(f"{v.regla} {v.ambito}: ninguna reparación mínima vale ({len(intentos)} intentos)")
            return {}, notas
    notas.append(f"más de {max_pasos} pasos")
    return {}, notas


class Vigente:
    """T-217: el mapa vigente publicado (datos/composicion/<t>.csv) como candidato, sobre las filas del canónico."""

    nombre = "vigente"

    def __init__(self, carpeta: Path | None = None):
        self.carpeta = Path(carpeta) if carpeta else ROOT / "datos" / "composicion"

    def generar(self, entrada: EntradaTerritorio, semilla: int | None, destino: Path) -> Salida:
        from .adaptadores import columnas_de_contrato, problema_y_plan
        from .reglas import Criterio, Reglas
        ctx = entrada.contexto
        comp = ctx.get("composicion_canonica")
        ruta = self.carpeta / f"{entrada.territorio}.csv"
        if not ruta.is_file():
            return Salida(None, "SIN_VIGENTE", f"no hay mapa publicado ({ruta.name})")
        if comp is None or not Path(comp).is_file():
            return Salida(None, "SIN_CANONICO", "el vigente se monta sobre las filas del canónico y no las hay")
        with open(ruta, encoding="utf-8", newline="") as fh:
            vig = {str(r["seccion"]).strip(): str(r["distrito"]).strip() for r in csv.DictReader(fh)}
        destino = Path(destino)
        criterio = ctx.get("criterio") or Criterio()
        atributos = ctx.get("atributos_canonicos") or entrada.atributos_secciones
        base, info = piezas_finas(Path(comp), entrada, destino / "piezas_finas.csv", atributos, criterio)
        col = columnas_de_contrato(entrada.cfg)
        campos, filas = _filas(base)
        secs = {str(f[col["seccion"]]).strip() for f in filas}
        if secs != set(vig):
            return Salida(None, "VIGENTE_NO_REPRESENTABLE",
                          f"secciones distintas de la entrada: {len(secs - set(vig))} sin distrito vigente, "
                          f"{len(set(vig) - secs)} del vigente que no están en la entrada")
        problema, _, _ = problema_y_plan(base, entrada.grafo_m03, entrada.cfg, atributos_secciones=atributos,
                                         respaldo_municipio_cusec=criterio.respaldo_municipio_cusec)
        # solo con piezas finas (autonómicas): en el Congreso o con unidades internas las unidades M04 no se parten
        grandes = (municipios_divisibles(problema, Reglas.desde_contrato(entrada.cfg, criterio), entrada.cfg)[0]
                   if info.get("aplicadas") else set())
        mun = {u.id: u.municipio for u in problema.unidades}
        uid = lambda f: str(f.get(col["unidad"]) or f[col["seccion"]]).strip()  # noqa: E731
        ds: dict[str, set] = defaultdict(set)
        for f in filas:
            ds[uid(f)].add(vig[str(f[col["seccion"]]).strip()])
        partidas = sorted(u for u, d in ds.items() if len(d) > 1)
        atomicas = [u for u in partidas if mun.get(u) not in grandes]
        if atomicas:
            return Salida(None, "VIGENTE_NO_REPRESENTABLE",
                          f"el vigente parte {len(atomicas)} unidades que aquí no se pueden partir (municipio atómico "
                          f"según el contrato o unidad M04 sin piezas finas; p. ej. {atomicas[0]})")
        for f in filas:
            d = vig[str(f[col["seccion"]]).strip()]
            if uid(f) in partidas:  # pieza M04 de un municipio divisible repartida en el vigente: una por distrito
                f[col["unidad"]] = f"{uid(f)}~v{d}"
            f[col["distrito"]] = d
        salida = _escribir(campos, filas, destino / Path(comp).name)
        extra = {"origen": f"datos/composicion/{ruta.name}", "sha256_origen": hashlib.sha256(ruta.read_bytes()).hexdigest(),
                 "unidades_divididas": len(partidas), "piezas_finas": info}
        # D-66: si el publicado incumple el núcleo (otro M04), vigente reparado; lo publicado queda en «publicado»
        from .exhaustivo import escribir_composicion
        reglas = Reglas.desde_contrato(entrada.cfg, criterio)
        ref = ctx.get("referencia_nucleos")
        prob_v, plan_v, _ = problema_y_plan(salida, entrada.grafo_m03, entrada.cfg, referencia_nucleos=ref,
                                            atributos_secciones=atributos,
                                            respaldo_municipio_cusec=criterio.respaldo_municipio_cusec)
        from .reglas import evaluar
        inf = evaluar(prob_v, reglas, plan_v)
        extra["publicado"] = {"fuera_tolerancia": len(inf.metricas["fuera_tolerancia"]), "valido": inf.valido,
                              "violaciones": [[x.regla, x.ambito] for x in inf.violaciones][:20]}
        if not inf.valido:
            plan_r, notas = reparar(prob_v, reglas, plan_v)
            extra["reparacion"] = notas
            if plan_r:
                salida = escribir_composicion(salida, plan_r, destino / "reparado" / Path(comp).name, entrada.cfg)
                extra["reparado"] = True
            else:
                extra["reparado"] = False
        return Salida(salida, "OK", atributos_secciones=atributos, extra=extra)


class Ponderado:
    """Cadena del laboratorio de naturalidad desde la composición canónica (entrada.contexto, lo pone competir)."""

    nombre = "ponderado"

    def __init__(self, pasos: int = 300, rpj: float = 0.5, rca: float = 0.3, rmov: float = 0.2, rlong: float = 0.3):
        self.pasos, self.recargo = pasos, (rpj, rca, rmov, rlong)

    def generar(self, entrada: EntradaTerritorio, semilla: int | None, destino: Path) -> Salida:
        from .adaptadores import problema_y_plan
        from .exhaustivo import escribir_composicion
        from .naturalidad_clave import natural_desde_m06
        from .naturalidad_competicion import cadena
        from .reglas import Criterio, Reglas
        if semilla is None:
            raise ValueError("Ponderado exige semilla")
        ctx = entrada.contexto
        inicio = "vigente" if semilla in (ctx.get("semillas_desde_vigente") or ()) else "canonico"
        comp = ctx.get("composicion_vigente" if inicio == "vigente" else "composicion_canonica")
        if comp is None or not Path(comp).is_file():
            return Salida(None, "SIN_CANONICO", f"el ponderado parte de la composición {inicio} y no la hay")
        criterio = ctx.get("criterio") or Criterio()
        funcion = ctx.get("funcion") or "D8"
        clave = "B" if funcion in ("A", "C") else funcion  # con A la cadena busca lo mismo que C
        atributos = ctx.get("atributos_canonicos") or entrada.atributos_secciones
        reglas = Reglas.desde_contrato(entrada.cfg, criterio)
        destino = Path(destino)
        nombre = Path(comp).name
        comp, finas = piezas_finas(Path(comp), entrada, destino / "piezas_finas.csv", atributos, criterio)
        problema, plan, _ = problema_y_plan(comp, entrada.grafo_m03, entrada.cfg,
                                            referencia_nucleos=ctx.get("referencia_nucleos"),
                                            atributos_secciones=atributos,
                                            respaldo_municipio_cusec=criterio.respaldo_municipio_cusec)
        nat = natural_desde_m06(problema, reglas, comp, entrada.grafo_m03, entrada.cfg)
        nat.u0 = plan
        r = cadena(nat, int(semilla), self.pasos, (clave,), nat.recargos(*self.recargo))
        mejor = r["mejor"].get(clave)
        salida = escribir_composicion(comp, mejor[1] if mejor else plan, destino / nombre, entrada.cfg)
        return Salida(salida, "OK", atributos_secciones=atributos,
                      extra={"inicio": inicio, "piezas_finas": finas, "unidades": len(problema.unidades),
                             "pasos": self.pasos, "recargo": list(self.recargo), "clave_cadena": clave,
                             "unicos": r["unicos"], "fallo": r["fallo"], "tiempo_s": round(r["tiempo_s"], 3)})
