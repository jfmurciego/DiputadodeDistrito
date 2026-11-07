#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archivo en origen: el propio run guarda en R2 su M06/M08 y en git la composición y los votos por partido (T-72).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.2
NOMBRE DE VERSIÓN: Archivo en origen
FECHA: 2026-11-07
ESTADO: candidato
CAMBIOS: 1.0.2 (T-90): composicion y partidos leen también los GeoJSON *.geojson.zip del estado (así los escriben
  M06 y M08; antes solo veían *.geojson sueltos).
  1.0.1 (T-72b): r2 sube el paquete mínimo y no el ZIP de estado (R2 total ≤ 8 GB); --extra; --sustituye-m06-run (el M08 acumulativo retira su M06 de R2) y el check acepta el M08
  que contiene el M06 publicado.
ANTERIOR: legacy/herramientas/archivo_origen_v1.0.1_20261107.py
QUÉ HACE: cuatro subcomandos.
  r2          sube a R2 el paquete mínimo (``ddd-minimo-<run>-M06``/M08: GeoJSON distritales, CSV/JSON de M06-M08,
              VALIDACION, manifiestos y ``--extra``; herramientas/archivar_artefactos_r2.empaquetar_minimo) del
              estado ``ddd-state-<run>-M06`` (o M08) del run en curso con sha256 y lo anota en
              orchestracion/archivo_r2.json (núcleo y clientes de herramientas/archivar_artefactos_r2.py, con sus
              reintentos). Si la copia falla, sale con 1 y ``::error::ARCHIVO_R2_FAILED``: el run no queda verde.
              Con ``--sustituye-m06-run R`` (tras M08): el estado M08 es acumulativo (lleva cache/run del M06), así que
              anota ``incluye_m06_run: R`` en la entrada M08 y retira de R2 y del manifiesto el M06 del run R
              (R2 bajo 10 GB, decisión del propietario). Si la retirada falla, solo avisa.
  composicion toma ``*_m06_composicion_distritos.csv`` del estado M06 descargado, lo valida contra el GeoJSON M06 del
              mismo estado (validación de herramientas/composicion_m06.py) y escribe
              datos/composicion/runs/<territorio>_<run>.csv (seccion, distrito, poblacion) y la clave ``runs`` de
              datos/composicion/MANIFEST.json. No toca datos/composicion/<territorio>.csv, que es la del M06 publicado.
  partidos    tras M08: votos por partido y distrito (herramientas/resultados_partidos.agregar) con la composición del
              run territorial y los ganadores del GeoJSON M08 del estado; escribe
              datos/resultados/runs/<territorio>_<run>_partidos.csv y la clave ``partidos_runs`` de
              datos/resultados/MANIFEST.json. Sin contrato Infoelectoral 2023 o sin composición del run territorial,
              lo omite con aviso (sale 0).
  comprobar   check de CI: cada territorio con canonical_m06 en orchestracion/publicaciones_visor.json (run más reciente)
              debe tener copia M06 de ese run en R2 o su composición en git; las excepciones viven en
              configuracion/excepciones_archivo_origen.json (las vacía T-71).
MOTIVO: los artefactos de Actions caducan a los 14 días y el archivista llegó tarde a los 49 M06 provinciales.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import archivar_artefactos_r2 as ar  # noqa: E402
import composicion_m06 as cm  # noqa: E402

COMPOSICION = Path("datos/composicion")
RESULTADOS = Path("datos/resultados")
EXCEPCIONES = Path("configuracion/excepciones_archivo_origen.json")


def _json(ruta: Path, defecto: dict) -> dict:
    return json.loads(ruta.read_text(encoding="utf-8")) if ruta.is_file() else defecto


def _escribir(ruta: Path, datos: dict) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    texto = json.dumps(datos, ensure_ascii=False, indent=1) + "\n"
    if not ruta.is_file() or ruta.read_text(encoding="utf-8") != texto:
        ruta.write_text(texto, encoding="utf-8")


# --- r2 --------------------------------------------------------------------------------------------

def archivar_uno(artefacto: dict, territorio: str, root: Path, descargar, r2_sha, r2_subir, bucket: str,
                 empaquetar=None) -> dict:
    """Archiva un artefacto concreto con el núcleo del archivista (con ``empaquetar``, su paquete mínimo);
    ValueError si no queda en R2."""
    man = ar.cargar_manifiesto(root / ar.MANIFIESTO)
    res = ar.archivar([artefacto], {artefacto["name"]: territorio}, {}, man, descargar, r2_sha, r2_subir, bucket,
                      empaquetar=empaquetar)
    if res["errores"]:
        raise ValueError("; ".join(res["errores"]))
    k = ar.clave({**artefacto, "territorio": ar._slug(territorio), "run": str(artefacto["workflow_run"]["id"])},
                 empaquetar is not None and artefacto["name"].startswith("ddd-state-"))
    if k not in man["artefactos"]:
        raise ValueError(f"{artefacto['name']}: no quedó anotado en el manifiesto")
    ar.guardar_manifiesto(root / ar.MANIFIESTO, man)
    return man["artefactos"][k]


