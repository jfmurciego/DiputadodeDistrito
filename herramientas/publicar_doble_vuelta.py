#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Publicador de la doble vuelta de los territorios del Congreso para la V4: baja de R2 el resultado de P75, lo verifica y lo deja en el sitio (T-409/T-418).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.1 · FECHA: 2026-11-19 · ESTADO: candidato
ANTERIOR: legacy/herramientas/publicar_doble_vuelta_v1.0.0_20261119.py
CAMBIOS: 1.0.1: T-422, ids de distrito normalizados a entero (M07 puede escribir «0.0»/espacios) y diagnóstico por territorio, fichero, línea y valor exacto. 1.0.0: fichero nuevo (con la geometría: decisión del Planificador, opción A).
MOTIVO: D-172/D-178: el mapa V4 muestra la doble vuelta de los 52 nac sin regenerar; P75 la calcula y la archiva en R2 (objetos con run e intento);
  P40 la baja al construir el sitio, con el mismo patrón que los GeoJSON M06 (bajar de origen y verificar sha256), sin datos en git.
QUÉ HACE: lee `configuracion/doble_vuelta_publicada.json` (el run de P75 FIJADO en el repo: elección, `run_p75`, clave y sha256 del INFORME.json). Sin ese fichero no
  hace nada (sale 0). Con él: (1) baja el INFORME.json de R2 y exige su sha256; exige 52/52 OK (todos los del informe, sin excepciones); (2) por territorio baja el ZIP
  de `clave_r2` y exige el `sha256_salida` del informe; (3) lee `doble_vuelta.csv` y `detalle.csv`, exige distritos 0..K-1 sin huecos y los pasa a públicos 1..K
  (numeracion_publica.numero_publico; el interno no se toca); (4) añade el escenario `primero` (la candidatura con más votos en primera vuelta, derivada del detalle de dv_base;
  empate → orden alfabético y `empate=true`) y exige que coincida con los votos de dv_base; (5) escribe en el destino (`<sitio>/v4/mapa/datos/`):
  `INDEX.json` (cabecera: elección, run de P75, sha256 del informe, bloques y alias, y por territorio id, nombre, etiqueta, distritos y sha256 de cada fichero) y, por territorio
  `nacNN`, `resultados_doble_vuelta.csv` (14 columnas), `detalle.csv` (7) y `distritos.geojson`, UTF-8, coma, punto decimal. Todo se valida en memoria antes de escribir nada: o 52/52 o nada.
  GEOMETRÍA (opción A): reutiliza el GeoJSON de distritos que P40 ya materializa en `<sitio>/datos/<nacNN>/distritos.geojson` (derivado del M06 con sha256, EPSG:4326, propiedad `distrito`
  1..K) y comprueba su sha256 contra `<sitio>/datos/INDEX.json`; lo SIMPLIFICA con Douglas-Peucker por anillo (tolerancia fija `TOLERANCIA_GRADOS` = 0,0005° ≈ 55 m, coordenadas a
  5 decimales; sin topología compartida: entre distritos vecinos puede quedar un hueco o solape de hasta la tolerancia, invisible a la escala del mapa), deja solo `district_id` (entero
  público 1..K) y exige que los distritos de la geometría sean EXACTAMENTE los del CSV (ni uno sin geometría ni uno sin dato). En INDEX.json: `geometria` (ruta, sha256, sha256_origen).
USO: python herramientas/publicar_doble_vuelta.py --sitio /tmp/site-candidate --destino /tmp/site-candidate/v4/mapa/datos [--fecha AAAA-MM-DD] [--fijado configuracion/doble_vuelta_publicada.json]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
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
MAX_DESCOMPRIMIDO = 64 * 1024 * 1024  # un CSV de un territorio pesa ≈ 0,5 MB: más de 64 MB descomprimidos es un ZIP anómalo
ESPERADOS = 52  # territorios del Congreso (nac): el informe fijado debe traerlos todos
TERRITORIO = re.compile(r"^nac\d{2}$")
TOLERANCIA_GRADOS = 0.0005  # Douglas-Peucker; ≈ 55 m en latitudes españolas
DECIMALES = 5  # ≈ 1 m
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
            if presentes[n].file_size > MAX_DESCOMPRIMIDO:
                raise DobleVueltaError(f"ZIP_DEMASIADO_GRANDE: {n} descomprime {presentes[n].file_size} B (tope {MAX_DESCOMPRIMIDO})")
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


