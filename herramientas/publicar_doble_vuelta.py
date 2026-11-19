#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Publicador de la doble vuelta de los territorios del Congreso para la V4: baja de R2 el resultado de P75, lo verifica y lo deja en el sitio (T-409/T-418).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-19 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
CAMBIOS: 1.0.0: fichero nuevo.
MOTIVO: D-172/D-178: el mapa V4 muestra la doble vuelta de los 52 nac sin regenerar; P75 la calcula y la archiva en R2 (objetos con run e intento);
  P40 la baja al construir el sitio, con el mismo patrón que los GeoJSON M06 (bajar de origen y verificar sha256), sin datos en git.
QUÉ HACE: lee `configuracion/doble_vuelta_publicada.json` (el run de P75 FIJADO en el repo: elección, `run_p75`, clave y sha256 del INFORME.json). Sin ese fichero no
  hace nada (sale 0). Con él: (1) baja el INFORME.json de R2 y exige su sha256; exige 52/52 OK (todos los del informe, sin excepciones); (2) por territorio baja el ZIP
  de `clave_r2` y exige el `sha256_salida` del informe; (3) lee `doble_vuelta.csv` y `detalle.csv`, exige distritos 0..K-1 sin huecos y los pasa a públicos 1..K
  (numeracion_publica.numero_publico; el interno no se toca); (4) añade el escenario `primero` (la candidatura con más votos en primera vuelta, derivada del detalle de dv_base;
  empate → orden alfabético y `empate=true`) y exige que coincida con los votos de dv_base; (5) escribe en el destino (`<sitio>/v4/mapa/datos/`):
  `INDEX.json` (cabecera: elección, run de P75, sha256 del informe, bloques y alias, y por territorio id, nombre, etiqueta, distritos y sha256 de cada fichero) y, por territorio
  `nacNN`, `resultados_doble_vuelta.csv` (14 columnas) y `detalle.csv` (7), UTF-8, coma, punto decimal. Todo se valida en memoria antes de escribir nada: o 52/52 o nada.
USO: python herramientas/publicar_doble_vuelta.py --destino /tmp/site-candidate/v4/mapa/datos [--fecha AAAA-MM-DD] [--fijado configuracion/doble_vuelta_publicada.json]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fuente_r2  # noqa: E402
from numeracion_publica import numero_publico  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FIJADO = Path("configuracion/doble_vuelta_publicada.json")
PUBLICACIONES = Path("orchestracion/publicaciones_visor.json")
ESCENARIOS = ("dv_base", "dv_A", "dv_B")
COLUMNAS = ["district_id", "escenario", "vuelta_decisiva", "candidatura_ganadora", "bloque_ganador", "votos_1v", "cuota_1v",
            "finalista_a", "finalista_b", "votos_a_2v", "votos_b_2v", "cuota_ganador_2v", "votos_abstencion", "empate"]
COLUMNAS_DETALLE = ["district_id", "escenario", "candidatura", "partido", "bloque", "votos_1v", "votos_candidatura"]
AVISO = "Simulación sin valor oficial"
PREFIJO_ETIQUETA = "Congreso "


class DobleVueltaError(Exception):
    """Fallo de verificación con causa en el mensaje (`CODIGO: detalle`)."""


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _csv(filas: list[dict], columnas: list[str]) -> bytes:
    b = io.StringIO()
    w = csv.DictWriter(b, fieldnames=columnas, lineterminator="\n")
    w.writeheader()
    w.writerows(filas)
    return b.getvalue().encode("utf-8")


def _leer(datos: bytes, columnas: list[str], nombre: str) -> list[dict]:
    filas = list(csv.DictReader(io.StringIO(datos.decode("utf-8"))))
    if not filas or any(c not in filas[0] for c in columnas):
        raise DobleVueltaError(f"CSV_INVALIDO: {nombre} sin filas o sin las columnas {columnas}")
    return filas


def _bajar(cp, bucket: str, clave: str, esperado: str, codigo: str) -> bytes:
    with tempfile.TemporaryDirectory() as td:
        dest = Path(td) / "objeto"
        try:
            cp(f"s3://{bucket}/{clave}", str(dest))
        except Exception as exc:  # noqa: BLE001 - clave ausente o R2 no disponible
            raise DobleVueltaError(f"CLAVE_AUSENTE: {clave} ({exc})") from exc
        datos = dest.read_bytes()
    real = sha256_bytes(datos)
    if real != esperado:
        raise DobleVueltaError(f"{codigo}: {clave} sha256 {real} != {esperado}")
    return datos


