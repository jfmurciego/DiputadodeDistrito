#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: motor 2 — P30 dentro de la cadena de producción (00 / 02, modo `motor: motor2`)
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: P30 en producción · competición D8 tras el canónico del run
FECHA: 2026-11-10
ESTADO: candidato (solo se ejecuta con la entrada `motor: motor2`; con `m05`, por defecto, nada lo llama)
CAMBIOS: 1.0.0 — fichero nuevo.
MOTIVO: T-216 (corte 5.0.0, paso 3; D-75): el motor nuevo como P30 en la cadena de producción detrás de un interruptor
  `motor: m05|motor2` con `m05` por defecto hasta el relevo.
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE (en el job M06 de la generación territorial, tras M04 + M05 canónico + M06 del propio run):
  competir   competición pública del motor 2 (competicion.competir_publico, la de la batería T-208): el canónico es el
             M06 que acaba de producir el run (mismas entradas M01-M03, M04, M05 canónico; no se recalcula), compite con
             N cadenas «ponderado» (generadores.Ponderado, semillas públicas de semilla.py) y el exhaustivo si el
             territorio es pequeño, y gana el mejor por la función D8. Escribe en <runs>/p30_motor2/: COMPETICION.{json,md}
             y P30.json (ganador, validez, huella del resultado, función, N, huella del motor 2). Si el ganador no es el
             canónico, reescribe el distrito de cada sección en la entrada de M06 (la salida M05) con el plan ganador
             (stdlib: geometrías y demás propiedades intactas; etiquetas 1..K emparejadas con las del canónico por
             máxima población común) y sale con 0 y `rehacer_m06=true`: el flujo vuelve a ejecutar M06. Antes guarda la
             salida M05 original (sha256 en P30.json): M05 es el competidor canónico y su linaje no cambia.
             Sin ganador válido: P30_SIN_GANADOR_VALIDO, sale con 3 (falla cerrado; nunca se publica un plan inválido).
  verificar  tras rehacer M06: la composición M06 nueva es la partición del ganador (mismas etiquetas); si no,
             P30_M06_NO_ES_EL_GANADOR y sale con 4. Después restaura byte a byte la salida M05 original (la evidencia M05
             —report.output.sha256, portfolio de GerryChain 50— sigue cuadrando); si su sha256 no vuelve a ser el
             guardado, P30_M05_NO_RESTAURADA y sale con 5.
  huella     huella del motor 2 (sha256 de ddd_motor2/**/*.py y de las tablas de naturalidad que lee, función y N) para
             compatibility/motor.json (herramientas/huella_checkpoint_motor.py, capa `motor2`).
NO HACE: tocar M04/M05/M06 ni ddd_core; decidir el relevo; lanzar nada.
USO: PYTHONHASHSEED=0 python -m ddd_motor2.produccion competir --params <contrato> [--cadenas 10] [--funcion D8]
     python -m ddd_motor2.produccion verificar --params <contrato>
     python -m ddd_motor2.produccion huella [--cadenas 10] [--funcion D8]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import sys
import zipfile
from pathlib import Path
from typing import Mapping

