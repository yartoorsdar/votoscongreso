"""Genera la versión de un solo archivo (imágenes incrustadas) para publicar como artefacto: python empaquetar_artefacto.py <carpeta_salida>"""
import re, sys, json, base64, pathlib
B = pathlib.Path(sys.argv[1]); W = pathlib.Path(__file__).resolve().parent.parent / 'web'
h = (W/'index.html').read_text(encoding='utf-8')
style = re.search(r'<style>(.*?)</style>', h, re.S).group(1); body = re.search(r'<body>(.*)</body>', h, re.S).group(1)
m = re.search(r'@media\(prefers-color-scheme:light\)\{:root\{(.*?)\}\}', style, re.S); light = m.group(1)
style = style.replace(m.group(0), '@media(prefers-color-scheme:light){:root:not([data-theme="dark"]){' + light + ';color-scheme:light}}\n:root[data-theme="light"]{' + light + ';color-scheme:light}')
style = style.replace('*{box-sizing:border-box}', ':root{color-scheme:dark}\n*{box-sizing:border-box}', 1)
out = '<title>Votos del Congreso</title>\n<style>' + style + '</style>\n' + body
img = {f'{k}/{f.stem}': f'data:image/{"png" if e=="png" else "jpeg"};base64,' + base64.b64encode(f.read_bytes()).decode()
       for k, e in (('b','png'),('d','jpg')) for f in (W/'img'/k).glob('*.'+e)}
a = 'src="img/b/${bi}.png?v=3"'; b = 'src="img/d/${d.id}.jpg"'; assert a in out and b in out
out = out.replace(a, 'src="${IMGDATA[\'b/\'+bi]}"').replace(b, 'src="${IMGDATA[\'d/\'+d.id]}"')
out = out.replace('<script>\nconst LBL', '<script>window.IMGDATA=' + json.dumps(img, separators=(',',':')) + ';</script>\n<script>\nconst LBL', 1)
B.mkdir(parents=True, exist_ok=True); (B/'index.html').write_text(out, encoding='utf-8'); print(len(out)//1024, 'KB ->', B/'index.html')