def retirar_m06(run_m06: str, clave_m08: str, root: Path, r2_borrar) -> list[str]:
    """Marca el M08 como contenedor del M06 del run y retira esas copias M06; devuelve las claves retiradas."""
    ruta = root / ar.MANIFIESTO
    man = ar.cargar_manifiesto(ruta)
    man["artefactos"][clave_m08]["incluye_m06_run"] = str(run_m06)
    retiradas = []
    for k, e in list(man["artefactos"].items()):
        if str(e.get("run_id")) == str(run_m06) and ar._FINAL.match(str(e.get("artefacto", ""))) \
                and ar._FINAL.match(e["artefacto"]).group(2) == "6":
            try:
                r2_borrar(k)
            except Exception as exc:  # noqa: BLE001 - ocupa espacio, pero no pierde datos
                print(f"::warning::No se pudo retirar {k} de R2: {exc}")
                continue
            del man["artefactos"][k]
            retiradas.append(k)
    ar.guardar_manifiesto(ruta, man)
    return retiradas


def r2_borrador(bucket: str, cuenta: str):
    ep = f"https://{cuenta}.r2.cloudflarestorage.com"

    def borrar(k: str) -> None:
        ar.con_reintentos(lambda: ar.subprocess.run(
            ["aws", "s3", "rm", f"s3://{bucket}/{k}", "--endpoint-url", ep, "--only-show-errors"], check=True),
            f"R2 borrado {k}")
    return borrar


def cmd_r2(a) -> int:
    root = Path(a.root_dir)
    repo, token = os.environ.get("GITHUB_REPOSITORY", ""), os.environ.get("GITHUB_TOKEN", "")
    bucket, cuenta = os.environ.get("R2_BUCKET", ""), os.environ.get("R2_ACCOUNT_ID", "")
    faltan = [n for n, v in (("GITHUB_REPOSITORY", repo), ("GITHUB_TOKEN", token), ("R2_BUCKET", bucket),
                             ("R2_ACCOUNT_ID", cuenta), ("AWS_ACCESS_KEY_ID", os.environ.get("AWS_ACCESS_KEY_ID")),
                             ("AWS_SECRET_ACCESS_KEY", os.environ.get("AWS_SECRET_ACCESS_KEY"))) if not v]
    if faltan:
        print(f"::error title=ARCHIVO_R2_FAILED::Faltan {', '.join(faltan)}; {a.artefacto} no se archiva en R2.")
        return 1
    try:
        lote = ar._gh_json(f"https://api.github.com/repos/{repo}/actions/runs/{a.run_id}/artifacts?per_page=100", token)
        cand = [x for x in lote.get("artifacts", []) if x.get("name") == a.artefacto and not x.get("expired")]
        if len(cand) != 1:
            raise ValueError(f"esperado un artefacto {a.artefacto} en el run {a.run_id}, hay {len(cand)}")
        art = {**cand[0], "workflow_run": {"id": int(a.run_id)}}
        sha, subir = ar.r2_cliente(bucket, cuenta)
        e = archivar_uno(art, a.territorio, root, ar.descargar_gh(repo, token), sha, subir, bucket,
                         empaquetar=ar.empaquetar_minimo(tuple(a.extra)))
    except Exception as exc:  # noqa: BLE001 - el paso debe fallar con mensaje claro
        print(f"::error title=ARCHIVO_R2_FAILED::{a.artefacto}: {exc}")
        return 1
    print(f"R2: {e['url']} sha256={e['sha256']} paquete={e['tamano_bytes']} B "
          f"estado_original={e.get('tamano_estado_original')} B sha256_estado={e.get('sha256_estado_original')}")
    if a.sustituye_m06_run:
        k = e["url"].split("/", 3)[3]
        for r in retirar_m06(a.sustituye_m06_run, k, root, r2_borrador(bucket, cuenta)):
            print(f"R2: retirado {r} (contenido en {k})")
    return 0


# --- composicion -----------------------------------------------------------------------------------

