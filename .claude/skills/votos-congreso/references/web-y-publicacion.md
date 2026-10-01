# La web y su publicación

Contenido: 1. Cómo está hecha · 2. Pantallas y lo que el usuario pidió · 3. Cómo cambiarla y probarla · 4. Publicar y compartir · 5. Errores ya cometidos · 6. Ideas pendientes

## 1. Cómo está hecha

- Una sola página, `web/index.html`, sin dependencias externas: HTML + CSS + JavaScript propios. Los datos van incrustados (`window.DATA`, entre `/*DATA*/` y `/*END*/`), así que abre con doble clic (`file://`) y desde cualquier servidor. `export_web.py` solo reemplaza esa región; el resto del archivo se edita a mano.
- Estilo copiado de gasolinasogt.com (pedido del usuario): fondo azul marino con degradado y brillos, tarjetas de vidrio esmerilado (fondo `rgba(255,255,255,.08)`, borde `rgba(255,255,255,.16)`, `backdrop-filter: blur(24px) saturate(1.6)`, radio 26 px), navegación en píldoras, fuente del sistema. Colores: azul `#4997D0` (títulos y acentos), marino `#1a2a4a`, violeta `#6c5ce7`; voto: a favor `#00b894`, en contra `#ff6b6b`, ausente `#7d8499`, licencia `#fdcb6e`, abstención `#a29bfe`. Modo claro automático con `prefers-color-scheme`. Todos los colores son variables CSS (`--F`, `--C`, `--gt-blue`...).
- Navegación por hash, sin recargar: `#/bloques`, `#/bloque/<id>`, `#/leyes`, `#/ley/<clave>`, `#/votacion/<id>`, `#/diputados`, `#/diputado/<índice>`. El menú tiene SOLO tres pestañas: Partidos, Leyes y Diputados. `#/votaciones` ya no existe y redirige a `#/leyes` (los enlaces viejos siguen funcionando). El botón «atrás» del navegador funciona y los enlaces se pueden compartir.
- Funciones de pantalla: `vBloques`, `vBloque`, `vLeyes`, `vLey`, `vVotacion`, `vDiputados`, `vDiputado` (`vVotaciones`, el listado general de votaciones, sigue en el código pero sin pestaña). Auxiliares: `cnts` (conteo), `bar` (barra de colores), `sum` (texto de conteos), `pres` («Presentes N de 160»), `photo`/`logo` (con iniciales si falta la imagen), `chips`, `vtxt` (texto buscable de una votación).

## 2. Pantallas y lo que el usuario pidió (cada punto salió de una petición suya)

- **Logos de partido**: vidrio esmerilado estilo iOS (pedido del usuario; el marco arcoíris del barril de gasolinasogt.com se probó y NO le gustó): tile translúcido con degradado, borde de 1 px, brillo superior (`::after`), sombra suave y `backdrop-filter`, y el logo sobre una placa blanca redondeada. Los PNG de `web/img/b/` están sin fondo blanco exterior (lo quita `js/imagenes.js` por relleno desde los bordes), por eso sobre la placa blanca se ven igual que los originales. Si se bajan logos de nuevo, subir el `?v=` de `img/b/<id>.png` (y en `empaquetar_artefacto.py`) para vencer la caché.
- **Partidos** (portada): tarjeta por bloque con logo, nº de diputados y barra del voto agregado; al entrar, las fotos de sus diputados con % a favor y % de ausencia. Agrupar por partido, con logo y foto, fue pedido explícito.
- **Leyes**: una tarjeta por ley (decreto o «Sin decreto», título, iniciativa, fecha, resultado de la votación decisiva), con búsqueda y filtros «Con decreto / Sin decreto».
- **Detalle de la ley** con jerarquía de títulos: «Detalle de la ley» (Número, Título, Iniciativa, Votada) → caja **Propósito** → «Votaciones de la ley» en etapas numeradas 1 Trámite previo, 2 Debate, 3 Articulado (un bloque por artículo, con sus enmiendas dentro; «Preámbulo» y «Artículo nuevo» aparte), 4 Redacción final. Cada votación muestra su etiqueta, su **fecha**, «**Presentes N de 160**» y la barra de voto; al hacer clic se abre el detalle por partido y diputado. En el encabezado de cada etapa va el rango de fechas.
- **Sin pestaña de votaciones** (el usuario la quitó: «esos procesos ya están en leyes»): lo procedimental sin ley (orden del día, actas, mociones, elecciones de magistrados) ya no se puede consultar en la web; sigue en la base de datos. Idea si lo pide: sección «Elecciones y nombramientos» (la sesión del 08/10/2024 tuvo 470 votaciones de magistrados de Apelaciones). La búsqueda por número de decreto, iniciativa o nombre vive en **Leyes**. El enlace de vuelta desde una votación sin ley usa `history.back()`.
- **Detalle de una votación**: agrupado por partido (logo y resumen), con la foto de cada diputado y su voto con aro de color; filtro por nombre, partido o tipo de voto; enlace de vuelta a su ley.
- **Diputados / ficha**: foto, bloque, barra y conteo, historial de votos con los mismos filtros (por defecto, solo leyes).
- Pie: aviso de que los datos son del Congreso, que el bloque mostrado es el actual y que no es un sitio oficial.

## 3. Cómo cambiarla y probarla

