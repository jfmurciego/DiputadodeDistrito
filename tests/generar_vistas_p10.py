# -*- coding: utf-8 -*-
"""T-375 (D-136/D-151): vistas derivadas de `p10-fuentes.yml` por tipo, con la forma de los workflows viejos.

PROYECTO: Diputado de Distrito · VERSIÓN: 1.0.0 · FECHA: 2026-11-17 · ESTADO: candidato · ANTERIOR: ninguna (fichero nuevo)
`p10-fuentes.yml` lleva los jobs de P11 (`p11_*`) y de P12 (`p12_*`). Muchos tests de contrato leen los jobs con los ids de siempre
(`resolver`, `territoriales`, `registrar`…): esta herramienta extrae de P10 los jobs de un tipo, quita el prefijo y revierte las
adaptaciones propias de P10 (needs/if de la entrada, territorio `inputs.territory_id || inputs.territorio`, edición `|| '2025'` y `always() && … != 'skipped'`),
y escribe `tests/fixtures/p10_vistas/_p11-territoriales.yml` y `_p12-electorales.yml`.
Reproducible: `python tests/generar_vistas_p10.py` las reescribe; `--comprobar` falla si difieren de lo generado (lo ejecuta tests/test_t375_p10_equivalencia.py).
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P10 = ROOT / ".github" / "workflows" / "p10-fuentes.yml"
SALIDA = ROOT / "tests" / "fixtures" / "p10_vistas"
TIPOS = {"p11": "_p11-territoriales.yml", "p12": "_p12-electorales.yml"}


def vista(tipo: str, texto: str | None = None) -> str:
    texto = texto if texto is not None else P10.read_text(encoding="utf-8")
    cabecera, resto = texto.split("\njobs:\n", 1)
    bloques = re.split(r"(?m)^(?=  [a-z0-9_]+:\n)", resto)
    jobs = [b for b in bloques if b.startswith(f"  {tipo}_")]
    cuerpo = "".join(b.rstrip("\n") + "\n\n" for b in jobs).rstrip("\n") + "\n"
    cuerpo = re.sub(rf"(?m)^  {tipo}_", "  ", cuerpo)
    cuerpo = re.sub(rf"needs\.{tipo}_", "needs.", cuerpo)

    def needs(m):
        return m.group(1) + re.sub(rf"(?<![\w-]){tipo}_", "", m.group(2))

    cuerpo = re.sub(r"(?m)^(    needs: )(.*)$", needs, cuerpo)
    cuerpo = cuerpo.replace("    needs: entrada\n", "", 1)
    cuerpo = re.sub(r"(?m)^    if: \$\{\{ contains\(inputs\.tipo, '[a-z]+'\) \}\}\n", "", cuerpo, count=1)
    cuerpo = cuerpo.replace("(inputs.territory_id || inputs.territorio)", "inputs.territory_id")
    cuerpo = cuerpo.replace('EDITION: "${{ inputs.data_edition || \'2025\' }}"', "EDITION: '${{ inputs.data_edition }}'")
    cuerpo = cuerpo.replace(" && needs.resolver.result != 'skipped' }}", " }}")
    # Salidas de workflow_call: solo las del tipo, con los ids viejos.
    ini, fin = cabecera.index("    outputs:\n"), cabecera.index("  workflow_dispatch:\n")
    lineas = cabecera[ini:fin].split("\n")
    salidas, i = ["    outputs:"], 1
    while i + 1 < len(lineas):
        nombre, valor = lineas[i], lineas[i + 1]
        partes = [p for p in re.findall(r"jobs\.[\w.]+", valor) if p.startswith(f"jobs.{tipo}_")]
        if partes:
            salidas += [nombre, "        value: ${{ " + " || ".join(p.replace(f"jobs.{tipo}_", "jobs.", 1) for p in partes) + " }}"]
        i += 2
    cabecera = cabecera[:ini] + "\n".join(salidas) + "\n" + cabecera[fin:]
    return (f"# VISTA DERIVADA de .github/workflows/p10-fuentes.yml (tipo {tipo.upper()}); no editar: python tests/generar_vistas_p10.py\n"
            f"{cabecera}\njobs:\n{cuerpo}")


def main(argv):
    ok = True
    for tipo, nombre in TIPOS.items():
        nuevo = vista(tipo)
        ruta = SALIDA / nombre
        if "--comprobar" in argv:
            if not ruta.is_file() or ruta.read_text(encoding="utf-8") != nuevo:
                print(f"DIFIERE: {ruta}"); ok = False
        else:
            SALIDA.mkdir(parents=True, exist_ok=True)
            ruta.write_text(nuevo, encoding="utf-8")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
