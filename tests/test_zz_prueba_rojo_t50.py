"""TEMPORAL (T-50): test roto a propósito para comprobar que `pruebas` se pone en rojo. Se revierte en el commit siguiente."""
import unittest


class PruebaRojo(unittest.TestCase):
    def test_roto_a_proposito(self):
        self.assertEqual(1, 2)
