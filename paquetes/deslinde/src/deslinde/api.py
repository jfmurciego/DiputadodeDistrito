#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: Deslinde — API pública mínima: entradas → competición → ganador y aceptación
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Deslinde 1.0.0 · API pública
FECHA: 2026-11-14
ESTADO: candidato (paquete Deslinde, T-257)
CAMBIOS: 1.0.0 — fichero nuevo (T-257, D-88).
MOTIVO: usar Deslinde fuera del repo con la misma competición que el P30 de producción (ddd_motor2/produccion.py):
  canónico = el M06 dado, vigente opcional (D-84), N cadenas ReCom ponderado con las semillas públicas, exhaustivo si
  cabe en el presupuesto, elección D8.
USO:
  from deslinde import api
  r = api.competir("contrato.yaml", "m03_grafo.json", "m06_composicion.csv", "salida/", territorio="NAC22",
                   tablas=("partidos_judiciales.csv", "comarcas_agrarias.csv", "areas_movilidad_2019.csv"),
                   vigente="vigente.csv", atributos="m06_secciones.geojson.zip")
  r["ganador"], r["estado"], r["huella_resultado"]
ANTERIOR: ninguna (fichero nuevo)
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import sys
from importlib import metadata
from pathlib import Path
from typing import Any, Mapping

VERSION = "1.0.0"
ESQUEMA = "deslinde-resultado/1"
CADENAS = 10       # D-67
FUNCION = "D8"     # D-84


def _sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _version(m: str) -> str | None:
    try:
        return metadata.version(m)
    except metadata.PackageNotFoundError:
        return None


def hashseed_fijo() -> bool:
    """PYTHONHASHSEED=0 de verdad: con `python -I` o `-E` la variable está pero Python la ignora (y el orden de los
    conjuntos cambia las cadenas; T-257 lo comprobó en nac26)."""
    return os.environ.get("PYTHONHASHSEED") == "0" and not sys.flags.ignore_environment


def entorno() -> dict:
    return {"python": platform.python_version(), "PYTHONHASHSEED": os.environ.get("PYTHONHASHSEED"),
            "ignora_entorno": bool(sys.flags.ignore_environment), "hashseed_fijo": hashseed_fijo(),
            **{m: _version(m) for m in ("gerrychain", "networkx", "rustworkx", "scipy", "numpy", "geopandas")}}


def cargar_contrato(contrato: str | Path | Mapping[str, Any]) -> dict:
    """Contrato MATERIALIZADO (validation con K, suelo, techo y tolerancia; generation_state.source_inputs)."""
    if isinstance(contrato, Mapping):
        return dict(contrato)
    import yaml  # noqa: PLC0415
    return yaml.safe_load(Path(contrato).read_text(encoding="utf-8")) or {}


def competir(contrato, grafo_m03, composicion_m06, destino, *, territorio: str, tablas=None, vigente=None,
             atributos=None, n_cadenas: int = CADENAS, funcion: str = FUNCION, criterio=None,
             exhaustivo: bool = True) -> dict:
    """Competición pública de Deslinde. `territorio`: código oficial (NAC22, AUT17…) o, con un resolutor registrado
    (deslinde.territorio.registrar), su id. `tablas`: deslinde.tablas.Tablas o (partidos, comarcas, areas); sin ellas,
    las registradas (con D8 hacen falta). Escribe COMPETICION.{json,md} y DESLINDE.json en `destino`."""
    from . import tablas as _tablas  # noqa: PLC0415
    from .candidatos import CanonicoDelRun, Ponderado, Vigente  # noqa: PLC0415
    from .competicion import EntradaTerritorio, competir_publico  # noqa: PLC0415
    from .informe import escribir  # noqa: PLC0415
    if tablas is not None:
        _tablas.registrar(tablas if isinstance(tablas, _tablas.Tablas) else _tablas.desde_ficheros(*tablas))
    cfg = cargar_contrato(contrato)
    destino = Path(destino)
    shutil.rmtree(destino, ignore_errors=True)
    comp = Path(composicion_m06)
    entrada = EntradaTerritorio(territorio, cfg, Path(grafo_m03))
    vig = Vigente(Path(vigente)) if vigente is not None else None
    res = competir_publico(entrada, CanonicoDelRun(comp, Path(atributos) if atributos else None), Ponderado(),
                           destino / "competicion", n_cadenas=n_cadenas, criterio=criterio, exhaustivo=exhaustivo,
                           funcion=funcion, vigente=vig)
    escribir(res, destino)
    g = res.ganador
    estado = ("SIN_GANADOR_VALIDO" if not res.valido else "GANA_CANONICO" if g.id == res.canonico.id else
              "GANA_OTRO_PLAN")
    fuentes = []
    if funcion != "A":
        try:
            fuentes = list(_tablas.tablas().fuentes)
        except Exception:  # noqa: BLE001  (sin tablas, la competición ya lo ha dicho en cada candidato)
            fuentes = []
    salida = {"schema": ESQUEMA, "version_deslinde": VERSION, "territorio": territorio, "funcion": funcion,
              "cadenas": int(n_cadenas), "estado": estado, "ganador": g.id, "generador": g.generador,
              "valido": bool(res.valido), "huella_resultado": res.huella(), "semilla_publica": res.semilla_publica,
              "composicion_m06_sha256": _sha(comp) if comp.is_file() else None,
              "ganador_composicion": str(g.composicion) if g.composicion else None,
              "ganador_composicion_sha256": g.composicion_sha256,
              "tablas_naturalidad": fuentes,
              "vigente": {k: (res.vigente or {}).get(k) for k in ("estado", "compite", "detalle", "sha256_origen",
                                                                 "reparado")},
              "candidatos": len(res.candidatos), "candidatos_validos": sum(c.estado == "VALIDO" for c in res.candidatos),
              "entorno": entorno()}
    (destino / "DESLINDE.json").write_text(json.dumps(salida, indent=2, ensure_ascii=False, default=str) + "\n",
                                           encoding="utf-8")
    return salida


def aceptar(resultado: Mapping[str, Any]) -> dict:
    """Aceptación mínima del resultado (lo de ACEPTACION_MOTOR2.md que no necesita la batería): hay ganador válido.
    «Nunca peor que el canónico ni que el vigente válido» se cumple por construcción (compiten; competicion.py)."""
    vig = resultado.get("vigente") or {}
    motivos = [] if resultado.get("valido") else ["sin ganador válido: no se publica"]
    return {"aceptado": not motivos, "motivos": motivos, "vigente_compite": bool(vig.get("compite"))}