def _extraer(zip_bytes: bytes, nombres: tuple[str, ...]) -> dict[str, bytes]:
    out = {}
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        presentes = {i.filename: i for i in z.infolist()}
        for n in nombres:  # solo nombres exactos: nada de rutas del ZIP (zip-slip)
            if n not in presentes or presentes[n].is_dir():
                raise DobleVueltaError(f"ZIP_INCOMPLETO: falta {n}")
            out[n] = z.read(presentes[n])
    return out


def _primero(detalle_base: list[dict], res_base: dict[str, dict]) -> tuple[list[dict], list[dict]]:
    """Escenario `primero` desde el detalle de dv_base: el máximo de votos_1v por distrito (empate: alfabético, `empate=true`)."""
    por_distrito: dict[str, list[dict]] = {}
    for d in detalle_base:
        por_distrito.setdefault(d["district_id"], []).append(d)
    filas = []
    for dist in sorted(por_distrito, key=int):
        cand = sorted(por_distrito[dist], key=lambda d: (-int(d["votos_1v"]), d["partido"]))
        total = sum(int(d["votos_1v"]) for d in cand)
        top = cand[0]
        if int(top["votos_1v"]) != int(res_base[dist]["votos_1v"]):
            raise DobleVueltaError(f"PRIMERO_INCOHERENTE: distrito {dist}: {top['votos_1v']} != votos_1v de dv_base {res_base[dist]['votos_1v']}")
        empate = len(cand) > 1 and int(cand[1]["votos_1v"]) == int(top["votos_1v"])
        filas.append({"district_id": dist, "escenario": "primero", "vuelta_decisiva": "1", "candidatura_ganadora": top["partido"],
                      "bloque_ganador": top["bloque"], "votos_1v": top["votos_1v"], "cuota_1v": f"{int(top['votos_1v']) / total:.6f}",
                      "finalista_a": "", "finalista_b": "", "votos_a_2v": "", "votos_b_2v": "", "cuota_ganador_2v": "",
                      "votos_abstencion": "0", "empate": "true" if empate else "false"})
    det = [{**d, "escenario": "primero"} for d in detalle_base]
    return filas, det


def _publico(filas: list[dict]) -> list[dict]:
    return [{**f, "district_id": str(numero_publico(int(f["district_id"])))} for f in filas]


def procesar_territorio(fila_informe: dict, zip_bytes: bytes) -> tuple[bytes, bytes, int]:
    """(resultados.csv, detalle.csv, K) públicos y validados de un territorio."""
    t = fila_informe["territorio"]
    f = _extraer(zip_bytes, ("doble_vuelta.csv", "detalle.csv"))
    res = _leer(f["doble_vuelta.csv"], COLUMNAS, f"{t}/doble_vuelta.csv")
    det = _leer(f["detalle.csv"], COLUMNAS_DETALLE, f"{t}/detalle.csv")
    try:
        ids = sorted({int(r["district_id"]) for r in res})
    except ValueError as exc:
        raise DobleVueltaError(f"ID_FUERA_DE_RANGO: {t}: district_id no numérico") from exc
    k = len(ids)
    if ids != list(range(k)):
        raise DobleVueltaError(f"ID_FUERA_DE_RANGO: {t}: los distritos internos deben ser 0..K-1 sin huecos, son {ids[:6]}…")
    for esc in ESCENARIOS:
        n = {r["district_id"] for r in res if r["escenario"] == esc}
        if len(n) != k:
            raise DobleVueltaError(f"ESCENARIO_INCOMPLETO: {t}: {esc} tiene {len(n)} de {k} distritos")
    desconocidos = {r["escenario"] for r in res} - set(ESCENARIOS)
    if desconocidos:
        raise DobleVueltaError(f"ESCENARIO_DESCONOCIDO: {t}: {sorted(desconocidos)}")
    base = {r["district_id"]: r for r in res if r["escenario"] == "dv_base"}
    det_base = [d for d in det if d["escenario"] == "dv_base"]
    p_res, p_det = _primero(det_base, base)
    todas = sorted(res + p_res, key=lambda r: (int(r["district_id"]), (*ESCENARIOS, "primero").index(r["escenario"])))
    todo_det = sorted(det + p_det, key=lambda d: (int(d["district_id"]), (*ESCENARIOS, "primero").index(d["escenario"])))
    return _csv(_publico(todas), COLUMNAS), _csv(_publico(todo_det), COLUMNAS_DETALLE), k


def nombres(root: Path) -> dict[str, tuple[str, str]]:
    """id → (nombre, etiqueta) del registro del visor (territory_label; el nombre sin el prefijo «Congreso »)."""
    out = {}
    for p in json.loads((root / PUBLICACIONES).read_text(encoding="utf-8"))["products"]:
        if p.get("kind") == "canonical_m08" and p.get("territory_label"):
            e = str(p["territory_label"])
            out[p["territory_id"]] = (e[len(PREFIJO_ETIQUETA):] if e.startswith(PREFIJO_ETIQUETA) else e, e)
    return out