ROOT = Path(__file__).resolve().parents[1]
VERSION = "1.0.0"
ESQUEMA = "ddd.p30-motor2/1.0"
FUNCION = "D8"
CADENAS = 10
# Tablas que lee la clave de naturalidad (naturalidad_mapas: partidos judiciales, comarcas agrarias, áreas de movilidad).
RESPALDO = ".m05_original"  # copia temporal de la salida M05 mientras se rehace M06 (se borra al restaurar)
DATOS_NATURALIDAD = ("configuracion/partidos_judiciales.csv", "docs/ESTUDIOS/T64_*/comarcas_agrarias.csv",
                     "datos/movilidad/**/*")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def huella_motor(funcion: str = FUNCION, cadenas: int = CADENAS, root: Path = ROOT) -> dict:
    """Huella del motor 2 para la capa `motor2` de compatibility/motor.json (solo en el modo motor2)."""
    ficheros = sorted(p for p in (root / "ddd_motor2").rglob("*.py") if "__pycache__" not in p.parts)
    for patron in DATOS_NATURALIDAD:
        ficheros += sorted(p for p in root.glob(patron) if p.is_file())
    engine = {p.relative_to(root).as_posix(): _sha(p.read_bytes()) for p in ficheros}
    payload = {"motor": "motor2", "funcion": funcion, "cadenas": int(cadenas), "engine_files": engine}
    payload["fingerprint"] = _sha(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    return payload


# --------------------------------------------------------------------------- rutas del contrato
def _territorio(params: Path) -> str:
    partes = Path(params).as_posix().split("/")
    if "territorios" in partes and partes.index("territorios") + 1 < len(partes):
        return partes[partes.index("territorios") + 1]
    return Path(params).stem


def _rutas(params: Path, runs_dir: Path | None = None) -> dict:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from ddd_core.config import load_params_yaml, module_cfg  # noqa: PLC0415  (solo lectura de rutas)
    cfg = load_params_yaml(str(params))
    s3 = module_cfg(cfg, "modulo_03_construir_grafo", "step3_build_graph")
    s6 = module_cfg(cfg, "modulo_06_consolidar_distritos", "step6_export_final")
    io_cfg = cfg.get("io") or {}
    runs = str(((io_cfg.get("runs") or {}).get("dir") or "ejecuciones/{run_id}"))
    meta = cfg.get("meta") or {}
    runs = runs.format(run_name=meta.get("run_name", Path(params).stem), run_id=os.environ.get("DDD_RUN_ID", "local"),
                       year=meta.get("year", ""))
    return {"grafo": Path(s3["out_graph_json"]), "in_m06": Path(s6["in_geojson"]),
            "composicion": Path(s6["out_composition_csv"]), "id": str(s6["id_field"]),
            "distrito": str(s6["district_field"]), "runs": Path(runs_dir) if runs_dir else Path(runs)}


def _secciones_m06(cache: Path) -> Path | None:
    geos = sorted(cache.glob("*_m06_secciones.geojson.zip")) or sorted(cache.glob("*_m06_secciones.geojson"))
    return geos[0] if geos else None


class CanonicoDelRun:
    """El canónico es el M06 que el run acaba de producir (M04 + M05 canónico + M06 de producción): no se recalcula."""

    nombre = "canonico"

    def __init__(self, composicion: Path, atributos: Path | None):
        self.composicion, self.atributos = Path(composicion), atributos

    def generar(self, entrada, semilla, destino: Path):
        from .competicion import Salida  # noqa: PLC0415
        destino = Path(destino)
        destino.mkdir(parents=True, exist_ok=True)
        if not self.composicion.is_file():
            return Salida(None, "SIN_M06", f"sin composición M06 del run ({self.composicion})")
        copia = destino / self.composicion.name
        shutil.copy2(self.composicion, copia)
        atr = None
        if self.atributos is not None and self.atributos.is_file():
            atr = destino / self.atributos.name
            shutil.copy2(self.atributos, atr)
        return Salida(copia, "OK", atributos_secciones=atr, extra={"origen": "M06 del run"})


# --------------------------------------------------------------------------- particiones
def _particion_csv(ruta: Path, col_sec: str, col_dis: str) -> dict[str, str]:
    with open(ruta, encoding="utf-8", newline="") as fh:
        return {str(f[col_sec]).strip(): str(f[col_dis]).strip() for f in csv.DictReader(fh)}


def _grupos(asig: Mapping[str, str]) -> set[frozenset]:
    g: dict[str, set] = {}
    for s, d in asig.items():
        g.setdefault(d, set()).add(s)
    return {frozenset(v) for v in g.values()}


def etiquetas(ganador: Mapping[str, str], canonico: Mapping[str, str], pob: Mapping[str, int]) -> dict[str, int]:
    """Etiqueta del ganador → id de distrito 1..K: emparejamiento voraz por máxima población común con el canónico
    (determinista: empates por etiqueta); los que sobran, en orden de su sección menor con los ids libres."""
    comun: dict[tuple[str, str], int] = {}
    for s, dg in ganador.items():
        dc = canonico.get(s)
        if dc is not None:
            comun[(dg, dc)] = comun.get((dg, dc), 0) + int(pob.get(s, 0)) + 1
    ids_can = sorted({int(d) for d in canonico.values()})
    asign: dict[str, int] = {}
    usados: set[int] = set()
    for (dg, dc), _ in sorted(comun.items(), key=lambda kv: (-kv[1], kv[0])):
        if dg not in asign and int(dc) not in usados:
            asign[dg] = int(dc)
            usados.add(int(dc))
    menor: dict[str, str] = {}
    for s, d in ganador.items():
        menor[d] = min(menor.get(d, s), s)
    libres = [i for i in ids_can if i not in usados] + [i for i in range(1, len(menor) + 1)
                                                         if i not in usados and i not in ids_can]
    for d in sorted((d for d in menor if d not in asign), key=menor.get):
        asign[d] = libres.pop(0)
    return asign


def _leer_geojson(ruta: Path) -> tuple[dict, str | None]:
    if ruta.name.lower().endswith(".zip"):
        with zipfile.ZipFile(ruta) as zf:
            nombre = next(n for n in zf.namelist() if n.lower().endswith((".geojson", ".json")) and not n.endswith("/"))
            return json.loads(zf.read(nombre).decode("utf-8")), nombre
    return json.loads(ruta.read_text(encoding="utf-8")), None


def _escribir_geojson(ruta: Path, datos: dict, miembro: str | None) -> None:
    texto = json.dumps(datos, ensure_ascii=False).encode("utf-8")
    tmp = ruta.with_name(ruta.name + ".tmp")
    if miembro is None:
        tmp.write_bytes(texto)
    else:
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(miembro, texto)
    tmp.replace(ruta)


def reescribir_entrada_m06(ruta: Path, campo_id: str, campo_distrito: str, plan: Mapping[str, int]) -> int:
    """Pone en la entrada de M06 el distrito del plan ganador; devuelve cuántas secciones cambian."""
    datos, miembro = _leer_geojson(ruta)
    feats = datos.get("features") or []
    ids = {str((f.get("properties") or {}).get(campo_id)) for f in feats}
    if ids != set(plan):
        raise ValueError(f"P30_SECCIONES_DISTINTAS: la entrada de M06 y el ganador no tienen las mismas secciones "
                         f"({len(ids - set(plan))} sin plan, {len(set(plan) - ids)} de más)")
    cambios = 0
    for f in feats:
        p = f["properties"]
        nuevo = int(plan[str(p[campo_id])])
        cambios += int(p[campo_distrito]) != nuevo
        p[campo_distrito] = nuevo
    _escribir_geojson(ruta, datos, miembro)
    return cambios


# --------------------------------------------------------------------------- subcomandos
def competir(params: Path, n_cadenas: int = CADENAS, funcion: str = FUNCION, *, cadena=None,
             runs_dir: Path | None = None) -> dict:
    """P30 del run. `cadena` se puede inyectar (pruebas); por defecto, generadores.Ponderado()."""
    import yaml  # noqa: PLC0415
    from .competicion import EntradaTerritorio, competir_publico  # noqa: PLC0415
    from .informe import escribir  # noqa: PLC0415
    from .adaptadores import columnas_de_contrato  # noqa: PLC0415
    r = _rutas(params, runs_dir)
    cfg = yaml.safe_load(Path(params).read_text(encoding="utf-8")) or {}
    t = _territorio(params)
    destino = r["runs"] / "p30_motor2"
    shutil.rmtree(destino, ignore_errors=True)
    if cadena is None:
        from .generadores import Ponderado  # noqa: PLC0415
        cadena = Ponderado()
    canonico = CanonicoDelRun(r["composicion"], _secciones_m06(r["composicion"].parent))
    entrada = EntradaTerritorio(t, cfg, r["grafo"])
    res = competir_publico(entrada, canonico, cadena, destino / "competicion", n_cadenas=n_cadenas, funcion=funcion)
    escribir(res, destino)
    g = res.ganador
    col = columnas_de_contrato(cfg)
    salida = {"schema": ESQUEMA, "version": VERSION, "territorio": t, "params": str(params), "funcion": funcion,
              "cadenas": int(n_cadenas), "ganador": g.id, "generador": g.generador, "valido": bool(res.valido),
              "estado_ganador": g.estado, "huella_resultado": res.huella(), "semilla_publica": res.semilla_publica,
              "motor2": huella_motor(funcion, n_cadenas), "candidatos": len(res.candidatos),
              "candidatos_validos": sum(c.estado == "VALIDO" for c in res.candidatos), "rehacer_m06": False,
              "secciones_cambiadas": 0, "run_id": os.environ.get("DDD_RUN_ID"),
              "metricas": {k: {"fuera_tolerancia": c.fuera_tolerancia,
                               "desvio_max": None if c.desvio_max is None else float(c.desvio_max)}
                           for k, c in (("ganador", g), ("canonico", res.canonico))}}
    if not res.valido:
        salida["estado"] = "P30_SIN_GANADOR_VALIDO"
    elif g.id == res.canonico.id:
        salida["estado"] = "P30_GANA_CANONICO"
    else:
        comp_g = Path(g.composicion)
        plan_g = _particion_csv(comp_g, col["seccion"], col["distrito"])
        with open(r["composicion"], encoding="utf-8", newline="") as fh:
            filas = list(csv.DictReader(fh))
        plan_c = {str(f[col["seccion"]]).strip(): str(f[col["distrito"]]).strip() for f in filas}
        pob = {str(f[col["seccion"]]).strip(): int(f.get(col["poblacion"]) or 0) for f in filas}
        et = etiquetas(plan_g, plan_c, pob)
        plan = {s: et[d] for s, d in plan_g.items()}
        respaldo = destino / RESPALDO / r["in_m06"].name
        respaldo.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(r["in_m06"], respaldo)
        salida["m05_salida"] = {"ruta": str(r["in_m06"]), "sha256": _sha(r["in_m06"].read_bytes())}
        salida["secciones_cambiadas"] = reescribir_entrada_m06(r["in_m06"], r["id"], r["distrito"], plan)
        (destino / "PLAN_GANADOR.json").write_text(json.dumps(plan, sort_keys=True) + "\n", encoding="utf-8")
        salida.update(estado="P30_GANA_OTRO_PLAN", rehacer_m06=True)
    (destino / "P30.json").write_text(json.dumps(salida, ensure_ascii=False, indent=2, default=str) + "\n",
                                      encoding="utf-8")
    return salida


def verificar(params: Path, runs_dir: Path | None = None) -> dict:
    import yaml  # noqa: PLC0415
    from .adaptadores import columnas_de_contrato  # noqa: PLC0415
    r = _rutas(params, runs_dir)
    col = columnas_de_contrato(yaml.safe_load(Path(params).read_text(encoding="utf-8")) or {})
    p30 = json.loads((r["runs"] / "p30_motor2" / "P30.json").read_text(encoding="utf-8"))
    plan = json.loads((r["runs"] / "p30_motor2" / "PLAN_GANADOR.json").read_text(encoding="utf-8"))
    m06 = _particion_csv(r["composicion"], col["seccion"], col["distrito"])
    ok = m06 == {s: str(d) for s, d in plan.items()}
    p30["verificacion_m06"] = {"igual_al_ganador": ok, "composicion": str(r["composicion"]),
                               "composicion_sha256": _sha(r["composicion"].read_bytes())}
    respaldo = r["runs"] / "p30_motor2" / RESPALDO / r["in_m06"].name
    if respaldo.is_file():
        shutil.copy2(respaldo, r["in_m06"])
        shutil.rmtree(respaldo.parent)
    esperado = (p30.get("m05_salida") or {}).get("sha256")
    p30["m05_restaurada"] = bool(esperado) and _sha(r["in_m06"].read_bytes()) == esperado
    (r["runs"] / "p30_motor2" / "P30.json").write_text(json.dumps(p30, ensure_ascii=False, indent=2, default=str) + "\n",
                                                       encoding="utf-8")
    return p30


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[3])
    sub = ap.add_subparsers(dest="orden", required=True)
    for nombre in ("competir", "verificar"):
        p = sub.add_parser(nombre)
        p.add_argument("--params", required=True, type=Path)
        p.add_argument("--runs-dir", type=Path, help="carpeta del run (RUNS_DIR del flujo); por defecto, la del contrato")
    for p in (sub.choices["competir"], sub.add_parser("huella")):
        p.add_argument("--cadenas", type=int, default=CADENAS)
        p.add_argument("--funcion", default=FUNCION)
    a = ap.parse_args(argv)
    if a.orden == "huella":
        print(json.dumps(huella_motor(a.funcion, a.cadenas), indent=2))
        return 0
    if a.orden == "competir":
        s = competir(a.params, a.cadenas, a.funcion, runs_dir=a.runs_dir)
        print(f"P30 {s['territorio']}: {s['estado']} ganador={s['ganador']} válido={s['valido']} "
              f"candidatos válidos={s['candidatos_validos']}/{s['candidatos']} huella={s['huella_resultado']} "
              f"secciones cambiadas={s['secciones_cambiadas']} rehacer_m06={str(s['rehacer_m06']).lower()}")
        if s["estado"] == "P30_SIN_GANADOR_VALIDO":
            print("::error title=P30_SIN_GANADOR_VALIDO::el motor 2 no tiene ganador válido; no se rehace M06")
            return 3
        return 0
    v = verificar(a.params, a.runs_dir)
    print(f"P30 verificación M06: igual al ganador={v['verificacion_m06']['igual_al_ganador']}")
    if not v["verificacion_m06"]["igual_al_ganador"]:
        print("::error title=P30_M06_NO_ES_EL_GANADOR::la composición M06 rehecha no es la partición del ganador")
        return 4
    print(f"P30 salida M05 restaurada (sha256 original): {v['m05_restaurada']}")
    if not v["m05_restaurada"]:
        print("::error title=P30_M05_NO_RESTAURADA::la salida M05 no vuelve a su sha256 original")
        return 5
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
