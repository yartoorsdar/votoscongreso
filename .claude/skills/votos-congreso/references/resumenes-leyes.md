# Resúmenes del propósito de cada ley

El panel «Detalle de la ley» de la web tiene una caja **Propósito** con 2 o 3 frases. Las redacta Claude (sin API) a partir del texto de la iniciativa. No es el texto final aprobado, y la web lo dice.

## Procedimiento

1. Saber qué falta: `python scraper/estado.py` lista las leyes «sin resumen» y si tienen PDF, extracto o nada.
2. Conseguir el URL del PDF de la iniciativa: lo traen `js/iniciativas.js` (detalle) y `js/decretos.js` (listado) y quedan en `data/pdf_origen.json`.
3. Leer el PDF en la página: `python scraper/preparar_js.py pdf` (por defecto, las iniciativas citadas en votaciones con PDF y sin extracto; o `--tokens 6852,6493`) → pegar el código en una pestaña del Congreso → `await window.__export()` → `python scraper/importar_pdf.py`. No se descarga nada.
4. Leer `data/pdf_extracto.json`: por iniciativa trae `extracto` (~3,500 caracteres desde «EXPOSICIÓN DE MOTIVOS» o el primer «CONSIDERANDO») y `objeto` (alrededor de «tiene por objeto»). Los PDF son escaneos con OCR: hay errores (`ó` → `6`, `ñ` → `n`), no los copies.
5. Redactar el resumen en el diccionario `R` de `scraper/resumenes_leyes.py` con la forma `"<clave de ley>": ("texto", "pdf"|"titulo")`, ejecutar `python scraper/resumenes_leyes.py` y luego `export_web.py`.

La clave de ley es la que usa la web: `d22-2026` (con decreto) o `i6493` (sin decreto; número menor si hay varias iniciativas fusionadas). `estado.py` las imprime.

## Cómo escribirlos

- Qué propone la ley y por qué, en lenguaje que entienda cualquier persona: sin jerga legal, sin siglas sin explicar (IDP, IVA sí se conocen; el resto, explicar).
- 2 o 3 frases, unas 40 a 60 palabras. La primera dice QUÉ hace la ley (verbo en presente: «Exime…», «Reforma…», «Declara…»); la segunda, para qué o a quién beneficia.
- Solo lo que está en la fuente. Cifras y fechas únicamente si el texto las trae (por ejemplo «hasta el 31 de diciembre de 2026», «Q36,000 en tres años»). Si dudas de un dato, quítalo.
- Describe lo PROPUESTO. Si el resumen se basa solo en el título o en notas del Congreso (no se pudo leer el PDF), marca la fuente `"titulo"`; la web lo anuncia.
- Si no hay fuente (sin PDF, expediente ilegible), NO se escribe resumen: la ley queda sin caja de propósito. En 2026 quedaron así 6 de 34 leyes. Es mejor vacío que inventado.
- Iniciativas fusionadas (6493-6719, 6527-6541, 6705-6707, 6355-6430): una sola ley; resumir lo común y enlazar ambos PDF.
- Expedientes enormes (la 6593 antilavado tiene 173 páginas, la 6541 portuaria 247): leer `objeto` y los primeros artículos; si no alcanza, usar `"titulo"`.

Ejemplo (decreto 22-2026): «Exime temporalmente del Impuesto a la Distribución de Petróleo (IDP) y del IVA a la gasolina regular, la gasolina superior y el diésel, desde el día siguiente a su publicación hasta el 31 de diciembre de 2026. Busca amortiguar el impacto en los hogares y en la producción del alza de precios: el barril WTI pasó de unos US$64 en febrero a más de US$100 en septiembre de 2026.»

## Cómo se muestran

Caja azul «Propósito» con el texto y una nota: «Resumen elaborado con IA a partir de la exposición de motivos de la iniciativa (o: a partir del título y de información del Congreso). Describe lo que se propuso, no necesariamente el texto final aprobado. Fuente oficial: iniciativa 6852 (PDF).» Los enlaces salen de `pdf_origen.json`. Para leyes sensibles (Código Penal, Código Procesal Penal, universidad pública, elecciones) conviene pedir revisión humana antes de dar el enlace por definitivo.
