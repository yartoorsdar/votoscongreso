// Diputados actuales con su bloque y la URL de su foto. Se ejecuta en cualquier pestaña del Congreso con javascript_tool:
//   python scraper/preparar_js.py roster
// La portada (HTML crudo) trae los 160 diputados en tarjetas: id, nombre ("Nombres Apellidos"), enlace al bloque
// (perfil_bloques/<id>/<año>) y la foto en miniatura (img[data-src]). /buscador_diputados NO sirve con fetch: se arma con JavaScript.
/*CFG*/
(() => {
  const P = window.__prog = { state: 'init', diputados: 0, err: null };
  const out = {};
  window.__export = async () => { const body = { kind: 'roster', diputados: Object.values(out) }; let s = JSON.stringify(body);
    if (s.length < 150000) { body.pad = ' '.repeat(150000 - s.length); s = JSON.stringify(body); } return s; };   // el relleno fuerza el guardado en disco
  (async () => {
    try {
      const r = await fetch('/', { credentials: 'include' }); const t = await r.text();
      if (!r.ok || /Incapsula|Request unsuccessful/.test(t.slice(0, 3000))) throw new Error('BLOQUEADO o HTTP ' + r.status);
      const d = new DOMParser().parseFromString(t, 'text/html');
      d.querySelectorAll('a[href*="perfil_diputado/"]').forEach(a => {
        const id = +a.getAttribute('href').match(/perfil_diputado\/(\d+)/)[1], nombre = a.textContent.trim().replace(/\s+/g, ' ');
        let el = a, b = null; for (let i = 0; i < 8 && el; i++) { b = el.querySelector('a[href*="perfil_bloques/"]'); if (b) break; el = el.parentElement; }
        const o = out[id] || (out[id] = { id, nombre: '', bloque_id: null, bloque: null, anio: null, foto: null });
        if (nombre.length > o.nombre.length && !/^VER/i.test(nombre)) o.nombre = nombre;
        const im = a.querySelector('img'); if (im && im.dataset.src) o.foto = new URL(im.dataset.src, location.origin).href;
        if (b) { const m = b.getAttribute('href').match(/perfil_bloques\/(\d+)\/(\d{4})/); o.bloque_id = m ? +m[1] : null; o.anio = m ? +m[2] : null; o.bloque = b.textContent.trim(); }
      });
      P.diputados = Object.keys(out).length; P.state = 'terminado';
    } catch (e) { P.state = 'detenido'; P.err = e.message; }
  })();
  return 'iniciado';
})();
