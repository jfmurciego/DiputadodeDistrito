#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Estado de campaña de P00 (T-379 PR 1): comprobación previa, recuento de apartados, parada, resultado, cierre e informe.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.2.0
NOMBRE DE VERSIÓN: Estado de campaña P00
FECHA: 2026-11-19
ESTADO: candidato
ANTERIOR: legacy/herramientas/campana_estado_v1.1.0_20261119.py
CAMBIOS 1.2.0 (T-379 PR 3b, D-147 y diseño §6): el plan del cierre admite `configuracion/catalogo_preparacion.yaml`, la
  ÚNICA ruta fuera de RUTAS_ROBOT (el cierre la escribe y su commit lanza la CI completa de main); la 1.0.x la rechazaba,
  al revés de D-147. Cualquier otra ruta fuera de RUTAS_ROBOT sigue siendo CIERRE_RUTA_NO_ROBOT.
CAMBIOS 1.1.0 (T-379 PR 3, §3, §4 y §16.1, D-147): `concurrencia` (segunda campaña rechazada con el run que bloquea; sigue la
  de run_id menor; `pull_request` y terminadas no cuentan), `hechos` (CI de la versión, R2 y gasto semanal D-46 para
  `comprobar --hechos`; sin evidencia → aviso, nunca bloqueo) y `cerrar-paso` (resultado de un paso de la cadena desde
  los `needs.<job>.result`). El resto, igual.
CAMBIOS 1.0.1 (T-377): las citas de ARCHIVO_ORIGEN_FAILED y SALIDA_48 apuntan a `p20-distritos.yml` (el reutilizable de generación se borró); mismas líneas de código, otra numeración. Solo texto.
CAMBIOS: 1.0.0: fichero nuevo (T-379 PR 1; incluye los arreglos del revisor de #861: semáforo inmutable, causas
  acreditadas en main con cita, re-ejecución vetada también al registrar, parada pegajosa, «ausente» de R2 exacto,
  entradas saneadas, causa normalizada sin perder el texto, D-147).
MOTIVO: diseño de P00 Campaña 1.1 (T-378/T-387, D-143, D-145) §2, §3, §4, §6, §10 y §13 (PR 1: estado de campaña, sin workflows).
QUÉ HACE (sin red, salvo el almacén R2; determinista; fallo cerrado; errores `::error::` a stderr):
  comprobar   territorios + elección (+ hechos) → semáforo verde/ámbar/rojo por territorio y si la campaña es lanzable.
  empezar     antes de un paso: parada sistémica (rc 10), re-ejecución no admitida (rc 4) y marca «sin_resultado».
  registrar   resultado de un paso (ok | apartado + causa) con clave (campaña, territorio, paso, run_attempt).
  recuento    apartados (último intento por territorio y paso), por causa y parada sistémica (D-143.6).
  resultado   rc 1 si hay ≥1 apartado, parada o cierre pendiente; rc 0 si no.
  cierre      plan del commit (rama main o p00-cierre/<run_id>; ficheros ⊆ RUTAS_ROBOT; vacío en ensayo) y objeto
              «cierre» idempotente por huella del estado.
  informe     markdown para el issue de la campaña.
  concurrencia lista de ejecuciones de P00 (API) → rc 3 si otra campaña de run_id menor sigue viva (D-147).
  hechos      ejecuciones de P90 de la versión + R2 + métricas → hechos de campaña para `comprobar --hechos`.
  cerrar-paso resultados de los jobs de un paso de la cadena (`needs.<job>.result`) → registrar ok | apartado; imprime
              {"sano": bool}. Un job en rojo = FALLO_NO_CONTROLADO; un obligatorio saltado o cancelado = PASO_INCOMPLETO.
NO HACE: lanzar, hacer commits, push ni llamar a la API de GitHub (eso es la PR 3).
ALMACÉN: `--almacen r2` (R2_BUCKET, R2_ACCOUNT_ID y AWS_*; aws s3/s3api como fuente_r2.py y listar_r2.py) o
  `--almacen dir:<ruta>` (directorio local, para pruebas y simulación). Claves bajo `campanas/<campaña>/`.
PARADA PEGAJOSA: al detectarse se fija en `campanas/<campaña>/parada.json` y ya no se levanta en esa campaña: `empezar`
  devuelve rc 10 incluso para re-ejecutar transitorios. Solo se sale con otra campaña (id = run_id nuevo) o con una
  orden explícita futura (no existe en la 1.0.0). La PR 3 debe documentarlo en el procedimiento del Operador.
CÓDIGOS DE SALIDA: 0 bien · 1 resultado en rojo · 2 entrada o estado inválido · 3 campaña no lanzable ·
  4 paso no re-ejecutable · 10 parada sistémica.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from ddd_core import territorio_ids as tids  # noqa: E402

REGISTRO = Path("configuracion/registro_electoral.yaml")
UNIVERSO_ENSAYO = Path("configuracion/elecciones_generales_2026.yaml")
CONTRATOS_ENSAYO = Path("configuracion/contratos_minsait_provisionales.yaml")
P90 = Path(".github/workflows/p90-automatico.yml")
CATALOGO_CIERRE = "configuracion/catalogo_preparacion.yaml"  # D-147: única ruta del cierre fuera de RUTAS_ROBOT

PASOS = ("P10", "P20", "P30")
ENSAYO_MES = "2026-11"
ENSAYO_P12 = "ensayo 2026-11-29"  # única opción de ensayo de preparacion-resultados-electorales.yml (1.0.17)
GRUPOS = {"todos": None, "congreso": "NAC", "autonómicas": "AUT", "autonomicas": "AUT"}

# Semáforo (§3). Causas de los hechos que aporta la comprobación previa del workflow (PR 3) y las que resuelve esta herramienta.
AMBAR = {"PAQUETE_FUENTES_CADUCADO", "CHECKPOINT_INCOMPATIBLE"}
ROJO = {"FUENTE_SIN_ESPEJO", "BLOQUEADA_SIN_DATO", "SIN_ELECCION", "ELECCION_NO_SOPORTADA", "CODIGO_INEXISTENTE",
        "CONGRESO_350", "ENSAYO_SIN_CONTRATO"}
