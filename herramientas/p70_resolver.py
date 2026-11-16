#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Resolutores de P70 Archivo (T-368, D-131/D-132): el botón pide solo territorio y elección; el código resuelve lo técnico.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Resolutores de P70 Archivo
FECHA: 2026-11-16
ESTADO: candidato
CAMBIOS: 1.0.0: fichero nuevo (T-368).
QUÉ HACE: `paquete-p10 <territorio>` imprime el run de P10 cuyo paquete de fuentes es el vigente en el catálogo de procedencia;
  `edicion <territorio> <AAAA-MM>` comprueba la elección contra el registro electoral y da la edición de datos del catálogo;
  `fecha-eleccion <AAAA-MM>` da la fecha AAAA-MM-DD de esa elección (publicaciones del visor; 2023-07 = 2023-07-23);
  `sha-poda` imprime el sha256 aprobado de la lista de poda (fichero versionado) y se niega si la lista ya no lo cumple.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

CATALOGO = "orchestracion/catalogo_procedencia.json"
REGISTRO = "configuracion/registro_electoral.yaml"
VISOR = "orchestracion/publicaciones_visor.json"
LISTA_PODA = "docs/ESTUDIOS/T145_PODA_R2/ola1_borrar.csv"
SHA_PODA = "docs/ESTUDIOS/T145_PODA_R2/SHA256_APROBADO.txt"
_MES = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
_TERR = re.compile(r"^[a-z0-9_]+$")


def _territorio(t: str) -> str:
    t = str(t).strip()
    if not _TERR.match(t):
        raise ValueError(f"P70_TERRITORIO_INVALIDO: «{t}» (un solo código, p. ej. aut01 o nac42)")
    return t


def run_p10(root: Path, territorio: str) -> str:
    """Run de P10 del paquete de fuentes vigente del territorio (catálogo de procedencia)."""
    from ddd_core.territorio_ids import id_legacy
    t = _territorio(territorio)
    filas = json.loads((root / CATALOGO).read_text(encoding="utf-8")).get("territorios") or {}
    for clave in dict.fromkeys((t, id_legacy(t))):
        run = str(((filas.get(clave) or {}).get("fuente_territorial") or {}).get("run_id") or "")
        if run.isdigit():
            return run
    raise ValueError(f"P70_SIN_PAQUETE_P10: el catálogo no tiene paquete de fuentes de {t}")


def _edicion_catalogo(root: Path, t: str) -> str:
    from ddd_core.territorio_ids import carpeta_de
    cat = root / "territorios" / carpeta_de(root, t) / "evidencia" / "catalogo"
    ed = sorted({m.group(1) for p in cat.glob("electoral_product_*.json") if (m := re.search(r"_(\d{4})\.json$", p.name))})
    if len(ed) != 1:
        raise ValueError(f"P70_EDICION_NO_UNICA: {t} tiene producto electoral en las ediciones {ed}")
    return ed[0]


def edicion(root: Path, territorio: str, eleccion: str) -> str:
    import yaml
    from ddd_core.territorio_ids import id_legacy
    t = _territorio(territorio)
    if not _MES.match(eleccion or ""):
        raise ValueError(f"P70_ELECCION_INVALIDA: «{eleccion}» (AAAA-MM)")
    reg = (yaml.safe_load((root / REGISTRO).read_text(encoding="utf-8")) or {}).get("territories") or {}
    fila = reg.get(t) or reg.get(id_legacy(t)) or {}
    fecha = str(fila.get("election_date") or "")
    if fecha[:7] != eleccion:
        raise ValueError(f"P70_ELECCION_NO_VIGENTE: {t} tiene registrada {fecha[:7] or 'ninguna'}, no {eleccion}")
    return _edicion_catalogo(root, t)


def fecha_eleccion(root: Path, eleccion: str) -> str:
    if not _MES.match(eleccion or ""):
        raise ValueError(f"P70_ELECCION_INVALIDA: «{eleccion}» (AAAA-MM)")
    if eleccion == "2023-07":
        return "2023-07-23"
    fechas = {str(p["election_date"]) for p in json.loads((root / VISOR).read_text(encoding="utf-8")).get("products", [])
              if str(p.get("election_date") or "").startswith(eleccion)}
    if len(fechas) != 1:
        raise ValueError(f"P70_ELECCION_SIN_FECHA: {eleccion} da las fechas {sorted(fechas)} en el registro del visor")
    return fechas.pop()


def sha_poda(root: Path) -> str:
    aprobado = (root / SHA_PODA).read_text(encoding="utf-8").strip().lower()
    real = hashlib.sha256((root / LISTA_PODA).read_bytes()).hexdigest()
    if not re.fullmatch(r"[0-9a-f]{64}", aprobado) or aprobado != real:
        raise ValueError(f"P70_LISTA_NO_APROBADA: la lista de poda ({real}) no es la aprobada en {SHA_PODA} ({aprobado})")
    return aprobado


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("paquete-p10", help="run de P10 del paquete de fuentes vigente").add_argument("territorio")
    e = sub.add_parser("edicion", help="edición de datos, comprobando la elección contra el registro")
    e.add_argument("territorio")
    e.add_argument("eleccion")
    sub.add_parser("fecha-eleccion", help="fecha AAAA-MM-DD de una elección AAAA-MM").add_argument("eleccion")
    sub.add_parser("sha-poda", help="sha256 aprobado de la lista de poda")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "paquete-p10":
            print(run_p10(ROOT, a.territorio))
        elif a.cmd == "edicion":
            print(edicion(ROOT, a.territorio, a.eleccion))
        elif a.cmd == "fecha-eleccion":
            print(fecha_eleccion(ROOT, a.eleccion))
        else:
            print(sha_poda(ROOT))
    except (ValueError, OSError) as exc:
        print(f"::error::{exc}", file=sys.stderr)  # stderr: la salida estándar se captura con $(…) y ocultaría la causa
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
