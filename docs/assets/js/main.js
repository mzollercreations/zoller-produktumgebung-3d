/* ZOLLER Produktumgebung 3D – Oberfläche: Themenwelten, Suche, Filter,
   Produkt-Panel, Lageplan, Rundgang, Begehen, AR-/3D-Ansicht, Deep-Links */
import { createAR, ICON_AR } from './ar.js';

const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const norm = (s) => String(s ?? '').normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[­»«|]/g, '').replace(/μ/g, 'm').toLowerCase().replace(/\s+/g, ' ').trim();
const pad2 = (n) => String(n).padStart(2, '0');
const isDesktop = () => window.matchMedia('(min-width: 1101px)').matches;
const isPhone = () => window.matchMedia('(max-width: 760px)').matches;
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

const app = $('#app');
// Sprachfassungen (Kanada, Mexiko): Texte aus window.ZI18N (deutscher Text als Schlüssel), gemeinsame Bilder unter ZBASE
const tr = (s, ...a) => ((window.ZI18N && window.ZI18N[s]) || s).replace(/\{(\d)\}/g, (m, i) => a[+i]);
const BASE = window.ZBASE || '';
const LANG = document.documentElement.lang || 'de';
const ICON_EXT = '<svg viewBox="0 0 24 24"><path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/></svg>';
const ICON_CART = '<svg viewBox="0 0 24 24"><circle cx="9" cy="20" r="1.4"/><circle cx="18" cy="20" r="1.4"/><path d="M3 4h2l2.4 11h11L21 8H6.2"/></svg>';
const ICON_MAIL = '<svg viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/></svg>';
const ICON_LINK = '<svg viewBox="0 0 24 24"><path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1"/><path d="M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/></svg>';
const ICON_EYE = '<svg viewBox="0 0 24 24"><path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/></svg>';

/* ------------------------------------------------------------------ Daten */
const data = await fetch('data/products.json', { cache: 'no-cache' }).then((r) => r.json());
const { categories, products } = data;
const SITE = data.site || 'https://mzollercreations.github.io/zoller-webseite/';
const catById = new Map(categories.map((c, i) => [c.id, { ...c, index: i }]));
const byId = new Map(products.map((p) => [p.id, p]));
const ordered = categories.flatMap((c) => products.filter((p) => p.cat === c.id).sort((a, b) => c.subs.indexOf(a.sub) - c.subs.indexOf(b.sub)));
const orderIndex = new Map(ordered.map((p, i) => [p.id, i]));
products.forEach((p) => {
  p._hay = norm([p.name, p.name.replace(/μ/g, 'mu'), p.name.replace(/μ/g, 'my'), p.id, p.claim, p.teaser, p.sub, catById.get(p.cat).name, p.badge, ...(p.tools || []), ...(p.models || []).map((m) => m.name)].join(' '));
  p._name = norm(p.name);
});
const thumb = (p) => (p.kind === 'package' ? null : `${BASE}img/p/${p.id}.webp`);
const arTag = (p) => (p.ar ? ' <i class="ar-tag" aria-hidden="true">AR</i>' : '');
$('#stats').textContent = `${products.length} ${tr('Produkte')} · ${categories.length} ${tr('Themenwelten')}`;

/* ------------------------------------------------------------------ Zustand */
const state = { selected: null, activeCat: null, openCat: null, tool: '', walk: false, tour: null };
let world = null;

/* ------------------------------------------------------------------ AR-/3D-Ansicht (ar.js) */
// Produkte mit CAD-Modell (product.ar): auf Handy/Tablet direkt in AR, am Rechner Dialog mit 3D-Modell und QR-Code.
// Solange der Dialog offen ist, pausiert die Halle (GPU frei für das CAD-Modell).
const arView = data.ar ? createAR({
  data, byId, base: BASE, tr, esc, contact: data.contact || `${SITE}unternehmen/kontakt/`,
  onOpen: (pid, mid) => { world?.setRunning(false); stopTour(); setHash(`ar/${pid}/${mid}`); },
  onClose: (pid) => {
    if (bootLater) { setHash(`produkt/${pid}`); const go = bootLater; bootLater = null; go(); return; }   // Halle erst jetzt aufbauen, dann zum Produkt
    world?.setRunning(true); setHash(state.selected ? `produkt/${state.selected}` : '');
  },
}) : null;

/* ------------------------------------------------------------------ Themenwelten-Dock */
const dockList = $('#dock-list');
dockList.innerHTML = categories.map((c, i) => {
  const items = products.filter((p) => p.cat === c.id);
  const subs = c.subs.map((s) => {
    const its = items.filter((p) => p.sub === s);
    return `<li class="cat__sub">${esc(s)}</li>` + its.map((p) => `<li><button type="button" class="cat__item" data-id="${p.id}">${thumb(p) ? `<img src="${thumb(p)}" alt="" loading="lazy">` : '<img alt="" src="data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 34 26%22%3E%3Ccircle cx=%2217%22 cy=%2213%22 r=%2211%22 fill=%22%23f0e600%22/%3E%3C/svg%3E">'}<span>${esc(p.name)}${arTag(p)}</span></button></li>`).join('');
  }).join('');
  return `<li class="cat" data-cat="${c.id}">
    <button type="button" class="cat__btn" aria-expanded="false"><span class="cat__num">${pad2(i + 1)}</span><span class="cat__name">${esc(c.name)}</span><span class="cat__count">${c.count}</span></button>
    <ul class="cat__items">${subs}</ul></li>`;
}).join('');

