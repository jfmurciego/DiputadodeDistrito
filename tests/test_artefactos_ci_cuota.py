"""
PROYECTO: Diputado de Distrito
PRUEBA: artefactos de diagnóstico de CI desacoplados de la cuota de almacenamiento
VERSIÓN: 1.0.0
FECHA: 2026-11-14
CAMBIO: T-271. Todo upload-artifact de los workflows de pruebas sube solo si el job falla, con
continue-on-error y retention-days <= 1, para que el veredicto dependa de los tests y no de la cuota
(«Artifact storage quota has been hit», main 439af6a). Los workflows de producción conservan sus
subidas en éxito.
ANTERIOR: ninguna.
"""
from pathlib import Path
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github/workflows"

# Workflows de pruebas: sus artefactos son solo diagnóstico.
PRUEBAS = {"pruebas-plataforma.yml"}

# Workflows de producción que necesitan sus artefactos (entre jobs, R2, publicación): no se tocan.
PRODUCCION = {
    "_reutilizable-generacion-territorial.yml",
    "_reutilizable-incorporacion-electoral.yml",
    "_reutilizable-publicar-sitio.yml",
    "_reutilizable-puerta-validacion.yml",
    "bateria-motor.yml",
    "ejecucion-completa-proyecto.yml",
    "generar-alternativas-territoriales.yml",
    "gestor-campanas.yml",
    "podar-r2.yml",
    "preparacion-fuentes.yml",
    "preparacion-legislatura-vigente.yml",
    "preparacion-resultados-electorales.yml",
    "produccion-distritos.yml",
}


def _pasos_subida(path):
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    for nombre_job, job in (data.get("jobs") or {}).items():
        for paso in job.get("steps") or []:
            if str(paso.get("uses", "")).startswith("actions/upload-artifact@"):
                yield nombre_job, paso


class ArtefactosDiagnosticoCi(unittest.TestCase):
    def test_clasificacion_completa_de_workflows_con_subidas(self):
        con_subidas = {
            p.name for p in WORKFLOWS.glob("*.yml") if any(True for _ in _pasos_subida(p))
        }
        sin_clasificar = con_subidas - PRUEBAS - PRODUCCION
        self.assertEqual(set(), sin_clasificar, "clasifica el workflow nuevo como pruebas o producción")

    def test_subidas_de_pruebas_solo_en_fallo_y_tolerantes(self):
        total = 0
        for nombre in sorted(PRUEBAS):
            for job, paso in _pasos_subida(WORKFLOWS / nombre):
                total += 1
                etiqueta = f"{nombre}:{job}:{paso.get('name', paso['uses'])}"
                cond = str(paso.get("if", ""))
                self.assertIn("failure()", cond, etiqueta)
                self.assertNotIn("always()", cond, etiqueta)
                self.assertIs(paso.get("continue-on-error"), True, etiqueta)
                retencion = (paso.get("with") or {}).get("retention-days")
                self.assertIsNotNone(retencion, etiqueta)
                self.assertLessEqual(int(retencion), 1, etiqueta)
        self.assertEqual(5, total)

    def test_pruebas_no_comparten_artefactos_entre_jobs(self):
        for nombre in PRUEBAS:
            texto = (WORKFLOWS / nombre).read_text(encoding="utf-8")
            self.assertNotIn("actions/download-artifact@", texto, nombre)

    def test_produccion_conserva_subidas_en_exito(self):
        for nombre in sorted(PRODUCCION):
            path = WORKFLOWS / nombre
            self.assertTrue(path.exists(), nombre)
            pasos = list(_pasos_subida(path))
            self.assertTrue(pasos, nombre)
            en_exito = [p for _, p in pasos if "failure()" not in str(p.get("if", ""))]
            self.assertTrue(en_exito, f"{nombre} perdió sus subidas en éxito")


if __name__ == "__main__":
    unittest.main()
