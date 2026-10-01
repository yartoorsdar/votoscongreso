"""Importa el resultado de js/iniciativas.js (kind 'iniciativas'): detalle de cada iniciativa, con su número de decreto.

Es la fuente AUTORITATIVA del decreto (la página de detalle lo trae en «Número de Decreto»). Efectos:
  - tabla iniciativa_detalle (título, ponentes, línea de tiempo, decreto, PDFs)
  - tabla decretos: agrega la iniciativa al decreto (export_web.py agrupa las votaciones por decreto con esa tabla)
  - votaciones.decreto: se fija para toda votación que cite la iniciativa (pisa lo que había puesto el cruce por fecha)
  - data/pdf_origen.json: URL del PDF de la iniciativa

Uso:  python scraper/importar_iniciativas.py [ruta_del_resultado]
"""
import json, pathlib, re, sys
from db import conn
from entrada import cargar, mas_reciente

DATA = pathlib.Path(__file__).resolve().parent.parent / "data"


def main(ruta=None):
    ruta = ruta or mas_reciente()
    d = cargar(ruta)
    if not isinstance(d, dict) or d.get("kind") != "iniciativas":
        sys.exit(f"{ruta}: no es un resultado de js/iniciativas.js")
    c = conn()
    pdf_origen = json.loads((DATA / "pdf_origen.json").read_text(encoding="utf-8")) if (DATA / "pdf_origen.json").exists() else {}
    con_decreto, conflictos = 0, []
    for it in d["items"]:
        n = it["n"]
        c.execute("INSERT OR REPLACE INTO iniciativa_detalle VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                  (n, it.get("id"), it.get("titulo"), it.get("fecha"), json.dumps(it.get("ponentes", []), ensure_ascii=False),
                   json.dumps(it.get("pasos", []), ensure_ascii=False), json.dumps(it.get("notas", []), ensure_ascii=False),
                   it.get("decreto"), it.get("decretoFecha"), it.get("decretoId"), it.get("decretoPdf"), it.get("pdf")))
        if it.get("pdf"):
            pdf_origen[n] = it["pdf"]
        dec = it.get("decreto")
        if not dec:
            continue
        con_decreto += 1
        fila = c.execute("SELECT fecha, resumen, iniciativas FROM decretos WHERE numero=?", (dec,)).fetchone()
        tokens = {t for t in (fila[2] if fila else "").split(",") if t} | {n}
        titulo = re.sub(r"^Iniciativa( de ley)? que dispone( aprobar)?\s*", "", it.get("titulo") or "", flags=re.I)
        c.execute("INSERT OR REPLACE INTO decretos VALUES(?,?,?,?)",
                  (dec, it.get("decretoFecha") or (fila[0] if fila else None), (fila[1] if fila else None) or titulo, ",".join(sorted(tokens))))
        previos = {r[0] for r in c.execute("SELECT DISTINCT decreto FROM votaciones WHERE iniciativa LIKE ? AND decreto IS NOT NULL", (f"%{n}%",))}
        if previos - {dec}:
            conflictos.append((n, sorted(previos), dec))
        c.execute("UPDATE votaciones SET decreto=? WHERE iniciativa LIKE ?", (dec, f"%{n}%"))
    c.commit()
    (DATA / "pdf_origen.json").write_text(json.dumps(pdf_origen, indent=1), encoding="utf-8")
    print(f"{len(d['items'])} iniciativas con detalle ({con_decreto} con decreto) | en total: "
          f"{c.execute('SELECT COUNT(*) FROM iniciativa_detalle').fetchone()[0]}")
    for n, antes, dec in conflictos:
        print(f"  CORREGIDO: iniciativa {n}: el cruce por fecha decía decreto {antes}, el detalle oficial dice {dec}")
    for it in d["items"]:
        estado = it["pasos"][-1]["paso"] + " " + (it["pasos"][-1]["estado"] or "") if it.get("pasos") else "sin pasos"
        print(f"  {it['n']:>5} {str(it.get('decreto') or '-'):>8}  {len(it.get('ponentes', [])):>2} ponentes | último paso: {estado} | {(it.get('titulo') or '')[:55]}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
