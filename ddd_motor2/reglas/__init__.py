"""Núcleo único de reglas de «plan válido» (T-160 · F1; diseño en docs/ARQUITECTURA/NUCLEO_REGLAS.md).

Python puro (solo stdlib). Interfaz pública:
    Unidad, Problema, Criterio, Reglas, ErrorContrato   (modelo)
    evaluar(problema, reglas, asignacion) -> Informe     (evaluar)
    variantes_criterio(), comparar_criterios(...)        (criterios: misma vara para la batería T-132)
    elegir_metodo(...)                                   (metodo: cadena frente a enumeración)
"""
from .modelo import CODIGOS, Criterio, ErrorContrato, ErrorDatos, Problema, Reglas, Unidad, norm_codigo
from .evaluar import Informe, Violacion, evaluar
from .criterios import comparar_criterios, resumen_por_opcion, variantes_criterio
from .metodo import Decision, elegir_metodo, cadena_degenerada

__all__ = [
    "CODIGOS", "Criterio", "ErrorContrato", "ErrorDatos", "Problema", "Reglas", "Unidad", "norm_codigo",
    "Informe", "Violacion", "evaluar", "comparar_criterios", "resumen_por_opcion", "variantes_criterio",
    "Decision", "elegir_metodo", "cadena_degenerada",
]
