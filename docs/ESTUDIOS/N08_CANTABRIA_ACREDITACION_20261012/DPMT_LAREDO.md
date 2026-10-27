# Contraste puntual MITECO del Regatón: alcance y límites

Versión: 1.0.0. Nombre: evidencia cartográfica MITECO Laredo. Fecha: 2026-10-12. Alcance: parte separada `3903503001:p0000`. Estado: DIAGNOSTIC; identidad jurídica exacta NOT_EVIDENCED. Cambios: evidencia oficial puntual nueva. Motivo: contrastar naturaleza litoral sin inventar isla ni conexión. Origen: expediente MITECO DES01/14/39/0001; sin predecesor.

La Demarcación de Costas en Cantabria publicó documentación del expediente DES01/14/39/0001 para consulta del 1 de octubre al 2 de noviembre de 2026. El ejecutor conserva su página y recibo en `cartografia_laredo/MITECO_REGATON_DES01_14_39_0001.html`. La consulta no se trata como deslinde definitivo vigente en 2025.

Se adquirieron exclusivamente tres miembros del ZIP oficial mediante peticiones HTTP Range, respuesta 206, sin descargar el archivo completo de 68713995 bytes:

| Miembro | Bytes comprimidos | Bytes PDF | CRC32 central verificado |
|---|---:|---:|---|
| 3.2 Anejo 1 Unidades geomorfológicas | 2168486 | 2660296 | `a4184f1a` |
| 3.1 Estudio justificativo 2023 | 6815762 | 7080005 | `de4d81e4` |
| 1.1 Plano escala 2000 Hoja 1 firmado | 926572 | 1037885 | `aab721c8` |

Los valores CRC definitivos son los registrados en `cartografia_dpmt/RECIBOS.json`, comprobados frente al directorio central. Se preservan procedencia, rangos, Content-Range, hash de respuesta de rango, hash del miembro descomprimido, fecha UTC y comando. Los PDFs no se alteran. El directorio central parcial se conserva como `ZIP_CENTRAL_RANGE.bin` para reproducir la extracción, no como sustituto del ZIP.

El estudio técnico es de abril de 2023; su figura 8 identifica unidades geomorfológicas sobre ortofoto de 2020. El anejo1, segunda página, contiene mapa ETRS89/UTM30N, escala 1:12000, abril de 2023. Declara clases playa, marismas, dunas, arenas antropizadas y áreas urbanizadas, además de distinguir límites de DPMT aprobado y anulado. El análisis describe la costa estuarina del Regatón y la influencia de las mareas sobre sus sedimentos y marismas. Este soporte es independiente del seccionado INE 2025.

El anejo conserva metadatos GeoPDF de coordenadas: GPTS `[43.40974,-3.47379,43.43566,-3.47399,43.43589,-3.4139,43.40997,-3.41373]`, LPTS `[0,1,0,0,1,0,1,1]`, viewport BBox `[20.64054,822.29087,1169.31045,142.29832]`, MediaBox `[0,0,1190.23937,841.49291]`. Estos permiten situar la parte original sobre el mapa, sin usar proximidad como enlace topológico. Se examinó la ubicación representante −3,45790836 /43,41701756: cae en entorno estuarino sin clase geomorfológica coloreada propia, próximo a los sectores de marisma representados al oeste y a la playa al este. Por tanto **el mapa no acredita que la totalidad de la parte separada sea una marisma, una duna o una isla**. La falta de color de clase tampoco prueba profundidad permanente ni población cero.

Esta evidencia refuerza la interpretación de ámbito litoral sometido a agua y mareas, junto con PNOA 2023 y la guía municipal ya conservados. No acredita un contacto lineal seco, ninguna asignación administrativa diferente de la fuente base, la causa exacta de discrepancia con el recinto IGN ni equivalencia jurídica DPMT/municipio. No hay reparación automática, aristas nuevas ni distribución poblacional. La geometría INE permanece íntegra; la parte mantiene población desconocida y separación original de 78,301 m.

La denominación DES01/08/39/0003 aparece en el estudio y su mapa como antecedente del tramo analizado; el expediente de publicación de 2026 es DES01/14/39/0001. Se registran ambas identidades, sin confundirlas ni considerar un antecedente anulado como aprobación posterior. El plano Hoja 1 también fue extraído y su texto conserva cuadrícula, pero no añade una certificación de identidad del polígono INE 2025.

Extracción de texto reproducible mediante Swift/PDFKit nativo macOS, `extraer_texto_pdf.swift`; el texto conserva separadores PAGE para localizar las páginas 13–15 del estudio y página 2 del anejo. `renderizar_pdf.swift` permite inspección raster temporal del PDF oficial; la imagen temporal no se incorpora a Git ni se publica mapa. Python autorizado para extracción ZIP: `extraer_miembros_zip.py`, peticiones puntuales sin retries; deflate raw y CRC central obligatorio. No se instalaron librerías.

Conclusión: PASS en adquisición/integridad y contexto físico litoral; NOT_EVIDENCED en clase del polígono completo, causa de discrepancia y identidad jurídica temporal exacta. Se agotó el contraste técnicamente disponible de estos miembros oficiales sin convertir la incertidumbre restante en una excepción aprobada. Para cerrar la adscripción exacta haría falta certificación administrativa con correspondencia entre el polígono INE 2025, recinto IGN y deslinde aplicable; para una clase geomorfológica exhaustiva, cartografía vectorial original del estudio o validación oficial expresa del banco completo. `generation_authorized=false` continúa intacto.
