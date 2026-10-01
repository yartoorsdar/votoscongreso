"""Arma el código JavaScript de un trabajo de extracción con sus parámetros, listo para pegarlo en javascript_tool.

  python scraper/preparar_js.py votos     --from 2024-01-01 --to 2025-12-31 [--max N]
  python scraper/preparar_js.py iniciativas [--tokens 6852,6493]   (sin --tokens: las citadas en votaciones sin detalle guardado)
                                    [--solo-listadas] [--sondeos 8]   (solo las del rango del listado; tope de ids a probar por iniciativa no listada)
  python scraper/preparar_js.py decretos
  python scraper/preparar_js.py pdf       [--tokens 6852,6493]   (usa data/pdf_origen.json; sin --tokens: los que aún no tienen extracto)
  python scraper/preparar_js.py roster
  python scraper/preparar_js.py logos     (hay que correrlo en la página /buscador_bloques ya cargada)
  python scraper/preparar_js.py imagenes  [--lote 1] [--lote-tam 60]  (fotos y logos que faltan en web/img)

Imprime el código en la salida estándar. Cada trabajo se ejecuta dentro de una pestaña de www.congreso.gob.gt del navegador integrado.
"""
import argparse, json, pathlib, re, sys
from db import conn

AQUI = pathlib.Path(__file__).resolve().parent
DATA = AQUI.parent / "data"
WEB = AQUI.parent / "web"


def cargar_json(ruta, defecto):
    return json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else defecto


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("trabajo", choices=["votos", "decretos", "iniciativas", "pdf", "roster", "logos", "imagenes"])
    ap.add_argument("--from", dest="desde"); ap.add_argument("--to", dest="hasta"); ap.add_argument("--max", type=int)
    ap.add_argument("--tokens"); ap.add_argument("--sondeos", type=int, default=40, help="iniciativas: máximo de ids a probar por iniciativa fuera del listado")
    ap.add_argument("--solo-listadas", action="store_true", help="iniciativas: solo las del rango que cubre el listado del Congreso (rápidas)")
    ap.add_argument("--rehacer", choices=["b", "d"], help="imagenes: volver a bajar todos los logos (b) o todas las fotos (d), aunque ya existan")
    ap.add_argument("--forzar", action="store_true", help="votos: releer también las sesiones ya guardadas")
    ap.add_argument("--lote", type=int, default=1); ap.add_argument("--lote-tam", type=int, default=60)
    a = ap.parse_args()
    cfg = {}
    if a.trabajo == "votos":
        c = conn()
        cfg = {"from": a.desde or "0000-00-00", "to": a.hasta or "9999-12-31",
               "skip": [r[0] for r in c.execute("SELECT id FROM sesiones_excluidas")] + ([] if a.forzar else [r[0] for r in c.execute("SELECT id FROM sesiones WHERE scraped=1 AND fecha BETWEEN ? AND ?", (a.desde or "0000", a.hasta or "9999"))])}
        if a.max: cfg["max"] = a.max
    elif a.trabajo == "decretos":
        cfg = {}
    elif a.trabajo == "pdf":
        origen = cargar_json(DATA / "pdf_origen.json", {})
        hechos = cargar_json(DATA / "pdf_extracto.json", {})
        if a.tokens:
            tokens = a.tokens.split(",")
        else:   # por defecto: iniciativas citadas en votaciones, con PDF conocido y sin extracto
            citadas = {t for (i,) in conn().execute("SELECT iniciativa FROM votaciones WHERE iniciativa IS NOT NULL") for t in re.findall(r"\d{4}", i)}
            citadas |= {t for (q,) in conn().execute("SELECT pregunta FROM votaciones") for t in re.findall(r"\b[56]\d{3}\b", q)}   # también las de mociones de urgencia
            tokens = sorted(t for t in citadas if t in origen and t not in hechos)
        cfg = {"urls": {t: origen[t] for t in tokens if t in origen}}
        faltan = [t for t in tokens if t not in origen]
        if faltan: print("// Sin URL de PDF (ejecuta primero 'iniciativas' o 'decretos'):", ",".join(faltan), file=sys.stderr)
        print(f"// {len(cfg['urls'])} PDF a leer", file=sys.stderr)
    elif a.trabajo == "iniciativas":
        if a.tokens: tokens = a.tokens.split(",")
        else:   # por defecto: las iniciativas citadas en votaciones que aún no tienen detalle guardado
            vistos = {t for (i,) in conn().execute("SELECT iniciativa FROM votaciones WHERE iniciativa IS NOT NULL") for t in re.findall(r"\d{4}", i)}
            vistos |= {t for (q,) in conn().execute("SELECT pregunta FROM votaciones") for t in re.findall(r"\b[56]\d{3}\b", q)}   # también las de mociones de urgencia
            tokens = sorted(vistos - {n for (n,) in conn().execute("SELECT numero FROM iniciativa_detalle")})
        cfg = {"tokens": tokens, "maxSondeos": a.sondeos}
        if a.solo_listadas: cfg["tokens"] = [t for t in tokens if 5790 <= int(t) <= 6852]
    elif a.trabajo == "imagenes":
        idx = cargar_json(WEB / "img" / "index.json", {"b": {}, "d": {}})
        fotos = cargar_json(DATA / "imagenes_origen.json", {"bloques": {}, "diputados": {}})
        items = [{"k": "b", "id": i, "url": u} for i, u in fotos["bloques"].items() if i not in idx["b"] or a.rehacer == "b"] + \
                [{"k": "d", "id": i, "url": u} for i, u in fotos["diputados"].items() if i not in idx["d"] or a.rehacer == "d"]
        total = len(items); items = items[(a.lote - 1) * a.lote_tam: a.lote * a.lote_tam]
        cfg = {"items": items}
        print(f"// lote {a.lote}: {len(items)} de {total} imágenes pendientes", file=sys.stderr)
    codigo = (AQUI / "js" / f"{a.trabajo}.js").read_text(encoding="utf-8")
    linea = "window.__cfg = " + json.dumps(cfg, ensure_ascii=False, separators=(",", ":")) + ";"
    if "/*CFG*/" not in codigo:
        sys.exit("El archivo js no tiene la marca /*CFG*/")
    print(codigo.replace("/*CFG*/", linea, 1))


if __name__ == "__main__":
    main()
