"""Importa el resultado de js/pdf.js (kind 'pdf'): fusiona los extractos en data/pdf_extracto.json.

Después, para cada ley sin resumen, se lee el extracto (y 'objeto') y se redacta el resumen en scraper/resumenes_leyes.py.
Uso:  python scraper/importar_pdf.py [ruta_del_resultado]
"""
import json, pathlib, sys
from entrada import cargar, mas_reciente

DESTINO = pathlib.Path(__file__).resolve().parent.parent / "data" / "pdf_extracto.json"


def main(ruta=None):
    ruta = ruta or mas_reciente()
    d = cargar(ruta)
    if not isinstance(d, dict) or d.get("kind") != "pdf":
        sys.exit(f"{ruta}: no es un resultado de js/pdf.js")
    actual = json.loads(DESTINO.read_text(encoding="utf-8")) if DESTINO.exists() else {}
    actual.update(d["docs"])
    DESTINO.write_text(json.dumps(actual, ensure_ascii=False, indent=1), encoding="utf-8")
    sin = [t for t, v in d["docs"].items() if not v.get("tiene_exposicion")]
    print(f"{len(d['docs'])} extractos nuevos ({len(actual)} en total)" + (f" | sin 'exposición de motivos': {', '.join(sin)}" if sin else ""))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