_ID_ENTERO = re.compile(r"^\+?(\d+)(?:\.0+)?$")


def _normalizar_ids(t: str, filas: list[dict], fichero: str) -> list[dict]:
    """Normaliza `district_id` a entero interno canónico («0», « 1 », «2.0», «02» → «0», «1», «2», «2»; T-422). M07 puede escribir el id
    como real (pandas, «0.0») o con espacios. Solo se admiten enteros no negativos con esa forma: lo demás se rechaza con los
    valores concretos (`ID_FUERA_DE_RANGO: <territorio>/<fichero>: ...`), sin adivinar."""
    malos: list[tuple[int, str]] = []  # (nº de línea en el fichero, repr exacto)
    out = []
    for n, r in enumerate(filas, start=2):  # la línea 1 es la cabecera
        m = _ID_ENTERO.match(str(r["district_id"]).strip())
        if m is None:
            malos.append((n, repr(r["district_id"])))
            continue
        out.append({**r, "district_id": str(int(m.group(1)))})
    if malos:
        ej = ", ".join(f"línea {n}: {v}" for n, v in malos[:6])
        raise DobleVueltaError(f"ID_FUERA_DE_RANGO: {t}/{fichero}: district_id no numérico en {len(malos)} de {len(filas)} filas "
                               f"({ej}); se rechaza (no se excluye en silencio: votos sin distrito no son un distrito); se admiten enteros ('0', '2.0', ' 1 ')")
    return out


def procesar_territorio(fila_informe: dict, zip_bytes: bytes) -> tuple[bytes, bytes, int]:
    """(resultados.csv, detalle.csv, K) públicos y validados de un territorio."""
    t = fila_informe["territorio"]
    f = _extraer(zip_bytes, ("doble_vuelta.csv", "detalle.csv"))
    res = _leer(f["doble_vuelta.csv"], COLUMNAS, f"{t}/doble_vuelta.csv")
    det = _leer(f["detalle.csv"], COLUMNAS_DETALLE, f"{t}/detalle.csv")
    res, det = _normalizar_ids(t, res, "doble_vuelta.csv"), _normalizar_ids(t, det, "detalle.csv")
    ids = sorted({int(r["district_id"]) for r in res})
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
    faltan = sorted(set(base) - {r["district_id"] for r in p_res}, key=int)
    if faltan:  # un distrito sin votos por partido en dv_base se quedaría sin fila `primero`
        raise DobleVueltaError(f"PRIMERO_INCOMPLETO: {t}: sin detalle de dv_base en los distritos {faltan[:8]}")
    todas = sorted(res + p_res, key=lambda r: (int(r["district_id"]), (*ESCENARIOS, "primero").index(r["escenario"])))
    todo_det = sorted(det + p_det, key=lambda d: (int(d["district_id"]), (*ESCENARIOS, "primero").index(d["escenario"])))
    return _csv(_publico(todas), COLUMNAS), _csv(_publico(todo_det), COLUMNAS_DETALLE), k


def _dist_punto_segmento(p, a, b) -> float:
    (px, py), (ax, ay), (bx, by) = p, a, b
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return ((px - ax) ** 2 + (py - ay) ** 2) ** 0.5
    u = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return ((px - (ax + u * dx)) ** 2 + (py - (ay + u * dy)) ** 2) ** 0.5


def douglas_peucker(puntos: list, tol: float) -> list:
    """Douglas-Peucker iterativo (sin recursión: los anillos tienen decenas de miles de puntos); conserva siempre el primero y el último."""
    n = len(puntos)
    if n < 3:
        return list(puntos)
    mantener = [False] * n
    mantener[0] = mantener[-1] = True
    pila = [(0, n - 1)]
    while pila:
        i, j = pila.pop()
        maxd, k = 0.0, -1
        for m in range(i + 1, j):
            d = _dist_punto_segmento(puntos[m], puntos[i], puntos[j])
            if d > maxd:
                maxd, k = d, m
        if k != -1 and maxd > tol:
            mantener[k] = True
            pila.append((i, k))
            pila.append((k, j))
    return [p for p, m in zip(puntos, mantener) if m]


def _anillo(anillo: list) -> list:
    pts = []
    for x, y, *_ in anillo:
        q = [round(x, DECIMALES), round(y, DECIMALES)]
        if not pts or pts[-1] != q:
            pts.append(q)
    s = douglas_peucker(pts, TOLERANCIA_GRADOS)
    if len(s) >= 4 and s[0] == s[-1]:
        return s
    return pts if len(pts) >= 4 and pts[0] == pts[-1] else anillo  # anillo minúsculo: se conserva tal cual (nunca se pierde un distrito)


