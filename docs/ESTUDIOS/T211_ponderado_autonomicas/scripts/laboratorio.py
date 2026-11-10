"""T-211: cifras del laboratorio T-179 que cita el README (unidades, fuera de tolerancia del vigente, planes únicos)."""
import json, glob
R = "docs/ESTUDIOS/T179_naturalidad_nacional/autonomicas/resultados/"
for t in ("madrid", "comunidad_foral_de_navarra"):
    r = json.load(open(f"{R}{t}/RESULTADO.json"))
    un = [c["unicos"] for c in r["cadenas"]["ponderado"]]
    print(f"{t}: unidades {r['unidades']}; vigente (A) fuera de tolerancia {len(r['ganadores']['A']['fuera_tolerancia'])}; "
          f"planes únicos por cadena ponderada {min(un)}-{max(un)} ({len(un)} cadenas, {r['parametros']['pasos']} pasos)")
m = json.load(open("datos/composicion/MANIFEST.json"))["territorios"]["comunidad_foral_de_navarra"]["run_id"]
e = json.load(open(f"territorios/comunidad_foral_de_navarra/evidencia/ejecuciones_completas/{m}.json"))
print(f"mapa publicado de Navarra: run {m}, optimization_algorithm = {e.get('optimization_algorithm')!r}")
