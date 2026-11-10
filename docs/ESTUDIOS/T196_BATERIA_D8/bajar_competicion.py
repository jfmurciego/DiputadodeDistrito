#!/usr/bin/env python3
"""T-196b: de los zips bateria-motor2-<run>-<t> (dir con ellos y lista id/nombre) saca datos/CANDIDATOS.csv y datos/MANIFEST_ARTEFACTOS.tsv.
Uso: python -I bajar_competicion.py <dir_zips> <arts.tsv>   (arts.tsv: id, nombre, expired)"""
import csv, hashlib, json, sys, zipfile
from pathlib import Path
zd, lista = Path(sys.argv[1]), Path(sys.argv[2])
out = Path(__file__).parent / "datos"
filas, man = [], []
for ln in sorted(lista.read_text().splitlines(), key=lambda l: l.split("\t")[1]):
    id_, nombre, _ = ln.split("\t")
    z = zd / f"{nombre}.zip"
    man.append((id_, nombre, hashlib.sha256(z.read_bytes()).hexdigest(), z.stat().st_size))
    with zipfile.ZipFile(z) as zf:
        n = [x for x in zf.namelist() if x.endswith("/COMPETICION.json")]
        if not n: continue  # p. ej. el artefacto «aceptacion»
        n = n[0]
        d = json.loads(zf.read(n))
    for c in d["candidatos"]:
        k = c.get("clave_naturalidad") or []
        k = k + [None] * 6
        filas.append({"territorio": d["territorio"], "candidato": c["id"], "canonico": c["id"] == "canonico",
                      "ganador": c["id"] == d["ganador"], "estado": c["estado"], "violaciones_duras": c["violaciones_duras"],
                      "fuera_tolerancia": c["fuera_tolerancia"], "desvio_max_pct": round(c["desvio_max"] * 100, 2),
                      "clave_fuera_tol": k[0], "exceso_tope": k[1], "demarcaciones_partidas": k[2],
                      "frontera_cortada_km": k[3], "clave_desvio": k[4], "huella_plan": c["huella_plan"]})
with open(out / "CANDIDATOS.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(filas[0])); w.writeheader(); w.writerows(filas)
with open(out / "MANIFEST_ARTEFACTOS.tsv", "w") as f:
    f.write("artefacto_id\tnombre\tsha256_zip\tbytes\n")
    for m in man: f.write("\t".join(map(str, m)) + "\n")
print(len(man), "artefactos", len(filas), "candidatos")
