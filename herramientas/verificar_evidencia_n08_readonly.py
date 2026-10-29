"""Versión 1.1.2; 2026-10-29; reproducción aislada y read-only de evidencias N08.

Nombre: verificador read-only de la evidencia nacional y Cáceres.
Alcance: verificar 74/74 y 26/26, y reproducir la matriz de cierre sin escribir
         en el repositorio ni mutar artefactos versionados.
Estado: candidato diagnóstico.
Cambios/motivo: ejecuta el verificador histórico en un root temporal aislado,
                conserva su hash y compara sus salidas byte a byte. Usa el
                snapshot M02 archivado que el manifiesto histórico acredita.
                1.1.1: monta también el motor M04 v7.6.4 archivado, que acredita el
                expediente de Cáceres, porque el rescate M04 del 26-10 cambia el activo.
                1.1.2: monta también el M06 v7.2.2 archivado (la exención de suelo por municipio cambia el activo).
Origen: nuevo; no sustituye ni modifica el verificador histórico.
Anterior: legacy/herramientas/verificar_evidencia_n08_readonly_v1.1.1_20261029.py
"""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any


HISTORICAL_REL = Path("docs/ESTUDIOS/N08_CIERRE_NACIONAL_20261013/verificar_evidencia.py")
OUTPUT_NAMES = ("MATRIZ_FACTIBILIDAD_52.csv", "VERIFICACION.json", "MANIFEST.json")
SOURCE_MANIFESTS = (
    Path("docs/ESTUDIOS/N08_TOPOLOGIA_NACIONAL_20251012/MANIFEST_ENTREGA.json"),
    Path("docs/ESTUDIOS/N08_CACERES_20261012/MANIFEST.json"),
    Path("docs/ESTUDIOS/N08_CIERRE_NACIONAL_20261013/MANIFEST.json"),
)