# Causas acreditadas en `main` (código → (transitoria, salida, cita)). Transitoria = se puede re-ejecutar en la misma
# ejecución (§4); el resto, no. Una causa fuera de la tabla es NO transitoria (fallo cerrado).
CAUSAS = {
    "SIN_RESULTADO": (True, None, "diseño P00 1.1 §4 (cancelación, tiempo agotado, runner perdido)"),
    "PUSH_RECHAZADO_TRAS_<N>": (True, 75, "herramientas/registrar_en_main.py l. 45 y 52-55; "
                                "persistir_estado_operativo_compartido.py l. 142; persistir_producto_electoral_operacional.py l. 447"),
    # Transitoria por diseño, pero si se agotó tras los reintentos es probable que se repita en la misma campaña
    # (cuota de Actions agotada: Settings → Billing); re-ejecutar solo tras comprobar la cuota.
    "ARTIFACT_EGRESS_QUOTA": (True, 75, ".github/workflows/_reutilizable-puerta-validacion.yml l. 14, 151 y 172 (cuota de Actions)"),
    "CATALOGO_PROCEDENCIA_NO_REGENERADO": (False, 76, "herramientas/registrar_en_main.py l. 46 y 282"),
    "RUTA_NO_FUSIONABLE": (False, 77, "herramientas/registrar_en_main.py l. 47 y 285-286"),
    # Envuelve la salida de registrar_en_main (75, 76 o 77) en `exit 1`: no se sabe si fue el push → no transitoria.
    "ARCHIVO_ORIGEN_FAILED": (False, 1, ".github/workflows/p20-distritos.yml l. 2196; "
                              "_reutilizable-incorporacion-electoral.yml l. 415"),
    "SALIDA_48": (False, 48, "registro o certificación fallidos: p20-distritos.yml l. 2115-2177, "
                  "preparacion-fuentes.yml l. 534, preparacion-resultados-electorales.yml l. 458"),
    "SALIDA_50": (False, 50, "registro durable incoherente: preparacion-fuentes.yml l. 536, "
                  "preparacion-resultados-electorales.yml l. 647, ejecucion-completa-proyecto.yml l. 1637"),
}
PREFIJO_PUSH = "PUSH_RECHAZADO_TRAS_"
# Salida del proceso → causa, solo cuando no hay código impreso. La 75 tiene tres orígenes: dos transitorios
# (registrar_en_main.py PUSH_RECHAZADO_TRAS_N; puerta ARTIFACT_EGRESS_QUOTA) y uno que no lo es
# (ejecucion-completa-proyecto.yml l. 897, «Digest remoto territorial contradice la acreditación»): sin el código impreso,
# SALIDA_75 es NO transitoria (fallo cerrado).
SALIDAS = {75: "SALIDA_75", 76: "CATALOGO_PROCEDENCIA_NO_REGENERADO", 77: "RUTA_NO_FUSIONABLE", 48: "SALIDA_48", 50: "SALIDA_50"}
CAUSA_DESCONOCIDA = "CAUSA_DESCONOCIDA"
RE_CAUSA = re.compile(r"[A-Z][A-Z0-9_]{2,63}")
RE_CAMPANA = re.compile(r"[A-Za-z0-9_-]{1,64}")
RE_TOKEN = re.compile(r"[a-z0-9_-]{1,40}")


def es_transitoria(causa: str | None) -> bool:
    c = causa or ""
    if c.startswith(PREFIJO_PUSH) and c[len(PREFIJO_PUSH):].isdigit():
        return True
    return c in CAUSAS and CAUSAS[c][0]
ESTADOS_FINALES = {"ok", "apartado"}

RC_ROJO, RC_ENTRADA, RC_NO_LANZABLE, RC_NO_REEJECUTABLE, RC_PARADA = 1, 2, 3, 4, 10


class EstadoError(Exception):
    """Entrada o estado inválido: fallo cerrado (rc 2)."""


class NoReejecutable(EstadoError):
    """Intento nuevo de un paso cuyo último intento fue un apartado no transitorio (rc 4)."""


def _error(msg: str) -> None:
    print("::error::" + " ".join(str(msg).split()), file=sys.stderr)  # sin saltos de línea: no inyecta comandos


def _yaml(path: Path) -> dict:
    import yaml

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def _json(obj) -> bytes:
    return (json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=1) + "\n").encode("utf-8")


# ─────────────────────────────── almacén ───────────────────────────────

class AlmacenLocal:
    """Directorio local con la misma interfaz que R2 (pruebas y simulación)."""

    def __init__(self, raiz: Path):
        self.raiz = Path(raiz)

    def leer(self, clave: str) -> bytes | None:
        p = self.raiz / clave
        return p.read_bytes() if p.is_file() else None

    def escribir(self, clave: str, datos: bytes) -> None:
        p = self.raiz / clave
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(p.suffix + ".tmp")
        tmp.write_bytes(datos)
        tmp.replace(p)

    def listar(self, prefijo: str) -> list[str]:
        base = self.raiz / prefijo
        if not base.exists():
            return []
        return sorted(str(p.relative_to(self.raiz)).replace(os.sep, "/") for p in base.rglob("*.json") if p.is_file())


RE_AUSENTE = re.compile(r"An error occurred \((?:404|NoSuchKey)\) when calling the (?:HeadObject|GetObject) operation")


class AlmacenR2:
    """R2 por la CLI de aws (mismo endpoint que fuente_r2.py). Un objeto ausente es None; cualquier otro fallo, error."""

    def __init__(self, bucket: str, cuenta: str, run=subprocess.run):
        self.bucket, self.ep, self.run = bucket, f"https://{cuenta}.r2.cloudflarestorage.com", run

    def _aws(self, args: list[str], entrada: bytes | None = None):
        return self.run(["aws", *args, "--endpoint-url", self.ep], input=entrada, capture_output=True)

    def leer(self, clave: str) -> bytes | None:
        p = self._aws(["s3", "cp", f"s3://{self.bucket}/{clave}", "-", "--only-show-errors"])
        if p.returncode == 0:
            return p.stdout
        err = (p.stderr or b"").decode("utf-8", "replace")
        if RE_AUSENTE.search(err):
            return None
        raise EstadoError(f"CAMPANA_R2_LECTURA {clave}: {err.strip()[:300]}")

    def escribir(self, clave: str, datos: bytes) -> None:
        p = self._aws(["s3", "cp", "-", f"s3://{self.bucket}/{clave}", "--only-show-errors"], entrada=datos)
        if p.returncode != 0:
            raise EstadoError(f"CAMPANA_R2_ESCRITURA {clave}: {(p.stderr or b'').decode('utf-8', 'replace').strip()[:300]}")

    def listar(self, prefijo: str) -> list[str]:
        p = self._aws(["s3api", "list-objects-v2", "--bucket", self.bucket, "--prefix", prefijo,
                       "--query", "Contents[].Key", "--output", "json"])
        if p.returncode != 0:
            raise EstadoError(f"CAMPANA_R2_LISTADO {prefijo}: {(p.stderr or b'').decode('utf-8', 'replace').strip()[:300]}")
        return sorted(json.loads(p.stdout or b"null") or [])


