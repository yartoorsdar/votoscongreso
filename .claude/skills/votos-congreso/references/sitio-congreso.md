# El sitio del Congreso (www.congreso.gob.gt): mapa, trampas y límites

Contenido: 1. Protección anti-bots · 2. Qué páginas hay · 3. Particularidades de los datos · 4. Cómo salen los datos del navegador · 5. Lo que NO sirve (ya probado) · 6. Ritmo y cadencia

## 1. Protección anti-bots (Incapsula / Imperva)

- `curl`, `requests` y Playwright/Chromium automatizado reciben una página «Request unsuccessful. Incapsula incident ID». Se probó: bloqueó ya la primera página.
- El navegador integrado de la app (`mcp__Claude_Browser__*`) sí carga el sitio: es un navegador normal. Dentro de una pestaña del Congreso, `fetch()` de rutas relativas funciona porque es el mismo origen y lleva las cookies de la sesión.
- Regla: no se intenta esquivar la protección (nada de cambiar user-agent, rotar IP ni resolver desafíos). Ritmo lento, una petición a la vez, y si hay bloqueo se detiene y se avisa. Cada script de `scraper/js/` ya lo hace: `get()` lanza un error si ve «Incapsula» o un HTTP distinto de 200.
- GitHub Actions u otros servidores en la nube (IPs de centro de datos, sin pantalla) lo más probable es que sean bloqueados. La extracción corre en el navegador de la app; en la nube solo cabe lo que no toca el sitio (importar, analizar, generar y publicar la web).
- El panel del navegador puede cerrarse en medio de un trabajo (pasó): las herramientas responden «Preview not found» y `tabs_context` dice `browserOpen: false`. `navigate` solo NO lo reabre (falla con «denied or failed»); `preview_start` con `url` sí. El trabajo en curso se pierde, pero lo ya guardado en IndexedDB queda: se vuelve a lanzar el mismo código y retoma.

## 2. Páginas y qué trae cada una

Las tablas vienen COMPLETAS en el HTML crudo (DataTables solo las pagina en el cliente), salvo donde se indica.

| Página | Qué trae | Cómo leerla |
|---|---|---|
| `/seccion_informacion_legislativa/votaciones_pleno` | Todas las sesiones del Pleno (1,086 desde 2009): tipo, número, descripción `No. 47, Fase 1, Fecha 29/09/2026 12:53:56` y enlace `eventos_votaciones/<sesión>` | `fetch` + `table tbody tr` |
| `/eventos_votaciones/<sesión>` | Las preguntas votadas en la sesión: texto, nº de pregunta, fecha y hora, enlace `detalle_de_votacion/<votación>/<sesión>` | `fetch` |
| `/detalle_de_votacion/<votación>/<sesión>` | El voto de cada diputado en 4 tablas: `#congreso_a_favor`, `#congreso_contra`, `#congreso_votos_nulos` (ausentes), `#congreso_licencia`. Columnas: nombre («Apellidos Nombres»), estado (`PRESENTE`/`AUSENTE`/`LICENCIA / EXCUSA`), voto | `fetch` |
| `/` (portada) | Los 160 diputados actuales en tarjetas: `perfil_diputado/<id>`, nombre, enlace de bloque `perfil_bloques/<id>/<año>`, foto en miniatura `img[data-src]` | `fetch` (HTML crudo) |
| `/buscador_diputados` | Los 160 nombres, armados con JavaScript | Solo DOM vivo; con `fetch` devuelve 0. No hace falta: la portada basta |
| `/buscador_bloques` | Logos de los bloques (`/assets/uploads/bloques/...`) | Solo DOM vivo (lazyload): navegar a la página y leer `img` |
| `/perfil_diputado/<id>` | Bloque actual, distrito, comisiones, iniciativas presentadas y «Historial político» (legislatura y bloque) | `fetch` |
| `/perfil_bloques/<id>/<año>` | Miembros del bloque | `fetch`. El año de la URL se IGNORA (ver §3) |
| `/seccion_informacion_legislativa/decretos` | TODOS los decretos (1,131 desde 1952): `Decreto: 22-2026 Fecha de Emisión: Martes, 22 de septiembre de 2026 Resumen: <nombre de la ley> ver detalle descargar` | `fetch` + regex sobre `body.innerText` (la regex de `js/decretos.js` reconoce 838; los más antiguos tienen otro formato) |
| `/seccion_informacion_legislativa/iniciativas` | Las 500 iniciativas más recientes: `Iniciativa: 6852 Conoció Pleno Martes, 22 de septiembre de 2026 Resumen: <nombre>`, enlace «ver detalle» (`detalle_pdf/iniciativas/<id interno>`) y PDF `info_legislativo/iniciativas/<hash>-<número>.pdf` | `fetch`; el enlace de detalle va seguido del PDF de la misma iniciativa |
| **`/detalle_pdf/iniciativas/<id interno>`** | **Detalle de una iniciativa: título, diputados ponentes, fecha de presentación y la tabla «Estado iniciativa» con cada paso y su fecha** (Dirección legislativa, Presentación pleno, Dictamen de comisión, Primer/Segundo/Tercer debate, Aprobación por artículos, Redacción final, **Número de Decreto**, Envío al ejecutivo, Sanciones, Publicación en el diario oficial, Entrada en vigencia). Más notas por paso y enlaces al PDF de la iniciativa y del decreto (`detalle_pdf/decretos/<id>`) | `fetch` + tablas (`js/iniciativas.js`) |
| `/assets/uploads/info_legislativo/iniciativas/<hash>-<n>.pdf` | Iniciativa completa (1 a 25 MB; hasta ~250 páginas en leyes grandes) | pdf.js dentro de la página (`js/pdf.js`) |
| `/assets/uploads/diputados/thumbs/...` | Foto del diputado | `fetch` + canvas (`js/imagenes.js`) |