dockList.addEventListener('click', (e) => {
  const item = e.target.closest('.cat__item');
  if (item) { selectProduct(item.dataset.id); return; }
  const btn = e.target.closest('.cat__btn');
  if (btn) {
    const id = btn.closest('.cat').dataset.cat;
    if (state.openCat === id && state.activeCat === id && !state.selected) { setOpenCat(null); return; }
    goSector(id);
  }
});
$('.dock__head').addEventListener('click', (e) => { if (isPhone() && !e.target.closest('#dock-toggle')) $('#dock-toggle').click(); });
$('#dock-toggle').addEventListener('click', () => {
  const dock = $('#dock'), c = dock.classList.toggle('is-collapsed');
  $('#dock-toggle').setAttribute('aria-expanded', String(!c));
  updateInset();
});

function collapseDock(c) {
  const dock = $('#dock');
  dock.classList.toggle('is-collapsed', c);
  $('#dock-toggle').setAttribute('aria-expanded', String(!c));
  updateInset();
}
function setOpenCat(id) {
  state.openCat = id;
  $$('.cat', dockList).forEach((li) => {
    const on = li.dataset.cat === id;
    li.classList.toggle('is-open', on);
    $('.cat__btn', li).setAttribute('aria-expanded', String(on));
  });
  if (isPhone()) updateInset();
}
function setActiveCat(id) {
  state.activeCat = id;
  $$('.cat', dockList).forEach((li) => li.classList.toggle('is-active', li.dataset.cat === id));
  if (id && state.openCat && state.openCat !== id) setOpenCat(id);
}
function markDockSelection() {
  $$('.cat__item', dockList).forEach((b) => b.classList.toggle('is-sel', b.dataset.id === state.selected));
  const sel = $(`.cat__item[data-id="${state.selected}"]`, dockList);
  if (sel) sel.scrollIntoView({ block: 'nearest', behavior: reducedMotion ? 'auto' : 'smooth' });
}

/* ------------------------------------------------------------------ Suche */
const search = $('#search'), results = $('#search-results');
let resultIds = [], resultIdx = -1;
function runSearch() {
  const q = norm(search.value);
  if (!q) { results.hidden = true; search.setAttribute('aria-expanded', 'false'); return; }
  const terms = q.split(' ');
  const scored = products.map((p) => {
    if (!terms.every((t) => p._hay.includes(t))) return null;
    let s = 0;
    if (p._name.startsWith(q)) s += 10;
    if (p._name.includes(q)) s += 5;
    if (p.id.startsWith(q)) s += 4;
    return { p, s };
  }).filter(Boolean).sort((a, b) => b.s - a.s || orderIndex.get(a.p.id) - orderIndex.get(b.p.id)).slice(0, 9);
  resultIds = scored.map((x) => x.p.id); resultIdx = scored.length ? 0 : -1;
  results.innerHTML = scored.length ? scored.map(({ p }, i) => `<li role="option" data-id="${p.id}" aria-selected="${i === 0}">
      ${thumb(p) ? `<img src="${thumb(p)}" alt="">` : '<img alt="">'}<div><div class="r-name">${esc(p.name)}${arTag(p)}</div><div class="r-meta">${esc(catById.get(p.cat).name)} · ${esc(p.sub)}</div></div></li>`).join('')
    : `<li class="r-empty">${tr('Kein Produkt gefunden')}</li>`;
  results.hidden = false; search.setAttribute('aria-expanded', 'true');
}
search.addEventListener('input', runSearch);
search.addEventListener('focus', () => { if (search.value) runSearch(); });
search.addEventListener('keydown', (e) => {
  if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
    e.preventDefault();
    if (!resultIds.length) return;
    resultIdx = (resultIdx + (e.key === 'ArrowDown' ? 1 : -1) + resultIds.length) % resultIds.length;
    $$('li', results).forEach((li, i) => li.setAttribute('aria-selected', String(i === resultIdx)));
  } else if (e.key === 'Enter') {
    if (resultIdx >= 0) { selectProduct(resultIds[resultIdx]); closeSearch(); }
  } else if (e.key === 'Escape') { closeSearch(); search.blur(); }
});
results.addEventListener('mousedown', (e) => {
  const li = e.target.closest('li[data-id]'); if (!li) return;
  e.preventDefault(); selectProduct(li.dataset.id); closeSearch(); search.blur();
});
search.addEventListener('blur', () => setTimeout(() => { results.hidden = true; }, 120));
function closeSearch() { search.value = ''; results.hidden = true; resultIds = []; search.setAttribute('aria-expanded', 'false'); }

/* ------------------------------------------------------------------ Werkzeugtyp-Filter */
const toolSel = $('#tooltype');
toolSel.insertAdjacentHTML('beforeend', data.toolTypes.slice().sort((a, b) => a.localeCompare(b, LANG)).map((t) => `<option>${esc(t)}</option>`).join(''));
toolSel.addEventListener('change', () => setTool(toolSel.value));
$('#filter-clear').addEventListener('click', () => setTool(''));
function setTool(tool) {
  state.tool = tool; toolSel.value = tool;
  toolSel.closest('.select').classList.toggle('is-active', !!tool);
  const ids = tool ? products.filter((p) => (p.tools || []).includes(tool)).map((p) => p.id) : null;
  world?.setFilter(ids);
  $$('.cat__item', dockList).forEach((b) => b.classList.toggle('is-dim', !!ids && !ids.includes(b.dataset.id)));
  const bar = $('#filterbar');
  bar.hidden = !tool;
  if (tool) {
    $('#filter-text').textContent = tr(ids.length === 1 ? '{0}: {1} passende Lösung leuchtet in der Halle' : '{0}: {1} passende Lösungen leuchten in der Halle', tool, ids.length);
    stopTour();
    if (state.selected) closePanel();
    world?.overview();
  }
}

