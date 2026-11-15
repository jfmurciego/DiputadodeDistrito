"""T-353: los ficheros de `territorios/<aut|nac>NN/config/**` llevan el id canónico de su carpeta.

Sin `git ls-files` (la CI corre en /app sin .git): recorre el árbol. `congreso350_*` queda fuera (D-76).
Falla si un `territory_id` (o claves análogas) difiere de la carpeta, o si alguna ruta `territorios/<id viejo>/` sobrevive.
"""
from __future__ import annotations

import os
import re
import unittest
from pathlib import Path

import yaml

from ddd_core import territorio_ids as ti

ROOT = Path(__file__).resolve().parents[1]
CLAVES = {"territory_id", "territorio_id"}
CARPETA = re.compile(r"^(aut|nac)\d\d$")


def _ficheros():
    base = ROOT / "territorios"
    for carpeta in sorted(p for p in base.iterdir() if p.is_dir() and CARPETA.match(p.name)):
        for d, _, fs in os.walk(carpeta / "config"):
            for f in sorted(fs):
                if f.endswith((".json", ".yaml", ".yml")):
                    yield carpeta.name, Path(d) / f


def _pares(nodo):
    if isinstance(nodo, dict):
        for k, v in nodo.items():
            if isinstance(v, str):
                yield str(k), v
            yield from _pares(v)
    elif isinstance(nodo, list):
        for v in nodo:
            yield from _pares(v)


class ConfigConIdCanonico(unittest.TestCase):
    def test_hay_ficheros(self):
        self.assertGreater(len(list(_ficheros())), 50)

    def test_territory_id_igual_a_la_carpeta_y_sin_ids_viejos(self):
        viejos = {t.id_legacy for t in ti.tabla().values()}
        ruta_vieja = re.compile(r"territorios/(%s)/" % "|".join(map(re.escape, sorted(viejos, key=len, reverse=True))))
        malos = []
        for carpeta, f in _ficheros():
            rel = f.relative_to(ROOT).as_posix()
            try:
                texto = f.read_text(encoding="utf-8")
            except FileNotFoundError:  # temporal de otro test concurrente
                continue
            try:
                datos = yaml.safe_load(texto)
            except yaml.YAMLError:
                datos = None
            for k, v in _pares(datos):
                if k in CLAVES and v != carpeta and not v.startswith("congreso350_"):
                    malos.append(f"{rel}: {k}={v!r} (carpeta {carpeta})")
            if ruta_vieja.search(texto):
                malos.append(f"{rel}: ruta territorios/<id viejo>/")
        self.assertEqual(malos, [])


if __name__ == "__main__":
    unittest.main()
