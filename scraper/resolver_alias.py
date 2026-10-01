"""Reconcilia nombres de los votos que no coinciden con la lista actual de diputados porque el Congreso los escribió distinto
a lo largo del tiempo: apellido de casada («de Pantoja»), segundo nombre que aparece o desaparece («Erick José» / «Erick José Mario»),
partículas, tildes. Guarda el resultado en la tabla alias_nombre (nombre del voto -> diputado), que usa export_web.py.

Regla (conservadora): se ignoran las partículas (de, del, la, las, los, y); un nombre se une con un diputado si el conjunto de
palabras de uno contiene al del otro, comparten 3 o más palabras y hay UN solo candidato. Lo ambiguo o sin candidato no se une
(son exdiputados de verdad o casos a revisar a mano). Imprime todo lo que une para poder revisarlo.

Uso:  python scraper/resolver_alias.py [--rehacer]      (se corre después de cada importación de votos)
"""
import sys
from db import conn

PARTICULAS = {"de", "del", "la", "las", "los", "y"}


def palabras(norm):
    return {t for t in norm.split() if t not in PARTICULAS}


def main(rehacer=False):
    c = conn()
    if rehacer:
        c.execute("DELETE FROM alias_nombre")
    roster = [(i, n, nn, palabras(nn)) for i, n, nn in c.execute("SELECT id, nombre, nombre_norm FROM diputados")]
    ya = {r[0] for r in c.execute("SELECT nombre_norm FROM alias_nombre")}
    pendientes = c.execute("""SELECT v.nombre_norm, MIN(v.diputado_nombre), COUNT(*), MIN(vt.fecha), MAX(vt.fecha)
        FROM votos v JOIN votaciones vt ON vt.id = v.votacion_id
        WHERE v.nombre_norm NOT IN (SELECT nombre_norm FROM diputados) GROUP BY v.nombre_norm""").fetchall()
    unidos, ambiguos, ex = [], [], []
    for nn, nombre, n_votos, f0, f1 in pendientes:
        if nn in ya:
            continue
        a = palabras(nn)
        cand = [(i, n) for i, n, _, b in roster if len(a & b) >= 3 and (a <= b or b <= a)]
        if len(cand) == 1:
            c.execute("INSERT OR REPLACE INTO alias_nombre VALUES(?,?,?)", (nn, cand[0][0], "subconjunto de palabras"))
            unidos.append((nombre, cand[0][1], n_votos, f0, f1))
        elif cand:
            ambiguos.append((nombre, [n for _, n in cand]))
        else:
            ex.append((nombre, n_votos, f0, f1))
    c.commit()
    print(f"{len(unidos)} nombres unidos a un diputado actual:")
    for nombre, actual, n, f0, f1 in sorted(unidos, key=lambda x: -x[2]):
        print(f"  {nombre!r:48} -> {actual!r:46} {n:5} votos {f0}..{f1}")
    if ambiguos:
        print(f"{len(ambiguos)} AMBIGUOS (revisar a mano):")
        for nombre, cands in ambiguos:
            print(f"  {nombre!r} -> {cands}")
    print(f"{len(ex)} nombres sin candidato (exdiputados o suplentes que ya no están en la lista actual)")
    for nombre, n, f0, f1 in sorted(ex, key=lambda x: -x[1])[:40]:
        print(f"  {nombre!r:48} {n:5} votos {f0}..{f1}")


if __name__ == "__main__":
    main("--rehacer" in sys.argv)