/* ------------------------------------------------------------------ Produkt-Panel */
const panel = $('#panel'), panelBody = $('#panel-body');

function productHTML(p) {
  const c = catById.get(p.cat);
  const hero = p.kind === 'package'
    ? `<div class="p-hero is-package"><div class="p-pkg" style="background:${{ STARTER: '#fff', BRONZE: 'linear-gradient(135deg,#f1c39b,#a8673a)', SILVER: 'linear-gradient(135deg,#fafbfc,#a7aeb5)', GOLD: 'linear-gradient(135deg,#fff3a6,#cfa92c)' }[p.tier]}"><div><small>TMS</small><span>${esc(p.tier)}</span><small>${tr('Softwarepaket')}</small></div></div></div>`
    : `<div class="p-hero"><img src="${esc(BASE + (p.header || `img/hd/${p.id}.webp`))}" alt=""${esc(p.name.replace(/­/g, ''))}" decoding="async">${p.ar && arView ? `<button type="button" class="p-arbadge" data-act="ar3d" title="${esc(arView.label)}">${ICON_AR}<span>3D · AR</span></button>` : ''}</div>`;
  const arCard = p.ar && arView ? `<button type="button" class="p-ar" data-act="ar">${ICON_AR}<span><b>${esc(arView.label)}</b><small>${esc(arView.summary(p))}</small></span><svg class="p-ar__go" viewBox="0 0 24 24" aria-hidden="true"><path d="m9 18 6-6-6-6"/></svg></button>` : '';
  const intro = (p.intro || []).filter((t) => t && t !== p.claim).map((t) => `<p>${esc(t)}</p>`).join('');
  const hl = p.highlights?.length ? `<ul class="p-hl">${p.highlights.map((h) => `<li>${esc(h)}</li>`).join('')}</ul>` : '';
  const cta = `<div class="p-cta">
      <a class="btn btn--primary" href="${esc(p.url)}">${tr('Zur Produktseite')} ${ICON_EXT}</a>
      ${p.shop ? `<a class="btn" href="${esc(p.shop)}" target="_blank" rel="noopener">${tr('Im Shop')} ${ICON_CART}</a>` : ''}
      <a class="btn btn--dark" href="${esc(data.contact || `${SITE}unternehmen/kontakt/`)}">${tr('Anfragen')} ${ICON_MAIL}</a>
      <button type="button" class="btn" data-act="show" title="${tr('Kamera zum Produkt')}">${ICON_EYE} ${tr('Im Raum zeigen')}</button>
      <button type="button" class="btn" data-act="copy" title="${tr('Direktlink kopieren')}">${ICON_LINK} ${tr('Link')}</button>
    </div>`;
  const tools = p.tools?.length ? `<div class="p-tags"><h4>${tr('Geeignet für')}</h4><div>${p.tools.map((t) => `<button type="button" data-tool="${esc(t)}">${esc(t)}</button>`).join('')}</div></div>` : '';
  const also = p.also?.length ? `<div class="p-also"><h4>${tr('Auch zu finden unter')}</h4>${p.also.map((a) => `${esc(catById.get(a.cat).name)} › ${esc(a.sub)}`).join('<br>')}</div>` : '';

  const acc = [];
  if (p.features?.length) acc.push([tr('Ausstattung & Merkmale'), p.features.length, p.features.map((f) => `<div class="feat"><b>${esc(f.title)}</b>${esc(f.text)}</div>`).join(''), true]);
  if (p.models?.length) acc.push([tr('Modelle'), p.models.length, `<div class="models">${p.models.map((m) => {
    const inner = `${m.img ? `<img src="${esc(BASE + m.img)}" alt="" loading="lazy">` : ''}<div><b>${esc(m.name)}</b>${m.text ? `<span>${esc(m.text)}</span>` : ''}</div>`;
    return m.href ? `<a class="model" href="${esc(m.href)}">${inner}</a>` : `<div class="model">${inner}</div>`;
  }).join('')}</div>`, !p.features?.length]);
  if (p.specs?.length) acc.push([tr('Technische Daten'), p.specs.length > 1 ? `${p.specs.length} ${tr('Tabellen')}` : '', p.specs.map((s) => `<div class="spec">${s.title ? `<h5>${esc(s.title)}</h5>` : ''}<table>${s.rows.map((r) => `<tr>${r.map((cell) => `<td>${esc(cell)}</td>`).join('')}</tr>`).join('')}</table></div>`).join(''), false]);
  if (p.sections?.length) acc.push([tr('Mehr erfahren'), '', p.sections.map((s) => `<div class="sect"><h5>${esc(s.title)}</h5>${s.text.map((t) => `<p>${esc(t)}</p>`).join('')}</div>`).join(''), false]);
  const gal = (p.gallery || []).filter((g) => g.src && g.src !== p.header);
  if (gal.length) acc.push([tr('Bilder'), gal.length, `<div class="gallery">${gal.map((g) => `<figure><img src="${esc(BASE + g.src)}" alt="${esc(g.title || g.text || p.name)}" loading="lazy" data-cap="${esc([g.title, g.text].filter(Boolean).join(' – '))}">${g.title || g.text ? `<figcaption>${g.title ? `<b>${esc(g.title)}</b>` : ''}${esc(g.text)}</figcaption>` : ''}</figure>`).join('')}</div>`, false]);
  if (p.links?.length) acc.push([tr('Weitere Seiten zum Produkt'), p.links.length, `<ul class="links">${p.links.map((l) => `<li><a href="${esc(l.href)}">${esc(l.label)}</a></li>`).join('')}</ul>`, false]);

  return `${hero}
    <div class="p-head">
      <div class="p-crumb"><span class="num">${pad2(c.index + 1)}</span><button type="button" data-cat="${c.id}">${esc(c.name)}</button><span>›</span><span>${esc(p.sub)}</span></div>
      <h2 class="p-title" id="panel-title">${esc(p.name)}${p.badge ? `<span class="p-badge">${esc(p.badge)}</span>` : ''}</h2>
      ${p.claim ? `<p class="p-claim">${esc(p.claim)}</p>` : ''}
    </div>
    <div class="p-body">${p.teaser && p.teaser !== p.claim ? `<p>${esc(p.teaser)}</p>` : ''}${intro}${hl}</div>
    ${arCard}${cta}${tools}${also}
    <div class="p-acc">${acc.map(([t, n, body, open]) => `<details class="acc"${open ? ' open' : ''}><summary>${esc(t)}${n ? `<small>${esc(n)}</small>` : ''}</summary><div class="acc__body">${body}</div></details>`).join('')}</div>
    <p class="p-source">${tr('Alle Details auf der Produktseite:')} <a href="${esc(p.url)}">${esc(p.name.replace(/\u00ad/g, ''))}</a></p>`;
}

