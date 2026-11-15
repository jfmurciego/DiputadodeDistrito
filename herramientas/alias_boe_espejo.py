#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mapa espejo→sigla BOE por elección y provincia, SOLO para el contraste de la puerta del histórico (T-343).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.1.0 · FECHA: 2026-11-15 · ESTADO: candidato
ANTERIOR: legacy/herramientas/alias_boe_espejo_v1.0.0_20261115.py
CAMBIOS: 1.1.0 (T-345, D-120): regla COMPOSICION_BOE (la composición de la coalición se toma del BOE de candidaturas proclamadas, con ficha y sha256 en
  configuracion/fuentes_coaliciones_boe/) y orden `extraer`. 1.0.0: fichero nuevo (revisión de #813: unicidad de la sigla del espejo, columna `fuerza`).
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
  (3) COMPOSICION_BOE (T-345): el BOE de candidaturas proclamadas (Congreso, por circunscripción; con sus correcciones de errores) rotula cada
      candidatura «NOMBRE: PARTIDO, PARTIDO… (SIGLAS)». Si la sigla del BOE de resultados (sin «COALICIÓN» ni comillas) está en el rótulo de UNA sola
      candidatura de la provincia, la sigla del espejo se acredita solo si cada una de sus partes (separadas por «-») es un partido de ese rótulo:
      sigla entre paréntesis del BOE, nombre del partido igual a la parte, o iniciales del nombre completo de un partido del rótulo (un segmento
      entero entre separadores, nunca un tramo suelto). El texto del BOE no va entero: `extraer` descarga los documentos (ids localizados barriendo
      el sumario), verifica y deja el extracto de los rótulos con el sha256 de cada original; `generar` y `comprobar` leen el extracto.
      Si el espejo integra solo parte de los partidos del rótulo, la fila lo dice en `prueba` (los votos validan, no prueban).
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
import urllib.request
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
COMPOS = "configuracion/fuentes_coaliciones_boe"
# BOE de candidaturas proclamadas (y correcciones) de cada elección, localizados barriendo el sumario (API datosabiertos, fecha de publicación).
FUENTES_COMPOSICION = {
    "201111": {"proclamadas": ("BOE-A-2011-16745", "2011-10-25"), "correcciones": [("BOE-A-2011-16922", "2011-10-27"), ("BOE-A-2011-17013", "2011-10-28")]},
    "201512": {"proclamadas": ("BOE-A-2015-12734", "2015-11-24"),
               "correcciones": [("BOE-A-2015-13053", "2015-12-01"), ("BOE-A-2015-13247", "2015-12-05"), ("BOE-A-2015-13868", "2015-12-18")]},
}
# nombre de la Junta en el BOE → nombre de la provincia en el CSV oficial (castellano); el resto coincide tras normalizar.
NOMBRE_JUNTA = {"ALICANTE/ALACANT": "Alicante", "ARABA/ÁLAVA": "Álava", "ILLES BALEARS": "Baleares", "BIZKAIA": "Vizcaya",
                "CASTELLÓN/CASTELLÓ": "Castellón", "CORUÑA (A)": "La Coruña", "GIPUZKOA": "Guipúzcoa", "GIRONA": "Gerona", "LLEIDA": "Lérida",
                "OURENSE": "Orense", "VALENCIA/VALÈNCIA": "Valencia", "RIOJA (LA)": "La Rioja"}
CONECTORES = {"EN", "DE", "DEL", "LA", "LAS", "EL", "LOS", "Y", "E", "I", "O"}
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


# --- COMPOSICION_BOE (T-345) -------------------------------------------------------------------------------------------------------
def _descargar(url: str) -> bytes:
    rq = urllib.request.Request(url, headers={"User-Agent": "ddd-alias-boe/1.1"})
    with urllib.request.urlopen(rq, timeout=120) as r:
        return r.read()


def _parrafos(xml: str) -> list:
    """[(clase, texto)] de los párrafos del documento; los rótulos de candidatura son de clase `centro_redonda`."""
    return [(c, re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", h)).strip()) for c, h in re.findall(r"<p class=\"([^\"]*)\">(.*?)</p>", xml, re.S)]


def _cpro_por_junta(raiz: Path, rel: str) -> dict:
    nombres = {}
    with (raiz / f"configuracion/resultados_oficiales_congreso_{rel}.csv").open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            nombres[norm(r["provincia"])] = r["codigo"]
    return nombres


def _junta_a_cpro(junta: str, nombres: dict) -> str:
    alias = NOMBRE_JUNTA.get(junta, junta)
    m = re.fullmatch(r"(.+) \((LA|LAS|EL|LOS|A)\)", alias)
    clave = norm(f"{m.group(2)} {m.group(1)}") if m else norm(alias)
    if clave not in nombres and norm("LAS " + alias) in nombres:
        clave = norm("LAS " + alias)
    if clave not in nombres:
        raise SystemExit(f"JUNTA_SIN_PROVINCIA {junta}")
    return nombres[clave]


def extraer_composicion(k: str, raiz: Path = ROOT, descargar=_descargar, fecha: str = "") -> dict:
    """Extracto de los rótulos de candidaturas al Congreso por provincia (BOE de proclamadas con sus correcciones aplicadas)."""
    spec = FUENTES_COMPOSICION[k]
    nombres = _cpro_por_junta(raiz, ELECCIONES[k])
    docs = {}
    for ident, f in [spec["proclamadas"]] + spec["correcciones"]:
        b = descargar(f"https://www.boe.es/diario_boe/xml.php?id={ident}")
        docs[ident] = (b, hashlib.sha256(b).hexdigest(), f)
    junta, sec, prov = None, None, {}
    for cl, h in _parrafos(docs[spec["proclamadas"][0]][0].decode("utf-8")):
        if h.startswith("JUNTA ELECTORAL DE "):
            junta, sec = h[19:], None
            prov.setdefault(_junta_a_cpro(junta, nombres), {"junta": junta, "congreso": []})
        elif h.startswith("CONGRESO"):
            sec = "C"
        elif h.startswith("SENADO"):
            sec = "S"
        elif sec == "C" and junta and cl == "centro_redonda":
            prov[_junta_a_cpro(junta, nombres)]["congreso"].append(h)
    aplicadas = []
    for ident, _ in spec["correcciones"]:
        junta, sec = None, None
        for _, h in _parrafos(docs[ident][0].decode("utf-8")):
            if h.startswith("JUNTA ELECTORAL DE "):
                junta, sec = h[19:], None
            elif h.startswith("CONGRESO"):
                sec = "C"
            elif h.startswith("SENADO"):
                sec = "S"
            for d, e in re.findall(r"Donde dice: «(.+?)»,? ?[Dd]ebe decir: «(.+?)»", h):
                if sec == "C" and junta and re.match(r"\d+\. [A-ZÁÉÍÓÚÑ]", d):
                    c = _junta_a_cpro(junta, nombres)
                    sin = [re.sub(r"\s+", "", x) for x in prov[c]["congreso"]]
                    if re.sub(r"\s+", "", d) in sin:  # el BOE de correcciones y el de proclamadas difieren a veces en espacios
                        i = sin.index(re.sub(r"\s+", "", d))
                        aplicadas.append({"boe": ident, "provincia": c, "dice": prov[c]["congreso"][i], "debe_decir": e})
                        prov[c]["congreso"][i] = e
    return {
        "eleccion": k, "descarga": fecha or "2026-11-15", "metodo": "xml.php?id=<BOE-A-…> de boe.es; ids localizados barriendo datosabiertos/api/boe/sumario/AAAAMMDD",
        "reproducir": "python herramientas/alias_boe_espejo.py extraer",
        "documentos": [{"boe": i, "url": f"https://www.boe.es/diario_boe/xml.php?id={i}", "fecha_publicacion": f, "sha256": s,
                        "papel": "proclamadas" if i == spec["proclamadas"][0] else "correccion"} for i, (_, s, f) in docs.items()],
        "correcciones_aplicadas": aplicadas, "provincias": dict(sorted(prov.items())),
    }


def _composicion(raiz: Path, k: str) -> dict | None:
    f = raiz / COMPOS / f"candidaturas_proclamadas_{k}.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None


def _partes_sigla(s: str) -> list:
    return [x for x in (norm(p) for p in s.split("-")) if x]


def _rotulo(h: str) -> tuple:
    """(segmentos de partido normalizados con su texto, siglas entre paréntesis normalizadas) de un rótulo «N. NOMBRE: P, P (SIGLAS)»."""
    cuerpo = re.sub(r"^\d+\.\s*", "", h)
    paren = re.findall(r"\(([^()]*)\)", cuerpo)
    cuerpo = re.sub(r"\([^()]*\)", " ", cuerpo)
    segs = [s.strip() for s in re.split(r"[:,;/\-–]", cuerpo) if s.strip()]
    return segs, {norm(x) for p in paren for x in re.split(r"[-,/ ]+", p) if norm(x)}


def _iniciales(parte: str, seg: str) -> bool:
    """`parte` son las iniciales de las palabras del segmento (cada palabra aporta un prefijo ≥ 1 letra; los conectores pueden saltarse)."""
    pal = [norm(w) for w in re.split(r"\W+", seg) if norm(w)]
    if len(pal) < 2:
        return False

    def rec(i: int, pos: int) -> bool:
        if i == len(pal):
            return pos == len(parte)
        w = pal[i]
        if w in CONECTORES and rec(i + 1, pos):
            return True
        return any(parte[pos:pos + n] == w[:n] and rec(i + 1, pos + n) for n in range(1, len(w) + 1) if pos + n <= len(parte))
    return rec(0, 0)


def prueba_composicion(parte: str, segs: list, siglas: set) -> str | None:
    if parte in siglas:
        return "SIGLA_EN_ROTULO"
    if any(norm(s) == parte for s in segs):
        return "NOMBRE_DE_PARTIDO"
    if any(_iniciales(parte, s) for s in segs):
        return "INICIALES_DE_PARTIDO"
    return None


def composicion_boe(comp: dict | None, c: str, b: str, D: dict, ps: dict) -> tuple | None:
    """(siglas del espejo, prueba, BOE-A-… y sha256 del documento, regla) si el rótulo único del BOE para `b` contiene los partidos de la sigla del espejo."""
    if not comp or c not in comp["provincias"]:
        return None
    rot = [h for h in comp["provincias"][c]["congreso"] if norm(b) and norm(b) in norm(h)]
    if len(rot) != 1:
        return f"{len(rot)} rótulos del BOE de proclamadas contienen la sigla (se exige uno)"
    segs, siglas = _rotulo(rot[0])
    hallados = []
    for s in sorted(D[c]):
        if s in ps:
            continue
        partes = _partes_sigla(s)
        pruebas = [prueba_composicion(p, segs, siglas) for p in partes]
        if partes and all(pruebas):
            hallados.append((s, partes, pruebas))
    if not hallados:
        return f"ninguna sigla del espejo con todas sus partes en el rótulo del BOE: {rot[0]}"
    texto = " | ".join(f"{s} = " + "+".join(f"{p} ({r})" for p, r in zip(pp, rr)) for s, pp, rr in hallados)
    regla = "COMPOSICION_BOE:" + "+".join(sorted({r for _, _, rr in hallados for r in rr}))
    sin_cubrir = sorted(siglas - {p for _, pp, _ in hallados for p in pp})
    if sin_cubrir:
        texto += f"; paréntesis del BOE con partes que el espejo no integra: {','.join(sin_cubrir)}"
    doc = next(d for d in comp["documentos"] if d["papel"] == "proclamadas")
    return [s for s, _, _ in hallados], f"{texto}; rótulo BOE: {rot[0]}", doc["boe"], doc["sha256"], regla


def generar(espejo: Path, raiz: Path = ROOT, manifiesto: dict | None = None, elecciones: dict | None = None) -> tuple[list, list]:
    manifiesto = manifiesto or json.loads((raiz / MANIFIESTO).read_text(encoding="utf-8"))
    ok, no = [], []
    pendientes: list = []
    for k, rel in (elecciones or ELECCIONES).items():
        ficha = json.loads((raiz / f"configuracion/resultados_oficiales_congreso_{rel}.json").read_text(encoding="utf-8"))
        fuente = {"boe": ficha["boe"], "doc": ficha["sha256_xml"], "csv": sha256(raiz / f"configuracion/resultados_oficiales_congreso_{rel}.csv")}
        boe = _leer_boe(raiz, rel)
        comp = _composicion(raiz, k)
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
                fuente_f = (fuente["boe"], fuente["doc"])
                directos = [(s, prueba_etiqueta(b, s)) for s in sorted(D[c]) if s not in ps and prueba_etiqueta(b, s)]
                if directos:
                    ss, regla = [s for s, _ in directos], "ETIQUETA:" + "+".join(sorted({r for _, r in directos}))
                    prueba = " | ".join(f"{s} ({r})" for s, r in directos)
                else:
                    fs = semillas.get(b, {})
                    rechazo = None
                    if not fs:
                        rechazo = "SIN_ETIQUETA_NI_FAMILIA: ninguna etiqueta del espejo de esta elección prueba la sigla"
                    elif len(fs) > 1:
                        rechazo = "FAMILIAS_AMBIGUAS: " + ",".join(sorted(fs))
                    else:
                        fam, sem = next(iter(fs.items()))
                        ss = sorted(s for s, (n, f) in D[c].items() if f == fam and s not in ps)
                        if len(ss) != 1:
                            rechazo = f"FAMILIA_NO_1A1: familia {fam}, siglas {ss}"
                    if rechazo:
                        cb = composicion_boe(comp, c, b, D, ps)
                        if not isinstance(cb, tuple):
                            no.append([k, c, b, rechazo + (f"; COMPOSICION_BOE: {cb}" if cb else "")])
                            continue
                        ss, prueba, doc_boe, doc_sha, regla = cb
                        fuente_f = (doc_boe, doc_sha)
                    else:
                        regla = "FAMILIA:" + fam
                        c0, s0, r0 = sorted(sem)[0]
                        prueba = f"{ss[0]} familia {fam}; semilla {c0} {s0} ({r0})"
                dif = (v - sum(D[c][s][0] for s in ss)) / v
                pendientes.append([k, c, b, "|".join(ss), regla, prueba, H[c], fuente_f[0], fuente_f[1], fuente["csv"],
                                   f"defecto {dif:.5f}", AVISO, _fuerza(regla)])
    uso = collections.Counter((f[0], f[1], x) for f in pendientes for x in f[3].split("|"))
    for f in pendientes:
        dup = [x for x in f[3].split("|") if uso[(f[0], f[1], x)] > 1]
        if dup:
            no.append([f[0], f[1], f[2], f"SIGLA_ESPEJO_DUPLICADA: {dup} acreditaría a más de una sigla del BOE"])
        else:
            ok.append(f)
    return ok, no


def _fuerza(regla: str) -> str:
    tipo = regla.split(":")[0]
    return tipo if tipo == "COMPOSICION_BOE" else tipo.lower()


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
        if d["regla"].startswith("COMPOSICION_BOE:"):
            cp = _composicion(raiz, d["eleccion"])
            doc = next((x for x in (cp or {}).get("documentos", []) if x["papel"] == "proclamadas"), None)
            if not doc or (d["fuente_boe"], d["sha256_documento_boe"]) != (doc["boe"], doc["sha256"]):
                err.append(f"FUENTE_COMPOSICION {d['eleccion']} {d['provincia']} {d['sigla_boe']}")
            elif not any(h in d["prueba"] for h in cp["provincias"].get(d["provincia"], {}).get("congreso", [])):
                err.append(f"ROTULO_FUERA_DEL_EXTRACTO {d['eleccion']} {d['provincia']} {d['sigla_boe']}")
        elif (d["fuente_boe"], d["sha256_documento_boe"]) != (fi["boe"], fi["sha256_xml"]):
            err.append(f"FUENTE_BOE {d['eleccion']} {d['sigla_boe']}")
        if d["sha256_csv_boe"] != sha256(raiz / f"configuracion/resultados_oficiales_congreso_{ELECCIONES[d['eleccion']]}.csv"):
            err.append(f"SHA_CSV_BOE {d['eleccion']}")
        if not d["regla"].split(":")[0] in ("ETIQUETA", "FAMILIA", "COMPOSICION_BOE") or not d["prueba"] or not d["siglas_espejo"]:
            err.append(f"SIN_PRUEBA {d['eleccion']} {d['provincia']} {d['sigla_boe']}")
        if d["fuerza"] != _fuerza(d["regla"]):
            err.append(f"FUERZA {d['eleccion']} {d['provincia']} {d['sigla_boe']}")
    uso = collections.Counter((f[0], f[1], x) for f in filas for x in f[3].split("|"))
    err += [f"SIGLA_ESPEJO_DUPLICADA {k}" for k, n in uso.items() if n > 1]
    for k in FUENTES_COMPOSICION:
        cp = _composicion(raiz, k)
        if not cp:
            err.append(f"FALTA_FUENTE_COMPOSICION {k}")
        elif not cp["documentos"] or any(not re.fullmatch(r"[0-9a-f]{64}", x["sha256"]) or not x["boe"].startswith("BOE-A-") for x in cp["documentos"]):
            err.append(f"FICHA_COMPOSICION {k}")
    return err


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("orden", choices=["generar", "comprobar", "extraer"])
    ap.add_argument("--espejo", type=Path, help="DIR con data/<elección>/sekzioa/<cpro>.json (sha256 del manifiesto)")
    ap.add_argument("--salida", type=Path, default=ROOT)
    a = ap.parse_args(argv)
    if a.orden == "extraer":
        import datetime
        for k in FUENTES_COMPOSICION:
            doc = extraer_composicion(k, fecha=datetime.date.today().isoformat())
            ruta = a.salida / COMPOS / f"candidaturas_proclamadas_{k}.json"
            ruta.parent.mkdir(parents=True, exist_ok=True)
            ruta.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
            print(k, len(doc["provincias"]), "provincias,", len(doc["correcciones_aplicadas"]), "correcciones aplicadas")
        return 0
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
