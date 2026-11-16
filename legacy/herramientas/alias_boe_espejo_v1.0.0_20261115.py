#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mapa espejo→sigla BOE por elección y provincia, SOLO para el contraste de la puerta del histórico (T-343).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-15 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
CAMBIOS: 1.0.0: fichero nuevo (revisión de #813: unicidad de la sigla del espejo, columna `fuerza`, regla CONTENIDA_EN_SIGLA_BOE retirada por no generar filas).
MOTIVO: la puerta del histórico (T-342) exige que TODO partido del CSV oficial del BOE de la provincia se compare con el
  espejo (cobertura total). Las siglas del BOE y las del espejo (Observatorio, T-89) no coinciden en coaliciones y federaciones
  («LA IZQUIERDA PLURAL» frente a «IU-LV», «PSOE» frente a «PSE-EE (PSOE)»). Orden del Planificador: el alias sale de ficheros con
  sha256, los votos validan pero no justifican, y lo que no se acredita con fichero se lista y la provincia falla.
QUÉ HACE: `generar` lee los CSV oficiales del BOE (configuracion/resultados_oficiales_congreso_<año>.csv) y el espejo (verificando el
  sha256 de cada fichero contra orchestracion/fuente_nazioenbehatokia.json) y, para cada sigla del BOE que no está tal cual en el
  espejo de la provincia, acredita la correspondencia SOLO con estas pruebas, todas de los propios ficheros:
  (1) ETIQUETA: una etiqueta del espejo en esa provincia cuyo texto prueba la sigla del BOE: prefijo literal de ≥ 10 caracteres
      (el espejo corta las etiquetas largas), texto igual tras quitar puntuación, tokens de la sigla del BOE (≥ 2) dentro de la
      etiqueta, o la sigla del BOE (≥ 6 caracteres normalizados, o como token entero) dentro de la etiqueta;
  (2) FAMILIA: la familia nativa del espejo (campo `f`) de una etiqueta de otra provincia de la MISMA elección que ya prueba la
      misma sigla del BOE por (1) o que la lleva tal cual; sirve solo si la familia es única para esa sigla y la provincia tiene
      UNA sola sigla de esa familia (correspondencia 1:1).
  FUERZA de la prueba (columna `fuerza`): ETIQUETA = el texto de la etiqueta del espejo en esa provincia prueba la sigla; FAMILIA = prueba
  más débil: se apoya en el campo `f` del espejo y en una semilla (la etiqueta de otra provincia de la misma elección que ya prueba la
  sigla, o la propia sigla tal cual). Una sigla del espejo no puede acreditar dos siglas del BOE de la misma provincia (se contaría
  dos veces): si ocurre, ninguna se acredita (SIGLA_ESPEJO_DUPLICADA). El texto del BOE NO está en el repositorio: solo el id BOE-A-… y el
  sha256 del documento (fichas resultados_oficiales_congreso_<año>.json), así que la prueba de texto es la del espejo, no la del BOE.
  Lo demás NO se acredita: se escribe en el CSV de no acreditados con su motivo y la provincia falla en la puerta (no se supone).
  La diferencia de votos frente al BOE se anota como validación (no como prueba). La homologación D-20 (T-97) no se usa ni se cambia.
  `comprobar` revalida sin red: cabecera, claves únicas, sha256 de los ficheros del espejo (manifiesto), del CSV del BOE y del
  documento del BOE contra su ficha JSON, y que cada alias tiene prueba (regla) y fuente.
AVISO: las siglas de coalición cambian entre elecciones; los resultados por coalición NO son comparables entre elecciones.
Uso: python herramientas/alias_boe_espejo.py generar --espejo DIR [--salida configuracion]
     python herramientas/alias_boe_espejo.py comprobar
"""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).parent))
import fuente_nazioenbehatokia as fnb  # noqa: E402

ELECCIONES = {"201111": "2011_11", "201512": "2015_12", "201606": "2016_06", "201904": "2019_04", "201911": "2019_11", "202307": "2023"}
ACREDITADOS = "configuracion/alias_siglas_boe_espejo.csv"
NO_ACREDITADOS = "configuracion/alias_siglas_boe_espejo_no_acreditados.csv"
MANIFIESTO = "orchestracion/fuente_nazioenbehatokia.json"
CAB = ["eleccion", "provincia", "sigla_boe", "siglas_espejo", "regla", "prueba", "sha256_espejo", "fuente_boe", "sha256_documento_boe",
       "sha256_csv_boe", "validacion_votos", "aviso", "fuerza"]
CAB_NO = ["eleccion", "provincia", "sigla_boe", "motivo"]
AVISO = "coaliciones: no comparables entre elecciones"


def sha256(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().upper()
    return re.sub(r"[^A-Z0-9]+", "", re.sub(r"COALICION|[«»\"]", "", s))


def _tokens(s: str) -> set:
    return {norm(t) for t in re.split(r"[^\w]+", s) if norm(t)}


def prueba_etiqueta(b: str, s: str) -> str | None:
    """Regla por la que la etiqueta del espejo `s` prueba la sigla del BOE `b`, o None."""
    if s == b:
        return None
    if len(s.strip()) >= 10 and b.startswith(s.strip()):
        return "PREFIJO_TRUNCADO"
    nb, ns = norm(b), norm(s)
    if nb == ns:
        return "NORMALIZADA_IGUAL"
    tb, ts = _tokens(b), _tokens(s)
    if len(tb) >= 2 and tb <= ts:
        return "TOKENS_BOE_EN_ETIQUETA"
    if len(nb) >= 6 and nb in ns:
        return "CONTIENE_SIGLA_BOE"
    if nb in ts:
        return "SIGLA_BOE_COMO_TOKEN"
    return None


def _leer_boe(raiz: Path, rel: str) -> dict:
    out: dict = collections.defaultdict(dict)
    with (raiz / f"configuracion/resultados_oficiales_congreso_{rel}.csv").open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            out[r["codigo"]][r["partido"]] = int(r["votos"])
    return out


def _espejo(espejo: Path, clave: str, cpro: str, manifiesto: dict) -> tuple[dict, str]:
    """({sigla con votos: (votos, familia)}, sha256 del fichero); falla si el sha256 no es el del manifiesto."""
    ruta = f"data/{clave}/sekzioa/{cpro}.json"
    f = espejo / ruta
    real = sha256(f)
    esperado = manifiesto["ficheros"][ruta]["sha256"]
    if real != esperado:
        raise SystemExit(f"ESPEJO_SHA256_DISTINTO {ruta}: {real} != {esperado}")
    doc = json.loads(f.read_text(encoding="utf-8"))
    fam = dict(zip(doc["s"], doc["f"]))
    return {s: (n, fam[s]) for s, n in fnb.totales_provincia(doc).items() if n > 0}, real


def generar(espejo: Path, raiz: Path = ROOT, manifiesto: dict | None = None, elecciones: dict | None = None) -> tuple[list, list]:
    manifiesto = manifiesto or json.loads((raiz / MANIFIESTO).read_text(encoding="utf-8"))
    ok, no = [], []
    pendientes: list = []
    for k, rel in (elecciones or ELECCIONES).items():
        ficha = json.loads((raiz / f"configuracion/resultados_oficiales_congreso_{rel}.json").read_text(encoding="utf-8"))
        fuente = {"boe": ficha["boe"], "doc": ficha["sha256_xml"], "csv": sha256(raiz / f"configuracion/resultados_oficiales_congreso_{rel}.csv")}
        boe = _leer_boe(raiz, rel)
        D, H = {}, {}
        for c in sorted(boe):
            D[c], H[c] = _espejo(espejo, k, c, manifiesto)
        semillas: dict = collections.defaultdict(lambda: collections.defaultdict(list))  # sigla BOE → familia → [(prov, etiqueta, regla)]
        for c, ps in sorted(boe.items()):
            for b in ps:
                if b in D[c]:
                    semillas[b][D[c][b][1]].append((c, b, "EXACTA"))
                    continue
                for s, (n, f) in sorted(D[c].items()):
                    r = None if s in ps else prueba_etiqueta(b, s)
                    if r:
                        semillas[b][f].append((c, s, r))
        for c, ps in sorted(boe.items()):
            for b, v in sorted(ps.items()):
                if b in D[c]:
                    continue
                directos = [(s, prueba_etiqueta(b, s)) for s in sorted(D[c]) if s not in ps and prueba_etiqueta(b, s)]
                if directos:
                    ss, regla = [s for s, _ in directos], "ETIQUETA:" + "+".join(sorted({r for _, r in directos}))
                    prueba = " | ".join(f"{s} ({r})" for s, r in directos)
                else:
                    fs = semillas.get(b, {})
                    if not fs:
                        no.append([k, c, b, "SIN_ETIQUETA_NI_FAMILIA: ninguna etiqueta del espejo de esta elección prueba la sigla"])
                        continue
                    if len(fs) > 1:
                        no.append([k, c, b, "FAMILIAS_AMBIGUAS: " + ",".join(sorted(fs))])
                        continue
                    fam, sem = next(iter(fs.items()))
                    ss = sorted(s for s, (n, f) in D[c].items() if f == fam and s not in ps)
                    if len(ss) != 1:
                        no.append([k, c, b, f"FAMILIA_NO_1A1: familia {fam}, siglas {ss}"])
                        continue
                    regla = "FAMILIA:" + fam
                    c0, s0, r0 = sorted(sem)[0]
                    prueba = f"{ss[0]} familia {fam}; semilla {c0} {s0} ({r0})"
                dif = (v - sum(D[c][s][0] for s in ss)) / v
                pendientes.append([k, c, b, "|".join(ss), regla, prueba, H[c], fuente["boe"], fuente["doc"], fuente["csv"],
                                   f"defecto {dif:.5f}", AVISO, regla.split(":")[0].lower()])
    uso = collections.Counter((f[0], f[1], x) for f in pendientes for x in f[3].split("|"))
    for f in pendientes:
        dup = [x for x in f[3].split("|") if uso[(f[0], f[1], x)] > 1]
        if dup:
            no.append([f[0], f[1], f[2], f"SIGLA_ESPEJO_DUPLICADA: {dup} acreditaría a más de una sigla del BOE"])
        else:
            ok.append(f)
    return ok, no


def _escribir(ruta: Path, cab: list, filas: list) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(cab)
        w.writerows(sorted(filas, key=lambda r: (r[0], r[1], r[2])))


def comprobar(raiz: Path = ROOT) -> list:
    """Errores de la tabla versionada (sin red)."""
    err = []
    man = json.loads((raiz / MANIFIESTO).read_text(encoding="utf-8"))["ficheros"]
    with (raiz / ACREDITADOS).open(encoding="utf-8", newline="") as fh:
        rd = csv.reader(fh)
        cab, filas = next(rd), list(rd)
    if cab != CAB:
        err.append("CABECERA_ACREDITADOS")
    claves = collections.Counter((f[0], f[1], f[2]) for f in filas)
    err += [f"CLAVE_REPETIDA {k}" for k, n in claves.items() if n > 1]
    fichas = {k: json.loads((raiz / f"configuracion/resultados_oficiales_congreso_{rel}.json").read_text(encoding="utf-8"))
              for k, rel in ELECCIONES.items()}
    for f in filas:
        d = dict(zip(CAB, f))
        if d["sha256_espejo"] != man.get(f"data/{d['eleccion']}/sekzioa/{d['provincia']}.json", {}).get("sha256"):
            err.append(f"SHA_ESPEJO {d['eleccion']} {d['provincia']}")
        fi = fichas[d["eleccion"]]
        if (d["fuente_boe"], d["sha256_documento_boe"]) != (fi["boe"], fi["sha256_xml"]):
            err.append(f"FUENTE_BOE {d['eleccion']} {d['sigla_boe']}")
        if d["sha256_csv_boe"] != sha256(raiz / f"configuracion/resultados_oficiales_congreso_{ELECCIONES[d['eleccion']]}.csv"):
            err.append(f"SHA_CSV_BOE {d['eleccion']}")
        if not d["regla"].split(":")[0] in ("ETIQUETA", "FAMILIA") or not d["prueba"] or not d["siglas_espejo"]:
            err.append(f"SIN_PRUEBA {d['eleccion']} {d['provincia']} {d['sigla_boe']}")
        if d["fuerza"] != d["regla"].split(":")[0].lower():
            err.append(f"FUERZA {d['eleccion']} {d['provincia']} {d['sigla_boe']}")
    uso = collections.Counter((f[0], f[1], x) for f in filas for x in f[3].split("|"))
    err += [f"SIGLA_ESPEJO_DUPLICADA {k}" for k, n in uso.items() if n > 1]
    return err


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("orden", choices=["generar", "comprobar"])
    ap.add_argument("--espejo", type=Path, help="DIR con data/<elección>/sekzioa/<cpro>.json (sha256 del manifiesto)")
    ap.add_argument("--salida", type=Path, default=ROOT)
    a = ap.parse_args(argv)
    if a.orden == "comprobar":
        e = comprobar()
        print("\n".join(e) or "OK")
        return 1 if e else 0
    if not a.espejo:
        ap.error("generar necesita --espejo")
    ok, no = generar(a.espejo)
    _escribir(a.salida / ACREDITADOS, CAB, ok)
    _escribir(a.salida / NO_ACREDITADOS, CAB_NO, no)
    print(f"acreditados {len(ok)}; no acreditados {len(no)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
