#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Batería del motor (T-132): entradas reproducibles desde fuente, M04-M06 en local y matriz territorio × regla.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.4.3
NOMBRE DE VERSIÓN: Batería del motor
FECHA: 2026-11-16
ESTADO: candidato
CAMBIOS 1.4.3 (T-384): el error BATERIA_FALTA_PAQUETE_P10 remite a «P70 Archivo · P71 archivar · paquete de fuentes de un territorio»
  (el workflow bateria-motor y su entrada archivar_p10 ya no existen: P80, D-132). Solo cambia el texto; sin run id ni parámetros técnicos (D-130).
CAMBIOS 1.4.2 (T-297): el recuento de candidatos cuenta el candidato exacto de Deslinde 1.1 (generador «exacto», solo con D8 y
  cuando aporta plan): esperados = 1 + N (+1 exhaustivo) (+1 exacto) (+1 vigente que compite); el exacto no es una cadena.
CAMBIOS 1.4.1 (T-304): `entradas_uno` decide REUSE ANTES de ejecutar_fuentes_workflow (resolve_source_action sin fuente oficial disponible: o REUSE o
  BLOCK, nunca ACQUIRE): un paquete que la política no reutilizaría falla sin llegar a ejecutar nada ni a la red. La comprobación posterior
  del log se conserva.
CAMBIOS 1.4.0 (T-303): la batería parte de la FUENTE, no de un M03 archivado (Deslinde 1.1 cambia M02/M03 y lo habría invalidado).
  `archivar-p10` sube a R2 (ARC-E) el paquete P10 de la fuente del territorio, `arc-e/paquetes-p10/<package_sha256>.zip` (el sha256
  del bundle es el package_sha256 del contrato; se comprueba al archivar y al leer). `entradas` lo baja, lo valida como la 00
  (`validate_prepared_package`), lo restaura como checkpoint de fuentes (la política de fuentes debe decidir REUSE: nunca adquiere) y
  EJECUTA M01, M02 y M03 con el código vigente y el contrato: cambiar M02/M03 cambia lo calculado, no hay grafo viejo en uso.
  Se retiran `archivar` y las entradas mínimas (arc-e/entradas-minimas, M01+M03) de T-298. Sin paquete: BATERIA_FALTA_PAQUETE_P10;
  paquete de otro contrato o alterado: BATERIA_PAQUETE_P10_CORRUPTO. `--desde-fuente` (diagnóstico local, sin red salvo
  --permitir-red-ine) reconstruye desde las fuentes nacionales verificadas (orchestracion/fuentes_r2.json).
CAMBIOS 1.3.0 (T-298): ver legacy/herramientas/bateria_motor_v1.3.0_20261114.py (R2 por identidad, sin INE por defecto).
CAMBIOS 1.2.5 (T-258): un único vigente. `composicion_publicada` delega en ddd_motor2.vigente.vigente_publicado, el
  mismo que usa la competición (generadores 1.2.2); si el run publicado no tiene composición versionada ya no cae en
  datos/composicion/<t>.csv de otro run (Canarias). `indicadores`: si el bloque «vigente» del COMPETICION.json no es
  del fichero publicado (sha256) → NO_EVALUABLE «vigente distinto del publicado»; si es VIGENTE_OTRO_SECCIONADO →
  SIN_VIGENTE con su motivo. `aceptacion` (T-224): SIN_VIGENTE (sin vigente comparable) consta en
  «vigente_no_comparable» y no bloquea; NO_EVALUABLE y sin INDICADORES.json siguen bloqueando. El canónico de la
  comparación es el del COMPETICION.json (el del run en el P30). La clave y el resto de comprobaciones no cambian.
CAMBIOS 1.2.4 (T-233): si `entradas_uno` falla (adquisición o M01-M03), copia a la salida del paso las últimas 60 líneas
  de log.txt y una línea `::error` con el estado, el rc y el motivo (última línea de error del log). Antes la traza solo
  estaba en el artefacto (403 desde la nube). La adquisición, los reintentos y la salida de éxito no cambian.
CAMBIOS 1.2.3 (T-229): `indicadores` lee bien el vigente en los cuatro territorios que la fase 2 de r5 (run 42927322822)
  dejó «sin comparación». (a) Canarias y Cataluña: el vigente publicado reparte unidades M04 de municipios divisibles; si al
  montarlo sobre el canónico salen unidades repartidas, se usa la composición que escribió el generador `vigente` en la
  competición (piezas finas, una unidad por distrito; la publicada, no la reparada), solo si reproduce sección a sección el
  fichero publicado; si no, sigue «sin comparación» con el motivo. (b) Extremadura y Asturias (unidades internas): un
  candidato sin GeoJSON propio (el vigente) se evaluaba sin atributos y faltaba unidad_r012; usa los del canónico, como el
  generador. El criterio no cambia.
CAMBIOS 1.2.2 (T-228): la comprobación 2 (y el desvío máximo de los indicadores) mide como el contrato y la competición
  (D-68, D-79, T-211): contra el objetivo REGIONAL (`Natural.fuera_regional`, el primer término de la clave D8 de la
  competición), no contra el objetivo de cada circunscripción. Las cifras por circunscripción siguen en el JSON
  (`fuera_tolerancia_circunscripcion`, `desvio_max_circunscripcion`), solo informan. Antes, r5 fase 2 (run 42927322822):
  Castilla-La Mancha salía PEOR (6 > 5 por circunscripción) con el ganador en 5 del contrato, igual que el vigente (5 y 5).
CAMBIOS 1.2.1 (T-222): el recuento de candidatos cuenta el vigente que compite (T-217): esperados = 1 + N (+1 exhaustivo)
  (+1 si el COMPETICION.json dice que el vigente compite y lo trae como candidato). El vigente no cuenta como cadena ni como
  cadena evaluable. Si no compite (no cumple el núcleo, no representable, fallo, o sin bloque «vigente»), consta en «vigente_excluido» con su motivo
  y no cuenta; si «compite» y la lista de candidatos no cuadran entre sí, el territorio queda en candidatos_incompletos (NO).
  Antes la fase 1 de r4 (run 42913861593: Madrid y Navarra, 12/12 VALIDO) salió NO por esperar 11.
CAMBIOS 1.2.0 (T-212): criterio «nunca peor que el mapa vigente publicado»: `indicadores` (por territorio, en el job: fuera de
  tolerancia, desvío máximo, partidos judiciales y comarcas partidos, frontera cortada y Polsby-Popper del vigente
  (datos/composicion), el canónico y el ganador, a INDICADORES.json/md y al resumen del paso) y `aceptacion` compara el ganador
  también con el vigente, con DOS comprobaciones por separado (Planificador): 1) la clave de elección del ganador nunca peor que la
  del canónico; 2) el recuento BRUTO de distritos fuera de tolerancia nunca peor que el del vigente. El desvío máximo mayor que el
  del vigente sale como aviso aparte y no bloquea. Sin composición vigente o no comparable, el territorio consta explícitamente y no hay aceptación.
CAMBIOS 1.1.1 (T-181): `aceptacion` exige al menos una cadena evaluable por territorio y ningún FALLO_GENERADOR (se leen del
  COMPETICION.json del territorio; sin él, NO), `--cadenas N`: candidatos = 1 + N (+1 exhaustivo), todos evaluados y cada cadena inválida con motivo. Antes un territorio donde fallaban todas las cadenas daba «SÍ» (ganador = canónico).
CAMBIOS 1.1.0 (T-208): subcomandos `lista` (matriz de territorios para Actions), `huella` (huella real: dos ejecuciones de la
  competición del motor 2 con igual huella) y `aceptacion` (une los resultados por territorio y aplica el criterio de
  T-194); `entradas` descarga las copias nacionales solo si hace falta (antes fallaba si faltaban). Nada cambia en `motor`.
CAMBIOS 1.0.1 (T-201): `composicion_publicada` solo cuenta los canonical_m06 de la elección por defecto (2023-07-23).
MOTIVO: responder en minutos y sin lanzar nada si el motor vigente produce distritos válidos en los 71 territorios
  (52 circunscripciones del Congreso + 19 comunidades) y qué cambia entre versiones del motor (decisión del
  propietario: opción B, batería primero).
CAMBIOS 1.2.6 (T-220): ids de territorio nuevos de la tabla maestra (aut01…nac52, D-61); el id viejo se lee vía ddd_core.territorio_ids.
ANTERIOR: legacy/herramientas/bateria_motor_v1.4.2_20261116.py
QUÉ HACE: subcomandos
  nacionales  copias nacionales oficiales con sha256 en inputs/_nacional/: seccionado INE 2023/2024/2025 (shapefile
              nacional; el 2025 sale de inputs/partes) y la tabla INE 65034 (de inputs/partes, convertida a «;» como
              la descarga en vivo y reducida a Sexo=Total y Edad=Todas las edades, que es lo único que usa el filtro).
  entradas    por territorio, T-303: paquete P10 de la fuente (R2, ARC-E, package_sha256 del contrato, verificado) → restauración de fuentes
              como la 00 (REUSE) → M01, M02 y M03 con el código vigente y el contrato (+ preparar_unidades_internas); guarda en
              <out>/entradas/<t>/ M01 + grafo con su sha256 (ENTRADAS.json) y compara la huella de población y seccionado con la del
              contrato. Nunca va al INE. Sin paquete BATERIA_FALTA_PAQUETE_P10; paquete alterado o de otro contrato
              BATERIA_PAQUETE_P10_CORRUPTO. Solo con --desde-fuente (diagnóstico local): adquisición desde las copias nacionales.
  archivar-p10 <t> --paquete <carpeta> --run <id>  sube a R2 el paquete P10 (artefacto ddd-source-package-* descomprimido) tras comprobar
              que es el del contrato; deja ARCHIVO_PAQUETES_P10.json (clave, sha256, bytes, run de origen, fecha).
  motor       por territorio: restaura las entradas, ejecuta M04, M05 canónico (o el motor base M05 de una versión
              legacy con --m05) y M06, y la validación de producción herramientas/validar_ejecucion.py (la misma
              regla, sin reglas paralelas); compara la partición con datos/composicion/<t>.csv.
  matriz      junta los resultados en <out>/MATRIZ.csv y <out>/MATRIZ.md (territorio × regla, tiempos, semilla,
              igualdad con lo publicado y entre versiones del motor).
  lista       JSON {"include":[{"t":...}]} con los territorios pedidos (o los 71) para la matriz de Actions.
  huella      huella real (criterio a de T-194): repite la competición del motor 2 en <out>/_huella2 y compara la
              huella_resultado con la de <out>/competicion/<t>/RESUMEN.json; escribe HUELLA_REAL.json junto a ella.
  indicadores indicadores de naturalidad del vigente, el canónico y el ganador de un territorio (ver CAMBIOS 1.2.0).
  aceptacion  une <out>/**/competicion/<t>/RESUMEN.json y aplica el criterio de aceptación del motor 2 (docs/ARQUITECTURA/
              ACEPTACION_MOTOR2.md): todos válidos, ninguno peor que el canónico ni que el vigente y huella real igual en Soria, Álava
              y Melilla; escribe ACEPTACION.json/md y RESUMEN.{json,md}; sale 1 si no se cumple.
