# VERSIÓN: 1.4.0
# CAMBIOS: 1.4.0: padrón por sha256 del EXTRACTO filtrado (D-119): extracto igual+crudo distinto sigue, extracto distinto para. 1.3.0: padrón 65034 descargado y comparado por sha256 (D-112). 1.2.0: id no canónico (T-336) → ACQUIRE; canónico → REUSE. 1.1.0: años pedidos ≠ contrato, Last-Modified solo avisa (cabeceras reales de 65034.csv), 200 sin cabeceras, BadZipFile. 1.0.0: fichero nuevo (T-323, D-112).
# ANTERIOR: ninguna (fichero nuevo; 1.0.0 solo existió en esta PR)
"""T-323: P10 usa el paquete de R2 y solo consulta el INE (HEAD): sin cambios usa R2, cambiado para y avisa, sin red degrada con aviso."""
import hashlib
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import yaml

from herramientas import p10_desde_r2 as p

ROOT = Path(__file__).resolve().parents[1]
# Valores independientes de la huella oficial medida el 2026-11-14 (ver orchestracion/fuentes_r2.json).
BYTES_2025 = 60298555
HEAD_IGUAL = {"content-length": str(BYTES_2025), "last-modified": "Tue, 04 Nov 2025 10:00:00 GMT"}
# Padrón sintético (formato del INE: ';', CRLF). El extracto esperado es un literal escrito a mano: BOM, delimitador original, "\n", solo Total/Todas las
# edades de 2025 de la provincia 50 (la de Huesca, el año 2024 y «Hombres» no entran).
CAB = "Total Nacional;Provincias;Municipios;Secciones;Sexo;Edad;Periodo;Total\r\n"
F1 = "Total Nacional;50 Zaragoza;50001 Abla;5000101001;Total;Todas las edades;2025;1.234\r\n"
F2 = "Total Nacional;50 Zaragoza;50001 Abla;5000101002;Total;Todas las edades;2025;800\r\n"
RUIDO = [
    "Total Nacional;50 Zaragoza;50001 Abla;5000101001;Total;Todas las edades;2024;1.100\r\n",
    "Total Nacional;50 Zaragoza;50001 Abla;5000101001;Hombres;Todas las edades;2025;600\r\n",
    "Total Nacional;22 Huesca;22001 Aban;2200101001;Total;Todas las edades;2025;300\r\n",
]
EXTRACTO = ("\ufeffTotal Nacional;Provincias;Municipios;Secciones;Sexo;Edad;Periodo;Total\n"
            "Total Nacional;50 Zaragoza;50001 Abla;5000101001;Total;Todas las edades;2025;1.234\n"
            "Total Nacional;50 Zaragoza;50001 Abla;5000101002;Total;Todas las edades;2025;800\n").encode("utf-8")
DECLARACION = {"territory": {"territorial_codes": [{"code": "50", "business_name": "Zaragoza"}]}}
PADRON_VIVO = [(CAB + F1 + RUIDO[0] + F2 + RUIDO[1] + RUIDO[2]).encode("utf-8")]
PADRON_SHA = hashlib.sha256(b"crudo de la copia").hexdigest()  # el crudo de la copia es otro: solo informa


def _indice(td: Path) -> Path:
    ruta = td / "indice.json"
    ruta.write_text(json.dumps({"fuentes": {
        "seccionado_2025.zip": {"origen_url": "https://www.ine.es/prodyser/cartografia/seccionado_2025.zip", "bytes": BYTES_2025, "descargado_en": "2026-11-14"},
        "65034.csv.zip": {"origen_url": "https://www.ine.es/jaxiT3/files/t/csv_bdsc/65034.csv", "bytes": 75489355, "descargado_en": "2026-02-16", "contenido_sha256": PADRON_SHA},
    }}), encoding="utf-8")
    return ruta


def _paquete_falso(t, work, territory_id=None, extracto=EXTRACTO):
    import zipfile
    d = Path(work) / "pkg"
    d.mkdir(parents=True)
    interior = io.BytesIO()
    with zipfile.ZipFile(interior, "w") as z:
        z.writestr("65034.csv", extracto)
    with zipfile.ZipFile(d / "prepared_sources.zip", "w") as z:
        z.writestr("materialized/inputs/65034.csv.zip", interior.getvalue())
    (d / "manifest.json").write_text(json.dumps({"path": "prepared_sources.zip", "territory_id": territory_id or "aut02"}), encoding="utf-8")
    return d


