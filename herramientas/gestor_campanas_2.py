#!/usr/bin/env python3
"""Gestor de Campañas 2.0 (T-105, D-22): seis entradas en español → plan en seco o campaña sin chats.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.3.1 · FECHA: 2026-11-12 · ESTADO: candidato
CAMBIOS: 1.3.0 (T-133): la campaña completa con tipo autonómico planifica también el histórico autonómico desde 2011
  (herramientas/historico_autonomico.py: paso A por comunidad, cada una con su calendario); filas con `tipo`
  («general» o «autonomico») y una prueba de cada tipo. Las comunidades sin paso B se omiten con su motivo.
CAMBIOS: 1.2.0 (T-130): elección «campaña completa» y tipo «nacional y autonómico»: UNA orden planifica la legislatura
  vigente (nacional y/o autonómica, con o sin ensemble 10) más el histórico de las cinco generales (matriz con `clave`
  por fila); el histórico autonómico queda como «pendiente» (T-131) sin impedir el resto. `lanzar` ejecuta la parte
  vigente del plan; el histórico lo ejecutan los jobs del workflow.
CAMBIOS: 1.1.0 (T-113): «histórico: generales 2019-11» planifica el paso A de T-83 por provincia
  (herramientas/historico_campana.py; matriz `historico` del plan, la ejecutan los jobs del workflow); el resto de
  elecciones históricas, el tipo autonómico, el mapa 350, el ensemble y publicar siguen fallando con mensaje claro.
  1.0.0: fichero nuevo.
CAMBIOS 1.3.1 (T-220): ids de territorio nuevos de la tabla maestra (aut01…nac52, D-61); el id viejo se lee vía ddd_core.territorio_ids.
ANTERIOR: legacy/herramientas/gestor_campanas_2_v1.3.0_20261112.py
QUÉ HACE: traduce las entradas del formulario «0 Gestor de Campañas», en el orden de D-22, a un plan de
  `legislatura_vigente.py` y, si «solo plan» está desactivado, lo lanza: 00 (con su cadena par → 00 electoral)
  → 05 si «publicar» = sí → 06 `ensemble_10` si «ensemble» = 10.
  1) elección: legislatura vigente o histórico (cuál); 2) tipo: nacional o autonómico; 3) territorios: «todos» o
  lista de provincias o comunidades por nombre, código o matrícula; 4) inicio; 5) publicar; 6) ensemble.
  Además `mapa` (407 o 350, T-102) y `solo plan`.
  Lo que aún no existe falla al planificar con un mensaje claro y sin lanzar nada (`::error::`, código 2).
NO HACE: aprobar el entorno `produccion` (el clic del propietario al lanzar es su permiso, D-22) ni reintentar.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import clave_eleccion as ce  # noqa: E402
import historico_autonomico as ha  # noqa: E402
import historico_campana as hc  # noqa: E402
import legislatura_vigente as lv  # noqa: E402
import sys as _sys_t220  # noqa: E402
from pathlib import Path as _Path_t220  # noqa: E402
if str(_Path_t220(__file__).resolve().parents[1]) not in _sys_t220.path:
    _sys_t220.path.insert(0, str(_Path_t220(__file__).resolve().parents[1]))
from ddd_core.territorio_ids import mismo_territorio  # noqa: E402  (T-220: id viejo o nuevo)

VIGENTE = "legislatura vigente"
COMPLETA = "campaña completa"
AMBOS = "nacional y autonómico"
ELECCIONES = [VIGENTE, COMPLETA, "histórico: generales 2019-11", "histórico: generales 2019-04", "histórico: generales 2016",
              "histórico: generales 2015", "histórico: generales 2011"]
TIPOS = ["nacional", "autonómico", AMBOS]
INICIOS = {"reutilizar progreso": "auto", "aprovechar fuentes": "aprovechar_fuentes",
           "desde el principio": "desde_el_principio"}
SI_NO = ["no", "sí"]
ENSEMBLES = ["ninguno", "10", "25"]
MAPAS = ["407", "350"]
CATALOG = Path("configuracion/catalogo_territorios_espana_2025.yaml")
ENSEMBLE_DIR = Path("configuracion/ensemble")


class NoDisponible(lv.GestorError):
    """Opción válida en el formulario que todavía no se puede lanzar."""


def _choice(name: str, value: str, options) -> str:
    v = str(value or "").strip()
    if v not in options:
        raise lv.GestorError(f"«{name}» no admite «{v}»; opciones: {', '.join(options)}")
    return v


def _communities(root: Path) -> list[dict]:
    return (yaml.safe_load((root / CATALOG).read_text(encoding="utf-8")) or {}).get("territories") or []


def _is_community(c: dict, token: str) -> bool:
    n = ce.normalize(token)
    names = {ce.normalize(c["name"]), ce.normalize(c["territory_id"])}
    names |= {x.removeprefix("COMUNIDAD-DE-").removeprefix("REGION-DE-").removeprefix("PRINCIPADO-DE-")
              .removeprefix("COMUNIDAD-FORAL-DE-").removeprefix("ISLAS-").removeprefix("ILLES-") for x in names}
    return n in names


def _resolve_tokens(cfg: dict, tipo: str, mapa: str, tokens: list[str], root: Path) -> list[str]:
    """territory_id de la legislatura vigente para «todos» o una lista de partes."""
    rows = cfg["territorios"]
    nac = [r for r in rows if r["ambito"] == "nacional"]
    target = {"autonómico": "autonómica", "nacional": lv.VARIANT if mapa == "350" else "nacional"}[tipo]
    exact = [r["territory_id"] for r in rows if r["ambito"] == target]
    if tokens and all(t in exact for t in tokens):  # territory_id exactos (relevo «continuar»)
        return list(dict.fromkeys(tokens))
    if tipo == "autonómico":
        aut = [r for r in rows if r["ambito"] == "autonómica"]
        if not tokens:
            return [r["territory_id"] for r in aut]
        units = {u["territory_id"]: u for u in ce.load_units(root)}
        out, unknown = [], []
        for t in tokens:
            hits = [r["territory_id"] for r in aut if ce._matches_filter(units[r["territory_id"]], t)
                    or any(_is_community(c, t) and mismo_territorio(str(c["territory_id"] or ""), str(r["territory_id"])) for c in _communities(root))]
            (out.extend(hits) if hits else unknown.append(t))
        if unknown:
            raise lv.GestorError(f"Comunidades desconocidas: {', '.join(unknown)} (nombre o código INE de comunidad, 01-19)")
        ids = list(dict.fromkeys(out))
    else:
        if not tokens:
            ids = [r["territory_id"] for r in nac]
        else:
            units = {u["territory_id"]: u for u in ce.load_units(root)}
            by_code = {r["codigo"]: r["territory_id"] for r in nac}
            out, unknown = [], []
            for t in tokens:
                # Provincia (código INE, matrícula o nombre) antes que comunidad: «Madrid» o «Murcia» dan lo mismo.
                hits = [r["territory_id"] for r in nac if ce._matches_filter(units[r["territory_id"]], t)]
                if not hits:
                    hits = [by_code[p] for c in _communities(root) if _is_community(c, t)
                            for p in c["province_codes"] if p in by_code]
                (out.extend(hits) if hits else unknown.append(t))
            if unknown:
                raise lv.GestorError(f"Partes desconocidas: {', '.join(unknown)} (provincia por nombre, código INE o "
                                     "matrícula, o comunidad por nombre)")
            ids = list(dict.fromkeys(out))
    if mapa == "350":
        twins = {r["codigo"][1:]: r["territory_id"] for r in rows if r["ambito"] == lv.VARIANT}
        code = {r["territory_id"]: r["codigo"] for r in nac}
        missing = [i for i in ids if code[i] not in twins]
        if missing and tokens:
            raise NoDisponible(f"Sin mapa de 350 (T-102): {', '.join(missing)}; las islas no tienen gemelo 350.")
        ids = [twins[code[i]] for i in ids if code[i] in twins]
    return ids


def resolve(entradas: dict, root: Path = Path(".")) -> dict:
    """Valida las entradas y devuelve lo que necesita `build_plan`; lo no disponible lanza NoDisponible."""
    eleccion = _choice("elección", entradas.get("eleccion"), ELECCIONES)
    tipo = _choice("tipo", entradas.get("tipo"), TIPOS)
    inicio = INICIOS[_choice("inicio", entradas.get("inicio"), INICIOS)]
    publicar = _choice("publicar", entradas.get("publicar"), SI_NO) == "sí"
    ensemble = _choice("ensemble", entradas.get("ensemble"), ENSEMBLES)
    mapa = _choice("mapa", entradas.get("mapa"), MAPAS)
    if eleccion == COMPLETA:
        return _resolve_completa(entradas, tipo, publicar, ensemble, mapa, root)
    if tipo == AMBOS:
        raise NoDisponible("El tipo «nacional y autonómico» solo existe con la elección «campaña completa».")
    if eleccion != VIGENTE:
        return _resolve_historico(entradas, eleccion, tipo, publicar, ensemble, mapa, root)
    if ensemble == "25":
        raise NoDisponible("El ensemble de 25 no está validado (solo existe `ensemble_10`, T-91). "
                           "Elija «ninguno» o «10».")
    if mapa == "350":
        if tipo != "nacional":
            raise NoDisponible("El mapa de 350 (T-102) solo existe para el tipo «nacional».")
        if publicar:
            raise NoDisponible("El mapa de 350 no se publica sin aprobación del propietario (D-18). Elija publicar «no».")
        if ensemble != "ninguno":
            raise NoDisponible("El mapa de 350 no tiene configuración de ensemble. Elija «ninguno».")
    raw = [t.strip() for t in str(entradas.get("territorios") or "").split(",") if t.strip()]
    auto = {t.removesuffix("@auto") for t in raw if t.endswith("@auto")}  # relevo «continuar»
    raw = [t.removesuffix("@auto") for t in raw]
    tokens = [] if [ce.normalize(t) for t in raw] in ([], ["TODOS"]) else raw
    cfg = lv.load_config(root)
    ids = _resolve_tokens(cfg, tipo, mapa, tokens, root)
    if not ids:
        raise lv.GestorError("La selección no contiene ningún territorio.")
    ens = {}
    if ensemble == "10":
        missing = [i for i in ids if not (root / ENSEMBLE_DIR / f"{i}.json").is_file()]
        if missing:
            raise NoDisponible(f"Sin configuración de ensemble de 10 ({ENSEMBLE_DIR}/<territorio>.json): "
                               f"{', '.join(missing)}. Elija «ninguno» o una lista con configuración.")
        ens = {i: i for i in ids}
    return {"ids": ids, "inicio": {i: ("auto" if i in auto else inicio) for i in ids}, "publicar": publicar,
            "ensemble": ens,
            "entradas": {"eleccion": eleccion, "tipo": tipo, "territorios": ",".join(raw) or "todos",
                         "inicio": entradas.get("inicio"), "publicar": "sí" if publicar else "no",
                         "ensemble": ensemble, "mapa": mapa}}


def _resolve_historico(entradas: dict, eleccion: str, tipo: str, publicar: bool, ensemble: str, mapa: str,
                       root: Path) -> dict:
    """Histórico (T-113): solo nacional, mapa 407, sin ensemble ni publicación; matriz del paso A."""
    if hc.CLAVES[eleccion] not in hc.SOPORTADAS:
        try:
            hc.plan(eleccion, [], False, root)  # NoDisponible con el mensaje de la elección
        except hc.NoDisponible as exc:
            raise NoDisponible(str(exc)) from exc
    if tipo != "nacional":
        raise NoDisponible("El histórico solo existe para el tipo «nacional» (generales al Congreso).")
    if mapa != "407":
        raise NoDisponible("El histórico va sobre los distritos vigentes de 407; el mapa de 350 no tiene histórico.")
    if ensemble != "ninguno":
        raise NoDisponible("El histórico no tiene ensemble. Elija «ninguno».")
    if publicar:
        raise NoDisponible("El histórico aún no se publica: la puerta 04 del histórico no está adaptada (T-83 A). "
                           "Elija publicar «no».")
    raw = [t.strip() for t in str(entradas.get("territorios") or "").split(",") if t.strip()]
    tokens = [] if [ce.normalize(t) for t in raw] in ([], ["TODOS"]) else raw
    cfg = lv.load_config(root)
    ids = _resolve_tokens(cfg, "nacional", "407", tokens, root)
    code = {r["territory_id"]: r["codigo"] for r in cfg["territorios"] if r["ambito"] == "nacional"}
    try:
        h = hc.plan(eleccion, [{"territory_id": i, "codigo": code[i]} for i in ids], bool(tokens), root)
    except hc.NoDisponible as exc:
        raise NoDisponible(str(exc)) from exc
    return {"historico": h, "entradas": {"eleccion": eleccion, "tipo": tipo, "territorios": ",".join(raw) or "todos",
                                         "inicio": entradas.get("inicio"), "publicar": "no", "ensemble": ensemble,
                                         "mapa": mapa}}


def _resolve_completa(entradas: dict, tipo: str, publicar: bool, ensemble: str, mapa: str, root: Path) -> dict:
    """Campaña completa (T-130): vigente (nacional y/o autonómica) + histórico de las 5 generales, en una orden."""
    if mapa != "407":
        raise NoDisponible("La campaña completa va sobre el mapa de 407. Elija mapa «407».")
    tipos = ["nacional", "autonómico"] if tipo == AMBOS else [tipo]
    raw = str(entradas.get("territorios") or "").strip()
    if tipo == AMBOS and [ce.normalize(t) for t in raw.split(",") if t.strip()] not in ([], ["TODOS"]):
        raise lv.GestorError("Con «nacional y autonómico» los territorios son «todos»: elija un tipo para acotar.")
    parts = [resolve({**entradas, "eleccion": VIGENTE, "tipo": t}, root) for t in tipos]
    out = {"completa": True, "ids": [i for p in parts for i in p["ids"]], "publicar": publicar,
           "inicio": {k: v for p in parts for k, v in p["inicio"].items()},
           "ensemble": {k: v for p in parts for k, v in p["ensemble"].items()},
           "entradas": {**parts[0]["entradas"], "eleccion": COMPLETA, "tipo": tipo}, "pendiente": []}
    rows, omitidos, partes = [], {}, []
    if "nacional" in tipos:
        lotes = [_resolve_historico({**entradas, "eleccion": e}, e, "nacional", False, "ninguno", "407", root)["historico"]
                 for e in ELECCIONES if e.startswith("histórico: generales")]
        rows += [{**r, "clave": h["clave"], "tipo": "general"} for h in lotes for r in h["include"]]
        omitidos.update({f"{h['clave']}:{t}": m for h in lotes for t, m in h["omitidos"].items()})
        partes.append("las cinco generales 2011-2023")
    if "autonómico" in tipos:
        try:
            h = ha.plan(parts[-1]["ids"], False, root)
        except ha.NoDisponible as exc:
            out["pendiente"].append(f"Histórico autonómico desde 2011: {exc}")
        else:
            rows += [{"territorio": r["comunidad"], "provincia": "", "clave": "autonomicas", "tipo": "autonomico",
                      "elecciones": r["elecciones"]} for r in h["include"]]
            omitidos.update({f"autonomicas:{t}": m for t, m in h["omitidos"].items()})
            partes.append("autonómicas desde 2011 (" + ", ".join(r["comunidad"] for r in h["include"]) + ")")
    if rows:
        out["historico"] = {"completa": True, "eleccion": " + ".join(partes), "clave": "completa", "prueba": rows[0],
                            "include": rows, "omitidos": omitidos}
    return out


def build(entradas: dict, running: dict[str, str], root: Path = Path("."), today=None) -> dict:
    r = resolve(entradas, root)
    if r.get("completa"):
        plan = lv.build_plan(lv.load_config(root), "legislatura completa", r["ids"], False, running, root=root,
                             today=today, inicio=r["inicio"], publicar=r["publicar"], ensemble=r["ensemble"])
        plan.update({"ambito": f"{r['entradas']['tipo']} · campaña completa · mapa 407", "entradas": r["entradas"],
                     "pendiente": r["pendiente"]})
        if "historico" in r:
            plan["historico"] = r["historico"]
        return plan
    if "historico" in r:
        return {"historico": r["historico"], "ambito": "histórico · nacional · mapa 407", "entradas": r["entradas"]}
    plan = lv.build_plan(lv.load_config(root), "legislatura completa", r["ids"], False, running, root=root,
                         today=today, inicio=r["inicio"], publicar=r["publicar"], ensemble=r["ensemble"])
    plan["ambito"] = f"{r['entradas']['tipo']} · mapa {r['entradas']['mapa']}"
    plan["entradas"] = r["entradas"]
    return plan


def markdown(plan: dict, solo_plan: bool) -> str:
    e = plan["entradas"]
    head = ["### 0 Gestor de Campañas 2.0 · " + ("SOLO PLAN (no se lanza nada)" if solo_plan else "LANZAMIENTO"), "",
            f"1) Elección: {e['eleccion']} · 2) Tipo: {e['tipo']} · 3) Territorios: {e['territorios']} · "
            f"4) Inicio: {e['inicio']} · 5) Publicar: {e['publicar']} · 6) Ensemble: {e['ensemble']} · Mapa: {e['mapa']}",
            ""]
    if "territorios" not in plan:
        return "\n".join(head) + hc.plan_markdown(plan["historico"])
    head += ["Cadena por territorio: 00 (par → 00 electoral) → 05 si publica → 06 si ensemble.", ""]
    md = "\n".join(head) + lv.plan_markdown(plan)
    if "historico" in plan:
        h = plan["historico"]
        md += (f"\n#### Histórico: {h['eleccion']}\n\n{len(h['include'])} ejecuciones del paso A (territorio × elección), "
               f"prueba: {h['prueba']['territorio']} {h['prueba']['clave']}; omitidos: {len(h['omitidos'])}. "
               "No publica.\n")
    for t in plan.get("pendiente", []):
        md += f"\n- Pendiente: {t}\n"
    return md


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("accion", choices=["plan", "lanzar"])
    for k in ("eleccion", "tipo", "territorios", "inicio", "publicar", "ensemble", "mapa"):
        ap.add_argument(f"--{k}", default="")
    ap.add_argument("--solo-plan", default="true")
    ap.add_argument("--sin-api", action="store_true", help="plan sin consultar runs en curso")
    ap.add_argument("--salida", type=Path, default=Path("plan.json"))
    ap.add_argument("--resumen", type=Path)
    ap.add_argument("--plan", type=Path, default=Path("plan.json"))
    ap.add_argument("--max-paralelo", type=int, default=3)
    ap.add_argument("--sin-prueba", action="store_true")
    ap.add_argument("--minutos", type=int, default=320)
    a = ap.parse_args(argv)
    try:
        if a.accion == "plan":
            entradas = {k: getattr(a, k) for k in ("eleccion", "tipo", "territorios", "inicio", "publicar",
                                                   "ensemble", "mapa")}
            plan = build(entradas, {} if a.sin_api else lv.running_00())
            a.salida.write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
            md = markdown(plan, a.solo_plan.lower() == "true")
            if a.resumen:
                a.resumen.write_text(md, encoding="utf-8")
            print(md)
            return 0
        plan = json.loads(a.plan.read_text(encoding="utf-8"))
        if "territorios" not in plan:
            raise lv.GestorError("El histórico lo ejecutan los jobs «histórico» del workflow, no «lanzar».")
        cont = {**plan["entradas"], "solo_plan": "false", "max_paralelo": str(a.max_paralelo)}
        report = lv.run_campaign(plan, "Canónico", max(1, a.max_paralelo), not a.sin_prueba,
                                 time.time() + a.minutos * 60, cont)
        print(json.dumps(report, ensure_ascii=False, indent=1))
        return lv.exit_code(report)
    except (lv.GestorError, OSError, KeyError) as exc:
        print(f"::error::{exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
