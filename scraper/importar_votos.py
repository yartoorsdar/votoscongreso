"""Importa a data/votos.db el resultado de js/votos.js (kind 'votos'). Es idempotente: se puede repetir sin duplicar.

Uso:  python scraper/importar_votos.py [ruta_del_resultado]      (sin ruta: el resultado más reciente de javascript_tool)
"""
import re, sys
from db import conn, norm
from entrada import cargar, mas_reciente

ESTADO = {"F": ("PRESENTE", "A FAVOR"), "C": ("PRESENTE", "CONTRA"), "B": ("PRESENTE", "ABSTENCIÓN"),
          "A": ("AUSENTE", "AUSENTE"), "L": ("LICENCIA / EXCUSA", "LICENCIA / EXCUSA")}


def main(ruta=None):
    ruta = ruta or mas_reciente()
    d = cargar(ruta)
    if not isinstance(d, dict) or d.get("kind") != "votos":
        sys.exit(f"{ruta}: no es un resultado de js/votos.js (kind={d.get('kind') if isinstance(d, dict) else type(d).__name__})")
    c = conn()
    roster, n_ses, n_vot, n_votos = d["roster"], 0, 0, 0
    excluidas = {r[0] for r in c.execute("SELECT id FROM sesiones_excluidas")}
    for s in d["sesiones"]:
        if s["sid"] in excluidas:
            continue   # no pertenece al periodo analizado (ver tabla sesiones_excluidas)
        c.execute("INSERT INTO sesiones(id,tipo,numero,descripcion,fecha,scraped) VALUES(?,?,?,?,?,1) "
                  "ON CONFLICT(id) DO UPDATE SET tipo=excluded.tipo, numero=excluded.numero, descripcion=excluded.descripcion, fecha=excluded.fecha, scraped=1",
                  (s["sid"], s["tipo"], int(s["num"] or 0), s["desc"], s["fecha"]))
        n_ses += 1
        for q in s["votaciones"]:
            ini = re.search(r"INICIATIVAS? DE LEY(?:ES)? ([\d\-, Y]+)", q["q"].upper())
            c.execute("INSERT INTO votaciones(id,sesion_id,numero,pregunta,fecha,iniciativa,scraped,hora) VALUES(?,?,?,?,?,?,1,?) "
                      "ON CONFLICT(id) DO UPDATE SET sesion_id=excluded.sesion_id, numero=excluded.numero, pregunta=excluded.pregunta, "
                      "fecha=excluded.fecha, iniciativa=excluded.iniciativa, scraped=1, hora=excluded.hora",   # no pisa 'decreto'
                      (q["vid"], s["sid"], int(q["n"] or 0), q["q"], q["f"], ini[1].strip() if ini else None, q.get("h")))
            n_vot += 1
            for nombre, codigo in zip(roster, q["v"]):
                if codigo == "?":
                    continue   # ese nombre no figuraba en esta votación (por ejemplo, un diputado que entró o salió después)
                estado, voto = ESTADO[codigo]
                c.execute("INSERT OR REPLACE INTO votos VALUES(?,?,?,?,?)", (q["vid"], nombre, norm(nombre), estado, voto))
                n_votos += 1
    c.commit()
    print(f"importado: {n_ses} sesiones, {n_vot} votaciones, {n_votos} votos  <-  {ruta}")
    for t in ("sesiones", "votaciones", "votos"):
        print(f"  total {t}:", c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0])


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