class P10DesdeR2(unittest.TestCase):
    def _preparar(self, head, restaurar=_paquete_falso, anios=lambda t: ("2025", "2025", "2025"), pedido=("2025", "2025", "2025"), descargar=lambda u: iter(PADRON_VIVO), declaracion=DECLARACION):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = p.preparar("aut02", *pedido, td / ".ddd-source-package", restaurar=restaurar, head=head, indice=_indice(td), anios=anios, descargar=descargar, declaracion=declaracion)
            return rc, out.getvalue() + err.getvalue(), (td / ".ddd-source-package" / "manifest.json").is_file()

    def test_ine_sin_cambios_usa_r2(self):
        rc, log, restaurado = self._preparar(lambda u: (200, HEAD_IGUAL))
        self.assertEqual(rc, 0)
        self.assertTrue(restaurado)
        self.assertNotIn("::error::", log)
        self.assertNotIn("SIN_COMPROBAR", log)  # una excepción tragada no debe dar un verde en falso

    def test_ine_cambiado_por_tamano_para_y_avisa(self):
        rc, log, restaurado = self._preparar(lambda u: (200, {**HEAD_IGUAL, "content-length": "60298999"}))
        self.assertEqual(rc, p.SALIDA_CAMBIADA)
        self.assertFalse(restaurado)
        self.assertIn("::error::FUENTE_INE_CAMBIADA seccionado_2025.zip", log)

    def test_last_modified_posterior_solo_avisa(self):
        rc, log, restaurado = self._preparar(lambda u: (200, {**HEAD_IGUAL, "last-modified": "Mon, 16 Nov 2026 08:00:00 GMT"}))
        self.assertEqual(rc, 0)
        self.assertTrue(restaurado)
        self.assertNotIn("::error::", log)

    def test_extracto_igual_sigue_aunque_el_crudo_difiera(self):
        pedidos = []
        rc, log, restaurado = self._preparar(lambda u: (200, HEAD_IGUAL), descargar=lambda u: (pedidos.append(u) or iter(PADRON_VIVO)))
        self.assertEqual(rc, 0)
        self.assertTrue(restaurado)
        self.assertEqual(pedidos, ["https://www.ine.es/jaxiT3/files/t/csv_bdsc/65034.csv"])
        self.assertIn("::notice::P10_PADRON_EXTRACTO_IGUAL 65034.csv.zip", log)
        self.assertIn("crudo cambió, extracto igual", log)
        self.assertNotIn("SIN_COMPROBAR", log)

    def test_extracto_distinto_para(self):
        vivo = (CAB + F1 + F2.replace("800", "801")).encode("utf-8")  # una sección cambia de población
        rc, log, restaurado = self._preparar(lambda u: (200, HEAD_IGUAL), descargar=lambda u: iter([vivo]))
        self.assertEqual(rc, p.SALIDA_CAMBIADA)
        self.assertFalse(restaurado)
        self.assertIn("::error::FUENTE_INE_CAMBIADA 65034.csv.zip (extracto filtrado", log)

    def test_extracto_igual_en_trozos_pequenos(self):
        crudo = PADRON_VIVO[0]
        trozos = [crudo[i:i + 7] for i in range(0, len(crudo), 7)]  # cortes en mitad de línea y de carácter
        rc, log, restaurado = self._preparar(lambda u: (200, HEAD_IGUAL), descargar=lambda u: iter(trozos))
        self.assertEqual(rc, 0)
        self.assertTrue(restaurado)

    def test_extracto_en_streaming_devuelve_el_literal(self):
        r = p.extracto_en_streaming(iter(PADRON_VIVO), DECLARACION, 2025, ["50"])
        self.assertEqual(r["extracto"], EXTRACTO)
        self.assertEqual(r["crudo_bytes"], len(PADRON_VIVO[0]))

    def test_paquete_con_tabulador_no_da_falso_cambio(self):
        # La copia de R2 del padrón va con tabulador y el INE con ';': mismo contenido, mismo veredicto.
        tab = EXTRACTO.decode("utf-8").lstrip("\ufeff").replace(";", "\t").encode("utf-8")
        rc, log, restaurado = self._preparar(lambda u: (200, HEAD_IGUAL), restaurar=lambda t, w: _paquete_falso(t, w, extracto=tab))
        self.assertEqual(rc, 0)
        self.assertTrue(restaurado)
        self.assertIn("P10_PADRON_EXTRACTO_IGUAL", log)

    def test_tabulador_con_un_valor_distinto_sigue_dando_54(self):
        # Control negativo de la forma canónica: tabulador + 800→801 frente al vivo con ';' no se enmascara.
        tab = EXTRACTO.decode("utf-8").lstrip("\ufeff").replace(";", "\t").replace("800", "801").encode("utf-8")
        rc, log, restaurado = self._preparar(lambda u: (200, HEAD_IGUAL), restaurar=lambda t, w: _paquete_falso(t, w, extracto=tab))
        self.assertEqual(rc, p.SALIDA_CAMBIADA)
        self.assertFalse(restaurado)

    def test_referencia_ilegible_degrada_con_aviso(self):
        for malo in (b"\xff\xfe\x00 no es utf8", b"una sola columna sin delimitador\notra"):
            rc, log, restaurado = self._preparar(lambda u: (200, HEAD_IGUAL), restaurar=lambda t, w, m=malo: _paquete_falso(t, w, extracto=m))
            self.assertEqual(rc, 0, log)
            self.assertTrue(restaurado)
            self.assertIn("::warning::P10_INE_SIN_COMPROBAR 65034.csv.zip: el extracto de referencia del paquete de R2 no es un CSV legible", log)
            self.assertNotIn("Traceback", log)

    def test_canonico_directo(self):
        c = p.canonico
        base = c(b"a;b\n1;2\n")
        self.assertEqual(base, b"a\tb\n1\t2\n")
        self.assertNotEqual(base, c(b"a;b\n1;3\n"))  # un valor distinto cambia el resultado
        self.assertEqual(c(b"a\tb\n1\t2\n"), base)  # tabulador y ';' equivalen
        self.assertEqual(c(b'a;b\n"1";2\n'), base)  # comillas innecesarias no cambian
        self.assertEqual(c(b"\xef\xbb\xbfa;b\r\n1;2\r\n"), base)  # BOM y CRLF no cambian
        con_tab = c(b'a;b\n"x\ty";2\n')  # campo con tabulador entrecomillado: se conserva y no se parte
        self.assertEqual(con_tab, b'a\tb\n"x\ty"\t2\n')
        self.assertEqual(c(b'a\tb\n"x\ty"\t2\n'), con_tab)
        self.assertEqual(c(b""), b"")

    def test_extracto_vacio_en_el_paquete_para(self):
        # Un extracto de referencia vacío frente a un padrón vivo con filas es evidencia positiva de cambio.
        rc, log, restaurado = self._preparar(lambda u: (200, HEAD_IGUAL), restaurar=lambda t, w: _paquete_falso(t, w, extracto=b""))
        self.assertEqual(rc, p.SALIDA_CAMBIADA)
        self.assertFalse(restaurado)

    def test_sin_declaracion_solo_avisa(self):
        rc, log, restaurado = self._preparar(lambda u: (200, HEAD_IGUAL), declaracion=None)
        self.assertEqual(rc, 0)
        self.assertTrue(restaurado)
        self.assertIn("sin extracto de referencia", log)

    def test_padron_sin_red_degrada_con_aviso(self):
        def sin_red(u):
            raise OSError("red caída")
            yield b""
        rc, log, restaurado = self._preparar(lambda u: (200, HEAD_IGUAL), descargar=sin_red)
        self.assertEqual(rc, 0)
        self.assertTrue(restaurado)
        self.assertIn("::warning::P10_INE_SIN_COMPROBAR 65034.csv.zip: no se pudo leer el padrón", log)

    def test_padron_cortado_a_medias_degrada_con_aviso(self):
        def corta(u):
            yield PADRON_VIVO[0][:50]
            raise ConnectionResetError("reset")
        rc, log, _ = self._preparar(lambda u: (200, HEAD_IGUAL), descargar=corta)
        self.assertEqual(rc, 0)
        self.assertIn("no se pudo leer el padrón", log)

    def test_200_sin_cabeceras_solo_avisa(self):
        rc, log, restaurado = self._preparar(lambda u: (200, {}))
        self.assertEqual(rc, 0)
        self.assertTrue(restaurado)
        self.assertIn("no devolvió Content-Length ni Last-Modified", log)

    def test_anios_pedidos_distintos_del_contrato_no_usan_r2(self):
        def no_restaurar(t, w):
            raise AssertionError("no debe restaurar un paquete de otro año")
        rc, log, restaurado = self._preparar(lambda u: (200, HEAD_IGUAL), restaurar=no_restaurar, pedido=("2025", "2026", "2026"))
        self.assertEqual(rc, 0)
        self.assertFalse(restaurado)
        self.assertIn("P10_R2_ANIOS_DISTINTOS", log)

    def test_id_no_canonico_no_se_reutiliza(self):
        # T-336: el paquete de R2 lleva un id distinto del canónico → ACQUIRE, sin consultar al INE.
        def no_hay_red(u):
            raise AssertionError("no se consulta al INE si el paquete no es reutilizable")
        rc, log, restaurado = self._preparar(no_hay_red, restaurar=lambda t, w: _paquete_falso(t, w, "zz99"))
        self.assertEqual(rc, 0)
        self.assertFalse(restaurado)
        self.assertIn("P10_R2_ID_NO_CANONICO", log)

    def test_id_canonico_sigue_en_reuse(self):
        rc, log, restaurado = self._preparar(lambda u: (200, HEAD_IGUAL), restaurar=lambda t, w: _paquete_falso(t, w, "aut02"))
        self.assertEqual(rc, 0)
        self.assertTrue(restaurado)
        self.assertNotIn("P10_R2_ID_NO_CANONICO", log)

    def test_zip_corrupto_sale_53(self):
        import zipfile

        def mal_zip(t, w):
            raise zipfile.BadZipFile("File is not a zip file")
        rc, log, _ = self._preparar(lambda u: (200, HEAD_IGUAL), restaurar=mal_zip)
        self.assertEqual(rc, p.SALIDA_CORRUPTO)

    def test_sin_red_o_503_o_403_degrada_con_aviso(self):
        def sin_red(u):
            raise OSError("red caída")
        for head in (sin_red, lambda u: (503, {}), lambda u: (403, {})):
            rc, log, restaurado = self._preparar(head)
            self.assertEqual(rc, 0)
            self.assertTrue(restaurado)
            self.assertIn("::warning::P10_INE_SIN_COMPROBAR", log)
            self.assertNotIn("::error::", log)

    def test_sin_paquete_en_r2_adquiere_como_antes(self):
        def no_hay_red(u):
            raise AssertionError("sin paquete no se consulta al INE")
        rc, log, restaurado = self._preparar(no_hay_red, restaurar=lambda t, w: None)
        self.assertEqual(rc, 0)
        self.assertFalse(restaurado)
        self.assertIn("P10_SIN_PAQUETE_R2", log)

    def test_paquete_corrupto_bloquea(self):
        from herramientas.bateria_motor import PaqueteP10Corrupto

        def corrupto(t, w):
            raise PaqueteP10Corrupto("sha256 distinto")
        rc, log, _ = self._preparar(lambda u: (200, HEAD_IGUAL), restaurar=corrupto)
        self.assertEqual(rc, p.SALIDA_CORRUPTO)
        self.assertIn("P10_PAQUETE_R2_CORRUPTO", log)

    def test_el_seccionado_solo_va_por_head(self):
        visto = []
        self._preparar(lambda u: (visto.append(u) or (200, HEAD_IGUAL)))
        self.assertEqual(visto, ["https://www.ine.es/prodyser/cartografia/seccionado_2025.zip"])

    def test_indice_real_cubre_las_fuentes_ine(self):
        nombres, faltan = p.fuentes_necesarias("2025", "2025")
        self.assertEqual((nombres, faltan), (["seccionado_2025.zip", "65034.csv.zip"], []))
        real = json.loads((ROOT / "orchestracion/fuentes_r2.json").read_text(encoding="utf-8"))["fuentes"]
        # Valor independiente: sha256 del miembro 65034.csv de la copia (zip 91d3ff9a…), medido el 2026-11-15.
        self.assertEqual(real["65034.csv.zip"]["contenido_sha256"], "1938833dea5c4ac1e722e0038c1ed2295c1efa446b930a560e4afd6eb8c18c2a")

    def test_workflow_cableado(self):
        s = (ROOT / ".github/workflows/_p11-territoriales.yml").read_text(encoding="utf-8")
        wf = yaml.safe_load(s)
        pasos = wf["jobs"]["territoriales"]["steps"]
        ids = [x.get("id") for x in pasos]
        self.assertLess(ids.index("previous"), ids.index("r2"))
        self.assertLess(ids.index("r2"), ids.index("acquire"))
        self.assertIn("p10_desde_r2.py preparar", pasos[ids.index("r2")]["run"])
        previo = pasos[ids.index("r2") - 1]
        self.assertIn("requirements.lock", previo["run"])
        self.assertIn("steps.r2.outputs.desde_r2 != 'true'", pasos[ids.index("acquire")]["if"])

    def test_todos_los_pasos_de_adquisicion_llevan_ambas_condiciones(self):
        # Los pasos de adquisición (buildx, build, mode, reconstruir, acquire, resumen) deben saltarse igual con reused_candidate y con desde_r2.
        pasos = yaml.safe_load((ROOT / ".github/workflows/_p11-territoriales.yml").read_text(encoding="utf-8"))["jobs"]["territoriales"]["steps"]
        ids = [x.get("id") for x in pasos]
        i_r2 = ids.index("r2")
        despues = [x for x in pasos[i_r2 + 1:] if "steps.previous.outputs.reused_candidate != 'true'" in str(x.get("if"))]
        self.assertGreaterEqual(len(despues), 6)
        for x in despues:
            self.assertIn("steps.r2.outputs.desde_r2 != 'true'", x["if"], x.get("name") or x.get("uses") or x.get("run"))
        usos = " ".join(str(x.get("uses")) for x in despues)
        self.assertIn("docker/setup-buildx-action", usos)
        self.assertIn("docker/build-push-action", usos)
        self.assertEqual({x.get("id") for x in despues} & {"mode", "acquire"}, {"mode", "acquire"})
        self.assertTrue(any("reconstruir_fuentes.sh" in str(x.get("run")) for x in despues))


