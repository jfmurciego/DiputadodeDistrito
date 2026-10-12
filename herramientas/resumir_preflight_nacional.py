#!/usr/bin/env python3
"""VERSIÓN 1.0.0; FECHA 2026-10-12; informes N08; ORIGEN nuevo.
ALCANCE diagnóstico/propuesta; ESTADO no aprobado; CAMBIOS/MOTIVO trazabilidad.
"""
import csv
import gzip
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from ddd_core.congreso_feasibility import evaluate_national

DOC = ROOT/'docs/ESTUDIOS/N08_TOPOLOGIA_NACIONAL_20251012'
PRODUCT = DOC/'producto'


def write(name, text):
    (DOC/name).write_text(text, encoding='utf-8')


def table(headers, rows):
    return '| '+' | '.join(headers)+' |\n| '+' | '.join('---' for _ in headers)+' |\n'+''.join('| '+' | '.join(str(x) for x in row)+' |\n' for row in rows)


def csv_write(name, headers, rows):
    with (DOC/name).open('w', encoding='utf-8', newline='') as f:
        w=csv.writer(f,lineterminator='\n');w.writerow(headers);w.writerows(rows)


def run():
    manifest=json.loads((PRODUCT/'manifest.json').read_text())
    products=[json.loads(gzip.decompress((PRODUCT/f'unidades/{i:02d}.json.gz').read_bytes())) for i in range(1,53)]
    summaries=[p['summary'] for p in products]
    options=evaluate_national(products)
    write('FACTIBILIDAD_OPCIONES.json',json.dumps(options,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
    rows=[[s[k] for k in ('CPRO','sections','population','k','edges','section_graph_components','physical_part_components','overlap_pairs','point_contacts','enclosed_voids')]
          +[len(s[k]) for k in ('isolated_sections','discontinuous_municipalities','multipart_sections_spanning_physical_components')]+[s['feasibility']] for s in summaries]
    csv_write('INVENTARIO_52.csv',['CPRO','secciones','poblacion_2025','K','aristas','componentes_seccionales','componentes_partes','solapamientos','contactos_punto','vacios_encerrados','secciones_aisladas','municipios_discontinuos','secciones_multicomponente','factibilidad'],rows)
    components=[]
    for p in products:
        code=p['summary']['CPRO']
        for c in p['physical_components']:
            components.append([code,'grafo_seccional',c['id'],len(c['sections']),c['population'],c['population'],''])
        for c in p['polygon_part_components']:
            components.append([code,'parte_poligonal',c['id'],len(c['parts']),c['population_exact'] if c['population_exact'] is not None else 'NOT_EVIDENCED',c['population_known'],','.join(c['population_unallocatable_sections'])])
    csv_write('COMPONENTES_POBLACION.csv',['CPRO','tipo','componente','unidades','poblacion_exacta','poblacion_conocida','CUSEC_sin_desagregacion'],components)
    overlaps=sum(s['overlap_pairs'] for s in summaries);point=sum(s['point_contacts'] for s in summaries)
    isolates=sum(len(s['isolated_sections']) for s in summaries);discontinuous=sum(len(s['discontinuous_municipalities']) for s in summaries)
    multipart=sum(len(s['multipart_sections_spanning_physical_components']) for s in summaries)
    impossible=[s for s in summaries if s['structural_impossibilities_under_strict_physical_contiguity']]
    artifact_size=sum(x['bytes'] for x in manifest['artifacts'].values())
    names={p['summary']['CPRO']:p['nodes'][0]['NPRO'] for p in products}
    write('INFORME_EJECUTIVO.md',f'''# N08 — diagnóstico topológico nacional ejecutado
Versión 1.0.0; nombre: base física Congreso; fecha 2026-10-12; alcance diagnóstico 52/52; estado N08 BLOCKED; origen nuevo. La ruta 20251012 conserva el nombre pedido por Work; no altera la fecha real.

Base: {manifest['base']}. Fuentes #239/#241/#242 reutilizadas, sin descarga ni modificación. Mónada 120.000, K=407 y 52 cuotas intactas. generation_authorized=false.

Cobertura demostrada: 36.554 CUSEC únicos, 49.128.297 habitantes, 52 unidades administrativas. Grafo original: {manifest['edges']:,} aristas de frontera lineal positiva con área de solapamiento cero; cero aristas interprovinciales, autorreferenciales o duplicadas. Las relaciones son no dirigidas y sus componentes se reconstruyen determinísticamente. Se excluyen {manifest['interprovincial_contacts_excluded']} contactos entre provincias.

Se distinguen {manifest['section_graph_components']} componentes del grafo seccional de {manifest['physical_part_components']} componentes de partes poligonales. {multipart} secciones abarcan partes en componentes distintos: el nodo seccional no acredita paso físico. Las poblaciones de los componentes seccionales concilian exactamente. En componentes de partes que comparten sección, se registra población exacta NOT_EVIDENCED, población conocida y CUSEC afectados; no se reparte por superficie.

Anomalías: {overlaps} pares de solapamiento intraprovincial, {manifest['interprovincial_overlap_pairs']} interprovinciales, {point} contactos exclusivamente puntuales, {isolates} secciones aisladas y {discontinuous} municipios discontinuos por grafo inducido de secciones o partes. Los pequeños solapamientos no se admiten automáticamente como ruido tolerable. Vacíos encerrados se miden sobre la unión original; pueden incluir agua, enclaves o déficits. Falta frontera independiente para clasificar huecos externos y cobertura de dominio: NOT_EVIDENCED, no ausencia de defectos.

Los productos comprimidos ocupan {artifact_size:,} bytes, sin coordenadas duplicadas ni fuentes originales. Cada nodo conserva todos los atributos originales, POB_2025, hash WKB y hash del ZIP; cada arista conserva longitud, área cero y hash WKB del contacto. Los conjuntos de partes y municipios se incluyen en los 52 paquetes. Manifiesto: producto/manifest.json, identidad {manifest['identity_sha256']}.

La preparación diagnóstica A tiene cobertura PASS, integridad topológica BLOCKED y cierre externo NOT_EVIDENCED. B, factibilidad de Cantabria, BLOCKED por componentes, población interna no desagregada y decisiones pendientes. C, autorización productiva, BLOCKED. No se declara READY, no se genera ningún distrito ni se ejecuta 00/M04–M06 real. La reproducción y el dictamen independiente se conservan con hashes y logs al cierre.

Siguiente acción técnica: resolver nominalmente el enclave de Valle de Villaverde y las tres secciones multipartes de Cantabria, contrastar sus componentes con evidencia administrativa/poblacional y una frontera independiente ya acreditable, y decidir una política explícita de contigüidad/excepciones. Después aprobar unidad mínima, disciplina municipal y límites; implementar el gate nacional final M04–M06 que exija simultáneamente K, conectividad y límites. Las pruebas sintéticas actuales no autorizan el piloto.
''')
    write('METODO_Y_REPRODUCCION.md',f'''# Método y reproducción
Versión 1.0.0; fecha 2026-10-12; alcance diagnóstico; estado candidato; origen nuevo.

El ZIP se reconstruye en RAM desde las tres partes protegidas, contrastando cada SHA y el ZIP 55c9da7e34d3bb3cb725400c35b58e72f4db2ea8321ef91237a89e708d2dbcc4. Se verifica CRC y cada miembro. Por incompatibilidad GDAL con el directorio acentuado, se renombra sólo el contenedor lector efímero; SHP/SHX/DBF/PRJ conservan exactamente sus bytes. Identidad geométrica WKB 6eccbc0c7f4867656c235462ae0b6d381dcdaeb5c912e5295976ca8f120860ff idéntica a #241. CRS EPSG:25830 sin transformación. Join CUSEC exacto y atributos administrativos contrastados contra CSV acreditado. No se repite adquisición ni se recalcula población acreditada.

Grafo físico raw: STRtree para candidatos que intersectan; frontera común medida en metros; longitud estrictamente >0 y área de intersección ==0. Contactos de punto y solapamientos se registran pero no son aristas. Provincias impermeables. No buffer, simplificación, make_valid, pasarela, redondeo ni tolerancia de área en ese grafo. Grafo operativo idéntico al seccional físico, sin puente añadido; no acredita contigüidad interna de nodos multipartes. Componentes de partes se calculan por contactos reales entre polígonos originales separados. Se conserva la semántica del motor común mediante adaptador aislado y sus tests.

Sensibilidad separada: umbrales de frontera 0/1/10/50m examinan fragilidad de contactos cortos. Grillas 0,01/0,1/1m examinan efectos de precisión desde centímetros a metros; no son política aprobada. Registran aristas nuevas NO ACREDITADAS, perdidas y secciones colapsadas. Ningún resultado redondeado se utiliza en el grafo original. La sensibilidad cuenta componentes seccionales; no acredita que el redondeo preserve partes de tierra. Vacíos encerrados se miden, sin llamar a todo hueco error o inventar un límite de dominio.

Comando constructor: `python herramientas/preflight_topologico_nacional.py --parts-dir <partes protegidas existentes> --output <directorio nuevo>`.
Comando auditor independiente: `python herramientas/verificar_topologia_nacional.py --parts-dir <partes> --product <producto> --output <acta.json>`.
Informes/alternativas: `python herramientas/resumir_preflight_nacional.py`.

Cada ámbito es checkpoint determinista ligado a hashes de fuente, código y software. --resume es explícito, rechaza checkpoints incompatibles y no es un reintento automático. Gzip mtime=0 y JSON canónico. Entorno productor: {json.dumps(manifest['software'],ensure_ascii=False)}. La reproducibilidad byte a byte requiere este entorno; CI comprueba integridad y contratos sobre artefactos y fixtures, sin reconstruir fuentes ni simular certificación territorial.
''')
    anomaly_rows=[]
    for p in products:
        s=p['summary']; anomaly_rows.append([s['CPRO'],names[s['CPRO']],s['overlap_pairs'],s['point_contacts'],len(s['isolated_sections']),len(s['discontinuous_municipalities']),len(s['multipart_sections_spanning_physical_components']),s['enclosed_voids']])
    write('ANOMALIAS.md','# Registro nacional de anomalías\nVersión 1.0.0; fecha 2026-10-12; estado diagnóstico; alcance52/52; origen nuevo.\n\n'+table(['CPRO','Provincia','Solapamientos','Puntos','Aisladas','Municipios discontinuos','CUSEC multipartes','Vacíos'],anomaly_rows)+f'\nDetalle nominal, parejas CUSEC, área/longitud/hash y municipios: producto/unidades/CPRO.json.gz. Contactos entre provincias: producto/contactos_interprovinciales.json.gz; {manifest["interprovincial_overlap_pairs"]} solapamientos se excluyen siempre del grafo. Secciones aisladas incluyen población cero si existiesen; nunca se omiten por su población. Municipio aislado respecto de otros se declara en cada paquete, separado del mero nodo aislado.\n')
    impossible_rows=[[s['CPRO'],names[s['CPRO']],s['k'],s['section_graph_components'],s['physical_part_components']] for s in impossible]
    write('FACTIBILIDAD_ESTRUCTURAL.md','# Factibilidad estructural frente a K aprobado\nVersión 1.0.0; fecha2026-10-12; diagnóstico necesario, sin partición; origen nuevo.\n\nBajo contigüidad física estricta y sin excepciones/pasarelas, componentes físicos>K_i impiden cubrir todas las partes con K_i distritos conectados. Este resultado es condicional a la definición raw y a integridad geométrica pendiente; no cuestiona K ni autoriza reducir componentes. Un número menor o igual a K nunca demuestra factibilidad.\n\n'+table(['CPRO','Provincia','K','Componentes seccionales','Componentes de partes'],impossible_rows)+'\nLa población de componentes de partes de 115 secciones carece de desagregación acreditada. COMPONENTES_POBLACION.csv explicita NOT_EVIDENCED y población conocida; no convertir esos datos en cero ni repartirlos por área. Los intervalos enteros de distritos por componente bajo cada opción se encuentran en FACTIBILIDAD_OPCIONES.json. Son condiciones necesarias de cobertura y población, no una solución de cortes, disciplina municipal o factibilidad M04–M06.\n')
    policy_rows=[[o['basis'],o['tolerance'],','.join(o['mean_outside_limits']) or 'ninguna',len(o['component_arithmetic_blocked']),len(o['municipal_indivisibility_blocked']),o['municipalities_requiring_split'],o['sections_above_upper']] for o in options['options']]
    write('PROPUESTA_POBLACION_MUNICIPIOS.md','''# Propuesta única, pendiente del propietario
Versión1.0.0; fecha2026-10-12; alcance análisis de seis opciones reales; estado NOT_APPROVED; origen nuevo.

Recomendación: mantener 120.000 como referencia institucional para K; utilizar P_i/K_i como centro operativo provincial y tolerancia ordinaria ±15%, preservando Soria/Ceuta/Melilla como excepciones poblacionales expresas. No crea nuevas excepciones provinciales. Fronteras provinciales duras. La indivisibilidad municipal absoluta debe descartarse como regla general: preservar municipios contiguos cuando quepan y sean compatibles con equilibrio; permitir subdivisión necesaria por secciones oficiales en municipios grandes o cuando equilibrio/conectividad lo exijan, minimizando cortes municipales como objetivo secundario. Toda sección multipartes necesita tratamiento acreditado específico antes de usarla como unidad atómica. Nunca inferir pasarelas ni población de partes por área.

Las seis alternativas comparan ±10/15/20% alrededor de referencia fija y promedio provincial. El centro provincial evita incompatibilidades aritméticas impuestas por el redondeo de K, sin sustituir la regla aprobada. ±15% es una propuesta intermedia: datos y casos afectados expuestos para decisión; no se atribuye optimalidad ni factibilidad suficiente. Municipios por encima del techo exigirían varios distritos si se adoptase ese límite; los listados nominales con población y mínimo de distritos aparecen en FACTIBILIDAD_OPCIONES.json. Las aristas/anomalías, los componentes diminutos y secciones desconectadas no se resuelven ampliando tolerancias.

'''+table(['Centro','Tolerancia','Media provincial fuera del intervalo','Provincias con bloqueo de componentes','Provincias incompatibles con municipio indivisible','Municipios > techo','Secciones > techo'],policy_rows)+'''
Límites se calculan con fracciones exactas: por cada componente ceil(P/cap)≤k_c≤floor(P/floor), con al menos una plaza y k_c≤n_secciones; luego sum(min)≤K_i≤sum(max). Componentes de cero población también requieren cobertura, de modo que no se omiten. Las excepciones poblacionales no dispensan contigüidad ni eliminan componentes físicos.

Falta aprobación expresa del propietario sobre centro y tolerancia, unidad mínima, regla de cortes municipales y tratamiento nominal de discontinuidades. Esta recomendación sigue el mandato de representación directa del proyecto, no los350 escaños ni Hamilton; no constituye dictamen jurídico de viabilidad constitucional o legislativa. No altera decisiones actuales ni configura el motor productivo.
''')
    cantabria=products[38];s=cantabria['summary'];nodes={n['id']:n for n in cantabria['nodes']}
    chosen=next(o for o in options['options'] if o['basis']=='provincial_mean' and o['tolerance']=='3/20')
    coption=chosen['units'][38]
    special_rows=[[uid,nodes[uid]['NMUN'],nodes[uid]['pop'],','.join(nodes[uid]['physical_part_components'])] for uid in s['isolated_sections']+s['multipart_sections_spanning_physical_components']]
    write('CANTABRIA.md',f'''# Cantabria — diagnóstico detallado, K=5
Versión1.0.0; fecha2026-10-12; estado BLOCKED; origen nuevo; sin generación.

CPRO39; P2025=593.623; 458 secciones y 102 municipios; K5 aprobado. {s['edges']} aristas raw, {s['point_contacts']} contactos puntuales y {s['overlap_pairs']} solapamientos, área por parejas {s['overlap_area_pair_sum_m2']:.12f}m². Dos componentes seccionales: 457 secciones/593.374 habitantes y Valle de Villaverde 3910101001/249 habitantes, enclave físico separado. No declarar viable K5 por el tamaño manejable.

Cinco componentes de partes: principal y tres partes de secciones Laredo/Ribamontán al Mar/Santander, además de Valle de Villaverde. Las tres secciones comparten con tierra principal una población total3.382 sin asignación a cada parte acreditada. Principal: 589.992 habitantes con localización inequívoca por sección completa; población total del principal NOT_EVIDENCED. Partes separadas: población conocida0, exacta NOT_EVIDENCED; no significan población cero. Valle de Villaverde sí tiene249 acreditados. Para K5, que cinco componentes≤cinco plazas no prueba viabilidad: bajo contigüidad estricta el pequeño enclave necesitaría una plaza muy por debajo de todos los suelos ordinarios propuestos, sin excepción poblacional aprobada para Cantabria.

'''+table(['CUSEC','Municipio','Población sección','Componentes de partes'],special_rows)+f'''
Municipios discontinuos por partes: Laredo39035, Luena39046, Ribamontán al Mar39061, Ruesga39067 y Santander39075. Los cinco son conexos en el grafo seccional: demuestra por qué ese grafo no basta para certificar contigüidad. La sensibilidad de frontera0/1/10/50m conserva dos componentes y reduce aristas1208/1205/1183/1151. Redondeo0,01/0,1/1m:1234/1235/1232 aristas,29/28/29 nuevas no acreditadas y2/2/3 componentes; nunca se incorporan. Hay28 vacíos encerrados con área75.426.757,886579m², aún sin clasificación entre agua/enclave/déficit: se requiere contraste de dominio, no reparación automática.

Propuesta ±15% sobre593623/5=118724,6: suelo100915,91 y techo136533,29. Resultado necesario de componentes: {coption['arithmetic_impossibility_section_graph']}; municipio indivisible imposible por tamaño: {coption['municipal_indivisibility_impossibility_by_size_or_count']}. Santander175.082 exige al menos dos distritos con ese techo; sección mínima y cortes necesitan autorización. No se ejecuta construcción de cinco distritos.

Paso técnico preciso: acreditar nominalmente enclave y partes con inventario administrativo y población desagregada o excepción expresa compatible con representación directa; contrastar28 vacíos con dominio independiente y decidir política de precisión geométrica sustentada en sensibilidad, manteniendo original intacto. Sin estos cierres, aumentar tolerancia no convierte249 habitantes en un distrito ordinario equilibrado ni une físicamente componentes. Después de decisiones expresas, gate aislado Congreso M04–M06 y ensayo posterior autorizado por separado.
''')


if __name__ == '__main__': run()