class EvidenceMismatch(RuntimeError):
    """Raised when historical evidence does not reproduce byte-for-byte."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _link_source(root: Path, temporary_root: Path, relative: Path) -> None:
    source = root / relative
    if not source.exists():
        raise EvidenceMismatch(f"MISSING_INPUT:{relative.as_posix()}")
    destination = temporary_root / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.symlink_to(source, target_is_directory=source.is_dir())


def verify(root: Path | str) -> dict[str, Any]:
    """Reproduce historical evidence in a disposable tree and compare outputs.

    The original verifier is copied byte-for-byte into a temporary directory.
    Its input trees are exposed there by symlinks; its output directory is a
    real temporary directory. No path under ``root`` is opened for writing.
    """
    root = Path(root).resolve()
    historical_script = root / HISTORICAL_REL
    output_dir = historical_script.parent
    if not historical_script.is_file():
        raise EvidenceMismatch(f"MISSING_HISTORICAL_VERIFIER:{HISTORICAL_REL}")

    expected_local_manifest = json.loads((output_dir / "MANIFEST.json").read_text(encoding="utf-8"))
    expected_script_sha = expected_local_manifest.get("files_sha256", {}).get("verificar_evidencia.py")
    actual_script_sha = _sha256(historical_script)
    if not expected_script_sha or expected_script_sha != actual_script_sha:
        raise EvidenceMismatch("HISTORICAL_VERIFIER_HASH_MISMATCH")

    before = {name: _sha256(output_dir / name) for name in OUTPUT_NAMES}
    manifests_before = {rel.as_posix(): _sha256(root / rel) for rel in SOURCE_MANIFESTS}

    with tempfile.TemporaryDirectory(prefix="ddd-n08-readonly-") as temporary:
        temp_root = Path(temporary)
        for rel in (
            Path("docs/ESTUDIOS/N08_TOPOLOGIA_NACIONAL_20251012"),
            Path("docs/ESTUDIOS/N08_CACERES_20261012"),
            Path("herramientas"),
            Path("tests"),
            Path("territorios/congreso"),
            Path("legacy/n08_caceres_20261012"),
        ):
            _link_source(root, temp_root, rel)

        # Igual que el M02: el expediente de Cáceres acredita el motor M04 v7.6.4.
        historical_m04 = root / "legacy/ddd_core/m04_seed_engine_v7.6.4.py"
        if not historical_m04.is_file():
            raise EvidenceMismatch("MISSING_HISTORICAL_M04_SNAPSHOT")
        temp_core = temp_root / "ddd_core"
        temp_core.mkdir(parents=True, exist_ok=True)
        for item in (root / "ddd_core").iterdir():
            target = historical_m04 if item.name == "m04_seed_engine.py" else item
            (temp_core / item.name).symlink_to(target, target_is_directory=target.is_dir())

        # El verificador histórico compara su manifiesto con el M02 que
        # existía al crear el expediente. El código activo puede evolucionar;
        # en la copia aislada se monta el snapshot exacto archivado para que
        # esta comprobación siga validando evidencia histórica, no el HEAD.
        source_modules = root / "modulos"
        temp_modules = temp_root / "modulos"
        temp_modules.mkdir(parents=True, exist_ok=True)
        historical_m02 = root / "legacy/modulo02/02_construir_adyacencias_v7.3.2.py"
        if not historical_m02.is_file():
            raise EvidenceMismatch("MISSING_HISTORICAL_M02_SNAPSHOT")
        historical_m06 = root / "legacy/modulo06/06_consolidar_distritos_v7.2.2.py"
        if not historical_m06.is_file():
            raise EvidenceMismatch("MISSING_HISTORICAL_M06_SNAPSHOT")
        historical_modules = {"02_construir_adyacencias.py": historical_m02, "06_consolidar_distritos.py": historical_m06}
        for item in source_modules.iterdir():
            target = historical_modules.get(item.name, item)
            (temp_modules / item.name).symlink_to(target, target_is_directory=target.is_dir())

        temp_output = temp_root / HISTORICAL_REL.parent
        temp_output.mkdir(parents=True, exist_ok=True)
        temp_script = temp_root / HISTORICAL_REL
        shutil.copyfile(historical_script, temp_script)
        if _sha256(temp_script) != actual_script_sha:
            raise EvidenceMismatch("TEMPORARY_VERIFIER_COPY_CHANGED")
        for name in ("INFORME.md", "TRANSICION.json", "REVISION_INDEPENDIENTE.md",
                     "INCIDENCIA_PUBLICACION.md"):
            (temp_output / name).symlink_to(output_dir / name)

        namespace: dict[str, Any] = {}
        # The copied script computes ROOT from __file__; using its isolated path
        # directs all writes to temp_root/docs/... while source inputs stay read-only.
        import runpy

        namespace.update(runpy.run_path(str(temp_script), run_name="ddd_n08_historical_reproducer"))
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            namespace["main"]()

        reproduced = {}
        for name in OUTPUT_NAMES:
            actual_path = temp_output / name
            expected_path = output_dir / name
            if not actual_path.is_file():
                raise EvidenceMismatch(f"REPRODUCED_OUTPUT_MISSING:{name}")
            actual_bytes = actual_path.read_bytes()
            expected_bytes = expected_path.read_bytes()
            reproduced[name] = {
                "byte_identical": actual_bytes == expected_bytes,
                "expected_sha256": hashlib.sha256(expected_bytes).hexdigest(),
                "reproduced_sha256": hashlib.sha256(actual_bytes).hexdigest(),
            }
            if actual_bytes != expected_bytes:
                raise EvidenceMismatch(f"REPRODUCED_OUTPUT_MISMATCH:{name}")

        verification = json.loads((temp_output / "VERIFICACION.json").read_text(encoding="utf-8"))
        if verification["national_manifest"]["verified"] != 74:
            raise EvidenceMismatch("NATIONAL_EVIDENCE_NOT_74_OF_74")
        if verification["caceres_manifest"]["verified"] != 26:
            raise EvidenceMismatch("CACERES_EVIDENCE_NOT_26_OF_26")
        if verification.get("generation_authorized") is not False:
            raise EvidenceMismatch("GENERATION_AUTHORIZATION_MUST_REMAIN_FALSE")

    after = {name: _sha256(output_dir / name) for name in OUTPUT_NAMES}
    manifests_after = {rel.as_posix(): _sha256(root / rel) for rel in SOURCE_MANIFESTS}
    if before != after:
        raise EvidenceMismatch("VERSIONED_OUTPUTS_MUTATED")
    if manifests_before != manifests_after:
        raise EvidenceMismatch("SOURCE_MANIFESTS_MUTATED")

    return {
        "status": "PASS",
        "read_only": True,
        "historical_verifier_sha256": actual_script_sha,
        "national_entries_verified": verification["national_manifest"]["verified"],
        "caceres_entries_verified": verification["caceres_manifest"]["verified"],
        "coverage": verification["coverage"],
        "generation_authorized": verification["generation_authorized"],
        "outputs": reproduced,
        "source_manifests_unchanged": True,
        "versioned_outputs_unchanged": True,
        "temporary_execution": True,
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1],
                        help="raíz del repositorio (predeterminada: raíz detectada desde esta herramienta)")
    args = parser.parse_args()
    print(json.dumps(verify(args.root), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