## 3. Particularidades de los datos (todas costaron tiempo)

- **Nombres**: las votaciones usan «Apellidos Nombres»; las listas de diputados, «Nombres Apellidos». La clave de unión es `db.norm()`: sin tildes, minúsculas, solo a-z y palabras ordenadas. Hay un nombre con carácter dañado (`Ju�n`); `norm` lo tolera porque lo trata como separador.
- **Voto**: los valores son `A FAVOR`, `CONTRA` (no «EN CONTRA»), `AUSENTE`, `LICENCIA / EXCUSA`. No se han visto abstenciones, pero el código las reconoce. «Presente» = votó a favor o en contra.
- **Cantidad de filas**: normalmente 160 por votación; 159 cuando un escaño estuvo vacante. Fuera de 159 a 162 merece revisión (`estado.py` lo cuenta).
- **Iniciativa en el texto**: las preguntas dicen `INICIATIVA DE LEY 6852` o `6493-6719` (iniciativas fusionadas); las de urgencia, `URGENCIA NACIONAL 6852`. El decreto NO aparece en el texto de la pregunta.
- **Los filtros de fecha y de texto de decretos e iniciativas se IGNORAN** (probado con rangos de 2024, 2025 y `searching_text`): decretos devuelve siempre todos; iniciativas, siempre las 500 más recientes (hoy cubren los números 5790 a 6852). No sirven ventanas de fechas para llegar a lo antiguo; para una iniciativa fuera del listado hay que dar con su id interno (los ids son correlativos pero NO coinciden con el número: 6852 ↔ 6491) probando ids vecinos hasta que «Número:» coincida; `js/iniciativas.js` lo intenta y, si no puede, la deja en `noEncontradas`. En 2026 fallaron 2 de 5 buscadas (6750 y 5770); 6729, 6741 y 6749 tampoco salen en el listado.
- **El decreto sale del detalle de la iniciativa** (fila «Número de Decreto»), no de una heurística. El cruce por fecha (`cruzar_decretos.py`) queda como plan B para decretos sin iniciativa: ratificaciones de decretos gubernativos (se enlazan por el texto de la votación) y reformas sin iniciativa propia (1-2026 y 2-2026 no tuvieron).
- **Fechas**: en el listado de iniciativas, «Conoció Pleno» es la fecha de entrada al trámite (no de la votación final). En decretos, la fecha de emisión coincide con el día de la votación final. El detalle da la fecha de CADA paso (la 6418: primer debate 19/08/2025, segundo 23/09/2025, tercero 28/04/2026).
- **El primer y el segundo debate NO se votan**: el Pleno los discute sin votación nominal, así que ese día no hay votos de esa ley (se comprobó con la 6418: el 19/08/2025 solo hubo orden del día, acta y mociones). Lo que se vota es el tercer debate (o el único), los artículos, las enmiendas y la redacción final. Cargar años anteriores NO completa las leyes de un año posterior (de las 20 leyes con decreto de 2026, solo 1 tenía votos antes de 2026); aporta las leyes de esos años.
- **Frontera de la legislatura**: la X legislatura (2024-2028) se instaló el 14/01/2024. Ese día hubo dos sesiones solemnes: la 41167 (07:06, cierre de la IX legislatura, con ~100 diputados que ya no están) y la 41168 (07:55, instalación de la X). La 41167 está en la tabla `sesiones_excluidas` y ni se importa ni se vuelve a extraer. Para otro periodo, mirar la hora de la primera sesión antes de fijar `--from`.
- **Un mismo diputado con distinto nombre**: apellido de casada que aparece o desaparece («Villagrán Antón Andrea Beatriz» en 2024, «Villagrán Antón De Pantoja Andrea Beatríz» hoy) o un segundo nombre («Erick José» / «Erick José Mario»). `scraper/resolver_alias.py` los une por palabras; lo que no se une son exdiputados de verdad (en 2024-2026: 3).
- **Bloque histórico NO existe en el sitio**: `/perfil_bloques/<id>/2024` y `/2025` devuelven exactamente la misma lista que 2026 (se comparó bloque por bloque: 17 bloques, mismos miembros). El «Historial político» del perfil da un solo bloque por legislatura (X legislatura = 2024-2028), así que quien cambió de bancada dentro de la legislatura aparece con el bloque actual (por ejemplo, 38 «Independiente», varios de ellos electos con otro partido). Para el bloque de cada fecha hace falta la solicitud de información pública (`solicitud_informacion_publica.md`) u otra fuente (TSE para el partido por el que fueron electos).
- **Exdiputados**: quienes salieron durante la legislatura ya no están en la portada pero sí en los votos. Quedan como «EX-DIPUTADO (bloque no disponible)» (`export_web.py`), sin foto.
- **Decretos faltantes**: el listado del Congreso no mostró el 10-2026 ni el 21-2026 (este se menciona en una votación de objeciones).