def _geojsons(estado: Path, campos: tuple[str, ...]):
    """GeoJSON del estado cuyas features traen ``campos`` (bytes)."""
    for f in sorted(x for x in estado.rglob("*") if x.is_file() and ar.es_geojson(x)):
        try:
            gj = ar.leer_geojson(f)
            props = gj["features"][0]["properties"]
        except (ValueError, KeyError, IndexError, TypeError, StopIteration, OSError, zipfile.BadZipFile):
            continue
        if all(c in props for c in campos):
            yield f, gj


def _como_zip(gj: dict) -> bytes:
    bio = io.BytesIO()
    with zipfile.ZipFile(bio, "w") as z:
        z.writestr("m06.geojson", json.dumps(gj))
    return bio.getvalue()


def escribir_composicion(estado: Path, territorio: str, run_id: str, root: Path) -> dict:
    """Valida la composición del estado contra su GeoJSON M06 y la escribe en git; ValueError si no cuadra."""
    comps = list(cm.composiciones(estado))
    if not comps:
        raise ValueError(f"no hay *composicion_distritos.csv en {estado}")
    m06s = [_como_zip(gj) for _, gj in _geojsons(estado, ("district_id", "section_count", "district_pop"))]
    if not m06s:
        raise ValueError(f"no hay GeoJSON M06 con district_id/section_count/district_pop en {estado}")
    errores = []
    for comp in comps:
        for m06 in m06s:
            try:
                filas = cm.validar(comp, m06)
            except (ValueError, KeyError) as exc:
                errores.append(str(exc))
                continue
            cuerpo = cm.csv_bytes(filas)
            ruta = root / COMPOSICION / "runs" / f"{territorio}_{run_id}.csv"
            ruta.parent.mkdir(parents=True, exist_ok=True)
            if not ruta.is_file() or ruta.read_bytes() != cuerpo:
                ruta.write_bytes(cuerpo)
            ruta_man = root / COMPOSICION / "MANIFEST.json"
            man = _json(ruta_man, {"schema": "ddd.composicion-m06/1.0", "territorios": {}})
            entrada = {"territorio": territorio, "run_id": str(run_id), "secciones": len(filas),
                       "sha256_csv": cm.sha256(cuerpo), "ruta": ruta.relative_to(root).as_posix()}
            man.setdefault("runs", {})[f"{territorio}/{run_id}"] = entrada
            man["runs"] = dict(sorted(man["runs"].items()))
            _escribir(ruta_man, man)
            return entrada
    raise ValueError("ninguna composición valida contra el M06 del estado: " + "; ".join(errores[:3]))


def cmd_composicion(a) -> int:
    try:
        e = escribir_composicion(Path(a.estado), a.territorio, a.run_id, Path(a.root_dir))
    except ValueError as exc:
        print(f"::error title=COMPOSICION_ORIGEN_FAILED::{a.territorio}/{a.run_id}: {exc}")
        return 1
    print(f"composición: {e['ruta']} ({e['secciones']} secciones, sha256 {e['sha256_csv']})")
    return 0


# --- partidos --------------------------------------------------------------------------------------

def ganadores_m08(estado: Path) -> list[str]:
    for _, gj in _geojsons(estado, ("district_id", "winner_party")):
        fs = sorted(gj["features"], key=lambda f: int(f["properties"]["district_id"]))
        return [f["properties"].get("winner_party") or "" for f in fs]
    raise ValueError(f"no hay GeoJSON M08 con winner_party en {estado}")


def escribir_partidos(estado: Path, territorio: str, run_id: str, run_territorial: str, root: Path,
                      zip_path: Path | None = None, contratos_yaml: Path | None = None) -> dict | None:
    """Votos por partido del run M08; None si no aplica (sin contrato 2023 o sin composición del run territorial)."""
    import resultados_partidos as rp
    ctr = rp.contratos(contratos_yaml or rp.CONTRATOS).get(territorio)
    man_c = _json(root / COMPOSICION / "MANIFEST.json", {}).get("runs", {})
    comp = man_c.get(f"{territorio}/{run_territorial}")
    if not ctr or not comp:
        return None
    rutac = root / comp["ruta"]
    if cm.sha256(rutac.read_bytes()) != comp["sha256_csv"]:
        raise ValueError(f"sha256 de {comp['ruta']} no coincide con el MANIFEST")
    with tempfile.TemporaryDirectory() as tmp:
        zp = zip_path or rp.bajar_zip(ctr, Path(tmp) / "mesa.zip")
        cuerpo = rp.agregar(zp, ctr, rp.leer_composicion(rutac), ganadores_m08(estado))
    ruta = root / RESULTADOS / "runs" / f"{territorio}_{run_id}_partidos.csv"
    ruta.parent.mkdir(parents=True, exist_ok=True)
    if not ruta.is_file() or ruta.read_bytes() != cuerpo:
        ruta.write_bytes(cuerpo)
    ruta_man = root / RESULTADOS / "MANIFEST.json"
    man = _json(ruta_man, {"schema": "ddd.resultados-ligeros/1.0", "territorios": {}})
    entrada = {"territorio": territorio, "run_id": str(run_id), "run_territorial": str(run_territorial),
               "sha256_composicion": comp["sha256_csv"], "sha256_zip": ctr["source_sha256"],
               "sha256_csv": cm.sha256(cuerpo), "ruta": ruta.relative_to(root).as_posix()}
    man.setdefault("partidos_runs", {})[f"{territorio}/{run_id}"] = entrada
    man["partidos_runs"] = dict(sorted(man["partidos_runs"].items()))
    _escribir(ruta_man, man)
    return entrada


