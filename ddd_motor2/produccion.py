#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: motor 2 — P30 dentro de la cadena de producción (00 / 02, modo `motor: motor2`)
VERSIÓN: 1.2.0
NOMBRE DE VERSIÓN: P30 en producción · Deslinde como paquete
FECHA: 2026-11-14
ESTADO: candidato (solo se ejecuta con la entrada `motor: motor2`; con `m05`, por defecto, nada lo llama)
CAMBIOS: 1.2.0 — (T-257, D-88) CanonicoDelRun se mueve al paquete Deslinde (deslinde/candidatos.py) y se importa
  de allí; la huella motor2 incluye el código del paquete (paquetes/deslinde/src/deslinde/**/*.py), así que cambia
  (D-89 lo admite: mismos mapas bit a bit). Misma competición.
  1.1.2 — (T-258) el vigente del P30 es el publicado en el visor (generadores 1.2.2, vigente.py): la huella
  motor2 del P30 (P30.json «motor2») añade el vigente RESUELTO del territorio (huella_vigente: run, ruta, sha256),
  no el registro global del visor: publicar otro territorio no la cambia. La huella global (`huella`, sin
  territorio) solo cambia por ddd_motor2/vigente.py. P30.json guarda también «run» y «origen» del vigente. El
  canónico sigue siendo el del run (CanonicoDelRun).
  1.1.1 — (T-265, D-90) la huella motor2 incluye la tabla maestra (configuracion/notacion_territorial.csv) y
  su resolutor (ddd_core/territorio_ids.py): de ellos sale el código oficial de la semilla. El territorio de la
  carpeta solo sirve para resolver ese código; P30.json publica `semilla_publica` con código, derivación y sha256.
  1.1.0 — (T-223) el P30 compite como la batería desde T-217 (competir.competir_territorio): con D8 entra
  también el mapa vigente publicado (generadores.Vigente; si cumple el núcleo, la mitad de las cadenas parte de él).
  La huella motor2 incluye datos/composicion/*.csv (el vigente cambia el resultado). P30.json guarda el entorno
  (python, PYTHONHASHSEED, versiones de la comprobación de la batería, GEOS) y el vigente (estado, compite, detalle, sha256). Con otro
  seccionado el vigente no compite (generadores 1.2.1).
  `competir` desde la línea de órdenes falla cerrado sin PYTHONHASHSEED=0 (P30_ENTORNO_NO_REPRODUCIBLE, sale con 6).
  1.0.1 — (T-221) P30.json publica también `metricas.<ganador|canonico>.violaciones_duras` y
    `composicion_m06_sha256` (la composición M06 canónica con la que compitió): la certificación (estado_produccion
    --motor motor2) los exige. Nada cambia en la competición ni en huella_resultado.
  1.0.0 — fichero nuevo.
MOTIVO: 1.1.1 — T-265 / D-90 (semilla por código oficial). T-216 (corte 5.0.0, paso 3; D-75): el motor nuevo como P30 en la cadena de producción detrás de un interruptor
  `motor: m05|motor2` con `m05` por defecto hasta el relevo.
ANTERIOR: legacy/ddd_motor2/produccion_v1.1.2_20261114.py
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
USO: PYTHONHASHSEED=0 python -m ddd_motor2.produccion competir --params <contrato> [--runs-dir <run>]
     python -m ddd_motor2.produccion verificar --params <contrato> [--runs-dir <run>]
     python -m ddd_motor2.produccion huella
  Función y N: FUNCION y CADENAS (D8, 10), sin opción en la línea de órdenes: la huella motor2 del checkpoint los
  incluye, así que un M06 de otra configuración nunca se reutiliza.
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
VERSION = "1.2.0"
ESQUEMA = "ddd.p30-motor2/1.0"
FUNCION = "D8"  # única fuente de la función y N del P30: el flujo no los pasa y la huella motor2 los incluye
CADENAS = 10
# Tablas que lee la clave de naturalidad (naturalidad_mapas: partidos judiciales, comarcas agrarias, áreas de movilidad).
RESPALDO = ".m05_original"  # copia temporal de la salida M05 mientras se rehace M06 (se borra al restaurar)
DESLINDE = "paquetes/deslinde/src/deslinde"  # T-257: el código de Deslinde entra en la huella motor2
DATOS_NATURALIDAD = ("configuracion/partidos_judiciales.csv", "docs/ESTUDIOS/T64_*/comarcas_agrarias.csv",
                     "datos/movilidad/**/*",
                     "datos/composicion/*.csv",  # T-223: el mapa vigente publicado compite (generadores.Vigente)
                     "configuracion/notacion_territorial.csv",  # T-265: código oficial de la semilla (tabla maestra)
                     "ddd_core/territorio_ids.py")  # T-265: su resolutor (codigo_semilla)
# Paquetes que fija la comprobación de dependencias del P30 y de la batería (requirements.lock + cadenas del laboratorio).
PAQUETES_ENTORNO = ("numpy", "pandas", "shapely", "geopandas", "pyogrio", "pyproj", "gerrychain", "networkx",
                    "rustworkx", "scipy")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def huella_vigente(t: str, root: Path = ROOT) -> dict:
    """T-258: el vigente RESUELTO de `t` (vigente.vigente_publicado: run, ruta y sha256), no el registro global del
    visor: publicar otro territorio no cambia la huella de `t`; cambiar el mapa publicado de `t`, sí."""
    from .vigente import vigente_publicado
    v = vigente_publicado(t, root)
    return {"territorio": t, "run": v.run, "ruta": v.ruta.relative_to(root).as_posix() if v.ruta else None,
            "sha256": _sha(v.ruta.read_bytes()) if v.ruta else None, **({"motivo": v.motivo} if v.motivo else {})}


