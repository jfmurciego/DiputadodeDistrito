#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: motor 2 — el único mapa vigente: el publicado en el visor
VERSIÓN: 1.0.1
NOMBRE DE VERSIÓN: Vigente único · el publicado en el visor
FECHA: 2026-11-12
ESTADO: candidato (motor 2; producción no lo importa)
CAMBIOS: 1.0.0 — (T-258) fichero nuevo. Un solo resolvedor del vigente para la competición (generadores.Vigente,
  competir --reanudar, P30) y la aceptación (herramientas/bateria_motor.py: indicadores y matriz). Antes la
  competición leía datos/composicion/<t>.csv y la aceptación la composición del run publicado en el visor: en 31
  territorios eran mapas distintos (Castilla y León y 30 del Congreso) y en Canarias la aceptación caía en el
  <t>.csv de otro run, así que la clave de la competición y la comprobación 2 medían vigentes distintos.
MOTIVO: T-258: que competición y aceptación comparen siempre contra el mismo vigente, el publicado en el visor.
CAMBIOS 1.0.1 (T-220): ids de territorio nuevos de la tabla maestra (aut01…nac52, D-61); el id viejo se lee vía ddd_core.territorio_ids.
ANTERIOR: legacy/ddd_motor2/vigente_v1.0.0_20261112.py
REGLA: el vigente de `t` es el canonical_m06 de mayor run de orchestracion/publicaciones_visor.json (elección
  2023-07-23; sin fecha cuenta como 2023-07-23). Su composición es datos/composicion/runs/<t>_<run>.csv; si no
  existe, datos/composicion/<t>.csv solo si MANIFEST.json dice que es de ese mismo run. Si no, no hay vigente
  comparable y se dice por qué (nunca otro mapa en su lugar). Sin registro en el visor no hay mapa publicado.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .semilla import territorio_ids  # noqa: E402  (T-220: el registro del visor guarda el id viejo)

ROOT = Path(__file__).resolve().parents[1]
ELECCION = "2023-07-23"


@dataclass(frozen=True)
class VigentePublicado:
    ruta: Path | None
    run: str | None
    motivo: str = ""  # vacío si hay composición; si no, por qué no hay vigente comparable


def run_publicado(t: str, root: Path = ROOT) -> str | None:
    pv = Path(root) / "orchestracion" / "publicaciones_visor.json"
    if not pv.is_file():
        return None
    runs = [int(p["run_id"]) for p in json.loads(pv.read_text(encoding="utf-8")).get("products") or []
            if p.get("kind") == "canonical_m06" and territorio_ids.mismo_territorio(str(p.get("territory_id") or ""), str(t)) and str(p.get("run_id") or "").isdigit()
            and str(p.get("election_date") or ELECCION) == ELECCION]
    return str(max(runs)) if runs else None


def vigente_publicado(t: str, root: Path = ROOT) -> VigentePublicado:
    root = Path(root)
    run = run_publicado(t, root)
    if run is None:
        return VigentePublicado(None, None, "sin mapa publicado en el visor (publicaciones_visor.json)")
    # T-220: la composición publicada puede llevar el id viejo en el nombre (productos derivados, D-61).
    f = territorio_ids.fichero_por_id(root / "datos" / "composicion" / "runs", "{}_" + str(run) + ".csv", t)
    if f.is_file():
        return VigentePublicado(f, run)
    canon = territorio_ids.fichero_por_id(root / "datos" / "composicion", "{}.csv", t)
    man = root / "datos" / "composicion" / "MANIFEST.json"
    run_canon = (territorio_ids.en_mapa(json.loads(man.read_text(encoding="utf-8")).get("territorios") or {}, t)
                 or {}).get("run_id") if man.is_file() else None
    if canon.is_file() and str(run_canon) == run:
        return VigentePublicado(canon, run)
    return VigentePublicado(None, run, f"el mapa publicado (run {run}) no tiene composición versionada en "
                                       f"datos/composicion (datos/composicion/{t}.csv es del run {run_canon or '—'})")