def cmd_partidos(a) -> int:
    try:
        e = escribir_partidos(Path(a.estado), a.territorio, a.run_id, a.run_territorial, Path(a.root_dir))
    except (ValueError, OSError) as exc:
        print(f"::error title=PARTIDOS_ORIGEN_FAILED::{a.territorio}/{a.run_id}: {exc}")
        return 1
    if e is None:
        print(f"::notice::{a.territorio}: sin contrato Infoelectoral 2023 o sin composición del run {a.run_territorial}; "
              "votos por partido omitidos.")
        return 0
    print(f"partidos: {e['ruta']} (sha256 {e['sha256_csv']})")
    return 0


# --- comprobar -------------------------------------------------------------------------------------

def comprobar(root: Path) -> dict:
    """{'faltan': [...], 'sobran_excepciones': [...]} para los M06 publicados en el visor."""
    vig = cm.m06_vigentes(root / cm.REGISTRO_VISOR.relative_to(cm.ROOT))
    r2 = set()
    for e in _json(root / ar.MANIFIESTO, {}).get("artefactos", {}).values():
        m = ar._FINAL.match(str(e.get("artefacto", "")))
        if m:  # M06 del run, o M08 acumulativo del mismo run o del que declara incluir el M06
            r2.add((e.get("territorio"), str(e.get("run_id"))))
            if e.get("incluye_m06_run"):
                r2.add((e.get("territorio"), str(e["incluye_m06_run"])))
    man = _json(root / COMPOSICION / "MANIFEST.json", {})
    git = {(t, str(e.get("run_id"))) for t, e in man.get("territorios", {}).items() if (root / COMPOSICION / f"{t}.csv").is_file()}
    git |= {(e["territorio"], str(e["run_id"])) for e in man.get("runs", {}).values() if (root / e["ruta"]).is_file()}
    exc = set(_json(root / EXCEPCIONES, {}).get("territorios", []))
    sin = sorted(t for t, p in vig.items() if (ar._slug(t), str(p["run_id"])) not in r2 and (t, str(p["run_id"])) not in git)
    return {"faltan": [t for t in sin if t not in exc], "sobran_excepciones": sorted(exc - set(sin))}


def cmd_comprobar(a) -> int:
    r = comprobar(Path(a.root_dir))
    for t in r["sobran_excepciones"]:
        print(f"aviso: {t} ya está archivado; quítalo de {EXCEPCIONES}")
    for t in r["faltan"]:
        print(f"::error::{t}: M06 publicado sin copia en R2 ni composición en git")
    return 1 if r["faltan"] else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root-dir", default=str(ROOT))
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("r2")
    p.add_argument("--run-id", required=True)
    p.add_argument("--artefacto", required=True)
    p.add_argument("--territorio", required=True)
    p.add_argument("--sustituye-m06-run", default="")
    p.add_argument("--extra", action="append", default=[], help="fichero o directorio local que entra en el paquete")
    p = sub.add_parser("composicion")
    p.add_argument("--estado", required=True)
    p.add_argument("--territorio", required=True)
    p.add_argument("--run-id", required=True)
    p = sub.add_parser("partidos")
    p.add_argument("--estado", required=True)
    p.add_argument("--territorio", required=True)
    p.add_argument("--run-id", required=True)
    p.add_argument("--run-territorial", required=True)
    sub.add_parser("comprobar")
    a = ap.parse_args(argv)
    return {"r2": cmd_r2, "composicion": cmd_composicion, "partidos": cmd_partidos, "comprobar": cmd_comprobar}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
