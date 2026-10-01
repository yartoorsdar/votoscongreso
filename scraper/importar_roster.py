"""Importa los resultados de js/roster.js (kind 'roster') y js/logos.js (kind 'logos').

  roster: reemplaza data diputados (id, nombre, bloque actual), guarda el bloque del año en bloque_anio y las URLs de las fotos.
  logos:  guarda las URLs de los logos de bloque.
Las URLs quedan en data/imagenes_origen.json; las imágenes se bajan después con js/imagenes.js + importar_imagenes.py.

Uso:  python scraper/importar_roster.py [ruta_del_resultado]
"""
import json, pathlib, sys
from db import conn, norm
from entrada import cargar, mas_reciente

ORIGEN = pathlib.Path(__file__).resolve().parent.parent / "data" / "imagenes_origen.json"


def main(ruta=None):
    ruta = ruta or mas_reciente()
    d = cargar(ruta)
    tipo = d.get("kind") if isinstance(d, dict) else None
    if tipo not in ("roster", "logos"):
        sys.exit(f"{ruta}: no es un resultado de roster.js ni de logos.js")
    origen = json.loads(ORIGEN.read_text(encoding="utf-8")) if ORIGEN.exists() else {"bloques": {}, "diputados": {}}
    if tipo == "logos":
        origen["bloques"].update({str(k): v for k, v in d["bloques"].items()})
        print(f"{len(d['bloques'])} logos de bloque")
    else:
        c = conn()
        n = 0
        for x in d["diputados"]:
            if not x["nombre"] or not x["bloque"]:
                continue   # tarjetas sin nombre o sin bloque: no son diputados en funciones
            c.execute("INSERT OR REPLACE INTO diputados VALUES(?,?,?,?,?)", (x["id"], x["nombre"], norm(x["nombre"]), x["bloque_id"], x["bloque"]))
            if x.get("anio"):
                c.execute("INSERT OR REPLACE INTO bloque_anio VALUES(?,?,?,?)", (x["id"], x["anio"], x["bloque_id"], x["bloque"]))
            if x.get("foto"):
                origen["diputados"][str(x["id"])] = x["foto"]
            n += 1
        c.commit()
        print(f"{n} diputados con bloque (año {d['diputados'][0].get('anio')})")
    ORIGEN.write_text(json.dumps(origen, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