function openPanel(p) {
  panelBody.innerHTML = productHTML(p);
  panelBody.scrollTop = 0;
  const i = orderIndex.get(p.id);
  $('#panel-pos').textContent = `${pad2(i + 1)} / ${ordered.length}`;
  panel.classList.add('is-open'); panel.setAttribute('aria-hidden', 'false');
  app.classList.add('panel-open');
  updateInset();
}
function closePanel({ keepSelection = false } = {}) {
  panel.classList.remove('is-open'); panel.setAttribute('aria-hidden', 'true');
  app.classList.remove('panel-open');
  if (!keepSelection) { state.selected = null; world?.clearSelection(); markDockSelection(); setHash(''); }
  updateInset();
}
function updateInset() {
  if (!world) return;
  const open = panel.classList.contains('is-open');
  const dock = $('#dock');
  const dockW = !isPhone() && !dock.classList.contains('is-collapsed') ? dock.offsetWidth + 16 : 0;
  if (isPhone()) world.setInset(0, open ? panel.offsetHeight : dock.offsetHeight + 12);
  else world.setInset((open ? panel.offsetWidth : 0) - dockW, 0);
}
window.addEventListener('resize', () => updateInset());

panelBody.addEventListener('click', (e) => {
  const cat = e.target.closest('[data-cat]');
  if (cat) { goSector(cat.dataset.cat); return; }
  const tool = e.target.closest('[data-tool]');
  if (tool) { setTool(tool.dataset.tool); return; }
  const act = e.target.closest('[data-act]');
  if (act?.dataset.act === 'ar' && state.selected) { arView?.start(state.selected); return; }
  if (act?.dataset.act === 'ar3d' && state.selected) { arView?.open(state.selected); return; }
  if (act?.dataset.act === 'show' && state.selected) { world?.focus(state.selected); if (isPhone()) closePanel({ keepSelection: true }); return; }
  if (act?.dataset.act === 'copy') {
    const url = `${location.origin}${location.pathname}#produkt/${state.selected}`;
    navigator.clipboard?.writeText(url).then(() => { act.lastChild.textContent = ` ${tr('Kopiert')}`; setTimeout(() => { act.lastChild.textContent = ` ${tr('Link')}`; }, 1600); }).catch(() => {});
    return;
  }
  const img = e.target.closest('.gallery img');
  if (img) openLightbox(img.src, img.dataset.cap);
});
$('#panel-close').addEventListener('click', () => closePanel());
$('#panel-prev').addEventListener('click', () => step(-1));
$('#panel-next').addEventListener('click', () => step(1));

function openLightbox(src, cap) {
  const lb = document.createElement('div');
  lb.className = 'lightbox'; lb.setAttribute('role', 'dialog');
  lb.innerHTML = `<div><img src="${esc(src)}" alt=""><p>${esc(cap || '')}</p></div>`;
  lb.addEventListener('click', () => lb.remove());
  document.body.appendChild(lb);
}

