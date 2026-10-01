// Listas de decretos e iniciativas (congreso.gob.gt). Se ejecuta DENTRO de una pestaña del Congreso con javascript_tool:
//   python scraper/preparar_js.py decretos
//
// IMPORTANTE (probado): estas dos páginas IGNORAN los filtros de fecha y de texto.
//   /seccion_informacion_legislativa/decretos     -> siempre TODOS los decretos (1,131 desde 1952): número, fecha de emisión, nombre de la ley
//   /seccion_informacion_legislativa/iniciativas  -> siempre las 500 iniciativas más recientes: número, fecha en que la conoció el Pleno, nombre, PDF
// Por eso basta UNA llamada a cada una. Para saber qué decreto salió de una iniciativa usa js/iniciativas.js (página de detalle);
// esta lista sirve para el nombre de la ley y para decretos sin iniciativa (p. ej. ratificación de un decreto gubernativo).
/*CFG*/
(() => {
  const C = Object.assign({ pausa: [1500, 3000] }, window.__cfg || {});
  const P = window.__prog = { state: 'init', decretos: 0, iniciativas: 0, err: null };
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const MES = { enero: 1, febrero: 2, marzo: 3, abril: 4, mayo: 5, junio: 6, julio: 7, agosto: 8, septiembre: 9, setiembre: 9, octubre: 10, noviembre: 11, diciembre: 12 };
  const iso = (d, m, y) => `${y}-${String(MES[m.toLowerCase()]).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
  const get = async ruta => {
    await sleep(C.pausa[0] + Math.random() * (C.pausa[1] - C.pausa[0]));
    const r = await fetch(ruta, { credentials: 'include' }); const t = await r.text();
    if (!r.ok || /Incapsula|Request unsuccessful/.test(t.slice(0, 3000))) throw new Error('BLOQUEADO o HTTP ' + r.status + ' en ' + ruta);
    return new DOMParser().parseFromString(t, 'text/html');
  };
  const decretos = {}, iniciativas = {};
  window.__export = async () => { const body = { kind: 'decretos', decretos: Object.values(decretos), iniciativas: Object.values(iniciativas) };
    let s = JSON.stringify(body); if (s.length < 150000) { body.pad = ' '.repeat(150000 - s.length); s = JSON.stringify(body); } return s; };
  (async () => {
    try {
      P.state = 'decretos';
      const dd = await get('/seccion_informacion_legislativa/decretos');
      [...dd.body.innerText.replace(/\s+/g, ' ').matchAll(/Decreto: (\d+-\d{4}) Fecha de Emisión: [^,]+, (\d+) de (\w+) de (\d{4}) Resumen: (.*?) ver detalle/g)]
        .forEach(m => { decretos[m[1]] = { n: m[1], f: iso(m[2], m[3], m[4]), r: m[5] }; });
      P.decretos = Object.keys(decretos).length;
      P.state = 'iniciativas';
      const di = await get('/seccion_informacion_legislativa/iniciativas'), pdf = {}, interno = {}; let pendiente = null;
      di.querySelectorAll('a[href*="detalle_pdf/iniciativas/"],a[href$=".pdf"]').forEach(a => { const h = a.getAttribute('href');
        if (h.includes('detalle_pdf/iniciativas/')) pendiente = +h.match(/iniciativas\/(\d+)/)[1];
        else if (pendiente !== null) { const m = h.match(/-(\d+)\.pdf$/); if (m) { pdf[m[1]] = new URL(h, location.origin).href; interno[m[1]] = pendiente; } pendiente = null; } });
      [...di.body.innerText.replace(/\s+/g, ' ').matchAll(/Iniciativa: (\d+) .*?, (\d+) de (\w+) de (\d{4}) Resumen: (.*?) ver detalle/g)]
        .forEach(m => { iniciativas[m[1]] = { n: m[1], f: iso(m[2], m[3], m[4]), r: m[5], pdf: pdf[m[1]] || null, id: interno[m[1]] || null }; });
      P.iniciativas = Object.keys(iniciativas).length; P.state = 'terminado';
    } catch (e) { P.state = 'detenido'; P.err = e.message; }
  })();
  return 'iniciado';
})();
