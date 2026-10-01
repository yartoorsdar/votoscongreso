---
name: votos-congreso
description: Extrae, ordena y publica los votos de los diputados del Congreso de Guatemala (congreso.gob.gt) - votaciones del Pleno sesión por sesión, voto de cada diputado y de su bloque (partido), leyes y decretos con sus etapas, resumen del propósito de cada ley y la web compartible. Úsala SIEMPRE que el usuario hable de votos, votaciones, diputados, bloques o partidos del Congreso de Guatemala (Guatemalan Congress votes), de un decreto o una iniciativa de ley (por ejemplo "decreto 22-2026", "iniciativa 6852"), de actualizar o ampliar los datos (sesiones nuevas, "agrega 2024 y 2025", otro año), de bajar, leer o resumir PDF de iniciativas, de la web o el enlace de votos, de cuánto tarda o cada cuánto hay que extraer, o de automatizar o scrapear congreso.gob.gt, aunque no nombre la skill.
---

# Votos del Congreso de Guatemala

Sistema que muestra cómo votó cada diputado y cada bloque en el Pleno, agrupado por partido, por ley y por votación. Se alimenta del sitio oficial (www.congreso.gob.gt), guarda todo en SQLite y publica una web de una sola página con enlace compartible.

Estado al 2026-10-01 (para el dato vivo, correr `python scraper/estado.py`): legislatura 2024-2028 completa hasta el 29/09/2026. 186 sesiones, 2,639 votaciones, 422,219 votos, 115 leyes (65 con decreto, 84 con resumen), 160 diputados actuales y 3 exdiputados. Web publicada: https://claude.ai/artifact/K7knNdjd27NZFDPxbsSM6x

Todos los comandos se corren desde la raíz del proyecto. Los detalles están en `references/`; aquí va lo que hay que tener presente siempre.

## Reglas (con su porqué)

1. **No se esquiva la protección anti-bots.** El sitio usa Incapsula: bloquea `curl`, `requests` y Playwright. Solo funciona el navegador integrado de la app, con una petición a la vez y pausa de 1.5 a 3 s. Si hay bloqueo, se detiene y se avisa; no se reintenta en bucle ni se abren pestañas en paralelo. Es el sitio de una institución pública y la extracción es de buena fe y a ritmo humano.
2. **Cero descargas de archivos y cero servidores locales.** Cada descarga obliga al usuario a dar clic en «Guardar» (fueron ~60) y una página del Congreso no puede conectarse a `127.0.0.1`. Los datos salen como resultado de `javascript_tool`; si es grande, la herramienta lo guarda sola en disco y `scraper/entrada.py` lo lee. El usuario no debe tener que tocar nada durante una extracción.
3. **La base es la fuente de verdad y todo es reanudable e idempotente.** Se puede repetir cualquier importación sin duplicar; la web se regenera siempre desde la base (`export_web.py`), nunca se edita su región de datos.
4. **Una pestaña de trabajo, intocable.** El código corre dentro de una pestaña del Congreso; navegarla lo mata. Para ver la web se usa otra pestaña.
5. **Probar chico antes de lanzar lo grande, y comprobar contra algo conocido.** Antes de un rastreo largo, una sesión; después de importar, cuadrar números (presentes + ausentes + licencias = 160; la redacción final del 22-2026 fue 148 a favor, 1 en contra, y coincide con la prensa).
6. **No inventar.** Sin fuente no hay resumen, sin bloque histórico no se finge uno, y lo que es heurística se rotula. Los límites se dicen antes de compartir: el bloque mostrado es el ACTUAL (el sitio no guarda historia), los resúmenes son hechos con IA y describen lo propuesto, y la clasificación de votaciones sale del texto de la pregunta.
7. **Estimar y confirmar antes de trabajos largos.** Calcular el tiempo con datos (sesiones × ~11.5 votaciones × ~4 s), dar opciones con una recomendación y esperar el visto bueno. Aprobado, ejecutar sin pedir más y reportar en hitos.

## Qué receta usar

