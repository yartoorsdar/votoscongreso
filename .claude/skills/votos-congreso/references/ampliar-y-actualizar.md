# Recetas: actualizar, ampliar a otros años y resolver problemas

Contenido: A. Ritual para correr un trabajo en el navegador · B. Actualización semanal · C. Ampliar a otros años · D. Antes de publicar · E. Si algo falla

Todos los comandos se ejecutan desde la raíz del proyecto (`PYTHONIOENCODING=utf-8 python ...` en Windows).

## A. Ritual para correr un trabajo en el navegador (todos los trabajos son iguales)

1. **Código**: `python scraper/preparar_js.py <trabajo> [opciones]` imprime el JavaScript con sus parámetros ya puestos (`votos`, `iniciativas`, `decretos`, `pdf`, `roster`, `logos`, `imagenes`).
2. **Pestaña**: usar una pestaña propia en `www.congreso.gob.gt` (`tabs_context`; si no hay panel, `preview_start` con una URL del Congreso). No navegarla ni usarla para otra cosa mientras corre. `logos` necesita que la pestaña esté en `/buscador_bloques`.
3. **Lanzar**: pegar el código completo en `javascript_tool`. Responde «iniciado» enseguida; el trabajo sigue en la página.
4. **Seguir el avance**: `({...window.__prog})` cada ≤40 s (esas llamadas expiran a los ~45 s; una espera de 30 a 40 s dentro de la llamada sirve de pausa). `state` pasa a `terminado` o `detenido` (con `err`). Para parar sin perder nada: `window.__stop = true`.
5. **Sacar los datos**: `await window.__export()` como última expresión. La respuesta grande se guarda sola en disco y el mensaje trae la ruta (ver `sitio-congreso.md` §4). No pedir al usuario que guarde nada.
6. **Importar**: el `importar_*.py` que corresponda; sin argumento usa el archivo más reciente, con la ruta del mensaje es explícito.
7. **Verificar**: `python scraper/estado.py`.

| Trabajo | Importador | Qué hace |
|---|---|---|
| `votos` | `importar_votos.py` | sesiones, votaciones (con hora) y votos de un rango de fechas; salta lo ya guardado |
| `iniciativas` | `importar_iniciativas.py` | detalle oficial de cada iniciativa citada en votos: decreto, ponentes, línea de tiempo, PDF |
| `decretos` | `cruzar_decretos.py` | nombres de leyes de todos los decretos y plan B de enlace por fecha |
| `pdf` | `importar_pdf.py` | texto de la exposición de motivos, para redactar resúmenes |
| `roster` / `logos` | `importar_roster.py` | diputados actuales, bloque y URLs de fotos y logos |
| `imagenes` | `importar_imagenes.py` | fotos y logos reducidos a `web/img` (por lotes: `--lote N`) |

## B. Actualización semanal (≈10 a 15 minutos de trabajo; el rastreo en sí son ~2 minutos por sesión nueva)

1. `python scraper/estado.py` para ver la fecha del último dato.
2. `votos --from <fecha del último dato> --to <hoy>`; correr; importar; `python scraper/resolver_alias.py` (une nombres escritos distinto; si aparece algún AMBIGUO o un exdiputado nuevo, revisarlo).
3. `iniciativas` (sin `--tokens`: toma las citadas en votos que aún no tienen detalle); correr; importar. Así llegan los decretos nuevos con su número oficial.
4. Cada 2 semanas o cuando salgan decretos: `decretos`; correr; `cruzar_decretos.py` (solo completa lo que el paso 3 no resolvió).
5. Si `estado.py` muestra leyes nuevas sin resumen: `pdf`; correr; `importar_pdf.py`; redactar (ver `resumenes-leyes.md`); `python scraper/resumenes_leyes.py`.
6. Cada mes: `roster`; correr; `importar_roster.py`. Si hay diputados sin foto local: `imagenes` por lotes.
7. `python scraper/export_web.py`, comprobar (sección D), `empaquetar_artefacto.py` y publicar (`web-y-publicacion.md` §4).
8. Decir al usuario qué cambió en números concretos (sesiones nuevas, leyes nuevas, decretos nuevos) y dar el enlace.

## C. Ampliar a otros años (ejemplo: 2024 y 2025 de la legislatura 2024-2028)

