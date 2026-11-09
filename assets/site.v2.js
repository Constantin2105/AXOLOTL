/* Axolotl — page UI (everything except the particle scene). Works on its own if the scene fails. */
(() => {
  const root = document.documentElement;
  root.classList.add('ui');
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
  const easeOut = t => 1 - Math.pow(1 - t, 3);

  /* ---------- Title, word by word ---------- */
  const title = document.getElementById('title');
  if (title) {
    title.setAttribute('aria-label', title.textContent);
    title.innerHTML = title.innerHTML.trim().split(' ').map((w, i) =>
      `<span class="w" aria-hidden="true"><span style="transition-delay:${(0.3 + i * 0.07).toFixed(2)}s">${w}</span></span>`).join(' ');
  }
  requestAnimationFrame(() => requestAnimationFrame(() => root.classList.add('ready')));

  /* ---------- Menu ---------- */
  const toggle = document.getElementById('menu-toggle');
  const menu = document.getElementById('menu');
  const label = toggle && toggle.querySelector('.menu-label');
  function setMenu(open) {
    if (!menu) return;
    toggle.setAttribute('aria-expanded', String(open));
    if (label) label.textContent = open ? (toggle.dataset.closeLabel || 'Fermer') : (toggle.dataset.openLabel || 'Menu');
    document.body.classList.toggle('menu-open', open);
    if (open) {
      menu.hidden = false;
      requestAnimationFrame(() => requestAnimationFrame(() => menu.classList.add('open')));
      const first = menu.querySelector('a');
      if (first) first.focus({ preventScroll: true });
    } else {
      menu.classList.remove('open');
      menu.hidden = true;
    }
  }
  if (toggle && menu) {
    toggle.addEventListener('click', () => setMenu(menu.hidden));
    menu.addEventListener('click', e => { if (e.target.closest('a')) setMenu(false); });
    document.addEventListener('keydown', e => {
      if (menu.hidden) return;
      if (e.key === 'Escape') { setMenu(false); toggle.focus(); return; }
      if (e.key !== 'Tab') return;
      const items = [toggle, ...menu.querySelectorAll('a')];
      const i = items.indexOf(document.activeElement);
      const next = e.shiftKey ? (i <= 0 ? items.length - 1 : i - 1) : (i === items.length - 1 || i < 0 ? 0 : i + 1);
      e.preventDefault();
      items[next].focus();
    });
  }

  /* ---------- Side rail ---------- */
  const links = [...document.querySelectorAll('.rail a[data-for]')];
  const dot = document.querySelector('.rail .dot');
  const sections = [...document.querySelectorAll('[data-sec]')];
  let current = '';
  function updateRail() {
    const mid = innerHeight * 0.5;
    let id = sections.length ? sections[0].id : '';
    for (const s of sections) if (s.getBoundingClientRect().top < mid) id = s.id;
    if (id === current) return;
    current = id;
    for (const a of links) {
      const on = a.dataset.for === id;
      a.classList.toggle('on', on);
      if (on) {
        a.setAttribute('aria-current', 'true');
        if (dot) dot.style.top = (a.parentElement.offsetTop + a.parentElement.offsetHeight / 2 - 4.5) + 'px';
      } else a.removeAttribute('aria-current');
    }
  }

  /* ---------- Reveals ---------- */
  const revealIO = new IntersectionObserver(entries => {
    for (const e of entries) if (e.isIntersecting) { e.target.classList.add('in'); revealIO.unobserve(e.target); }
  }, { rootMargin: '0px 0px -2% 0px' });
  document.querySelectorAll('.reveal, .stagger').forEach(el => revealIO.observe(el));

  /* ---------- Counters: count up once, then put the original text back exactly ---------- */
  const decimalMark = document.documentElement.lang === 'en' ? '.' : ',';
  const fmt = (v, d) => v.toFixed(d).replace('.', decimalMark);
  const countIO = new IntersectionObserver(entries => {
    for (const e of entries) {
      if (!e.isIntersecting) continue;
      countIO.unobserve(e.target);
      const el = e.target, original = el.innerHTML;
      const to = parseFloat(el.dataset.count), dec = parseInt(el.dataset.decimals || '0', 10);
      const suffix = original.replace(/^[\d.,]+/, '');
      const t0 = performance.now();
      const step = now => {
        const t = clamp((now - t0) / 1400, 0, 1);
        if (t < 1) { el.innerHTML = fmt(to * easeOut(t), dec) + suffix; requestAnimationFrame(step); }
        else el.innerHTML = original;
      };
      requestAnimationFrame(step);
    }
  }, { threshold: 0.6 });
  if (!reduce) document.querySelectorAll('.num-figure[data-count]').forEach(el => countIO.observe(el));

  /* ---------- Synthetic mammogram with scan + flagged zones ---------- */
  const viewer = document.querySelector('.viewer');
  const sc = document.getElementById('scan');
  const scanline = document.querySelector('.scanline');
  const AMBER = '#f2a93b';
  // roundRect needs Safari 16 / Firefox 112: fall back to square corners rather than throwing
  const rr = (ctx, x, y, w, h, r) => { ctx.beginPath(); if (ctx.roundRect) ctx.roundRect(x, y, w, h, r); else ctx.rect(x, y, w, h); };
  let base = null, zones = null, prog = [0, 0];

  function renderBase() {
    const r = sc.getBoundingClientRect(), d = Math.min(devicePixelRatio || 1, 2);
    const w = r.width, h = r.height;
    if (!w || !h) return false;
    sc.width = w * d; sc.height = h * d;
    base = document.createElement('canvas');
    base.width = sc.width; base.height = sc.height;
    const c = base.getContext('2d');
    c.setTransform(d, 0, 0, d, 0, 0);
    c.fillStyle = '#000'; c.fillRect(0, 0, w, h);
    const cx = w * 0.06, cy = h * 0.52, R = Math.min(w * 0.62, h * 0.62);
    const shape = new Path2D();
    shape.moveTo(0, h * 0.04);
    shape.bezierCurveTo(R * 0.9, h * 0.06, R * 1.25, cy - R * .55, R * 1.18, cy + R * .05);
    shape.bezierCurveTo(R * 1.1, cy + R * .7, R * .55, h * 0.98, 0, h);
    shape.closePath();
    c.save(); c.clip(shape);
    const g = c.createRadialGradient(cx, cy, R * .1, cx, cy, R * 1.3);
    g.addColorStop(0, '#9a9a9a'); g.addColorStop(.55, '#6a6a6a'); g.addColorStop(1, '#2a2a2a');
    c.fillStyle = g; c.fillRect(0, 0, w, h);
    let seed = 7; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
    c.filter = 'blur(2px)'; c.globalCompositeOperation = 'lighter';
    for (let i = 0; i < 260; i++) {
      const y0 = h * (0.05 + rnd() * 0.9), x0 = rnd() * R * .4;
      c.strokeStyle = `rgba(255,255,255,${0.025 + rnd() * 0.05})`; c.lineWidth = 1 + rnd() * 5;
      c.beginPath(); c.moveTo(x0, y0);
      c.quadraticCurveTo(R * (0.5 + rnd() * .3), y0 + (cy - y0) * .4 + (rnd() - .5) * 60, R * 1.12, cy + (rnd() - .5) * 30);
      c.stroke();
    }
    c.filter = 'blur(6px)';
    for (let i = 0; i < 90; i++) { c.fillStyle = `rgba(255,255,255,${0.03 + rnd() * .05})`; c.beginPath(); c.arc(rnd() * R, h * (.1 + rnd() * .8), 6 + rnd() * 26, 0, 7); c.fill(); }
    const z1 = [R * .62, cy - R * .32], z2 = [R * .95, cy + R * .06];
    c.filter = 'blur(3px)'; c.fillStyle = 'rgba(255,255,255,.22)'; c.beginPath(); c.arc(z1[0], z1[1], 13, 0, 7); c.fill();
    c.filter = 'none'; c.fillStyle = 'rgba(255,255,255,.55)';
    for (let i = 0; i < 9; i++) { c.beginPath(); c.arc(z2[0] + (rnd() - .5) * 14, z2[1] + (rnd() - .5) * 12, .9 + rnd() * .8, 0, 7); c.fill(); }
    c.restore(); c.globalCompositeOperation = 'source-over'; c.filter = 'none';
    const img = c.getImageData(0, 0, base.width, base.height), p = img.data;
    for (let i = 0; i < p.length; i += 4) { const n = (rnd() - .5) * 18; p[i] += n; p[i + 1] += n; p[i + 2] += n; }
    c.putImageData(img, 0, 0);
    c.setTransform(d, 0, 0, d, 0, 0);
    c.strokeStyle = '#9aa3a8'; c.lineWidth = 1; c.beginPath(); c.moveTo(w - 100, h - 24); c.lineTo(w - 40, h - 24); c.stroke();
    c.fillStyle = '#9aa3a8'; c.font = '12px "IBM Plex Mono", monospace'; c.textAlign = 'right'; c.fillText('10 mm', w - 40, h - 32);
    zones = [[z1[0], z1[1], 26, '1'], [z2[0], z2[1], 20, '2']];
    return true;
  }

  function paint() {
    if (!base) return;
    const c = sc.getContext('2d'), d = sc.width / sc.getBoundingClientRect().width;
    c.setTransform(1, 0, 0, 1, 0, 0);
    c.drawImage(base, 0, 0);
    c.setTransform(d, 0, 0, d, 0, 0);
    zones.forEach(([x, y, s, n], i) => {
      const t = prog[i];
      if (t <= 0) return;
      const per = s * 8;
      c.save();
      c.strokeStyle = AMBER; c.lineWidth = 2;
      c.setLineDash([per, per]); c.lineDashOffset = per * (1 - t);
      rr(c, x - s, y - s, s * 2, s * 2, 6); c.stroke();
      c.restore();
      const a = clamp((t - 0.7) / 0.3, 0, 1);
      if (a > 0) {
        c.globalAlpha = a;
        c.fillStyle = AMBER; rr(c, x + s - 4, y - s - 26, 22, 22, 6); c.fill();
        c.fillStyle = '#111518'; c.font = '500 12px "IBM Plex Mono", monospace'; c.textAlign = 'center'; c.textBaseline = 'middle';
        c.fillText(n, x + s + 7, y - s - 15);
        c.globalAlpha = 1; c.textBaseline = 'alphabetic';
      }
    });
  }

  function tween(ms, onStep) {
    return new Promise(res => {
      const t0 = performance.now();
      const f = now => {
        const t = clamp((now - t0) / ms, 0, 1);
        try { onStep(t); } catch (e) { res(); return; }
        t < 1 ? requestAnimationFrame(f) : res();
      };
      requestAnimationFrame(f);
    });
  }

  async function playScan() {
    try {
      const h = sc.getBoundingClientRect().height;
      if (scanline) {
        scanline.style.opacity = '1';
        await tween(1600, t => { scanline.style.transform = `translateY(${(easeOut(t) * h).toFixed(1)}px)`; });
        scanline.style.transition = 'opacity .5s'; scanline.style.opacity = '0';
      }
      await tween(700, t => { prog[0] = easeOut(t); paint(); });
      await tween(700, t => { prog[1] = easeOut(t); paint(); });
    } finally {
      viewer.classList.add('done');   // the zone list must never stay hidden
    }
  }

  if (viewer && sc) {
    const fonts = document.fonts ? document.fonts.ready : Promise.resolve();
    fonts.then(() => {
      renderBase();
      if (reduce) { prog = [1, 1]; try { paint(); } finally { viewer.classList.add('done'); } return; }
      paint();
      const io = new IntersectionObserver(es => {
        if (es.some(e => e.isIntersecting)) { io.disconnect(); playScan(); }
      }, { threshold: 0.45 });
      io.observe(sc);
    });
    let rs;
    addEventListener('resize', () => { clearTimeout(rs); rs = setTimeout(() => { renderBase(); paint(); }, 200); });
  }

  /* ---------- Roadmap line follows the scroll ---------- */
  const road = document.querySelector('.road');
  function updateRoad() {
    if (!road || reduce) return;
    const r = road.getBoundingClientRect();
    const p = clamp((innerHeight * 0.9 - r.top) / (innerHeight * 0.55), 0, 1);
    road.style.setProperty('--progress', p.toFixed(3));
  }

  /* ---------- Scroll loop ---------- */
  let ticking = false;
  function onScroll() {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(() => { ticking = false; updateRail(); updateRoad(); });
  }
  addEventListener('scroll', onScroll, { passive: true });
  addEventListener('resize', onScroll);
  updateRail(); updateRoad();
})();
