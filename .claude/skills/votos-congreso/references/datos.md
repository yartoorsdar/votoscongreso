# Datos: base SQLite, reglas de organización y formato de la web

Contenido: 1. Mapa del proyecto · 2. Tablas · 3. Cómo se ordena (clasificación, leyes, decretos) · 4. Datos que lee la web · 5. Comprobaciones de cordura

## 1. Mapa del proyecto (comandos desde la raíz del proyecto)

```
data/votos.db                  base SQLite: la fuente de verdad (se crea y migra sola con scraper/db.py)
data/pdf_origen.json           iniciativa -> URL del PDF oficial          (lo llenan decretos.js / iniciativas.js)
data/pdf_extracto.json         iniciativa -> texto de su exposición      (importar_pdf.py)
data/resumenes.json            ley -> resumen del propósito              (scraper/resumenes_leyes.py)
data/imagenes_origen.json      URLs de fotos y logos en el Congreso      (importar_roster.py)
web/index.html                 la web (una sola página) con los datos incrustados
web/img/b/<bloque>.png  web/img/d/<diputado>.jpg  web/img/index.json   fotos y logos propios (240 y 160 px)
scraper/js/*.js                trabajos que corren DENTRO del navegador
scraper/preparar_js.py         arma el código de cada trabajo con sus parámetros
scraper/importar_*.py, cruzar_decretos.py   pasan el resultado a la base
scraper/export_web.py          base -> datos incrustados en web/index.html
scraper/empaquetar_artefacto.py  web -> un solo archivo con imágenes para publicar
scraper/estado.py              reporte de estado (qué hay, qué falta)
```

## 2. Tablas de `data/votos.db`

| Tabla | Clave | Contenido |
|---|---|---|
| `sesiones` | `id` (id del Congreso) | tipo (Ordinaria/Solemne/Extraordinaria), número, descripción, `fecha` ISO, `scraped` (1 = sus votaciones ya se leyeron) |
| `votaciones` | `id` | `sesion_id`, `numero`, `pregunta`, `fecha` ISO, `hora` (HH:MM:SS; solo en lo extraído después de 2026-10-01), `iniciativa` (texto «6493-6719» sacado de la pregunta), `decreto`, `scraped` |
| `votos` | (`votacion_id`, `nombre_norm`) | `diputado_nombre` tal cual lo publica el Congreso, `estado` (PRESENTE/AUSENTE/LICENCIA / EXCUSA), `voto` (A FAVOR/CONTRA/AUSENTE/LICENCIA / EXCUSA/ABSTENCIÓN) |
| `diputados` | `id` (id del Congreso) | `nombre`, `nombre_norm`, `bloque_id`, `bloque` (el ACTUAL) |
| `alias_nombre` | `nombre_norm` | nombre con que el Congreso escribió a un diputado en el pasado -> `diputado_id` actual (`resolver_alias.py`) |
| `sesiones_excluidas` | `id` | sesiones que no se importan (la 41167, cierre de la IX legislatura) y por qué |
| `bloque_anio` | (`diputado_id`, `anio`) | bloque observado en un año; hoy solo 2026 (el sitio no da historia, ver `sitio-congreso.md` §3) |
| `decretos` | `numero` («22-2026») | `fecha` de emisión, `resumen` (nombre de la ley), `iniciativas` (números separados por coma) |
| `iniciativas` | `numero` | fecha en que la conoció el Pleno y nombre, del listado de las 500 más recientes |
| `iniciativa_detalle` | `numero` | título, ponentes (JSON), `pasos` (JSON: paso, fecha, estado), notas (JSON), decreto, fecha del decreto, PDFs |

Convenciones: todas las fechas son ISO `YYYY-MM-DD`; las importaciones son idempotentes (`INSERT OR REPLACE`, o `ON CONFLICT DO UPDATE` en `votaciones` para no pisar `decreto`); `db.conn()` crea tablas y agrega columnas nuevas solas.

## 3. Cómo se ordena la información

**Nombre normalizado** (`db.norm`): sin tildes, minúsculas, solo letras a-z, palabras ordenadas. Es la clave que une «Apellidos Nombres» (votos) con «Nombres Apellidos» (listas). Cuando el Congreso escribió distinto a la misma persona en otra fecha, `python scraper/resolver_alias.py` (se corre tras cada importación de votos) la une a su diputado actual si un conjunto de palabras contiene al otro, comparten 3 o más y hay un solo candidato, e imprime lo que une y los ambiguos para revisar. `export_web.py` y `estado.py` respetan esos alias; lo que queda sin unir son exdiputados («EX-DIPUTADO», sin foto).

**Clase de cada votación** (`export_web.py`, campo `t`), por el texto de la pregunta:
- `L` ley o decreto: aprobación en primer/segundo/tercer/único debate, redacción final, ratificar un decreto, objeciones a un decreto.
- `A` artículos y enmiendas: artículo, enmienda, preámbulo, título, capítulo, fondo de revisión (sin «redacción final»).
- `P` trámite y otros: orden del día, actas, mociones, dictámenes, límite de tiempo, proyectos de acuerdo.
En la web, «Leyes y decretos» (`L`) es el filtro por defecto porque el usuario quiere ver lo que decide una ley, no el proceso.

