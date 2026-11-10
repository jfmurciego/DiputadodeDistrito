#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: motor 2 — adaptadores de generador para la competición (canónico y GerryChain)
VERSIÓN: 1.1.0
NOMBRE DE VERSIÓN: Competición · generador ponderado
FECHA: 2026-11-10
ESTADO: candidato (motor 2; producción no lo importa)
CAMBIOS: 1.1.0 — generador «Ponderado» (T-205): las cadenas ReCom del laboratorio de naturalidad (árbol de expansión
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
ANTERIOR: legacy/ddd_motor2/generadores_v1.0.2_20261110.py
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

import shutil
import sys
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
        comp = ctx.get("composicion_canonica")
        if comp is None or not Path(comp).is_file():
            return Salida(None, "SIN_CANONICO", "el ponderado parte de la composición canónica y no la hay")
        criterio = ctx.get("criterio") or Criterio()
        funcion = ctx.get("funcion") or "D8"
        clave = "B" if funcion in ("A", "C") else funcion  # con A la cadena busca lo mismo que C
        atributos = ctx.get("atributos_canonicos") or entrada.atributos_secciones
        reglas = Reglas.desde_contrato(entrada.cfg, criterio)
        problema, plan, _ = problema_y_plan(comp, entrada.grafo_m03, entrada.cfg,
                                            referencia_nucleos=ctx.get("referencia_nucleos"),
                                            atributos_secciones=atributos,
                                            respaldo_municipio_cusec=criterio.respaldo_municipio_cusec)
        nat = natural_desde_m06(problema, reglas, comp, entrada.grafo_m03, entrada.cfg)
        nat.u0 = plan
        r = cadena(nat, int(semilla), self.pasos, (clave,), nat.recargos(*self.recargo))
        mejor = r["mejor"].get(clave)
        destino = Path(destino)
        salida = escribir_composicion(comp, mejor[1] if mejor else plan, destino / Path(comp).name, entrada.cfg)
        return Salida(salida, "OK", atributos_secciones=atributos,
                      extra={"pasos": self.pasos, "recargo": list(self.recargo), "clave_cadena": clave,
                             "unicos": r["unicos"], "fallo": r["fallo"], "tiempo_s": round(r["tiempo_s"], 3)})
