#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: motor 2 — adaptadores de generador para la competición (canónico y GerryChain)
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Competición
FECHA: 2026-11-10
ESTADO: candidato (motor 2; producción no lo importa)
CAMBIOS: fichero nuevo.
MOTIVO: T-163: que el orquestador (competicion.py) llame a los generadores reales sin tocarlos, con las mismas
  entradas y pasos que la batería T-132 (herramientas/bateria_motor.py y banco_generadores.py), que se importan en
  diferido y no se modifican.
ANTERIOR: ninguna (fichero nuevo)
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
    geo = next(_bateria()._cache(res["territorio"]).glob("*_m06_secciones.geojson*"), None)
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