/* ------------------------------------------------------------------ Aktionen */
function selectProduct(id, { fly = true, fromTour = false } = {}) {
  const p = byId.get(id); if (!p) return;
  if (!fromTour) stopTour();
  state.selected = id;
  setActiveCat(p.cat); setOpenCat(p.cat); markDockSelection();
  world?.focus(id, { fly });
  if (!fromTour || isDesktop()) openPanel(p);
  setHash(`produkt/${id}`);
  hideHint();
}
function goSector(id, { fromTour = false } = {}) {
  if (!fromTour) stopTour();
  if (state.selected) closePanel();
  setActiveCat(id); setOpenCat(id);
  world?.sector(id);
  setHash(`themenwelt/${id}`);
  hideHint();
}
function goOverview() {
  stopTour();
  if (state.selected) closePanel();
  setOpenCat(null);
  world?.overview();
  setHash('');
}
function step(dir) {
  const cur = state.selected ? orderIndex.get(state.selected) : (dir > 0 ? -1 : 0);
  const next = ordered[(cur + dir + ordered.length) % ordered.length];
  selectProduct(next.id);
}
function setHash(h) {
  const url = h ? `#${h}` : location.pathname + location.search;
  history.replaceState(null, '', url);
}

/* ------------------------------------------------------------------ Rundgang */
const tourbar = $('#tourbar');
function tourSteps() {
  const steps = [];
  categories.forEach((c) => {
    steps.push({ type: 'sector', id: c.id, dwell: 3.2 });
    ordered.filter((p) => p.cat === c.id).forEach((p) => steps.push({ type: 'product', id: p.id, dwell: 7 }));
  });
  return steps;
}
function startTour(fromId) {
  if (!world) return;
  if (world.mode === 'walk') { world.setWalk(false); }
  const steps = tourSteps();
  let i = 0;
  if (fromId) { const k = steps.findIndex((s) => s.id === fromId); if (k >= 0) i = k; }
  state.tour = { steps, i, t: 0, playing: true };
  if (isPhone()) collapseDock(true);
  tourbar.hidden = false; $('#btn-tour').classList.add('is-on');
  hideHint();
  tourGo();
}
function tourGo() {
  const T = state.tour; if (!T) return;
  const s = T.steps[T.i]; T.t = 0;
  if (s.type === 'sector') {
    if (state.selected) closePanel();
    goSector(s.id, { fromTour: true });
    const c = catById.get(s.id);
    $('#tour-now').innerHTML = `${pad2(c.index + 1)} ${esc(c.name)}<small>${c.count} ${tr('Produkte')}</small>`;
  } else {
    const p = byId.get(s.id);
    selectProduct(s.id, { fromTour: true });
    $('#tour-now').innerHTML = `${esc(p.name)}<small>${esc(p.claim || p.sub)}</small>`;
  }
  updateTourBar();
}
function updateTourBar() {
  const T = state.tour; if (!T) return;
  const s = T.steps[T.i];
  const frac = (T.i + Math.min(1, T.t / (s.dwell + 2))) / T.steps.length;
  $('#tour-progress').style.width = `${(frac * 100).toFixed(2)}%`;
  $('#tour-play').innerHTML = T.playing ? '<svg viewBox="0 0 24 24"><path d="M8 5h3v14H8zM13 5h3v14h-3z"/></svg>' : '<svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>';
  $('#tour-play').setAttribute('aria-label', T.playing ? tr('Pause') : tr('Weiter abspielen'));
}
function tourTick(dt) {
  const T = state.tour; if (!T || !T.playing) return;
  T.t += dt;
  const s = T.steps[T.i];
  if (T.t > s.dwell + 2.0) { T.i = (T.i + 1) % T.steps.length; tourGo(); }
  else updateTourBar();
}
function stopTour() {
  if (!state.tour) return;
  state.tour = null; tourbar.hidden = true; $('#btn-tour').classList.remove('is-on');
}
$('#tour-play').addEventListener('click', () => { if (state.tour) { state.tour.playing = !state.tour.playing; updateTourBar(); } });
$('#tour-next').addEventListener('click', () => { const T = state.tour; if (T) { T.i = (T.i + 1) % T.steps.length; T.playing = true; tourGo(); } });
$('#tour-prev').addEventListener('click', () => { const T = state.tour; if (T) { T.i = (T.i - 1 + T.steps.length) % T.steps.length; T.playing = true; tourGo(); } });
$('#tour-stop').addEventListener('click', stopTour);

/* ------------------------------------------------------------------ Knöpfe & Tastatur */
$('#btn-overview').addEventListener('click', goOverview);
$('#btn-tour').addEventListener('click', () => (state.tour ? stopTour() : startTour(state.selected)));
$('#btn-walk').addEventListener('click', () => toggleWalk());
$('#walk-exit').addEventListener('click', () => toggleWalk(false));
$('#btn-help').addEventListener('click', () => toggleHelp(true));
$('#help-close').addEventListener('click', () => toggleHelp(false));
$('#help').addEventListener('click', (e) => { if (e.target.id === 'help') toggleHelp(false); });
// Land und Sprache: dieselbe Ansicht (#produkt/…, #themenwelt/…) in der anderen Sprachfassung öffnen
$('#btn-lang').addEventListener('click', () => toggleLangs(true));
$('#langs-close').addEventListener('click', () => toggleLangs(false));
$('#langs').addEventListener('click', (e) => { if (e.target.id === 'langs') toggleLangs(false); });
$$('#langs .lang-site').forEach((a) => a.addEventListener('click', () => { a.hash = location.hash; }));

