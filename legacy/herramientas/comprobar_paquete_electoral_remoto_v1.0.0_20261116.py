#!/usr/bin/env python3
"""Comprueba al planificar la 00 que el paquete electoral del par sigue descargable.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Puerta temprana del paquete electoral (T-246)
FECHA: 2026-11-11
ESTADO: candidato
QUÉ HACE: cuando la 00 consume un par preparado (no ejecuta 03), localiza por metadatos REST el
paquete electoral acreditado con las mismas rutas que la puerta 03 → 04 (artefacto vivo del run,
mismo nombre y digest en otro run, copia durable en release) y bloquea con una causa accionable
solo ante evidencia positiva: falta (404/410 o ausente de un inventario completo), caducó (`expired` o
`expires_at` pasado) o su digest contradice la acreditación. Lo no determinable (503 de cuota, red, 403 de
permisos, inventario incompleto) y la caducidad próxima solo avisan (::warning::, salida 0): decide la puerta 03.
CAMBIOS: herramienta nueva.
MOTIVO: el paquete fuente se retiene 30 días; con «Reutilizar» la 00 no lo regenera y caía en la
puerta 03 tras gastar M04-M06.
ANTERIOR: ninguna (fichero nuevo).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import time
from pathlib import Path
from typing import Callable
from urllib.parse import quote

from herramientas.descargar_artefacto import Runner, _run, clasificar
from herramientas.localizar_artefacto_durable import LocationError, locate

SCHEMA = "ddd.preflight-paquete-electoral/1.0"
EXIT_BLOCK = 76
DEFAULT_MARGIN_HOURS = 12

Api = Callable[[str], object]


class ApiIndeterminada(RuntimeError):
    """La API no permitió concluir (cuota, red, permisos): no es evidencia de que falte el paquete."""


_sleep = time.sleep


def gh_api(path: str, *, runner: Runner | None = None, attempts: int = 3,
           sleep: Callable[[float], None] | None = None) -> object:
    """REST con la clasificación de T-251: 404/410 = ausente ({}); el resto, reintento y ApiIndeterminada."""
    runner = runner or _run
    sleep = sleep or _sleep
    salida = ""
    for attempt in range(attempts):
        proc = runner(["gh", "api", path])
        if proc.returncode == 0:
            return json.loads(proc.stdout or "{}")
        salida = f"{proc.stdout or ''}\n{proc.stderr or ''}"
        if clasificar(salida) == "missing":
            return {}
        if attempt + 1 < attempts:
            sleep(2 ** (attempt + 1))
    raise ApiIndeterminada(f"{path}: {salida.strip()[:300]}")


def _listing(api: Api, path: str) -> dict:
    """Inventario de artefactos; una respuesta sin forma de inventario no prueba nada."""
    doc = api(path)
    if not isinstance(doc, dict) or not isinstance(doc.get("artifacts", []), list):
        raise ApiIndeterminada(f"{path}: respuesta sin inventario de artefactos")
    return doc


def _sha(value: object) -> str:
    return str(value or "").removeprefix("sha256:").lower()


def _parse_time(value: object) -> dt.datetime | None:
    if not value:
        return None
    try:
        parsed = dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=dt.timezone.utc)


def remedio(territory: str) -> str:
    return (
        f"Regenera el paquete electoral de {territory}: «preparacion-resultados-electorales.yml» con "
        "reutilizar_si_ya_preparada=false; después «preparacion-legislatura-vigente.yml» prepare_one del "
        "territorio (registra el par nuevo) y relanza la 00."
    )


def requerido(plan: dict) -> bool:
    """El paquete solo lo exige la 00 que consume el par sin ejecutar 03."""
    activation = plan.get("electoral_activation") or {}
    return (
        plan.get("publication_mode_effective", plan.get("publication_mode")) == "electoral"
        and activation.get("execution") == "EXECUTE"
        and plan.get("run_prepare_electoral") is False
        and bool((plan.get("prepared_source_pair") or {}).get("pair_sha256"))
    )


def _expected(plan: dict, root: Path) -> dict:
    source = (plan.get("existing") or {}).get("electoral_source") or {}
    pair_rel = (plan.get("prepared_source_pair") or {}).get("receipt_path")
    artifact_id = None
    if pair_rel and (root / pair_rel).is_file():
        pair = json.loads((root / pair_rel).read_text(encoding="utf-8"))
        remote = (pair.get("electoral_source") or {}).get("remote_verification") or {}
        artifact_id = remote.get("artifact_id")
    return {
        "run_id": int(source.get("run_id") or 0),
        "artifact_name": str(source.get("artifact_name") or ""),
        "artifact_sha256": _sha(source.get("artifact_sha256")),
        "artifact_id": artifact_id if isinstance(artifact_id, int) else None,
        "pair_receipt": pair_rel,
    }


def evaluar(
    plan: dict,
    *,
    repo: str,
    root: Path,
    api: Api = gh_api,
    now: dt.datetime | None = None,
    margin_hours: float = DEFAULT_MARGIN_HOURS,
) -> dict:
    territory = str(plan.get("territory_name") or plan.get("territory_id") or "")
    base = {"schema": SCHEMA, "territory": territory}
    if not requerido(plan):
        return {**base, "decision": "NOT_REQUIRED"}
    exp = _expected(plan, root)
    base["expected"] = exp
    now = now or dt.datetime.now(dt.timezone.utc)
    limit = now + dt.timedelta(hours=margin_hours)

    def block(code: str, detail: str) -> dict:
        return {**base, "decision": "BLOCK", "code": code,
                "message": f"{code}: {detail}. {remedio(territory)}"}

    def warn(code: str, detail: str, decision: str = "INDETERMINATE", **extra) -> dict:
        return {**base, "decision": decision, "code": code, "warning": f"{code}: {detail}", **extra}

    name, digest, run_id = exp["artifact_name"], exp["artifact_sha256"], exp["run_id"]
    if run_id <= 0 or not name or not re.fullmatch(r"[0-9a-f]{64}", digest):
        return warn("ELECTORAL_PACKAGE_IDENTITY_INCOMPLETE",
                    f"el plan no acredita run, nombre y sha256 del paquete electoral (run={run_id}, nombre={name!r}); "
                    "decide la puerta 03")

    def caducado(a: dict) -> bool:
        expires = _parse_time(a.get("expires_at"))
        return a.get("expired") is True or (expires is not None and expires <= now)

    try:
        listing = _listing(api, f"repos/{repo}/actions/runs/{run_id}/artifacts?per_page=100")
        rows = listing.get("artifacts") or []
        complete = int(listing.get("total_count") or len(rows)) <= len(rows)
        named = [a for a in rows if a.get("name") == name]
        live = [a for a in named if not caducado(a) and _sha(a.get("digest")) == digest]
        found_note = "en su run"
        if not live:
            others = _listing(api, f"repos/{repo}/actions/artifacts?name={quote(name)}&per_page=100").get("artifacts") or []
            live = [a for a in others if not caducado(a) and _sha(a.get("digest")) == digest]
            found_note = "en otro run con el mismo digest"

        def release_copy() -> dict | None:
            try:
                located = locate(repo, run_id, name, digest, api=api)
            except LocationError:
                return None
            return located if located.get("source") == "release" else None

        if live:
            latest = max(live, key=lambda a: _parse_time(a.get("expires_at")) or now)
            ready = {"source": "actions", "note": found_note, "artifact_id": latest.get("id"),
                     "expires_at": latest.get("expires_at")}
            if (found_note == "en su run" and exp["artifact_id"] is not None
                    and all(a.get("id") != exp["artifact_id"] for a in live)):
                return warn("ELECTORAL_PACKAGE_ARTIFACT_ID_CHANGED",
                            f"artifact_id remoto de {name} distinto del receipt del par ({exp['artifact_id']}); "
                            "nombre y digest coinciden", decision="READY", **ready)
            expires = _parse_time(latest.get("expires_at"))
            if expires is not None and expires < limit and release_copy() is None:
                return warn("ELECTORAL_PACKAGE_EXPIRES_SOON",
                            f"{name} (run {run_id}) caduca el {expires.isoformat()}, quizá antes de la puerta 03 → 04; "
                            + remedio(territory), decision="READY", **ready)
            return {**base, "decision": "READY", **ready}

        durable = release_copy()
    except ApiIndeterminada as exc:
        return warn("ELECTORAL_PACKAGE_UNDETERMINED",
                    f"no se pudo consultar la API de GitHub ({exc}); decide la puerta 03")
    if durable is not None:
        return {**base, "decision": "READY", "source": "release", "release_tag": durable.get("release_tag")}
    if any(caducado(a) for a in named):
        return block("ELECTORAL_PACKAGE_EXPIRED",
                     f"{name} (run {run_id}) ha caducado en Actions y no tiene copia durable con el mismo sha256")
    if named:
        return block("ELECTORAL_PACKAGE_DIGEST_MISMATCH",
                     f"{name} (run {run_id}) existe con un digest distinto del acreditado sha256:{digest} "
                     "y no hay copia con el acreditado")
    if not complete:
        return warn("ELECTORAL_PACKAGE_UNDETERMINED",
                    f"inventario del run {run_id} incompleto y sin {name}; decide la puerta 03")
    return block("ELECTORAL_PACKAGE_MISSING",
                 f"{name} no existe en el run {run_id} (o el run ya no existe) ni en otro run ni en releases durables")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--plan", required=True, type=Path)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--root-dir", default=".", type=Path)
    ap.add_argument("--margin-hours", type=float, default=DEFAULT_MARGIN_HOURS)
    ap.add_argument("--output", type=Path)
    ns = ap.parse_args(argv)
    try:
        plan = json.loads(ns.plan.read_text(encoding="utf-8"))
        result = evaluar(plan, repo=ns.repo, root=ns.root_dir, api=gh_api, margin_hours=ns.margin_hours)
    except Exception as exc:  # noqa: BLE001 - lo inesperado nunca bloquea: decide la puerta 03
        result = {"schema": SCHEMA, "decision": "INDETERMINATE", "code": "ELECTORAL_PACKAGE_UNDETERMINED",
                  "warning": f"ELECTORAL_PACKAGE_UNDETERMINED: comprobación no concluyente "
                             f"({type(exc).__name__}: {str(exc)[:300]}); decide la puerta 03"}
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if ns.output:
        ns.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    if result["decision"] == "BLOCK":
        print(f"::error::{result['message']}", file=sys.stderr)
        return EXIT_BLOCK
    if result.get("warning"):
        print(f"::warning::{result['warning']}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
