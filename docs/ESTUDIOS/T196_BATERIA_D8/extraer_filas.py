#!/usr/bin/env python3
"""T-196: extrae la fila JSON de `ddd_motor2.competir` de cada job «Competición <t>» del run 42886114842 (logs por job).

Uso: python extraer_filas.py <owner/repo> > datos/filas.json   (necesita `gh`; los artefactos dan 403 desde la nube)
Solo lee la API de Actions; no lanza nada. La fila es la que imprime `competir` por territorio."""
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = sys.argv[1] if len(sys.argv) > 1 else "jfmurciego/DiputadodeDistrito"
JOBS = Path(__file__).parent / "datos" / "JOBS_run42886114842.tsv"


def fila(linea: str):
    id_, nombre, _ = linea.rstrip("\n").split("\t")
    if not nombre.startswith("Competición "):
        return None
    t = nombre.split()[-1]
    log = subprocess.run(["gh", "api", f"repos/{REPO}/actions/jobs/{id_}/logs"], capture_output=True, text=True, check=True).stdout
    for x in log.splitlines():
        m = re.search(r'(\{"territorio": "%s", "estado".*\})\s*$' % re.escape(t), x)
        if m:
            return {**json.loads(m.group(1)), "job_id": int(id_)}
    raise SystemExit(f"sin fila en el log de {t}")


with ThreadPoolExecutor(6) as ex:
    filas = sorted((f for f in ex.map(fila, JOBS.read_text().splitlines()) if f), key=lambda f: f["territorio"])
print(json.dumps(filas, indent=1, ensure_ascii=False))
