"""Estado del proyecto: qué hay en la base, qué falta y qué revisar. Úsalo antes y después de cada actualización.

  python scraper/estado.py
"""
import json, pathlib, re, sys
from db import conn

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8")
c = conn()


def uno(sql, *a):
    return c.execute(sql, a).fetchone()[0]


print("== Base de datos (data/votos.db)")
print(f"  sesiones: {uno('SELECT COUNT(*) FROM sesiones')} ({uno('SELECT COUNT(*) FROM sesiones WHERE scraped=1')} leídas) | "
      f"rango: {uno('SELECT MIN(fecha) FROM sesiones')} a {uno('SELECT MAX(fecha) FROM sesiones')}")
por_anio = c.execute("SELECT substr(fecha,1,4), COUNT(*), SUM(scraped) FROM sesiones GROUP BY 1 ORDER BY 1").fetchall()
print("  por año (sesiones / leídas):", ", ".join(f"{a}: {n}/{int(s or 0)}" for a, n, s in por_anio))
print(f"  votaciones: {uno('SELECT COUNT(*) FROM votaciones')} | votos: {uno('SELECT COUNT(*) FROM votos')} | "
      f"con hora: {uno('SELECT COUNT(*) FROM votaciones WHERE hora IS NOT NULL')}")
sin_sesion = c.execute("SELECT COUNT(*) FROM (SELECT v.sesion_id FROM votaciones v LEFT JOIN sesiones s ON s.id=v.sesion_id WHERE s.id IS NULL)").fetchone()[0]
raras = c.execute("SELECT COUNT(*) FROM (SELECT votacion_id, COUNT(*) n FROM votos GROUP BY 1 HAVING n NOT BETWEEN 159 AND 162)").fetchone()[0]
print(f"  votaciones sin sesión: {sin_sesion} | votaciones con un número raro de diputados (fuera de 159-162): {raras}")

print("== Diputados")
img = json.loads((RAIZ / "web" / "img" / "index.json").read_text(encoding="utf-8")) if (RAIZ / "web" / "img" / "index.json").exists() else {"b": {}, "d": {}}
sin_foto = [i for (i,) in c.execute("SELECT id FROM diputados") if str(i) not in img["d"]]
ex = c.execute("SELECT COUNT(DISTINCT v.nombre_norm) FROM votos v LEFT JOIN diputados d ON d.nombre_norm=v.nombre_norm "
               "LEFT JOIN alias_nombre a ON a.nombre_norm=v.nombre_norm WHERE d.id IS NULL AND a.nombre_norm IS NULL").fetchone()[0]
alias = uno("SELECT COUNT(*) FROM alias_nombre")
print(f"  en la lista actual: {uno('SELECT COUNT(*) FROM diputados')} | sin foto local: {len(sin_foto)} | nombres con votos que ya no están en la lista (exdiputados): {ex} | nombres unidos por alias: {alias}")
print(f"  bloques con logo local: {len(img['b'])} | bloque por año guardado para: {[r[0] for r in c.execute('SELECT DISTINCT anio FROM bloque_anio ORDER BY 1')] or 'ningún año'}")

print("== Decretos e iniciativas")
sin_ini = [r[0] for r in c.execute("SELECT numero FROM decretos WHERE iniciativas='' OR iniciativas IS NULL ORDER BY fecha")]
print(f"  decretos: {uno('SELECT COUNT(*) FROM decretos')} | sin iniciativa enlazada: {sin_ini}")
print(f"  iniciativas guardadas: {uno('SELECT COUNT(*) FROM iniciativas')} | votaciones con decreto: {uno('SELECT COUNT(*) FROM votaciones WHERE decreto IS NOT NULL')}")

print("== Leyes en la web (datos incrustados en web/index.html)")
html = (RAIZ / "web" / "index.html").read_text(encoding="utf-8")
i0 = html.index("window.DATA=") + len("window.DATA=")
datos = json.JSONDecoder().raw_decode(html[i0:])[0]
leyes = datos["ley"]
sin_resumen = {k: l for k, l in leyes.items() if not l.get("r")}
extractos = json.loads((RAIZ / "data" / "pdf_extracto.json").read_text(encoding="utf-8")) if (RAIZ / "data" / "pdf_extracto.json").exists() else {}
print(f"  leyes: {len(leyes)} | con decreto: {sum(1 for l in leyes.values() if l['d'])} | sin título: {sum(1 for l in leyes.values() if not l['t'])} | "
      f"con resumen: {len(leyes) - len(sin_resumen)}")
for k, l in sorted(sin_resumen.items(), key=lambda x: x[1]["f"]):
    toks = [t for t in l["i"].split("-") if t]
    estado = "extracto listo" if any(t in extractos for t in toks) else ("falta leer su PDF" if l.get("pdf") else "sin PDF conocido")
    print(f"    sin resumen: {k:<10} {l['f']}  iniciativa {l['i'] or '-':<10} {estado:<18} {(l['t'] or '')[:55]}")
votaciones_web = datos["v"]
print(f"  datos de la web hasta: {max(v['f'] for v in votaciones_web)} | votaciones en la web: {len(votaciones_web)} (en la base: {uno('SELECT COUNT(*) FROM votaciones WHERE scraped=1')})")
print(f"  tamaño de web/index.html: {len(html) // 1024} KB")
