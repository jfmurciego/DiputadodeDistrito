# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: test T-360 del registro concurrente de las cadenas en main
VERSIÓN: 1.0.0
FECHA: 2026-11-16
ANTERIOR: ninguna (fichero nuevo)
FUNCIÓN: 14 cadenas (14 clones de un remoto bare en tmp, en hilos) registran a la vez con
herramientas/registrar_en_main.py: entrada propia en un JSON compartido (delta), fichero propio del run y una
promoción re-derivada (--aplicar) sobre un YAML compartido. Ningún push queda rechazado de forma definitiva y no se
pierde ninguna entrada. Control negativo: con un solo intento (sin reintento) y todos los pushes a la vez, al menos
una cadena acaba en PUSH_RECHAZADO_TRAS_1. También: los grupos únicos ya no están en los jobs de registro y el
catálogo de procedencia viaja en el mismo commit que el registro.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from herramientas import registrar_en_main as rm  # noqa: E402

CADENAS = 14
WF = ROOT / ".github/workflows"


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, text=True, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE).stdout.strip()


def _repo(td: Path, catalogo: bool = False) -> Path:
    remoto = td / "remoto.git"
    git(td, "init", "--quiet", "--bare", "-b", "main", str(remoto))
    semilla = td / "semilla"
    git(td, "clone", "--quiet", str(remoto), str(semilla))
    git(semilla, "config", "user.name", "t"); git(semilla, "config", "user.email", "t@t")
    (semilla / "orchestracion").mkdir()
    _r2(semilla, {"schema": "x", "artefactos": {"base/1": {"sha256": "0" * 64}}})
    (semilla / "configuracion").mkdir()
    (semilla / "configuracion/catalogo.yaml").write_text("territorios: {}\n", encoding="utf-8")
    if catalogo:  # catálogo real, regenerado con la herramienta sobre la semilla
        from herramientas import catalogo_procedencia as cp
        (semilla / rm.CATALOGO_PROCEDENCIA).write_text(cp.serializar(cp.generar(semilla)), encoding="utf-8")
    git(semilla, "add", "-A"); git(semilla, "commit", "--quiet", "-m", "base")
    git(semilla, "push", "--quiet", "origin", "HEAD:main")
    return remoto