USO: python herramientas/bateria_motor.py nacionales
     python herramientas/bateria_motor.py entradas --todos
     python herramientas/bateria_motor.py motor --todos [--m05 7.4.2]
     python herramientas/bateria_motor.py matriz
No escribe en el contrato ni en el motor: la declaración temporal de fuentes va a territorios/<t>/config/ (las rutas
se resuelven respecto al contrato) y se borra al terminar.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import yaml  # noqa: E402
import sys as _sys_t220  # noqa: E402
from pathlib import Path as _Path_t220  # noqa: E402
if str(_Path_t220(__file__).resolve().parents[1]) not in _sys_t220.path:
    _sys_t220.path.insert(0, str(_Path_t220(__file__).resolve().parents[1]))
from ddd_core.territorio_ids import carpeta_de  # noqa: E402  (T-220: id viejo o nuevo)

NACIONAL = ROOT / "inputs" / "_nacional"
OUT = ROOT / "bateria"
URL_SECCIONADO = "https://www.ine.es/prodyser/cartografia/seccionado_{}.zip"
URL_65034 = "https://www.ine.es/jaxiT3/files/t/csv_bdsc/65034.csv"
EDICIONES = (2023, 2024, 2025)
REGLAS = ("K", "atomicidad", "poblacion", "contiguidad", "provincia", "municipal", "otras")
M05_BASE = {
    "7.4.4": ROOT / "ddd_core" / "m05_opt_engine_v741.py",
    "7.4.3": ROOT / "legacy" / "ddd_core" / "m05_opt_engine_v7.4.3_20261108.py",
    "7.4.2": ROOT / "legacy" / "ddd_core" / "m05_opt_engine_v7.4.2_20261108.py",
}
FECHA_ZIP = (2025, 1, 1, 0, 0, 0)
# Entrada mínima de M04 (orden del propietario, 10-11): M01 secciones con población y grafo M03; con ellas M04-M06 dan la
# misma partición (comprobado en Congreso Madrid, con unidades internas). Lo demás queda solo como sha256 en ENTRADAS.json.
ENTRADA_MINIMA = ("_m01_secciones_poblacion.geojson.zip", "_m03_grafo.json")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def territorios() -> list[str]:
    out = []
    for d in sorted((ROOT / "territorios").iterdir()):
        t = d.name
        if t == "congreso" or t.startswith("congreso350_"):
            continue
        if (d / "config" / f"{t}_2025.yaml").is_file() and (d / "config" / "fuentes_oficiales.yaml").is_file():
            out.append(t)
    return out


def contrato(t: str) -> Path:
    return ROOT / "territorios" / carpeta_de(ROOT, t) / "config" / f"{t}_2025.yaml"


# --------------------------------------------------------------------------- nacionales
INDICE_FUENTES = ROOT / "orchestracion" / "fuentes_r2.json"


class FuenteNacionalError(RuntimeError):
    pass


class PaqueteP10Corrupto(RuntimeError):
    """El paquete existe en R2 pero no es de la identidad vigente o un fichero no cuadra con su sha256."""


def _espejo() -> dict:
    return json.loads(INDICE_FUENTES.read_text(encoding="utf-8"))["fuentes"]


def _bajar_r2(clave: str, dest: Path) -> None:
    _r2_cp(f"s3://{os.environ['R2_BUCKET']}/{clave}", str(dest))