def almacen(spec: str):
    if spec.startswith("dir:") and len(spec) > 4:
        return AlmacenLocal(Path(spec[4:]))
    if spec == "r2":
        bucket, cuenta = os.environ.get("R2_BUCKET", ""), os.environ.get("R2_ACCOUNT_ID", "")
        if not bucket or not cuenta:
            raise EstadoError("CAMPANA_R2_SIN_CREDENCIALES (R2_BUCKET/R2_ACCOUNT_ID)")
        return AlmacenR2(bucket, cuenta)
    raise EstadoError(f"almacén no válido: {spec!r} (r2 | dir:<ruta>)")


def _prefijo(campana: str) -> str:
    if not RE_CAMPANA.fullmatch(str(campana)):
        raise EstadoError(f"id de campaña no válido: {campana!r}")
    return f"campanas/{campana}/"


def clave_paso(campana: str, territorio: str, paso: str, intento: int) -> str:
    return f"{_prefijo(campana)}pasos/{territorio}/{paso}/{intento}.json"


def _leer_json(alm, clave: str):
    b = alm.leer(clave)
    if b is None:
        return None
    try:
        d = json.loads(b)
    except ValueError as exc:
        raise EstadoError(f"CAMPANA_OBJETO_CORRUPTO {clave}: {exc}") from exc
    if not isinstance(d, dict):
        raise EstadoError(f"CAMPANA_OBJETO_CORRUPTO {clave}: no es un objeto JSON")
    return d


# ─────────────────────────── territorios y elección ───────────────────────────

def resolver_territorios(valor: str) -> list[str]:
    """`todos` | `congreso` | `autonómicas` | lista de códigos (`nac22, aut11`). Devuelve códigos tal cual (en minúsculas)
    en orden de entrada y sin duplicados; los que no existen se marcan después en rojo, no aquí."""
    v = str(valor or "").strip()
    if not v:
        raise EstadoError("territorios vacío: usa todos, congreso, autonómicas o una lista de códigos")
    if v.lower() in GRUPOS:
        return tids.ids_nuevos(GRUPOS[v.lower()])
    fichas = [t.lower() for t in re.split(r"[\s,;]+", v) if t]
    if any(t in GRUPOS for t in fichas):
        raise EstadoError(f"un grupo ({', '.join(GRUPOS)}) no se mezcla con códigos: {v!r}")
    # Un código mal formado no aborta la campaña: queda saneado («?» delante y en cada carácter fuera de
    # [a-z0-9_-], 40 como mucho) y sale rojo CODIGO_INEXISTENTE por territorio; nunca llega crudo al informe.
    fichas = [t if RE_TOKEN.fullmatch(t) else "?" + re.sub(r"[^a-z0-9_-]", "?", t)[:40] for t in fichas]
    return list(dict.fromkeys(fichas))


def traducir_eleccion(valor: str) -> dict:
    """Elección del botón → entrada `eleccion` de P12. `vigente` y `2026-11` (ensayo) se admiten; otro `AAAA-MM`
    se acepta pero no está soportado (rojo por territorio, D-137). Cualquier otra cosa es error de entrada."""
    v = str(valor or "").strip()
    if v == "vigente":
        return {"eleccion": v, "p12": "vigente", "ensayo": False, "soportada": True}
    m = re.fullmatch(r"(\d{4})-(\d{2})", v)
    if not m or not 1 <= int(m.group(2)) <= 12:
        raise EstadoError(f"elección no válida: {v!r} (vigente o AAAA-MM)")
    if v == ENSAYO_MES:
        return {"eleccion": v, "p12": ENSAYO_P12, "ensayo": True, "soportada": True}
    return {"eleccion": v, "p12": None, "ensayo": False, "soportada": False}


def _causa_territorio(codigo: str, el: dict, root: Path) -> tuple[str | None, dict]:
    """(causa roja o None, datos de la elección) por territorio, desde el catálogo real."""
    if tids.es_variante_350(codigo):
        return "CONGRESO_350", {}
    if not re.fullmatch(r"(aut|nac)\d\d", codigo) or codigo not in tids.tabla():
        return "CODIGO_INEXISTENTE", {}
    if not el["soportada"]:
        return "ELECCION_NO_SOPORTADA", {}
    if not el["ensayo"]:
        fila = (_yaml(root / REGISTRO).get("territories") or {}).get(codigo)
        if not fila:
            return "SIN_ELECCION", {}
        return None, {"election_id": str(fila["election_id"]), "election_date": str(fila["election_date"])}
    universo = _yaml(root / UNIVERSO_ENSAYO)
    filas = [r for r in universo.get("circunscripciones") or [] if str(r.get("territory_id")) == codigo]
    if not filas:
        return "SIN_ELECCION", {}
    eid = str(filas[0]["election_id"])
    contrato = (_yaml(root / CONTRATOS_ENSAYO).get("contracts") or {}).get(eid)
    if not isinstance(contrato, dict) or contrato.get("rehearsal") is not True:
        return "ENSAYO_SIN_CONTRATO", {"election_id": eid}
    return None, {"election_id": eid, "election_date": str(universo["election_date"])}


