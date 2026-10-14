/* ZOLLER Produktumgebung 3D – AR-/3D-Ansicht der Produkte mit echten CAD-Daten
   (dieselben Modelle und Texte wie auf den Produktseiten der Webseite, tools/ar.py -> data.ar, product.ar).
   - iPhone/iPad: AR Quick Look direkt mit der USDZ-Datei (Banner »Jetzt anfragen« führt zum Kontakt)
   - Android: Scene Viewer direkt, im Dialog WebXR über model-viewer
   - Rechner: Dialog mit drehbarem CAD-Modell, Maßlinien und QR-Code fürs Handy (#ar/<produkt>/<modell>)
   model-viewer (assets/vendor, enthält eigenes three.js) lädt erst beim ersten Öffnen des Dialogs. */

export const ICON_AR = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 8V5a2 2 0 0 1 2-2h3M16 3h3a2 2 0 0 1 2 2v3M21 16v3a2 2 0 0 1-2 2h-3M8 21H5a2 2 0 0 1-2-2v-3"/><path d="M12 6.8 16.5 9.4v5.2L12 17.2l-4.5-2.6V9.4z"/><path d="M7.5 9.4 12 12l4.5-2.6M12 12v5.2"/></svg>';
const ICON_EXT = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/></svg>';
const ICON_PLAN = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3.5 3.5h7v7h-7zM13.5 3.5h7v4h-7zM13.5 10.5h7v10h-7zM3.5 13.5h7v7h-7z"/></svg>';

const ua = navigator.userAgent;
const IOS = /iPad|iPhone|iPod/.test(ua) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
const QL = IOS && (() => { const a = document.createElement('a'); return !!(a.relList && a.relList.supports && a.relList.supports('ar')); })();
const ANDROID = /Android/i.test(ua);
export const MOBILE = QL || ANDROID;
const REDUCED = matchMedia('(prefers-reduced-motion: reduce)').matches;
const ORBIT = '-28deg 74deg auto';
const ORBIT_IN = '-62deg 78deg auto';
const DIMS = ['w', 'd', 'h'];
const SVGNS = 'http://www.w3.org/2000/svg';
const here = () => location.href.split('#')[0];