function toggleWalk(on = !state.walk) {
  if (!world) return;
  stopTour();
  if (on && isPhone() && panel.classList.contains('is-open')) closePanel({ keepSelection: true });
  world.setWalk(on);
}
function toggleHelp(on) { $('#help').hidden = !on; if (on) $('#help-close').focus(); }
function toggleLangs(on) { $('#langs').hidden = !on; if (on) ($('#langs .is-current') || $('#langs-close')).focus(); }

window.addEventListener('keydown', (e) => {
  if (e.target instanceof Element && e.target.closest('input, select, textarea')) return;
  if (e.metaKey || e.ctrlKey || e.altKey) return;
  const k = e.key;
  if (arView?.isOpen) { if (k === 'Escape') arView.close(); return; }
  if (k === 'Escape') {
    const lb = $('.lightbox'); if (lb) { lb.remove(); return; }
    if (!$('#help').hidden) { toggleHelp(false); return; }
    if (!$('#langs').hidden) { toggleLangs(false); return; }
    if (state.tour) { stopTour(); return; }
    if (panel.classList.contains('is-open')) { const p = byId.get(state.selected); closePanel(); if (p && world?.mode !== 'walk') world.sector(p.cat); return; }
    if (state.walk) { toggleWalk(false); return; }
    goOverview(); return;
  }
  if (k === '/') { e.preventDefault(); search.focus(); return; }
  if (k === '?') { toggleHelp($('#help').hidden); return; }
  if (k === 'g' || k === 'G') { toggleWalk(!state.walk); return; }
  if (k === '+' || k === '=') { world?.zoom(0.75); return; }
  if (k === '-' || k === '_') { world?.zoom(1.35); return; }
  if (state.walk) return; // Pfeiltasten/WASD gehören dem Begehen-Modus
  if (k === 'ArrowRight') { e.preventDefault(); step(1); }
  else if (k === 'ArrowLeft') { e.preventDefault(); step(-1); }
  else if (k === 'h' || k === 'H') goOverview();
  else if (k === 't' || k === 'T') (state.tour ? stopTour() : startTour(state.selected));
  else if (/^[1-9]$/.test(k) && categories[+k - 1]) goSector(categories[+k - 1].id);
});

/* ------------------------------------------------------------------ Hinweis */
/* ------------------------------------------------------------------ Steuerungslegende, Zoom, Hinweise */
const legend = $('#legend');
const LEGEND_KEY = 'zoller3d.legend';
let legendTouched = false, hintTimer = 0;
function setLegend(open, remember = false) {
  legend.classList.toggle('is-collapsed', !open);
  $('#legend-toggle').setAttribute('aria-expanded', String(open));
  if (remember) { legendTouched = true; try { localStorage.setItem(LEGEND_KEY, open ? '1' : '0'); } catch { /* privat */ } }
}
$('#legend-toggle').addEventListener('click', () => setLegend(legend.classList.contains('is-collapsed'), true));
try { if (localStorage.getItem(LEGEND_KEY) === '0') { setLegend(false); legendTouched = true; } } catch { /* privat */ }
// Auf dem Handy klappt die Legende nach der ersten Bewegung ein (bleibt per Tipp erreichbar)
function hideHint() { if (isPhone() && !legendTouched) { legendTouched = true; clearTimeout(hintTimer); setLegend(false); } }

$('#zoom-in').addEventListener('click', () => { stopTour(); world?.zoom(0.68); });
$('#zoom-out').addEventListener('click', () => { stopTour(); world?.zoom(1.47); });

const toast = $('#toast');
let toastTimer = 0;
function showToast(text) {
  toast.textContent = text; toast.classList.add('is-on');
  clearTimeout(toastTimer); toastTimer = setTimeout(() => toast.classList.remove('is-on'), 2400);
}
const LIMIT_TEXT = {
  zoom: tr('Weiter heraus geht es nicht – Sie sehen die ganze Halle.'),
  pan: tr('Rand der Ausstellung erreicht.'),
  walk: tr('Hier endet der Ausstellungsbereich.'),
};

/* ------------------------------------------------------------------ Tooltip */
const tooltip = $('#tooltip');
function showTooltip(id, pt, sec) {
  if ((!id && !sec) || !pt || state.walk && !id) { tooltip.classList.remove('is-on'); return; }
  if (id) {
    const p = byId.get(id);
    tooltip.innerHTML = `<b>${esc(p.name)}${arTag(p)}</b><span>${esc(p.claim || p.teaser || p.sub)}</span><em>${id === state.selected ? tr('Ausgewählt') : tr('Klicken für Details')}</em>`;
  } else {
    const c = catById.get(sec);
    tooltip.innerHTML = `<b>${pad2(c.index + 1)} ${esc(c.name)}</b><span>${esc(c.text)}</span><em>${tr('Themenwelt ansteuern')}</em>`;
  }
  tooltip.style.left = `${pt.x}px`; tooltip.style.top = `${pt.y}px`;
  tooltip.classList.add('is-on');
}

