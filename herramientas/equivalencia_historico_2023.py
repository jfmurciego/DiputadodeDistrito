#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Equivalencia de las secciones de los seccionados INE históricos (2012-2020) con el seccionado INE 2023 (T-328).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-14 · ESTADO: candidato
CAMBIOS: 1.0.0: fichero nuevo.
MOTIVO: D-105 (propietario): el histórico desde 2011 va sobre el mapa destino 2023 (como D-65) con la regla de M07 7.4.0:
  la sección partida va ENTERA al distrito con mayor población, sin repartir votos. Una tabla por seccionado histórico.
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE: por año de seccionado y provincia, las secciones históricas cuyo CUSEC no existe en 2023, o que lo conservan con
  el límite cambiado (diferencia simétrica > 5 % del área), se cruzan con las de 2023 con
  `equivalencia_seccionado_2026_2023.medir` (mismo núcleo: 1:1 al 95 %, astillas < 1 %, peso de población del padrón
  65034 a 1-1-2023, D-13). Tipos: 1:1, contenida, partida, sin_vigente. Las demás secciones conservan su CUSEC (identidad).
  Verifica el sha256 de cada ZIP contra TABLA_FUENTES (T-306 §3, docs/AUDITORIAS/T85…/informe.json); si falta el
  fichero o el sha256 no coincide, para sin escribir esa tabla. Escribe, por año:
    configuracion/equivalencia_seccionado_ine_<año>_a_2023.csv  seccion_<año>, seccion_2023, tipo, peso_area, peso_poblacion
    configuracion/equivalencia_seccionado_ine_<año>_a_2023.json fuentes con sha256, sha256 del CSV y resumen por provincia.
  Años de seccionado → elección: 2012→2011-11, 2015→2015-12, 2016→2016-06, 2019→2019-04, 2020→2019-11.
