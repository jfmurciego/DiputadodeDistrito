#!/usr/bin/env python3
"""Métricas del proceso (T-65): 00 a la primera, minutos de Actions, PR y CI, coste de agentes.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.1.1
NOMBRE DE VERSIÓN: Métricas del proceso con paginación completa
FECHA: 2026-11-10
ESTADO: candidato
CAMBIOS 1.1.1: T-215 (corte 5.0.0, paso 4), el run-name de la 00 empieza por «P00 Campaña»; se acepta también el viejo
  («00 Ejecución Completa del Proyecto») para el histórico.
CAMBIOS: runs por ventanas de fechas (bisecta si una ventana llega al tope de 1.000), reintentos con espera en la API,
  minutos de Actions = suma de la duración real de los jobs (caché por run), no el reloj del run (T-161).
MOTIVO: T-155 (#615): con una sola consulta topada a 1.000 daba 5.920 min frente a 46.284 reales (27-10 → 10-11).
ANTERIOR: legacy/herramientas/metricas_proceso_v1.1.0_20261110.py
QUÉ HACE: con la API REST de GitHub (stdlib; token de GH_TOKEN/GITHUB_TOKEN, o `gh api` si no hay) y los ficheros del
  repo escribe orchestracion/metricas_proceso.json (y un espejo opcional para el dashboard):
  - 00 por territorio: intentos hasta el primer éxito y % que pasan a la primera, por semana. El territorio sale de
    (1) el run-name, (2) territorios/*/evidencia/ejecuciones_completas/<run>.json, (3) la línea `TERRITORY:` del job
    «Planificar» (máximo --max-logs descargas por ejecución; lo resuelto se conserva en `cache`). Cuentan también los
    runs encadenados de github-actions[bot]; cancelados y omitidos no son intentos.
  - minutos de Actions por workflow (reloj de cada run) y por territorio (suma de jobs de cada 00).
  - PR fusionadas por día, horas de PR abierta a fusionada, duración de `pruebas` (run «Pruebas de la Plataforma»).
  - fallos de CI en PR por causa (job y paso fallidos; máximo --max-detalle consultas por ejecución).
  - coste de agentes desde los LIBRO_DE_COSTES*.md (filas de tabla y tokens citados en las notas).
NO HACE: lanzar ni publicar nada; no usa modelos. Solo lee.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import statistics
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "ddd.metricas-proceso/1"
SALIDA = "orchestracion/metricas_proceso.json"
WF_00 = "ejecucion-completa-proyecto.yml"
NOMBRE_PRUEBAS = "Pruebas de la Plataforma"
OBJETIVO_PRIMERA = 60.0
TERMINALES = {"success", "failure", "timed_out", "startup_failure"}
EVENTOS_NO_00 = {"pull_request", "pull_request_target", "push"}
RUN_NAME = re.compile(r"^(?:P00 Campaña|00 Ejecución Completa del Proyecto) · (.+?) · (.+)$")
REINTENTOS = 5
TOPE_SEMANAL_MIN = 15000  # D-46 (propietario): aviso al 70 % y al 100 %, sin corte automático
AVISOS_PCT = (70, 100)
TOPE_CONSULTA = 1000  # la API de runs no devuelve más de 1.000 resultados por consulta filtrada
LINEA_TERRITORIO = re.compile(r"TERRITORY:\s*(.+?)\s*$")


def ts(valor):
    return datetime.fromisoformat(valor.replace("Z", "+00:00")) if valor else None


def semana(valor):
    y, w, _ = ts(valor).isocalendar()
    return f"{y}-W{w:02d}"


def minutos(ini, fin):
    a, b = ts(ini), ts(fin)
    return max(0.0, (b - a).total_seconds() / 60) if a and b else 0.0


def mediana(xs):
    return round(statistics.median(xs), 2) if xs else None


def p90(xs):
    if not xs:
        return None
    xs = sorted(xs)
    return round(xs[min(len(xs) - 1, int(0.9 * len(xs)))], 2)


# ---------------------------------------------------------------- cliente REST
class Cliente:
    """GET sobre la API REST. `get` devuelve JSON; `texto` sigue la redirección de los logs sin reenviar el token."""

    def __init__(self, repo, token=None):
        self.repo = repo
        self.token = token or os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")

    def _url(self, ruta, params):
        q = ("?" + urllib.parse.urlencode(params)) if params else ""
        return f"https://api.github.com/repos/{self.repo}/{ruta}{q}"

    def _cab(self):
        h = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "ddd-metricas"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def get(self, ruta, params=None):
        """GET con reintentos y espera exponencial (la API resetea conexiones en lotes largos, y limita en 403/429/5xx)."""
        for intento in range(REINTENTOS):
            try:
                if not self.token:
                    out = subprocess.run(["gh", "api", f"repos/{self.repo}/{ruta}", "-X", "GET",
                                          *sum((["-f", f"{k}={v}"] for k, v in (params or {}).items()), [])],
                                         capture_output=True, text=True, check=True)
                    return json.loads(out.stdout)
                with urllib.request.urlopen(urllib.request.Request(self._url(ruta, params), headers=self._cab()), timeout=60) as r:
                    return json.load(r)
            except urllib.error.HTTPError as e:
                if e.code not in (403, 429, 500, 502, 503, 504) or intento == REINTENTOS - 1:
                    raise
            except (OSError, subprocess.CalledProcessError, ValueError):
                if intento == REINTENTOS - 1:
                    raise
            time.sleep(2 ** (intento + 1))

    def texto(self, ruta):
        if not self.token:
            return subprocess.run(["gh", "api", f"repos/{self.repo}/{ruta}"], capture_output=True, text=True, check=True).stdout

        class _Sin(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *a, **k):
                return None

        op = urllib.request.build_opener(_Sin)
        try:
            op.open(urllib.request.Request(self._url(ruta, None), headers=self._cab()), timeout=60)
        except urllib.error.HTTPError as e:
            if e.code not in (301, 302, 303, 307, 308):
                raise
            with urllib.request.urlopen(e.headers["Location"], timeout=120) as r:
                return r.read().decode("utf-8", "replace")
        return ""


def paginar(api, ruta, params, clave, parar=None, max_paginas=60):
    """Lista todas las páginas; `parar(item)` True corta (listas ordenadas por fecha)."""
    out = []
    for pagina in range(1, max_paginas + 1):
        datos = api.get(ruta, {**params, "per_page": 100, "page": pagina})
        items = datos[clave] if clave else datos
        for it in items:
            if parar and parar(it):
                return out
            out.append(it)
        if len(items) < 100:
            break
    return out


def _iso(d):
    return d.strftime("%Y-%m-%dT%H:%M:%SZ")


def runs_por_ventanas(api, desde, hasta, horas=6, params=None):
    """Todos los runs creados en [desde, hasta]: ventanas de `horas`; si una llega al tope de la API se parte por la mitad."""
    vistos = {}

    def ventana(a, b):
        items = paginar(api, "actions/runs", {**(params or {}), "created": f"{_iso(a)}..{_iso(b)}"}, "workflow_runs")
        if len(items) >= TOPE_CONSULTA and (b - a) > timedelta(seconds=1):
            m = a + (b - a) / 2
            ventana(a, m.replace(microsecond=0))
            ventana(m.replace(microsecond=0) + timedelta(seconds=1), b)
            return
        if len(items) >= TOPE_CONSULTA:
            print(f"AVISO: ≥{TOPE_CONSULTA} runs en un solo segundo ({_iso(a)}); resultado incompleto", file=sys.stderr)
        for it in items:
            vistos[it["id"]] = it

    paso = timedelta(hours=horas)
    a = desde
    while a < hasta:
        b = min(a + paso, hasta)
        ventana(a, b)
        a = b + timedelta(seconds=1)
    return list(vistos.values())


# ------------------------------------------------------------------- territorio
def cargar_evidencia(raiz):
    """run_id -> territory_id y nombre -> id, desde las evidencias de ejecución completa."""
    por_run, por_nombre = {}, {}
    for f in glob.glob(str(Path(raiz) / "territorios/*/evidencia/ejecuciones_completas/*.json")):
        try:
            d = json.loads(Path(f).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        tid = d.get("territory_id")
        if not tid:
            continue
        if d.get("workflow_run_id"):
            por_run[str(d["workflow_run_id"])] = tid
        if d.get("territory_name"):
            por_nombre[d["territory_name"]] = tid
    return por_run, por_nombre


def territorio_de_log(api, run_id):
    jobs = api.get(f"actions/runs/{run_id}/jobs", {"per_page": 100})["jobs"]
    plan = next((j for j in jobs if j["name"].startswith("Planificar")), None)
    if not plan:
        return None
    for linea in api.texto(f"actions/jobs/{plan['id']}/logs").splitlines():
        m = LINEA_TERRITORIO.search(linea)
        if m:
            return m.group(1)
    return None


def resolver_territorios(api, runs_00, evidencia, cache, max_logs):
    por_run, por_nombre = evidencia
    res, descargas = {}, 0
    for r in sorted(runs_00, key=lambda x: x["created_at"], reverse=True):
        rid = str(r["id"])
        m = RUN_NAME.match(r.get("display_title") or "")
        if m:
            t = m.group(1)
        elif rid in por_run:
            t = por_run[rid]
        elif rid in cache:
            t = cache[rid]
        elif descargas < max_logs:
            descargas += 1
            try:
                t = territorio_de_log(api, rid)
            except (OSError, subprocess.CalledProcessError, KeyError, ValueError):
                t = None
            if t:
                t = por_nombre.get(t, t)
                cache[rid] = t
        else:
            t = None
        res[rid] = por_nombre.get(t, t) if t else None
    return res


# ---------------------------------------------------------------------- cálculos
def calcular_00(runs_00, territorios):
    """Intentos hasta el primer éxito por territorio y % a la primera por semana."""
    por_t = defaultdict(list)
    cancelados = sin_territorio = 0
    por_actor = defaultdict(int)
    for r in sorted(runs_00, key=lambda x: x["created_at"]):
        if r.get("conclusion") not in TERMINALES:
            cancelados += 1
            continue
        por_actor[(r.get("actor") or {}).get("login", "?")] += 1
        t = territorios.get(str(r["id"]))
        if not t:
            sin_territorio += 1
            continue
        por_t[t].append(r)
    filas, semanas = [], defaultdict(lambda: {"territorios": 0, "primera": 0, "runs": 0, "runs_ok": 0})
    for t, rs in sorted(por_t.items()):
        ok = next((i for i, r in enumerate(rs) if r["conclusion"] == "success"), None)
        s = semana(rs[0]["created_at"])
        filas.append({"territorio": t, "semana_inicio": s, "runs": len(rs),
                      "intentos_hasta_exito": None if ok is None else ok + 1,
                      "a_la_primera": ok == 0, "con_exito": ok is not None})
        semanas[s]["territorios"] += 1
        semanas[s]["primera"] += int(ok == 0)
        for r in rs:
            sr = semana(r["created_at"])
            semanas[sr]["runs"] += 1
            semanas[sr]["runs_ok"] += int(r["conclusion"] == "success")
    por_semana = [{"semana": s, **v,
                   "pct_a_la_primera": round(100 * v["primera"] / v["territorios"], 1) if v["territorios"] else None,
                   "pct_runs_ok": round(100 * v["runs_ok"] / v["runs"], 1) if v["runs"] else None}
                  for s, v in sorted(semanas.items())]
    n = len(filas)
    con_exito = [f for f in filas if f["con_exito"]]
    return {
        "objetivo_pct_a_la_primera": OBJETIVO_PRIMERA,
        "territorios": n,
        "con_exito": len(con_exito),
        "a_la_primera": sum(f["a_la_primera"] for f in filas),
        "pct_a_la_primera": round(100 * sum(f["a_la_primera"] for f in filas) / n, 1) if n else None,
        "intentos_medianos_hasta_exito": mediana([f["intentos_hasta_exito"] for f in con_exito]),
        "runs_cancelados_u_omitidos": cancelados,
        "runs_sin_territorio": sin_territorio,
        "runs_por_actor": dict(sorted(por_actor.items())),
        "por_semana": por_semana,
        "por_territorio": filas,
    }


def minutos_de_jobs(api, rid, cache_min):
    """Duración real: suma de (completed_at - started_at) de todos los jobs del run (el /timing da 0 en repo público)."""
    if rid not in cache_min:
        jobs = paginar(api, f"actions/runs/{rid}/jobs", {"filter": "all"}, "jobs")
        cache_min[rid] = round(sum(minutos(j.get("started_at"), j.get("completed_at")) for j in jobs), 3) if jobs else None
    return cache_min[rid]


def minutos_de_runs(api, runs, cache_min, max_detalle):
    """run_id -> minutos. Jobs reales (con caché); sin jobs o pasado el tope de consultas, reloj del run. Devuelve (minutos, nº reloj)."""
    res, consultas, reloj = {}, 0, 0
    for r in sorted(runs, key=lambda x: x["created_at"], reverse=True):
        if r.get("conclusion") is None:
            continue
        rid = str(r["id"])
        m = cache_min.get(rid)
        if rid not in cache_min and consultas < max_detalle:
            consultas += 1
            try:
                m = minutos_de_jobs(api, rid, cache_min)
            except (OSError, subprocess.CalledProcessError, KeyError, ValueError):
                m = None
        if m is None:
            reloj += 1
            m = minutos(r.get("run_started_at") or r.get("created_at"), r.get("updated_at"))
        res[rid] = m
    return res, reloj


def minutos_por_workflow(runs, por_run=None):
    acc = defaultdict(lambda: {"runs": 0, "minutos": 0.0})
    for r in runs:
        if r.get("conclusion") is None:
            continue
        a = acc[r.get("name") or r.get("path") or "?"]
        a["runs"] += 1
        a["minutos"] += (por_run or {}).get(str(r["id"])) if por_run and str(r["id"]) in por_run else \
            minutos(r.get("run_started_at") or r.get("created_at"), r.get("updated_at"))
    filas = [{"workflow": k, "runs": v["runs"], "minutos": round(v["minutos"], 1)} for k, v in acc.items()]
    return sorted(filas, key=lambda f: -f["minutos"])


def gasto_semanal(runs, por_run, tope=TOPE_SEMANAL_MIN):
    """Minutos de jobs por semana ISO (fecha de creación del run) frente al tope; `aviso` = mayor umbral cruzado (70/100) o None."""
    acc = defaultdict(float)
    for r in runs:
        if str(r["id"]) in por_run:
            acc[semana(r["created_at"])] += por_run[str(r["id"])]
    filas = []
    for sem, m in sorted(acc.items()):
        pct = 100 * m / tope
        cruzados = [u for u in AVISOS_PCT if pct >= u]
        filas.append({"semana": sem, "minutos": round(m, 1), "pct_tope": round(pct, 1), "aviso": max(cruzados) if cruzados else None})
    return {"tope_minutos": tope, "avisos_pct": list(AVISOS_PCT), "corte_automatico": False, "por_semana": filas,
            "aviso_semana_actual": filas[-1]["aviso"] if filas else None}


def minutos_por_territorio(runs_00, territorios, por_run):
    acc = defaultdict(float)
    for r in runs_00:
        rid = str(r["id"])
        if rid in por_run:
            acc[territorios.get(rid) or "(sin territorio)"] += por_run[rid]
    return sorted(({"territorio": t, "minutos": round(m, 1)} for t, m in acc.items()), key=lambda f: -f["minutos"])


def calcular_prs(prs, desde):
    fusionadas = [p for p in prs if p.get("merged_at") and ts(p["merged_at"]) >= desde]
    por_dia = defaultdict(int)
    horas = []
    for p in fusionadas:
        por_dia[p["merged_at"][:10]] += 1
        horas.append(minutos(p["created_at"], p["merged_at"]) / 60)
    return {"fusionadas": len(fusionadas), "fusionadas_por_dia": dict(sorted(por_dia.items())),
            "horas_abierta_mediana": mediana(horas), "horas_abierta_p90": p90(horas)}


def calcular_pruebas(runs):
    ok = [minutos(r.get("run_started_at") or r["created_at"], r["updated_at"]) for r in runs
          if r.get("name") == NOMBRE_PRUEBAS and r.get("event") == "pull_request" and r.get("conclusion") == "success"]
    return {"runs_ok": len(ok), "minutos_mediana": mediana(ok), "minutos_p90": p90(ok)}


def causa_de_jobs(jobs):
    for j in jobs:
        if j.get("conclusion") == "failure":
            paso = next((s["name"] for s in j.get("steps") or [] if s.get("conclusion") == "failure"), "(sin paso)")
            return f"{j['name']} · {paso}"
    return "(sin job fallido)"


def fallos_ci(api, runs, cache_causas, max_detalle):
    fallidos = [r for r in runs if r.get("event") == "pull_request" and r.get("conclusion") == "failure"]
    consultas, cuenta = 0, defaultdict(int)
    for r in sorted(fallidos, key=lambda x: x["created_at"], reverse=True):
        rid = str(r["id"])
        if rid not in cache_causas:
            if consultas >= max_detalle:
                cuenta["(sin clasificar)"] += 1
                continue
            consultas += 1
            try:
                cache_causas[rid] = f"{r.get('name', '?')} / " + causa_de_jobs(api.get(f"actions/runs/{rid}/jobs", {"per_page": 100})["jobs"])
            except (OSError, subprocess.CalledProcessError, KeyError, ValueError):
                cuenta["(sin clasificar)"] += 1
                continue
        cuenta[cache_causas[rid]] += 1
    return {"total": len(fallidos), "por_causa": dict(sorted(cuenta.items(), key=lambda kv: -kv[1]))}


NUM = r"(\d[\d.,]*)"


def a_entero(s):
    return int(re.sub(r"[.,]", "", s))


def leer_costes(raiz):
    filas, notas = [], []
    for f in sorted(glob.glob(str(Path(raiz) / "**/LIBRO_DE_COSTES*.md"), recursive=True)):
        rel = str(Path(f).relative_to(raiz))
        if rel.startswith("legacy/"):
            continue
        for linea in Path(f).read_text(encoding="utf-8").splitlines():
            if linea.startswith("|"):
                c = [x.strip() for x in linea.strip().strip("|").split("|")]
                if len(c) >= 9 and re.match(r"\d{4}-\d{2}-\d{2}", c[0]):
                    filas.append({"fecha": c[0], "agente": c[1], "modelo": c[2], "etiqueta": c[3], "casos": c[4],
                                  "tokens": a_entero(c[7]) if re.fullmatch(NUM, c[7]) else 0, "a_la_primera": c[8]})
            else:
                m = re.match(r"- (\d{4}-\d{2}-\d{2}) · ([^·]+) · ", linea)
                t = re.search(NUM + r" tokens", linea)
                if m and t:
                    notas.append({"fecha": m.group(1), "agente": m.group(2).strip(), "tokens": a_entero(t.group(1)), "fuente": rel})
    return {"filas_tabla": filas, "notas_con_tokens": notas,
            "tokens_total": sum(f["tokens"] for f in filas) + sum(n["tokens"] for n in notas),
            "nota": "tokens de la tabla + primera cifra «N tokens» de cada nota; aproximado"}


# ------------------------------------------------------------------------ main
def generar(api, raiz, dias, max_logs, max_detalle, ahora=None, previo=None, ventana_horas=6):
    ahora = ahora or datetime.now(timezone.utc)
    desde = ahora - timedelta(days=dias)
    cache = (previo or {}).get("cache", {})
    c_terr, c_min, c_causas = (dict(cache.get(k, {})) for k in ("territorio_por_run", "minutos_por_run", "causa_por_run"))
    runs = runs_por_ventanas(api, desde, ahora, ventana_horas, {"status": "completed"})
    runs_00 = [r for r in runs if (r.get("path") or "").endswith(WF_00) and r.get("event") not in EVENTOS_NO_00]
    terr = resolver_territorios(api, runs_00, cargar_evidencia(raiz), c_terr, max_logs)
    p00 = calcular_00(runs_00, terr)
    min_run, runs_reloj = minutos_de_runs(api, runs, c_min, max_detalle)
    por_terr = minutos_por_territorio(runs_00, terr, min_run)
    prs = paginar(api, "pulls", {"state": "closed", "sort": "updated", "direction": "desc"}, None,
                  parar=lambda p: ts(p["updated_at"]) < desde)
    costes = leer_costes(raiz)
    por_wf = minutos_por_workflow(runs, min_run)
    min_total = round(sum(f["minutos"] for f in por_wf), 1)
    cerradas = p00["con_exito"]
    vivos = {str(r["id"]) for r in runs}
    return {
        "schema": SCHEMA,
        "generado": ahora.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "repo": api.repo, "ventana": {"desde": desde.strftime("%Y-%m-%d"), "dias": dias},
        "ejecuciones_00": p00,
        "minutos_actions": {"total": min_total, "runs": len(min_run), "runs_con_reloj_en_vez_de_jobs": runs_reloj,
                            "por_workflow": por_wf, "por_territorio_00": por_terr,
                            "gasto_semanal": gasto_semanal(runs, min_run)},
        "pr": {**calcular_prs(prs, desde), "pruebas": calcular_pruebas(runs)},
        "fallos_ci_pr": fallos_ci(api, runs, c_causas, max_detalle),
        "coste_agentes": costes,
        "coste_por_territorio_cerrado": {
            "territorios_con_exito_00": cerradas,
            "minutos_actions_por_territorio": round(min_total / cerradas, 1) if cerradas else None,
            "tokens_agentes_por_territorio": round(costes["tokens_total"] / cerradas) if cerradas else None},
        "cache": {"territorio_por_run": {k: v for k, v in c_terr.items() if k in vivos},
                  "minutos_por_run": {k: v for k, v in c_min.items() if k in vivos},
                  "causa_por_run": {k: v for k, v in c_causas.items() if k in vivos}},
    }


def sin_fecha(d):
    return {k: v for k, v in d.items() if k != "generado"}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", "jfmurciego/diputadodedistrito"))
    ap.add_argument("--dias", type=int, default=42)
    ap.add_argument("--max-logs", type=int, default=40, help="descargas de log de «Planificar» por ejecución")
    ap.add_argument("--max-detalle", type=int, default=1500, help="consultas de jobs por ejecución (minutos y causas de CI)")
    ap.add_argument("--ventana-horas", type=int, default=6, help="tamaño de las ventanas de fechas (tope de 1.000 por consulta)")
    ap.add_argument("--salida", default=SALIDA)
    ap.add_argument("--espejo", help="copia adicional para el dashboard (p. ej. dashboard/metricas_proceso.json)")
    a = ap.parse_args(argv)
    out = ROOT / a.salida
    previo = json.loads(out.read_text(encoding="utf-8")) if out.exists() else None
    datos = generar(Cliente(a.repo), ROOT, a.dias, a.max_logs, a.max_detalle, previo=previo, ventana_horas=a.ventana_horas)
    if previo and sin_fecha(previo) == sin_fecha(datos):
        datos["generado"] = previo["generado"]
    texto = json.dumps(datos, ensure_ascii=False, indent=1, sort_keys=False) + "\n"
    for destino in filter(None, [a.salida, a.espejo]):
        p = ROOT / destino
        p.parent.mkdir(parents=True, exist_ok=True)
        if not p.exists() or p.read_text(encoding="utf-8") != texto:
            p.write_text(texto, encoding="utf-8")
    p0 = datos["ejecuciones_00"]
    print(f"00: {p0['territorios']} territorios, {p0['pct_a_la_primera']} % a la primera (objetivo {OBJETIVO_PRIMERA}); "
          f"minutos Actions {datos['minutos_actions']['total']}; PR fusionadas {datos['pr']['fusionadas']}; "
          f"fallos CI en PR {datos['fallos_ci_pr']['total']}; tokens agentes {datos['coste_agentes']['tokens_total']}")
    g = datos["minutos_actions"]["gasto_semanal"]
    if g["por_semana"]:
        u = g["por_semana"][-1]
        marca = f" · AVISO {u['aviso']} % del tope" if u["aviso"] else ""
        print(f"Gasto {u['semana']}: {u['minutos']} de {g['tope_minutos']} min ({u['pct_tope']} %){marca}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