/* ------------------------------------------------------------------ Lageplan */
const mm = $('#minimap'), mctx = mm.getContext('2d');
let mmScale = 1, mmC = 110, mmDirty = 0;
function sizeMinimap() {
  const r = mm.getBoundingClientRect(), d = Math.min(2, window.devicePixelRatio || 1);
  mm.width = Math.round(r.width * d); mm.height = Math.round(r.height * d);
  mmC = mm.width / 2;
}
function drawMinimap() {
  if (!world) return;
  const L = world.layout, W = mm.width, c = mmC;
  const R = L.wallR + 2.4; mmScale = (c - 6 * (W / 220)) / R;
  const s = mmScale, u = W / 220;
  const X = (x) => c + x * s, Y = (z) => c + z * s;
  mctx.clearRect(0, 0, W, W);
  const st = world.state();
  // Zonengrenze
  const zr = world.zone().wallR + 1.3;
  mctx.strokeStyle = '#f0e600'; mctx.lineWidth = 2.4 * u; mctx.setLineDash([5 * u, 4 * u]);
  mctx.beginPath(); mctx.arc(c, c, zr * s, 0, Math.PI * 2); mctx.stroke(); mctx.setLineDash([]);
  // Platz
  mctx.fillStyle = '#ffffff'; mctx.beginPath(); mctx.arc(c, c, L.plazaR * s, 0, Math.PI * 2); mctx.fill();
  mctx.strokeStyle = '#f0e600'; mctx.lineWidth = 2.2 * u; mctx.stroke();
  mctx.fillStyle = '#17181b'; mctx.beginPath(); mctx.arc(c, c, 3.1 * s, 0, Math.PI * 2); mctx.fill();
  // Themenwelten
  for (const sec of L.sectors) {
    const a0 = sec.th0 - Math.PI / 2 - 0.03, a1 = sec.th1 - Math.PI / 2 + 0.03;
    const active = sec.id === st.activeSector || sec.id === state.activeCat && !st.activeSector && state.selected;
    mctx.fillStyle = active ? '#17181b' : 'rgba(23,24,27,0.16)';
    mctx.beginPath(); mctx.arc(c, c, L.wallR * s, a0, a1); mctx.arc(c, c, L.tierIn[0] * s, a1, a0, true); mctx.closePath(); mctx.fill();
    const mid = sec.mid - Math.PI / 2, rr = (L.tierIn[0] - 2.8) * s;
    mctx.fillStyle = active ? '#17181b' : '#6b6e73';
    mctx.font = `800 ${11 * u}px "T-Star", sans-serif`; mctx.textAlign = 'center'; mctx.textBaseline = 'middle';
    mctx.fillText(pad2(sec.index + 1), c + Math.cos(mid) * rr, c + Math.sin(mid) * rr);
  }
  // Produkte
  for (const p of world.products) {
    const sel = p.id === state.selected, hov = p.id === st.hovered;
    const dim = state.tool && !(p.tools || []).includes(state.tool);
    const inActive = st.activeSector === p.cat;
    mctx.fillStyle = sel || hov ? '#f0e600' : (dim ? 'rgba(160,160,160,0.5)' : (inActive ? '#ffffff' : (state.tool ? '#f0e600' : '#2b2d31')));
    mctx.beginPath(); mctx.arc(X(p.pos.x), Y(p.pos.z), (sel ? 4.2 : hov ? 3.6 : 2.2) * u, 0, Math.PI * 2); mctx.fill();
    if (sel) { mctx.strokeStyle = '#17181b'; mctx.lineWidth = 1.6 * u; mctx.stroke(); }
  }
  // Kamera
  const cx = X(clampR(st.x, st.z, R).x), cy = Y(clampR(st.x, st.z, R).z);
  const len = 26 * u, spread = 0.5;
  const g = mctx.createRadialGradient(cx, cy, 0, cx, cy, len);
  g.addColorStop(0, 'rgba(240,230,0,0.75)'); g.addColorStop(1, 'rgba(240,230,0,0)');
  mctx.fillStyle = g; mctx.beginPath(); mctx.moveTo(cx, cy);
  const ang = st.yaw - Math.PI / 2;
  mctx.arc(cx, cy, len, ang - spread, ang + spread); mctx.closePath(); mctx.fill();
  mctx.fillStyle = '#17181b'; mctx.beginPath(); mctx.arc(cx, cy, 4 * u, 0, Math.PI * 2); mctx.fill();
  mctx.strokeStyle = '#f0e600'; mctx.lineWidth = 2 * u; mctx.stroke();
}
function clampR(x, z, R) { const r = Math.hypot(x, z); return r > R ? { x: x * R / r, z: z * R / r } : { x, z }; }
mm.addEventListener('click', (e) => {
  if (!world) return;
  const r = mm.getBoundingClientRect(), k = mm.width / r.width;
  const x = ((e.clientX - r.left) * k - mmC) / mmScale, z = ((e.clientY - r.top) * k - mmC) / mmScale;
  let best = null, bd = 2.6;
  for (const p of world.products) { const d = Math.hypot(p.pos.x - x, p.pos.z - z); if (d < bd) { bd = d; best = p; } }
  if (best) { selectProduct(best.id); return; }
  const L = world.layout, rr = Math.hypot(x, z);
  if (rr > L.tierIn[0] - 4 && rr < L.wallR + 2) {
    let th = Math.atan2(x, -z); if (th < 0) th += Math.PI * 2;
    const sec = L.sectors.find((s) => { const a = ((th - s.th0) % (Math.PI * 2) + Math.PI * 2) % (Math.PI * 2); return a <= s.th1 - s.th0 + 0.05; });
    if (sec && !state.walk) { goSector(sec.id); return; }
  }
  stopTour();
  world.flyToPoint(x, z);
});

