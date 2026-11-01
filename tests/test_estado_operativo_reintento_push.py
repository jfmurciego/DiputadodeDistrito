# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: test T-11 (b) del reintento del estado operativo compartido
VERSIÓN: 1.0.0
FECHA: 2026-11-01
FUNCIÓN: el push del estado compartido reintenta 10 veces con espera exponencial y jitter
(las 05 de La Rioja, Lugo, Santa Cruz de Tenerife y Tarragona agotaron 4 intentos de <1 s).
"""
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from herramientas import persistir_estado_operativo_compartido as p  # noqa: E402


class ReintentoEstadoCompartido(unittest.TestCase):
    def test_espera_exponencial_acotada(self):
        with mock.patch.object(p.random, "uniform", return_value=1.0):
            self.assertEqual([p.shared_state_backoff(a) for a in (1, 2, 3, 4, 5, 6)], [2.0, 4.0, 8.0, 16.0, 30.0, 30.0])
        with mock.patch.object(p.random, "uniform", return_value=0.5):
            self.assertEqual(p.shared_state_backoff(1), 1.0)

    def test_persist_shared_state_usa_reintento_largo(self):
        with mock.patch.object(p, "persist_rederived_tree") as tree:
            tree.return_value = p.PersistenceResult(head_sha="a" * 40, attempt=1, changed=True)
            self.assertEqual(p.persist_shared_state(root_dir=ROOT, edition="2025"), "a" * 40)
        kwargs = tree.call_args.kwargs
        self.assertEqual(kwargs["max_attempts"], 10)
        self.assertIs(kwargs["backoff"], p.shared_state_backoff)

    def test_otros_persistidores_conservan_su_espera(self):
        import inspect
        self.assertIsNone(inspect.signature(p.persist_rederived_tree).parameters["backoff"].default)


if __name__ == "__main__":
    unittest.main()
