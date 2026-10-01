// Texto de las iniciativas de ley en PDF, leído DENTRO de la página del Congreso con pdf.js (sin descargar el PDF a disco).
//   python scraper/preparar_js.py pdf [--tokens 6852,6493]
//
// Los PDF son escaneos de 1 a 25 MB con una capa de texto OCR (con errores: ó -> 6, ñ -> n...). De cada uno se devuelve:
//   extracto: ~3,500 caracteres desde "EXPOSICIÓN DE MOTIVOS" (o desde el primer "CONSIDERANDO")
//   objeto:   ~700 caracteres alrededor de "tiene por objeto" / "Objeto de la Ley" (a veces es lo más claro del documento)
// Solo se leen las primeras cfg.paginas páginas: la exposición de motivos está al principio incluso en expedientes de 250 páginas.
/*CFG*/
(() => {
  const C = Object.assign({ urls: {}, paginas: 12, maxExtracto: 3500, pausa: [1200, 2200], pdfjs: '3.11.174' }, window.__cfg || {});
  const P = window.__prog = { state: 'init', n: 0, total: Object.keys(C.urls).length, err: [] };
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const docs = {};
  window.__export = async () => { const body = { kind: 'pdf', docs }; let s = JSON.stringify(body);
    if (s.length < 150000) { body.pad = ' '.repeat(150000 - s.length); s = JSON.stringify(body); } return s; };
  const cargarScript = src => new Promise((ok, mal) => { const s = document.createElement('script'); s.src = src; s.onload = ok; s.onerror = () => mal(new Error('No cargó ' + src)); document.head.appendChild(s); });
  (async () => {
    try {
      const base = `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/${C.pdfjs}/`;
      if (!window.pdfjsLib) await cargarScript(base + 'pdf.min.js');
      pdfjsLib.GlobalWorkerOptions.workerSrc = URL.createObjectURL(new Blob([`importScripts('${base}pdf.worker.min.js');`], { type: 'text/javascript' }));  // un worker de otro origen se carga así
      for (const [token, url] of Object.entries(C.urls)) {
        await sleep(C.pausa[0] + Math.random() * (C.pausa[1] - C.pausa[0])); P.state = 'pdf ' + token;
        try {
          const doc = await pdfjsLib.getDocument({ url, withCredentials: true }).promise; let txt = '';
          for (let p = 1; p <= Math.min(C.paginas, doc.numPages); p++) { const pg = await doc.getPage(p); const c = await pg.getTextContent(); txt += c.items.map(i => i.str).join(' ') + '\n'; }
          txt = txt.replace(/[ \t]+/g, ' ').replace(/\n\s*\n+/g, '\n');
          const em = txt.match(/EXPOSICI[OÓ0]N\s+DE\s+MOTIVOS/i) || txt.match(/CONSIDERANDO/i), i0 = em ? em.index + em[0].length : 0;
          const ob = txt.match(/(tiene\s+por\s+objeto|objeto\s+de\s+(la\s+)?(presente\s+)?(ley|iniciativa))/i);
          docs[token] = { url, paginas: doc.numPages, tiene_exposicion: !!em, extracto: txt.slice(i0, i0 + C.maxExtracto).trim(),
                          objeto: ob ? txt.slice(Math.max(0, ob.index - 100), ob.index + 600).trim() : null };
        } catch (e) { P.err.push(token + ': ' + e.message); }
        P.n++;
      }
      P.state = 'terminado';
    } catch (e) { P.state = 'detenido'; P.err.push(e.message); }
  })();
  return 'iniciado';
})();
