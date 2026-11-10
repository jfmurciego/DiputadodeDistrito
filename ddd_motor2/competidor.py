#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: motor 2 — la competición como sustituto de M05 (interfaz acordada con la batería T-132)
VERSIÓN: 1.2.0
NOMBRE DE VERSIÓN: Competición · núcleos desde el M04
FECHA: 2026-11-10
ESTADO: candidato (motor 2; producción no lo importa; no lanza nada en Actions)
CAMBIOS: 1.2.0 — R-NUCLEO se juzga contra el distrito inicial del M04 (modulo_05.in_geojson: district_id +
  ddd_closed_urban), como el certificador y frozen_districts de GerryChain, no contra la composición del canónico:
  un plan que rompe un núcleo se descarta aunque el canónico lo rompiera. Sin district_id en el M04, la referencia
  vuelve a ser la del canónico.
  1.1.0 — la competición incluye el candidato «exhaustivo» (enumeración exacta en territorios pequeños,
  competicion 1.2.0); si gana, su M05 es el GeoJSON M05 del canónico con district_id reescrito por sección según la
  composición del exhaustivo (sin informe M05: se borra out_report); --sin-exhaustivo lo quita.
  1.0.1 — si el ganador no trae informe M05, se borra out_report (no queda el del último candidato);
  1.0.0 — fichero nuevo.
MOTIVO: 1.2.0 — T-195: misma regla de núcleos que el certificador (T-175) al generar y descartar planes.
MOTIVO: 1.1.0 — T-175: enumeración exacta en el competidor del motor nuevo.
  T-163 / D-48: que el banco de la batería (herramientas/banco_generadores.py, generador «competidor») juzgue la
  competición igual que cualquier otro generador: la batería hace unidades + M04, llama a esta orden en lugar de M05 y
  después M06, validación de producción, núcleo y calidad.
ANTERIOR: legacy/ddd_motor2/competidor_v1.1.0_20261110.py
USO: DDD_RUN_ID=<id> PYTHONHASHSEED=0 python -m ddd_motor2.competidor --params territorios/<t>/config/<t>_2025.yaml \
       --run-id <id> [--semilla <n>] [--cadenas 5] [--territorio <t>]
  Lee lo mismo que M05 (modulo_05: in_graph_json, in_geojson = M04) y deja en modulo_05.out_geojson y out_report el
  M05 del candidato ganador. Por cada candidato: M05 (canónico: modulos/05_optimizar_distritos.py; GerryChain:
  ddd_core/m05_gerrychain_strategy.py --seed-count 1 --seed-base <semilla pública>, desde la semilla canónica si la
  Formación M04 no es admisible, como producción) y M06 para obtener la composición que juzga el núcleo.
  --semilla se ignora: las semillas son las públicas del territorio (ddd_motor2/semilla.py); se acepta por la firma
  común del banco. El informe de la competición va a <carpeta de out_geojson>/competicion/COMPETICION.{json,md}.
  rc 0 si dejó salida (aunque el ganador no sea válido: la batería valida); 2 si ningún candidato es evaluable (sin plan,
  o ERROR_DATOS/ERROR_CONTRATO en todos; borra out_geojson y out_report); 3 si el contrato no trae el ancla.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GC_PY = os.environ.get("DDD_GERRYCHAIN_PYTHON", "/opt/ddd-gerrychain/bin/python")

from .competicion import EntradaTerritorio, Salida, competir_publico  # noqa: E402
from .informe import escribir  # noqa: E402
from .reglas import ErrorContrato  # noqa: E402


def rutas(params: str, run_id: str) -> tuple[dict, dict, dict]:
    os.environ["DDD_RUN_ID"] = run_id
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from ddd_core.config import load_params_yaml, module_cfg
    cfg = load_params_yaml(params)
    return (cfg, module_cfg(cfg, "modulo_05_optimizar_distritos", "step5_optimize"),
            module_cfg(cfg, "modulo_06_consolidar_distritos", "step6_export_final"))


