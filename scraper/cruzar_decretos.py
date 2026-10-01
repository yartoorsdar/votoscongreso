"""Importa la lista de decretos/iniciativas (js/decretos.js, kind 'decretos') y, solo para los decretos que aún no tienen
iniciativa enlazada, la deduce por fecha. PLAN B: la fuente autoritativa es js/iniciativas.js + importar_iniciativas.py.

Regla del plan B: la fecha de emisión del decreto es el día en que el Pleno votó la iniciativa (sus votaciones ya están en la base);
si ese día se votaron varias, se desempata por el parecido entre el nombre de la ley del decreto y el de la iniciativa
(>= 60 % de las palabras de 4+ letras); si queda una sola candidata, se toma esa.
Efecto: tablas decretos e iniciativas, votaciones.decreto, data/pdf_origen.json (iniciativa -> URL del PDF oficial) y las
ratificaciones de decretos gubernativos (se enlazan por el texto de la votación).

Uso:  python scraper/cruzar_decretos.py [ruta_del_resultado]      (sin ruta: el más reciente de javascript_tool)
"""
import json, pathlib, re, sys, unicodedata
from db import conn
from entrada import cargar, mas_reciente

DATA = pathlib.Path(__file__).resolve().parent.parent / "data"
PARASITAS = {"iniciativa", "dispone", "aprobar", "decreto", "numero", "congreso", "republica"}


def palabras(s):
    t = unicodedata.normalize("NFD", s.lower()).encode("ascii", "ignore").decode()
    return set(re.findall(r"[a-z]{4,}", t)) - PARASITAS


def main(ruta=None):
    ruta = ruta or mas_reciente()
    d = cargar(ruta)
    if not isinstance(d, dict) or d.get("kind") != "decretos":
        sys.exit(f"{ruta}: no es un resultado de js/decretos.js")
    c = conn()
    for i in d["iniciativas"]:
        c.execute("INSERT OR REPLACE INTO iniciativas VALUES(?,?,?)", (i["n"], i["f"], i["r"]))
    pdf_origen = json.loads((DATA / "pdf_origen.json").read_text(encoding="utf-8")) if (DATA / "pdf_origen.json").exists() else {}
    pdf_origen.update({i["n"]: i["pdf"] for i in d["iniciativas"] if i.get("pdf")})
    (DATA / "pdf_origen.json").write_text(json.dumps(pdf_origen, indent=1), encoding="utf-8")

    desde, hasta = c.execute("SELECT MIN(fecha), MAX(fecha) FROM votaciones").fetchone()   # solo decretos del periodo con votos en la base
    ya = {n: ini for n, ini in c.execute("SELECT numero, iniciativas FROM decretos")}
    titulos = {n: palabras(r) for n, r in c.execute("SELECT numero, resumen FROM iniciativas")}
    res = []
    for dec in (x for x in d["decretos"] if desde <= x["f"] <= hasta):
        if ya.get(dec["n"]):   # ya enlazado (detalle oficial u otra corrida): solo se refresca el nombre
            c.execute("UPDATE decretos SET fecha=?, resumen=? WHERE numero=?", (dec["f"], dec["r"], dec["n"]))
            continue
        cand = set()
        for (ini,) in c.execute("SELECT iniciativa FROM votaciones WHERE fecha=? AND iniciativa IS NOT NULL", (dec["f"],)):
            cand.update(re.findall(r"\d{4}", ini))
        tdec = palabras(dec["r"])
        puntaje = sorted(((len(tdec & titulos.get(t, set())) / (len(tdec) or 1), t) for t in cand), reverse=True)
        elegidas = [t for s, t in puntaje if s >= 0.6] or (list(cand) if len(cand) == 1 else [])
        c.execute("INSERT OR REPLACE INTO decretos VALUES(?,?,?,?)", (dec["n"], dec["f"], dec["r"], ",".join(elegidas)))
        for t in elegidas:
            c.execute("UPDATE votaciones SET decreto=? WHERE iniciativa LIKE ?", (dec["n"], f"%{t}%"))
        res.append((dec["n"], dec["f"], elegidas, dec["r"]))
    # Ratificaciones de decretos gubernativos: no tienen iniciativa propia, se enlazan por el texto de la votación.
    for num in {m for (p,) in c.execute("SELECT pregunta FROM votaciones WHERE upper(pregunta) LIKE '%DECRETO GUBERNATIVO%'") for m in re.findall(r"DECRETO GUBERNATIVO (\d+-\d{4})", p.upper())}:
        if c.execute("SELECT 1 FROM decretos WHERE numero=?", (num,)).fetchone():
            c.execute("UPDATE votaciones SET decreto=? WHERE upper(pregunta) LIKE ?", (num, f"%DECRETO GUBERNATIVO {num}%"))
    c.commit()
    for n, f, ts, r in sorted(res, key=lambda x: x[1]):
        print(f"{n:>9} {f} -> {','.join(ts) or 'SIN MATCH':<12} | {r[:60]}")
    print(f"decretos nuevos por fecha: {len(res)} ({sum(1 for x in res if x[2])} con iniciativa) | decretos en el listado: {len(d['decretos'])} | "
          f"iniciativas guardadas: {len(d['iniciativas'])} | votaciones con decreto: {c.execute('SELECT COUNT(*) FROM votaciones WHERE decreto IS NOT NULL').fetchone()[0]}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
