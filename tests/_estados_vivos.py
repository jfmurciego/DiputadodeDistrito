"""Estados válidos del ciclo de preparación de un territorio (T-146).

El bot reescribe `configuracion/catalogo_territorios_espana_2025.yaml` y los contratos de cada territorio en cada
preparación (p. ej. «preparación territorial de aut11» deja `source_prepared_pending_pre_m04`). Un test sobre el
repositorio vivo no debe fijar UN estado del ciclo: acepta el conjunto o usa una fixture fija (`tests/_raiz_congelada.py`).
"""
ESTADOS_PREPARADO = frozenset({"generation_ready", "source_prepared_pending_pre_m04"})
