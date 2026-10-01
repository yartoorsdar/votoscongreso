"""Importa el resultado de js/imagenes.js (kind 'imagenes'): escribe web/img/b/<bloque>.png y web/img/d/<diputado>.jpg
y actualiza web/img/index.json (qué imágenes existen). Copias propias: la web no depende de las URLs del Congreso.

Uso:  python scraper/importar_imagenes.py [ruta_del_resultado]      (se puede repetir lote a lote)
"""
import base64, json, pathlib, sys
from entrada import cargar, mas_reciente

IMG = pathlib.Path(__file__).resolve().parent.parent / "web" / "img"


def main(ruta=None):
    ruta = ruta or mas_reciente()
    d = cargar(ruta)
    if not isinstance(d, dict) or d.get("kind") != "imagenes":
        sys.exit(f"{ruta}: no es un resultado de js/imagenes.js")
    (IMG / "b").mkdir(parents=True, exist_ok=True); (IMG / "d").mkdir(parents=True, exist_ok=True)
    indice = json.loads((IMG / "index.json").read_text(encoding="utf-8")) if (IMG / "index.json").exists() else {"b": {}, "d": {}}
    for tipo, ext in (("b", "png"), ("d", "jpg")):
        for k, uri in d[tipo].items():
            (IMG / tipo / f"{k}.{ext}").write_bytes(base64.b64decode(uri.split(",", 1)[1]))
            indice[tipo][k] = 1
    (IMG / "index.json").write_text(json.dumps(indice), encoding="utf-8")
    print(f"{len(d['b'])} logos y {len(d['d'])} fotos nuevos | en total: {len(indice['b'])} logos, {len(indice['d'])} fotos")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
