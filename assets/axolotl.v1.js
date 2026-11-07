/* Axolotl — particle scene. Falls back to the still poster on any problem (no WebGL, no three.js,
   missing data, reduced motion, ?nogl). States: "hero" (beside the hero text), "regen" (section 02,
   replays a leg regrowing) and "cloud" (dispersed behind the cards). */
(() => {
  const root = document.documentElement;
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduce || new URLSearchParams(location.search).has('nogl') || !window.THREE) return;
  const canvas = document.getElementById('gl');
  const heroAnchor = document.querySelector('#intro .hero-stage');
  const regenAnchor = document.querySelector('[data-axolotl-stage]');
  if (!canvas || !heroAnchor) return;

  const TILT = -0.38, ROT_Z = 0.36;
  const DATA_URL = 'assets/axolotl.v1.bin';

  start().catch(() => { root.classList.remove('gl-on'); });

  async function start() {
    let renderer;
    try { renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: false, powerPreference: 'high-performance' }); }
    catch (e) { return; }
    const small = innerWidth < 900;
    const finePointer = matchMedia('(pointer: fine)').matches;
    const PR = Math.min(devicePixelRatio || 1, small ? 1.5 : 2);
    renderer.setPixelRatio(PR);

    const res = await fetch(DATA_URL);
    if (!res.ok) throw new Error('data');
    const buf = await res.arrayBuffer();
    const head = new Uint8Array(buf, 0, 4);
    if (String.fromCharCode(...head) !== 'AXL2') throw new Error('format');
    const NB = new DataView(buf).getUint32(4, true);
    const bPos = new Int16Array(buf, 8, 3 * NB);
    const bCol = new Uint8Array(buf, 8 + 6 * NB, 3 * NB);
    const bGeo = new Uint8Array(buf, 8 + 9 * NB, NB);
    const bKind = new Uint8Array(buf, 8 + 10 * NB, NB);
    const bPart = new Uint8Array(buf, 8 + 11 * NB, NB);
    const bGrow = new Uint8Array(buf, 8 + 12 * NB, NB);

    let seed = 7;
    const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
    const randn = () => Math.sqrt(-2 * Math.log(rnd() + 1e-9)) * Math.cos(6.2831853 * rnd());
    const unit = () => { const z = rnd() * 2 - 1, a = rnd() * 6.2831853, r = Math.sqrt(1 - z * z); return [r * Math.cos(a), z, r * Math.sin(a)]; };

    const T = [], C = [], S = [], R = [], G = [], L = [];
    const push = (x, y, z, r, g, b, size, delay, kind, geo, leg, grow) => {
      T.push(x, y, z); C.push(r, g, b); S.push(size); R.push(delay, rnd(), kind, rnd()); G.push(geo); L.push(leg, grow);
    };
    const step = small ? 2 : 1;
    const shoulder = [0, 0, 0]; let ns = 0;
    const legTips = [];
    for (let i = 0; i < NB; i++) {
      const x = bPos[i * 3] / 1000, y = bPos[i * 3 + 1] / 1000, z = bPos[i * 3 + 2] / 1000;
      const k = bKind[i], g = bGeo[i] / 255, leg = bPart[i] === 1 ? 1 : 0, grow = bGrow[i] / 255;
      if (leg && grow < 0.08) { shoulder[0] += x; shoulder[1] += y; shoulder[2] += z; ns++; }
      if (leg && grow > 0.7) legTips.push(i);
      if (i % step && !leg) continue;          // phones keep every leg point so the regrowth stays legible
      const size = k === 1 ? 0.7 + rnd() * 0.9 : k === 2 ? 2.6 : (rnd() < 0.03 ? 2.6 + rnd() * 1.6 : 0.75 + rnd() * 1.2);
      push(x, y, z, bCol[i * 3] / 255, bCol[i * 3 + 1] / 255, bCol[i * 3 + 2] / 255, size,
        Math.min(1, g * 0.85 + rnd() * 0.2), k, g, leg, grow);
    }
    if (ns) { shoulder[0] /= ns; shoulder[1] /= ns; shoulder[2] /= ns; }
    const dust = [[0.91, 0.65, 0.77], [0.72, 0.64, 0.92], [0.61, 0.75, 0.94]];
    for (let i = 0; i < (small ? 500 : 1300); i++) {
      const d = dust[Math.floor(rnd() * 3)];
      push(randn() * 5, randn() * 4, randn() * 3, d[0], d[1], d[2], 0.6 + rnd() * 1.3, rnd(), 5, 0, 0, 0);
    }
    // Amber cells around the whole body during formation
    for (let i = 0; i < (small ? 80 : 180); i++) {
      const j = Math.floor(rnd() * NB), [ux, uy, uz] = unit(), d = 0.25 + rnd() * 0.6;
      push(bPos[j * 3] / 1000 + ux * d, bPos[j * 3 + 1] / 1000 + uy * d, bPos[j * 3 + 2] / 1000 + uz * d,
        0.95, 0.66, 0.23, 1.6 + rnd() * 1.6, bGeo[j] / 255, 6, bGeo[j] / 255, 0, 0);
    }
    // Amber cells that overgrow the regrowing leg, then get removed
    for (let i = 0; i < 40 && legTips.length; i++) {
      const j = legTips[Math.floor(rnd() * legTips.length)], [ux, uy, uz] = unit(), d = 0.15 + rnd() * 0.35;
      push(bPos[j * 3] / 1000 + ux * d, bPos[j * 3 + 1] / 1000 + uy * d, bPos[j * 3 + 2] / 1000 + uz * d * 0.4,
        0.95, 0.66, 0.23, 1.8 + rnd() * 1.6, 1, 7, bGeo[j] / 255, 0, 0);
    }

    const count = T.length;
    const start = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      const [ux, uy, uz] = unit(), d = 7 + rnd() * 12;
      start[i * 3] = T[i * 3] + ux * d; start[i * 3 + 1] = T[i * 3 + 1] + uy * d; start[i * 3 + 2] = T[i * 3 + 2] + uz * d;
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.Float32BufferAttribute(T, 3));
    geo.setAttribute('aStart', new THREE.BufferAttribute(start, 3));
    geo.setAttribute('aColor', new THREE.Float32BufferAttribute(C, 3));
    geo.setAttribute('aSize', new THREE.Float32BufferAttribute(S, 1));
    geo.setAttribute('aRand', new THREE.Float32BufferAttribute(R, 4));
    geo.setAttribute('aGeo', new THREE.Float32BufferAttribute(G, 1));
    geo.setAttribute('aLeg', new THREE.Float32BufferAttribute(L, 2));

    const uniforms = {
      uTime: { value: 0 }, uForm: { value: 0 }, uClean: { value: 0 }, uCloud: { value: 0 },
      uRegen: { value: 1 }, uRegenT: { value: 0 }, uShoulder: { value: new THREE.Vector3(...shoulder) },
      uPR: { value: PR }, uScale: { value: 1 }, uMouse: { value: new THREE.Vector2(99, 99) }
    };
    const material = new THREE.ShaderMaterial({
      uniforms, transparent: true, depthWrite: false,
      vertexShader: `
        uniform float uTime, uForm, uClean, uCloud, uRegen, uRegenT, uPR, uScale;
        uniform vec3 uShoulder;
        uniform vec2 uMouse;
        attribute vec3 aStart, aColor;
        attribute float aSize, aGeo;
        attribute vec4 aRand;
        attribute vec2 aLeg;
        varying vec3 vColor;
        varying float vAlpha;
        float ease(float t){ return t < .5 ? 4.*t*t*t : 1. - pow(-2.*t + 2., 3.) / 2.; }
        void main(){
          float delay = aRand.x, ph = aRand.y * 6.2831853, kind = aRand.z, r = aRand.w;
          float f = ease(clamp(uForm * 1.7 - delay * 0.7, 0., 1.));
          vec3 p = position;
          vec3 col = aColor;
          float a = 0.88;
          // Leg regrowth: points beyond the growth front are folded back to the shoulder and hidden
          if (aLeg.x > 0.5) {
            float vis = 1. - smoothstep(uRegen - 0.04, uRegen + 0.04, aLeg.y);
            p = mix(uShoulder, p, vis);
            a *= vis;
            float front = 1. - smoothstep(0., 0.08, abs(aLeg.y - uRegen));
            col = mix(col, vec3(1., .86, .92), front * step(uRegen, 0.999) * 0.8);
          }
          // Swimming wave, growing towards the tail
          float amp = smoothstep(0.15, 1., aGeo);
          p.z += sin(uTime * 1.7 - aGeo * 7.) * 0.55 * amp;
          p.x += sin(uTime * 1.2 - aGeo * 5.) * 0.12 * amp;
          if (kind > 0.5 && kind < 1.5) {
            p.z += sin(uTime * 2.6 + abs(p.x) * 3. + p.y * 2.) * 0.12;
            p.x += sign(p.x) * (0.5 + 0.5 * sin(uTime * 1.3 + p.y)) * 0.05;
          }
          if (kind > 2.5 && kind < 3.5) p.z += sin(uTime * 1.9 + sign(p.x) * 1.6 + p.y) * 0.16;
          p += vec3(sin(uTime * .7 + ph * 3.), cos(uTime * .9 + ph * 2.), sin(uTime * .8 + ph * 5.)) * 0.012;
          if (kind > 4.5 && kind < 5.5) { p += vec3(sin(uTime * .2 + ph * 4.), cos(uTime * .17 + ph * 3.), sin(uTime * .15 + ph)) * 0.6; a = 0.28; }
          // Cloud: the shape loosens into a soft cloud
          vec3 dir = normalize(aStart - position + 0.0001);
          p += dir * uCloud * (0.4 + r * 3.);
          vec3 pos = mix(aStart, p, f);
          vec4 mv = modelViewMatrix * vec4(pos, 1.);
          vec2 d = mv.xy - uMouse;
          float dl = length(d);
          mv.xy += d / (dl + 0.0001) * smoothstep(1.6, 0., dl) * 0.5 * f * (1. - uCloud);
          gl_Position = projectionMatrix * mv;
          gl_PointSize = aSize * uPR * mix(1., uScale, .6) * (24. / -mv.z);
          if (kind > 5.5 && kind < 6.5) {
            float gone = smoothstep(r * 0.6, r * 0.6 + 0.4, uClean);
            a = 0.95 * (1. - gone);
            gl_PointSize *= 1. + 0.8 * (1. - gone) * (0.5 + 0.5 * sin(uTime * 6. + ph));
          }
          if (kind > 6.5) {
            float on = smoothstep(0.2, 0.3, uRegenT - r * 0.1) * (1. - smoothstep(0.7, 0.85, uRegenT + r * 0.05));
            a = 0.95 * on * (1. - uCloud);
            gl_PointSize *= 1. + 0.7 * on * (0.5 + 0.5 * sin(uTime * 7. + ph));
          }
          vColor = col;
          vAlpha = a * (0.1 + 0.9 * f) * (1. - uCloud * 0.3);
        }`,
      fragmentShader: `
        varying vec3 vColor;
        varying float vAlpha;
        void main(){
          float d = length(gl_PointCoord - .5);
          if (d > .5) discard;
          gl_FragColor = vec4(vColor, smoothstep(.5, .1, d) * vAlpha);
        }`
    });
    const points = new THREE.Points(geo, material);
    points.frustumCulled = false;
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(35, 1, 0.1, 100);
    camera.position.set(0, 0, 18);
    const inner = new THREE.Group(), outer = new THREE.Group();
    inner.add(points); outer.add(inner); scene.add(outer);
    inner.rotation.x = TILT;
    outer.rotation.z = ROT_Z;

    // Size of the posed animal on screen, used to fit it into its anchor box
    const box = new THREE.Box3();
    const v = new THREE.Vector3();
    outer.updateMatrixWorld(true);
    for (let i = 0; i < NB; i += 7) {
      v.set(bPos[i * 3] / 1000, bPos[i * 3 + 1] / 1000, bPos[i * 3 + 2] / 1000).applyMatrix4(points.matrixWorld);
      box.expandByPoint(v);
    }
    const objW = box.max.x - box.min.x, objH = box.max.y - box.min.y;
    const objCx = (box.max.x + box.min.x) / 2, objCy = (box.max.y + box.min.y) / 2;

    let halfH = 1, halfW = 1;
    function resize() {
      renderer.setSize(innerWidth, innerHeight, false);
      camera.aspect = innerWidth / innerHeight;
      camera.updateProjectionMatrix();
      halfH = Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)) * camera.position.z;
      halfW = halfH * camera.aspect;
    }
    addEventListener('resize', resize);
    addEventListener('orientationchange', resize);
    resize();

    // Where should the animal be? Recomputed every frame from the anchors, so scroll restore, resize
    // and orientation changes are all handled the same way.
    const visibleShare = el => {
      const r = el.getBoundingClientRect();
      if (!r.height) return 0;
      return Math.max(0, Math.min(r.bottom, innerHeight) - Math.max(r.top, 0)) / r.height;
    };
    function fit(el) {
      const r = el.getBoundingClientRect();
      const wW = r.width / innerWidth * 2 * halfW, wH = r.height / innerHeight * 2 * halfH;
      const s = Math.min(wH * 0.95 / objH, wW * 0.98 / objW);
      return {
        x: ((r.left + r.width / 2) / innerWidth * 2 - 1) * halfW - objCx * s,
        y: -((r.top + r.height / 2) / innerHeight * 2 - 1) * halfH - objCy * s,
        s
      };
    }
    function target() {
      if (visibleShare(heroAnchor) > 0.3) return { state: 'hero', ...fit(heroAnchor) };
      if (regenAnchor && visibleShare(regenAnchor) > 0.3) return { state: 'regen', ...fit(regenAnchor) };
      return { state: 'cloud' };
    }

    const mouse = { tx: 0, ty: 0, x: 0, y: 0, in: false };
    if (finePointer) {
      addEventListener('pointermove', e => { mouse.tx = e.clientX / innerWidth * 2 - 1; mouse.ty = -(e.clientY / innerHeight * 2 - 1); mouse.in = true; }, { passive: true });
      document.addEventListener('pointerleave', () => { mouse.in = false; });
    }

    let running = true;
    canvas.addEventListener('webglcontextlost', e => { e.preventDefault(); running = false; root.classList.remove('gl-on'); });

    if (new URLSearchParams(location.search).has('debug')) window.__axolotl = { uniforms, get state() { return state; } };
    const first = target();
    const cur = { x: first.x ?? 0, y: first.y ?? 0, s: first.s ?? 1, cloud: first.state === 'cloud' ? 1 : 0 };
    let state = first.state, regenStart = -1, regenPending = state === 'regen', shown = false;
    const t0 = performance.now();
    let last = t0;
    const ease = t => 1 - Math.pow(1 - t, 3);

    function frame(now) {
      if (!running) return;
      const t = (now - t0) / 1000;
      const dt = Math.min(0.1, (now - last) / 1000); last = now;
      const kMove = 1 - Math.exp(-dt * 5), kCloud = 1 - Math.exp(-dt * 3.6), kMouse = 1 - Math.exp(-dt * 3.6);
      uniforms.uTime.value = t;
      uniforms.uForm.value = Math.min(1, Math.max(0, (t - 0.2) / 3.6));
      uniforms.uClean.value = Math.min(1, Math.max(0, (t - 3.4) / 1.6));

      const tg = target();
      if (tg.state !== state) {
        if (tg.state === 'regen') regenPending = true;
        state = tg.state;
      }
      // The browser restores the scroll position (or jumps to a #hash) after this script starts:
      // during the first moments, follow the target instantly instead of gliding from the hero.
      const settle = t < 0.8 ? 1 : 0;
      if (tg.state !== 'cloud') {
        const k = settle || kMove;
        cur.x += (tg.x - cur.x) * k; cur.y += (tg.y - cur.y) * k; cur.s += (tg.s - cur.s) * k;
      }
      cur.cloud += ((tg.state === 'cloud' ? 1 : 0) - cur.cloud) * (settle || kCloud);
      if (settle) { regenPending = tg.state === 'regen'; }
      uniforms.uCloud.value = cur.cloud;
      uniforms.uScale.value = cur.s;

      // Leg regrowth, once per entry into section 02, after the body has formed
      if (regenPending && uniforms.uForm.value >= 1 && cur.cloud < 0.2) { regenPending = false; regenStart = t; }
      if (regenStart >= 0) {
        const e = t - regenStart;
        if (e < 0.6) { uniforms.uRegen.value = 1 - ease(e / 0.6); uniforms.uRegenT.value = 0; }
        else if (e < 3.0) { const k = (e - 0.6) / 2.4; uniforms.uRegen.value = ease(k); uniforms.uRegenT.value = k; }
        else { uniforms.uRegen.value = 1; uniforms.uRegenT.value = 1; regenStart = -1; }
      }

      mouse.x += (mouse.tx - mouse.x) * kMouse; mouse.y += (mouse.ty - mouse.y) * kMouse;
      uniforms.uMouse.value.set(mouse.in ? mouse.tx * halfW : 99, mouse.in ? mouse.ty * halfH : 99);

      outer.position.set(cur.x, cur.y, 0);
      outer.scale.setScalar(cur.s);
      outer.rotation.x = -mouse.y * 0.12;
      outer.rotation.y = mouse.x * 0.18 + cur.cloud * 0.5;
      inner.rotation.x = TILT + Math.sin(t * 0.3) * 0.06;
      inner.rotation.y = Math.sin(t * 0.22) * 0.1;
      renderer.render(scene, camera);
      if (!shown) { shown = true; root.classList.add('gl-on'); }
      requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
  }
})();
