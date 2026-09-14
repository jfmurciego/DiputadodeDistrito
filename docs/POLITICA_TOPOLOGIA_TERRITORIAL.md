# Política de topología territorial

**Versión:** 1.0.0  
**Fecha:** 2026-09-13  
**Estado:** vigente — R037  
**Anterior:** ninguno — documento nuevo

## Decisión continental

Una sección aislada o una unidad administrativa desconectada no se repara por proximidad automática. El diagnóstico produce bloqueo. La admisión posterior exige una pasarela declarada con extremos, tipo, razón y fuente; solo se admiten enclaves/exclaves administrativos, discontinuidades del mismo municipio o huecos cartográficos demostrados. Una pasarela altera el grafo lógico, por lo que debe aparecer en contrato y manifiesto.

R023 mantiene bloqueados Cantabria, Castilla-La Mancha, Navarra, Comunidad Valenciana, Galicia, País Vasco y Región de Murcia. R037 no los ejecuta ni afirma haber resuelto sus anomalías.

## Decisión archipelágica

El mar no se convierte en arista. Cada isla o componente físico conserva contigüidad interna; ningún distrito cruza componentes. K debe repartirse explícitamente por componente antes de M04. Si una isla pequeña no puede sostener un distrito bajo los límites generales, la excepción debe apoyarse en una agrupación legal o administrativa explícita; la mera cercanía marítima no basta.

Illes Balears y Canarias quedan con política definida pero no admitidas. No se crean carpetas territoriales ni se abre M04.

## Puerta ejecutable

`herramientas/validar_politica_topologica.py` contrasta los siete contadores con la evidencia persistida R023, valida la prohibición de puentes automáticos y marítimos, y exige expediente completo para cualquier futura reparación. El registro canónico es `configuracion/politica_topologia_territorial_2025.yaml`.
