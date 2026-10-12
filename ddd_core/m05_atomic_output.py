"""Atomic promotion helper for opt-in M05 candidate runs."""
from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path


class CandidateRejected(RuntimeError):
    """The staged M05 run did not pass its admission gate."""


def run_staged_output(output_path, report_path, execute):
    """Run entirely in a sibling temporary directory; promote only on admission.

    ``execute(staged_output, staged_report)`` returns ``(admitted, result)``.
    Exceptions and rejected results leave durable output/report paths untouched.
    """
    output = Path(output_path).resolve()
    report = Path(report_path).resolve() if report_path else None
    output.parent.mkdir(parents=True, exist_ok=True)
    if report:
        report.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="ddd_m05_private_run_", dir=str(output.parent)) as out_raw:
        with tempfile.TemporaryDirectory(prefix="ddd_m05_private_report_", dir=str(report.parent)) if report else _null_tempdir() as report_raw:
            out_td = Path(out_raw); report_td = Path(report_raw) if report else out_td
            staged_output = out_td / output.name
            staged_report = report_td / report.name if report else None
            admitted, result = execute(staged_output, staged_report)
            if not admitted:
                raise CandidateRejected("M05 private candidate rejected; durable outputs preserved")
            if not staged_output.is_file():
                raise CandidateRejected("M05 private candidate missing staged GeoJSON")
            if report and not staged_report.is_file():
                raise CandidateRejected("M05 private candidate missing staged report")

            output_backup = out_td / (output.name + ".previous") if output.exists() else None
            report_backup = report_td / (report.name + ".previous") if report and report.exists() else None
            if output_backup: shutil.copy2(output, output_backup)
            if report_backup: shutil.copy2(report, report_backup)
            output_promoted = report_promoted = False
            try:
                os.replace(staged_output, output); output_promoted = True
                if report:
                    os.replace(staged_report, report); report_promoted = True
            except Exception:
                # A pair of filesystem paths cannot be renamed in one syscall.
                # Roll back the first rename if the second one fails.
                if report_promoted:
                    if report_backup: os.replace(report_backup, report)
                    else: report.unlink(missing_ok=True)
                if output_promoted:
                    if output_backup: os.replace(output_backup, output)
                    else: output.unlink(missing_ok=True)
                raise
            return result


class _null_tempdir:
    """Context manager placeholder when no report path is requested."""
    def __enter__(self):
        return None

    def __exit__(self, *_exc):
        return False
