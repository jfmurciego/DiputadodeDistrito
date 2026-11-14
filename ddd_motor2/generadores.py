#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: motor 2 — adaptadores de generador para la competición (canónico y GerryChain)
VERSIÓN: 1.3.0
NOMBRE DE VERSIÓN: Deslinde 1.0.0 · candidatos desde el paquete
FECHA: 2026-11-14
ESTADO: candidato (motor 2; producción no lo importa)
CAMBIOS: 1.3.0 — (T-257, D-88) piezas_finas, municipios_divisibles, reparar, Ponderado y la lógica del Vigente se
  mueven sin cambios al paquete Deslinde (deslinde/candidatos.py) y se re-exportan aquí; Vigente queda como subclase
  que da el mapa publicado en el visor (ruta) y su origen en el repo. Canonico y GerryChain (batería) siguen aquí.
  1.2.2 — (T-258) «Vigente» lee el mapa publicado en el visor (vigente.vigente_publicado: canonical_m06 de
  mayor run en publicaciones_visor.json → datos/composicion/runs/<t>_<run>.csv, o <t>.csv si MANIFEST dice que es ese
  run), el mismo que mide la aceptación; antes leía siempre datos/composicion/<t>.csv, que en Castilla y León y 30
  del Congreso es otro mapa. Sin composición del run publicado (Canarias) no compite: «SIN_VIGENTE» con el motivo,
  nunca otro mapa. extra añade «run». Con `carpeta` (pruebas), como 1.2.1. Ponderado, Canonico y GerryChain intactos.
  1.2.1 — (T-223, Planificador) el vigente solo compite si sus secciones son exactamente las de la entrada
  (el seccionado de la edición del contrato que se genera); si no, «VIGENTE_OTRO_SECCIONADO» con el motivo
  («vigente excluido: otro seccionado», p. ej. las 52 del Congreso al pasar al par 2025/2025, D-65), sin reproyectarlo.
  1.2.0 — (T-217) generador «Vigente»: el mapa publicado (datos/composicion/<t>.csv) como composición M06 sobre
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
CAMBIOS 1.2.3 (T-220): ids de territorio nuevos de la tabla maestra (aut01…nac52, D-61); el id viejo se lee vía ddd_core.territorio_ids.
ANTERIOR: legacy/ddd_motor2/generadores_v1.2.3_20261114.py
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

from deslinde.candidatos import (  # noqa: F401  (T-257: Deslinde es la fuente única; se re-exportan)
    Ponderado, Vigente as _Vigente, _escribir, _filas, _ratio_atomicidad, municipios_divisibles, piezas_finas, reparar)

from .competicion import EntradaTerritorio, Salida
from .semilla import territorio_ids  # noqa: E402  (T-220: ámbito por el resolutor)

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


class Vigente(_Vigente):
    """T-217: el mapa vigente publicado como candidato, sobre las filas del canónico. T-258: el publicado en el visor
    (vigente.vigente_publicado, el mismo que mide la aceptación); `carpeta` (pruebas) fija <carpeta>/<t>.csv.
    La lógica (piezas finas, representabilidad, reparación) es la de Deslinde (deslinde.candidatos.Vigente)."""

    def __init__(self, carpeta: Path | None = None, root: Path | None = None):
        super().__init__()
        self.carpeta = Path(carpeta) if carpeta else None
        self.root = Path(root) if root else ROOT

    def ruta(self, t: str) -> tuple[Path | None, str | None, str]:
        """(composición, run, motivo si no hay): la del visor o, con `carpeta`, <carpeta>/<t>.csv."""
        if self.carpeta is not None:
            f = territorio_ids.fichero_por_id(self.carpeta, "{}.csv", t)
            return (f, None, "") if f.is_file() else (None, None, f"no hay mapa publicado ({f.name})")
        from .vigente import vigente_publicado
        v = vigente_publicado(t, self.root)
        return v.ruta, v.run, v.motivo

    def origen(self, ruta: Path) -> str:
        return ruta.relative_to(self.root).as_posix() if ruta.is_relative_to(self.root) else f"datos/composicion/{ruta.name}"