def comprobar(territorios: str, eleccion: str, hechos: dict | None = None, publicar: bool = False,
              root: Path = ROOT) -> dict:
    """Semáforo de la comprobación previa (§2, §3). Un rojo es por territorio; solo es global la entrada inválida."""
    el = traducir_eleccion(eleccion)
    codigos = resolver_territorios(territorios)
    hechos = hechos or {}
    por_terr = hechos.get("territorios") or {}
    ajenos = sorted(set(por_terr) - set(codigos))
    if ajenos:
        raise EstadoError(f"hechos de territorios fuera de la campaña: {', '.join(ajenos)}")
    filas = []
    for c in codigos:
        causa, datos = _causa_territorio(c, el, root)
        causas = [causa] if causa else []
        for h in por_terr.get(c) or []:
            if h not in AMBAR | ROJO:
                raise EstadoError(f"causa desconocida en los hechos de {c}: {h!r}")
            causas.append(h)
        causas = list(dict.fromkeys(causas))
        color = "rojo" if any(x in ROJO for x in causas) else ("ámbar" if causas else "verde")
        etiqueta = tids.etiqueta(c) if c in tids.tabla() else c
        filas.append({"territorio": c, "etiqueta": etiqueta, "color": color, "causas": causas, **datos})
    camp = hechos.get("campana") or {}
    bloqueos, avisos = [], []
    for k, codigo in (("ci_verde", "CI_NO_VERDE"), ("r2_responde", "R2_NO_RESPONDE")):
        if camp.get(k) is False:
            bloqueos.append(codigo)  # solo con evidencia positiva (lección T-246)
        elif camp.get(k) is None:
            avisos.append(f"{codigo}_SIN_COMPROBAR")
    if not any(f["color"] != "rojo" for f in filas):
        bloqueos.append("NINGUN_TERRITORIO_LANZABLE")
    if el["ensayo"] and publicar:
        avisos.append("ENSAYO_NO_PUBLICA")
    return {"eleccion": el, "territorios": filas, "lanzados": [f["territorio"] for f in filas if f["color"] != "rojo"],
            "lanzable": not bloqueos, "bloqueos": bloqueos, "avisos": avisos,
            "gasto_semanal_min": camp.get("gasto_semanal_min"), "publicar": bool(publicar) and not el["ensayo"]}


def guardar_semaforo(alm, campana: str, semaforo: dict) -> str:
    """El semáforo fija los lanzados (denominador de la parada): igual → no hace nada; distinto → error."""
    clave = f"{_prefijo(campana)}semaforo.json"
    previo = _leer_json(alm, clave)
    if previo is not None:
        if previo == json.loads(_json(semaforo)):
            return "sin_cambios"
        raise EstadoError(f"CAMPANA_SEMAFORO_DISTINTO {campana}: ya hay otra comprobación previa en el almacén")
    alm.escribir(clave, _json(semaforo))
    return "escrito"


def leer_semaforo(alm, campana: str) -> dict:
    s = _leer_json(alm, f"{_prefijo(campana)}semaforo.json")
    if not s:
        raise EstadoError(f"CAMPANA_SIN_SEMAFORO {campana}: falta la comprobación previa en el almacén")
    return s


# ─────────────────────────── pasos y recuento ───────────────────────────

def _validar_paso(semaforo: dict, territorio: str, paso: str, intento: int) -> None:
    if territorio not in semaforo["lanzados"]:
        raise EstadoError(f"{territorio!r} no es un territorio lanzado de la campaña")
    if paso not in PASOS:
        raise EstadoError(f"paso no válido: {paso!r} ({', '.join(PASOS)})")
    if not isinstance(intento, int) or intento < 1:
        raise EstadoError(f"run_attempt no válido: {intento!r}")


def _sin_hora(d: dict | None) -> dict | None:
    return None if d is None else {k: v for k, v in d.items() if k != "hora"}


def _registros(alm, campana: str) -> dict[tuple[str, str], dict[int, dict]]:
    pre = f"{_prefijo(campana)}pasos/"
    out: dict[tuple[str, str], dict[int, dict]] = {}
    for clave in alm.listar(pre):
        m = re.fullmatch(re.escape(pre) + r"([a-z0-9_-]+)/(P\d0)/(\d+)\.json", clave)
        if not m:
            raise EstadoError(f"CAMPANA_CLAVE_INESPERADA {clave}")
        d = _leer_json(alm, clave)
        if d is None:
            raise EstadoError(f"CAMPANA_OBJETO_DESAPARECIDO {clave}: listado pero no legible")
        out.setdefault((m.group(1), m.group(2)), {})[int(m.group(3))] = d
    return out


def _ultimo(regs: dict, territorio: str, paso: str) -> tuple[int, dict] | None:
    por = regs.get((territorio, paso)) or {}
    if not por:
        return None
    i = max(por)
    return i, por[i]


