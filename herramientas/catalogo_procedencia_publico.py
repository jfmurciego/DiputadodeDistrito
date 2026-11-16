#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Versión pública (lista blanca) del catálogo de procedencia (T-361).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.1 · FECHA: 2026-11-16 · ESTADO: candidato
CAMBIOS: 1.0.1: valida también los VALORES permitidos (tipo y formato; url https de dominios oficiales; sin run id, rutas internas ni r2://) y falla cerrado.
  1.0.0: fichero nuevo.
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
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORIGEN = ROOT / "orchestracion" / "catalogo_procedencia.json"
SCHEMA = "ddd.catalogo-procedencia-publico/1.0"
CAMPOS_FUENTE = ("proveedor", "url")
CAMPOS_PRODUCTO = ("producto", "eleccion", "eleccion_declarada", "vigente", "sha256", "generado")
CAMPOS_FUENTE_TERRITORIAL = ("population_year", "section_year")


DOMINIOS = ("ine.es", "interior.gob.es", "boe.es")
PRODUCTOS = {"M06", "M08", "composicion", "resultados", "static", "ensemble", "datos_abiertos"}
RE_FECHA = re.compile(r"\d{4}-\d{2}-\d{2}")
RE_SHA = re.compile(r"[0-9a-f]{64}")
RE_ID = re.compile(r"[A-Za-z0-9_]{1,40}")
RE_NOMBRE_LARGO = re.compile(r"[^/\\:<>\n]{1,120}")
RE_VERSION = re.compile(r"[0-9A-Za-z][0-9A-Za-z.+\-]{0,30}")
RE_NOMBRE = re.compile(r"[A-Za-zÁÉÍÓÚáéíóúñÑ0-9 ._\-]{1,60}")
PROHIBIDO = re.compile(r"\b\d{10,}\b|territorios/|receipt|r2://|actions/runs", re.I)


class ErrorCatalogo(Exception):
    pass


def _ok(v, regex, ruta):
    if not isinstance(v, str) or not regex.fullmatch(v):
        raise ErrorCatalogo(f"{ruta}: valor con formato no permitido")
    return v


def _url(v, ruta):
    from urllib.parse import urlsplit
    u = urlsplit(v) if isinstance(v, str) else None
    h = (u.hostname or "") if u else ""
    if not u or u.scheme != "https" or not any(h == d or h.endswith("." + d) for d in DOMINIOS):
        raise ErrorCatalogo(f"{ruta}: url no permitida")
    return v


def _valida_valores(o, ruta="$"):
    """Ningún string público (clave o valor) puede llevar run id, rutas internas o r2://."""
    if isinstance(o, dict):
        for k, v in o.items():
            if PROHIBIDO.search(str(k)):
                raise ErrorCatalogo(f"{ruta}: clave con contenido interno")
            _valida_valores(v, f"{ruta}.{k}")
    elif isinstance(o, list):
        for i, v in enumerate(o):
            _valida_valores(v, f"{ruta}[{i}]")
    elif isinstance(o, str) and PROHIBIDO.search(o):
        raise ErrorCatalogo(f"{ruta}: valor con contenido interno")


def _tomar(d, campos):
    return {k: d[k] for k in campos if k in d}


def _fuente(d, ruta):
    if not isinstance(d, dict) or not isinstance(d.get("url"), str):
        raise ErrorCatalogo(f"{ruta}: falta fuente con url")
    _url(d["url"], ruta + ".url")
    if "proveedor" in d:
        _ok(d["proveedor"], RE_NOMBRE_LARGO, ruta + ".proveedor")
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
    _ok(motor["nombre"], RE_NOMBRE, "motor.nombre")
    if "version" in motor:
        _ok(motor["version"], RE_VERSION, "motor.version")
    pub_fo = {k: _fuente(fo.get(k), "fuentes_oficiales." + k) for k in ("poblacion_por_sexo_y_edad", "secciones_censales")}
    res = fo.get("resultados_electorales")
    if not isinstance(res, dict) or not res:
        raise ErrorCatalogo("falta fuentes_oficiales.resultados_electorales")
    pub_fo["resultados_electorales"] = {_ok(f, RE_FECHA, "resultados_electorales.fecha"): _fuente(v, "resultados_electorales." + f) for f, v in res.items()}
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
            _ok(p["producto"], RE_ID, f"{tid}.producto")
            if p["producto"] not in PRODUCTOS:
                raise ErrorCatalogo(f"territorio {tid}: producto desconocido")
            if not isinstance(p["vigente"], bool):
                raise ErrorCatalogo(f"territorio {tid}: vigente no booleano")
            if "eleccion" in p:
                _ok(p["eleccion"], RE_FECHA, f"{tid}.eleccion")
            if "sha256" in p and p["sha256"] is not None:
                _ok(p["sha256"], RE_SHA, f"{tid}.sha256")
            if "eleccion_declarada" in p and not isinstance(p["eleccion_declarada"], bool):
                raise ErrorCatalogo(f"territorio {tid}: eleccion_declarada no booleano")
            if "generado" in p:
                _ok(p["generado"], RE_FECHA, f"{tid}.generado")
            if p["vigente"] and (not p.get("eleccion") or not p.get("sha256")):
                raise ErrorCatalogo(f"territorio {tid}: producto vigente sin eleccion/sha256")
            prods.append(_tomar(p, CAMPOS_PRODUCTO))
        ft = _tomar(t.get("fuente_territorial") or {}, CAMPOS_FUENTE_TERRITORIAL)
        for k, v in ft.items():
            if not isinstance(v, int) or isinstance(v, bool) or not 1900 <= v <= 2100:
                raise ErrorCatalogo(f"territorio {tid}.{k}: año no válido")
        pub_t[_ok(tid, RE_ID, "territorio")] = {"fuente_territorial": ft, "productos": prods}
    pub = {"schema": SCHEMA, "motor": _tomar(motor, ("nombre", "version")), "fuentes_oficiales": pub_fo, "territorios": pub_t}
    _valida_valores(pub)
    return pub


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