**Etapa dentro de una ley** (campo `e`), en el orden del procedimiento: `T` trámite previo (moción, urgencia, dictamen) → `D` debate → `A` articulado → `F` redacción final. En el articulado se agrupa por artículo (`ar`: número; 0 = preámbulo; vacío = «artículo nuevo»); las enmiendas quedan dentro del artículo al que se refieren. Los grupos salen en el orden en que realmente se votaron (el preámbulo suele votarse al final).

**Etiqueta** (`lb`): la pregunta sin el sufijo «DEL PROYECTO DE DECRETO QUE DISPONE APROBAR LA INICIATIVA DE LEY n», en minúscula con la primera mayúscula.

**Qué es una ley** (clave `k`): se buscan los números de iniciativa (`[56]\d{3}`) en la columna `iniciativa` y en el texto de la pregunta (así entran las mociones de «URGENCIA NACIONAL 6852»). Las iniciativas que aparecen juntas en una votación forman una sola ley (union-find: «6493-6719»). La clave es `d<decreto>` si la ley tiene decreto (`d22-2026`) y `i<número menor>` si no (`i6493`). Votaciones sin ninguna iniciativa (orden del día, actas) no pertenecen a ninguna ley.

**Decreto de una ley**, por orden de confianza:
1. Detalle oficial de la iniciativa (`iniciativa_detalle.decreto`, fila «Número de Decreto»): `importar_iniciativas.py` lo fija en `decretos.iniciativas` y `votaciones.decreto` y avisa si corrige algo.
2. Cruce por fecha (`cruzar_decretos.py`): plan B para decretos sin iniciativa enlazada.
3. Ratificaciones de «decreto gubernativo n-aaaa»: por el texto de la votación.
Una ley sin decreto se muestra como «Sin decreto todavía» (en trámite, o el decreto aún no se emitió).

**Título de una ley**: nombre del decreto (`decretos.resumen`); si no hay decreto, el de la iniciativa en `iniciativas` (sin el prefijo «Iniciativa que dispone aprobar»). Algunas iniciativas no salen en el listado y quedan sin título (se muestran como «Iniciativa 6750»).

**Resumen del propósito, PDFs, ponentes y línea de tiempo**: ver `resumenes-leyes.md`. Los resúmenes se buscan por la clave de la ley y, si esta cambió (una ley sin decreto `i6702` pasa a `d2-2026` cuando se le asigna), por `i<número de iniciativa>`; los títulos salen de `decretos`, de `iniciativas` (listado) o de `iniciativa_detalle`. `iniciativa_detalle` ya guarda ponentes y pasos, pero la web todavía NO los muestra (idea pendiente).

## 4. Datos que lee la web (`window.DATA` dentro de `web/index.html`, entre `/*DATA*/` y `/*END*/`)

```
d:   [{id, n, b, bi}]            diputados: id, nombre, bloque, id del bloque (exdiputados: id negativo, bi 0)
v:   [{id, f, s, n, p, i, d, t, v, k?, e?, ar?, lb?}]
        id votación · f fecha · s sesión («Ordinaria 47») · n nº de pregunta · p pregunta · i iniciativa · d decreto · t clase L/A/P
        v = cadena con un carácter por diputado, en el orden de `d`: F a favor, C en contra, A ausente, L licencia, B abstención, ? sin dato
        k clave de ley · e etapa T/D/A/F · ar artículo · lb etiqueta
img: {b:{id:1}, d:{id:1}}        qué logos/fotos existen en web/img
dec: {numero: nombre}            decretos
ley: {clave: {d, f, i, t, r?, rf?, pdf[{i,u}]}}   d decreto · f fecha de la última votación · i iniciativas · t título · r resumen · rf fuente del resumen (pdf|titulo)
```
Se regenera siempre con `python scraper/export_web.py`; nunca se edita a mano. Una votación ocupa ~200 bytes: con 2024-2025 la web pasaría de ~320 KB a poco más de 1 MB.

## 5. Comprobaciones de cordura (después de importar y antes de publicar)

- `python scraper/estado.py` debe mostrar: sesiones leídas = sesiones del rango, 0 votaciones sin sesión, 0 votaciones con número raro de diputados, `votos` = votaciones × ~160.
- En una votación: presentes + ausentes + licencias = 160 (159 si hay vacante). Ejemplo conocido: decreto 22-2026, redacción final = 148 a favor, 1 en contra, 5 ausentes, 6 con licencia (149 presentes) y coincide con lo publicado por la prensa.
- Una ley con decreto debería tener votación de clase `F` o `D` el día de la fecha del decreto.
- Si una importación repetida cambia los totales, algo no es idempotente: investigar antes de seguir (la prueba de 2026-10-01 con la sesión del 29/09 dio 3,680 filas idénticas).
