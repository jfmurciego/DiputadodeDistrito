#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inventario de fuentes por elección y provincia del histórico de generales 2011-2023 (T-81).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-07 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE: sin red, junta el manifiesto del espejo nazioenbehatokia (T-89), el contrato de Infoelectoral 2023-07 y las
  oficiales locales (2023-07, 2019-11) en orchestracion/inventario_fuentes_historico.json: por elección y provincia,
  fuente, fecha, sha256 y cobertura. Lo no adquirido queda como null/«no_adquirida»; nada se inventa.
Uso: python herramientas/inventario_fuentes_historico.py [--comprobar]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SALIDA = ROOT / "orchestracion" / "inventario_fuentes_historico.json"
FECHAS = {"201111": "2011-11-20", "201512": "2015-12-20", "201606": "2016-06-26",
          "201904": "2019-04-28", "201911": "2019-11-10", "202307": "2023-07-23"}
FECHA_ESPEJO = "2026-11-07"  # fecha del manifiesto T-89 (commit que lo añadió)


def construir(raiz: Path = ROOT) -> dict:
    man = json.loads((raiz / "orchestracion/fuente_nazioenbehatokia.json").read_text(encoding="utf-8"))
    ficheros = man["ficheros"]
    contratos = yaml.safe_load((raiz / "configuracion/contratos_infoelectoral.yaml").read_text(encoding="utf-8"))["contracts"]
    info = {c["province"]: c for c in contratos.values() if c["election_date"] == "2023-07-23"}
    prov = sorted({k.rsplit("/", 1)[1][:2] for k in ficheros if "/sekzioa/" in k})
    oficiales = {"202307": "configuracion/resultados_oficiales_congreso_2023.csv",
                 "201911": "configuracion/resultados_oficiales_congreso_2019_11.csv"}
    out = {"schema": "ddd.inventario-fuentes-historico/1.0", "generado_por": "herramientas/inventario_fuentes_historico.py",
           "elecciones": {}}
    for e in man["elecciones"]:
        k, sec = e["clave"], e["seccionado"]
        cont = man["contraste"].get(k)
        pv = {}
        for c in prov:
            d, g = ficheros.get(f"data/{k}/sekzioa/{c}.json"), ficheros.get(f"geo/sekzioak/{sec}/{c}.json")
            p = {"nazioenbehatokia": {"datos": d and {"ruta": f"data/{k}/sekzioa/{c}.json", **d},
                                      "geometria": g and {"ruta": f"geo/sekzioak/{sec}/{c}.json", **g},
                                      "fecha_espejo": FECHA_ESPEJO, "copia": man["copia_r2_prefijo"]},
                 "infoelectoral": ({"estado": "espejo_release", "release": info[c]["mirror"]["release_tag"],
                                    "sha256": info[c]["source_sha256"], "bytes": info[c]["source_bytes"]}
                                   if k == "202307" and c in info else {"estado": "no_adquirida"}),
                 "ine_seccionado": {"estado": "no_adquirido_localmente", "edicion": sec},
                 "cobertura": {"provincia": bool(d and g), "secciones": None}}
            pv[c] = p
        out["elecciones"][k] = {"fecha": FECHAS[k], "seccionado": sec,
                                "oficial_local": oficiales.get(k),
                                "contraste": ({"comparadas": cont["comparadas"], "defecto_max": cont["defecto_max"],
                                               "errores": len(cont["errores"])} if cont else None),
                                "provincias": pv}
    return out


def main(argv=None) -> int:
    nuevo = json.dumps(construir(), ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    if argv and "--comprobar" in argv:
        return 0 if SALIDA.exists() and SALIDA.read_text(encoding="utf-8") == nuevo else 1
    SALIDA.write_text(nuevo, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
