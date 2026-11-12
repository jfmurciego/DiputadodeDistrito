"""T-259 / D-66: esquema y validación de la excepción de distritos mixtos por municipio (sin tocar el núcleo)."""
import unittest

from ddd_motor2.excepcion_d66 import PENDIENTE, leer, validar
from ddd_motor2.reglas import ErrorContrato


def entrada(**kw):
    e = {"municipio": "05019", "max_mixtos": 2, "motivo": "infactible por población",
         "prueba_infactibilidad": "docs/ESTUDIOS/x/prueba.json", "aprobacion": "D-66"}
    e.update(kw)
    return {k: v for k, v in e.items() if v is not None}


def cfg(lista):
    return {"validation": {"expected_districts": 3, "max_mixed_districts_exceptions": lista}}


class ExcepcionD66(unittest.TestCase):
    def test_sin_excepciones_es_valido(self):
        self.assertEqual(validar({"validation": {"expected_districts": 3}}), [])
        self.assertEqual(validar(cfg([])), [])
        self.assertEqual(validar({}), [])

    def test_una_y_dos_entradas_validas_se_leen_pero_validar_falla(self):
        uno = cfg([entrada(municipio=5019)])
        self.assertEqual(leer(uno)[0]["municipio"], "05019")
        dos = cfg([entrada(municipio="37274"), entrada()])
        self.assertEqual([x["municipio"] for x in leer(dos)], ["05019", "37274"])
        for c in (uno, dos):
            with self.assertRaises(ErrorContrato) as e:
                validar(c)
            self.assertIn(PENDIENTE, str(e.exception))

    def test_mas_de_dos_entradas(self):
        c = cfg([entrada(municipio=m) for m in ("05019", "37274", "40194")])
        with self.assertRaisesRegex(ErrorContrato, "como máximo 2"):
            leer(c)

    def test_motivo_vacio_o_ausente(self):
        for m in ("", "   ", None):
            with self.assertRaisesRegex(ErrorContrato, r"motivo falta o está vacío"):
                leer(cfg([entrada(motivo=m)]))

    def test_sin_aprobacion_o_mal_formada(self):
        with self.assertRaisesRegex(ErrorContrato, r"aprobacion falta"):
            leer(cfg([entrada(aprobacion=None)]))
        with self.assertRaisesRegex(ErrorContrato, r"id de una decisión"):
            leer(cfg([entrada(aprobacion="el propietario")]))

    def test_max_mixtos_distinto_de_2(self):
        for mx in (1, 3, "2", True, None):
            with self.assertRaisesRegex(ErrorContrato, r"max_mixtos debe ser 2"):
                leer(cfg([entrada(max_mixtos=mx)]))

    def test_sin_prueba_municipio_malo_repetido_o_claves_de_mas(self):
        with self.assertRaisesRegex(ErrorContrato, r"prueba_infactibilidad falta"):
            leer(cfg([entrada(prueba_infactibilidad=None)]))
        with self.assertRaisesRegex(ErrorContrato, r"código INE"):
            leer(cfg([entrada(municipio="Ávila")]))
        with self.assertRaisesRegex(ErrorContrato, r"repite"):
            leer(cfg([entrada(), entrada(municipio="5019")]))
        with self.assertRaisesRegex(ErrorContrato, r"desconocidas"):
            leer(cfg([dict(entrada(), extra=1)]))
        with self.assertRaisesRegex(ErrorContrato, r"debe ser una lista"):
            leer(cfg({"municipio": "05019"}))


if __name__ == "__main__":
    unittest.main()
