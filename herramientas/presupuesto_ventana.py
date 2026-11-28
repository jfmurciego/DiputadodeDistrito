#!/usr/bin/env python3
"""Presupuesto de la ventana de 5 horas: acepta o rechaza un plan de flota (T-511, D-217).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0
FECHA: 2026-11-28
ESTADO: candidato
CAMBIOS: 1.0.0: fichero nuevo.
MOTIVO: el tope real de gasto es la ventana de 5 horas, no el semanal; dos flotas la agotaron el 27 y el 28-11 sin
  que ninguna regla lo impidiera (investigación T-509, hallazgo C-1).
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE: lee un plan de flota en JSON y la configuración `configuracion/presupuesto_ventana.json` (ventana en USD de
  equivalencia, reparto reserva/coordinación/trabajo, modelo y esfuerzo por rol, coste estimado por sesión) y comprueba:
  1. cada rol existe en la tabla;
  2. ninguna sesión sube de modelo ni de esfuerzo sobre la tabla sin `"autorizado_propietario": true` (la frase del
     propietario; Fable y esfuerzo máximo solo con ella);
  3. el gasto estimado de coordinación y de trabajo cabe en su parte del reparto, y el total no invade la reserva.
Formato del plan: {"sesiones": [{"rol": "implementador", "cantidad": 3, "modelo": "sonnet", "esfuerzo": "high",
  "autorizado_propietario": false}]}. `modelo`, `esfuerzo` y `cantidad` son opcionales (tabla y 1).
  `"ya_gastado_usd"` (opcional, número) se resta del trabajo disponible: es lo gastado en la ventana por otros chats.
Uso: python herramientas/presupuesto_ventana.py --plan flota.json [--config RUTA]
Salida: 0 si el plan cabe; 1 con una línea «::error» por fallo; 2 si el plan o la configuración no se pueden leer.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configuracion" / "presupuesto_ventana.json"
EPS = 1e-9


class ErrorEntrada(Exception):
    pass


def cargar_json(ruta: Path) -> dict:
    try:
        datos = json.loads(Path(ruta).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ErrorEntrada(f"no se puede leer {ruta}: {exc}") from exc
    if not isinstance(datos, dict):
        raise ErrorEntrada(f"{ruta}: se esperaba un objeto JSON")
    return datos


def evaluar(plan: dict, cfg: dict) -> tuple[list[str], dict]:
    """Devuelve (errores, resumen). Sin errores, el plan cabe."""
    errores: list[str] = []
    try:
        ventana = float(cfg["ventana_usd"])
        reparto = cfg["reparto"]
        costes = cfg["coste_sesion_usd"]
        roles = cfg["roles"]
        orden_m = list(cfg["orden_modelos"])
        orden_e = list(cfg["orden_esfuerzo"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ErrorEntrada(f"configuración incompleta: {exc!r}") from exc
    if abs(sum(float(v) for v in reparto.values()) - 1.0) > 1e-6:
        raise ErrorEntrada("el reparto de la configuración no suma 1")

    gasto = {"coordinacion": 0.0, "trabajo": 0.0}
    sesiones = plan.get("sesiones")
    if not isinstance(sesiones, list) or not sesiones:
        raise ErrorEntrada("el plan necesita una lista «sesiones» no vacía")
    total_sesiones = 0
    for i, s in enumerate(sesiones):
        rol = s.get("rol") if isinstance(s, dict) else None
        if rol not in roles:
            errores.append(f"sesión {i}: rol desconocido {rol!r} (roles: {', '.join(sorted(roles))})")
            continue
        base = roles[rol]
        modelo = s.get("modelo", base["modelo"])
        esfuerzo = s.get("esfuerzo", base["esfuerzo"])
        cantidad = s.get("cantidad", 1)
        if not isinstance(cantidad, int) or isinstance(cantidad, bool) or cantidad < 1:
            errores.append(f"sesión {i} ({rol}): cantidad no válida {cantidad!r}")
            continue
        if modelo not in orden_m or esfuerzo not in orden_e or esfuerzo not in costes.get(modelo, {}):
            errores.append(f"sesión {i} ({rol}): modelo/esfuerzo no válidos {modelo!r}/{esfuerzo!r}")
            continue
        sube = (orden_m.index(modelo) > orden_m.index(base["modelo"])
                or orden_e.index(esfuerzo) > orden_e.index(base["esfuerzo"]))
        if sube and s.get("autorizado_propietario") is not True:
            errores.append(
                f"sesión {i} ({rol}): {modelo}/{esfuerzo} supera la tabla ({base['modelo']}/{base['esfuerzo']}) "
                "sin autorizado_propietario")
        gasto[base["categoria"]] += cantidad * float(costes[modelo][esfuerzo])
        total_sesiones += cantidad

    ya = plan.get("ya_gastado_usd", 0)
    if not isinstance(ya, (int, float)) or isinstance(ya, bool) or ya < 0:
        raise ErrorEntrada("ya_gastado_usd debe ser un número ≥ 0")
    gasto["trabajo"] += float(ya)

    limite = {k: ventana * float(reparto[k]) for k in ("coordinacion", "trabajo")}
    for cat in ("coordinacion", "trabajo"):
        if gasto[cat] > limite[cat] + EPS:
            errores.append(
                f"{cat}: {gasto[cat]:.2f} USD estimados > {limite[cat]:.2f} USD "
                f"({float(reparto[cat]):.0%} de {ventana:.0f})")
    tope_total = ventana * (1 - float(reparto["reserva_propietario"]))
    total = gasto["coordinacion"] + gasto["trabajo"]
    if total > tope_total + EPS:
        errores.append(
            f"total: {total:.2f} USD estimados > {tope_total:.2f} USD: invade la reserva del propietario "
            f"({float(reparto['reserva_propietario']):.0%})")
    resumen = {"sesiones": total_sesiones, "gasto_usd": gasto, "limite_usd": limite,
               "total_usd": total, "tope_total_usd": tope_total}
    return errores, resumen


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--plan", required=True, help="plan de flota en JSON")
    ap.add_argument("--config", default=str(CONFIG), help="configuración (por defecto la del repositorio)")
    args = ap.parse_args(argv)
    try:
        plan = cargar_json(Path(args.plan))
        cfg = cargar_json(Path(args.config))
        errores, r = evaluar(plan, cfg)
    except ErrorEntrada as exc:
        print(f"::error::{exc}")
        return 2
    print(f"{r['sesiones']} sesiones · coordinación {r['gasto_usd']['coordinacion']:.2f}/"
          f"{r['limite_usd']['coordinacion']:.2f} USD · trabajo {r['gasto_usd']['trabajo']:.2f}/"
          f"{r['limite_usd']['trabajo']:.2f} USD · total {r['total_usd']:.2f}/{r['tope_total_usd']:.2f} USD")
    for e in errores:
        print(f"::error::{e}")
    if errores:
        return 1
    print("PLAN ACEPTADO")
    return 0


if __name__ == "__main__":
    sys.exit(main())
