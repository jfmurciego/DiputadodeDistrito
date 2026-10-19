# Preflight nacional provincial 52/52

Ejecución diagnóstica completa; no constituye autorización ni certificación de distritos.

- Base: `21a4a150eb14f1abecd5d798b159d84a71df1f4a`
- SHA herramienta: `1873a261e1b3a85c2ad34b74db2ab0fb61902663173e91aa262cc648093d1455`
- SHA manifiesto lote: `0595df6237b183c9f6499c16e28ff7da7331ab54d46f4f2a00f1c5564f10efc5`
- SHA transición: `43ad0c85e89940977741749a2231c24c7320d4e4771f391a5a47eff1fc2b6048`
- SHA manifiesto de fuentes: `f99e1690071b6383d90094b35fe024865d5bc75ef95983014452d1d25dbadc37`
- Ejecuciones: 52/52, una por provincia, sin reintentos; retornos 0: 52/52.
- Cobertura: 36,554 secciones; población 49,128,297; 99,597 aristas del grafo acreditado.

| Módulo | Resultado |
|---|---|
| M01 | PASS: 52 |
| M02 | PASS: 52 |
| M03 | PASS: 52 |
| M04 | PASS_NECESSARY_ONLY: 50; BLOCKED: 2 |
| M05 | SYNTHETIC_CONTRACT_PASS_ONLY: 52 |
| M06 | SYNTHETIC_CONTRACT_PASS_ONLY: 52 |

Los M01-M03 pasaron en todas las unidades. M04 es solo un análisis de condiciones necesarias: CPRO09 y CPRO34 quedan `BLOCKED` por `PHYSICAL_COMPONENTS_EXCEED_K`, con `feasibility_proven=false`; esto no demuestra imposibilidad. M05 y M06 se probaron únicamente mediante fixtures sintéticos; no se ejecutaron contra particiones territoriales. Las 52 salidas conservan `generation_authorized=false`, cero distritos y certificación de producto `NOT_PERFORMED`. El estado global se mantiene bloqueado por la acreditación independiente del dominio provincial y decisiones contractuales que no se deducen de esta ejecución.
