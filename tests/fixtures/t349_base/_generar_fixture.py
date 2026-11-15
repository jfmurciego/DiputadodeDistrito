"""Congela el estado de los registros en el commit base de T-349 (una vez; no se ejecuta en los tests).

Uso (desde la raíz, en el commit base indicado en LEEME.md): python tests/fixtures/t349_base/_generar_fixture.py
Copia FIEL los recibos electorales; del resto (fuentes territoriales, par, M06, M08, registro del visor) solo los campos de
identidad. Así los tests no dependen del estado vivo del catálogo: cuando la Activación registre recibos canónicos, la fixture
sigue siendo el estado «antes» (id viejo) que T-349 debe rechazar.
"""
import json
import shutil
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
import sys
sys.path.insert(0, str(ROOT))
OUT = Path(__file__).resolve().parent / "raiz"
from ddd_core import territorio_ids  # noqa: E402

tab = territorio_ids.tabla()
cat = yaml.safe_load((ROOT / "configuracion/catalogo_preparacion.yaml").read_text(encoding="utf-8"))
mini = {"territories": []}


def copiar(rel, campos=None):
    src = ROOT / rel
    dst = OUT / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    if campos is None:
        shutil.copy2(src, dst)
    else:
        d = json.loads(src.read_text(encoding="utf-8"))
        dst.write_text(json.dumps({k: d[k] for k in campos if k in d}, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


if OUT.exists():
    shutil.rmtree(OUT)
for r in cat["territories"]:
    tid = r["territory_id"]
    if tid not in tab:
        continue
    st = r["editions"]["2025"]
    ev = st.get("evidence") or {}
    fila = {"territory_id": tid, "name": r["name"], "editions": {"2025": {"evidence": {}}}}
    e2 = fila["editions"]["2025"]
    prep = st.get("preparation_evidence")
    if prep:
        e2["territorial_sources_prepared"] = True
        e2["preparation_evidence"] = {k: prep[k] for k in ("run_id", "artifact_name", "receipt_path") if k in prep}
        if prep.get("receipt_path"):
            copiar(prep["receipt_path"], ("schema", "kind", "territory_id", "territory_name", "edition", "run_id", "artifact_name", "artifact_sha256", "retrieved_at", "created_at"))
    if ev.get("electoral_source"):
        e2["electoral_source_prepared"] = True
        e2["evidence"]["electoral_source"] = ev["electoral_source"]
        copiar(ev["electoral_source"])
    for clave, campos in (("prepared_source_pair", ("schema", "territory_id", "edition", "pair_sha256")),
                          ("territorial_product", ("schema", "kind", "territory_id", "edition", "run_id", "artifact_name", "artifact_sha256", "stage")),
                          ("electoral_product", ("schema", "kind", "territory_id", "edition", "run_id", "artifact_name", "artifact_sha256", "stage"))):
        if ev.get(clave):
            e2["evidence"][clave] = ev[clave]
            copiar(ev[clave], campos)
    mini["territories"].append(fila)
(OUT / "configuracion").mkdir(parents=True, exist_ok=True)
(OUT / "configuracion/catalogo_preparacion.yaml").write_text(yaml.safe_dump(mini, allow_unicode=True, sort_keys=True), encoding="utf-8")
for carpeta in ("composicion", "resultados"):
    (OUT / "datos" / carpeta).mkdir(parents=True, exist_ok=True)
    for f in sorted((ROOT / "datos" / carpeta).glob("*.csv")):
        (OUT / "datos" / carpeta / f.name).write_text("", encoding="utf-8")
visor = json.loads((ROOT / "orchestracion/publicaciones_visor.json").read_text(encoding="utf-8"))
(OUT / "orchestracion").mkdir(parents=True, exist_ok=True)
(OUT / "orchestracion/publicaciones_visor.json").write_text(json.dumps(
    {"products": [{k: p.get(k) for k in ("id", "kind", "territory_id", "run_id")} for p in visor["products"]], "ensembles": []},
    ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
