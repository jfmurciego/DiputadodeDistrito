#!/usr/bin/env python3
"""T-196: agregados de la batería r3 (motor 2, D8, N=10; run 42886114842) y comparación con el laboratorio T-179 (D8 frente a A).

Uso: python analizar.py   (desde cualquier carpeta; lee datos/filas.json y las TABLA.csv de docs/ESTUDIOS/T179_naturalidad_nacional;
escribe datos/COMPARACION.csv e imprime las tablas del README). Sin red: todas las cifras salen de ficheros versionados.

Definiciones. `frente_al_canonico` lo calcula competir.comparar: clave de naturalidad del ganador < = > la del canónico
(evaluable, violaciones duras, distritos fuera de tolerancia, exceso sobre el tope del 8 %, demarcaciones partidas
—partidos judiciales + comarcas agrarias—, frontera cortada, desvío máximo). «Mejora» = el ganador es una cadena con clave
estrictamente menor; «empata» = igual clave (gana el canónico por desempate); «empeora» no puede darse según la clave (el canónico compite); con el recuento bruto de fuera de tolerancia el ganador sí es peor en 6 autonómicas (README, adenda).
La fila de la batería solo trae fuera de tolerancia y desvío del ganador: partidos y comarcas están en COMPETICION.json
(artefacto, no accesible desde la nube). Del laboratorio se usa la misma clave sin exceso_tope (no está en TABLA.csv)."""
import csv
import json
from collections import Counter
from pathlib import Path

AQUI = Path(__file__).resolve().parent
LAB = AQUI.parent / "T179_naturalidad_nacional"
UNICOS = {"congreso_avila", "congreso_ceuta", "congreso_melilla", "congreso_palencia", "congreso_segovia", "congreso_soria",
          "congreso_teruel", "congreso_zamora"}  # un solo distrito: nada que elegir (Ceuta y Melilla autonómicas tienen varios)


def num(x):
    return float(x) if x not in ("", None) else 0.0


def lab_tablas():
    """Lee las TABLA.csv del laboratorio. Cada (territorio, función) debe salir de UNA sola tabla: si dos tablas lo traen, se avisa
    (antes el último en orden alfabético pisaba en silencio: autonomicas/mapas, mapas, t202/mapas)."""
    out, origen, solapes = {}, {}, []
    for f in sorted(LAB.rglob("TABLA.csv")):
        for r in csv.DictReader(open(f, encoding="utf-8")):
            k = (r["territorio"], r["funcion"])
            if k in out:
                solapes.append((k, origen[k], str(f.relative_to(LAB)), out[k] != r))
            out[k], origen[k] = r, str(f.relative_to(LAB))
    if solapes:
        print("AVISO: territorios en más de una TABLA.csv del laboratorio:", solapes)
    return out


def clave_lab(r):  # fuera de tolerancia, demarcaciones partidas, frontera cortada, desvío (en % )
    return (int(r["fuera_tolerancia"]), num(r["pj_partidos"]) + num(r["ca_partidas"]) + num(r["comarca_partidas"]),
            num(r["frontera_cortada"]), num(r["desvio_max_pct"]))


def semilla(c):
    return c.replace("ponderado-s", "").replace("ponderado-", "") if c.startswith("ponderado") else None