## 4. Cómo salen los datos del navegador (sin descargas)

1. El script de `scraper/js/` corre dentro de la pestaña y deja su resultado en `window.__export()`.
2. Se llama con `javascript_tool` como última expresión: `await window.__export()`.
3. Si la respuesta es grande, la herramienta NO la mete al contexto: la guarda en `~/.claude/projects/<proyecto>/<sesión>/tool-results/` y devuelve la ruta. Según la versión del mensaje se llama `mcp-Claude_Browser-javascript_tool-<n>.txt` («exceeds maximum allowed tokens») o `toolu_<id>.json` («Output too large», con una vista previa de 2 KB que sí entra al contexto). Probado hasta 1 MB, íntegro. Los scripts rellenan con espacios hasta 150,000 caracteres para que SIEMPRE se guarde en disco.
4. `scraper/entrada.py` lee cualquiera de los dos formatos (lista `[{type,text}]`; `text` = cadena JSON + pie «Tab Context»). Los importadores (`importar_*.py`, `cruzar_decretos.py`) usan el archivo más reciente si no se les da ruta.
5. Cada llamada de `javascript_tool` expira a los ~45 s: los trabajos largos se lanzan sin `await` y se consultan con `window.__prog`.

## 5. Lo que NO sirve (para no volver a intentarlo)

- Descargar con `<a download>`/Blob: cada archivo pide «Guardar» al usuario (llegaron a ser ~60) y queda como `.tmp` hasta que lo hace.
- `fetch` desde la página del Congreso a `http://127.0.0.1:...`: falla («Failed to fetch», incluso con `mode: 'no-cors'`); la app bloquea el acceso de una página pública a la red local. Por eso no hay servidor receptor.
- Playwright/`requests`/`curl`: bloqueados por Incapsula.
- `/buscador_diputados` con `fetch`; `searching_text`, `searching_date_ini` y `searching_date_end` en decretos/iniciativas; el año en `/perfil_bloques/<id>/<año>`: se ignoran.
- Empaquetar los PDF en base64 en un solo JSON: cada uno pesa 10 MB o más. Se hace con pdf.js dentro de la página y solo sale el texto.
- Navegar la pestaña de trabajo a otra página mientras corre un script: lo mata. Para ver la web usa otra pestaña.

## 6. Ritmo y cadencia

- Pausa de 1.5 a 3 s entre peticiones, una a la vez: ~3.6 a 4 s por votación (medido: 23 votaciones en 91 s). Extracción real de 2025: 64 sesiones, 644 votaciones, 41 min; de 2024 (desde el 14/01): 67 sesiones, 1,358 votaciones, 84 min. El promedio es ~10 a 20 votaciones por sesión, pero hay sesiones con cientos (el presupuesto de octubre de 2024 llevó ~45 min por sí sola): el contador de sesiones puede no moverse un buen rato mientras el de votaciones sí.
- Una sesión se guarda en IndexedDB solo al terminar: si el panel se cierra en medio de una sesión enorme se pierde esa sesión, no las anteriores.
- El Pleno sesiona sobre todo martes (29 de 56 sesiones en 2026) y jueves (24). Hay recesos largos (12, 19 y 56 días en 2026). Con una ley o grupo de leyes aprobado cada 1 o 2 semanas, lo razonable es extraer votos **cada semana** (miércoles o viernes), decretos **cada 2 semanas** (el número sale unos días después) y diputados/bloques **cada mes**.
- Sesiones por año según el listado: 2009: 47, 2010: 58, 2011: 66, 2012: 36, 2013: 18, 2014: 20, 2015: 27, 2016: 53, 2017: 98, 2018: 85, 2019: 100, 2020: 71, 2021: 90, 2022: 89, 2023: 40, 2024: 68, 2025: 64, 2026: 56 (hasta septiembre).
- Si la pestaña queda oculta, el navegador puede frenar los temporizadores; si el ritmo cae mucho, trae la pestaña al frente (`tabs_select`).
