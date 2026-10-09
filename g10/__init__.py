"""Orquestación reproducible G10 para Diputado de Distrito."""

from .core import (Admission, FailureClass, TaskStatus, aggregate_summaries,
                   classify_failure, compute_fingerprint, decide_admission,
                   retry_decision, validate_plan)

__all__ = ["Admission", "FailureClass", "TaskStatus", "aggregate_summaries",
           "classify_failure", "compute_fingerprint", "decide_admission",
           "retry_decision", "validate_plan"]