/* ------------------------------------------------------------------ Fallback ohne WebGL */
function showFallback(reason) {
  app.classList.remove('is-loading');
  $('#minimap-wrap').hidden = true;
  $('#btn-tour').hidden = true; $('#btn-walk').hidden = true;
  const fb = $('#fallback');
  fb.hidden = false;
  fb.innerHTML = `<p class="fallback__note">${esc(reason)} ${tr('Hier sind alle Produkte als Übersicht – ein Klick öffnet die Details.')}</p>` + categories.map((c, i) => `<h2><span>${pad2(i + 1)}</span>${esc(c.name)}</h2><div class="fallback__grid">${ordered.filter((p) => p.cat === c.id).map((p) => `<button type="button" data-id="${p.id}">${thumb(p) ? `<img src="${thumb(p)}" alt="" loading="lazy">` : ''}<b>${esc(p.name)}${arTag(p)}</b><span>${esc(p.claim || p.sub)}</span></button>`).join('')}</div>`).join('');
  fb.addEventListener('click', (e) => { const b = e.target.closest('[data-id]'); if (b) selectProduct(b.dataset.id); });
}

/* ------------------------------------------------------------------ Start */
function hasWebGL() {
  try { const c = document.createElement('canvas'); return !!(c.getContext('webgl2') || c.getContext('webgl')); } catch { return false; }
}

const loaderBar = $('#loader-bar'), loaderText = $('#loader-text');
async function boot() {
  if (!hasWebGL()) { showFallback(tr('Ihr Browser unterstützt kein WebGL, daher kann der 3D-Showroom nicht angezeigt werden.')); return; }
  try {
    await Promise.race([
      Promise.all(['400', '500', '700', '800'].map((w) => document.fonts.load(`${w} 40px "T-Star"`))),
      new Promise((r) => setTimeout(r, 2500)),
    ]);
  } catch { /* Schrift-Fallback */ }
  const { createWorld } = await import('./world.js');
  world = await createWorld($('#scene'), data, {
    mobile: isPhone(), base: BASE,
    onProgress: (f) => { loaderBar.style.width = `${Math.round(f * 100)}%`; loaderText.textContent = `${tr('Exponate werden aufgestellt …')} ${Math.round(f * 100)} %`; },
  });

  world.on('select', (id) => { if (id === state.selected && panel.classList.contains('is-open')) { world.focus(id); return; } selectProduct(id); });
  world.on('sector', (id) => goSector(id));
  world.on('hover', (id, pt, sec) => showTooltip(id, pt, sec));
  world.on('active', (id) => { if (!state.selected) setActiveCat(id); });
  world.on('background', () => { if (panel.classList.contains('is-open') && !state.walk) closePanel(); });
  world.on('interact', () => { if (state.tour?.playing) { state.tour.playing = false; updateTourBar(); } hideHint(); });
  world.on('mode', (m) => {
    state.walk = m === 'walk';
    $('#btn-walk').classList.toggle('is-on', state.walk);
    $('#btn-walk').setAttribute('aria-pressed', String(state.walk));
    $('#walkhint').hidden = !state.walk;
    app.classList.toggle('is-walk', state.walk);
    if (state.walk && isPhone() && !legendTouched) setLegend(true);
    tooltip.classList.remove('is-on');
  });
  let last = performance.now();
  world.on('frame', () => {
    const now = performance.now(), dt = Math.min(0.1, (now - last) / 1000); last = now;
    tourTick(dt);
    if (++mmDirty % 2 === 0) drawMinimap();
  });

  window.zoller3d = { world, selectProduct, goSector, goOverview };
  if (isPhone()) collapseDock(true);
  sizeMinimap();
  window.addEventListener('resize', sizeMinimap);
  app.classList.remove('is-loading');
  world.start();
  if (arView?.isOpen) world.setRunning(false);
  updateInset();

  world.on('limit', (kind) => showToast(LIMIT_TEXT[kind] || LIMIT_TEXT.pan));
  if (isPhone()) hintTimer = setTimeout(hideHint, 14000);

  // Deep-Link
  const route = (delay) => {
    const h = decodeURIComponent(location.hash.slice(1));
    const ar = arRoute(h);
    if (ar) { setTimeout(() => { selectProduct(ar[0]); arView.open(ar[0], ar[1]); }, arView.isOpen ? 0 : delay); return; }
    if (h.startsWith('produkt/') && byId.has(h.slice(8))) setTimeout(() => selectProduct(h.slice(8)), delay);
    else if (h.startsWith('themenwelt/') && catById.has(h.slice(11))) setTimeout(() => goSector(h.slice(11)), delay);
  };
  route(2600);
  window.addEventListener('hashchange', () => route(0));
}

// #ar/<produkt>/<modell> (QR-Code der AR-Ansicht): Dialog sofort öffnen; die Halle baut sich erst auf, wenn er
// geschlossen wird – so gehören Netz und GPU des Handys ganz dem CAD-Modell
function arRoute(h) {
  const m = /^ar\/([\w-]+)(?:\/([\w-]+))?$/.exec(h);
  return m && arView?.has(m[1]) ? [m[1], m[2]] : null;
}
function start() {
  boot().catch((err) => {
    console.error(err);
    showFallback(tr('Der 3D-Showroom konnte nicht gestartet werden.'));
  });
}
let bootLater = null;
const arFirst = arRoute(decodeURIComponent(location.hash.slice(1)));
if (arFirst && arView.open(arFirst[0], arFirst[1])) bootLater = start;
else start();