export function createAR({ data, byId, base = '', tr, esc, contact, onOpen, onClose }) {
  const AR = data.ar;
  const T = AR.t;
  const model = (id) => {
    const m = AR.models[id];
    const lab = (k) => m[k] + (m[k + '2'] ? ` (${m[k + '2']})` : '');
    return { id, ...m, glb: `${base}ar/${id}.glb?v=${m.v}`, usdz: `${base}ar/${id}.usdz?v=${m.v}`, poster: `${base}ar/${id}.webp?v=${m.v}`,
      lab_w: lab('w'), lab_d: lab('d'), lab_h: lab('h') };
  };
  const st = { open: false, pid: null, m: null, mv: null, dimsOn: false, dimKey: '', r0: 1, touched: false, from: null };

  /* ---------------------------------------------------------------- AR starten (ohne Dialog) */
  function quickLookUrl(m) {
    const u = new URL(m.usdz, location.href), enc = encodeURIComponent;
    u.hash = `callToAction=${enc(T.cta)}&checkoutTitle=${enc(m.name)}&checkoutSubtitle=${enc(m.full)}&allowsContentScaling=0`;
    return u.href;
  }
  let qlAnchor = null;
  function quickLook(m) {
    // <a rel="ar"> mit <img> als erstem Kind, Klick noch in der Nutzergeste (kein await davor)
    if (!qlAnchor) {
      qlAnchor = document.createElement('a');
      qlAnchor.rel = 'ar'; qlAnchor.style.display = 'none';
      qlAnchor.appendChild(document.createElement('img'));
      qlAnchor.addEventListener('message', (e) => { if (e.data === '_apple_ar_quicklook_button_tapped') location.href = contact; });
      document.body.appendChild(qlAnchor);
    }
    qlAnchor.href = quickLookUrl(m);
    qlAnchor.click();
  }
  function sceneViewer(m, pid) {
    const glb = new URL(m.glb, location.href); glb.search = '';
    const p = new URLSearchParams({ mode: 'ar_preferred', resizable: 'false', disable_occlusion: 'true', title: m.name.replace(/[»«]/g, ''), link: `${here()}#produkt/${pid}` });
    location.href = `intent://arvr.google.com/scene-viewer/1.2?${p}&file=${encodeURIComponent(glb.href)}` +
      `#Intent;scheme=https;package=com.google.android.googlequicksearchbox;action=android.intent.action.VIEW;` +
      `S.browser_fallback_url=${encodeURIComponent(`${here()}#ar/${pid}/${m.id}`)};end;`;
  }
  // Knopf »In AR ansehen«: auf Handy/Tablet sofort AR, am Rechner der Dialog mit QR-Code
  function start(pid, mid) {
    const p = byId.get(pid); if (!p?.ar) return;
    const m = model(p.ar.includes(mid) ? mid : (st.open && st.pid === pid && st.m ? st.m.id : p.ar[0]));
    if (QL) return quickLook(m);
    if (ANDROID) { if (st.open && st.mv?.canActivateAR) return st.mv.activateAR(); return sceneViewer(m, pid); }
    open(pid, m.id);
  }

  /* ---------------------------------------------------------------- Dialog */
  const tool = (k, path) => `<button type="button" class="arv__tool" data-tool="${k}" aria-label="${esc(T[k])}" title="${esc(T[k])}"><svg viewBox="0 0 24 24" aria-hidden="true">${path}</svg></button>`;
  const dlg = document.createElement('div');
  dlg.className = 'arv'; dlg.hidden = true;
  dlg.setAttribute('role', 'dialog'); dlg.setAttribute('aria-modal', 'true'); dlg.setAttribute('aria-labelledby', 'arv-title');
  dlg.innerHTML = `<div class="arv__card">
      <div class="arv__stage" data-stage>
        <img class="arv__poster" data-poster alt="" decoding="async">
        <div class="arv__loading" data-loading hidden><i></i><span>${esc(T.loading)}</span></div>
        <span class="arv__hint" data-hint hidden>${esc(T.drag)}</span>
        <div class="arv__tools" data-tools hidden>
          <button type="button" class="arv__tool arv__tool--dims" data-tool="dims" aria-pressed="false"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 17h18M3 14v6M21 14v6M7 17v-2M11 17v-3M15 17v-2M19 17v-1"/></svg><span>${esc(T.dims)}</span></button>
          ${tool('zoom_out', '<path d="M5 12h14"/>')}${tool('zoom_in', '<path d="M5 12h14M12 5v14"/>')}
          ${tool('reset', '<path d="M4 12a8 8 0 1 0 2.4-5.7"/><path d="M4 4v4h4"/>')}
          ${document.fullscreenEnabled || document.webkitFullscreenEnabled ? tool('fullscreen', '<path d="M4 9V4h5M15 4h5v5M20 15v5h-5M9 20H4v-5"/>') : ''}
        </div>
        ${MOBILE ? `<button type="button" class="arv__stagego" data-go>${ICON_AR}<span>${esc(T.ar)}</span></button>` : ''}
      </div>
      <div class="arv__info">
        <span class="arv__eyebrow">${esc(T.eyebrow)}</span>
        <h2 class="arv__title" id="arv-title" data-out="title"></h2>
        <p class="arv__shown" data-shown hidden></p>
        <p class="arv__lead">${esc(T.lead)}</p>
        <div class="arv__chips" data-chips role="radiogroup" aria-label="${esc(T.model)}" hidden></div>
        <dl class="arv__dims">${['w', 'd', 'h', 'area'].map((k) => `<div><dt>${esc(T[k])}</dt><dd><span data-out="${k}"></span><small data-out="${k}2"></small></dd></div>`).join('')}</dl>
        <p class="arv__note">${esc(T.note)}</p>
        ${MOBILE ? `<p class="arv__arhint">${esc(T.ar_hint)}</p>` : ''}
        <p class="arv__msg" data-msg role="status" hidden></p>
        <div class="arv__qr" data-qr hidden><div class="arv__qrcode" data-qrcode aria-hidden="true"></div><div><b>${esc(T.qr_title)}</b><p>${esc(T.qr_text)}</p></div></div>
        <div class="arv__actions">
          <a class="btn btn--primary" data-page href="#">${esc(tr('Zur Produktseite'))} ${ICON_EXT}</a>
          <a class="btn" href="${esc(AR.planer)}">${ICON_PLAN} ${esc(T.planer)}</a>
        </div>
      </div>
      <button type="button" class="round round--close arv__close" data-close aria-label="${esc(tr('Schließen'))}" title="${esc(tr('Schließen'))}"><svg viewBox="0 0 24 24"><path d="M6 6l12 12M18 6 6 18"/></svg></button>
    </div>`;
  (document.getElementById('app') || document.body).appendChild(dlg);
  const $ = (s) => dlg.querySelector(s);
  const stage = $('[data-stage]'), poster = $('[data-poster]');

  function msg(text) { const el = $('[data-msg]'); el.textContent = text || ''; el.hidden = !text; }

  function apply(m) {
    st.m = m;
    for (const k of ['title', 'w', 'd', 'h', 'area', 'w2', 'd2', 'h2', 'area2']) { const el = $(`[data-out="${k}"]`); if (el) el.textContent = m[k] || ''; }
    stage.setAttribute('aria-label', m.label);
    poster.src = m.poster; poster.alt = m.label;
    dlg.querySelectorAll('[data-model]').forEach((b) => b.setAttribute('aria-checked', String(b.dataset.model === m.id)));
    if (st.mv) {
      // das bisherige Modell bleibt stehen, bis das neue geladen ist (model-viewer tauscht dann)
      st.mv.src = m.glb; st.mv.iosSrc = quickLookUrl(m); st.mv.alt = m.label;
      st.dimKey = ''; dimLabels();
    }
    showQR();
    onOpen?.(st.pid, m.id);
  }

  function open(pid, mid) {
    const p = byId.get(pid); if (!p?.ar) return false;
    const first = !st.open;
    if (first) st.from = document.activeElement;
    if (st.pid !== pid && st.dimsOn) setDims(false);   // neues Produkt: erst ohne Maßlinien
    st.pid = pid;
    const ids = p.ar, m = model(ids.includes(mid) ? mid : ids[0]);
    const chips = $('[data-chips]');
    chips.hidden = ids.length < 2;
    chips.innerHTML = ids.length < 2 ? '' : ids.map((id) => `<button type="button" class="arv__chip" role="radio" data-model="${id}" aria-checked="false">${esc(AR.models[id].name)}</button>`).join('');
    const shown = $('[data-shown]'); shown.textContent = p.arShown || ''; shown.hidden = !p.arShown;
    $('[data-page]').href = p.url;
    msg('');
    dlg.hidden = false; st.open = true;
    document.documentElement.classList.add('arv-open');
    if (st.mv && st.m && st.m.id !== m.id) stage.classList.remove('is-loaded');
    apply(m);
    if (first) { requestAnimationFrame(() => dlg.classList.add('is-in')); $('[data-close]').focus({ preventScroll: true }); }
    build();
    if (st.dimsOn) dimLoop();
    return true;
  }
  function close() {
    if (!st.open) return;
    st.open = false;
    dlg.classList.remove('is-in'); dlg.hidden = true;
    document.documentElement.classList.remove('arv-open');
    if (document.fullscreenElement) document.exitFullscreen?.();
    onClose?.(st.pid);
    st.from?.focus?.({ preventScroll: true });
  }

  /* ---------------------------------------------------------------- QR-Code (Rechner) */
  let qrLoad = null;
  function showQR() {
    const box = $('[data-qr]');
    if (MOBILE || !st.m) { box.hidden = true; return; }
    qrLoad ||= new Promise((ok, fail) => { const s = document.createElement('script'); s.src = `${base}assets/vendor/qrcode.js`; s.onload = ok; s.onerror = fail; document.head.appendChild(s); });
    const url = `${location.origin}${location.pathname}#ar/${st.pid}/${st.m.id}`;
    qrLoad.then(() => {
      const q = window.qrcode(0, 'M'); q.addData(url); q.make();
      $('[data-qrcode]').innerHTML = q.createSvgTag({ cellSize: 4, margin: 0, scalable: true });
      box.hidden = false;
    }).catch(() => { box.hidden = true; });
  }

  /* ---------------------------------------------------------------- 3D-Modell (model-viewer) */
  let mvLoad = null;
  function loadMV() {
    mvLoad ||= new Promise((ok, fail) => {
      self.ModelViewerElement = Object.assign(self.ModelViewerElement || {}, { dracoDecoderLocation: `${base}assets/vendor/draco/` });
      const s = document.createElement('script');
      s.type = 'module'; s.src = `${base}assets/vendor/model-viewer.min.js`; s.onerror = fail;
      document.head.appendChild(s);
      customElements.whenDefined('model-viewer').then(ok);
    });
    return mvLoad;
  }
  function build() {
    if (st.mv || st.building) return;
    st.building = true;
    const loading = $('[data-loading]');
    const slow = setTimeout(() => { if (!stage.classList.contains('is-loaded')) loading.hidden = false; }, 350);
    loadMV().then(() => {
      const m = st.m;
      const mv = st.mv = document.createElement('model-viewer');
      const attrs = {
        src: m.glb, 'ios-src': quickLookUrl(m), alt: m.label,
        ar: '', 'ar-modes': 'webxr scene-viewer quick-look', 'ar-scale': 'fixed', 'ar-placement': 'floor',
        'camera-controls': '', 'touch-action': 'pan-y', 'interaction-prompt': 'none',
        'environment-image': 'legacy', exposure: '1.1', 'tone-mapping': 'neutral',
        'shadow-intensity': '1', 'shadow-softness': '0.85',
        'camera-orbit': REDUCED ? ORBIT : ORBIT_IN, 'min-camera-orbit': 'auto 18deg auto', 'max-camera-orbit': 'auto 92deg auto',
        'interpolation-decay': '110', loading: 'eager',
      };
      for (const [k, v] of Object.entries(attrs)) mv.setAttribute(k, v);
      const slot = document.createElement('span'); slot.slot = 'ar-button'; slot.hidden = true;   // eigener AR-Knopf
      mv.appendChild(slot);
      stage.insertBefore(mv, $('[data-loading]'));
      dimSetup();
      mv.addEventListener('load', () => {
        clearTimeout(slow);
        loading.hidden = true;
        stage.classList.add('is-loaded');
        $('[data-tools]').hidden = false;
        if (!st.touched) $('[data-hint]').hidden = false;
        mv.cameraOrbit = REDUCED ? ORBIT : ORBIT_IN;
        mv.jumpCameraToGoal();
        st.r0 = mv.getCameraOrbit().radius;
        if (!REDUCED) requestAnimationFrame(() => { mv.cameraOrbit = ORBIT; });
        st.dimKey = ''; dimLabels();
      });
      mv.addEventListener('error', () => { clearTimeout(slow); loading.hidden = true; });
      mv.addEventListener('camera-change', (e) => { if (e.detail?.source === 'user-interaction') { st.touched = true; $('[data-hint]').hidden = true; } });
      mv.addEventListener('quick-look-button-tapped', () => { location.href = contact; });
      mv.addEventListener('ar-status', (e) => { const s = e.detail.status; if (s === 'failed') msg(T.arfail); else if (s === 'session-started') msg(''); });
      if (ANDROID) {
        // Android ohne ARCore: kein AR – Hinweis statt Knopf
        setTimeout(() => { if (!mv.canActivateAR) { const go = $('[data-go]'); if (go) go.hidden = true; msg(T.noar); } }, 1500);
      }
    }).catch(() => { clearTimeout(slow); loading.hidden = true; }).finally(() => { st.building = false; });
  }
  function zoomBy(f) {
    const mv = st.mv; if (!mv) return;
    const o = mv.getCameraOrbit();
    const min = st.r0 * 0.35, max = st.r0 * 1.6;
    mv.cameraOrbit = `${o.theta}rad ${o.phi}rad ${Math.min(max, Math.max(min, o.radius * f))}m`;
    $('[data-hint]').hidden = true;
  }

  /* ---------------------------------------------------------------- Maßlinien */
  const lines = {}, labels = {};
  function dimSetup() {
    const svg = document.createElementNS(SVGNS, 'svg');
    svg.setAttribute('class', 'arv__dimlines'); svg.setAttribute('aria-hidden', 'true');
    for (const k of DIMS) {
      const g = document.createElementNS(SVGNS, 'g');
      g.innerHTML = '<line class="arv__dimline"/><line class="arv__dimtick"/><line class="arv__dimtick"/>';
      svg.appendChild(g); lines[k] = g;
      for (const end of ['a', 'b']) {
        const p = document.createElement('div');
        p.slot = `hotspot-dim-${k}${end}`; p.className = 'arv__dimpt'; p.dataset.position = '0m 0m 0m';
        st.mv.appendChild(p);
      }
      const lab = document.createElement('span');
      lab.className = 'arv__dimlabel'; lab.setAttribute('aria-hidden', 'true');
      stage.appendChild(lab); labels[k] = lab;
    }
    stage.appendChild(svg);
  }
  function dimLabels() { for (const k of DIMS) if (labels[k] && st.m) labels[k].textContent = st.m['lab_' + k]; }
  function dimPlace() {
    // Kanten zur Kamera hin: Breite vorn unten, Tiefe an der sichtbaren Seite unten, Höhe an der vorderen sichtbaren Ecke
    const [W, D, H] = st.m.mm.map((v) => v / 1000);
    const o = 0.06, orbit = st.mv.getCameraOrbit();
    const s = Math.sin(orbit.theta) >= 0 ? 1 : -1, c = Math.cos(orbit.theta) >= 0 ? 1 : -1;
    const key = `${st.m.id}${s}${c}`;
    if (key === st.dimKey) return;
    st.dimKey = key;
    const x = s * (W / 2 + o), z = c * (D / 2 + o);
    const pts = { w: [[-W / 2, 0, z], [W / 2, 0, z]], d: [[x, 0, -D / 2], [x, 0, D / 2]], h: [[x, 0, z], [x, H, z]] };
    const fmt = (p) => p.map((v) => v.toFixed(4) + 'm').join(' ');
    for (const k of DIMS) {
      st.mv.updateHotspot({ name: `hotspot-dim-${k}a`, position: fmt(pts[k][0]) });
      st.mv.updateHotspot({ name: `hotspot-dim-${k}b`, position: fmt(pts[k][1]) });
    }
  }
  function dimDraw() {
    if (!st.dimsOn || !st.mv?.loaded) return;
    dimPlace();
    const set = (el, x1, y1, x2, y2) => { el.setAttribute('x1', x1); el.setAttribute('y1', y1); el.setAttribute('x2', x2); el.setAttribute('y2', y2); };
    for (const k of DIMS) {
      const a = st.mv.queryHotspot(`hotspot-dim-${k}a`), b = st.mv.queryHotspot(`hotspot-dim-${k}b`);
      const [ln, t1, t2] = lines[k].children, lab = labels[k];
      if (!a || !b) { lines[k].style.display = lab.style.display = 'none'; continue; }
      lines[k].style.display = lab.style.display = '';
      const A = a.canvasPosition, B = b.canvasPosition;
      const dx = B.x - A.x, dy = B.y - A.y, len = Math.hypot(dx, dy) || 1, nx = -dy / len * 6, ny = dx / len * 6;
      set(ln, A.x, A.y, B.x, B.y); set(t1, A.x - nx, A.y - ny, A.x + nx, A.y + ny); set(t2, B.x - nx, B.y - ny, B.x + nx, B.y + ny);
      lab.style.transform = `translate(${(A.x + B.x) / 2}px, ${(A.y + B.y) / 2}px) translate(-50%, -50%)`;
    }
  }
  let dimRaf = 0;
  function dimLoop() {
    if (dimRaf) return;
    const tick = () => { dimRaf = st.dimsOn && st.open ? requestAnimationFrame(tick) : 0; dimDraw(); };
    dimRaf = requestAnimationFrame(tick);
  }
  function setDims(on) {
    st.dimsOn = on;
    stage.classList.toggle('show-dims', on);
    $('[data-tool="dims"]').setAttribute('aria-pressed', String(on));
    if (on) { st.dimKey = ''; dimLabels(); dimLoop(); }
  }

  /* ---------------------------------------------------------------- Bedienung */
  dlg.addEventListener('click', (e) => {
    if (e.target === dlg || e.target.closest('[data-close]')) { close(); return; }
    const chip = e.target.closest('[data-model]');
    if (chip) { if (chip.dataset.model !== st.m?.id) { stage.classList.remove('is-loaded'); apply(model(chip.dataset.model)); } return; }
    if (e.target.closest('[data-go]')) { start(st.pid, st.m?.id); return; }
    const t = e.target.closest('[data-tool]');
    if (!t) return;
    const k = t.dataset.tool;
    if (k === 'dims') setDims(!st.dimsOn);
    else if (k === 'zoom_in') zoomBy(1 / 1.25);
    else if (k === 'zoom_out') zoomBy(1.25);
    else if (k === 'reset' && st.mv) { st.mv.cameraOrbit = ORBIT; st.mv.cameraTarget = 'auto auto auto'; st.mv.fieldOfView = 'auto'; }
    else if (k === 'fullscreen') {
      if (document.fullscreenElement || document.webkitFullscreenElement) (document.exitFullscreen || document.webkitExitFullscreen).call(document);
      else (stage.requestFullscreen || stage.webkitRequestFullscreen).call(stage);
    }
  });

  return {
    has: (pid) => !!byId.get(pid)?.ar,
    open, close, start,
    get isOpen() { return st.open; },
    get pid() { return st.pid; },
    // Untertitel der AR-Karte im Panel: ein Modell -> Originalgröße mit Maßen, mehrere -> Modellnamen
    summary(p) { return p.ar.length > 1 ? p.ar.map((id) => AR.models[id].name).join(' · ') : AR.models[p.ar[0]].full; },
    label: T.ar,
  };
}