class ContrastarExtracto(unittest.TestCase):
    def _run(self, extracto, padron=PADRON_VIVO[0]):
        from herramientas import contrastar_extracto_p10 as c
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            d = _paquete_falso(None, td, extracto=extracto)
            (td / "padron.csv").write_bytes(padron)
            (td / "decl.yaml").write_text(yaml.safe_dump(DECLARACION), encoding="utf-8")
            out = io.StringIO()
            with redirect_stdout(out):
                rc = c.main(["--paquete-dir", str(d), "--padron", str(td / "padron.csv"), "--declaracion", str(td / "decl.yaml"), "--edicion", "2025", "--provincias", "50"])
            return rc, out.getvalue()

    def test_igual_con_tabulador_en_el_paquete(self):
        tab = EXTRACTO.decode("utf-8").lstrip("\ufeff").replace(";", "\t").encode("utf-8")
        rc, out = self._run(tab)
        self.assertEqual(rc, 0)
        self.assertIn("IGUAL", out)

    def test_distinto_sale_1(self):
        rc, out = self._run(EXTRACTO.replace(b"800", b"801"))
        self.assertEqual(rc, 1)
        self.assertIn("DISTINTO", out)

    def test_extracto_vacio_sale_2_con_mensaje(self):
        rc, out = self._run(b"")
        self.assertEqual(rc, 2)
        self.assertIn("Extracto vacío", out)


if __name__ == "__main__":
    unittest.main()
