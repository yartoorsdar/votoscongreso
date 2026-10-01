// Logos de los bloques. Solo existen en el DOM VIVO de https://www.congreso.gob.gt/buscador_bloques (se cargan con JavaScript y
// lazyload; el HTML crudo no los trae). Navega una pestaña a esa página, espera 2 s y ejecuta:
//   python scraper/preparar_js.py logos
// Devuelve { bloque_id: url_del_logo } asociando cada imagen con el enlace perfil_bloques/<id> más cercano.
/*CFG*/
(() => {
  const bloques = {};
  document.querySelectorAll('img').forEach(i => {
    const s = i.currentSrc && !i.currentSrc.startsWith('data') ? i.currentSrc : i.dataset.src;
    if (!s || !/uploads\/bloques/.test(s)) return;
    let e = i, a = null; for (let k = 0; k < 6 && e; k++) { a = e.querySelector('a[href*="perfil_bloques/"]'); if (a) break; e = e.parentElement; }
    if (a) bloques[+a.href.match(/perfil_bloques\/(\d+)/)[1]] = new URL(s, location.origin).href;
  });
  const body = { kind: 'logos', pagina: location.pathname, bloques }; let s = JSON.stringify(body);
  if (s.length < 150000) { body.pad = ' '.repeat(150000 - s.length); s = JSON.stringify(body); }   // el relleno fuerza el guardado en disco
  return s;
})();
