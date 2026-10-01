// Detalle de cada iniciativa de ley: título, ponentes, línea de tiempo y NÚMERO DE DECRETO. Se ejecuta DENTRO de una pestaña del Congreso:
//   python scraper/preparar_js.py iniciativas --tokens 6852,6493,6418
//
// Es la fuente autoritativa del decreto: la página /detalle_pdf/iniciativas/<id interno> trae la tabla «Estado iniciativa»
// (Dirección legislativa -> Presentación pleno -> debates -> Aprobación por artículos -> Redacción final -> Número de Decreto ->
// Envío al ejecutivo -> Sanciones -> Publicación en el diario oficial -> Entrada en vigencia) con fecha y estado de cada paso.
//
// Cómo se llega a esa página:
//  - /seccion_informacion_legislativa/iniciativas lista las 500 iniciativas más recientes (ignora los filtros de fecha y de texto) y
//    cada una trae el enlace «ver detalle» (id interno) y el PDF (<hash>-<número>.pdf). Los ids internos son correlativos pero
//    no coinciden con el número de iniciativa (6852 -> 6491).
//  - Las que no salen en el listado se buscan interpolando entre sus vecinos listados y probando ids cercanos hasta que «Número:» coincida.
//  - Progreso: window.__prog. Detener: window.__stop = true.
/*CFG*/
(() => {
  const C = Object.assign({ tokens: [], pausa: [1500, 3000], maxSondeos: 40 }, window.__cfg || {});
  const P = window.__prog = { state: 'init', n: 0, total: C.tokens.length, sondeos: 0, noEncontradas: [], err: null, t0: Date.now() };
  window.__stop = false;
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const MES = { enero: 1, febrero: 2, marzo: 3, abril: 4, mayo: 5, junio: 6, julio: 7, agosto: 8, septiembre: 9, setiembre: 9, octubre: 10, noviembre: 11, diciembre: 12 };
  const items = {};
  window.__export = async () => { const body = { kind: 'iniciativas', items: Object.values(items) }; let s = JSON.stringify(body);
    if (s.length < 150000) { body.pad = ' '.repeat(150000 - s.length); s = JSON.stringify(body); } return s; };
  const get = async u => {
    await sleep(C.pausa[0] + Math.random() * (C.pausa[1] - C.pausa[0]));
    const r = await fetch(u, { credentials: 'include' }); const t = await r.text();
    if (!r.ok || /Incapsula|Request unsuccessful/.test(t.slice(0, 3000))) throw new Error('BLOQUEADO o HTTP ' + r.status + ' en ' + u);
    return new DOMParser().parseFromString(t, 'text/html');
  };
  const dmy = s => { const m = (s || '').match(/(\d\d)-(\d\d)-(\d{4})/); return m ? `${m[3]}-${m[2]}-${m[1]}` : null; };
  const titulo = tb => { let e = tb; for (let i = 0; i < 4 && e; i++) { let p = e.previousElementSibling; while (p) { const t = p.textContent.replace(/\s+/g, ' ').trim(); if (t && t.length < 80) return t; p = p.previousElementSibling; } e = e.parentElement; } return ''; };

  // Lee /detalle_pdf/iniciativas/<id>; devuelve null si la página no es una iniciativa (id inexistente).
  const detalle = async id => {
    P.sondeos++;
    const d = await get('/detalle_pdf/iniciativas/' + id);
    const txt = d.body.innerText.replace(/\s+/g, ' ');
    const n = (txt.match(/Número: (\d+)/) || [])[1]; if (!n) return null;
    const pasos = [], notas = [];
    let decreto = null, decretoFecha = null;
    d.querySelectorAll('table').forEach(tb => {
      const cab = [...(tb.rows[0]?.cells || [])].map(c => c.textContent.trim().toLowerCase());
      const fila = r => [...r.cells].map(c => c.textContent.replace(/\s+/g, ' ').trim());
      if (cab.join('|') === 'no.|paso|fecha|estado') [...tb.rows].slice(1).forEach(r => { const c = fila(r); pasos.push({ n: +c[0], paso: c[1], fecha: dmy(c[2]), estado: c[3] }); });
      else if (cab[0] === 'fecha' && /decreto/.test(cab[1] || '')) { const c = fila(tb.rows[1] || { cells: [] }); decretoFecha = dmy(c[0]); decreto = c[1] || null; }
      else if (cab.join('|') === 'no.|descripción') [...tb.rows].slice(1).forEach(r => notas.push({ seccion: titulo(tb), texto: fila(r)[1] }));
    });
    const dec = [...d.querySelectorAll('a')].map(a => a.getAttribute('href') || '');
    const mf = txt.match(/Fecha: \w+, (\d+) de (\w+) de (\d{4})/);   // fecha de presentación en la Dirección Legislativa
    return { n, id, titulo: ((txt.match(/Detalle: (.*?) Institución Ponente/) || [])[1] || '').trim(),
      ponentes: ((txt.match(/Diputados ponentes: (.*?) Fecha:/) || [])[1] || '').split(/\s*\d+\.-\s*/).map(s => s.trim()).filter(Boolean),
      fecha: mf ? `${mf[3]}-${String(MES[mf[2].toLowerCase()]).padStart(2, '0')}-${String(mf[1]).padStart(2, '0')}` : null,
      pasos, notas, decreto, decretoFecha,
      decretoId: (dec.find(h => /detalle_pdf\/decretos\/\d+/.test(h)) || '').match(/decretos\/(\d+)/)?.[1] || null,
      decretoPdf: dec.find(h => /info_legislativo\/decretos\/.*\.pdf$/.test(h)) || null,
      pdf: dec.find(h => /info_legislativo\/iniciativas\/.*\.pdf$/.test(h)) || null };
  };

  (async () => {
    try {
      P.state = 'listado';
      const l = await get('/seccion_informacion_legislativa/iniciativas'), mapa = {}; let pendiente = null;
      l.querySelectorAll('a[href*="detalle_pdf/iniciativas/"],a[href$=".pdf"]').forEach(a => { const h = a.getAttribute('href');
        if (h.includes('detalle_pdf/iniciativas/')) pendiente = +h.match(/iniciativas\/(\d+)/)[1];
        else if (pendiente !== null) { const m = h.match(/-(\d+)\.pdf$/); if (m) mapa[m[1]] = { id: pendiente, pdf: new URL(h, location.origin).href }; pendiente = null; } });
      const lista = Object.entries(mapa).map(([num, v]) => ({ num: +num, id: v.id })).sort((a, b) => a.num - b.num);
      P.listadas = lista.length; P.rango = lista.length ? lista[0].num + '..' + lista[lista.length - 1].num : null;

      // Busca el id interno de una iniciativa que NO sale en el listado: interpola entre los dos vecinos listados y prueba ids cercanos
      // (los ids son correlativos pero no coinciden con el número). Máximo cfg.maxSondeos ids por iniciativa.
      const buscar = async tk => {
        const t = +tk, lo = [...lista].reverse().find(x => x.num < t), hi = lista.find(x => x.num > t);
        if (!lo && !hi) return null;
        const pend = lo && hi ? (hi.id - lo.id) / (hi.num - lo.num) : 1, ref = lo || hi;
        let id = Math.round(ref.id + (t - ref.num) * pend); const vistos = new Set();
        for (let k = 0; k < C.maxSondeos; k++) {
          if (lo && id <= lo.id) id = lo.id + 1; if (hi && id >= hi.id) id = hi.id - 1;
          if (vistos.has(id)) { id += (vistos.size % 2 ? 1 : -1) * Math.ceil(vistos.size / 2); if (vistos.has(id)) continue; }
          vistos.add(id);
          const x = await detalle(id); if (window.__stop) return null;
          if (x && x.n === tk) return x;
          id += x ? (Math.round((t - +x.n) * pend) || (t > +x.n ? 1 : -1)) : 1;
        }
        return null;
      };
      for (const tk of C.tokens) {
        if (window.__stop) { P.state = 'detenido a pedido'; return; }
        P.state = 'iniciativa ' + tk; const id = mapa[tk]?.id ?? null;
        const r = id !== null ? await detalle(id) : await buscar(tk);
        if (r) { r.pdf = r.pdf || mapa[tk]?.pdf || null; items[tk] = r; } else P.noEncontradas.push(tk);
        P.n++;
      }
      P.state = 'terminado';
    } catch (e) { P.state = 'detenido'; P.err = e.message; }
  })();
  return 'iniciado';
})();
