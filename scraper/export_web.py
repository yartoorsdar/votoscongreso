"""SQLite -> datos incrustados en web/index.html (compacto: un carácter por diputado por votación)."""
import json, pathlib, re
from db import conn

c = conn()
dips = c.execute("SELECT id, nombre, nombre_norm, COALESCE(bloque,'SIN BLOQUE'), COALESCE(bloque_id,0) FROM diputados ORDER BY nombre").fetchall()
# Diputados que votaron en 2026 pero ya no están en la lista actual (salieron del Congreso): se incluyen sin bloque.
extra = c.execute("SELECT DISTINCT v.nombre_norm, v.diputado_nombre FROM votos v LEFT JOIN diputados d ON d.nombre_norm=v.nombre_norm "
                  "LEFT JOIN alias_nombre a ON a.nombre_norm=v.nombre_norm WHERE d.id IS NULL AND a.nombre_norm IS NULL").fetchall()
dips += [(-i - 1, n.replace("�", "a"), nn, "EX-DIPUTADO (bloque no disponible)", 0) for i, (nn, n) in enumerate(extra)]  # �: carácter dañado en la fuente
idx = {d[2]: i for i, d in enumerate(dips)}
# nombres que el Congreso escribió distinto a lo largo del tiempo -> misma persona (scraper/resolver_alias.py)
for alias, nn in c.execute("SELECT a.nombre_norm, d.nombre_norm FROM alias_nombre a JOIN diputados d ON d.id=a.diputado_id"):
    idx[alias] = idx[nn]
CODE = {"A FAVOR": "F", "EN CONTRA": "C", "CONTRA": "C", "AUSENTE": "A", "LICENCIA / EXCUSA": "L", "ABSTENCION": "B", "ABSTENCIÓN": "B"}


def tipo(p):
    """L = ley/decreto (votación que decide), A = artículos y enmiendas, P = trámite y otros."""
    u = p.upper()
    if re.search(r"ART[IÍ]CULO|ENMIENDA|PRE[AÁ]MBULO|T[IÍ]TULO|CAP[IÍ]TULO|FONDO (DE )?REVISI[OÓ]N", u) and "REDACCI" not in u: return "A"
    if re.search(r"EN (PRIMER|SEGUNDO|TERCER|[UÚ]NICO) DEBATE|REDACCI[OÓ]N FINAL|OBJECIONES|RATIFICAR", u): return "L"
    return "P"


def etapa(p):
    """Etapa dentro de la ley, en el orden del procedimiento: T trámite previo, D debate, A articulado, F redacción final."""
    u = p.upper()
    if "REDACCI" in u and "FINAL" in u: return "F"
    if re.search(r"EN (PRIMER|SEGUNDO|TERCER|[UÚ]NICO) DEBATE", u): return "D"
    if re.search(r"ART[IÍ]CULO|ENMIENDA|PRE[AÁ]MBULO|T[IÍ]TULO|CAP[IÍ]TULO|FONDO (DE )?REVISI", u): return "A"
    return "T"


def articulo(p):
    u = p.upper()
    m = re.search(r"ART[IÍ]CULO\s+(\d+)", u)
    if m: return int(m[1])
    return 0 if re.search(r"PRE[AÁ]MBULO", u) else None


def etiqueta(p):
    s = re.sub(r"\s+(DEL|AL)\s+PROYECTO DE DECRETO.*$", "", p.strip(), flags=re.I)
    s = re.sub(r"\s+", " ", s)
    return s[:1].upper() + s[1:].lower()


def tokens(ini, preg):
    return sorted(set(re.findall(r"\b[56]\d{3}\b", f"{ini or ''} {preg}")))


# decreto <- iniciativa (cruzar_decretos.py)
tokdec = {t: n for n, ini in c.execute("SELECT numero, iniciativas FROM decretos") for t in (ini or "").split(",") if t}
dec_res = {n: r for n, r in c.execute("SELECT numero, resumen FROM decretos")}
ini_res = {n: re.sub(r"^Iniciativa( de ley)? que dispone( aprobar)?\s*", "", r, flags=re.I) for n, r in c.execute("SELECT numero, resumen FROM iniciativas")}
ini_res.update({n: re.sub(r"^Iniciativa( de ley)? que dispone( aprobar)?\s*", "", t, flags=re.I) for n, t in c.execute("SELECT numero, titulo FROM iniciativa_detalle WHERE titulo<>''")})