def obtener_fuente_nacional(nombre: str, destino: Path) -> Path:
    """Deja ``destino/nombre`` con el sha256 de orchestracion/fuentes_r2.json (ARC-E). Solo para --desde-fuente. Orden: copia local, carpeta
    DDD_ESPEJO_DIR, inputs/partes (2025 y 65034), R2 (arc-e/fuentes/ine/...). Nunca ine.es; sha256 distinto = FuenteNacionalError."""
    ficha = _espejo().get(nombre)
    if ficha is None:
        raise FuenteNacionalError(f"{nombre}: no está en {INDICE_FUENTES.name}")
    esperado = ficha["sha256"]
    dest = destino / nombre
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_file() and sha256(dest) == esperado:
        return dest
    dest.unlink(missing_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    local = os.environ.get("DDD_ESPEJO_DIR")
    partes = ROOT / "inputs" / "partes"
    if local and (Path(local) / nombre).is_file():
        shutil.copyfile(Path(local) / nombre, tmp)
    elif nombre in ("seccionado_2025.zip", "65034.csv.zip") and sorted(partes.glob(nombre + ".part*")):
        with open(tmp, "wb") as fh:
            for p in sorted(partes.glob(nombre + ".part*")):
                fh.write(p.read_bytes())
    else:
        try:
            _bajar_r2(ficha["clave"], tmp)
        except Exception as exc:  # noqa: BLE001
            tmp.unlink(missing_ok=True)
            raise FuenteNacionalError(f"{nombre}: sin copia local ni R2 {ficha['clave']} ({exc})") from exc
    if sha256(tmp) != esperado:
        obtenido = sha256(tmp)
        tmp.unlink(missing_ok=True)
        raise FuenteNacionalError(f"{nombre}: sha256 {obtenido} distinto del esperado {esperado}")
    tmp.rename(dest)
    return dest


def nacionales(args) -> int:
    NACIONAL.mkdir(parents=True, exist_ok=True)
    for nombre in ("65034.csv.zip", "seccionado_2025.zip"):
        if (ROOT / "inputs" / nombre).is_file() and not (NACIONAL / nombre).is_file():
            shutil.move(str(ROOT / "inputs" / nombre), NACIONAL / nombre)
    for nombre in ["65034.csv.zip", *(f"seccionado_{ed}.zip" for ed in EDICIONES)]:
        obtener_fuente_nacional(nombre, NACIONAL)
    totales = NACIONAL / "65034_totales.csv.zip"
    if not totales.is_file():
        buf = io.StringIO()
        with zipfile.ZipFile(NACIONAL / "65034.csv.zip") as zf, zf.open("65034.csv") as raw:
            reader = csv.reader(io.TextIOWrapper(raw, encoding="utf-8-sig", newline=""), delimiter="\t")
            w = csv.writer(buf, delimiter=";", lineterminator="\n")
            cab = next(reader)
            w.writerow(cab)
            i_sexo, i_edad = cab.index("Sexo"), cab.index("Edad")
            for row in reader:
                if row[i_sexo] == "Total" and row[i_edad] == "Todas las edades":
                    w.writerow(row)
        with zipfile.ZipFile(totales, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(zipfile.ZipInfo("65034.csv", FECHA_ZIP), buf.getvalue().encode("utf-8"))
    manifest = {
        "schema": "ddd.bateria-nacionales/1.0",
        "ficheros": {p.name: {"sha256": sha256(p), "bytes": p.stat().st_size} for p in sorted(NACIONAL.glob("*.zip"))},
        "origen": {"indice": str(INDICE_FUENTES.relative_to(ROOT)), "seccionado": URL_SECCIONADO, "65034": URL_65034},
    }
    (NACIONAL / "NACIONALES.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(manifest["ficheros"], indent=1))
    return 0


# --------------------------------------------------------------------------- entradas
def _declaracion_temporal(t: str, nac: dict, seccionado: str) -> Path:
    base = ROOT / "territorios" / carpeta_de(ROOT, t) / "config"
    d = yaml.safe_load((base / "fuentes_oficiales.yaml").read_text(encoding="utf-8"))
    terr = d.setdefault("territory", {})
    if not terr.get("section_year") or not terr.get("population_year"):
        # Declaración incompleta (p. ej. esquema 1.1): años y seccionado del contrato; queda anotado.
        meta = (_cfg(t).get("meta") or {})
        terr["population_year"] = int(meta.get("source_population_year") or terr.get("edition"))
        terr["section_year"] = int(meta.get("source_section_year") or terr.get("edition"))
        d["source_bindings"]["secciones_censales"]["materialized_path"] = f"inputs/seccionado_{terr['section_year']}.zip"
        d["_bateria_declaracion_completada_desde_contrato"] = True
    ed_sec = int(terr.get("section_year") or terr.get("edition"))
    ed_pob = int(terr.get("population_year") or terr.get("edition"))
    b = d["source_bindings"]
    tmp = base / "_bateria_fuentes.yaml"
    if seccionado == "ogc":
        tmp.write_text(yaml.safe_dump(d, allow_unicode=True, sort_keys=False), encoding="utf-8")
        return tmp
    pob = "65034_totales.csv.zip"
    sec = f"seccionado_{ed_sec}.zip"
    b["poblacion_por_sexo_y_edad"]["snapshot"] = {
        "path": f"inputs/_nacional/{pob}", "expected_sha256": nac[pob]["sha256"],
        "official_origin_url": URL_65034, "edition": ed_pob, "acquired_at": "2026-02-16"}
    b["secciones_censales"]["snapshot"] = {
        "path": f"inputs/_nacional/{sec}", "expected_sha256": nac[sec]["sha256"],
        "official_origin_url": URL_SECCIONADO.format(ed_sec), "edition": ed_sec, "acquired_at": "2026-11-09"}
    if ed_pob != ed_sec:
        origen = f"seccionado_{ed_pob}.zip"
        b["secciones_censales"]["population_sectioning_snapshot"] = {
            "path": f"inputs/_nacional/{origen}", "expected_sha256": nac[origen]["sha256"],
            "official_origin_url": URL_SECCIONADO.format(ed_pob), "edition": ed_pob, "acquired_at": "2026-11-09"}
    pol = d.setdefault("environment_policy", {})
    for env in ("development", "test", "production"):
        pol[env] = sorted(set(pol.get(env) or []) | {"verified_snapshot"})
    tmp.write_text(yaml.safe_dump(d, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return tmp


def _cfg(t: str) -> dict:
    return yaml.safe_load(contrato(t).read_text(encoding="utf-8"))


def _cache(t: str) -> Path:
    os.environ.setdefault("DDD_RUN_ID", f"bateria-{t}")
    from ddd_core.config import load_params_yaml, module_cfg
    cfg = load_params_yaml(str(contrato(t)))
    return Path(module_cfg(cfg, "modulo_03_construir_grafo", "step3_build_graph")["out_graph_json"]).parent


def _huellas_contrato(cfg: dict) -> dict:
    out = {}
    for item in ((cfg.get("generation_state") or {}).get("source_inputs") or []):
        if isinstance(item, dict) and item.get("path"):
            out[str(item["path"])] = str(item.get("sha256") or "")
    srcs = ((cfg.get("resolved_source_contract") or {}).get("sources") or {})
    for s in srcs.values():
        art = (s or {}).get("artifact") or {}
        if art.get("path"):
            out.setdefault(str(art["path"]), str(art.get("sha256") or ""))
    return out


def _run(cmd: list[str], log: Path, env: dict) -> tuple[int, float]:
    t0 = time.time()
    with open(log, "a", encoding="utf-8") as fh:
        fh.write(f"\n$ {' '.join(cmd)}\n")
        fh.flush()
        rc = subprocess.run(cmd, cwd=ROOT, stdout=fh, stderr=subprocess.STDOUT, env=env).returncode
    return rc, round(time.time() - t0, 1)


# Ruta de producción (official_live): el seccionado llega del OGC del INE como en la 00; solo la tabla 65034 se sirve
# desde la copia nacional (su descarga en vivo, de 1,6 GB, no termina en 15 min desde la sesión cloud).
ADQUISICION_OGC = (
    "import runpy,sys;from pathlib import Path;sys.path.insert(0,str(Path.cwd()))\n"
    "import herramientas.adquirir_fuentes_oficiales as a\n"
    "orig=a.live_fetch;local=Path('inputs/_nacional/65034_totales.csv.zip').read_bytes()\n"
    "a.live_fetch=lambda url,*x,**k: local if '65034' in url else orig(url,*x,**k)\n"
    "sys.argv=['ejecutar_fuentes_workflow']+sys.argv[1:]\n"
    "runpy.run_module('herramientas.ejecutar_fuentes_workflow',run_name='__main__')\n"
)


LOG_COLA = 60


def _volcar_log(t: str, log: Path, res: dict) -> None:
    """Fallo: copia a la salida del paso la cola de log.txt y una línea ::error (T-233)."""
    try:
        lineas = log.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        lineas = []
    cola = lineas[-LOG_COLA:]
    errores = [x.strip() for x in cola if x.strip() and ("Error" in x or "Exception" in x or x.startswith("FALLO"))]
    no_vacias = [x.strip() for x in cola if x.strip()]
    motivo = (errores or no_vacias or ["sin log"])[-1].replace("::", ": ")
    print(f"--- {t}: últimas {len(cola)} líneas de {log.name} ---", flush=True)
    for x in cola:
        print(x, flush=True)
    print(f"--- fin de {log.name} ---", flush=True)
    print(f"::error title=entradas {t}::{res.get('estado')} rc={res.get('rc')}: {motivo}", flush=True)


def entradas_uno(t: str, out: Path, nac: dict, seccionado: str = "shapefile", paquete: Path | None = None) -> dict:
    """Entradas M01-M03 de un territorio. Con ``paquete`` (carpeta del paquete P10 de la fuente, ya validado) hace lo mismo que la
    00: restaura el paquete como checkpoint de fuentes (REUSE, sin adquisición) y ejecuta M01, M02 y M03 con el código vigente."""
    dest = out / "entradas" / t
    shutil.rmtree(dest, ignore_errors=True)
    dest.mkdir(parents=True)
    log = dest / "log.txt"
    env = dict(os.environ, DDD_RUN_ID=f"bateria-{t}", PYTHONHASHSEED="0")
    res: dict = {"territorio": t, "tiempos": {}}
    decl = _declaracion_temporal(t, nac, "ogc" if paquete is not None else seccionado)
    res["seccionado"] = "paquete_p10" if paquete is not None else seccionado
    completada = "_bateria_declaracion_completada_desde_contrato" in decl.read_text(encoding="utf-8")
    work = out / "_trabajo" / t
    shutil.rmtree(work, ignore_errors=True)
    try:
        if paquete is not None:
            from herramientas.politica_reutilizacion_fuentes import resolve_source_action
            dec = resolve_source_action(prepared_manifest=json.loads((paquete / "manifest.json").read_text(encoding="utf-8")),
                                        root=paquete, requested_edition=_anios_fuentes(t)[0], official_available=False)
            if dec["decision"] != "REUSE":  # sin fuente oficial disponible solo hay REUSE o BLOCK: nunca se llega a adquirir
                with open(log, "a", encoding="utf-8") as fh:
                    fh.write(f"BATERIA_PAQUETE_P10_NO_REUTILIZABLE: {dec['decision']}: {dec['reason']}\n")
                res.update(estado="FALLO_ADQUISICION", rc=96)
                _volcar_log(t, log, res)
                return res
            ckpt_in = work / "ckpt_in"
            shutil.copytree(paquete, ckpt_in / "sources")
            rc, s = _run([sys.executable, "-m", "herramientas.ejecutar_fuentes_workflow", "--declaration", str(decl),
                          "--working", str(work / "pkg"), "--checkpoint-in", str(ckpt_in), "--checkpoint-out", str(work / "ckpt"),
                          "--acquisition-evidence", str(work / "ev"), "--environment", "production",
                          "--acquisition-mode", "verified_snapshot", "--root-dir", str(ROOT)], log, env)
            if rc == 0 and '"decision": "REUSE"' not in log.read_text(encoding="utf-8", errors="replace"):
                rc = 97  # la 00 reutiliza el paquete; si hubiera adquirido, la batería no mide lo mismo (y habría ido a la red)
                with open(log, "a", encoding="utf-8") as fh:
                    fh.write("BATERIA_PAQUETE_P10_NO_REUTILIZADO: la política de fuentes no reutilizó el paquete\n")
        else:
            modo = ["official_live"] if seccionado == "ogc" else ["verified_snapshot"]
            rc, s = _run([sys.executable, "-c", ADQUISICION_OGC, "--declaration", str(decl),
                          "--working", str(work / "pkg"), "--checkpoint-out", str(work / "ckpt"),
                          "--acquisition-evidence", str(work / "ev"), "--environment", "production",
                          "--acquisition-mode", *modo, "--root-dir", str(ROOT)], log, env)
    finally:
        decl.unlink(missing_ok=True)
    res["tiempos"]["adquisicion"] = s
    res["declaracion_completada_desde_contrato"] = completada
    mat = work / "ev" / "materialized" / "inputs"
    if rc != 0 or not mat.is_dir():
        res.update(estado="FALLO_ADQUISICION", rc=rc)
        _volcar_log(t, log, res)
        return res
    contrato_sha = _huellas_contrato(_cfg(t))
    res["fuentes"] = {}
    for f in sorted(mat.iterdir()):
        shutil.copy2(f, ROOT / "inputs" / f.name)
        shutil.copy2(f, dest / f.name)
        h = sha256(f)
        esperado = contrato_sha.get(f"inputs/{f.name}", "")
        res["fuentes"][f.name] = {"sha256": h, "contrato_sha256": esperado, "igual_contrato": h == esperado}
    cache = _cache(t)
    shutil.rmtree(cache, ignore_errors=True)
    for n, script in ((1, "01_preparar_base_territorial"), (2, "02_construir_adyacencias"), (3, "03_construir_grafo")):
        rc, s = _run([sys.executable, f"modulos/{script}.py", "--params", str(contrato(t).relative_to(ROOT))], log, env)
        res["tiempos"][f"M0{n}"] = s
        if rc != 0:
            res.update(estado=f"FALLO_M0{n}", rc=rc)
            _volcar_log(t, log, res)
            return res
    res["estado"] = "OK"
    res["origen"] = "paquete_p10" if paquete is not None else "fuente"
    res["salidas"] = {}
    for f in sorted(cache.iterdir()):
        if f.is_file() and any(f"_m0{n}_" in f.name for n in (1, 2, 3)):
            res["salidas"][f.name] = sha256(f)
    _guardar_minima(t, cache, dest, res)
    return res


def _identidad_contrato(t: str) -> dict:
    cfg = _cfg(t)
    gs = cfg.get("generation_state") or {}
    return {"contrato": str(contrato(t).relative_to(ROOT)), "contrato_sha256": sha256(contrato(t)),
            "package_sha256": gs.get("package_sha256"), "compatibility_identity_sha256": gs.get("compatibility_identity_sha256")}


def _guardar_minima(t: str, cache: Path, dest: Path, res: dict) -> None:
    """Deja en ``dest`` solo la entrada mínima y ENTRADAS.json (sha256 de todo, identidad del contrato)."""
    for f in dest.iterdir():
        if f.is_file() and f.name not in ("log.txt",):
            f.unlink()
    res["entrada_minima"] = {}
    for suf in ENTRADA_MINIMA:
        f = next(cache.glob(f"*{suf}"), None)
        if f is None:
            res["estado"] = f"FALTA_ENTRADA_MINIMA{suf}"
            continue
        shutil.copy2(f, dest / f.name)
        res["entrada_minima"][f.name] = sha256(f)
    res["identidad_contrato"] = _identidad_contrato(t)
    (dest / "ENTRADAS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _r2_cp(origen: str, destino: str) -> None:
    ep = f"https://{os.environ['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com"
    subprocess.run(["aws", "s3", "cp", origen, destino, "--endpoint-url", ep, "--only-show-errors"], check=True)


def clave_paquete(ident: dict) -> str:
    """Clave en R2 (ARC-E) del paquete P10 de la fuente: por el sha256 del paquete del contrato (sin id de territorio)."""
    return f"arc-e/paquetes-p10/{ident['package_sha256']}.zip"


def _anios_fuentes(t: str) -> tuple[str, str, str]:
    d = yaml.safe_load((ROOT / "territorios" / carpeta_de(ROOT, t) / "config" / "fuentes_oficiales.yaml").read_text(encoding="utf-8"))
    terr = d.get("territory") or {}
    meta = _cfg(t).get("meta") or {}
    ed = terr.get("edition")
    return (str(ed), str(terr.get("population_year") or meta.get("source_population_year") or ed),
            str(terr.get("section_year") or meta.get("source_section_year") or ed))


def validar_paquete_p10(t: str, carpeta: Path) -> None:
    """El paquete de la fuente es el del contrato (sha256 del bundle = package_sha256) y lo acepta la validación de la 00."""
    from herramientas.seleccionar_paquete_fuentes import validate_prepared_package
    esperado = _identidad_contrato(t)["package_sha256"]
    if not esperado:
        raise PaqueteP10Corrupto("el contrato no declara package_sha256")
    man = carpeta / "manifest.json"
    if not man.is_file():
        raise PaqueteP10Corrupto("sin manifest.json")
    manifiesto = json.loads(man.read_text(encoding="utf-8"))
    bundle = carpeta / str(manifiesto.get("path") or "")
    if not bundle.is_file() or sha256(bundle) != esperado or str(manifiesto.get("sha256")).lower() != esperado:
        raise PaqueteP10Corrupto("el paquete no es el del contrato (sha256 del bundle distinto de package_sha256)")
    ed, pob, sec = _anios_fuentes(t)
    ok, motivos = validate_prepared_package(carpeta, territory_id=t, edition=ed, population_year=pob, section_year=sec)
    if not ok:
        raise PaqueteP10Corrupto("paquete rechazado por la validación de la 00: " + "; ".join(motivos))


def paquete_p10_desde_r2(t: str, out: Path) -> Path | None:
    """Baja de R2 y extrae el paquete P10 de ``t`` (clave por package_sha256) y lo valida. None si no está; PaqueteP10Corrupto si no vale."""
    ident = _identidad_contrato(t)
    bucket = os.environ.get("R2_BUCKET", "")
    if not bucket or not ident["package_sha256"]:
        return None
    work = out / "_trabajo" / f"{t}-p10"
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    z = work / "paquete.zip"
    try:
        _r2_cp(f"s3://{bucket}/{clave_paquete(ident)}", str(z))
    except (subprocess.CalledProcessError, KeyError, OSError):
        shutil.rmtree(work, ignore_errors=True)
        return None
    carpeta = work / "pkg"
    with zipfile.ZipFile(z) as zf:
        raiz = carpeta.resolve()
        for m in zf.infolist():
            if raiz not in (carpeta / m.filename).resolve().parents and (carpeta / m.filename).resolve() != raiz:
                raise PaqueteP10Corrupto(f"ruta insegura en el paquete: {m.filename}")
        zf.extractall(carpeta)
    validar_paquete_p10(t, carpeta)
    return carpeta


def entradas(args) -> int:
    """T-303: la batería usa la MISMA fuente que producción y recalcula con el código vigente. Toma el paquete P10 de la fuente del
    territorio (R2, ARC-E, por package_sha256 del contrato, verificado) y ejecuta como la 00 la restauración de fuentes y M01, M02 y M03
    con el contrato. No hay M03 archivado que usar: un cambio de M02/M03 cambia lo calculado. Nunca va al INE. Sin paquete:
    BATERIA_FALTA_PAQUETE_P10; paquete que no es el del contrato o alterado: BATERIA_PAQUETE_P10_CORRUPTO.
    ``--desde-fuente`` (solo diagnóstico local) reconstruye desde las fuentes nacionales verificadas."""
    nac = None
    out = Path(args.out)
    fallos = 0
    for t in (territorios() if args.todos else args.territorios):
        paquete = None
        if not args.desde_fuente:
            try:
                paquete = paquete_p10_desde_r2(t, out)
            except PaqueteP10Corrupto as exc:
                print(f"::error::BATERIA_PAQUETE_P10_CORRUPTO {t}: {exc}. Vuelve a archivarlo (archivar_p10=<run de P10 de {t}>).", flush=True)
                fallos += 1
                continue
            if paquete is None:
                print(f"::error::BATERIA_FALTA_PAQUETE_P10 {t}: no hay paquete de fuentes en R2 ({clave_paquete(_identidad_contrato(t))}). "
                      f"Archívalo una vez con «P70 Archivo · P71 archivar · paquete de fuentes de un territorio» ({t}).", flush=True)
                fallos += 1
                continue
        else:
            if args.seccionado == "ogc" and not args.permitir_red_ine:
                print("::error::BATERIA_RED_INE_PROHIBIDA: --seccionado ogc exige --permitir-red-ine (OGC e INE solo existen dentro de P10)")
                return 2
            if nac is None:
                for nombre in ["65034.csv.zip", *(f"seccionado_{ed}.zip" for ed in EDICIONES)]:
                    obtener_fuente_nacional(nombre, NACIONAL)
                nacionales(args)
                nac = json.loads((NACIONAL / "NACIONALES.json").read_text(encoding="utf-8"))["ficheros"]
        r = entradas_uno(t, out, nac or {}, args.seccionado, paquete=paquete)
        iguales = {k: v["igual_contrato"] for k, v in (r.get("fuentes") or {}).items()}
        print(f"{t}: {r['estado']} {r['tiempos']} huella=contrato {iguales}", flush=True)
        fallos += r["estado"] != "OK"
    return 1 if fallos else 0


def archivar_p10(args) -> int:
    """Archiva en R2 (ARC-E) el paquete P10 de la fuente de ``territorio`` (carpeta ``--paquete`` = artefacto ddd-source-package-* ya
    descomprimido): comprueba que es el del contrato y lo sube en ``arc-e/paquetes-p10/<package_sha256>.zip`` con su sha256."""
    from herramientas.archivar_artefactos_r2 import r2_cliente
    t, carpeta = args.territorio, Path(args.paquete)
    bucket, cuenta = os.environ.get("R2_BUCKET", ""), os.environ.get("R2_ACCOUNT_ID", "")
    if not bucket or not cuenta:
        print("::error::BATERIA_R2_SIN_CREDENCIALES (R2_BUCKET/R2_ACCOUNT_ID)")
        return 2
    try:
        validar_paquete_p10(t, carpeta)
    except PaqueteP10Corrupto as exc:
        print(f"::error::BATERIA_PAQUETE_P10_OTRO_CONTRATO {t}: {exc}")
        return 1
    ident = _identidad_contrato(t)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    z = out / f"{t}-paquete-p10.zip"
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:  # determinista: orden y fecha fijos
        for f in sorted(p for p in carpeta.rglob("*") if p.is_file()):
            info = zipfile.ZipInfo(f.relative_to(carpeta).as_posix(), FECHA_ZIP)
            info.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(info, f.read_bytes())
    h = sha256(z)
    clave = clave_paquete(ident)
    sha_remoto, subir = r2_cliente(bucket, cuenta)
    if sha_remoto(clave) != h:
        subir(clave, z, h)
    registro = {t: {"url": f"r2://{bucket}/{clave}", "clave": clave, "sha256_zip": h, "bytes": z.stat().st_size,
                    "package_sha256": ident["package_sha256"], "origen_run": args.run,
                    "archivado_en": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}}
    (out / "ARCHIVO_PAQUETES_P10.json").write_text(json.dumps(registro, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(registro[t]))
    return 0


# --------------------------------------------------------------------------- motor
M05_PARCHE = (
    "import importlib.util,sys;from pathlib import Path\n"
    "spec=importlib.util.spec_from_file_location('m05',Path('modulos/05_optimizar_distritos.py'))\n"
    "m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)\n"
    "m.BASE_ENGINE=Path(sys.argv[1]);sys.argv=['05_optimizar_distritos.py']+sys.argv[2:];m.main()\n"
)


def _reglas(val: dict) -> dict:
    f = [str(x) for x in val.get("failures") or []]
    r = {
        "K": not any(x.startswith(("distritos=", "geometrías distritales")) for x in f),
        "atomicidad": not any(("nulo" in x or "duplicados" in x or "no conservada" in x) for x in f),
        "poblacion": not val.get("below_floor") and not val.get("above_cap"),
        "contiguidad": not val.get("graph_disconnected"),
        "provincia": not val.get("province_crossings") and not any(x.startswith(("provincia ", "falta campo provincial")) for x in f),
        "municipal": not val.get("municipality_violations") and not any("disciplina municipal" in x for x in f),
    }
    conocidas = ("distritos=", "geometrías", "nulo", "duplicados", "no conservada", "bajo límite", "sobre límite",
                 "desconectados", "interprovinciales", "provincia ", "falta campo", "municipios con fragmentación")
    r["otras"] = not any(not any(k in x for k in conocidas) for x in f)
    return r


def composicion_publicada(t: str) -> tuple[Path | None, str | None]:
    """Composición del M06 vigente en el visor: la misma que compite (ddd_motor2.vigente.vigente_publicado, T-258).
    (None, run) si el run publicado no tiene composición versionada: nunca otro mapa en su lugar."""
    from ddd_motor2.vigente import vigente_publicado
    v = vigente_publicado(t, ROOT)
    return v.ruta, v.run


def _comparar_publicado(t: str, comp: Path) -> dict:
    pub, run = composicion_publicada(t)
    if pub is None or not comp.is_file():
        return {"publicado": pub is not None, "igual": None}
    import pandas as pd
    a = pd.read_csv(pub, dtype=str)
    b = pd.read_csv(comp, dtype=str)
    sid = "CUSEC_KEY" if "CUSEC_KEY" in b.columns else b.columns[0]
    pa = {frozenset(g["seccion"]) for _, g in a.groupby("distrito")}
    pb = {frozenset(g[sid]) for _, g in b.groupby("district_id")}
    sa, sb = set(a["seccion"]), set(b[sid])
    return {"publicado": True, "run_publicado": run, "fichero": str(pub.relative_to(ROOT)), "igual": pa == pb,
            "distritos_iguales": len(pa & pb), "distritos_publicados": len(pa),
            "secciones_solo_publicado": len(sa - sb), "secciones_solo_bateria": len(sb - sa)}


def restaurar(t: str, out: Path) -> Path | None:
    """Copia las entradas archivadas de ``t`` a su caché y a inputs/; devuelve la caché o None si faltan."""
    src = out / "entradas" / t
    if not (src / "ENTRADAS.json").is_file():
        return None
    cache = _cache(t)
    shutil.rmtree(cache, ignore_errors=True)
    cache.mkdir(parents=True)
    for f in src.iterdir():
        if "_m0" in f.name:
            shutil.copy2(f, cache / f.name)
        elif f.suffix == ".zip":
            shutil.copy2(f, ROOT / "inputs" / f.name)
    return cache


def pasos_m04(p: str, run_id: str, dest: Path) -> list:
    return [("unidades", [sys.executable, "herramientas/preparar_unidades_internas.py", "--params", p, "--run-id", run_id,
                          "--job-report", str(dest / "preparacion_unidades_internas.json")]),
            ("M04", [sys.executable, "modulos/04_generar_semillas.py", "--params", p])]


def metricas(t: str, comp: Path | None, val: dict) -> dict:
    """Desvío máximo, distritos fuera de la tolerancia del contrato y municipios partidos (de la composición M06)."""
    if comp is None or not comp.is_file() or not val.get("target_population"):
        return {}
    import pandas as pd
    c = pd.read_csv(comp, dtype={"CUMUN": str})
    pop = next(x for x in ("section_pop", "poblacion") if x in c.columns)
    tol = float(((_cfg(t).get("validation") or {}).get("target_tolerance_ratio")) or 0.12)
    dev = (c.groupby("district_id")[pop].sum() / float(val["target_population"]) - 1).abs()
    partidos = int((c.groupby("CUMUN")["district_id"].nunique() > 1).sum()) if "CUMUN" in c.columns else None
    return {"desvio_max": round(float(dev.max()), 4), "fuera_tolerancia": int((dev > tol + 1e-9).sum()),
            "tolerancia": tol, "municipios_partidos": partidos}


def _composicion_m06(t: str, run_id: str, cache: Path) -> Path | None:
    """Composición M06 en la ruta que fija el contrato (con el run_id de la ejecución), o en la caché."""
    viejo = os.environ.get("DDD_RUN_ID")
    os.environ["DDD_RUN_ID"] = run_id
    try:
        from ddd_core.config import load_params_yaml, module_cfg
        s6 = module_cfg(load_params_yaml(str(contrato(t))), "modulo_06_consolidar_distritos", "step6_export_final")
        f = Path(s6.get("out_composition_csv") or "")
        if f.is_file():
            return f
    finally:
        if viejo is None:
            os.environ.pop("DDD_RUN_ID", None)
        else:
            os.environ["DDD_RUN_ID"] = viejo
    return next(cache.glob("*_m06_composicion_distritos.csv"), None)


def validar_y_resumir(t: str, p: str, run_id: str, dest: Path, res: dict, cache: Path, log: Path, env: dict) -> dict:
    """M06 ya ejecutado: validación de producción, reglas, métricas y comparación con lo publicado."""
    rc, s = _run([sys.executable, "herramientas/validar_ejecucion.py", "--params", p, "--run-id", run_id], log, env)
    res["tiempos"]["validacion"] = s
    comp = _composicion_m06(t, run_id, cache)
    if comp:  # antes de borrar ejecuciones/<run>: algunos contratos (Aragón) dejan ahí la composición
        shutil.copy2(comp, dest / comp.name)
        res["composicion_sha256"] = sha256(comp)
        comp = dest / comp.name
    vpath = ROOT / "ejecuciones" / run_id / "VALIDACION.json"
    val = json.loads(vpath.read_text(encoding="utf-8")) if vpath.is_file() else {"estado": "FAIL", "failures": ["sin VALIDACION"]}
    shutil.rmtree(ROOT / "ejecuciones" / run_id, ignore_errors=True)
    (dest / "VALIDACION.json").write_text(json.dumps(val, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    res["validacion"] = val.get("estado")
    res["fallos"] = val.get("failures") or []
    res["reglas"] = _reglas(val) if val.get("estado") in ("PASS", "FAIL") and "districts_found" in val else {r: False for r in REGLAS}
    res["K"] = val.get("districts_found")
    res["K_esperado"] = val.get("expected_districts")
    for informe, clave in (("_m04_informe.json", "m04"), ("_m05_informe.json", "m05_informe")):
        f = next(cache.glob(f"*{informe}"), None)
        if f:
            d = json.loads(f.read_text(encoding="utf-8"))
            res[clave] = {k: d.get(k) for k in ("version", "engine_version", "seed", "population_baseline_status")}
    res["metricas"] = metricas(t, comp, val)
    res["publicado"] = _comparar_publicado(t, comp) if comp else {"igual": None}
    (dest / "RESULTADO.json").write_text(json.dumps(res, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return res


def motor_uno(t: str, out: Path, version: str) -> dict:
    res: dict = {"territorio": t, "m05": version, "tiempos": {}}
    cache = restaurar(t, out)
    if cache is None:
        res["estado"] = "SIN_ENTRADAS"
        return res
    dest = out / "motor" / version / t
    shutil.rmtree(dest, ignore_errors=True)
    dest.mkdir(parents=True)
    log = dest / "log.txt"
    run_id = f"bateria-{t}-{version}"
    env = dict(os.environ, DDD_RUN_ID=run_id, PYTHONHASHSEED="0", DDD_OPTIMIZATION_ALGORITHM="Canónico")
    p = str(contrato(t).relative_to(ROOT))
    pasos = pasos_m04(p, run_id, dest) + [
             ("M05", [sys.executable, "modulos/05_optimizar_distritos.py", "--params", p] if version == "7.4.4"
              else [sys.executable, "-c", M05_PARCHE, str(M05_BASE[version]), "--params", p]),
             ("M06", [sys.executable, "modulos/06_consolidar_distritos.py", "--params", p])]
    res["estado"] = "OK"
    for nombre, cmd in pasos:
        rc, s = _run(cmd, log, env)
        res["tiempos"][nombre] = s
        if rc != 0:
            res.update(estado=f"FALLO_{nombre}", rc=rc)
            break
    return validar_y_resumir(t, p, run_id, dest, res, cache, log, env)


def motor(args) -> int:
    out = Path(args.out)
    fallos = 0
    for t in (territorios() if args.todos else args.territorios):
        r = motor_uno(t, out, args.m05)
        malas = [k for k, v in (r.get("reglas") or {}).items() if not v]
        print(f"{t} [{args.m05}]: {r['estado']} validación={r.get('validacion')} FAIL={malas} "
              f"publicado={r.get('publicado', {}).get('igual')} t={sum(r['tiempos'].values()):.1f}s", flush=True)
        fallos += r.get("validacion") != "PASS"
    return 1 if fallos else 0


# --------------------------------------------------------------------------- matriz
def matriz(args) -> int:
    out = Path(args.out)
    filas = []
    versiones = sorted(p.name for p in (out / "motor").iterdir()) if (out / "motor").is_dir() else []
    por_t: dict = {}
    for v in versiones:
        for f in sorted((out / "motor" / v).glob("*/RESULTADO.json")):
            r = json.loads(f.read_text(encoding="utf-8"))
            comp = next(f.parent.glob("*_m06_composicion_distritos.csv"), None)
            if comp is not None:  # siempre contra el M06 vigente del visor, aunque el resultado sea anterior
                r["publicado"] = _comparar_publicado(r["territorio"], comp)
                if not r.get("metricas"):
                    vf = f.parent / "VALIDACION.json"
                    r["metricas"] = metricas(r["territorio"], comp, json.loads(vf.read_text(encoding="utf-8")) if vf.is_file() else {})
            por_t.setdefault(r["territorio"], {})[v] = r
    for t in sorted(por_t):
        for v, r in sorted(por_t[t].items()):
            reglas = r.get("reglas") or {}
            otras = {w: x.get("composicion_sha256") == r.get("composicion_sha256") for w, x in por_t[t].items() if w != v}
            filas.append({
                "territorio": t, "m05": v, "estado": r.get("estado"), "validacion": r.get("validacion"),
                **{f"regla_{k}": "PASS" if reglas.get(k) else "FAIL" for k in REGLAS},
                "K": r.get("K"), "K_esperado": r.get("K_esperado"),
                "semilla": (r.get("m05_informe") or {}).get("seed"),
                "tiempo_s": round(sum((r.get("tiempos") or {}).values()), 1),
                "igual_publicado": (r.get("publicado") or {}).get("igual"),
                "run_publicado": (r.get("publicado") or {}).get("run_publicado"),
                "desvio_max": (r.get("metricas") or {}).get("desvio_max"),
                "fuera_tolerancia": (r.get("metricas") or {}).get("fuera_tolerancia"),
                "municipios_partidos": (r.get("metricas") or {}).get("municipios_partidos"),
                "distritos_iguales_publicado": (r.get("publicado") or {}).get("distritos_iguales"),
                "igual_otras_versiones": json.dumps(otras, sort_keys=True),
                "fallos": " | ".join(r.get("fallos") or []),
            })
    if not filas:
        print("sin resultados")
        return 1
    with open(out / "MATRIZ.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(filas[0]))
        w.writeheader()
        w.writerows(filas)
    lineas = ["| territorio | M05 | " + " | ".join(REGLAS) + " | K | s | = publicado |", "|" + "---|" * (len(REGLAS) + 5)]
    for f in filas:
        lineas.append(f"| {f['territorio']} | {f['m05']} | " + " | ".join("✓" if f[f'regla_{k}'] == "PASS" else "✗" for k in REGLAS)
                      + f" | {f['K']}/{f['K_esperado']} | {f['tiempo_s']} | {f['igual_publicado']} |")
    for v in versiones:
        sub = [f for f in filas if f["m05"] == v]
        lineas.append(f"\n{v}: PASS {sum(f['validacion'] == 'PASS' for f in sub)}/{len(sub)}; "
                      f"igual al publicado {sum(f['igual_publicado'] is True for f in sub)}/{sum(f['igual_publicado'] is not None for f in sub)}")
    (out / "MATRIZ.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print(lineas[-len(versiones):] if versiones else "")
    return 0


# --------------------------------------------------------------------------- motor 2 en Actions (T-208)
HUELLA_REAL = ("nac42", "nac01", "aut19")  # criterio a de T-194 (nombres de territorio de la batería)


def lista(args) -> int:
    todos = territorios()
    pedidos = args.territorios or todos
    desconocidos = [t for t in pedidos if t not in todos]
    if desconocidos:
        print(f"::error::BATERIA_TERRITORIO_DESCONOCIDO {' '.join(desconocidos)}")
        return 2
    print(json.dumps({"include": [{"t": t} for t in pedidos]}))
    return 0


def huella(args) -> int:
    from ddd_motor2.competir import competir_territorio
    out = Path(args.out)
    t = args.territorio
    primera = json.loads((out / "competicion" / t / "RESUMEN.json").read_text(encoding="utf-8"))["territorios"][0]
    sombra = out / "_huella2"
    sombra.mkdir(parents=True, exist_ok=True)
    if not (sombra / "entradas").exists():
        (sombra / "entradas").symlink_to((out / "entradas").resolve(), target_is_directory=True)
    segunda = competir_territorio(t, sombra, args.cadenas, funcion=args.funcion)
    h1, h2 = primera.get("huella_resultado"), segunda.get("huella_resultado")
    res = {"territorio": t, "huella_1": h1, "huella_2": h2, "igual": bool(h1) and h1 == h2,
           "funcion": args.funcion, "cadenas": args.cadenas, "estado_2": segunda.get("estado")}
    (out / "competicion" / t / "HUELLA_REAL.json").write_text(json.dumps(res, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(res))
    return 0 if res["igual"] else 1


# --------------------------------------------------------------------------- indicadores frente al vigente (T-212)
def peor_que(g: dict, ref: dict) -> list[str]:
    """Causas por las que el plan `g` es peor que `ref` en el recuento BRUTO de distritos fuera de tolerancia (la del contrato).
    Es la vara que bloquea frente al vigente (Planificador, T-212); el desvío máximo va aparte (`aviso_desvio`) y no bloquea."""
    if g["fuera_tolerancia"] > ref["fuera_tolerancia"]:
        return [f"más distritos fuera de tolerancia ({g['fuera_tolerancia']} > {ref['fuera_tolerancia']})"]
    return []


def aviso_desvio(g: dict, ref: dict) -> list[str]:
    """Desvío máximo mayor que el de `ref` (informa; D8 puede cambiarlo por naturalidad dentro de la tolerancia)."""
    if g["desvio_max"] > ref["desvio_max"]:
        return [f"mayor desvío máximo ({g['desvio_max'] * 100:.2f} % > {ref['desvio_max'] * 100:.2f} %)"]
    return []


def _composicion_de(carpeta: Path) -> Path | None:
    return next(iter(sorted(carpeta.glob("*_m06_composicion_distritos.csv"))), None) if carpeta.is_dir() else None


def _forma(comp: Path, plan: dict, col: dict, grafo_dir: Path) -> dict:
    """Polsby-Popper medio y mínimo de los distritos (geometrías de la M01 de las entradas, EPSG:3035). Solo informa: si no
    se puede calcular, devuelve el motivo."""
    import tempfile
    from ddd_motor2 import naturalidad as nat, naturalidad_mapas as nm
    from ddd_motor2.adaptadores import leer_composicion
    try:
        import geopandas as gpd
        zips = sorted(grafo_dir.glob("*_m01_secciones_poblacion.geojson.zip"))
        if not zips:
            return {"pp_error": "sin M01 (geometrías) en las entradas"}
        with tempfile.TemporaryDirectory() as td, zipfile.ZipFile(zips[0]) as z:
            n = next(x for x in z.namelist() if x.endswith((".geojson", ".json")))
            z.extract(n, td)
            g = gpd.read_file(Path(td) / n)
        clave = next((c for c in (col["seccion"], "CUSEC_KEY", "CUSEC") if c in g.columns), None)
        if clave is None or g.crs is None:
            return {"pp_error": "la M01 no trae identificador de sección o CRS"}
        sec_u = {str(f[col["seccion"]]).strip(): str(f.get(col["unidad"]) or f[col["seccion"]]).strip()
                 for f in leer_composicion(comp, col)}
        g = g.assign(_d=[plan.get(sec_u.get(str(s).strip())) for s in g[clave]]).dropna(subset=["_d"]).to_crs(nm.CRS)
        f = nat.forma({str(d): geo for d, geo in g.dissolve(by="_d").geometry.items()})
        v = [x["polsby_popper"] for x in f.values() if x["polsby_popper"] is not None]
        return {"pp_medio": sum(v) / len(v), "pp_min": min(v)} if v else {"pp_error": "sin geometrías"}
    except Exception as exc:  # solo informa
        return {"pp_error": f"{type(exc).__name__}: {exc}"}


def recuento_contrato(nat, plan: dict) -> dict:
    """Fuera de tolerancia y desvío máximo como el contrato, el núcleo y el M04 (objetivo regional): el mismo recuento que
    el primer término de la clave D8 de la competición (Natural.fuera_regional, T-211). Por circunscripción solo informa."""
    from fractions import Fraction
    tol = nat.tol / nat.objetivo
    circ = [abs(Fraction(p) - o) / o for p, o in nat.desvios(plan).values()]
    reg = [abs(Fraction(p) - nat.objetivo) / nat.objetivo for p, _ in nat.desvios(plan).values()]
    return {"distritos": len(reg), "fuera_tolerancia": nat.fuera_regional(plan), "desvio_max": float(max(reg)),
            "fuera_tolerancia_circunscripcion": sum(1 for x in circ if x > tol), "desvio_max_circunscripcion": float(max(circ))}


def _indicadores_plan(comp: Path, cfg: dict, grafo: Path, referencia: Path | None, atributos: Path | None) -> dict:
    from ddd_motor2.adaptadores import columnas_de_contrato, problema_y_plan
    from ddd_motor2.naturalidad_clave import corte_km, natural_desde_m06, partidas
    from ddd_motor2.reglas import Criterio, Reglas, evaluar
    crit = Criterio()
    reglas = Reglas.desde_contrato(cfg, crit)
    problema, plan, _ = problema_y_plan(comp, grafo, cfg, referencia_nucleos=referencia, atributos_secciones=atributos,
                                        respaldo_municipio_cusec=crit.respaldo_municipio_cusec)
    nat = natural_desde_m06(problema, reglas, comp, grafo, cfg)
    r = {**recuento_contrato(nat, plan),
         "partidos_judiciales_partidos": partidas(plan, (nat.pj,)), "comarcas_partidas": partidas(plan, (nat.ca,)),
         "frontera_cortada_km": corte_km(plan, nat.largo), "valido_reglas_actuales": evaluar(problema, reglas, plan).valido}
    r.update(_forma(comp, plan, columnas_de_contrato(cfg), grafo.parent))
    return r


def _vigente_sobre(canonico: Path, vigente: Path, destino: Path, col: dict) -> Path:
    """Composición del canónico (con unidades, municipio y provincia) con el distrito de cada sección tomado del vigente."""
    with open(vigente, encoding="utf-8", newline="") as fh:
        v = {str(r["seccion"]).strip(): r["distrito"] for r in csv.DictReader(fh)}
    with open(canonico, encoding="utf-8", newline="") as fh:
        rd = csv.DictReader(fh)
        filas = list(rd)
        campos = rd.fieldnames
    sec = {str(f[col["seccion"]]).strip() for f in filas}
    if sec != set(v):
        raise ValueError(f"secciones distintas: {len(sec - set(v))} solo en el canónico, {len(set(v) - sec)} solo en el vigente")
    for f in filas:
        f[col["distrito"]] = v[str(f[col["seccion"]]).strip()]
    destino.mkdir(parents=True, exist_ok=True)
    out = destino / "vigente_m06_composicion_distritos.csv"
    with open(out, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=campos)
        w.writeheader()
        w.writerows(filas)
    return out


def _vigente_de_la_competicion(carpeta: Path, d: dict, can: Path, pub: Path, col: dict) -> Path | None:
    """T-229: composición que escribió el generador `vigente` (piezas finas; la publicada, no la reparada) si el bloque
    «vigente» del COMPETICION.json viene del mismo fichero publicado (sha256) y reproduce su distrito en cada sección."""
    import hashlib
    bloque = d.get("vigente") or {}
    f = carpeta / "vigente" / can.name
    if not f.is_file() or bloque.get("sha256_origen") != hashlib.sha256(pub.read_bytes()).hexdigest():
        return None
    with open(pub, encoding="utf-8", newline="") as fh:
        v = {str(r["seccion"]).strip(): str(r["distrito"]).strip() for r in csv.DictReader(fh)}
    with open(f, encoding="utf-8", newline="") as fh:
        m = {str(r[col["seccion"]]).strip(): str(r[col["distrito"]]).strip() for r in csv.DictReader(fh)}
    return f if m == v else None


def indicadores_territorio(t: str, out: Path, *, cfg: dict | None = None, grafo: Path | None = None,
                           vigente: tuple[Path | None, str | None] | None = None) -> dict:
    """Indicadores del vigente, el canónico y el ganador de `t` (lee <out>/competicion/<t>/COMPETICION.json). Estado:
    OK | PEOR | UN_DISTRITO (el único plan posible; sin vigente se anota) | SIN_VIGENTE | NO_EVALUABLE (con motivo).
    Escribe INDICADORES.json y .md junto al COMPETICION.json. `cfg`, `grafo` y `vigente` se pueden inyectar (pruebas)."""
    from ddd_motor2.adaptadores import columnas_de_contrato
    out = Path(out)
    carpeta = out / "competicion" / t
    res: dict = {"territorio": t, "estado": "NO_EVALUABLE", "motivo": ""}
    try:
        cfg = cfg if cfg is not None else _cfg(t)
        grafo = grafo or next((out / "entradas" / t).glob("*_m03_grafo.json"))
        if vigente is not None:
            (pub, run), motivo_sin = vigente, "sin composición vigente publicada (datos/composicion)"
        else:
            from ddd_motor2.vigente import vigente_publicado
            v = vigente_publicado(t, ROOT)
            pub, run, motivo_sin = v.ruta, v.run, f"sin composición vigente publicada: {v.motivo}"
        res.update(run_vigente=run, fichero_vigente=str(pub.relative_to(ROOT)) if pub and pub.is_relative_to(ROOT) else (str(pub) if pub else None))
        d = json.loads((carpeta / "COMPETICION.json").read_text(encoding="utf-8"))
        cands = {c["id"]: c for c in d["candidatos"]}

        def donde(cid: str) -> tuple[Path, Path | None]:
            c = cands[cid]
            p = Path(c.get("composicion") or "")
            if not p.is_file():
                p = _composicion_de(carpeta / cid) or p
            if not p.is_file():
                raise FileNotFoundError(f"sin composición del candidato {cid}")
            # T-229: sin GeoJSON propio (el vigente se monta sobre las filas del canónico) valen los atributos del canónico
            return p, next(iter(sorted((carpeta / cid).glob("*_m06_secciones.geojson*"))), attrs_canonico)
        attrs_canonico = None
        can, attrs = donde(d["canonico"])
        attrs_canonico = attrs
        res["ganador"], res["canonico_id"] = d["ganador"], d["canonico"]
        try:  # comprobación 1: clave de elección del ganador frente a la del canónico (la calcula la competición)
            res["clave_frente_canonico"] = json.loads((carpeta / "RESUMEN.json").read_text(encoding="utf-8"))["territorios"][0].get("frente_al_canonico")
        except (OSError, ValueError, KeyError, IndexError):
            res["clave_frente_canonico"] = None
        res["canonico"] = _indicadores_plan(can, cfg, grafo, can, attrs)
        if d["ganador"] == d["canonico"]:
            gan = res["canonico"]
        else:
            comp_g, attrs_g = donde(d["ganador"])
            gan = _indicadores_plan(comp_g, cfg, grafo, can, attrs_g)
        res["ganador_indicadores"] = gan
        bloque = d.get("vigente") or {}
        if pub is None:
            k = int(((cfg.get("validation") or {}).get("expected_districts")) or 0)
            res["estado"], res["motivo"] = ("UN_DISTRITO", "un solo distrito: el único plan posible; sin composición vigente") \
                if k == 1 else ("SIN_VIGENTE", motivo_sin)
            if bloque.get("sha256_origen"):  # T-258: la competición juzgó un vigente que no es el publicado
                res["estado"], res["motivo"] = "NO_EVALUABLE", "la competición juzgó un vigente y no hay mapa publicado"
            return res
        if bloque:  # T-258: un único vigente; la competición y la comprobación 2 miden el mismo fichero publicado
            import hashlib
            if bloque.get("estado") == "VIGENTE_OTRO_SECCIONADO":  # T-224: sin vigente comparable, consta y no bloquea
                res["estado"], res["motivo"] = "SIN_VIGENTE", bloque.get("detalle") or "vigente excluido: otro seccionado"
                return res
            if bloque.get("sha256_origen") != hashlib.sha256(pub.read_bytes()).hexdigest():
                res["estado"], res["motivo"] = "NO_EVALUABLE", (
                    f"vigente distinto del publicado: la competición juzgó {bloque.get('origen') or bloque.get('estado')} "
                    f"(sha256 {str(bloque.get('sha256_origen'))[:12]}) y el visor publica {res['fichero_vigente']}")
                return res
        from ddd_motor2.adaptadores import ErrorDatos
        vig = _vigente_sobre(can, pub, carpeta / "vigente", columnas_de_contrato(cfg))
        try:
            res["vigente"] = _indicadores_plan(vig, cfg, grafo, can, attrs)
        except ErrorDatos as exc:  # T-229: el vigente reparte unidades M04 → el de la competición, con piezas finas
            fino = _vigente_de_la_competicion(carpeta, d, can, pub, columnas_de_contrato(cfg)) if "atomicidad" in str(exc) else None
            if fino is None:
                raise
            res["vigente"] = _indicadores_plan(fino, cfg, grafo, can, attrs)
            res["vigente_lectura"] = f"piezas finas de la competición ({exc})"
        causas = peor_que(gan, res["vigente"])
        res["estado"], res["motivo"] = ("PEOR", "; ".join(causas)) if causas else ("OK", "")
        res["aviso_desvio"] = aviso_desvio(gan, res["vigente"])
    except Exception as exc:
        res["estado"], res["motivo"] = "NO_EVALUABLE", f"{type(exc).__name__}: {exc}"
    return res


def _celda(v) -> str:
    return "—" if v is None else (f"{v:.2f}" if isinstance(v, float) else str(v))


def tabla_indicadores(r: dict) -> list[str]:
    clave = r.get("clave_frente_canonico")
    lin = [f"### {r['territorio']}",
           f"- Comprobación 1 · clave de elección frente al canónico: **{clave or 'sin dato'}** ("
           f"{'peor: NO' if clave == 'empeora' else ('sin dato en este paso; la puerta final usa el RESUMEN de la competición' if clave is None else 'no es peor')}).",
           f"- Comprobación 2 · distritos fuera de tolerancia (recuento bruto) frente al vigente: **{r['estado']}**"
           + (f" ({r['motivo']})" if r.get("motivo") else "") + ".",
           f"- Aviso (no bloquea) · desvío máximo frente al vigente: {'; '.join(r['aviso_desvio']) if r.get('aviso_desvio') else 'no es mayor'}.", "",
           f"Vigente: run {r.get('run_vigente') or '—'} · `{r.get('fichero_vigente') or 'sin composición'}`.", "",
           "| Plan | Fuera de tol. | Desvío máx. % | Part. judiciales | Comarcas | Frontera km | PP medio | PP mín. | Válido (reglas actuales) |",
           "|---|---|---|---|---|---|---|---|---|"]
    notas: list[str] = []
    for nombre, k in (("Vigente", "vigente"), (f"Canónico ({r.get('canonico_id', '')})", "canonico"),
                      (f"Ganador ({r.get('ganador', '')})", "ganador_indicadores")):
        x = r.get(k)
        if x is None:
            lin.append(f"| {nombre} | sin dato | | | | | | | |")
            continue
        pp = x.get("pp_medio"), x.get("pp_min")
        lin.append(f"| {nombre} | {x['fuera_tolerancia']} | {x['desvio_max'] * 100:.2f} | {x['partidos_judiciales_partidos']} | "
                   f"{x['comarcas_partidas']} | {_celda(x['frontera_cortada_km'])} | {_celda(pp[0] and round(pp[0], 3))} | "
                   f"{_celda(pp[1] and round(pp[1], 3))} | {x['valido_reglas_actuales']} |")
        if x.get("pp_error"):
            notas.append(f"Polsby-Popper de {nombre.split(' ')[0].lower()} no calculado: {x['pp_error']}")
    return lin + ([""] + notas if notas else [])


def escribir_indicadores(r: dict, out: Path) -> str:
    """INDICADORES.json y .md junto al COMPETICION.json del territorio; devuelve el markdown (resumen del paso)."""
    carpeta = Path(out) / "competicion" / r["territorio"]
    carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / "INDICADORES.json").write_text(json.dumps(r, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md = "\n".join(tabla_indicadores(r)) + "\n"
    (carpeta / "INDICADORES.md").write_text(md, encoding="utf-8")
    return md


def indicadores(args) -> int:
    print(escribir_indicadores(indicadores_territorio(args.territorio, Path(args.out)), Path(args.out)))
    return 0  # el veredicto lo da `aceptacion`; aquí solo se deja constancia


def cadenas_de(carpeta: Path) -> dict | None:
    """Candidatos de un COMPETICION.json: el canónico, el vigente (T-217) y el exhaustivo no son cadenas; el resto sí.
    `vigente_compite`: el bloque «vigente» dice que compite Y está entre los candidatos (si no cuadran, `vigente_incoherente`);
    `vigente_excluido`: motivo por el que no compite (también si el COMPETICION.json no trae bloque «vigente»; None si compite)."""
    try:
        d = json.loads((carpeta / "COMPETICION.json").read_text(encoding="utf-8"))
        todos = d["candidatos"]
        info = d.get("vigente") or {}
        en_lista = any(c["id"] == "vigente" for c in todos)
        dice = bool(info.get("compite"))
        excluido = None
        if not info and not en_lista:
            excluido = "sin bloque «vigente» en COMPETICION.json (función A o competición anterior a T-217)"
        elif info and not dice and not en_lista:
            excluido = "; ".join(x for x in (info.get("estado") or "sin estado", info.get("detalle")) if x)
        cs = [c for c in todos if c["id"] not in (d["canonico"], "vigente") and c["generador"] not in ("exhaustivo", "exacto")]
        return {"candidatos": len(todos), "exhaustivo": any(c["generador"] == "exhaustivo" for c in todos), "cadenas": len(cs),
                "exacto": any(c["generador"] == "exacto" for c in todos),
                "vigente_compite": dice and en_lista, "vigente_incoherente": dice != en_lista, "vigente_excluido": excluido,
                "evaluables": sum(1 for c in cs if c["estado"] in ("VALIDO", "INVALIDO")),
                "fallos_generador": sum(1 for c in todos if c["estado"] == "FALLO_GENERADOR"),
                "no_evaluados": sorted(c["id"] for c in todos if c["estado"] not in ("VALIDO", "INVALIDO")),
                "invalidas_sin_motivo": sorted(c["id"] for c in cs if c["estado"] == "INVALIDO"
                                               and not (c.get("violaciones") or c.get("detalle")))}
    except (OSError, ValueError, KeyError, TypeError):
        return None


def criterio_aceptacion(filas: list[dict], huellas: dict, esperados: list[str], cadenas: dict | None = None,
                       n_cadenas: int | None = None, vigentes: dict | None = None) -> dict:
    """Criterio T-194 sobre los resultados reales: sin red ni motor. `huellas` = {territorio: HUELLA_REAL.json};
    `cadenas` = {territorio: cadenas_de(...)}. T-181: sin cadena evaluable, con FALLO_GENERADOR, con candidatos sin evaluar,
    con un número de candidatos distinto de 1 + N (+1 si hay exhaustivo, +1 si compite el vigente, T-222) o con una cadena inválida sin motivo, no hay aceptación.
    T-212: `vigentes` = {territorio: INDICADORES.json}; PEOR que el vigente = NO; sin indicadores o NO_EVALUABLE
    = sin aceptación y constan por nombre (nunca verde por omisión); UN_DISTRITO sin vigente consta aparte y vale.
    T-224/T-258: SIN_VIGENTE (sin vigente comparable: otro seccionado o sin mapa publicado) consta con su motivo en
    «vigente_no_comparable» y no bloquea; un vigente de la competición distinto del publicado es NO_EVALUABLE."""
    cadenas = cadenas or {}
    vigentes = vigentes or {}
    est = {t: (vigentes.get(t) or {}).get("estado") for t in esperados}
    vig_peor = sorted(t for t in esperados if est[t] == "PEOR")
    vig_sin = sorted(t for t in esperados if est[t] not in ("OK", "PEOR", "UN_DISTRITO", "SIN_VIGENTE"))
    vig_no_comp = sorted(t for t in esperados if est[t] == "SIN_VIGENTE")  # T-224: consta con su motivo, no bloquea
    vig_un = sorted(t for t in esperados if est[t] == "UN_DISTRITO")
    vig_aviso = sorted(t for t in esperados if (vigentes.get(t) or {}).get("aviso_desvio"))
    por_t = {f["territorio"]: f for f in filas}
    faltan = [t for t in esperados if t not in por_t]
    no_validos = sorted(t for t in esperados if t in por_t and por_t[t].get("estado") != "VALIDO")
    peores = sorted(t for t in esperados if t in por_t and por_t[t].get("frente_al_canonico") == "empeora")
    def mal(c: dict) -> bool:
        esperado = None if n_cadenas is None else (1 + n_cadenas + (1 if c["exhaustivo"] else 0) + (1 if c.get("exacto") else 0)
                                                   + (1 if c.get("vigente_compite") else 0))
        return bool(not c["evaluables"] or c["fallos_generador"] or c["no_evaluados"] or c["invalidas_sin_motivo"]
                    or c.get("vigente_incoherente") or (esperado is not None and c["candidatos"] != esperado))
    sin_cadenas = sorted(t for t in esperados if not (cadenas.get(t) or {}).get("evaluables"))
    fallo_gen = sorted(t for t in esperados if (cadenas.get(t) or {}).get("fallos_generador"))
    incompletos = sorted(t for t in esperados if t in cadenas and cadenas[t] and mal(cadenas[t]) and t not in sin_cadenas + fallo_gen)
    h_pedidas = [t for t in HUELLA_REAL if t in esperados]
    h_mal = sorted(t for t in h_pedidas if not (huellas.get(t) or {}).get("igual"))
    return {"esperados": len(esperados), "faltan": faltan, "no_validos": no_validos, "empeoran": peores,
            "sin_cadenas": sin_cadenas, "fallo_generador": fallo_gen, "candidatos_incompletos": incompletos,
            "vigente_excluido": {t: c["vigente_excluido"] for t in esperados if (c := cadenas.get(t)) and c.get("vigente_excluido")},
            "vigente_peor": vig_peor, "vigente_sin": vig_sin, "vigente_un_distrito": vig_un, "vigente_aviso_desvio": vig_aviso,
            "vigente_no_comparable": {t: (vigentes.get(t) or {}).get("motivo") or "" for t in vig_no_comp},
            "vigente_motivos": {t: (vigentes.get(t) or {}).get("motivo") or "sin INDICADORES.json" for t in vig_peor + vig_sin},
            "huella_real": {t: (huellas.get(t) or {}).get("huella_1") for t in h_pedidas}, "huella_real_mal": h_mal,
            "parcial": len(h_pedidas) < len(HUELLA_REAL),
            "aceptacion": bool(esperados) and not (faltan or no_validos or peores or h_mal or sin_cadenas or fallo_gen or incompletos or vig_peor or vig_sin) and len(h_pedidas) == len(HUELLA_REAL)}


def aceptacion(args) -> int:
    from ddd_motor2.competir import escribir_resumen
    out = Path(args.out)
    filas, huellas = [], {}
    for f in sorted(out.rglob("RESUMEN.json")):
        if f.parent.parent.name == "competicion" and f.parent.name != "_huella2":
            filas.extend(json.loads(f.read_text(encoding="utf-8"))["territorios"])
    for f in sorted(out.rglob("HUELLA_REAL.json")):
        h = json.loads(f.read_text(encoding="utf-8"))
        huellas[h["territorio"]] = h
    esperados = args.territorios or territorios()
    vigentes = {}
    for f in sorted(out.rglob("INDICADORES.json")):
        if f.parent.parent.name == "competicion":
            i = json.loads(f.read_text(encoding="utf-8"))
            vigentes[i["territorio"]] = i
    filas = sorted({x["territorio"]: x for x in filas}.values(), key=lambda x: x["territorio"])
    tot = escribir_resumen(filas, out / "competicion") if filas else {}
    cadenas = {t: c for t in esperados if (c := cadenas_de(out / "competicion" / t)) is not None}
    res = criterio_aceptacion(filas, huellas, esperados, cadenas, args.cadenas, vigentes)
    res["totales"] = tot
    (out / "ACEPTACION.json").write_text(json.dumps(res, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    fallos = bool(res["faltan"] or res["no_validos"] or res["empeoran"] or res["huella_real_mal"] or res["sin_cadenas"]
              or res["fallo_generador"] or res["candidatos_incompletos"] or res["vigente_peor"] or res["vigente_sin"]
              or not esperados)
    veredicto = "NO" if fallos else ("PARCIAL (sin las tres huellas reales: no es aceptación)" if res["parcial"] else "SÍ")
    md = [f"# Aceptación del motor 2 · {veredicto}", "",
          f"- Territorios esperados: {res['esperados']}; faltan: {res['faltan'] or 'ninguno'}.",
          f"- No válidos: {res['no_validos'] or 'ninguno'}; peores que el canónico: {res['empeoran'] or 'ninguno'}.",
          f"- Sin ninguna cadena evaluable: {res['sin_cadenas'] or 'ninguno'}; con FALLO_GENERADOR: {res['fallo_generador'] or 'ninguno'}; "
          f"candidatos sin evaluar o fuera de 1 + N (+1 exhaustivo, +1 exacto, +1 vigente que compite): {res['candidatos_incompletos'] or 'ninguno'}.",
          f"- Vigente excluido de la competición (no cuenta como candidato): {', '.join(res['vigente_excluido']) or 'ninguno'}.",
          *[f"  - {t}: {m}" for t, m in res["vigente_excluido"].items()],
          f"- Comprobación 1 · clave de elección peor que la del canónico: {res['empeoran'] or 'ninguno'}.",
          f"- Comprobación 2 · más distritos fuera de tolerancia (recuento bruto) que el mapa vigente publicado: {res['vigente_peor'] or 'ninguno'}; sin vigente comparable (no cuentan como verde): "
          f"{res['vigente_sin'] or 'ninguno'}; un distrito sin composición vigente (único plan posible): {res['vigente_un_distrito'] or 'ninguno'}.",
          f"- Sin vigente comparable (T-224: otro seccionado, sin mapa publicado en el visor o el run publicado sin composición versionada; SIN_VIGENTE consta y NO bloquea la aceptación): {', '.join(res['vigente_no_comparable']) or 'ninguno'}.",
          *[f"  - {t}: {m}" for t, m in res["vigente_no_comparable"].items()],
          f"- Aviso (no bloquea) · desvío máximo mayor que el del vigente: {res['vigente_aviso_desvio'] or 'ninguno'}.",
          *[f"  - {t}: {m}" for t, m in res["vigente_motivos"].items()],
          f"- Huella real (Soria, Álava, Melilla; dos ejecuciones iguales): "
          f"{'fallan ' + ', '.join(res['huella_real_mal']) if res['huella_real_mal'] else 'correcta'} {res['huella_real']}."]
    if vigentes:
        md += ["", "## Frente al vigente (fuera de tolerancia · desvío máx. %)", "",
               "| Territorio | Estado | Vigente | Canónico | Ganador |", "|---|---|---|---|---|"]
        for t in esperados:
            i = vigentes.get(t) or {}
            c = lambda k: (f"{i[k]['fuera_tolerancia']} · {i[k]['desvio_max'] * 100:.2f}" if i.get(k) else "—")  # noqa: E731
            md.append(f"| {t} | {i.get('estado', 'sin INDICADORES.json')} | {c('vigente')} | {c('canonico')} | {c('ganador_indicadores')} |")
    (out / "ACEPTACION.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))
    return 1 if fallos else 0  # PARCIAL sale 0 (sin fallos) pero nunca cuenta como aceptación: `aceptacion` es false


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("nacionales")
    for nombre in ("entradas", "motor"):
        p = sub.add_parser(nombre)
        p.add_argument("territorios", nargs="*")
        p.add_argument("--todos", action="store_true")
        p.add_argument("--out", default=str(OUT))
        if nombre == "entradas":
            p.add_argument("--desde-r2", action="store_true", help="obsoleto (T-298): R2 es la vía por defecto")
            p.add_argument("--desde-fuente", action="store_true", help="solo diagnóstico local: reconstruye desde las fuentes, no desde R2")
            p.add_argument("--seccionado", default="shapefile", choices=("ogc", "shapefile"),
                           help="solo --desde-fuente. shapefile (por defecto): copia nacional verificada, sin red; ogc: OGC del INE (exige --permitir-red-ine)")
            p.add_argument("--permitir-red-ine", action="store_true",
                           help="solo diagnóstico local con --desde-fuente --seccionado ogc: permite ir al OGC del INE; la batería nunca lo usa")
        if nombre == "motor":
            p.add_argument("--m05", default="7.4.4", choices=sorted(M05_BASE))
    sub.add_parser("matriz").add_argument("--out", default=str(OUT))
    p = sub.add_parser("indicadores")
    p.add_argument("territorio")
    p.add_argument("--out", default=str(OUT))
    p = sub.add_parser("archivar-p10")
    p.add_argument("territorio")
    p.add_argument("--paquete", required=True)
    p.add_argument("--run", default="")
    p.add_argument("--out", default=str(OUT))
    sub.add_parser("lista").add_argument("territorios", nargs="*")
    p = sub.add_parser("huella")
    p.add_argument("territorio")
    p.add_argument("--out", default=str(OUT))
    p.add_argument("--funcion", default="D8")
    p.add_argument("--cadenas", type=int, default=10)
    p = sub.add_parser("aceptacion")
    p.add_argument("--cadenas", type=int, default=10)
    p.add_argument("territorios", nargs="*")
    p.add_argument("--out", default=str(OUT))
    a = ap.parse_args(argv)
    return {"lista": lista, "huella": huella, "indicadores": indicadores, "aceptacion": aceptacion, "nacionales": nacionales, "archivar-p10": archivar_p10, "entradas": entradas, "motor": motor, "matriz": matriz}[a.cmd](a)


if __name__ == "__main__":
    raise SystemExit(main())
