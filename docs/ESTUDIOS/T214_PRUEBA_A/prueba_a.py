# PROYECTO: Diputado de Distrito
# VERSIÓN: 1.0.0
# FECHA: 2026-11-10
# QUÉ HACE: prueba A de T-170 (T-214): ejecuta el canónico actual (M04 + M05 de main, sin editarlos) con el id viejo y
#   con el id nuevo del mismo territorio y compara bit a bit la asignación unidad→distrito y el GeoJSON.
# CAMBIOS: fichero nuevo.
# MOTIVO: D-60/D-61: el cambio de id no puede cambiar el mapa.
# ANTERIOR: ninguna (fichero nuevo)
# USO: python docs/ESTUDIOS/T214_PRUEBA_A/prueba_a.py <id_viejo> <m01.geojson.zip> <m03_grafo.json[.gz]> [--salida informe.json]
#   Se ejecuta desde la raíz del repo. Crea territorios/<id_nuevo>/ temporal (copia del contrato con el id sustituido)
#   y lo borra al acabar. Las entradas se copian a .cache (ignorado por git).
import argparse, gzip, hashlib, json, shutil, subprocess, sys, tempfile, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from ddd_core.territorio_ids import resolver_id  # noqa: E402


def _sha(b):
    return hashlib.sha256(b).hexdigest()


def _geojson_bytes(zip_path):
    with zipfile.ZipFile(zip_path) as z:
        names = [n for n in z.namelist() if n.endswith((".geojson", ".json"))]
        return z.read(names[0])


def _asignacion(raw, id_field="CUSEC_KEY", district_field="district_id"):
    data = json.loads(raw)
    return {str(f["properties"][id_field]): f["properties"].get(district_field) for f in data["features"]}


def _campos_con_id(raw, tid):
    """Claves (de nivel superior o de propiedades) cuyo valor contiene el id: lo único que puede diferir."""
    data = json.loads(raw)
    claves = {k for k, v in data.items() if k != "features" and tid in json.dumps(v, ensure_ascii=False)}
    for f in data["features"]:
        claves |= {f"properties.{k}" for k, v in f["properties"].items() if tid in str(v)}
    return sorted(claves)


def _preparar(tid, m01, m03, contrato_txt=None, viejo=None, lookup_tmp=None):
    tdir = ROOT / "territorios" / tid
    if contrato_txt is not None:
        (tdir / "config").mkdir(parents=True, exist_ok=True)
        txt = contrato_txt.replace(viejo, tid)
        if lookup_tmp:
            txt = txt.replace("configuracion/particiones_insulares_2025.json", str(lookup_tmp))
        (tdir / "config" / f"{tid}_2025.yaml").write_text(txt, encoding="utf-8")
        src = ROOT / "territorios" / viejo / "config" / "fuentes_oficiales.yaml"
        if src.exists():
            (tdir / "config" / "fuentes_oficiales.yaml").write_text(src.read_text(encoding="utf-8").replace(viejo, tid), encoding="utf-8")
    cache = tdir / ".cache" / "ddd" / "preparacion" / f"{tid}_2025"
    if cache.exists():
        shutil.rmtree(cache)
    cache.mkdir(parents=True)
    shutil.copyfile(m01, cache / f"{tid}_2025_m01_secciones_poblacion.geojson.zip")
    raw = Path(m03).read_bytes()
    if str(m03).endswith(".gz"):
        raw = gzip.decompress(raw)
    (cache / f"{tid}_2025_m03_grafo.json").write_bytes(raw)
    return tdir / "config" / f"{tid}_2025.yaml", cache


def _motor(params, log):
    for mod in ("modulos/04_generar_semillas.py", "modulos/05_optimizar_distritos.py"):
        r = subprocess.run([sys.executable, mod, "--params", str(params.relative_to(ROOT))], cwd=ROOT,
                           capture_output=True, text=True)
        log.write_text((log.read_text() if log.exists() else "") + f"$ {mod}\n{r.stdout}\n{r.stderr}\n")
        if r.returncode != 0:
            raise SystemExit(f"{mod} falló con {params.name} (código {r.returncode}); log en {log}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("viejo"); ap.add_argument("m01"); ap.add_argument("m03"); ap.add_argument("--salida")
    a = ap.parse_args()
    viejo = a.viejo
    nuevo = resolver_id(viejo)
    assert nuevo != viejo, "el id ya es nuevo"
    contrato = ROOT / "territorios" / viejo / "config" / f"{viejo}_2025.yaml"
    txt = contrato.read_text(encoding="utf-8")
    tmp = Path(tempfile.mkdtemp(prefix=f"pruebaA_{nuevo}_"))
    lookup_tmp = None
    if "particiones_insulares_2025.json" in txt:
        pay = json.loads((ROOT / "configuracion/particiones_insulares_2025.json").read_text(encoding="utf-8"))
        pay["territories"] = {(nuevo if k == viejo else k): v for k, v in pay["territories"].items()}
        lookup_tmp = tmp / "particiones_insulares_2025.json"
        lookup_tmp.write_text(json.dumps(pay, ensure_ascii=False), encoding="utf-8")
    nuevo_dir = ROOT / "territorios" / nuevo
    if nuevo_dir.exists():
        raise SystemExit(f"{nuevo_dir} ya existe: no se pisa")
    res = {"id_viejo": viejo, "id_nuevo": nuevo, "contrato_sha256": _sha(contrato.read_bytes()),
           "m01_sha256": _sha(Path(a.m01).read_bytes()), "m03_sha256": _sha(Path(a.m03).read_bytes())}
    try:
        p_v, c_v = _preparar(viejo, a.m01, a.m03)
        p_n, c_n = _preparar(nuevo, a.m01, a.m03, txt, viejo, lookup_tmp)
        _motor(p_v, tmp / "log_viejo.txt")
        _motor(p_n, tmp / "log_nuevo.txt")
        for etapa, suf in (("M04", "m04_semillas"), ("M05", "m05_distritos_optimizados")):
            bv = _geojson_bytes(c_v / f"{viejo}_2025_{suf}.geojson.zip")
            bn = _geojson_bytes(c_n / f"{nuevo}_2025_{suf}.geojson.zip")
            av, an = _asignacion(bv), _asignacion(bn)
            res[etapa] = {
                "geojson_sha256_viejo": _sha(bv), "geojson_sha256_nuevo": _sha(bn),
                "geojson_identico": bv == bn,
                "geojson_identico_salvo_id": bv.replace(viejo.encode(), nuevo.encode()) == bn,
                "unidades": len(av), "distritos": len(set(av.values())),
                "asignacion_identica": av == an,
                "asignacion_sha256": _sha(json.dumps(sorted(av.items()), default=str).encode()),
                "campos_con_el_id": _campos_con_id(bn, nuevo),
            }
        res["PASA"] = all(res[e]["asignacion_identica"] and res[e]["geojson_identico_salvo_id"] for e in ("M04", "M05"))
    finally:
        shutil.rmtree(nuevo_dir, ignore_errors=True)
        shutil.rmtree(ROOT / "territorios" / viejo / ".cache", ignore_errors=True)
    out = json.dumps(res, ensure_ascii=False, indent=2)
    print(out)
    if a.salida:
        Path(a.salida).write_text(out + "\n", encoding="utf-8")
    return 0 if res["PASA"] else 1


if __name__ == "__main__":
    sys.exit(main())
