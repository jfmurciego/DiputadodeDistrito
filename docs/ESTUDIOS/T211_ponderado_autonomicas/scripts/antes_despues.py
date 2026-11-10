"""T-211: antes (r3, CANDIDATOS.csv de T-196) y después (competición local con naturalidad_clave 1.1.0)."""
import csv, json, sys
from pathlib import Path
antes = {}
for r in csv.DictReader(open(sys.argv[1])):
    if r["canonico"] == "True": antes.setdefault(r["territorio"], {})["can"] = r
    if r["ganador"] == "True": antes.setdefault(r["territorio"], {})["gan"] = r
print("| Territorio | Canónico | Ganador r3 (antes) | Ganador ahora | Clave del ganador ahora (fuera, exceso, demarcaciones) |")
print("|---|---|---|---|---|")
for t, d in (("aragon", "bat3a"), ("castilla_la_mancha", "bat3b"), ("castilla_y_leon", "bat3a"), ("galicia", "bat3b")):
    C = json.loads(Path(f"/tmp/claude-0/{d}/competicion/{t}/COMPETICION.json").read_text())
    g = next(c for c in C["candidatos"] if c["id"] == C["ganador"])
    c = next(x for x in C["candidatos"] if x["id"] == "canonico")
    a = antes[t]
    print(f"| {t} | {c['fuera_tolerancia']} (r3 {a['can']['fuera_tolerancia']}) | {a['gan']['candidato']}: "
          f"{a['gan']['fuera_tolerancia']} | {g['id']}: {g['fuera_tolerancia']} | "
          f"{g['clave_naturalidad'][0]}, {g['clave_naturalidad'][1]:.4f}, {g['clave_naturalidad'][2]} |")