def umbral_parada(lanzados: int) -> int:
    """Apartados que paran la campaña: ≥20 % de los lanzados con un mínimo de 3 (71 → 15)."""
    return max(3, -(-lanzados // 5))


def _parada(apartados: list[dict], lanzados: int) -> dict:
    por_causa: dict[str, int] = {}
    for a in apartados:
        por_causa[a["causa"]] = por_causa.get(a["causa"], 0) + 1
    misma = sorted(c for c, n in por_causa.items() if n >= 3)
    total = len(apartados) >= umbral_parada(lanzados)
    motivo = []
    if misma:
        motivo.append(f"≥3 apartados con la misma causa ({', '.join(misma)})")
    if total:
        motivo.append(f"{len(apartados)} apartados ≥ {umbral_parada(lanzados)} (20 % de {lanzados}, mínimo 3)")
    return {"activa": bool(misma or total), "motivo": "; ".join(motivo), "por_causa": dict(sorted(por_causa.items()))}


def recuento(alm, campana: str, final: bool = False, jobs: dict | None = None) -> dict:
    """Estado por territorio con el ÚLTIMO intento de cada (territorio, paso). `jobs` = {territorio: {paso: conclusión}}
    de la API: un job en `success` sin salida «ok» en el almacén es apartado SALIDA_R2_AUSENTE. Con `final`, la marca
    «sin_resultado» (o un paso sin objeto) es apartado SIN_RESULTADO salvo que la parada impidiera empezarlo."""
    sem = leer_semaforo(alm, campana)
    regs = _registros(alm, campana)
    jobs = jobs or {}
    lanzados = sem["lanzados"]
    filas: dict[str, dict] = {}
    for t in lanzados:
        fila = {"estado": "sano", "paso": None, "causa": None, "intento": None}
        for paso in PASOS:
            u = _ultimo(regs, t, paso)
            concl = (jobs.get(t) or {}).get(paso)
            reg = u[1] if u else None
            fila.update(paso=paso, intento=u[0] if u else None)
            if reg and reg.get("estado") == "ok":
                continue
            if reg and reg.get("estado") == "apartado":
                fila.update(estado="apartado", causa=reg.get("causa") or CAUSA_DESCONOCIDA)
            elif concl == "success":
                fila.update(estado="apartado", causa="SALIDA_R2_AUSENTE")
            elif reg is not None:  # marca sin_resultado
                fila.update(estado="apartado" if final else "en_curso", causa="SIN_RESULTADO" if final else None)
                if final and concl:
                    fila["detalle"] = concl
            else:
                fila.update(estado="pendiente_final" if final else "pendiente")
            break
        else:
            fila.update(paso=None, intento=None)
        filas[t] = fila
    explicitos = [dict(territorio=t, **f) for t, f in filas.items() if f["estado"] == "apartado"]
    parada_curso = _parada(explicitos, len(lanzados))
    if _leer_json(alm, f"{_prefijo(campana)}parada.json"):
        parada_curso["activa"] = True
    for t, f in filas.items():
        if f["estado"] == "pendiente_final":
            if parada_curso["activa"]:
                f["estado"] = "detenido"
            else:
                f.update(estado="apartado", causa="SIN_RESULTADO")
    apartados = [dict(territorio=t, **f) for t, f in filas.items() if f["estado"] == "apartado"]
    parada = _parada(apartados, len(lanzados))
    fijada = _leer_json(alm, f"{_prefijo(campana)}parada.json")
    if fijada and not parada["activa"]:  # pegajosa: una re-ejecución que sana no reabre la campaña
        parada.update(activa=True, motivo=f"fijada: {fijada.get('motivo', '')}")
    return {"campana": campana, "final": final, "lanzados": len(lanzados), "umbral_parada": umbral_parada(len(lanzados)),
            "territorios": filas, "apartados": len(apartados), "sanos": sum(f["estado"] == "sano" for f in filas.values()),
            "parada": parada}


def empezar(alm, campana: str, territorio: str, paso: str, intento: int) -> tuple[int, str]:
    """Antes de un paso: parada → rc 10; re-ejecución de un paso con fallo no transitorio → rc 4; si no, marca
    «sin_resultado» (idempotente) y rc 0. Un paso ya sano en un intento anterior no se repite (rc 0, «ya_ok»)."""
    sem = leer_semaforo(alm, campana)
    _validar_paso(sem, territorio, paso, intento)
    rec = recuento(alm, campana)
    if rec["parada"]["activa"]:
        _fijar_parada(alm, campana, rec["parada"]["motivo"])
        return RC_PARADA, f"PARADA_SISTEMICA: {rec['parada']['motivo']}"
    regs = _registros(alm, campana)
    por = regs.get((territorio, paso)) or {}
    previos = {i: r for i, r in por.items() if i < intento}
    if previos and previos[max(previos)].get("estado") == "ok":
        return 0, "ya_ok"
    try:
        _comprobar_reejecucion(por, territorio, paso, intento)
    except NoReejecutable as exc:
        return RC_NO_REEJECUTABLE, str(exc)
    actual = por.get(intento)
    if actual is not None:
        if actual.get("estado") in ESTADOS_FINALES:
            raise EstadoError(f"CAMPANA_CLAVE_CERRADA {clave_paso(campana, territorio, paso, intento)}")
        return 0, "marca_existente"
    alm.escribir(clave_paso(campana, territorio, paso, intento),
                 _json({"campana": campana, "territorio": territorio, "paso": paso, "intento": intento,
                        "estado": "sin_resultado", "hora": _ahora()}))
    return 0, "marcado"


RESULTADOS_JOB = {"success", "failure", "cancelled", "skipped"}


def cerrar_paso(alm, campana: str, territorio: str, paso: str, intento: int, resultados: dict[str, str],
                obligatorios: list[str], huellas: dict | None = None) -> dict:
    """Cierre de un paso de la cadena (§4) desde los `needs.<job>.result` de sus jobs llamados: algún job en rojo →
    apartado FALLO_NO_CONTROLADO (la herramienta que fallaba no pudo atraparlo); algún obligatorio no «success» →
    apartado PASO_INCOMPLETO; si no, ok. Nunca cuenta como verde nada que no sea success en todos los obligatorios."""
    for job, r in resultados.items():
        if r not in RESULTADOS_JOB:
            raise EstadoError(f"resultado de job no válido: {job}={r!r}")
    faltan = [j for j in obligatorios if j not in resultados]
    if faltan:
        raise EstadoError(f"faltan resultados de jobs obligatorios: {', '.join(faltan)}")
    rojos = sorted(j for j, r in resultados.items() if r == "failure")
    incompletos = sorted(j for j in obligatorios if resultados[j] != "success")
    if rojos:
        estado, causa = "apartado", "FALLO_NO_CONTROLADO"
    elif incompletos:
        estado, causa = "apartado", "PASO_INCOMPLETO"
    else:
        estado, causa = "ok", None
    registrar(alm, campana, territorio, paso, intento, estado, causa, huellas if estado == "ok" else None)
    return {"sano": estado == "ok", "estado": estado, "causa": causa, "rojos": rojos, "incompletos": incompletos}


def _comprobar_reejecucion(por: dict, territorio: str, paso: str, intento: int) -> None:
    previos = {i: r for i, r in por.items() if i < intento}
    if not previos:
        return
    i = max(previos)
    r = previos[i]
    if r.get("estado") == "apartado" and not es_transitoria(r.get("causa")):
        raise NoReejecutable(f"NO_REEJECUTABLE: {territorio} {paso} intento {i} apartado por {r.get('causa')}")


def _fijar_parada(alm, campana: str, motivo: str) -> None:
    clave = f"{_prefijo(campana)}parada.json"
    if _leer_json(alm, clave) is None:  # la primera gana
        alm.escribir(clave, _json({"campana": campana, "motivo": motivo, "hora": _ahora()}))


def normalizar_causa(causa: str | None, salida: int | None = None) -> tuple[str, str | None]:
    """(código, texto original saneado o None). Sin código: el de la salida si es inequívoca; si no, desconocida."""
    c = str(causa or "").strip().upper()
    if not c:
        return (SALIDAS.get(salida, CAUSA_DESCONOCIDA) if salida is not None else CAUSA_DESCONOCIDA), None
    if RE_CAUSA.fullmatch(c):
        return c, None
    return CAUSA_DESCONOCIDA, re.sub(r"[^A-Za-z0-9 _.:/-]", "?", str(causa).strip())[:200]


def registrar(alm, campana: str, territorio: str, paso: str, intento: int, estado: str, causa: str | None = None,
              huellas: dict | None = None, salida: int | None = None) -> str:
    """Escribe el resultado del paso. Misma clave y mismo contenido (salvo la hora) → no hace nada; una clave ya cerrada
    con otro resultado → error (nunca se reescribe la historia de un intento)."""
    sem = leer_semaforo(alm, campana)
    _validar_paso(sem, territorio, paso, intento)
    if estado not in ESTADOS_FINALES:
        raise EstadoError(f"estado no válido: {estado!r} (ok | apartado)")
    original = None
    if estado == "ok":
        if causa or salida not in (None, 0):
            raise EstadoError("un paso «ok» no lleva causa ni salida distinta de 0")
    else:
        causa, original = normalizar_causa(causa, salida)
    nuevo = {"campana": campana, "territorio": territorio, "paso": paso, "intento": intento, "estado": estado,
             "causa": causa, "huellas": dict(sorted((huellas or {}).items())), "hora": _ahora()}
    if original:
        nuevo["causa_original"] = original
    _comprobar_reejecucion(_registros(alm, campana).get((territorio, paso)) or {}, territorio, paso, intento)
    clave = clave_paso(campana, territorio, paso, intento)
    previo = _leer_json(alm, clave)
    if previo and previo.get("estado") in ESTADOS_FINALES:
        if _sin_hora(previo) == _sin_hora(nuevo):
            return "sin_cambios"
        raise EstadoError(f"CAMPANA_CLAVE_CERRADA {clave}: ya tiene {previo.get('estado')} {previo.get('causa') or ''}".rstrip())
    alm.escribir(clave, _json(nuevo))
    if estado == "apartado":
        rec = recuento(alm, campana)
        if rec["parada"]["activa"]:
            _fijar_parada(alm, campana, rec["parada"]["motivo"])
    return "escrito"


def _ahora() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


# ─────────────────────────── cierre y resultado ───────────────────────────

def huella_estado(alm, campana: str) -> str:
    """sha256 de la lista ordenada de claves (último intento de cada territorio y paso) con su estado, causa y huellas."""
    regs = _registros(alm, campana)
    filas = []
    for (t, paso) in sorted(regs):
        i, r = _ultimo(regs, t, paso)
        filas.append([clave_paso(campana, t, paso, i), r.get("estado"), r.get("causa"), r.get("huellas") or {}])
    return hashlib.sha256(json.dumps(filas, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def rutas_robot(root: Path = ROOT) -> re.Pattern:
    try:
        texto = (root / P90).read_text(encoding="utf-8")
    except OSError as exc:
        raise EstadoError(f"CIERRE_SIN_RUTAS_ROBOT: no puedo leer {P90} ({exc})") from exc
    m = re.search(r"RUTAS_ROBOT:\s*'([^']+)'", texto)
    if not m:
        raise EstadoError(f"CIERRE_SIN_RUTAS_ROBOT: no encuentro RUTAS_ROBOT en {P90}")
    try:
        return re.compile(m.group(1))
    except re.error as exc:
        raise EstadoError(f"CIERRE_SIN_RUTAS_ROBOT: RUTAS_ROBOT no es una expresión válida ({exc})") from exc


def plan_cierre(alm, campana: str, ref: str, run_id: str, ensayo: bool, ficheros: list[str], root: Path = ROOT) -> dict:
    """Commit de cierre (§6, §10): en `main` solo si la ejecución viene de `refs/heads/main`; si no, rama
    `p00-cierre/<run_id>`. En ensayo, sin ficheros ni commit. Toda ruta debe casar con RUTAS_ROBOT de P90 (D-147:
    `configuracion/catalogo_preparacion.yaml` es la única excepción: no está en RUTAS_ROBOT y el cierre sí lo escribe)."""
    if not re.fullmatch(r"\d+", str(run_id)):
        raise EstadoError(f"run_id no válido: {run_id!r}")
    lista = [] if ensayo else sorted(dict.fromkeys(ficheros))
    patron = rutas_robot(root)
    ajenas = [f for f in lista if f != CATALOGO_CIERRE and not patron.match(f)]
    if ajenas:
        raise EstadoError(f"CIERRE_RUTA_NO_ROBOT: {', '.join(map(repr, ajenas))} (fuera de RUTAS_ROBOT de P90; "
                          f"D-147: solo {CATALOGO_CIERRE} entra en el cierre fuera de esa lista)")
    huella = huella_estado(alm, campana)
    rama = "main" if ref == "refs/heads/main" else f"p00-cierre/{run_id}"
    return {"campana": campana, "rama": rama, "ficheros": lista, "commit": bool(lista), "huella": huella,
            "mensaje": f"P00 campaña {campana} · cierre · huella {huella[:12]}"}


def registrar_cierre(alm, campana: str, huella: str, rama: str, sha: str | None) -> str:
    """Objeto «cierre» en el almacén, SOLO tras confirmar el push (o sin commit en ensayo). Misma huella → no hace nada;
    otra huella con un cierre ya hecho → error. La huella debe ser la del estado actual."""
    actual = huella_estado(alm, campana)
    if huella != actual:
        raise EstadoError(f"CIERRE_HUELLA_DISTINTA: {huella[:12]} ≠ estado {actual[:12]}")
    clave = f"{_prefijo(campana)}cierre.json"
    previo = _leer_json(alm, clave)
    nuevo = {"campana": campana, "huella": huella, "rama": rama, "sha": sha}
    if previo:
        if previo == nuevo:
            return "sin_cambios"
        raise EstadoError(f"CIERRE_YA_HECHO {campana}: {previo.get('huella', '')[:12]} en {previo.get('rama')}")
    alm.escribir(clave, _json(nuevo))
    return "escrito"


def resultado(alm, campana: str, jobs: dict | None = None) -> tuple[int, dict]:
    rec = recuento(alm, campana, final=True, jobs=jobs)
    cierre = _leer_json(alm, f"{_prefijo(campana)}cierre.json")
    pendiente = not cierre or cierre.get("huella") != huella_estado(alm, campana)
    motivos = []
    if rec["apartados"]:
        motivos.append(f"{rec['apartados']} apartado(s)")
    if rec["parada"]["activa"]:
        motivos.append("parada sistémica")
    if pendiente:
        motivos.append("cierre pendiente")
    return (RC_ROJO if motivos else 0), {"recuento": rec, "cierre": cierre, "cierre_pendiente": pendiente, "motivos": motivos}


# ─────────────────────────────── informe ───────────────────────────────

def informe(alm, campana: str, jobs: dict | None = None) -> str:
    sem = leer_semaforo(alm, campana)
    rc, res = resultado(alm, campana, jobs)
    rec = res["recuento"]
    el = sem["eleccion"]
    eleccion = f"{el['eleccion']} (ensayo: no persiste, no commitea, no publica)" if el["ensayo"] else el["eleccion"]
    color = {f["territorio"]: f for f in sem["territorios"]}
    out = [f"## P00 Campaña · {campana}", "",
           f"- Elección: {eleccion}",
           f"- Resultado: {'rojo' if rc else 'verde'}" + (f" ({'; '.join(res['motivos'])})" if res["motivos"] else ""),
           f"- Lanzados: {rec['lanzados']} · sanos: {rec['sanos']} · apartados: {rec['apartados']}"
           f" · umbral de parada: {rec['umbral_parada']}",
           f"- Parada sistémica: {'sí — ' + rec['parada']['motivo'] if rec['parada']['activa'] else 'no'}",
           "- Cierre: " + ("pendiente" if res["cierre_pendiente"] else
                           f"hecho en `{res['cierre']['rama']}` ({res['cierre']['sha'] or 'sin commit'}), huella "
                           f"`{res['cierre']['huella'][:12]}`"), "",
           "| Territorio | Semáforo | Estado | Paso | Causa |", "|---|---|---|---|---|"]
    for t, f in rec["territorios"].items():
        c = color[t]
        out.append(f"| {c['etiqueta']} | {c['color']} | {f['estado']} | {f['paso'] or '—'} | {f['causa'] or '—'} |")
    if rec["parada"]["por_causa"]:
        out += ["", "**Apartados por causa**", ""] + [f"- `{k}`: {n}" for k, n in rec["parada"]["por_causa"].items()]
    rojos = [f for f in sem["territorios"] if f["color"] == "rojo"]
    if rojos:
        out += ["", "**Rojos de la comprobación previa** (no se lanzaron; no cuentan como apartados)", ""]
        out += [f"- {f['etiqueta']}: {', '.join(f['causas'])}" for f in rojos]
    if sem.get("avisos"):
        out += ["", "**Avisos**: " + ", ".join(sem["avisos"])]
    return "\n".join(out) + "\n"


# ───────────────────────── comprobación previa: campaña ─────────────────────────

VIVOS = {"in_progress", "queued", "waiting", "requested", "pending"}


def segunda_campana(runs: list[dict], run_id: int) -> tuple[int, str]:
    """D-147 (§3, §16.1): rc 3 si otra ejecución de P00 de run_id MENOR sigue viva (también «solo comprobar» o `waiting`).
    Las de la prueba de humo (`pull_request`) y las terminadas no cuentan. Las de run_id mayor se rechazan solas."""
    propio = int(run_id)
    otras = []
    for r in runs:
        if not isinstance(r, dict) or not isinstance(r.get("id"), int) or not isinstance(r.get("status"), str):
            raise EstadoError(f"ejecución no válida en la lista: {r!r}")
        if r["id"] != propio and r["status"] in VIVOS and r.get("event") != "pull_request":
            otras.append(r["id"])
    previas = sorted(i for i in otras if i < propio)
    if previas:
        return RC_NO_LANZABLE, (f"CAMPANA_EN_CURSO: hay otra campaña en curso (run {previas[0]}); esta se rechaza sin "
                                "lanzar nada (D-147). La cancela el Operador con frase del propietario.")
    return 0, "sin otra campaña en curso"


def hechos_campana(runs_p90: list[dict], sha: str, r2_responde: bool | None, metricas: dict | None = None) -> dict:
    """Hechos de campaña (§3): CI de ESTA versión (ejecuciones de P90 con su head_sha; un rojo bloquea, un verde sin rojo
    acredita, nada concluyente → None = aviso), R2 y gasto de la semana actual (D-46, de orchestracion/metricas_proceso.json)."""
    if not re.fullmatch(r"[0-9a-f]{40}", str(sha)):
        raise EstadoError(f"sha no válido: {sha!r}")
    conclusiones = {r.get("conclusion") for r in runs_p90
                    if isinstance(r, dict) and r.get("head_sha") == sha and r.get("status") == "completed"
                    and r.get("event") in ("push", "schedule", "pull_request")}
    ci = False if "failure" in conclusiones else (True if "success" in conclusiones else None)
    semanas = (((metricas or {}).get("minutos_actions") or {}).get("gasto_semanal") or {}).get("por_semana") or []
    gasto = semanas[-1].get("minutos") if semanas and isinstance(semanas[-1], dict) else None
    return {"campana": {"ci_verde": ci, "r2_responde": r2_responde, "gasto_semanal_min": gasto}}


def _lista(d: dict | list, clave: str) -> list:
    v = d.get(clave) if isinstance(d, dict) else d
    if not isinstance(v, list):
        raise EstadoError(f"se esperaba una lista en «{clave}»")
    return v


# ─────────────────────────────── CLI ───────────────────────────────

def _cargar(ruta: str | None) -> dict:
    if not ruta:
        return {}
    try:
        d = json.loads(Path(ruta).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise EstadoError(f"no puedo leer {ruta}: {exc}") from exc
    if not isinstance(d, dict):
        raise EstadoError(f"{ruta} no es un objeto JSON")
    return d


def _imprimir(obj) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    sub = ap.add_subparsers(dest="accion", required=True)

    def con_campana(p):
        p.add_argument("--almacen", required=True, help="r2 | dir:<ruta>")
        p.add_argument("--campana", required=True, help="id de campaña (run_id de P00)")
        return p

    def con_paso(p):
        con_campana(p)
        p.add_argument("--territorio", required=True)
        p.add_argument("--paso", required=True, choices=PASOS)
        p.add_argument("--intento", required=True, type=int, help="run_attempt")
        return p

    p = sub.add_parser("comprobar", help="semáforo de la comprobación previa")
    p.add_argument("--territorios", required=True, help="todos | congreso | autonómicas | nac22, aut11")
    p.add_argument("--eleccion", default="vigente", help="vigente | AAAA-MM (2026-11 = ensayo)")
    p.add_argument("--hechos", help="JSON {territorios: {código: [causas]}, campana: {ci_verde, r2_responde, gasto_semanal_min}}")
    p.add_argument("--publicar", action="store_true")
    p.add_argument("--almacen", help="si se da con --campana, guarda el semáforo")
    p.add_argument("--campana")
    p.add_argument("--root-dir", default=str(ROOT))
    con_paso(sub.add_parser("empezar", help="antes de un paso: parada, re-ejecución y marca sin_resultado"))
    p = con_paso(sub.add_parser("registrar", help="resultado de un paso"))
    p.add_argument("--estado", required=True, choices=sorted(ESTADOS_FINALES))
    p.add_argument("--causa", help="código de causa impreso por la herramienta (se normaliza)")
    p.add_argument("--salida", type=int, help="código de salida del proceso, si no hay código de causa")
    p.add_argument("--huellas", help="JSON {nombre: sha256}")
    for nombre, ayuda in (("recuento", "apartados y parada"), ("resultado", "rc 1 si hay apartados, parada o cierre pendiente"),
                          ("informe", "markdown para el issue")):
        p = con_campana(sub.add_parser(nombre, help=ayuda))
        p.add_argument("--jobs", help="JSON {territorio: {paso: conclusión}} de la API de Actions")
        if nombre == "recuento":
            p.add_argument("--final", action="store_true")
    p = con_campana(sub.add_parser("plan-cierre", help="rama, ficheros y huella del commit de cierre"))
    p.add_argument("--ref", required=True)
    p.add_argument("--run-id", required=True)
    p.add_argument("--fichero", action="append", default=[])
    p.add_argument("--root-dir", default=str(ROOT))
    p = con_campana(sub.add_parser("registrar-cierre", help="objeto cierre tras confirmar el push"))
    p.add_argument("--huella", required=True)
    p.add_argument("--rama", required=True)
    p.add_argument("--sha")
    p = con_paso(sub.add_parser("cerrar-paso", help="registrar un paso desde los resultados de sus jobs"))
    p.add_argument("--resultados", required=True, help='JSON {job: success|failure|cancelled|skipped}')
    p.add_argument("--obligatorio", action="append", default=[], help="job que debe estar en success")
    p.add_argument("--huellas", help="JSON {nombre: sha256} (solo si el paso queda ok)")
    p = sub.add_parser("concurrencia", help="rc 3 si hay otra campaña viva de run_id menor (D-147)")
    p.add_argument("--runs", required=True, help="JSON de GET actions/workflows/<p00>/runs ({workflow_runs: [...]})")
    p.add_argument("--run-id", required=True, type=int)
    p = sub.add_parser("hechos", help="hechos de campaña para comprobar --hechos")
    p.add_argument("--runs-p90", required=True, help="JSON de GET actions/workflows/p90-automatico.yml/runs?head_sha=<sha>")
    p.add_argument("--sha", required=True)
    p.add_argument("--r2", choices=("ok", "fallo", "desconocido"), default="desconocido")
    p.add_argument("--metricas", help="orchestracion/metricas_proceso.json")
    ns = ap.parse_args(argv)
    try:
        if ns.accion == "comprobar":
            s = comprobar(ns.territorios, ns.eleccion, _cargar(ns.hechos), ns.publicar, Path(ns.root_dir))
            if ns.almacen and ns.campana:
                guardar_semaforo(almacen(ns.almacen), ns.campana, s)
            _imprimir(s)
            if not s["lanzable"]:
                _error(f"CAMPANA_NO_LANZABLE: {', '.join(s['bloqueos'])}")
                return RC_NO_LANZABLE
            return 0
        if ns.accion == "concurrencia":
            rc, msg = segunda_campana(_lista(_cargar(ns.runs), "workflow_runs"), ns.run_id)
            (print if rc == 0 else _error)(msg)
            return rc
        if ns.accion == "hechos":
            met = _cargar(ns.metricas) if ns.metricas and Path(ns.metricas).exists() else {}
            r2 = {"ok": True, "fallo": False}.get(ns.r2)
            _imprimir(hechos_campana(_lista(_cargar(ns.runs_p90), "workflow_runs"), ns.sha, r2, met))
            return 0
        alm = almacen(ns.almacen)
        if ns.accion == "empezar":
            rc, msg = empezar(alm, ns.campana, ns.territorio, ns.paso, ns.intento)
            (print if rc == 0 else _error)(msg)
            return rc
        if ns.accion == "registrar":
            huellas = json.loads(ns.huellas) if ns.huellas else None
            if huellas is not None and not isinstance(huellas, dict):
                raise EstadoError("--huellas debe ser un objeto JSON {nombre: sha256}")
            print(registrar(alm, ns.campana, ns.territorio, ns.paso, ns.intento, ns.estado, ns.causa, huellas, ns.salida))
            return 0
        if ns.accion == "cerrar-paso":
            try:
                res = json.loads(ns.resultados)
                huellas = {k: v for k, v in json.loads(ns.huellas).items() if v} if ns.huellas else None
            except ValueError as exc:
                raise EstadoError(f"JSON no válido: {exc}") from exc
            if not isinstance(res, dict):
                raise EstadoError("--resultados debe ser un objeto JSON")
            _imprimir(cerrar_paso(alm, ns.campana, ns.territorio, ns.paso, ns.intento, res, ns.obligatorio, huellas))
            return 0
        if ns.accion == "recuento":
            r = recuento(alm, ns.campana, ns.final, _cargar(ns.jobs))
            _imprimir(r)
            if r["parada"]["activa"]:
                _error(f"PARADA_SISTEMICA: {r['parada']['motivo']}")
                return RC_PARADA
            return 0
        if ns.accion == "resultado":
            rc, r = resultado(alm, ns.campana, _cargar(ns.jobs))
            _imprimir(r)
            if rc:
                _error(f"CAMPANA_RESULTADO_ROJO: {'; '.join(r['motivos'])}")
            return rc
        if ns.accion == "informe":
            print(informe(alm, ns.campana, _cargar(ns.jobs)), end="")
            return 0
        if ns.accion == "plan-cierre":
            sem = leer_semaforo(alm, ns.campana)
            _imprimir(plan_cierre(alm, ns.campana, ns.ref, ns.run_id, sem["eleccion"]["ensayo"], ns.fichero, Path(ns.root_dir)))
            return 0
        if ns.accion == "registrar-cierre":
            print(registrar_cierre(alm, ns.campana, ns.huella, ns.rama, ns.sha))
            return 0
    except NoReejecutable as exc:
        _error(str(exc))
        return RC_NO_REEJECUTABLE
    except (EstadoError, ValueError) as exc:
        _error(str(exc))
        return RC_ENTRADA
    return RC_ENTRADA


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