def _geometria(g: dict) -> dict:
    if g.get("type") == "Polygon":
        return {"type": "Polygon", "coordinates": [_anillo(a) for a in g["coordinates"]]}
    if g.get("type") == "MultiPolygon":
        return {"type": "MultiPolygon", "coordinates": [[_anillo(a) for a in poli] for poli in g["coordinates"]]}
    raise DobleVueltaError(f"GEOMETRIA_NO_SOPORTADA: {g.get('type')}")


def procesar_geometria(t: str, geojson: bytes, ids_datos: set[int]) -> bytes:
    """GeoJSON público del territorio (`distrito` 1..K) → simplificado con solo `district_id`; sus distritos deben ser exactamente los del CSV."""
    gj = json.loads(geojson.decode("utf-8"))
    feats, vistos = [], []
    for f in gj["features"]:
        n = int(f["properties"]["distrito"])
        if not f.get("geometry") or not f["geometry"].get("coordinates"):
            raise DobleVueltaError(f"DATO_SIN_GEOMETRIA: {t} distrito {n} sin geometría")
        vistos.append(n)
        feats.append({"type": "Feature", "properties": {"district_id": n}, "geometry": _geometria(f["geometry"])})
    if len(set(vistos)) != len(vistos):
        raise DobleVueltaError(f"GEOMETRIA_DUPLICADA: {t} repite distritos")
    sin_geom, sin_dato = sorted(ids_datos - set(vistos)), sorted(set(vistos) - ids_datos)
    if sin_geom:
        raise DobleVueltaError(f"DATO_SIN_GEOMETRIA: {t} distritos con dato y sin geometría: {sin_geom[:8]}")
    if sin_dato:
        raise DobleVueltaError(f"GEOMETRIA_SIN_DATO: {t} distritos con geometría y sin dato: {sin_dato[:8]}")
    feats.sort(key=lambda f: f["properties"]["district_id"])
    return (json.dumps({"type": "FeatureCollection", "features": feats}, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


def nombres(root: Path) -> dict[str, tuple[str, str]]:
    """id → (nombre, etiqueta) del registro del visor (territory_label; el nombre sin el prefijo «Congreso »)."""
    out = {}
    for p in json.loads((root / PUBLICACIONES).read_text(encoding="utf-8"))["products"]:
        if p.get("kind") == "canonical_m08" and p.get("territory_label"):
            e = str(p["territory_label"])
            out[p["territory_id"]] = (e[len(PREFIJO_ETIQUETA):] if e.startswith(PREFIJO_ETIQUETA) else e, e)
    return out


def publicar(root: Path, destino: Path, cp=fuente_r2._cp, bucket: str = "", fecha: str = "", fijado: Path | None = None, sitio: Path | None = None) -> dict | None:
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
    if sitio is None:
        raise DobleVueltaError("GEOMETRIA_AUSENTE: falta --sitio (el sitio candidato con datos/<nacNN>/distritos.geojson de P40)")
    try:
        indice_datos = json.loads((sitio / "datos/INDEX.json").read_text(encoding="utf-8"))["territorios"]
    except (OSError, KeyError, ValueError) as exc:
        raise DobleVueltaError(f"GEOMETRIA_AUSENTE: sin {sitio}/datos/INDEX.json ({exc})") from exc
    try:
        bloques_sha, alias_sha = inf["entradas"]["bloques"]["sha256"], inf["entradas"]["alias"]["sha256"]
    except (KeyError, TypeError) as exc:
        raise DobleVueltaError(f"INFORME_SIN_ENTRADAS: el informe no trae entradas.bloques/alias.sha256 ({exc!r})") from exc
    ids = [x["territorio"] for x in inf["territorios"]]
    malos_ids = [i for i in ids if not isinstance(i, str) or not TERRITORIO.match(i)]
    if malos_ids:  # el id entra en rutas de salida: solo nacNN
        raise DobleVueltaError(f"TERRITORIO_INVALIDO: {malos_ids[:5]}")
    if len(set(ids)) != len(ids):
        raise DobleVueltaError(f"TERRITORIO_DUPLICADO: {sorted({i for i in ids if ids.count(i) > 1})}")
    if len(ids) != ESPERADOS or inf.get("total") != ESPERADOS:
        raise DobleVueltaError(f"INFORME_INCOMPLETO: {len(ids)} territorios (total {inf.get('total')}), se esperan {ESPERADOS}")
    nom = nombres(root)
    ficheros: dict[str, bytes] = {}
    entradas = []
    fallos_id: list[str] = []
    for x in sorted(inf["territorios"], key=lambda x: x["territorio"]):
        t = x["territorio"]
        if not x.get("clave_r2") or not x.get("sha256_salida"):
            raise DobleVueltaError(f"CLAVE_AUSENTE: {t} sin clave_r2/sha256_salida en el informe")
        try:
            res, det, k = procesar_territorio(x, _bajar(cp, bucket, x["clave_r2"], x["sha256_salida"], "ZIP_SHA256_DISTINTO"))
        except DobleVueltaError as exc:
            if str(exc).startswith("ID_FUERA_DE_RANGO"):  # diagnóstico por territorio: se siguen recorriendo los 52 y se informa de todos a la vez
                fallos_id.append(str(exc))
                continue
            raise
        ficheros[f"{t}/resultados_doble_vuelta.csv"], ficheros[f"{t}/detalle.csv"] = res, det
        origen = sitio / "datos" / t / "distritos.geojson"
        try:
            gbytes = origen.read_bytes()
            esperado = indice_datos[t]["geojson"]["sha256"]
        except (OSError, KeyError) as exc:
            raise DobleVueltaError(f"GEOMETRIA_AUSENTE: {t} sin {origen} o sin entrada en datos/INDEX.json") from exc
        if sha256_bytes(gbytes) != esperado:
            raise DobleVueltaError(f"GEOMETRIA_SHA256_DISTINTO: {t} {sha256_bytes(gbytes)} != {esperado}")
        geo = procesar_geometria(t, gbytes, {int(r["district_id"]) for r in csv.DictReader(io.StringIO(res.decode("utf-8")))})
        ficheros[f"{t}/distritos.geojson"] = geo
        nombre, etiqueta = nom.get(t, (t, t))
        entradas.append({"id": t, "nombre": nombre, "etiqueta": etiqueta, "distritos": k, "run_m08": x["run"],
                         "sin_casar_pct": x.get("sin_casar_pct"), "sha256_paquete_p75": x["sha256_salida"],
                         "resultados": {"ruta": f"{t}/resultados_doble_vuelta.csv", "sha256": sha256_bytes(res)},
                         "detalle": {"ruta": f"{t}/detalle.csv", "sha256": sha256_bytes(det)},
                         "geometria": {"ruta": f"{t}/distritos.geojson", "sha256": sha256_bytes(geo), "sha256_origen": esperado}})
    if fallos_id:
        raise DobleVueltaError(f"{len(fallos_id)} territorios con ids de distrito inválidos: " + " | ".join(fallos_id))
    indice = {"schema": "ddd.v4-doble-vuelta/1.0", "eleccion": pin["eleccion"], "aviso": AVISO, "p75_run": pin["run_p75"],
              "informe_sha256": pin["informe_sha256"], "bloques_sha256": bloques_sha, "alias_sha256": alias_sha,
              "generado": fecha or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
              "simplificacion": {"algoritmo": "Douglas-Peucker por anillo", "tolerancia_grados": TOLERANCIA_GRADOS, "decimales": DECIMALES, "crs": "EPSG:4326"},
              "territorios": entradas}
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
    ap.add_argument("--sitio", default="/tmp/site-candidate", help="sitio candidato con datos/<nacNN>/distritos.geojson (P40)")
    ap.add_argument("--destino", required=True)
    ap.add_argument("--fecha", default="")
    ap.add_argument("--fijado", default="")
    a = ap.parse_args(argv)
    bucket = os.environ.get("R2_BUCKET", "")
    if (ROOT / (a.fijado or FIJADO)).is_file() and (not bucket or not os.environ.get("R2_ACCOUNT_ID")):
        print("::error title=DOBLE_VUELTA_SIN_CREDENCIALES::faltan R2_BUCKET/R2_ACCOUNT_ID")
        return 3
    try:
        publicar(ROOT, Path(a.destino), bucket=bucket, fecha=a.fecha, fijado=Path(a.fijado) if a.fijado else None, sitio=Path(a.sitio))
    except DobleVueltaError as exc:
        print(f"::error title=DOBLE_VUELTA::{exc}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
