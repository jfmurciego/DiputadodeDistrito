"""Versión 1.0.0; 2026-11-09; candidato. T-118: un M06 reutilizado no colisiona al registrar el M08 de un run «Reutilizar»."""
from __future__ import annotations

import hashlib
import unittest

from herramientas import registro_publicaciones_visor as reg

REPO = "jfmurciego/DiputadodeDistrito"


def entry(kind, ident, **extra):
    blob = hashlib.sha1(ident.encode()).hexdigest()
    base = {"id": ident, "asset_type": "territorial_product", "source_type": "repository_blob", "repository": REPO,
            "blob_sha": blob, "immutable_location": f"github-git-blob://{REPO}/{blob}", "territory_id": "x_territorio",
            "sha256": hashlib.sha256(ident.encode()).hexdigest(), "kind": kind, "run_id": 111,
            "expected_districts": 1, "label": ident}
    base.update(extra)
    return base


def registry(*products):
    return {"schema": reg.SCHEMA, "products": list(products), "ensembles": []}


class M06ReutilizadoTests(unittest.TestCase):
    def test_m06_reutilizado_bajo_otro_run_se_omite_y_m08_entra(self):
        base = registry(entry("canonical_m06", "m06-x-1", run_id=1))
        reutilizado = {**entry("canonical_m06", "m06-x-1", run_id=1), "id": "m06-x-2", "run_id": 2}
        m08 = entry("canonical_m08", "m08-x-2", run_id=2)
        cand = reg.make_candidate(base, [reutilizado, m08])
        ids = {p["id"] for p in cand["products"]}
        self.assertEqual(ids, {"m06-x-1", "m08-x-2"})

    def test_m08_con_bytes_de_m06_sigue_rechazado(self):
        base = registry(entry("canonical_m06", "m06-x-1", run_id=1))
        falso = {**entry("canonical_m06", "m06-x-1", run_id=1), "id": "m08-x-2", "kind": "canonical_m08", "run_id": 2}
        with self.assertRaises(ValueError):
            reg.make_candidate(base, [falso])

    def test_m06_nuevo_con_otros_bytes_se_registra(self):
        base = registry(entry("canonical_m06", "m06-x-1", run_id=1))
        nuevo = entry("canonical_m06", "m06-x-2", run_id=2)
        cand = reg.make_candidate(base, [nuevo])
        self.assertEqual(len(cand["products"]), 2)


if __name__ == "__main__":
    unittest.main()
