#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Versión pública (lista blanca) del catálogo de procedencia (T-361).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-16 · ESTADO: candidato
CAMBIOS: 1.0.0: fichero nuevo.
MOTIVO: la P50 publicaba el catálogo entero (run_id, receipt_path, blob_sha, copias R2…); el público solo ve lo que lee el visor V3 (D-92, T-273).
ANTERIOR: ninguno
QUÉ HACE: lee orchestracion/catalogo_procedencia.json y escribe el JSON público con SOLO estas claves (las que lee visor/v3/v3.js,
  provenanceHtml): motor{nombre,version}; fuentes_oficiales{poblacion_por_sexo_y_edad|secciones_censales{proveedor,url},
  resultados_electorales[fecha]{proveedor,url}}; territorios[id]{fuente_territorial{population_year,section_year},
  productos[]{producto,eleccion,eleccion_declarada,vigente,sha256,generado}}. La huella sha256 se conserva tal cual (el visor la abrevia).
  Determinista: sort_keys, sin reloj. Falla cerrado (salida 1, sin escribir) si el origen falta, no es JSON o carece de lo que el visor necesita.
Uso: python herramientas/catalogo_procedencia_publico.py [--origen F] [--salida F]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORIGEN = ROOT / "orchestracion" / "catalogo_procedencia.json"
SCHEMA = "ddd.catalogo-procedencia-publico/1.0"
CAMPOS_FUENTE = ("proveedor", "url")
CAMPOS_PRODUCTO = ("producto", "eleccion", "eleccion_declarada", "vigente", "sha256", "generado")
CAMPOS_FUENTE_TERRITORIAL = ("population_year", "section_year")


class ErrorCatalogo(Exception):
    pass


def _tomar(d, campos):
    return {k: d[k] for k in campos if k in d}


def _fuente(d, ruta):
    if not isinstance(d, dict) or not isinstance(d.get("url"), str):
        raise ErrorCatalogo(f"{ruta}: falta fuente con url")
    return _tomar(d, CAMPOS_FUENTE)


def filtrar(cat) -> dict:
    if not isinstance(cat, dict):
        raise ErrorCatalogo("el catálogo no es un objeto JSON")
    motor = cat.get("motor")
    if not isinstance(motor, dict) or not motor.get("nombre"):
        raise ErrorCatalogo("falta motor.nombre")
    fo = cat.get("fuentes_oficiales")
    if not isinstance(fo, dict):
        raise ErrorCatalogo("falta fuentes_oficiales")
    pub_fo = {k: _fuente(fo.get(k), "fuentes_oficiales." + k) for k in ("poblacion_por_sexo_y_edad", "secciones_censales")}
    res = fo.get("resultados_electorales")
    if not isinstance(res, dict) or not res:
        raise ErrorCatalogo("falta fuentes_oficiales.resultados_electorales")
    pub_fo["resultados_electorales"] = {f: _fuente(v, "resultados_electorales." + f) for f, v in res.items()}
    terr = cat.get("territorios")
    if not isinstance(terr, dict) or not terr:
        raise ErrorCatalogo("faltan territorios")
    pub_t = {}
    for tid, t in terr.items():
        if not isinstance(t, dict) or not isinstance(t.get("productos"), list):
            raise ErrorCatalogo(f"territorio {tid}: sin productos")
        prods = []
        for p in t["productos"]:
            if not isinstance(p, dict) or not p.get("producto") or "vigente" not in p:
                raise ErrorCatalogo(f"territorio {tid}: producto sin producto/vigente")
            if p["vigente"] and (not p.get("eleccion") or not p.get("sha256")):
                raise ErrorCatalogo(f"territorio {tid}: producto vigente sin eleccion/sha256")
            prods.append(_tomar(p, CAMPOS_PRODUCTO))
        pub_t[tid] = {"fuente_territorial": _tomar(t.get("fuente_territorial") or {}, CAMPOS_FUENTE_TERRITORIAL), "productos": prods}
    return {"schema": SCHEMA, "motor": _tomar(motor, ("nombre", "version")), "fuentes_oficiales": pub_fo, "territorios": pub_t}


def serializar(pub) -> str:
    return json.dumps(pub, sort_keys=True, ensure_ascii=False, indent=1) + "\n"


def generar(origen: Path) -> str:
    try:
        cat = json.loads(Path(origen).read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ErrorCatalogo(f"no existe {origen}")
    except (ValueError, OSError) as e:
        raise ErrorCatalogo(f"{origen} no es JSON válido: {e}")
    return serializar(filtrar(cat))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--origen", type=Path, default=ORIGEN)
    ap.add_argument("--salida", type=Path, required=True)
    a = ap.parse_args(argv)
    try:
        txt = generar(a.origen)
    except ErrorCatalogo as e:
        print(f"::error::Catálogo de procedencia público: {e}", file=sys.stderr)
        return 1
    a.salida.parent.mkdir(parents=True, exist_ok=True)
    a.salida.write_text(txt, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
