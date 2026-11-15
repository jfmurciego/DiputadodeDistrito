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
VIEJO = ti.id_legacy("aut02")  # derivado de la tabla maestra: sin literal de id viejo (test_t220)
CARPETA = re.compile(r"^(aut|nac)\d\d$")


def _ficheros(raiz=ROOT):
    base = raiz / "territorios"
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


def revisar(raiz=ROOT) -> list[str]:
    viejos = {t.id_legacy for t in ti.tabla().values()}
    ruta_vieja = re.compile(r"territorios/(%s)/" % "|".join(map(re.escape, sorted(viejos, key=len, reverse=True))))
    malos = []
    for carpeta, f in _ficheros(raiz):
        rel = f.relative_to(raiz).as_posix()
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
    return malos


class ConfigConIdCanonico(unittest.TestCase):
    def test_hay_ficheros(self):
        self.assertGreater(len(list(_ficheros())), 50)

    def test_repositorio_sin_ids_viejos(self):
        self.assertEqual(revisar(), [])

    def _arbol(self, td, contenido):
        cfg = Path(td) / "territorios" / "aut02" / "config" / "elecciones"
        cfg.mkdir(parents=True)
        (cfg / "c.json").write_text(contenido, encoding="utf-8")
        (Path(td) / "territorios" / "congreso350_alava" / "config").mkdir(parents=True)  # fuera de alcance

    def test_control_positivo_detecta_id_viejo_y_ruta_vieja(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            self._arbol(td, '{"territory_id": "%s", "path": "territorios/%s/config/x.json"}' % (VIEJO, VIEJO))
            malos = revisar(Path(td))
        self.assertEqual(len(malos), 2, malos)
        self.assertIn(f"territory_id={VIEJO!r}", malos[0])
        self.assertIn("ruta territorios/<id viejo>/", malos[1])

    def test_control_negativo_acepta_canonico_y_otra_carpeta_es_error(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            self._arbol(td, '{"territory_id": "aut02", "path": "territorios/aut02/config/x.json"}')
            self.assertEqual(revisar(Path(td)), [])
        with tempfile.TemporaryDirectory() as td:
            self._arbol(td, '{"territory_id": "aut12"}')
            self.assertEqual(len(revisar(Path(td))), 1)


if __name__ == "__main__":
    unittest.main()
