#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Histórico AUTONÓMICO en el Gestor 2.0: plan y paso A (M07/M08) por comunidad y elección, con puerta (T-133).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.1 · FECHA: 2026-11-09 · ESTADO: candidato
CAMBIOS: 1.0.1 (T-134): el plan (`elecciones`, `requisitos`, `plan`) solo usa la biblioteca estándar: el job «Legislatura
  vigente» del Gestor solo instala PyYAML y fallaba con `No module named 'shapely'` (run 42705439861) al importar este
  módulo. `reagregacion_autonomicas` (shapely, geopandas) se importa de forma perezosa solo en `ejecutar`.
CAMBIOS: 1.0.0: fichero nuevo.
MOTIVO: orden del propietario (09-11): el Gestor lanza TODO el histórico, también las autonómicas desde 2011, cada
  comunidad con sus propias fechas (configuracion/calendario_autonomicas.csv, sin calendario común). Reproduce para
  las comunidades el paso A de las generales (historico_campana.py + historico_m07m08.py).
ANTERIOR: legacy/herramientas/historico_autonomico_v1.0.0_20261109.py (1.0.0 reutiliza funciones de reagregacion_autonomicas.py, reagregacion_historico.py y
  historico_m07m08.py sin modificarlas)
QUÉ HACE: `plan(comunidades, explicito)` devuelve, por comunidad, las elecciones del calendario (en alcance, no vigentes,
  con dato por sección en el Observatorio) y lo que falta (M06 publicado en orchestracion/publicaciones_visor.json con
  la misma huella que la composición, composición en datos/composicion/, paso B versionado en
  datos/resultados/historico/autonomicas/); lo pedido y no soportado falla con NoDisponible, con «todas» se omite.
  `ejecutar` (una comunidad, en el runner) reconstruye seccionado 2025 y padrón, baja el M06 del blob (sha256 de la
  composición), los ficheros del Observatorio y los seccionados INE (sha256 del MANIFEST del paso B), reagrega a la
  sección vigente, escribe el paquete M07 de cada elección, ejecuta M07 y M08 tal cual y compara con el paso B.
  Puerta: código 0 solo si el cuadre del paso B es exacto (`ok`), M07 da PASS y el ganador coincide con B en cada
  distrito.
