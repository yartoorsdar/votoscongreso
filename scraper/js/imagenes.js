// Fotos de diputados y logos de bloques: se descargan DENTRO de la página y se reducen en un canvas (fotos 240 px cuadradas; logos 360 px de lado mayor, con su proporción, sin fondo blanco exterior y sin márgenes)
// y salen como data URL por window.__export(). No guarda archivos. Va por lotes (preparar_js.py imagenes --lote N).
//   python scraper/preparar_js.py imagenes --lote 1 --lote-tam 60
// Las fotos se recortan a cuadrado con un pequeño sesgo hacia arriba (rostro); los logos NO se deforman ni se encajonan en un cuadrado.
/*CFG*/
(() => {
  const C = Object.assign({ items: [], tam: { b: 360, d: 240 }, pausa: [500, 1100] }, window.__cfg || {});
  const P = window.__prog = { state: 'init', n: 0, total: C.items.length, err: [] };
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const out = { b: {}, d: {} };
  window.__export = async () => { const body = { kind: 'imagenes', b: out.b, d: out.d }; let s = JSON.stringify(body);
    if (s.length < 150000) { body.pad = ' '.repeat(150000 - s.length); s = JSON.stringify(body); } return s; };
  (async () => {
    try {
      for (const it of C.items) {
        await sleep(C.pausa[0] + Math.random() * (C.pausa[1] - C.pausa[0])); P.state = 'img';
        try {
          const r = await fetch(it.url, { credentials: 'include' }); if (!r.ok) throw new Error('HTTP ' + r.status);
          const bm = await createImageBitmap(await r.blob()), sz = C.tam[it.k];
          if (it.k === 'b') {   // logo: conserva su proporción (lado mayor = sz), quita el fondo blanco EXTERIOR (deja los blancos internos) y recorta los márgenes
            const e = Math.min(1, sz / Math.max(bm.width, bm.height)), w = Math.round(bm.width * e), h = Math.round(bm.height * e);
            const c0 = document.createElement('canvas'); c0.width = w; c0.height = h; const x0 = c0.getContext('2d', { willReadFrequently: true }); x0.drawImage(bm, 0, 0, w, h);
            const im = x0.getImageData(0, 0, w, h), d = im.data;
            const blanco = i => d[i + 3] > 200 && Math.min(d[i], d[i + 1], d[i + 2]) >= 238;
            const R = new Uint8Array(w * h), pila = [];                       // relleno por inundación desde los bordes: solo el blanco conectado con el exterior
            const meter = (x, y) => { const k = y * w + x; if (!R[k] && blanco(k * 4)) { R[k] = 1; pila.push(k); } };
            for (let x = 0; x < w; x++) { meter(x, 0); meter(x, h - 1); } for (let y = 0; y < h; y++) { meter(0, y); meter(w - 1, y); }
            while (pila.length) { const k = pila.pop(), x = k % w, y = (k / w) | 0; if (x > 0) meter(x - 1, y); if (x < w - 1) meter(x + 1, y); if (y > 0) meter(x, y - 1); if (y < h - 1) meter(x, y + 1); }
            for (let k = 0; k < w * h; k++) if (R[k]) d[k * 4 + 3] = 0;
            for (let pasada = 0; pasada < 2; pasada++) {                       // borde suave: los píxeles claros junto a lo quitado pasan a semitransparentes y pierden el halo blanco
              const marca = [];
              for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) { const k = y * w + x, i = k * 4; if (d[i + 3] !== 255) continue;
                const vec = (x > 0 && d[i - 1] === 0) || (x < w - 1 && d[i + 7] === 0) || (y > 0 && d[i - w * 4 + 3] === 0) || (y < h - 1 && d[i + w * 4 + 3] === 0);
                if (!vec) continue; const m = Math.min(d[i], d[i + 1], d[i + 2]); if (m < 150) continue; marca.push([i, Math.max(0, Math.min(1, (238 - m) / (238 - 150)))]); }
              for (const [i, a] of marca) { if (a <= 0.02) { d[i + 3] = 0; continue; } for (let q = 0; q < 3; q++) d[i + q] = Math.max(0, Math.min(255, (d[i + q] - 255 * (1 - a)) / a)); d[i + 3] = Math.round(255 * a); } }
            x0.putImageData(im, 0, 0);
            let x1 = w, y1 = h, x2 = -1, y2 = -1;
            for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) if (d[(y * w + x) * 4 + 3] > 12) { if (x < x1) x1 = x; if (x > x2) x2 = x; if (y < y1) y1 = y; if (y > y2) y2 = y; }
            if (x2 < 0) { x1 = 0; y1 = 0; x2 = w - 1; y2 = h - 1; }
            const m = Math.round(Math.max(w, h) * 0.015); x1 = Math.max(0, x1 - m); y1 = Math.max(0, y1 - m); x2 = Math.min(w - 1, x2 + m); y2 = Math.min(h - 1, y2 + m);
            const c = document.createElement('canvas'); c.width = x2 - x1 + 1; c.height = y2 - y1 + 1; c.getContext('2d').drawImage(c0, x1, y1, c.width, c.height, 0, 0, c.width, c.height);
            out.b[it.id] = c.toDataURL('image/png');
          } else {
            const c = document.createElement('canvas'); c.width = c.height = sz; const x = c.getContext('2d'); x.fillStyle = '#fff'; x.fillRect(0, 0, sz, sz);
            const s = Math.min(bm.width, bm.height); x.drawImage(bm, (bm.width - s) / 2, (bm.height - s) * 0.15, s, s, 0, 0, sz, sz); out.d[it.id] = c.toDataURL('image/jpeg', 0.82);
          }
        } catch (e) { P.err.push(it.k + it.id + ': ' + e.message); }
        P.n++;
      }
      P.state = 'terminado';
    } catch (e) { P.state = 'detenido'; P.err.push(e.message); }
  })();
  return 'iniciado';
})();