_data = pathlib.Path(__file__).resolve().parent.parent / "data"
RES = json.loads((_data / "resumenes.json").read_text(encoding="utf-8")) if (_data / "resumenes.json").exists() else {}
PDFS = json.loads((_data / "pdf_origen.json").read_text(encoding="utf-8")) if (_data / "pdf_origen.json").exists() else {}

rows = c.execute("SELECT id,sesion_id,numero,pregunta,fecha,iniciativa,decreto FROM votaciones WHERE scraped=1 ORDER BY fecha DESC, id DESC").fetchall()

# Una ley = conjunto de iniciativas que aparecen juntas en alguna votación (union-find); si tiene decreto, la clave es el decreto.
padre = {}
def raiz(x):
    padre.setdefault(x, x)
    while padre[x] != x:
        padre[x] = padre[padre[x]]; x = padre[x]
    return x
for r in rows:
    ts = tokens(r[5], r[3])
    for t in ts[1:]: padre[raiz(t)] = raiz(ts[0])
    if ts: raiz(ts[0])
dec_de = {}
for r in rows:
    ts = tokens(r[5], r[3])
    d = r[6] or next((tokdec[t] for t in ts if t in tokdec), None)
    if d:
        for t in ts: dec_de[raiz(t)] = d
def clave(ts, d):
    if d: return "d" + d
    return ("i" + min(raiz(t) for t in ts)) if ts else None

vots, leyes = [], {}
for vid, sid, num, preg, fecha, ini, dec in rows:
    row = ["?"] * len(dips)
    for n, v in c.execute("SELECT nombre_norm, voto FROM votos WHERE votacion_id=?", (vid,)):
        if n in idx: row[idx[n]] = CODE.get(v, "?")
    ses = c.execute("SELECT numero, tipo FROM sesiones WHERE id=?", (sid,)).fetchone() or ("", "")
    ts = tokens(ini, preg)
    d = dec or next((tokdec[t] for t in ts if t in tokdec), None) or next((dec_de[raiz(t)] for t in ts if raiz(t) in dec_de), None)
    k = clave(ts, d)
    v = {"id": vid, "f": fecha, "s": f"{ses[1]} {ses[0]}", "n": int(num or 0), "p": preg, "i": ini, "d": d, "t": tipo(preg), "v": "".join(row)}
    if k:
        v.update(k=k, e=etapa(preg), ar=articulo(preg), lb=etiqueta(preg))
        L = leyes.setdefault(k, {"d": d, "ts": set(), "f": fecha})
        L["ts"].update(ts); L["f"] = max(L["f"], fecha)
    vots.append(v)

for k, L in leyes.items():
    ts = sorted(L["ts"])
    L["i"] = "-".join(ts)
    L["t"] = (dec_res.get(L["d"]) if L["d"] else None) or next((ini_res[t] for t in ts if t in ini_res), None)
    L["t"] = (L["t"][:1].upper() + L["t"][1:]) if L["t"] else None
    # resumen del propósito (resumenes_leyes.py): por clave de ley o, si la clave cambió (i6702 -> d2-2026 al asignarse decreto), por iniciativa
    res = RES.get(k) or next((RES[f"i{t}"] for t in ts if f"i{t}" in RES), None)
    if res:
        L["r"], L["rf"] = res["r"], res["f"]
    L["pdf"] = [{"i": t, "u": PDFS[t]} for t in ts if t in PDFS]
    del L["ts"]

web = pathlib.Path(__file__).resolve().parent.parent / "web"
imgidx = web / "img" / "index.json"
img = json.loads(imgidx.read_text(encoding="utf-8")) if imgidx.exists() else {"b": {}, "d": {}}
out = web / "index.html"  # datos incrustados en el HTML: funciona abierto con doble clic (file://) y desde cualquier servidor
payload = json.dumps({"d": [{"id": d[0], "n": d[1], "b": d[3], "bi": d[4]} for d in dips], "v": vots, "img": img, "dec": dec_res, "ley": leyes},
                     ensure_ascii=False, separators=(",", ":"))
html = out.read_text(encoding="utf-8")
a, b = html.index("/*DATA*/"), html.index("/*END*/")
out.write_text(html[:a] + "/*DATA*/window.DATA=" + payload.replace("</", "<\\/") + ";" + html[b:], encoding="utf-8")
print(len(dips), "diputados,", len(vots), "votaciones,", len(leyes), "leyes ->", out, out.stat().st_size // 1024, "KB")
print("leyes con decreto:", sum(1 for L in leyes.values() if L["d"]), "| sin título:", sum(1 for L in leyes.values() if not L["t"]))