def main():
    filas = json.loads((AQUI / "datos" / "filas.json").read_text(encoding="utf-8"))
    lab = lab_tablas()
    out = []
    for f in filas:
        t = f["territorio"]
        a, d8 = lab.get((t, "A")), lab.get((t, "D8"))
        lf = None
        if a and d8:
            ka, kd = clave_lab(a), clave_lab(d8)
            lf = "mejora" if kd < ka else ("empata" if kd == ka else "empeora")
        out.append({
            "territorio": t, "ambito": "congreso" if t.startswith("congreso_") else "autonomica", "un_distrito": t in UNICOS,
            "estado": f["estado"], "candidatos": f["candidatos"], "validos": f["candidatos_validos"],
            "frente_r3": f["frente_al_canonico"], "ganador_r3": f["ganador"],
            "fuera_tol_r3": f["fuera_tolerancia"], "desvio_r3_pct": round(100 * f["desvio_max"], 2),
            "desvio_canonico_r3_pct": round(100 * f["desvio_max_canonico"], 2), "tiempo_s": f["tiempo_s"],
            "lab_frente": lf or "", "lab_candidato": d8["candidato"] if d8 else "",
            "fuera_tol_canonico_r3": f["fuera_tolerancia"] if f["ganador"] == "canonico" else "",  # solo si gana el canónico; si no, solo se sabe >= ganador
            "lab_fuera_tol_A": a["fuera_tolerancia"] if a else "", "lab_fuera_tol_D8": d8["fuera_tolerancia"] if d8 else "",
            "lab_desvio_A_pct": a["desvio_max_pct"] if a else "", "lab_desvio_D8_pct": d8["desvio_max_pct"] if d8 else "",
            "misma_semilla_ganadora": (semilla(f["ganador"]) == semilla(d8["candidato"])) if d8 and semilla(f["ganador"]) else "",
            "mismo_frente": (f["frente_al_canonico"] == lf) if lf else "",
        })
    with open(AQUI / "datos" / "COMPARACION.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    cabecera = ("| Territorio | Frente r3 | Fuera de tol.: vigente (lab A) | canónico r3 | ganador r3 | lab D8 | Desvío máx. %: vigente | canónico r3 | ganador r3 | lab D8 |\n"
                "|---|---|---|---|---|---|---|---|---|---|")
    filas_md = [f"| {r['territorio']} | {r['frente_r3']} | {r['lab_fuera_tol_A'] or 'n/d'} | "
                f"{r['fuera_tol_canonico_r3'] if r['fuera_tol_canonico_r3'] != '' else ('≥ ' + str(r['fuera_tol_r3']))} | {r['fuera_tol_r3']} | "
                f"{r['lab_fuera_tol_D8'] or 'n/d'} | {r['lab_desvio_A_pct'] or 'n/d'} | {r['desvio_canonico_r3_pct']} | {r['desvio_r3_pct']} | "
                f"{r['lab_desvio_D8_pct'] or 'n/d'} |" for r in out]
    (AQUI / "datos" / "TABLA_TERRITORIOS.md").write_text(
        "# Tabla por territorio (T-196)\n\nGenerada por `analizar.py`. «vigente» = mapa publicado en `datos/composicion` (columna A del laboratorio T-179). "
        "El canónico de r3 solo tiene dato de distritos fuera de tolerancia donde gana el canónico; en el resto la tabla pone «≥ ganador», que vale solo para la clave de elección y NO para el recuento bruto (en 6 autonómicas el canónico tiene menos que el ganador: Andalucía figura «≥ 21» y el canónico real es 20; véase la adenda del README) "
        "y el valor exacto está en `COMPETICION.json` (artefacto, no accesible). "
        "n/d = territorio sin dato en el laboratorio.\n\n" + cabecera + "\n" + "\n".join(filas_md) + "\n", encoding="utf-8")
    print("## Frente al canónico (r3)")
    for amb in ("congreso", "autonomica", None):
        rs = [r for r in out if amb is None or r["ambito"] == amb]
        multi = [r for r in rs if not r["un_distrito"]]
        print(f"- {amb or 'total'}: {len(rs)} territorios {dict(Counter(r['frente_r3'] for r in rs))}; con más de un distrito "
              f"{len(multi)} {dict(Counter(r['frente_r3'] for r in multi))}; fuera de tolerancia del ganador {sum(r['fuera_tol_r3'] for r in rs)}; "
              f"gana cadena {sum(1 for r in rs if r['ganador_r3'] != 'canonico')}; tiempo {round(sum(r['tiempo_s'] for r in rs) / 60)} min")
    cj = [r for r in out if r["lab_frente"]]
    print(f"\n## Laboratorio T-179 (D8 frente a A, misma clave sin exceso_tope): {len(cj)} territorios con dato")
    print(dict(Counter(r["lab_frente"] for r in cj if not r["un_distrito"])))
    print("coinciden frente r3 y laboratorio (más de un distrito):", dict(Counter(r["mismo_frente"] for r in cj if not r["un_distrito"])))
    print("misma cadena ganadora que el laboratorio:", dict(Counter(r["misma_semilla_ganadora"] for r in cj if r["misma_semilla_ganadora"] != "")))
    print("sin dato de laboratorio:", [r["territorio"] for r in out if not r["lab_frente"]])
    print("frente distinto:", [(r["territorio"], r["frente_r3"], r["lab_frente"]) for r in cj if r["mismo_frente"] is False])
    dif = [(r["territorio"], r["fuera_tol_r3"], r["lab_fuera_tol_D8"]) for r in cj if str(r["fuera_tol_r3"]) != str(r["lab_fuera_tol_D8"])]
    print("fuera de tolerancia distinto (ganador r3 / D8 laboratorio):", dif)
    sf = sum(r["fuera_tol_r3"] for r in cj)
    print("suma fuera de tolerancia r3 en los territorios con laboratorio:", sf, "; D8 laboratorio:", sum(int(r["lab_fuera_tol_D8"]) for r in cj),
          "; A laboratorio:", sum(int(r["lab_fuera_tol_A"]) for r in cj))
    dv = sum(abs(float(r["desvio_r3_pct"]) - float(r["lab_desvio_D8_pct"])) > 0.01 for r in cj)
    print("desvío máx. del ganador distinto al D8 del laboratorio (>0,01 pt):", dv, "de", len(cj))


if __name__ == "__main__":
    main()
