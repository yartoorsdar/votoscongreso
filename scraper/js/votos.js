// Votaciones del Pleno (congreso.gob.gt). Se ejecuta DENTRO de una pestaña del Congreso con javascript_tool,
// generado con:  python scraper/preparar_js.py votos --from 2024-01-01 --to 2025-12-31
//
//  - Una petición a la vez, con pausa de 1.5 a 3 s. Si el sitio bloquea, se detiene y NO reintenta.
//  - No descarga archivos (cada descarga obliga al usuario a dar clic en Guardar). Cada sesión se guarda en IndexedDB
//    (sobrevive a una recarga) y los datos salen por `await window.__export()`, que se devuelve como resultado de
//    javascript_tool; si es grande, la herramienta lo guarda sola en disco (ver scraper/entrada.py).
//  - Es reanudable: salta las sesiones de cfg.skip y las que ya están en IndexedDB.
//  - Progreso: window.__prog.  Para detenerlo sin perder lo ya guardado: window.__stop = true.
//  - NO navegues esta pestaña a otra página mientras corre: se pierde el trabajo en curso (lo ya guardado en IndexedDB se conserva).
/*CFG*/
(() => {
  const C = Object.assign({ from: '0000-00-00', to: '9999-12-31', skip: [], max: 100000, pausa: [1500, 3000], soloExportar: false }, window.__cfg || {});
  const P = window.__prog = { state: 'init', sesion: 0, total: 0, votaciones: 0, ultima: null, tablas: [], avisos: [], err: null, t0: Date.now() };
  window.__stop = false;
  const sleep = ms => new Promise(r => setTimeout(r, ms));

  // ---- almacenamiento: IndexedDB con respaldo en memoria
  const mem = new Map(); let db = null;
  const abrir = () => new Promise(res => { try { const rq = indexedDB.open('votoscongreso_v1', 1);
    rq.onupgradeneeded = () => rq.result.createObjectStore('sesiones', { keyPath: 'sid' });
    rq.onsuccess = () => res(rq.result); rq.onerror = () => res(null); } catch (e) { res(null); } });
  const guardar = s => { mem.set(s.sid, s); return new Promise(res => { if (!db) return res(); const tx = db.transaction('sesiones', 'readwrite');
    tx.objectStore('sesiones').put(s); tx.oncomplete = tx.onerror = () => res(); }); };
  const todas = () => new Promise(res => { if (!db) return res([...mem.values()]); const rq = db.transaction('sesiones').objectStore('sesiones').getAll();
    rq.onsuccess = () => res(rq.result); rq.onerror = () => res([...mem.values()]); });

  // ---- exportación compacta: lista de nombres (roster) + una cadena por votación con un carácter por nombre
  const CODIGO = { 'A FAVOR': 'F', 'CONTRA': 'C', 'EN CONTRA': 'C', 'AUSENTE': 'A', 'LICENCIA / EXCUSA': 'L', 'ABSTENCION': 'B', 'ABSTENCIÓN': 'B' };
  window.__export = async () => {
    const ses = (await todas()).sort((a, b) => b.fecha.localeCompare(a.fecha) || b.sid - a.sid);
    const roster = [], ix = new Map();
    for (const s of ses) for (const q of s.votaciones) for (const [n] of q.votos) if (!ix.has(n)) { ix.set(n, roster.length); roster.push(n); }
    const body = { kind: 'votos', roster, sesiones: ses.map(s => ({ sid: s.sid, tipo: s.tipo, num: s.num, desc: s.desc, fecha: s.fecha,
      votaciones: s.votaciones.map(q => { const a = Array(roster.length).fill('?'); for (const [n, , v] of q.votos) a[ix.get(n)] = CODIGO[v] || '?';
        return { vid: q.vid, n: q.n, q: q.q, f: q.f, h: q.h, v: a.join('') }; }) })) };
    let s = JSON.stringify(body);
    // Relleno: un resultado grande se guarda solo en disco y no entra al contexto; uno pequeño sí entraría.
    if (s.length < 150000) { body.pad = ' '.repeat(150000 - s.length); s = JSON.stringify(body); }
    return s;
  };

  const get = async u => {
    await sleep(C.pausa[0] + Math.random() * (C.pausa[1] - C.pausa[0]));
    const r = await fetch(u, { credentials: 'include' }); const t = await r.text();
    if (!r.ok || /Incapsula|Request unsuccessful/.test(t.slice(0, 3000))) throw new Error('BLOQUEADO o HTTP ' + r.status + ' en ' + u);
    return new DOMParser().parseFromString(t, 'text/html');
  };
  const iso = d => { const m = (d || '').match(/(\d\d)\/(\d\d)\/(\d{4})(?: (\d\d:\d\d:\d\d))?/); return m ? { f: `${m[3]}-${m[2]}-${m[1]}`, h: m[4] || null } : { f: null, h: null }; };
  const TABLA = { a_favor: 'A FAVOR', contra: 'CONTRA', votos_nulos: 'AUSENTE', licencia: 'LICENCIA / EXCUSA' };

  (async () => {
    try {
      db = await abrir();
      if (C.soloExportar) { P.state = 'listo para exportar'; return; }
      P.state = 'lista de sesiones';
      const lista = await get('/seccion_informacion_legislativa/votaciones_pleno');   // trae las ~1,000 sesiones en el HTML
      const hechas = new Set((await todas()).map(s => s.sid)), saltar = new Set(C.skip);
      const ses = [...lista.querySelectorAll('table tbody tr')].map(r => { const a = r.querySelector('a[href*="eventos_votaciones/"]'); if (!a) return null;
        const t = [...r.cells].map(x => x.textContent.trim()); return { sid: +a.getAttribute('href').split('/').pop(), tipo: t[0], num: t[1], desc: t[2], fecha: iso(t[2]).f }; })
        .filter(s => s && s.fecha && s.fecha >= C.from && s.fecha <= C.to && !saltar.has(s.sid) && !hechas.has(s.sid))
        .sort((a, b) => b.fecha.localeCompare(a.fecha)).slice(0, C.max);
      P.total = ses.length;
      for (const s of ses) {
        if (window.__stop) { P.state = 'detenido a pedido'; return; }
        P.state = 'sesión'; P.sesion++;
        const ev = await get('/eventos_votaciones/' + s.sid), filas = [];
        for (const r of ev.querySelectorAll('table tbody tr')) {
          const a = r.querySelector('a[href*="detalle_de_votacion/"]'); if (!a) continue;
          const t = [...r.cells].map(x => x.textContent.trim().replace(/\s+/g, ' '));
          filas.push({ vid: +a.getAttribute('href').match(/detalle_de_votacion\/(\d+)/)[1], q: t[0], n: t[1], ...iso(t[2]) });
        }
        if (!filas.length) P.avisos.push('Sesión ' + s.sid + ' (' + s.fecha + ') sin votaciones');
        const votaciones = [];
        for (const q of filas) {
          const dt = await get('/detalle_de_votacion/' + q.vid + '/' + s.sid), votos = [];
          dt.querySelectorAll('table[id^="congreso_"]').forEach(tb => { const k = tb.id.replace('congreso_', ''); if (!P.tablas.includes(k)) P.tablas.push(k);
            tb.querySelectorAll('tbody tr').forEach(tr => { const c = [...tr.cells].map(x => x.textContent.trim().replace(/\s+/g, ' '));
              if (c[0] && c[1]) votos.push([c[0], c[1], c[2] || TABLA[k] || k.toUpperCase()]); }); });
          if (!votos.length) throw new Error('Sin filas de votos en la votación ' + q.vid + ': la estructura de la página pudo cambiar');
          if (votos.length < 150) P.avisos.push('Votación ' + q.vid + ' con solo ' + votos.length + ' diputados');
          votaciones.push({ vid: q.vid, q: q.q, n: q.n, f: q.f, h: q.h, votos }); P.votaciones++; P.ultima = s.fecha;
        }
        await guardar({ sid: s.sid, tipo: s.tipo, num: s.num, desc: s.desc, fecha: s.fecha, votaciones });
      }
      P.state = 'terminado';
    } catch (e) { P.state = 'detenido'; P.err = e.message; }
  })();
  return 'iniciado';
})();