- **Estimar con datos, no a ojo**: sesiones del rango (tabla por año en `sitio-congreso.md` §6) × ~11.5 votaciones por sesión × ~4 s por votación. 2024-2025 = 132 sesiones → ~1,500 votaciones → 1 h 45 min a 2 h 30 min, sin intervención del usuario pero con la pestaña abierta. Dar la cifra al usuario y esperar su visto bueno antes de empezar.
- **Por bloques**: un año a la vez (`--from 2024-01-01 --to 2024-12-31`), exportando e importando al terminar cada uno; si el panel se cierra, solo se repite el bloque en curso (lo guardado en IndexedDB se conserva).
- **Después** (así se hizo con 2024-2025): `resolver_alias.py`; `iniciativas --solo-listadas --sondeos 8` (101 iniciativas en ~9 min; halló 87, 14 no tienen página de detalle) y luego las más antiguas con `--sondeos 12` (20 intentadas, 4 halladas, ~8 min); `decretos` y `cruzar_decretos.py`; `pdf` (53 PDF en ~10 min, más 9 que solo citaban mociones de urgencia) y redactar los resúmenes (~1 h); `export_web.py`. Resultado: 2,639 votaciones y 115 leyes, 65 con decreto y 84 con resumen.
- **Qué aporta un año nuevo**: las leyes de ese año (2024: 21 decretos, 2025: 24). NO completa leyes de años posteriores: el primer y el segundo debate no se votan.
- **Empezar en la fecha de instalación de la legislatura** (2024-01-14, no 01-01) y excluir la sesión de cierre de la anterior (`sesiones_excluidas`).
- **Qué NO mejora**: el bloque sigue siendo el actual (el sitio no guarda historia). Aumentarán los exdiputados (sin foto ni bloque). Hay que avisarlo antes de publicar, y explicar que la solicitud de información pública es el camino para el bloque por fecha.
- **Web**: pasará de ~320 KB a poco más de 1 MB; añadir selector de año.

## D. Antes de publicar

- `estado.py` limpio: 0 votaciones sin sesión, 0 con número raro de diputados, sesiones leídas = sesiones del rango, y las leyes sin resumen son las esperadas.
- Cuadre de una votación conocida (ver `datos.md` §5) y, si hay una ley nueva, comparar su resultado con la prensa o con el Congreso.
- Abrir en el navegador una ley con decreto, una en trámite y una votación, y leer el DOM (conteos de filas, imágenes cargadas, «Presentes N de 160»).
- Confirmar que el aviso «bloque actual» y la nota de «resumen con IA» siguen en pantalla.

## E. Si algo falla

| Síntoma | Causa probable | Qué hacer |
|---|---|---|
| `state: 'detenido'`, `err` empieza con «BLOQUEADO» | Incapsula bloqueó | Parar. No reintentar de inmediato ni abrir otra pestaña en paralelo; avisar al usuario; esperar y retomar más tarde con el mismo código |
| `err`: «Sin filas de votos en la votación N» | la estructura de la página cambió, o esa votación está vacía | abrir `/detalle_de_votacion/N/<sesión>` en otra pestaña, comparar las tablas `#congreso_*` y ajustar `js/votos.js` |
| «Preview not found», `browserOpen: false` | el panel se cerró | `preview_start` con `url`; volver a lanzar el MISMO código (retoma desde IndexedDB) |
| `P.n` o `P.votaciones` no avanza | pestaña oculta, navegó a otra página o se recargó | `tabs_select`; mirar `location.href` y `window.__prog`; relanzar |
| `importar_*` dice «no es un resultado de…» | tomó otro archivo guardado | pasar la ruta que dio el mensaje de la herramienta |
| La respuesta de `__export()` entró al contexto | resultado pequeño sin relleno | usar el `__export()` de los scripts de `scraper/js` (rellenan hasta 150,000 caracteres) |
| Ley sin título | su iniciativa no sale en el listado de 500 | `iniciativas --tokens N`; si no la encuentra, queda sin título (en 2024-2026 quedaron 24 de 115) |
| `iniciativas` se queda mucho en una sola iniciativa | búsqueda de una iniciativa no listada (cada intento cuesta ~2 s) | usar `--solo-listadas` y `--sondeos 8`; las no halladas se dejan |
| Un diputado aparece como «EX-DIPUTADO» y no lo es | su nombre cambió (apellido de casada) | `resolver_alias.py` |
| Decreto equivocado | quedó el cruce por fecha | correr `iniciativas` e importar: el detalle oficial pisa y avisa «CORREGIDO» |
| Web vacía al abrir `#/votaciones` | estado declarado después de `route()` | ver `web-y-publicacion.md` §5 |
| `UnicodeEncodeError` en la consola | consola de Windows en cp1252 | `PYTHONIOENCODING=utf-8` |
