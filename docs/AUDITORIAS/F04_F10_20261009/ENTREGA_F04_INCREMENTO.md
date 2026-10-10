# Incremento correctivo F04

Versión 1.0.0; 2026-10-10. Predecesor: ENTREGA_F04.md y árbol33140afb2fb567322358c91c10daa0f3aae27fd7. Una causa corregida, ciclo1.

Entrega vigente: candidate-results-v3.json, matriz-19-v3.json, cinco candidato-v3 y derived-receipt-v3.json. Sustituye únicamente la selección de candidatos v2; las versiones anteriores permanecen como historial NO_GO y no se deben consumir.

El script corregir_declaraciones.py copia los bytes numéricos y el informe exacto, modifica las cuatro declaraciones y crea paquete/manifest/receipt con nuevas identidades. En cada fuente separa adquisición histórica de operación local, verifica SHA/bytes reales y registra ruta local. Logs correccion-v3.*. Sin promoción ni modificaciones productivas.
