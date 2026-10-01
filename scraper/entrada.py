"""Lee lo que el navegador devolvió como resultado de javascript_tool.

Cuando el resultado es grande, la herramienta lo guarda sola en un archivo
  ~/.claude/projects/<proyecto>/<sesión>/tool-results/mcp-Claude_Browser-javascript_tool-<n>.txt
y el mensaje de error con la ruta es todo lo que entra al contexto. Ese archivo es una lista JSON [{"type","text"}];
"text" trae el valor devuelto (una cadena JSON) seguido de un pie ("Tab Context...") que hay que ignorar.

Uso:  from entrada import cargar;  d = cargar("ruta")  |  cargar()  (el más reciente)  |  python entrada.py [ruta]
"""
import glob, json, os, pathlib, sys


def mas_reciente():
    """El archivo guardado más reciente. Según la versión de la app se llama mcp-Claude_Browser-javascript_tool-<n>.txt o toolu_<id>.json."""
    base = pathlib.Path.home() / ".claude" / "projects" / "*" / "*" / "tool-results"
    archivos = glob.glob(str(base / "mcp-Claude_Browser-javascript_tool-*.txt")) + glob.glob(str(base / "toolu_*.json"))
    if not archivos:
        raise FileNotFoundError("No hay resultados guardados de javascript_tool en " + str(base))
    return max(archivos, key=os.path.getmtime)


def cargar(ruta=None):
    ruta = ruta or mas_reciente()
    texto = pathlib.Path(ruta).read_text(encoding="utf-8")
    try:
        bruto = json.loads(texto)
    except json.JSONDecodeError:
        bruto = None
    if isinstance(bruto, list) and bruto and isinstance(bruto[0], dict) and "text" in bruto[0]:
        texto = bruto[0]["text"]            # envoltorio de la herramienta
    elif bruto is not None:
        return bruto                         # JSON simple (por ejemplo, un archivo guardado a mano)
    valor, _ = json.JSONDecoder().raw_decode(texto.lstrip())   # lo que devolvió la página; lo demás es el pie
    while isinstance(valor, str):            # JSON.stringify devuelve una cadena que contiene JSON
        try:
            valor = json.loads(valor)
        except json.JSONDecodeError:
            break
    return valor


if __name__ == "__main__":
    d = cargar(sys.argv[1] if len(sys.argv) > 1 else None)
    if isinstance(d, dict):
        resumen = {k: (len(v) if hasattr(v, "__len__") and not isinstance(v, str) else v) for k, v in d.items() if k != "pad"}
        print("kind:", d.get("kind"), "|", resumen)
    else:
        print(type(d).__name__, len(d))
