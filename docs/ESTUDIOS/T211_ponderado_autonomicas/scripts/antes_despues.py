"""T-211: antes (r3, CANDIDATOS.csv de T-196) y después (competición local con naturalidad_clave 1.1.0).
Los COMPETICION.json del «después» se generaron en sesión (no están en git) con el commit 3326ef48 (rama
claude/t211-diagnostico-ponderado; version_orquestador «1.3.1»: el mismo código que competicion 1.3.2 /
naturalidad_clave 1.1.0 de #693, salvo la cabecera y VERSION). Su extracto (ganador, fuera de tolerancia y clave de cada
candidato, huella) está en ../datos/despues_clave_contrato.json. Con #694 (competicion 1.4.0: el vigente compite y
piezas finas) la competición ya no es la misma, y la batería nueva no reproduce estas huellas: solo la regla «el
ganador no tiene más fuera de tolerancia del contrato que el canónico».
"""
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
