from __future__ import annotations

import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
SELECTOR = "herramientas.seleccionar_paquete_fuentes"


class GeospatialPackageValidationEnvironmentTests(unittest.TestCase):
    def test_all_active_package_selectors_have_geospatial_runtime(self):
        found: list[tuple[str, str, str]] = []

        for path in sorted(WORKFLOWS.glob("*.yml")):
            workflow = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            for job_name, job in (workflow.get("jobs") or {}).items():
                if not isinstance(job, dict):
                    continue
                steps = job.get("steps") or []
                if not isinstance(steps, list):
                    continue
                for index, step in enumerate(steps):
                    if not isinstance(step, dict):
                        continue
                    run = str(step.get("run") or "")
                    if SELECTOR not in run:
                        continue

                    step_name = str(step.get("name") or step.get("id") or index)
                    found.append((path.name, str(job_name), step_name))

                    containerized = all(
                        marker in run
                        for marker in (
                            "docker run",
                            "ddd-production:${GITHUB_SHA}",
                            "--entrypoint python",
                        )
                    )
                    if containerized:
                        continue

                    previous_runs = "\n".join(
                        str(previous.get("run") or "")
                        for previous in steps[:index]
                        if isinstance(previous, dict)
                    )
                    with self.subTest(
                        workflow=path.name,
                        job=job_name,
                        step=step_name,
                    ):
                        self.assertIn(
                            "-r requirements.lock",
                            previous_runs,
                            "selector host-side sin requirements.lock fijado",
                        )
                        self.assertIn(
                            "import geopandas",
                            previous_runs,
                            "selector host-side sin verificación geoespacial",
                        )

        workflows = {workflow for workflow, _job, _step in found}
        self.assertTrue(
            {
                "preparacion-fuentes.yml",
                "produccion-distritos.yml",
                "_reutilizable-generacion-territorial.yml",
                "producir-territorio-por-contrato.yml",
            }.issubset(workflows),
            found,
        )

    def test_generation_reusables_validate_recovered_package_in_container(self):
        for name in (
            "_reutilizable-generacion-territorial.yml",
            "producir-territorio-por-contrato.yml",
        ):
            with self.subTest(workflow=name):
                text = (WORKFLOWS / name).read_text(encoding="utf-8")
                recover = text.index("name: Recuperar datos territoriales preparados")
                tail = text[recover:]
                selector = tail.index(SELECTOR)
                prefix = tail[:selector]
                self.assertIn("docker run", prefix)
                self.assertIn("ddd-production:${GITHUB_SHA}", prefix)
                self.assertIn("--entrypoint python", prefix)
                self.assertNotIn(
                    "\n          python -m herramientas.seleccionar_paquete_fuentes",
                    tail[: selector + len(SELECTOR)],
                )

    def test_common_gate_has_pinned_runtime_for_transitive_territorial_validation(self):
        workflow_path = WORKFLOWS / "_reutilizable-puerta-validacion.yml"
        workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
        steps = workflow["jobs"]["validar"]["steps"]

        install_index = next(
            index
            for index, step in enumerate(steps)
            if step.get("name") == "Instalar runtime fijado de validación"
        )
        verify_index = next(
            index
            for index, step in enumerate(steps)
            if step.get("name") == "Verificar runtime geoespacial de la puerta"
        )
        gate_index = next(
            index
            for index, step in enumerate(steps)
            if step.get("id") == "gate"
        )

        self.assertLess(install_index, verify_index)
        self.assertLess(verify_index, gate_index)
        self.assertIn("-r requirements.lock", steps[install_index]["run"])
        for module in ("geopandas", "pandas", "shapely", "pyproj", "pyogrio", "yaml"):
            self.assertIn(module, steps[verify_index]["run"])

        validator = (
            ROOT / "herramientas" / "validar_puerta_ejecucion.py"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "from herramientas.seleccionar_paquete_fuentes import validate_prepared_package",
            validator,
        )
        self.assertIn(
            "validate_prepared_package(",
            validator,
            "la regresión debe seguir cubriendo la dependencia transitiva geoespacial",
        )

    def test_no_active_gate_validator_runs_with_yaml_only_runtime(self):
        gate = (WORKFLOWS / "_reutilizable-puerta-validacion.yml").read_text(
            encoding="utf-8"
        )
        self.assertNotIn(
            "python -m pip install --disable-pip-version-check PyYAML==6.0.2",
            gate,
        )
        self.assertIn("-r requirements.lock", gate)
        self.assertIn("import geopandas", gate)

    def test_all_active_pair_consumers_have_geospatial_runtime(self):
        consumer = "herramientas.consumir_par_fuentes_legislatura"
        found: list[tuple[str, str, str]] = []

        for path in sorted(WORKFLOWS.glob("*.yml")):
            workflow = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            for job_name, job in (workflow.get("jobs") or {}).items():
                if not isinstance(job, dict):
                    continue
                steps = job.get("steps") or []
                if not isinstance(steps, list):
                    continue
                for index, step in enumerate(steps):
                    if not isinstance(step, dict):
                        continue
                    run = str(step.get("run") or "")
                    if consumer not in run:
                        continue
                    step_name = str(step.get("name") or step.get("id") or index)
                    found.append((path.name, str(job_name), step_name))
                    previous_runs = "\n".join(
                        str(previous.get("run") or "")
                        for previous in steps[:index]
                        if isinstance(previous, dict)
                    )
                    with self.subTest(
                        workflow=path.name,
                        job=job_name,
                        step=step_name,
                    ):
                        self.assertIn(
                            "-r requirements.lock",
                            previous_runs,
                            "consumidor de par sin requirements.lock fijado",
                        )
                        self.assertIn(
                            "import geopandas",
                            previous_runs,
                            "consumidor de par sin verificación geoespacial",
                        )

        self.assertTrue(found, "no se localizaron consumidores activos de pares")
        self.assertTrue(
            all(workflow == "ejecucion-completa-proyecto.yml" for workflow, _job, _step in found),
            found,
        )

    def test_02_uses_pinned_geospatial_environment_before_package_selection(self):
        workflow = yaml.safe_load(
            (WORKFLOWS / "produccion-distritos.yml").read_text(encoding="utf-8")
        )
        steps = workflow["jobs"]["resolver_interfaz"]["steps"]
        install_index = next(
            index
            for index, step in enumerate(steps)
            if step.get("name") == "Instalar entorno geoespacial para selección de fuentes"
        )
        verify_index = next(
            index
            for index, step in enumerate(steps)
            if step.get("name") == "Verificar entorno geoespacial para selección de fuentes"
        )
        selector_index = next(
            index
            for index, step in enumerate(steps)
            if SELECTOR in str(step.get("run") or "")
        )
        self.assertLess(install_index, verify_index)
        self.assertLess(verify_index, selector_index)
        self.assertIn("-r requirements.lock", steps[install_index]["run"])
        self.assertIn("import geopandas", steps[verify_index]["run"])


if __name__ == "__main__":
    unittest.main()