def _r2(raiz: Path, doc: dict) -> None:
    """Mismo formato que el archivista real (indent=2, sort_keys=True)."""
    (raiz / "orchestracion/archivo_r2.json").write_text(
        json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _clon(td: Path, remoto: Path, i: int) -> Path:
    c = td / f"cadena{i:02d}"
    git(td, "clone", "--quiet", "--depth", "1", "-b", "main", str(remoto), str(c))
    return c


def _promover(i: int):
    """La promoción sobre un YAML compartido: se re-deriva desde el HEAD vigente (como promover_catalogo_operacional)."""
    def aplicar(root: Path) -> None:
        p = root / "configuracion/catalogo.yaml"
        doc = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        doc.setdefault("territorios", {})[f"aut{i + 1:02d}"] = {"run_id": 1000 + i}
        p.write_text(yaml.safe_dump(doc, sort_keys=True), encoding="utf-8")
    return aplicar


def _cadenas(td: Path, remoto: Path, max_intentos: int, catalogo: bool = True):
    clones = [_clon(td, remoto, i) for i in range(CADENAS)]
    for i, c in enumerate(clones):  # el paso del job deja su cambio en el árbol (como archivo_origen.py)
        p = c / "orchestracion/archivo_r2.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
        doc["artefactos"][f"aut{i + 1:02d}/{1000 + i}"] = {"sha256": f"{i:064x}"}
        doc["actualizado_en"] = f"t{i}"
        _r2(c, doc)
        (c / "datos/runs").mkdir(parents=True)
        (c / f"datos/runs/aut{i + 1:02d}_{1000 + i}.csv").write_text(f"seccion,distrito\n{i},1\n", encoding="utf-8")
    barrera = threading.Barrier(CADENAS)
    resultados: dict[int, object] = {}

    def antes_de_push(intento: int) -> None:
        if intento == 1:  # todas han derivado desde el mismo HEAD antes del primer push: colisión segura
            barrera.wait(timeout=60)

    def correr(i: int) -> None:
        try:
            resultados[i] = rm.registrar(
                root_dir=clones[i], rama="main", mensaje=f"chore: registrar aut{i:02d}",
                rutas=["orchestracion/archivo_r2.json", "datos/runs", "configuracion/catalogo.yaml"],
                aplicar=_promover(i), max_intentos=max_intentos, backoff=lambda n: rm.espera(n) / 20,  # misma forma, escala 1/20
                antes_de_push=antes_de_push, catalogo=catalogo)
        except Exception as exc:  # noqa: BLE001
            resultados[i] = exc

    hilos = [threading.Thread(target=correr, args=(i,)) for i in range(CADENAS)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join(timeout=300)
    return resultados


def _estado_final(td: Path, remoto: Path) -> Path:
    final = td / "final"
    git(td, "clone", "--quiet", "-b", "main", str(remoto), str(final))
    return final


class RegistroConcurrente(unittest.TestCase):
    def setUp(self):
        self.td = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.td, ignore_errors=True)

    def test_14_cadenas_sin_push_rechazado_ni_perdida(self):
        remoto = _repo(self.td, catalogo=True)
        res = _cadenas(self.td, remoto, max_intentos=rm.MAX_INTENTOS)
        fallos = {i: r for i, r in res.items() if isinstance(r, Exception)}
        self.assertEqual(fallos, {})
        self.assertEqual(len(res), CADENAS)
        self.assertTrue(all(r.estado == "REGISTRADO" for r in res.values()))
        self.assertTrue(any(r.intento > 1 for r in res.values()), "sin colisión el test sería vacuo")
        final = _estado_final(self.td, remoto)
        r2 = json.loads((final / "orchestracion/archivo_r2.json").read_text(encoding="utf-8"))
        esperado = {"base/1"} | {f"aut{i + 1:02d}/{1000 + i}" for i in range(CADENAS)}
        self.assertEqual(set(r2["artefactos"]), esperado)
        self.assertEqual(r2["schema"], "x")
        cat = yaml.safe_load((final / "configuracion/catalogo.yaml").read_text(encoding="utf-8"))
        self.assertEqual(cat["territorios"], {f"aut{i + 1:02d}": {"run_id": 1000 + i} for i in range(CADENAS)})
        self.assertEqual(len(list((final / "datos/runs").glob("*.csv"))), CADENAS)
        self.assertEqual(int(git(final, "rev-list", "--count", "HEAD")), CADENAS + 1)
        texto = (final / "orchestracion/archivo_r2.json").read_text(encoding="utf-8")  # formato del archivista intacto
        self.assertEqual(texto, json.dumps(r2, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
        from herramientas import catalogo_procedencia as cp  # el versionado no va por detrás del registro
        self.assertEqual((final / rm.CATALOGO_PROCEDENCIA).read_text(encoding="utf-8"), cp.serializar(cp.generar(final)))

    def test_control_negativo_sin_reintento_hay_push_rechazado(self):
        remoto = _repo(self.td)
        res = _cadenas(self.td, remoto, max_intentos=1)
        rechazados = [r for r in res.values() if isinstance(r, rm.PushRechazado)]
        self.assertGreaterEqual(len(rechazados), 1)
        self.assertTrue(all(str(r).startswith("PUSH_RECHAZADO_TRAS_1:") for r in rechazados))
        final = _estado_final(self.td, remoto)
        r2 = json.loads((final / "orchestracion/archivo_r2.json").read_text(encoding="utf-8"))
        self.assertLess(len(r2["artefactos"]), CADENAS + 1)

    def test_no_op_si_ya_esta_registrado(self):
        remoto = _repo(self.td)
        c = _clon(self.td, remoto, 0)
        r = rm.registrar(root_dir=c, rama="main", mensaje="x", rutas=["orchestracion/archivo_r2.json"], backoff=None)
        self.assertEqual(r.estado, "NO_OP")

    def test_catalogo_de_procedencia_en_el_mismo_commit(self):
        remoto = _repo(self.td, catalogo=True)
        c = _clon(self.td, remoto, 0)
        # catálogo por detrás de los registros (lo que dejaba el robot aparte): el registro lo repone en su commit
        (c / "configuracion/catalogo.yaml").write_text("territorios: {aut01: {run_id: 1}}\n", encoding="utf-8")
        (c / rm.CATALOGO_PROCEDENCIA).write_text("{}\n", encoding="utf-8")
        git(c, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-am", "registro ajeno sin catálogo")
        git(c, "push", "-q", "origin", "HEAD:main")
        (c / "datos/runs").mkdir(parents=True)
        (c / "datos/runs/a.csv").write_text("x\n", encoding="utf-8")
        r = rm.registrar(root_dir=c, rama="main", mensaje="x", rutas=["datos/runs"], backoff=None)
        self.assertEqual(r.estado, "REGISTRADO")
        final = _estado_final(self.td, remoto)
        cambiados = set(git(final, "show", "--name-only", "--format=", "HEAD").splitlines())
        self.assertEqual(cambiados, {"datos/runs/a.csv", rm.CATALOGO_PROCEDENCIA})
        from herramientas import catalogo_procedencia as cp
        self.assertEqual((final / rm.CATALOGO_PROCEDENCIA).read_text(encoding="utf-8"), cp.serializar(cp.generar(final)))

    def _dos(self, cambiar):
        remoto = _repo(self.td)
        a, b = _clon(self.td, remoto, 0), _clon(self.td, remoto, 1)
        for c, v in ((a, "A"), (b, "B")):
            doc = json.loads((c / "orchestracion/archivo_r2.json").read_text(encoding="utf-8"))
            cambiar(doc, v)
            _r2(c, doc)
        for c in (a, b):  # b derivó del mismo HEAD que a: su primer push se rechaza y re-aplica su delta
            rm.registrar(root_dir=c, rama="main", mensaje="x", rutas=["orchestracion/archivo_r2.json"],
                         backoff=None, catalogo=False)
        return json.loads((_estado_final(self.td, remoto) / "orchestracion/archivo_r2.json").read_text(encoding="utf-8"))

    def test_misma_clave_gana_el_ultimo_en_registrar(self):
        r2 = self._dos(lambda d, v: d["artefactos"].__setitem__("aut01/1", {"sha256": v}))
        self.assertEqual(r2["artefactos"]["aut01/1"], {"sha256": "B"})
        self.assertIn("base/1", r2["artefactos"])

    def test_borrado_de_clave_se_reaplica_sin_tocar_lo_ajeno(self):
        def cambiar(d, v):
            if v == "A":
                d["artefactos"]["aut02/2"] = {"sha256": "A"}
            else:
                d["artefactos"].pop("base/1")
        r2 = self._dos(cambiar)
        self.assertEqual(r2["artefactos"], {"aut02/2": {"sha256": "A"}})

    def test_fetch_fallido_se_reintenta(self):
        remoto = _repo(self.td)
        c = _clon(self.td, remoto, 0)
        (c / "datos/runs").mkdir(parents=True)
        (c / "datos/runs/a.csv").write_text("x\n", encoding="utf-8")
        real = rm._git
        fallos = {"n": 0}

        def git_con_corte(root, *args, check=True):
            if args[0] == "fetch" and fallos["n"] < 2:
                fallos["n"] += 1
                return subprocess.CompletedProcess(args, 128, "", "fatal: unable to access: Connection reset")
            return real(root, *args, check=check)
        from unittest import mock
        with mock.patch.object(rm, "_git", git_con_corte):
            r = rm.registrar(root_dir=c, rama="main", mensaje="x", rutas=["datos/runs"], backoff=None)
        self.assertEqual((r.estado, r.intento), ("REGISTRADO", 3))
        with mock.patch.object(rm, "_git", lambda root, *a, check=True: subprocess.CompletedProcess(a, 128, "", "red")
                               if a[0] == "fetch" else real(root, *a, check=check)):
            with self.assertRaisesRegex(rm.PushRechazado, "^PUSH_RECHAZADO_TRAS_2: .*fetch: red"):
                rm.registrar(root_dir=c, rama="main", mensaje="x", rutas=["datos/runs"], backoff=None, max_intentos=2)

    def test_rutas_no_fusionables_se_rechazan_antes_de_empujar(self):
        remoto = _repo(self.td)
        c = _clon(self.td, remoto, 0)
        (c / "configuracion/catalogo.yaml").write_text("territorios: {aut01: 1}\n", encoding="utf-8")
        with self.assertRaisesRegex(rm.RutaNoFusionable, "RUTA_NO_FUSIONABLE: configuracion/catalogo.yaml"):
            rm.registrar(root_dir=c, rama="main", mensaje="x", rutas=["configuracion/catalogo.yaml"], backoff=None)
        git(c, "checkout", "--", "configuracion/catalogo.yaml")
        (c / "orchestracion/archivo_r2.json").write_text("[1, 2]\n", encoding="utf-8")
        with self.assertRaisesRegex(rm.RutaNoFusionable, "objeto JSON en la raíz"):
            rm.registrar(root_dir=c, rama="main", mensaje="x", rutas=["orchestracion/archivo_r2.json"], backoff=None)
        self.assertEqual(int(git(_estado_final(self.td, remoto), "rev-list", "--count", "HEAD")), 1)

    def test_catalogo_que_no_se_regenera_falla_cerrado(self):
        remoto = _repo(self.td, catalogo=True)
        c = _clon(self.td, remoto, 0)
        (c / "datos/runs").mkdir(parents=True)
        (c / "datos/runs/a.csv").write_text("x\n", encoding="utf-8")
        from unittest import mock
        from herramientas import catalogo_procedencia as cp
        with mock.patch.object(cp, "generar", side_effect=ValueError("roto")):
            with self.assertRaisesRegex(rm.CatalogoNoRegenerado, "CATALOGO_PROCEDENCIA_NO_REGENERADO: ValueError: roto"):
                rm.registrar(root_dir=c, rama="main", mensaje="x", rutas=["datos/runs"], backoff=None)
        self.assertEqual(int(git(_estado_final(self.td, remoto), "rev-list", "--count", "HEAD")), 1)

    def test_formato_json_del_remoto(self):
        doc = {"b": 1, "a": {"d": 2, "c": 3}}
        for indent in (1, 2):
            for sort_keys in (True, False):
                texto = json.dumps(doc, ensure_ascii=False, indent=indent, sort_keys=sort_keys) + "\n"
                if not sort_keys or indent == 2:
                    self.assertEqual(rm._volcar_json(doc, texto), texto)

    def test_delta_json_conserva_lo_ajeno_y_quita_lo_propio(self):
        base = {"a": {"x": 1, "y": 2}, "b": 1}
        nuevo = {"a": {"x": 1, "z": 3}, "b": 2}
        ajeno = {"a": {"x": 1, "y": 2, "w": 9}, "b": 1, "c": 5}
        self.assertEqual(rm.aplicar_delta(ajeno, rm.delta_json(base, nuevo)),
                         {"a": {"x": 1, "w": 9, "z": 3}, "b": 2, "c": 5})


class SinGruposUnicos(unittest.TestCase):
    def test_jobs_de_registro_sin_grupo_unico(self):
        casos = {
            "ejecucion-completa-proyecto.yml": ("actualizar_estado", "manifestar"),
            "_reutilizable-generacion-territorial.yml": ("pre_m04_evidence", "pre_m04_diagnostic", "registrar"),
            "_reutilizable-incorporacion-electoral.yml": ("registrar",),
        }
        for fichero, jobs in casos.items():
            texto = (WF / fichero).read_text(encoding="utf-8")
            datos = yaml.safe_load(texto)
            for job in jobs:
                self.assertNotIn("concurrency", datos["jobs"][job], f"{fichero}:{job}")
            self.assertNotIn("group: ddd-catalog-promotion", texto)
            self.assertNotIn("group: ddd-shared-operational-state", texto)
            self.assertNotIn("git pull --rebase", texto)

    def test_registros_usan_el_registrador_comun(self):
        territorial = (WF / "_reutilizable-generacion-territorial.yml").read_text(encoding="utf-8")
        self.assertEqual(territorial.count("python -m herramientas.registrar_en_main"), 2)
        self.assertIn("--aplicar \"$promote\"", territorial)
        electoral = (WF / "_reutilizable-incorporacion-electoral.yml").read_text(encoding="utf-8")
        self.assertEqual(electoral.count("python -m herramientas.registrar_en_main"), 1)
        orq = (WF / "ejecucion-completa-proyecto.yml").read_text(encoding="utf-8")
        self.assertEqual(orq.count("python -m herramientas.registrar_en_main"), 1)


class PasosBash(unittest.TestCase):
    """Los fragmentos nuevos corren bajo `bash -eo pipefail` (shell de los pasos): rc 0 si registra, salida propia si no."""

    def _fragmento(self, fichero: str, paso: str, desde: str) -> str:
        datos = yaml.safe_load((WF / fichero).read_text(encoding="utf-8"))
        for job in datos["jobs"].values():
            for st in job.get("steps", []):
                if st.get("name") == paso:
                    run = st["run"]
                    return run[run.index(desde):]
        raise AssertionError(paso)

    def _correr(self, fragmento: str, rc_python: int, env: dict) -> subprocess.CompletedProcess:
        with tempfile.TemporaryDirectory() as td:
            stub = Path(td) / "python"
            stub.write_text(f'#!/bin/bash\nprintf "%s\\n" "$@" >> "{td}/args"\nexit {rc_python}\n', encoding="utf-8")
            stub.chmod(0o755)
            entorno = {"PATH": f"{td}:/usr/bin:/bin", **env}
            p = subprocess.run(["bash", "-eo", "pipefail", "-c", fragmento], text=True, capture_output=True, env=entorno)
            p.args_python = (Path(td) / "args").read_text(encoding="utf-8") if (Path(td) / "args").exists() else ""
            return p

    def test_producto_territorial(self):
        frag = self._fragmento("_reutilizable-generacion-territorial.yml", "Registrar producto territorial certificado",
                               "# T-360")
        env = {"TERRITORY_ID": "aut07", "GITHUB_RUN_ID": "1", "GITHUB_REF_NAME": "main", "edition": "2025",
               "artifact_name": "ddd-state-1-M06", "digest": "sha256:" + "a" * 64, "checkout_sha": "b" * 40,
               "decision": "PASS", "manifest": "territorios/aut07/evidencia/generaciones_m06/1.json"}
        frag = "".join(f"{k}='{v}'\n" for k, v in env.items() if k.islower()) + frag
        ok = self._correr(frag, 0, env)
        self.assertEqual(ok.returncode, 0, ok.stderr)
        self.assertIn("--aplicar", ok.args_python)
        self.assertIn("--decision 'PASS'", ok.args_python)
        ko = self._correr(frag, 75, env)
        self.assertEqual(ko.returncode, 48)
        self.assertIn("rc=75", ko.stdout)

    def test_archivos_en_origen_y_manifiesto(self):
        casos = [
            ("_reutilizable-generacion-territorial.yml", "Archivo en origen — M06 a R2 y composición a git", "rc=0", 1),
            ("_reutilizable-incorporacion-electoral.yml", "Archivo en origen — M08 a R2 y votos por partido a git", "rc=0", 1),
        ]
        env = {"TERRITORY_ID": "aut07", "GITHUB_RUN_ID": "1", "GITHUB_REF_NAME": "main"}
        for fichero, paso, desde, rc_fallo in casos:
            frag = self._fragmento(fichero, paso, desde)
            self.assertEqual(self._correr(frag, 0, env).returncode, 0, paso)
            ko = self._correr(frag, 75, env)
            self.assertEqual(ko.returncode, rc_fallo, paso)
            self.assertIn("ARCHIVO_ORIGEN_FAILED", ko.stdout)

    def test_manifiesto_conserva_su_salida_50(self):
        frag = self._fragmento("ejecucion-completa-proyecto.yml", "Conservar manifiesto durable en producción", "rc=0")
        env = {"TERRITORY_ID": "aut07", "target": "territorios/aut07/evidencia/ejecuciones_completas/1.json"}
        frag = f"target='{env['target']}'\n" + frag
        self.assertEqual(self._correr(frag, 0, env).returncode, 0)
        ko = self._correr(frag, 75, env)
        self.assertEqual(ko.returncode, 50)
        self.assertIn("rc=75", ko.stdout)


if __name__ == "__main__":
    unittest.main()