1. Datos: `python scraper/export_web.py` (imprime diputados, votaciones y leyes). Interfaz: editar `web/index.html` fuera de la región de datos.
2. Servidor local: `cd web && python -m http.server 8080` (en segundo plano) y abrir `http://127.0.0.1:8080/index.html` en OTRA pestaña, nunca en la que corre una extracción.
3. Probar con el navegador antes de publicar, leyendo el DOM en vez de fiarse de un vistazo: por ejemplo, abrir `#/ley/d22-2026` y comprobar que hay 19 filas `.lrow`, 4 etapas y que «Presentes 149 de 160» aparece en la redacción final; contar `img.ph` cargadas en `#/bloque/45` (18).
4. Si el navegador no recarga: un cambio solo de hash no recarga el script, así que `location.reload()` o añadir `?v=N` a la URL. Las imágenes con `loading="lazy"` no cargan en una pestaña en segundo plano: traerla al frente (`tabs_select`) antes de contarlas.
5. La vista previa de archivos de la app abre `file://` como copia estática: carga los datos (están incrustados) pero no las imágenes relativas. No es un fallo.

## 4. Publicar y compartir

1. `python scraper/export_web.py`
2. `python scraper/empaquetar_artefacto.py <carpeta_temporal>` genera `<carpeta_temporal>/index.html`: quita `<!doctype>/<html>/<head>/<body>` (el artefacto pone su propio esqueleto), pone `<title>Votos del Congreso</title>`, reordena los temas (oscuro por defecto; claro con `prefers-color-scheme` y `data-theme`) e incrusta las 177 imágenes como `data:` URI (el archivo final pesa ~4.5 MB con los datos de 2024-2026; el límite del artefacto es 16 MB).
3. Herramienta `Artifact` con `file_path` = ese archivo y `label` = lo que cambió. **Con la misma ruta se mantiene el mismo enlace**; si es una conversación nueva, primero `action: read` del enlace y publicar con `url: https://claude.ai/artifact/K7knNdjd27NZFDPxbsSM6x`. Si la primera llamada responde «repite la llamada idéntica una vez», se repite tal cual.
4. Quién lo ve lo decide el usuario desde el menú Compartir de la página; la herramienta no lo cambia. Al terminar, avisar si cambió (en esta sesión apareció como «Cualquiera con el enlace»). Antes de recomendar compartir, recordar los avisos: bloque actual y no histórico, resúmenes hechos con IA.
5. Alternativas de hosting si algún día se quiere dominio propio: la carpeta `web/` es estática (GitHub Pages, Netlify, Vercel). No hace falta salvo que el usuario lo pida.

## 5. Errores ya cometidos (no repetir)

- Cargar los datos con `fetch('data.json')`: no funciona con doble clic (`file://`) y la página se quedaba en «Cargando…». Los datos van incrustados.
- Declarar `const ST = {}` DESPUÉS de la primera llamada a `route()`: si el enlace abre directo en `#/votaciones`, la vista sale vacía (error de «cannot access before initialization»). El estado se declara arriba, junto a `let D,V,...`.
- `[...str.keys()]` sobre un string: no existe; usar `[...Array(str.length).keys()]`.
- Plural «votaciónes»; y `<b>` dentro de `.vitem small` que quedaba en línea aparte (se arregló con `.vitem small b{display:inline}`).
- Escribir un archivo con Python y fallar a mitad de escritura (error de codificación en la consola de Windows) lo deja vacío: usar `PYTHONIOENCODING=utf-8` y la herramienta Write, y comprobar el tamaño después.
- Pegar JavaScript largo con tildes en el shell con heredoc: puede romperse; crear el archivo con Write. En un script de Python dentro de un heredoc, `\b` se convierte en un retroceso invisible: usar `chr(92)` o escribir el archivo con Write (un regex `\b[56]\d{3}\b` falló en silencio así).
- **Recuadro transparente al pasar el mouse**: un elemento con `backdrop-filter` que además se mueve (`transform: translateY`) en `:hover` deja un recuadro suelto en Chrome. Los controles pequeños (menú, filtros, buscador) no llevan `backdrop-filter`, y el hover cambia color y borde, no posición; las tarjetas tampoco se mueven.
- **Caché de imágenes**: si cambia un PNG con el mismo nombre, el navegador sigue mostrando el viejo. Subir el `?v=` de `img/b/<id>.png` en `web/index.html` y en `empaquetar_artefacto.py` (hoy `?v=3`).
- **Capas de un marco con pseudo-elementos**: dentro de un contexto de apilamiento, un `::before` con `z-index:-1` se pinta ENCIMA del fondo del propio elemento; si el fondo oscuro va en el elemento, el arcoíris lo tapa. El oscuro debe ir en un `::after` posterior.
- **Estilos que el usuario rechazó** (no volver a proponerlos): logo de partido sobre tarjeta blanca con marco arcoíris del barril de gasolinasogt.com, y el mismo marco con logo transparente. Quedó el vidrio esmerilado estilo iOS. Ante un rechazo de estilo, volver al estado anterior que le gustaba y proponer algo distinto, no parchear sobre lo rechazado.

## 6. Ideas pendientes (ya hay datos, falta mostrarlos)

- Línea de tiempo de la ley (`iniciativa_detalle.pasos`): presentada → conocida por el Pleno → dictamen → debates → decreto → enviado al Ejecutivo → sancionado → publicado → vigente, y los diputados ponentes («quién presentó la ley»).
- Selector de año cuando se carguen 2024-2025; hora de cada votación (`votaciones.hora`).
- Mayoría requerida y si se alcanzó (simple, absoluta, calificada) en la redacción final.
- Bloque por fecha: depende de la respuesta a la solicitud de información pública.