def huella_motor(funcion: str = FUNCION, cadenas: int = CADENAS, root: Path = ROOT, territorio: str | None = None) -> dict:
    """Huella del motor 2 para la capa `motor2` de compatibility/motor.json (solo en el modo motor2). Con `territorio`
    (el P30), añade el vigente publicado que compite en ese territorio (huella_vigente)."""
    ficheros = sorted(p for d in ("ddd_motor2", DESLINDE) for p in (root / d).rglob("*.py") if "__pycache__" not in p.parts)
    for patron in DATOS_NATURALIDAD:
        ficheros += sorted(p for p in root.glob(patron) if p.is_file())
    engine = {p.relative_to(root).as_posix(): _sha(p.read_bytes()) for p in ficheros}
    payload = {"motor": "motor2", "funcion": funcion, "cadenas": int(cadenas), "engine_files": engine}
    if territorio:
        payload["vigente"] = huella_vigente(territorio, root)
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


from deslinde.candidatos import CanonicoDelRun  # noqa: E402,F401  (T-257: movido a Deslinde)


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
def entorno() -> dict:
    """Lo que decide la reproducibilidad bit a bit fuera del código: intérprete, semilla de hash y versiones."""
    from importlib.metadata import PackageNotFoundError, version  # noqa: PLC0415
    out = {"python": sys.version.split()[0], "PYTHONHASHSEED": os.environ.get("PYTHONHASHSEED")}
    for m in PAQUETES_ENTORNO:
        try:
            out[m] = version(m)
        except PackageNotFoundError:
            out[m] = None
    try:
        import shapely  # noqa: PLC0415
        out["geos"] = shapely.geos_version_string
    except ImportError:
        out["geos"] = None
    return out


def generadores_por_defecto(cadena=None, vigente=None, funcion: str = FUNCION):
    """Como competir.competir_territorio (la batería): sin inyección, Ponderado y, salvo con A, el vigente publicado."""
    if cadena is None:
        from .generadores import Ponderado, Vigente  # noqa: PLC0415
        cadena = Ponderado()
        if vigente is None and funcion != "A":
            vigente = Vigente()
    return cadena, vigente


def competir(params: Path, n_cadenas: int = CADENAS, funcion: str = FUNCION, *, cadena=None,
             runs_dir: Path | None = None, vigente=None) -> dict:
    """P30 del run. `cadena` y `vigente` se pueden inyectar (pruebas); por defecto, como la batería
    (competir.competir_territorio): generadores.Ponderado() y, salvo con la función A, generadores.Vigente()."""
    import yaml  # noqa: PLC0415
    from .competicion import EntradaTerritorio, competir_publico  # noqa: PLC0415
    from .informe import escribir  # noqa: PLC0415
    from .adaptadores import columnas_de_contrato  # noqa: PLC0415
    r = _rutas(params, runs_dir)
    cfg = yaml.safe_load(Path(params).read_text(encoding="utf-8")) or {}
    t = _territorio(params)
    destino = r["runs"] / "p30_motor2"
    shutil.rmtree(destino, ignore_errors=True)
    cadena, vigente = generadores_por_defecto(cadena, vigente, funcion)
    canonico = CanonicoDelRun(r["composicion"], _secciones_m06(r["composicion"].parent))
    entrada = EntradaTerritorio(t, cfg, r["grafo"])
    res = competir_publico(entrada, canonico, cadena, destino / "competicion", n_cadenas=n_cadenas, funcion=funcion,
                           vigente=vigente)
    escribir(res, destino)
    g = res.ganador
    col = columnas_de_contrato(cfg)
    salida = {"schema": ESQUEMA, "version": VERSION, "territorio": t, "params": str(params), "funcion": funcion,
              "cadenas": int(n_cadenas), "ganador": g.id, "generador": g.generador, "valido": bool(res.valido),
              "estado_ganador": g.estado, "huella_resultado": res.huella(), "semilla_publica": res.semilla_publica,
              "motor2": huella_motor(funcion, n_cadenas, territorio=t), "candidatos": len(res.candidatos),
              "candidatos_validos": sum(c.estado == "VALIDO" for c in res.candidatos), "rehacer_m06": False,
              "secciones_cambiadas": 0, "run_id": os.environ.get("DDD_RUN_ID"), "entorno": entorno(),
              "vigente": {k: (res.vigente or {}).get(k) for k in ("estado", "compite", "detalle", "sha256_origen",
                                                                 "reparado", "run", "origen")},
              "composicion_m06_sha256": _sha(r["composicion"].read_bytes()) if r["composicion"].is_file() else None,
              "metricas": {k: {"fuera_tolerancia": c.fuera_tolerancia, "violaciones_duras": c.duras,
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
    sub.add_parser("huella")  # siempre con FUNCION y CADENAS: es la huella que entra en compatibility/motor.json
    a = ap.parse_args(argv)
    if a.orden == "huella":
        print(json.dumps(huella_motor(), indent=2))
        return 0
    if a.orden == "competir":
        if os.environ.get("PYTHONHASHSEED") != "0":  # T-223: sin ella el orden de los conjuntos cambia entre procesos
            print("::error title=P30_ENTORNO_NO_REPRODUCIBLE::el P30 exige PYTHONHASHSEED=0 (como la batería)")
            return 6
        s = competir(a.params, runs_dir=a.runs_dir)
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