class _Paso:
    """Ejecuta M05 (orden dada) + M06 dentro del run y guarda las salidas del candidato en su carpeta."""

    def __init__(self, params: str, run_id: str, s5: dict, s6: dict, log: Path):
        self.params, self.run_id, self.s5, self.s6, self.log = params, run_id, s5, s6, log
        self.env = dict(os.environ, DDD_RUN_ID=run_id, PYTHONHASHSEED="0")

    def run(self, cmd: list[str]) -> int:
        with open(self.log, "a", encoding="utf-8") as fh:
            fh.write(f"$ {' '.join(cmd)}\n")
            fh.flush()
            return subprocess.run(cmd, cwd=ROOT, stdout=fh, stderr=subprocess.STDOUT, env=self.env).returncode

    def m05_y_m06(self, cmd: list[str], destino: Path, extra: dict) -> Salida:
        destino.mkdir(parents=True, exist_ok=True)
        out5, rep5 = Path(self.s5["out_geojson"]), Path(self.s5["out_report"])
        for f in (out5, rep5):
            f.unlink(missing_ok=True)
        rc = self.run(cmd)
        if rc != 0 or not out5.is_file():
            return Salida(None, f"FALLO_M05_rc{rc}", f"M05 rc={rc}", extra=extra)
        shutil.copy2(out5, destino / out5.name)
        if rep5.is_file():
            shutil.copy2(rep5, destino / rep5.name)
        rc = self.run([sys.executable, "modulos/06_consolidar_distritos.py", "--params", self.params])
        comp, geo = Path(self.s6["out_composition_csv"]), Path(self.s6["out_geojson"])
        if rc != 0 or not comp.is_file():
            return Salida(None, f"FALLO_M06_rc{rc}", f"M06 rc={rc}", extra=extra)
        shutil.copy2(comp, destino / comp.name)
        atr = None
        if geo.is_file():
            atr = destino / geo.name
            shutil.copy2(geo, atr)
        return Salida(destino / comp.name, "OK", atributos_secciones=atr, extra=extra)


class CanonicoM05:
    nombre = "canonico"

    def __init__(self, paso: _Paso):
        self.paso = paso
        self.m05: Path | None = None  # semilla canónica para GerryChain si M04 no es admisible

    def generar(self, entrada, semilla, destino):
        sal = self.paso.m05_y_m06([sys.executable, "modulos/05_optimizar_distritos.py", "--params", self.paso.params],
                                  Path(destino), {})
        if sal.composicion is not None:
            self.m05 = Path(destino) / Path(self.paso.s5["out_geojson"]).name
        return sal


class GerryChainM05:
    nombre = "gerrychain"

    def __init__(self, paso: _Paso, canonico: CanonicoM05):
        self.paso, self.canonico = paso, canonico
        self.m04_admisible: bool | None = None

    def generar(self, entrada, semilla, destino):
        base = [GC_PY, "ddd_core/m05_gerrychain_strategy.py", "--params", self.paso.params, "--run-id", self.paso.run_id]
        if self.m04_admisible is None:
            self.m04_admisible = self.paso.run(base + ["--validate-baseline-only", "--seed-count", "1"]) == 0
        inicial: list[str] = []
        extra = {"m04_admisible": self.m04_admisible}
        if not self.m04_admisible:
            if self.canonico.m05 is None:
                return Salida(None, "SIN_SEMILLA", "M04 no admisible y el canónico no dio semilla", extra=extra)
            inicial = ["--initial", str(self.canonico.m05)]
            extra["semilla_inicial"] = "canonica"
        return self.paso.m05_y_m06(base + ["--seed-count", "1", "--seed-base", str(int(semilla))] + inicial,
                                   Path(destino), extra)


def m05_desde_composicion(base_m05: Path, composicion: Path, destino: Path, s6: dict) -> Path:
    """GeoJSON M05 con el plan de una composición M06 (mismas secciones): district_id reescrito por sección."""
    import csv
    from ddd_core.m05_swap_polish import load_geo, write_geo
    idf = str(s6.get("id_field", "CUSEC_KEY"))
    with open(composicion, encoding="utf-8", newline="") as fh:
        rd = csv.DictReader(fh)
        sid = idf if idf in (rd.fieldnames or []) else "CUSEC_KEY"
        dist = {str(r[sid]).strip(): int(r["district_id"]) for r in rd}
    g = load_geo(base_m05)
    claves = g[idf].astype(str).str.strip()
    faltan = sorted(set(claves) - set(dist))
    if faltan:
        raise ValueError(f"la composición no asigna {len(faltan)} secciones del M05 (p. ej. {faltan[0]})")
    g["district_id"] = claves.map(dist).astype("int64")
    write_geo(g, destino)
    return destino


