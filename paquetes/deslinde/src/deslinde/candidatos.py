#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: Deslinde — candidatos de la competición: canónico (M06 dado), vigente (opcional) y ReCom ponderado
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Deslinde 1.0.0 · candidatos sin rutas del repo
FECHA: 2026-11-14
ESTADO: candidato (paquete Deslinde, T-257)
CAMBIOS: 1.0.0 — fichero nuevo (T-257, D-88): el código de los candidatos de Deslinde 1.0 sale sin cambios de
  ddd_motor2/generadores.py 1.2.3 (piezas_finas, municipios_divisibles, reparar, Vigente, Ponderado) y de
  ddd_motor2/produccion.py 1.1.2 (CanonicoDelRun). Cambios: el ámbito (Congreso o no) lo da el resolutor de
  deslinde.territorio; el vigente es un CSV que da quien llama (el repo sigue dando el del visor, como subclase) y su
  «origen» lo decide la subclase. Mismos planes.
MOTIVO: T-257: paquete independiente con fuente única; ddd_motor2 importa de aquí.
CANDIDATOS (§5 de docs/ARQUITECTURA/DESLINDE_1_0.md):
  CanonicoDelRun  el M06 dado (en producción, el que acaba de producir el run): no se recalcula.
  Vigente         el mapa vigente (opcional) sobre las filas del canónico, con piezas finas y reparación mínima.
  Ponderado       cadena ReCom ponderado (deslinde.ponderado.cadena) desde el canónico o el vigente.
ANTERIOR: ninguna (fichero nuevo)
"""
from __future__ import annotations

import csv
import hashlib
import shutil
from collections import defaultdict
from fractions import Fraction
from pathlib import Path

from . import territorio as _territorio
from .competicion import EntradaTerritorio, Salida


class CanonicoDelRun:
    """El canónico es el M06 que el run acaba de producir (M04 + M05 canónico + M06 de producción): no se recalcula."""

    nombre = "canonico"

    def __init__(self, composicion: Path, atributos: Path | None):
        self.composicion, self.atributos = Path(composicion), atributos

    def generar(self, entrada, semilla, destino: Path):
        destino = Path(destino)
        destino.mkdir(parents=True, exist_ok=True)
        if not self.composicion.is_file():
            return Salida(None, "SIN_M06", f"sin composición M06 del run ({self.composicion})")
        copia = destino / self.composicion.name
        shutil.copy2(self.composicion, copia)
        atr = None
        if self.atributos is not None and self.atributos.is_file():
            atr = destino / self.atributos.name
            shutil.copy2(self.atributos, atr)
        return Salida(copia, "OK", atributos_secciones=atr, extra={"origen": "M06 del run"})


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
    if _territorio.resolutor().es_nacional(entrada.territorio):
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
    """T-217: el mapa vigente como candidato opcional (D-84), sobre las filas del canónico. Deslinde: el CSV
    (columnas seccion,distrito) lo da quien llama; el repo (ddd_motor2.generadores.Vigente) da el publicado en el
    visor (T-258)."""

    nombre = "vigente"

    def __init__(self, composicion: Path | None = None, run: str | None = None):
        self.composicion, self.run = (Path(composicion) if composicion else None), run

    def ruta(self, t: str) -> tuple[Path | None, str | None, str]:
        """(composición, run, motivo si no hay)."""
        if self.composicion is None or not self.composicion.is_file():
            return None, None, f"no hay mapa vigente ({self.composicion or 'sin fichero'})"
        return self.composicion, self.run, ""

    def origen(self, ruta: Path) -> str:
        return ruta.name

    def generar(self, entrada: EntradaTerritorio, semilla: int | None, destino: Path) -> Salida:
        from .adaptadores import columnas_de_contrato, problema_y_plan
        from .reglas import Criterio, Reglas
        ctx = entrada.contexto
        comp = ctx.get("composicion_canonica")
        ruta, run, motivo = self.ruta(entrada.territorio)
        if ruta is None:
            return Salida(None, "SIN_VIGENTE", motivo)
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
            return Salida(None, "VIGENTE_OTRO_SECCIONADO",
                          f"vigente excluido: otro seccionado ({ruta.name}): {len(secs - set(vig))} secciones de la "
                          f"entrada sin distrito vigente, "
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
        extra = {"origen": self.origen(ruta), "run": run, "sha256_origen": hashlib.sha256(ruta.read_bytes()).hexdigest(),
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
        from .ponderado import cadena
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