Uso: python herramientas/equivalencia_historico_2023.py --historicos DIR --s2023 seccionado_2023.zip \
       --padron 65034.csv.zip [--anios 2012 2015 2016 2019 2020]
  (DIR contiene seccionado_<año>.zip, bajados de https://www.ine.es/prodyser/cartografia/seccionado_<año>.zip)
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import equivalencia_seccionado_2026_2023 as e26  # noqa: E402
import equivalencia_seccionados as es  # noqa: E402

SCHEMA = "ddd.equivalencia-seccionado-historico-2023/1.0"
SHA_2023 = "7a15e700a4592d793230441cfcb4b72e40979998aef019ca644389271886bf1f"
SHA_PADRON = "91d3ff9a90bac1c06e26df97179daa325b65fa77c9209879d6a40333b17057f3"
# año del seccionado → (elección, sha256 del ZIP); fuente: T-306 §3 / T-85 informe.json
TABLA_FUENTES = {
    "2012": ("2011-11", "772ad76b84e1b3bb9293a5595d2ccafa06f21a3a58ccc96a9ec5dadd99e46c4a"),
    "2015": ("2015-12", "50dda58ed4afb57c7f1f38e6b6b8150768efaa225bfc3a523b9c210a2a218c03"),
    "2016": ("2016-06", "3410af763bfe58d1b0f9c0d0038cbdd6417e0f3f6d0fce6a3e70bef64c84b3e1"),
    "2019": ("2019-04", "656119dadadb57ef3fa9d20a8ba33399fe606e553c9fef3fc338786e52fae967"),
    "2020": ("2019-11", "07544bb49256e9e9f290b6f459a0a833e69c97900eb840c3f5bbe863914ede6e"),
}


def salida_csv(anio: str) -> Path:
    return ROOT / f"configuracion/equivalencia_seccionado_ine_{anio}_a_2023.csv"


def cabecera(anio: str) -> list[str]:
    return [f"seccion_{anio}", "seccion_2023", "tipo", "peso_area", "peso_poblacion"]


def verificar(ruta: Path, sha_esperado: str) -> str | None:
    """None si el fichero existe y su sha256 coincide; si no, el motivo (sin lanzar excepción)."""
    if not ruta.is_file():
        return f"falta {ruta.name}"
    real = es.sha256(ruta)
    return None if real == sha_esperado else f"sha256 de {ruta.name} = {real}, esperado {sha_esperado}"


def tabla_anio(hist: dict, s23: dict, pob: dict[str, int]) -> tuple[list[list], dict]:
    """Filas y resumen por provincia de un seccionado histórico ({cpro: {cusec: geom}}) frente al de 2023."""
    filas, provincias = [], {}
    for cpro in sorted(set(hist) | set(s23)):
        ah, a23 = hist.get(cpro, {}), s23.get(cpro, {})
        nuevas = {k: g for k, g in ah.items() if k not in a23}
        nuevas.update({k: g for k, g in ah.items()
                       if k in a23 and g.symmetric_difference(a23[k]).area > (1 - es.UMBRAL) * g.area})
        f, r = e26.medir(nuevas, a23, {k: v for k, v in pob.items() if k[:2] == cpro})
        r["secciones_hist_sin_2023"] = r.pop("secciones_2026_sin_2023")
        r["secciones_2023_sin_hist"] = len(set(a23) - set(ah))
        filas += f
        provincias[cpro] = r
    return filas, provincias


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--historicos", type=Path, required=True, help="directorio con seccionado_<año>.zip")
    ap.add_argument("--s2023", type=Path, required=True)
    ap.add_argument("--padron", type=Path, required=True, help="INE 65034 (periodo 2023), 65034.csv.zip")
    ap.add_argument("--anios", nargs="*", default=list(TABLA_FUENTES))
    a = ap.parse_args(argv)
    fallos = [m for m in (verificar(a.s2023, SHA_2023), verificar(a.padron, SHA_PADRON)) if m]
    fallos += [m for an in a.anios if (m := verificar(a.historicos / f"seccionado_{an}.zip", TABLA_FUENTES[an][1]))]
    if fallos:
        print("PARADA: no se escribe ninguna tabla.\n  " + "\n  ".join(fallos), file=sys.stderr)
        return 2
    s23, pob = es.leer_seccionado(a.s2023), es.leer_padron(a.padron, "2023")
    for an in a.anios:
        zip_h = a.historicos / f"seccionado_{an}.zip"
        filas, provincias = tabla_anio(es.leer_seccionado(zip_h), s23, pob)
        buf = io.StringIO()
        w = csv.writer(buf, lineterminator="\n")
        w.writerow(cabecera(an))
        w.writerows(filas)
        cuerpo = buf.getvalue().encode("utf-8")
        salida = salida_csv(an)
        salida.write_bytes(cuerpo)
        tot = sum(p["poblacion_2023"] for p in provincias.values())
        afe = sum(p["poblacion_afectada_partidas"] for p in provincias.values())
        meta = {"schema": SCHEMA, "decision": "D-105; regla M07 7.4.0 (sección entera al distrito de más población); peso D-13",
                "eleccion": TABLA_FUENTES[an][0],
                "csv": {"ruta": salida.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(cuerpo).hexdigest()},
                "fuentes": {f"seccionado_{an}": {"url": f"{es.URL_INE}seccionado_{an}.zip", "sha256": TABLA_FUENTES[an][1]},
                            "seccionado_2023": {"url": f"{es.URL_INE}seccionado_2023.zip", "sha256": SHA_2023},
                            "padron_65034": {"url": "https://www.ine.es/jaxiT3/files/t/csv_bdsc/65034.csv",
                                             "periodo": "2023", "sha256": SHA_PADRON}},
                "umbral_1a1": es.UMBRAL, "astilla": es.ASTILLA,
                "nacional": {"poblacion_2023": tot, "poblacion_afectada_partidas": afe,
                             "pct_poblacion_afectada": round(100 * afe / tot, 4) if tot else 0.0},
                "provincias": provincias}
        salida.with_suffix(".json").write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(an, TABLA_FUENTES[an][0], len(filas), "filas", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
