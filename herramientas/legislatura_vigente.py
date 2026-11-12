#!/usr/bin/env python3
"""Legislatura vigente: configuración, plan y lanzamiento por ámbito del Gestor de Campañas.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.2.4 · FECHA: 2026-11-12 · ESTADO: candidato
CAMBIOS 1.2.3: T-215 (corte 5.0.0, paso 4), la 00 se llama «P00 Campaña»: TITLE_00 nuevo; los runs en curso con el
  título viejo («00 Ejecución Completa del Proyecto · …») siguen contando como en curso y `Campaign.poll` los sigue.
CAMBIOS 1.2.2: T-201, `territory_state(..., eleccion)`: el M08 publicado cuenta por (territorio, elección), por defecto 2023-07-23; un M08
  de otra elección no marca PUBLICADO ni pisa el run; tampoco su M06 marca TERRITORIAL_CERTIFICADO.
CAMBIOS 1.2.1: T-130, el Gestor da por resultado de la 00 el de la que lanzó él (la primera, p. ej. la de prueba), no el de la
  hija «Reutilizar» que encadena el bot (run 42637133308: seguía la 42651881625 en vez de la 42637193077). Una hija
  fallida solo cuenta si hay que publicar (el eslabón electoral es el que se publica).
CAMBIOS 1.2.0: T-105 (Gestor 2.0, D-22): `build_plan` admite inicio (reutilizar/aprovechar fuentes/desde el principio),
  publicar sí/no por fila y ensemble de 10 (06 `ensemble_10`) tras la publicación; una sola 06 del Gestor a la vez;
  el relevo `continuar` pasa las entradas 2.0 y marca con «@auto» los territorios ya iniciados (no se rehacen).
CAMBIOS 1.1.0: T-102, ámbito «congreso 350» (49 gemelos `congreso350_*`, K = escaños reales de 2023);
  «legislatura completa» y «nacional» no los incluyen salvo que se pidan por territory_id (relevo `continuar`).
  Los gemelos nunca publican (D-18): 00 con publish_result=false y sin 05; «COMPLETO_SIN_PUBLICAR» → `nada`.
CAMBIOS 1.2.4 (T-220): ids de territorio nuevos de la tabla maestra (aut01…nac52, D-61); el id viejo se lee vía ddd_core.territorio_ids.
ANTERIOR: legacy/herramientas/legislatura_vigente_v1.2.3_20261112.py
QUÉ HACE: T-86.
  - `generar` escribe `configuracion/legislatura_vigente.yaml` desde los ficheros con fuente del repo
    (registro electoral, preparación de la legislatura y escaños oficiales del BOE), con su sha256; nada de memoria.
    `--comprobar` falla si el fichero versionado no coincide con lo generado.
  - `plan` lista, por ámbito, los territorios con su clave T-03, estado actual y acción: `nada` (M08 publicado),
    `publicar` (00 completa sin publicar), `reutilizar`, `desde_el_principio` o `esperar` (00 en curso).
  - `lanzar` ejecuta un plan: primero un territorio de prueba si el lote es > 1, después el resto con concurrencia
    limitada; por territorio 00 (con el encadenado par → 00 electoral de la propia 00) → 05 del run final (D-3).
    Si se acerca al límite del job, se relanza a sí mismo en modo `continuar` (bot, sin segundo clic).
NO HACE: aprobar el entorno `produccion` (el clic es del propietario, una vez por campaña) ni reintentar fallos.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import clave_eleccion as ce  # noqa: E402
import resultados_ligeros as rl  # noqa: E402
import sys as _sys_t220  # noqa: E402
from pathlib import Path as _Path_t220  # noqa: E402
if str(_Path_t220(__file__).resolve().parents[1]) not in _sys_t220.path:
    _sys_t220.path.insert(0, str(_Path_t220(__file__).resolve().parents[1]))
from ddd_core.territorio_ids import mismo_territorio, carpeta_de  # noqa: E402  (T-220: id viejo o nuevo)

CONFIG = Path("configuracion/legislatura_vigente.yaml")
REGISTRY = Path("configuracion/registro_electoral.yaml")
PREPARATION = Path("configuracion/preparacion_legislatura_vigente.yaml")
SEATS_2023 = Path("configuracion/resultados_oficiales_congreso_2023.json")
VIEWER = Path("orchestracion/publicaciones_visor.json")
WF_00 = "ejecucion-completa-proyecto.yml"
WF_05 = "desplegar-visor-publico.yml"
WF_GESTOR = "gestor-campanas.yml"
WF_06 = "generar-alternativas-territoriales.yml"
ARTIFACT_DAYS = 12  # margen bajo los 14 días de los artefactos M06/M08 de la 00
TITLE_00 = "P00 Campaña"
TITLES_00 = (TITLE_00, "00 Ejecución Completa del Proyecto")  # T-215: el viejo, para runs anteriores al corte
AMBITOS = ["legislatura completa", "nacional", "autonómicas", "comunidad", "provincias", "congreso 350"]
VARIANT = "congreso_350"
MODES = {
    "reutilizar": "Reutilizar progreso existente",
    "desde_el_principio": "Ejecutar desde el principio",
    "aprovechar_fuentes": "Generar desde fuente territorial acreditada",
}
INICIOS = ("auto", "aprovechar_fuentes", "desde_el_principio")


class GestorError(ValueError):
    pass


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# --------------------------------------------------------------------------- configuración

def build_config(root: Path = Path(".")) -> dict:
    """Legislatura vigente derivada solo de ficheros con fuente del repositorio."""
    units = ce.load_units(root)
    errors = ce.validate(units)
    if errors:
        raise GestorError("; ".join(errors))
    prep = {str(t["territory_id"]): t for t in (yaml.safe_load((root / PREPARATION).read_text(encoding="utf-8"))
                                                  or {}).get("territories") or []}
    seats = json.loads((root / SEATS_2023).read_text(encoding="utf-8"))
    territories = []
    for u in sorted(units, key=lambda u: (u["scope"] != "NAC", u["code"])):
        p = prep.get(u["territory_id"]) or {}
        source = str((p.get("electoral") or {}).get("source") or "").strip()
        if p and str(p.get("election_date")) != u["election_date"]:
            raise GestorError(f"Fecha distinta en registro y preparación: {u['territory_id']}")
        territories.append({
            "territory_id": u["territory_id"],
            "ambito": VARIANT if u.get("variant") == VARIANT else "nacional" if u["scope"] == "NAC" else "autonómica",
            "codigo": u["code"], "nombre": u["name"], "selector_00": u["dispatch_name"],
            "election_id": u["election_id"], "fecha": u["election_date"], "clave": u["key"],
            "fuente_resultados": source or "sin fuente",
        })
    nac_dates = sorted({t["fecha"] for t in territories if t["ambito"] == "nacional"})
    return {
        "schema": "ddd-legislatura-vigente/1.0",
        "generado_por": "herramientas/legislatura_vigente.py generar",
        "fuentes": {
            str(REGISTRY): _sha(root / REGISTRY),
            str(PREPARATION): _sha(root / PREPARATION),
            str(SEATS_2023): _sha(root / SEATS_2023),
        },
        "nacional": {
            "fechas": nac_dates, "claves": [f"ES-NAC-{d.replace('-', '')}" for d in nac_dates],
            "escanos_oficiales": {"boe": seats.get("boe"), "fichero": "configuracion/resultados_oficiales_congreso_2023.csv",
                                  "sha256": seats.get("sha256_csv")},
        },
        "totales": {"nacional": sum(t["ambito"] == "nacional" for t in territories),
                    "autonómica": sum(t["ambito"] == "autonómica" for t in territories),
                    VARIANT: sum(t["ambito"] == VARIANT for t in territories),
                    "total": len(territories)},
        "territorios": territories,
    }


def dump_config(cfg: dict) -> str:
    head = ("# PROYECTO: Diputado de Distrito\n# FICHERO: legislatura_vigente.yaml (GENERADO, no editar a mano)\n"
            "# QUÉ ES: elección vigente de cada territorio (Congreso por provincia y autonómicas) para el Gestor de\n"
            "#   Campañas (T-86). Se regenera con `python herramientas/legislatura_vigente.py generar`; la CI comprueba\n"
            "#   que coincide con las fuentes (sha256 en `fuentes`).\n")
    return head + yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False, width=200)


def load_config(root: Path = Path(".")) -> dict:
    return yaml.safe_load((root / CONFIG).read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- selección y estado

def select(cfg: dict, ambito: str, tokens: list[str]) -> list[dict]:
    rows = cfg["territorios"]
    if ambito not in AMBITOS:
        raise GestorError(f"Ámbito desconocido: {ambito}")
    if ambito == "legislatura completa" and not tokens:
        rows = [r for r in rows if r["ambito"] != VARIANT]
    elif ambito == "nacional":
        rows = [r for r in rows if r["ambito"] == "nacional"]
    elif ambito == "congreso 350":
        rows = [r for r in rows if r["ambito"] == VARIANT]
    elif ambito in ("autonómicas", "comunidad"):
        rows = [r for r in rows if r["ambito"] == "autonómica"]
    elif ambito == "provincias":
        rows = [r for r in rows if r["ambito"] == "nacional"]
    if ambito in ("comunidad", "provincias") and not tokens:
        raise GestorError(f"El ámbito «{ambito}» necesita territorios")
    if ambito == "comunidad" and len(tokens) != 1:
        raise GestorError("El ámbito «comunidad» admite una sola comunidad")
    if not tokens:
        return rows
    units = {u["territory_id"]: u for u in ce.load_units()}

    def hit(r: dict, t: str) -> bool:
        if t == r["territory_id"]:
            return True
        if ambito == "congreso 350":
            # «Soria», «42» o «congreso350_soria»: la provincia del gemelo.
            n = ce.normalize(t)
            return n in {r["codigo"][1:], ce.normalize(r["nombre"]).removeprefix("CONGRESO-350-")} or \
                (n.isdigit() and n.zfill(2) == r["codigo"][1:])
        return ambito in ("comunidad", "provincias") and ce._matches_filter(units[r["territory_id"]], t)

    unknown = [t for t in tokens if not any(hit(r, t) for r in rows)]
    if unknown:
        raise GestorError(f"Fuera del ámbito «{ambito}»: {', '.join(unknown)}")
    return [r for r in rows if any(hit(r, t) for t in tokens)]


def territory_state(root: Path, tid: str, viewer: dict, today, eleccion: str = rl.ELECCION_POR_DEFECTO) -> dict:
    """Estado según el repo: M08 publicado, 00 completa sin publicar, producto territorial o nada."""
    m08 = [p for p in viewer.get("products") or [] if mismo_territorio(str(p.get("territory_id") or ""), str(tid)) and p.get("kind") == "canonical_m08"
           and rl.eleccion_de(p) == eleccion]
    if m08:
        return {"estado": "PUBLICADO", "run_id": str(max(m08, key=lambda p: int(p.get("run_id") or 0)).get("run_id"))}
    manifests = []
    for f in (root / "territorios" / carpeta_de(root, tid) / "evidencia" / "ejecuciones_completas").glob("*.json"):
        try:
            manifests.append(json.loads(f.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            continue
    manifests.sort(key=lambda m: int(m.get("workflow_run_id") or 0))
    complete = [m for m in manifests if m.get("status") == "SUCCESS" and m.get("electoral_status") == "COMPLETE"]
    if complete:
        last = complete[-1]
        try:
            age = (today - datetime.fromisoformat(str(last.get("generated_at"))[:10]).date()).days
        except ValueError:
            age = ARTIFACT_DAYS + 1
        # Con los artefactos de la 00 caducados, la 05 no puede promover el run: se rehace con «Reutilizar».
        return {"estado": "COMPLETO_SIN_PUBLICAR" if age <= ARTIFACT_DAYS else "COMPLETO_CADUCADO",
                "run_id": str(last["workflow_run_id"])}
    m06 = any(mismo_territorio(str(p.get("territory_id") or ""), str(tid)) and p.get("kind") == "canonical_m06"
                and rl.eleccion_de(p) == eleccion for p in viewer.get("products") or [])
    if m06 or any(str(m.get("territorial_status") or "").startswith("CERTIFIED") for m in manifests):
        return {"estado": "TERRITORIAL_CERTIFICADO", "run_id": ""}
    return {"estado": "SIN_PRODUCTO", "run_id": ""}


def build_plan(cfg: dict, ambito: str, tokens: list[str], forzar: bool, running: dict[str, str],
               root: Path = Path("."), today=None, inicio: str | dict = "auto", publicar: bool | None = None,
               ensemble: dict[str, str] | None = None) -> dict:
    """`inicio`: uno de INICIOS, o un dict territory_id → inicio (relevo); `publicar=None` = por ámbito (D-18);
    `ensemble`: territory_id → configuración de `configuracion/ensemble/` (06 `ensemble_10` tras publicar)."""
    viewer = json.loads((root / VIEWER).read_text(encoding="utf-8")) if (root / VIEWER).is_file() else {}
    rows = []
    for r in select(cfg, ambito, tokens):
        st = territory_state(root, r["territory_id"], viewer, today or datetime.now(timezone.utc).date())
        modo = inicio.get(r["territory_id"], "auto") if isinstance(inicio, dict) else inicio
        if forzar:
            modo = "desde_el_principio"
        if modo not in INICIOS:
            raise GestorError(f"Inicio desconocido: {modo}")
        publica = (r["ambito"] != VARIANT) if publicar is None else bool(publicar)
        if r["selector_00"] in running:
            st = {"estado": "EN_CURSO", "run_id": running[r["selector_00"]]}
            accion = "esperar"
        elif modo != "auto":
            accion = modo
        else:
            accion = {"PUBLICADO": "nada",
                      "COMPLETO_SIN_PUBLICAR": "publicar" if publica else "nada",
                      "COMPLETO_CADUCADO": "reutilizar",
                      "TERRITORIAL_CERTIFICADO": "reutilizar", "SIN_PRODUCTO": "desde_el_principio"}[st["estado"]]
        rows.append({**{k: r[k] for k in ("territory_id", "nombre", "ambito", "selector_00", "clave", "fecha")},
                     "estado": st["estado"], "run_id": st["run_id"], "accion": accion, "publicar": publica,
                     "ensemble": (ensemble or {}).get(r["territory_id"], "")})
    counts = {}
    for row in rows:
        counts[row["accion"]] = counts.get(row["accion"], 0) + 1
    return {"ambito": ambito, "forzar": forzar, "count": len(rows), "acciones": counts, "territorios": rows}


def plan_markdown(plan: dict) -> str:
    acc = ", ".join(f"{k} {v}" for k, v in sorted(plan["acciones"].items()))
    out = [f"### Gestor · plan · {plan['ambito']} · {plan['count']} territorios ({acc})", "",
           "| # | Clave | Territorio | Estado | Run | Acción | Publicar | Ensemble |", "|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(plan["territorios"], 1):
        pub = "sí" if r.get("publicar", r.get("ambito") != VARIANT) else "no"
        out.append(f"| {i} | {r['clave']} | {r['selector_00']} | {r['estado']} | {r['run_id']} | {r['accion']} | {pub} "
                   f"| {r.get('ensemble') or '—'} |")
    return "\n".join(out) + "\n"


# --------------------------------------------------------------------------- GitHub (gh api)

def _gh(*args: str) -> str:
    for attempt in range(5):
        p = subprocess.run(["gh", "api", *args], capture_output=True, text=True)
        if p.returncode == 0:
            return p.stdout
        time.sleep(2 ** (attempt + 1))
    raise GestorError(f"gh api {' '.join(args)}: {p.stderr.strip()}")


def _repo() -> str:
    return os.environ["GITHUB_REPOSITORY"]


def list_runs(workflow: str, since: str = "", status: str = "") -> list[dict]:
    q = "per_page=100"
    if since:
        q += f"&created=%3E%3D{since}"
    if status:
        q += f"&status={status}"
    return json.loads(_gh(f"repos/{_repo()}/actions/workflows/{workflow}/runs?{q}")).get("workflow_runs") or []


def running_00() -> dict[str, str]:
    """Selector del 00 → run en cola o en curso, por el run-name «00 … · <territorio> · <modo>»."""
    out = {}
    for status in ("queued", "in_progress", "waiting", "pending", "requested"):
        for run in list_runs(WF_00, status=status):
            parts = str(run.get("display_title") or "").split(" · ")
            if len(parts) >= 3 and parts[0] in TITLES_00:
                out.setdefault(parts[1], str(run["id"]))
    return out


def dispatch(workflow: str, inputs: dict) -> None:
    args = ["-X", "POST", f"repos/{_repo()}/actions/workflows/{workflow}/dispatches", "-f", "ref=main"]
    for k, v in inputs.items():
        args += ["-F" if isinstance(v, bool) else "-f", f"inputs[{k}]={str(v).lower() if isinstance(v, bool) else v}"]
    _gh(*args)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# --------------------------------------------------------------------------- lanzamiento

class Territorio:
    """Máquina de estados de un territorio: 00 (y su cadena) → 05 del run final."""

    def __init__(self, row: dict, algorithm: str, log):
        self.row, self.algorithm, self.log = row, algorithm, log
        self.fase, self.since, self.run_id, self.resultado = "pendiente", "", row.get("run_id") or "", ""
        self.idle_since = 0.0

    @property
    def tid(self) -> str:
        return self.row["territory_id"]

    def start(self) -> None:
        acc = self.row["accion"]
        self.since = _now()
        if acc == "nada":  # solo queda el ensemble
            self._ok(f"OK sin 00 ({self.row.get('estado', '')})")
        elif acc == "publicar" and not self.publishes:
            self._ok("OK sin publicar (D-18)")
        elif acc == "publicar":
            self._queue_publish(self.row["run_id"])
        elif acc == "esperar":
            self.fase = "00"
        else:
            dispatch(WF_00, {"territory_id": self.row["selector_00"], "data_edition": "2025",
                             "execution_mode": MODES[acc], "optimization_algorithm": self.algorithm,
                             "publication_mode": "electoral", "publish_result": self.publishes,
                             "lanzado_por_eleccion": True})
            self.fase = "00"
            self.log(f"{self.tid}: 00 lanzada ({MODES[acc]})")

    @property
    def publishes(self) -> bool:
        """«Publicar» del Gestor 2.0; por defecto, Congreso 350 (T-102) no publica (D-18)."""
        return bool(self.row.get("publicar", self.row.get("ambito") != VARIANT))

    def _queue_publish(self, run_id: str) -> None:
        self.run_id, self.fase = run_id, "cola_05"

    def publish(self) -> None:
        """Una sola 05 del Gestor a la vez: la 05 no lleva el run en su nombre y se identifica por orden."""
        self.since = _now()
        dispatch(WF_05, {"pagina_publicar": "Sitio completo", "production_run_id": self.run_id})
        self.fase = "05"
        self.log(f"{self.tid}: 05 lanzada con production_run_id={self.run_id}")

    def ensemble(self) -> None:
        """Una sola 06 del Gestor a la vez (se identifica por orden, como la 05); galería en el visor si publica."""
        self.since = _now()
        dispatch(WF_06, {"territory_id": self.row["ensemble"], "stage": "ensemble_10", "execution_confirmed": True,
                         "deploy_pages": self.publishes})
        self.fase = "06"
        self.log(f"{self.tid}: 06 lanzada (ensemble_10, {self.row['ensemble']})")

    def _ok(self, text: str) -> None:
        if self.row.get("ensemble") and self.fase not in ("06", "cola_06"):
            self.resultado, self.fase = text, "cola_06"
        else:
            self._end(text)

    def poll(self) -> None:
        if self.fase == "00":
            mark = tuple(f"{t} · {self.row['selector_00']} · " for t in TITLES_00)  # T-215: también el título viejo
            waiting = self.row["accion"] == "esperar"
            runs = [r for r in list_runs(WF_00, since="" if waiting else self.since[:10])
                    if str(r.get("display_title") or "").startswith(mark)
                    and (int(r["id"]) >= int(self.row["run_id"]) if waiting else r.get("created_at", "") >= self.since)]
            if not runs:
                return
            if any(r.get("status") != "completed" for r in runs):
                self.idle_since = 0.0
                return
            # La cadena (par → 00 electoral) se lanza antes de terminar la 00: margen para verla aparecer.
            if not self.idle_since:
                self.idle_since = time.time()
                return
            if time.time() - self.idle_since < 120:
                return
            own = min(runs, key=lambda r: (r.get("created_at", ""), int(r["id"])))  # la que lanzó el Gestor
            last = max(runs, key=lambda r: (r.get("created_at", ""), int(r["id"])))  # hijas encadenadas por el bot
            self.run_id = str(own["id"])
            if own.get("conclusion") != "success":
                self._end(f"FALLO 00 {self.run_id} ({own.get('conclusion')})")
            elif not self.publishes:
                self._ok(f"OK 00 {self.run_id} (sin publicar)")
            elif len(runs) == 1 and self.row["accion"] != "esperar":
                self._ok(f"OK 00 {self.run_id} (publicada por la propia 00)")
            elif last.get("conclusion") != "success":
                self.run_id = str(last["id"])
                self._end(f"FALLO 00 {self.run_id} ({last.get('conclusion')}, eslabón encadenado)")
            else:
                self._queue_publish(str(last["id"]))  # eslabón electoral de la cadena: no publica, publica el Gestor
        elif self.fase == "05":
            runs = [r for r in list_runs(WF_05, since=self.since[:10]) if r.get("created_at", "") >= self.since]
            if runs and all(r.get("status") == "completed" for r in runs):
                last = min(runs, key=lambda r: r.get("created_at", ""))
                ok = last.get("conclusion") == "success"
                text = f"{'OK' if ok else 'FALLO'} 05 {last['id']} (00 {self.run_id})"
                if ok:
                    self._ok(text)
                else:
                    self._end(text)
        elif self.fase == "06":
            runs = [r for r in list_runs(WF_06, since=self.since[:10]) if r.get("created_at", "") >= self.since]
            if runs and all(r.get("status") == "completed" for r in runs):
                last = min(runs, key=lambda r: r.get("created_at", ""))
                ok = last.get("conclusion") == "success"
                self._end(f"{self.resultado}; {'OK' if ok else 'FALLO'} 06 {last['id']}".lstrip("; "))

    def _end(self, text: str) -> None:
        self.fase, self.resultado = "fin", text
        self.log(f"{self.tid}: {text}")

    @property
    def ok(self) -> bool:
        return self.resultado.startswith("OK") and "FALLO" not in self.resultado


def run_campaign(plan: dict, algorithm: str, max_parallel: int, test_first: bool, deadline: float,
                 continue_inputs: dict, poll_seconds: int = 60, log=print) -> list[dict]:
    todo = [Territorio(r, algorithm, log) for r in plan["territorios"] if r["accion"] != "nada" or r.get("ensemble")]
    if not todo:
        log("Nada que lanzar: todos los territorios están publicados.")
        return []
    pending = list(todo)
    if test_first and len(todo) > 1:
        probe = pending.pop(0)
        log(f"Territorio de prueba: {probe.tid}")
        probe.start()
        while probe.fase != "fin":
            if time.time() > deadline:
                return _relay(todo, continue_inputs, log)
            time.sleep(poll_seconds)
            _step([probe])
        if not probe.ok:
            log(f"::error::El territorio de prueba falló ({probe.resultado}); no se lanza el resto.")
            return _report(todo)
    active: list[Territorio] = []
    while pending or active:
        if time.time() > deadline:
            return _relay(todo, continue_inputs, log)
        while pending and len(active) < max_parallel:
            t = pending.pop(0)
            t.start()
            active.append(t)
        time.sleep(poll_seconds)
        _step(active)
        active = [t for t in active if t.fase != "fin"]
    return _report(todo)


def _step(active: list[Territorio]) -> None:
    for t in active:
        if t.fase in ("00", "05", "06"):
            t.poll()
    if not any(t.fase == "05" for t in active):
        queued = [t for t in active if t.fase == "cola_05"]
        if queued:
            queued[0].publish()
    if not any(t.fase == "06" for t in active):
        queued = [t for t in active if t.fase == "cola_06"]
        if queued:
            queued[0].ensemble()


def _report(todo: list[Territorio]) -> list[dict]:
    return [{"territory_id": t.tid, "accion": t.row["accion"], "resultado": t.resultado or "NO_INICIADO"} for t in todo]


def _relay(todo: list[Territorio], inputs: dict, log) -> list[dict]:
    """Relevo `continuar`: los iniciados van con «@auto» (se retoman por su estado, sin rehacerlos); una 06 ya lanzada
    no se repite."""
    rest = [t for t in todo if t.fase not in ("fin", "06")]
    log(f"Límite del job: relevo en modo continuar con {len(rest)} territorios.")
    tokens = [t.tid if t.fase == "pendiente" else f"{t.tid}@auto" for t in rest]
    dispatch(WF_GESTOR, {**inputs, "modo": "continuar", "territorios": ",".join(tokens)})
    return _report(todo)


def exit_code(report: list[dict]) -> int:
    return 1 if any("FALLO" in r["resultado"] for r in report) else 0


# --------------------------------------------------------------------------- CLI

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("accion", choices=["generar", "plan", "lanzar"])
    ap.add_argument("--comprobar", action="store_true")
    ap.add_argument("--ambito", default="legislatura completa")
    ap.add_argument("--territorios", default="")
    ap.add_argument("--forzar", default="false")
    ap.add_argument("--sin-api", action="store_true", help="plan sin consultar runs en curso")
    ap.add_argument("--salida", type=Path, default=Path("plan.json"))
    ap.add_argument("--resumen", type=Path)
    ap.add_argument("--plan", type=Path, default=Path("plan.json"))
    ap.add_argument("--estrategia", default="Canónico")
    ap.add_argument("--max-paralelo", type=int, default=3)
    ap.add_argument("--sin-prueba", action="store_true")
    ap.add_argument("--minutos", type=int, default=320, help="presupuesto del job antes del relevo")
    a = ap.parse_args(argv)
    try:
        if a.accion == "generar":
            text = dump_config(build_config())
            if a.comprobar:
                if not CONFIG.is_file() or CONFIG.read_text(encoding="utf-8") != text:
                    print(f"::error::{CONFIG} no coincide con sus fuentes; regenérelo.", file=sys.stderr)
                    return 1
                print(f"{CONFIG} coincide con sus fuentes.")
                return 0
            CONFIG.write_text(text, encoding="utf-8")
            return 0
        if a.accion == "plan":
            tokens = [t.strip() for t in a.territorios.split(",") if t.strip()]
            running = {} if a.sin_api else running_00()
            plan = build_plan(load_config(), a.ambito, tokens, a.forzar.lower() == "true", running)
            a.salida.write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
            md = plan_markdown(plan)
            if a.resumen:
                a.resumen.write_text(md, encoding="utf-8")
            print(md)
            return 0
        plan = json.loads(a.plan.read_text(encoding="utf-8"))
        cont = {"estrategia": a.estrategia, "max_paralelo": str(a.max_paralelo), "forzar": a.forzar.lower()}
        report = run_campaign(plan, a.estrategia, max(1, a.max_paralelo), not a.sin_prueba,
                              time.time() + a.minutos * 60, cont)
        print(json.dumps(report, ensure_ascii=False, indent=1))
        return exit_code(report)
    except (GestorError, OSError, KeyError) as exc:
        print(f"::error::{exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