def publicar(root: Path, destino: Path, cp=fuente_r2._cp, bucket: str = "", fecha: str = "", fijado: Path | None = None) -> dict | None:
    f = root / (fijado or FIJADO)
    if not f.is_file():
        print("[doble_vuelta] sin doble vuelta fijada (configuracion/doble_vuelta_publicada.json): nada que publicar")
        return None
    pin = json.loads(f.read_text(encoding="utf-8"))
    for k in ("eleccion", "run_p75", "informe_clave", "informe_sha256"):
        if not pin.get(k):
            raise DobleVueltaError(f"FIJADO_INVALIDO: falta {k} en {FIJADO}")
    inf_bytes = _bajar(cp, bucket, pin["informe_clave"], pin["informe_sha256"], "INFORME_SHA256_DISTINTO")
    inf = json.loads(inf_bytes)
    if inf.get("eleccion") != pin["eleccion"] or str(inf.get("run_p75")) != str(pin["run_p75"]):
        raise DobleVueltaError(f"INFORME_NO_ES_EL_FIJADO: {inf.get('eleccion')}/{inf.get('run_p75')} != {pin['eleccion']}/{pin['run_p75']}")
    malos = [x for x in inf["territorios"] if x.get("estado") != "OK"]
    if malos or inf.get("ok") != inf.get("total") or not inf["territorios"]:
        detalle = ", ".join(f"{x['territorio']}={x.get('estado')}" for x in malos) or f"{inf.get('ok')}/{inf.get('total')} OK"
        raise DobleVueltaError(f"INFORME_INCOMPLETO: {detalle}")
    nom = nombres(root)
    ficheros: dict[str, bytes] = {}
    entradas = []
    for x in sorted(inf["territorios"], key=lambda x: x["territorio"]):
        t = x["territorio"]
        if not x.get("clave_r2") or not x.get("sha256_salida"):
            raise DobleVueltaError(f"CLAVE_AUSENTE: {t} sin clave_r2/sha256_salida en el informe")
        res, det, k = procesar_territorio(x, _bajar(cp, bucket, x["clave_r2"], x["sha256_salida"], "ZIP_SHA256_DISTINTO"))
        ficheros[f"{t}/resultados_doble_vuelta.csv"], ficheros[f"{t}/detalle.csv"] = res, det
        nombre, etiqueta = nom.get(t, (t, t))
        entradas.append({"id": t, "nombre": nombre, "etiqueta": etiqueta, "distritos": k, "run_m08": x["run"],
                         "sin_casar_pct": x.get("sin_casar_pct"), "sha256_paquete_p75": x["sha256_salida"],
                         "resultados": {"ruta": f"{t}/resultados_doble_vuelta.csv", "sha256": sha256_bytes(res)},
                         "detalle": {"ruta": f"{t}/detalle.csv", "sha256": sha256_bytes(det)}})
    indice = {"schema": "ddd.v4-doble-vuelta/1.0", "eleccion": pin["eleccion"], "aviso": AVISO, "p75_run": pin["run_p75"],
              "informe_sha256": pin["informe_sha256"], "bloques_sha256": inf["entradas"]["bloques"]["sha256"],
              "alias_sha256": inf["entradas"]["alias"]["sha256"],
              "generado": fecha or datetime.now(timezone.utc).strftime("%Y-%m-%d"), "territorios": entradas}
    # todo validado: ahora se escribe (o 52/52 o nada)
    for ruta, datos in ficheros.items():
        p = destino / ruta
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(datos)
    (destino / "INDEX.json").write_text(json.dumps(indice, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[doble_vuelta] {len(entradas)} territorios en {destino}")
    return indice


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--destino", required=True)
    ap.add_argument("--fecha", default="")
    ap.add_argument("--fijado", default="")
    a = ap.parse_args(argv)
    bucket = os.environ.get("R2_BUCKET", "")
    if (ROOT / (a.fijado or FIJADO)).is_file() and (not bucket or not os.environ.get("R2_ACCOUNT_ID")):
        print("::error title=DOBLE_VUELTA_SIN_CREDENCIALES::faltan R2_BUCKET/R2_ACCOUNT_ID")
        return 3
    try:
        publicar(ROOT, Path(a.destino), bucket=bucket, fecha=a.fecha, fijado=Path(a.fijado) if a.fijado else None)
    except DobleVueltaError as exc:
        print(f"::error title=DOBLE_VUELTA::{exc}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