NO HACE: publicar, ni escribir en datos/resultados/historico/ del repositorio (el resultado va al artefacto del run).
Uso: python herramientas/historico_autonomico.py ejecutar --comunidad galicia --salida DIR [--trabajo DIR]
"""
from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
sys.path.insert(0, str(ROOT))

CALENDARIO = "configuracion/calendario_autonomicas.csv"
INDICE = "fuentes/observatorio_autonomicas/index.json"

PUBLICACIONES = "orchestracion/publicaciones_visor.json"
COMPOSICION_MANIFEST = "datos/composicion/MANIFEST.json"
B = "datos/resultados/historico/autonomicas"
DESDE = "2011"
PASS = {"PASS", "PASS_WITH_DECLARED_EXCEPTIONS"}


class NoDisponible(ValueError):
    """Histórico autonómico pedido que todavía no se puede lanzar."""


def _json(root: Path, rel: str) -> dict:
    return json.loads((root / rel).read_text(encoding="utf-8"))


def leer_calendario(raiz: Path = ROOT) -> dict[str, list[dict]]:
    """{comunidad: [filas en alcance]} (como `reagregacion_autonomicas.leer_calendario`, sin sus dependencias)."""
    out: dict[str, list[dict]] = {}
    with open(raiz / CALENDARIO, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if r["en_alcance"] == "si":
                out.setdefault(r["comunidad"], []).append(r)
    return out


def _ra():
    """Módulo del paso B (shapely, geopandas): solo en el runner del histórico."""
    import reagregacion_autonomicas as ra
    return ra


def elecciones(comunidad: str, root: Path = ROOT) -> list[dict]:
    """Elecciones históricas de una comunidad: del calendario, en alcance, no vigentes, desde 2011 y con dato por sección."""
    filas = leer_calendario(root).get(comunidad, [])
    indice = _json(root, INDICE)["sekzioak"]
    return [{"eleccion": f["mes"].replace("-", ""), "fecha": f["fecha"] or f["mes"],
             "cod_ine": f["cod_ine"]} for f in filas
            if f["vigente"] != "si" and f["mes"] >= DESDE and f"{f['cod_ine']}-{f['mes'].replace('-', '')}" in indice]


def requisitos(comunidad: str, root: Path = ROOT) -> list[str]:
    """Lo que falta para el paso A de una comunidad (vacío si se puede ejecutar)."""
    falta = []
    comp = _json(root, COMPOSICION_MANIFEST)["territorios"].get(comunidad)
    if comp is None or not (root / f"datos/composicion/{comunidad}.csv").is_file():
        falta.append("sin composición (datos/composicion/)")
    elif not any(p.get("kind") == "canonical_m06" and p.get("territory_id") == comunidad
                 and p.get("blob_sha") == comp["blob_sha"] and p.get("sha256") == comp["sha256_m06"]
                 for p in _json(root, PUBLICACIONES)["products"]):
        falta.append("sin M06 publicado con la huella de la composición")
    cal = leer_calendario(root)
    if comunidad not in cal:
        falta.append("sin calendario (configuracion/calendario_autonomicas.csv)")
    els = elecciones(comunidad, root) if comunidad in cal else []
    if comunidad in cal and not els:
        falta.append("ninguna elección histórica con dato por sección")
    sin_b = [e["eleccion"] for e in els if not (root / B / comunidad / e["eleccion"] / f"{comunidad}.csv").is_file()]
    if sin_b:
        falta.append("sin paso B versionado para " + ", ".join(sin_b))
    return falta


def plan(comunidades: list[str], explicito: bool, root: Path = ROOT) -> dict:
    """comunidades = territory_id de la legislatura vigente (autonómica). Matriz del paso A, una fila por comunidad
    con sus propias elecciones."""
    ok, omitidos = [], {}
    for c in comunidades:
        falta = requisitos(c, root)
        if falta:
            omitidos[c] = "; ".join(falta)
        else:
            ok.append({"comunidad": c, "elecciones": [e["eleccion"] for e in elecciones(c, root)]})
    if omitidos and explicito:
        raise NoDisponible("Histórico autonómico no disponible para: " + " · ".join(f"{t}: {m}" for t, m in omitidos.items()))
    if not ok:
        raise NoDisponible("Ninguna comunidad de la selección tiene lo necesario para el histórico autonómico.")
    return {"clave": "autonomicas", "eleccion": "autonómicas desde 2011", "prueba": ok[0], "include": ok,
            "omitidos": omitidos}


def plan_markdown(p: dict) -> str:
    lines = ["Histórico autonómico desde 2011, paso A por comunidad y con su propio calendario: reagregación a la sección "
             "vigente → M07/M08 sobre el M06 publicado. Puerta: cuadre del paso B exacto, M07 PASS y mismo ganador que B. "
             "Resultado en el artefacto del run; no publica.",
             f"Lote de prueba: {p['prueba']['comunidad']}.", "", "| Comunidad | Elecciones |", "|---|---|"]
    lines += [f"| {r['comunidad']} | {', '.join(r['elecciones'])} |" for r in p["include"]]
    if p["omitidos"]:
        lines += ["", "Omitidos (no soportados todavía):", ""]
        lines += [f"- {t}: {m}" for t, m in p["omitidos"].items()]
    return "\n".join(lines) + "\n"


# --- ejecución en el runner ---------------------------------------------------------------------------------------
def escribir_paquete(carpeta: Path, comunidad: str, ele: str, fecha: str, secciones: dict, fuente: dict) -> dict:
    """Paquete M07 de una autonómica: como `reagregacion_historico.escribir_paquete`, con contrato autonómico."""
    from ddd_core.electoral_contract import party_key
    import equivalencia_seccionados as eqs
    ra = _ra()
    carpeta.mkdir(parents=True, exist_ok=True)
    sv, sp, dic, con = (carpeta / n for n in ("secciones.csv", "participacion.csv", "partidos.json", "contrato.json"))
    with open(sv, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["section_id", "party", "votes"])
        for v in sorted(secciones):
            for p, n in sorted(secciones[v]["votos"].items()):
                w.writerow([v, p, n])
    with open(sp, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["section_id", *ra.rh.CAMPOS])
        for v in sorted(secciones):
            w.writerow([v, *(secciones[v][c] for c in ra.rh.CAMPOS)])
    siglas = sorted({p for r in secciones.values() for p in r["votos"]})
    vistos: dict = {}
    for p in siglas:
        k = party_key(p)
        if k in vistos:
            raise SystemExit(f"SIGLAS_AMBIGUAS {comunidad} {ele} {vistos[k]!r} {p!r}")
        vistos[k] = p
    dic.write_text(json.dumps({"schema_family": "ddd-party-dictionary", "schema_version": "1.0.0",
                               "unknown_party_policy": "reject",
                               "parties": [{"canonical_id": p, "display_name": p} for p in siglas]},
                              ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    contrato = {
        "schema_family": "ddd-election", "schema_version": "1.0.0",
        "election_id": f"{comunidad}_{ele}", "territory_id": comunidad,
        "title": f"Elecciones autonómicas {ele[:4]} ({comunidad}) — histórico reagregado (T-133)",
        "election_date": fecha if len(fecha) == 10 else f"{fecha}-01", "input_mode": "verifiable_file",
        "boundary_independence": True,
        "sources": [{"publisher": "Diputado de Distrito (T-133) sobre el Observatorio Electoral de las Naciones",
                     "source_url": "https://nazioenbehatokia.eus/", "retrieved_at": fecha if len(fecha) == 10 else f"{fecha}-01",
                     "path": str(sv), "sha256": eqs.sha256(sv),
                     "adapter": {"kind": "long_csv", "separator": ",", "section_field": "section_id",
                                 "party_field": "party", "votes_field": "votes"}}],
        "party_dictionary": {"path": str(dic), "sha256": eqs.sha256(dic)},
        "source_verification": {"secondary_source": fuente,
                                "note": "el Observatorio suma secciones y excluye el voto CERA: el hueco frente al total es de la fuente"},
        "reconciliation": {"kind": "accepted_source_ddd_loss_budget"},
    }
    con.write_text(json.dumps(contrato, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return {n.name: eqs.sha256(n) for n in (sv, sp, dic, con)}


def _bajar_verificado(url: str, destino: Path, esperado: str | None, headers: dict | None = None) -> Path:
    import historico_campana as hc
    if esperado is None:
        raise SystemExit(f"SIN_HUELLA {url}")
    return hc._bajar(url, destino, esperado, headers)


def _m06(comunidad: str, destino: Path) -> Path:
    import os
    comp = _json(ROOT, COMPOSICION_MANIFEST)["territorios"][comunidad]
    repo = os.environ.get("GITHUB_REPOSITORY", "jfmurciego/diputadodedistrito")
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    h = {"Accept": "application/vnd.github.raw"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return _bajar_verificado(f"https://api.github.com/repos/{repo}/git/blobs/{comp['blob_sha']}", destino,
                             comp["sha256_m06"], h)


def ejecutar(comunidad: str, trabajo: Path, salida: Path, solo: list[str] | None = None) -> int:
    import subprocess
    import equivalencia_seccionados as eqs
    ra = _ra()
    import fuente_nazioenbehatokia as fnb
    import historico_m07m08 as hm
    falta = requisitos(comunidad)
    if falta:
        raise SystemExit(f"NO_SOPORTADO {comunidad}: {'; '.join(falta)}")
    subprocess.run(["bash", str(ROOT / "inputs/partes/reconstruir_fuentes.sh")], check=True)
    seccionado, padron = ROOT / "inputs/seccionado_2025.zip", ROOT / "inputs/65034.csv.zip"
    els = [e for e in elecciones(comunidad) if not solo or e["eleccion"] in solo]
    manifiestos = {e["eleccion"]: _json(ROOT, f"{B}/{comunidad}/{e['eleccion']}/MANIFEST.json") for e in els}
    m06 = _m06(comunidad, trabajo / f"{comunidad}_m06.zip")
    comp = ra.leer_composicion(comunidad)
    provincias = sorted({s[:2] for s in comp})
    vig_all, pob = eqs.leer_seccionado(seccionado), eqs.leer_padron(padron)
    años = sorted({manifiestos[e["eleccion"]]["seccionado_historico"] for e in els})
    todos = {}
    for y in años:  # huellas de los seccionados históricos: las del MANIFEST del paso B (fuente independiente)
        esperado = next(m["fuentes"]["historicos"].get(str(y)) for m in manifiestos.values()
                        if str(y) in m["fuentes"]["historicos"])
        z = _bajar_verificado(ra.INE.format(y), trabajo / "historicos" / f"seccionado_{y}.zip", esperado)
        todos[y] = eqs.leer_seccionado(z)
    composicion_m07 = hm.leer_composicion(ROOT / f"datos/composicion/{comunidad}.csv")
    secc, asign, _ = hm.secciones_m06(composicion_m07, seccionado, trabajo / "secciones_m06.geojson.zip", m06, pob)
    paquete = trabajo / "paquete"
    informe, ok = {}, True
    for e in els:
        ele, mb = e["eleccion"], manifiestos[e["eleccion"]]
        clave, año = f"{e['cod_ine']}-{ele}", mb["seccionado_historico"]
        votos, huellas, eq = {}, {}, {}
        for c in provincias:
            ruta = f"sekzioa/{clave}/{c}.json"
            f = _bajar_verificado(ra.BASE + ruta, trabajo / "obs" / ruta, mb["fuentes"]["observatorio"].get(ruta))
            huellas[ruta] = eqs.sha256(f)
            v = fnb.leer_provincia(json.loads(f.read_text(encoding="utf-8")))
            por_año = {y: z.get(c, {}) for y, z in todos.items()}
            por_año.setdefault(2025, vig_all[c])
            hist, _ = eqs.completar_geometrias(v, año, por_año)
            dx, dy = eqs.desplazamiento_sistematico(hist, vig_all[c])
            if dx or dy:
                from shapely.affinity import translate
                hist = {k: translate(g, dx, dy) for k, g in hist.items()}
            eq.update(eqs.equivalencia(hist, vig_all[c], pob))
            votos.update(v)
        sec = ra.rh.redondear({"distritos": ra.rh.reagregar_secciones(votos, eq)["distritos"]})
        escribir_paquete(paquete / ele / comunidad, comunidad, ele, e["fecha"], sec,
                         {"observatorio": huellas, "calendario": eqs.sha256(ROOT / CALENDARIO)})
        pq = paquete / ele / comunidad
        tr = trabajo / "m07" / ele
        tr.mkdir(parents=True, exist_ok=True)
        p = hm.params(comunidad, tr, secc, m06, pq / "contrato.json")
        hm.ejecutar("07_agregar_resultados_electorales.py", p)
        hm.ejecutar("08_integrar_resultados.py", p)
        rec = json.loads((tr / "m07_reconciliacion.json").read_text(encoding="utf-8"))
        dest = salida / ele / comunidad
        dest.mkdir(parents=True, exist_ok=True)
        shutil.copy(tr / "m07_resumen_electoral.csv", dest / "resumen_electoral.csv")
        shutil.copy(tr / "m07_resultados_partido.csv", dest / "resultados_partido.csv")
        hm.escribir_participacion(dest / "participacion.csv", hm.participacion(pq / "participacion.csv", asign))
        resumen = hm.leer_resumen(dest / "resumen_electoral.csv")
        cb = _contraste(comunidad, ele, resumen)
        puerta = {"b_ok": bool(mb["cuadre"]["ok"]), "m07": rec.get("status"), "paso_b": cb}
        puerta["estado"] = "PASS" if (puerta["b_ok"] and rec.get("status") in PASS
                                      and not cb.get("ganador_distinto") and "estado" not in cb) else "FAIL"
        informe[ele] = puerta
        ok &= puerta["estado"] == "PASS"
        print(comunidad, ele, json.dumps(puerta, ensure_ascii=False), flush=True)
    res = {"comunidad": comunidad, "estado": "PASS" if ok else "FAIL", "elecciones": informe,
           "m06": eqs.sha256(m06)}
    (salida / f"PUERTA_{comunidad}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
                                                    encoding="utf-8")
    return 0 if ok else 1


def _contraste(comunidad: str, ele: str, resumen: dict) -> dict:
    """Ganador por distrito del paso B versionado frente al de M07 (mismos nombres de sigla de la fuente)."""
    pb = ROOT / B / comunidad / ele / f"{comunidad}.csv"
    if not pb.exists():
        return {"estado": "sin paso B"}
    with open(pb, encoding="utf-8", newline="") as f:
        b = {r["distrito"]: r for r in csv.DictReader(f)}
    dif = {d: int(resumen[d]["total_votes"]) - int(b[d]["votos_candidaturas"]) for d in b if d in resumen}
    return {"distritos_b": len(b), "distritos_m07": len(resumen), "dif_total": sum(dif.values()),
            "dif_max_distrito": max((abs(x) for x in dif.values()), default=0),
            "ganador_distinto": sorted(d for d in b if d in resumen and b[d]["ganador"] != resumen[d]["winner_party"])}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("accion", choices=["ejecutar"])
    ap.add_argument("--comunidad", required=True)
    ap.add_argument("--elecciones", nargs="*", help="limita a estas elecciones AAAAMM (por defecto, todas)")
    ap.add_argument("--trabajo", type=Path, default=ROOT / ".cache/ddd/historico_autonomico")
    ap.add_argument("--salida", type=Path, default=ROOT / "salida_historico")
    a = ap.parse_args(argv)
    a.salida.mkdir(parents=True, exist_ok=True)
    return ejecutar(a.comunidad, a.trabajo / a.comunidad, a.salida, a.elecciones)


if __name__ == "__main__":
    sys.exit(main())