| El usuario pide… | Receta | Detalle |
|---|---|---|
| Actualizar con sesiones nuevas (semanal) | `votos` → `iniciativas` → (`decretos`) → `export_web` → publicar | `references/ampliar-y-actualizar.md` B |
| Agregar años (otra legislatura o más atrás) | estimar → `votos` por año → `resolver_alias` → `iniciativas` → resúmenes | idem C |
| «¿Por qué no sale el decreto X?» / datos de una ley | `iniciativas --tokens N` (decreto oficial, ponentes, línea de tiempo) | `references/datos.md` §3 |
| Resumen del propósito de una ley | `pdf` → leer extracto → redactar | `references/resumenes-leyes.md` |
| Cambiar la web, el diseño o los filtros | editar `web/index.html`, probar, republicar | `references/web-y-publicacion.md` |
| Compartir / enlace para socios | `empaquetar_artefacto.py` + Artifact sobre el mismo archivo | idem §4 |
| Fotos, logos o diputados nuevos | `roster` / `logos` / `imagenes` | `references/ampliar-y-actualizar.md` A |
| «¿Cada cuánto extraer?» / «¿cuánto tarda?» | cadencia y fórmula | `references/sitio-congreso.md` §6 y recetas C |
| Algo falló | tabla de síntomas | `references/ampliar-y-actualizar.md` F |

## Cómo correr un trabajo en el navegador (resumen; ver recetas A)

1. `python scraper/preparar_js.py <votos|iniciativas|decretos|pdf|roster|logos|imagenes> [opciones]` imprime el código con sus parámetros.
2. Pegarlo en `javascript_tool` sobre la pestaña del Congreso (responde «iniciado»; sigue corriendo en la página).
3. Seguir con `({...window.__prog})` (cada llamada expira a los ~45 s). Se detiene con `window.__stop = true`.
4. Al terminar (`state: 'terminado'`): `await window.__export()` como última expresión. La respuesta se guarda sola en disco y trae la ruta.
5. `python scraper/importar_<tipo>.py [ruta]` (sin ruta usa la más reciente). Luego `python scraper/estado.py`.

Si el panel del navegador se cierra («Preview not found»), reabrir con `preview_start` y una URL del Congreso (`navigate` solo no basta) y volver a lanzar el mismo código: retoma desde lo guardado en IndexedDB.

## Cómo trabajar con este usuario

- Español claro y directo, sin jerga; la primera frase dice el resultado y luego el porqué. Cifras concretas y enlaces o rutas de lo entregado.
- Hace preguntas de viabilidad antes de comprometerse («¿cuánto tarda?», «¿se puede automático?»). Responder primero con datos reales y esperar su decisión; si dice «solo es pregunta, no programes», no tocar nada.
- Quiere procesos que corran solos: ningún paso que requiera sus clics. Si algo necesita su acción (compartir el artefacto, enviar la solicitud de información, permisos de la app), decirlo claro.
- Prefiere ver el resultado en la web real: tras cada cambio de interfaz, probarlo en el navegador y publicarlo en el MISMO enlace (el artefacto), indicando qué cambió.
- Pide mejoras de a una (agrupar por partido, fechas, presentes, filtro de leyes, resumen, quitar una pestaña, pulir logos). Hacer lo pedido, comprobarlo con datos y mencionar en una línea lo que aún no está.
- En lo visual da referencias concretas (una captura, una página) y rechaza sin rodeos lo que no le gusta. Para estilo: abrir la referencia real y leer su CSS, probar en el navegador con captura antes de publicar, y si rechaza algo, deshacerlo del todo y proponer otra dirección en lugar de retocar lo rechazado. Cada cambio se publica en el mismo enlace.
- Corregir de frente cuando algo que dije resultó falso (pasó con «cargar 2025 completa las leyes de 2026»): decirlo en la primera frase, con el dato que lo demuestra, y ajustar la skill.
- El usuario comparte el enlace con sus socios: antes de recomendarlo, repetir los avisos (bloque actual, resúmenes con IA, datos solo de los años cargados).
- Al aprender algo no obvio del sitio o del flujo, guardarlo en la memoria del proyecto.

## Mapa de archivos

- `references/sitio-congreso.md`: páginas del Congreso, trampas de los datos, qué NO sirve, ritmo y cadencia.
- `references/datos.md`: tablas, clasificación de votaciones, cómo se arma una ley y su decreto, formato de los datos de la web, comprobaciones.
- `references/resumenes-leyes.md`: cómo leer los PDF y escribir los resúmenes.
- `references/web-y-publicacion.md`: la web, lo que el usuario pidió, publicar y errores ya cometidos.
- `references/ampliar-y-actualizar.md`: recetas paso a paso, estimaciones y qué hacer si algo falla.
- `scraper/js/*.js`: trabajos que corren dentro del navegador. `scraper/*.py`: preparar, importar, exportar, empaquetar y reportar estado.
- `solicitud_informacion_publica.md`: solicitud lista para pedir al Congreso el histórico y los cambios de bloque (la vía oficial y más completa; la envía el usuario).

## Requisitos

Python 3 (solo biblioteca estándar), las herramientas del navegador integrado (`mcp__Claude_Browser__*`) y la herramienta `Artifact` para publicar. No hacen falta Playwright ni `pdftotext`.