def referencia_m04(s5: dict, cfg: dict, carpeta: Path) -> Path | None:
    """Referencia de núcleos = distrito inicial del M04 (T-195); None si el M04 no lo trae (se usa el canónico)."""
    from .adaptadores import referencia_desde_m04
    from .reglas import ErrorDatos
    m04 = s5.get("in_geojson")
    if not m04 or not Path(m04).is_file():
        return None
    try:
        return referencia_desde_m04(m04, carpeta / "referencia_nucleos_m04.csv", cfg)
    except (ErrorDatos, OSError, ValueError):
        return None


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="python -m ddd_motor2.competidor",
                                 description="Competición canónico + GerryChain en lugar de M05 (T-163).")
    ap.add_argument("--params", required=True)
    ap.add_argument("--run-id", default=os.environ.get("DDD_RUN_ID", ""))
    ap.add_argument("--semilla", type=int, help="ignorada: semillas públicas del territorio")
    ap.add_argument("--cadenas", type=int, default=5)
    ap.add_argument("--territorio", help="por defecto, el directorio territorios/<t>/ del contrato")
    ap.add_argument("--sin-exhaustivo", action="store_true", help="sin enumeración exacta (solo canónico + cadenas)")
    return ap


def territorio_de(params: Path) -> str:
    return params.parts[params.parts.index("territorios") + 1] if "territorios" in params.parts \
        else params.stem.rsplit("_", 1)[0]


def main(argv=None) -> int:
    ap = parser()
    a = ap.parse_args(argv)
    if not a.run_id:
        ap.error("falta --run-id (o DDD_RUN_ID)")
    params = Path(a.params)
    t = a.territorio or territorio_de(params)
    cfg, s5, s6 = rutas(str(params), a.run_id)
    carpeta = Path(s5["out_geojson"]).parent / "competicion"
    shutil.rmtree(carpeta, ignore_errors=True)
    carpeta.mkdir(parents=True)
    paso = _Paso(str(params), a.run_id, s5, s6, carpeta / "log.txt")
    can = CanonicoM05(paso)
    entrada = EntradaTerritorio(t, cfg, Path(s5["in_graph_json"]),
                                referencia_nucleos=referencia_m04(s5, cfg, carpeta))
    try:
        r = competir_publico(entrada, can, GerryChainM05(paso, can), carpeta, n_cadenas=a.cadenas,
                             exhaustivo=not a.sin_exhaustivo)
    except ErrorContrato as exc:
        print(f"ERROR_CONTRATO: {exc}", file=sys.stderr)
        return 3
    escribir(r, carpeta)
    g = r.ganador
    if not g.evaluable:  # nadie con plan juzgable (fallo de generador o ErrorDatos/ErrorContrato en todos)
        for clave in ("out_geojson", "out_report"):  # no dejar a la batería el M05 del último candidato
            Path(s5[clave]).unlink(missing_ok=True)
        print(f"ningún candidato evaluable (ganador {g.id}: {g.estado})", file=sys.stderr)
        return 2
    d = Path(g.composicion).parent
    if g.id == "exhaustivo":  # sin M05 propio: el del canónico con el plan del exhaustivo
        if can.m05 is None:
            print("ganador exhaustivo sin M05 del canónico de base", file=sys.stderr)
            return 2
        m05_desde_composicion(can.m05, Path(g.composicion), d / Path(s5["out_geojson"]).name, s6)
    for clave in ("out_geojson", "out_report"):
        f = d / Path(s5[clave]).name
        if f.is_file():
            shutil.copy2(f, s5[clave])
        else:  # sin informe del ganador: no dejar el del último candidato
            Path(s5[clave]).unlink(missing_ok=True)
    # rc 0 aunque el ganador no sea válido: hay salida y la batería la valida (M06 + validar_ejecucion + núcleo).
    print(f"ganador={g.id} estado={g.estado} valido={r.valido} huella_resultado={r.huella()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
