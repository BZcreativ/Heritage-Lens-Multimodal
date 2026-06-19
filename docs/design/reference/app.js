/* ============ Heritage Lens — Sidebar Classic (hi-fi mockup) ============ */
(function () {
  'use strict';
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];

  /* ---------- sample data ---------- */
  const SOURCES = [
    { n: 1, type: 'pdf', title: 'Chalcatzingo: Excavations on the Olmec Frontier', sub: 'Grove, D. C. · pp. 114–121',
      meta: { Author: 'David C. Grove', Work: 'Chalcatzingo: Excavations on the Olmec Frontier', Type: 'Monograph (PDF)', Location: 'pp. 114–121', Publisher: 'University of Texas Press, 1987', Institution: 'UT Mesoamerica Collection' } },
    { n: 2, type: 'pdf', title: 'The Chalcatzingo Reliefs: An Iconographic Analysis', sub: 'Angulo V., J. · Plate 4',
      meta: { Author: 'Jorge Angulo V.', Work: 'Ancient Chalcatzingo (ed. Grove)', Type: 'Chapter (PDF)', Location: 'Plate 4, pp. 132–158', Publisher: 'University of Texas Press', Institution: 'INAH' } },
    { n: 3, type: 'img', title: 'Monument 1 “El Rey” — relief photograph', sub: 'INAH photographic archive',
      meta: { Subject: 'Monument 1 (“El Rey”)', Type: 'Photograph (image)', Site: 'Chalcatzingo, Morelos', Credit: 'Archivo Fotográfico, INAH', Modality: 'visual_caption + ocr_text' } },
    { n: 4, type: 'vid', title: 'Olmec Hydraulic & Cave Iconography (lecture)', sub: 'Seminar recording · 02:14',
      meta: { Speaker: 'Dr. M. Tate', Work: 'Formative Mesoamerica Lecture Series', Type: 'Video (audio_transcript)', Timestamp: '02:14–04:09', Institution: 'Dumbarton Oaks' } },
    { n: 5, type: 'pdf', title: 'Rulership and the Sacred Mountain in Formative Mesoamerica', sub: 'Reilly, F. K. · pp. 27–45',
      meta: { Author: 'F. Kent Reilly III', Type: 'Journal article (PDF)', Location: 'pp. 27–45', Publisher: 'RES: Anthropology and Aesthetics', Institution: 'Peabody Museum' } },
  ];

  const VIDEOS = [
    { modality: 'audio', label: 'audio_transcript', ts: '02:14', cap: 'Lecturer describes the cave-mouth motif as a portal between political and supernatural realms.' },
    { modality: 'visual', label: 'visual_caption', ts: '05:48', cap: 'Frame shows the seated “El Rey” figure with emanating scroll and raindrop glyphs.' },
    { modality: 'ocr', label: 'ocr_text', ts: '11:02', cap: 'On-screen caption: “Monument 1, Chalcatzingo — Middle Formative, c. 700–500 BCE.”' },
  ];

  const IMAGES = [
    { label: 'Monument 1 “El Rey” relief', cap: 'Monument 1 (“El Rey”), Chalcatzingo — seated figure within a cave-mouth emitting rain and scroll motifs. INAH archive.' },
    { label: 'Monument 2 — procession', cap: 'Monument 2 hillside relief showing a procession of figures with elaborate headdresses.' },
    { label: 'Cave-mouth detail', cap: 'Detail of the stylised cave-mouth / earth-monster maw framing the seated ruler.' },
    { label: 'Rain & scroll glyphs', cap: 'Close reading of rain-drop and volute (scroll) motifs emanating from the cave.' },
    { label: 'Site context photo', cap: 'Cerro Chalcatzingo with the carved boulders in situ on the talus slope.' },
  ];

  /* ---------- elements ---------- */
  const els = {
    q: $('#q'), go: $('#go'), empty: $('#emptyState'), loading: $('#loadingState'),
    results: $('#resultsState'), recapQ: $('#recapQ'), loadTxt: $('#loadTxt'),
    sourceList: $('#sourceList'), vidGrid: $('#vidGrid'), imgGrid: $('#imgGrid'),
    history: $('#history'), toast: $('#toast'),
  };

  /* ---------- render galleries / sources ---------- */
  function renderSources() {
    els.sourceList.innerHTML = SOURCES.map(s => `
      <div class="src" data-n="${s.n}">
        <button class="src-head" aria-expanded="false">
          <span class="src-num">${s.n}</span>
          <span class="src-main"><span class="src-title">${s.title}</span><span class="src-sub">${s.sub}</span></span>
          <span class="src-type ${s.type}">${s.type}</span>
          <svg class="src-chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg>
        </button>
        <div class="src-detail"><dl class="src-detail-inner">${
          Object.entries(s.meta).map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join('')
        }</dl></div>
      </div>`).join('');
    $$('.src-head', els.sourceList).forEach(btn => {
      btn.addEventListener('click', () => {
        const src = btn.closest('.src');
        const open = src.classList.toggle('open');
        btn.setAttribute('aria-expanded', String(open));
      });
    });
  }

  function renderVideos() {
    els.vidGrid.innerHTML = VIDEOS.map(v => `
      <div class="vid-card">
        <div class="ph">video frame<div class="play"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg></div></div>
        <div class="vid-meta">
          <span class="modality ${v.modality}">${v.label}</span>
          <p class="cap">${v.cap}</p>
          <div class="seek"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>Seek to ${v.ts}</div>
        </div>
      </div>`).join('');
  }

  function renderImages() {
    els.imgGrid.innerHTML = IMAGES.map((im, i) => `
      <div class="img-thumb" data-i="${i}"><div class="ph">${im.label}</div></div>`).join('');
    $$('.img-thumb', els.imgGrid).forEach(t => {
      t.addEventListener('click', () => openLightbox(IMAGES[+t.dataset.i]));
    });
  }

  /* ---------- search states ---------- */
  const STEPS = ['Retrieving across the corpus…', 'Interpreting retrieved passages…', 'Attributing sources…', 'Evaluating what cannot be known…'];
  let searching = false;

  function setState(state) {
    els.empty.style.display = state === 'empty' ? '' : 'none';
    els.loading.style.display = state === 'loading' ? '' : 'none';
    els.results.classList.toggle('show', state === 'results');
  }

  function runSearch(query) {
    if (!query || searching) return;
    searching = true;
    els.q.value = query;
    addHistory(query);
    setState('loading');
    const stepEls = $$('.loading .st');
    let i = 0;
    stepEls.forEach(s => s.classList.remove('done', 'active'));
    els.loadTxt.textContent = STEPS[0];
    const tick = setInterval(() => {
      if (i > 0) stepEls[i - 1].classList.add('done');
      if (i < stepEls.length) {
        stepEls[i].classList.add('active');
        els.loadTxt.textContent = STEPS[i];
        i++;
      } else {
        clearInterval(tick);
        finish(query);
      }
    }, 480);
  }

  function finish(query) {
    els.recapQ.textContent = query;
    setState('results');
    const epi = $('#epiPanel'); if (epi) epi.style.display = '';
    searching = false;
    try { location.hash = 'q=' + encodeURIComponent(query); } catch (e) {}
  }

  /* ---------- history ---------- */
  function getHistory() { try { return JSON.parse(localStorage.getItem('hl_hist') || '[]'); } catch (e) { return []; } }
  function addHistory(q) {
    let h = getHistory().filter(x => x !== q);
    h.unshift(q); h = h.slice(0, 8);
    localStorage.setItem('hl_hist', JSON.stringify(h));
    renderHistory();
  }
  function renderHistory() {
    const h = getHistory();
    els.history.innerHTML = h.length ? h.map(q =>
      `<button class="ghost-btn" style="width:100%;justify-content:flex-start;text-align:left" data-q="${q.replace(/"/g, '&quot;')}">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex:none"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>
        <span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${q}</span></button>`).join('')
      : `<div style="font-size:12px;color:var(--text-faint)">No queries yet.</div>`;
    $$('button[data-q]', els.history).forEach(b => b.addEventListener('click', () => runSearch(b.dataset.q)));
  }

  /* ---------- lightbox ---------- */
  function openLightbox(im) {
    $('#lbImg').textContent = im.label;
    $('#lbCap').innerHTML = `<b>${im.label}</b>${im.cap}`;
    $('#lightbox').classList.add('show');
  }
  $('#lbClose').addEventListener('click', () => $('#lightbox').classList.remove('show'));
  $('#lightbox').addEventListener('click', e => { if (e.target.id === 'lightbox') $('#lightbox').classList.remove('show'); });

  /* ---------- collapse columns (full-screen view) ---------- */
  function setCol(side, collapsed) {
    const cls = side === 'nav' ? 'nav-collapsed' : 'rail-collapsed';
    document.body.classList.toggle(cls, collapsed);
    const btn = side === 'nav' ? $('#btnNav') : $('#btnRail');
    btn.classList.toggle('on', collapsed);
    btn.setAttribute('aria-pressed', String(collapsed));
    btn.title = collapsed
      ? (side === 'nav' ? 'Show sidebar' : 'Show session panel')
      : (side === 'nav' ? 'Hide sidebar' : 'Hide session panel');
    localStorage.setItem('hl_col_' + side, collapsed ? '1' : '0');
  }
  $('#btnNav').addEventListener('click', () => setCol('nav', !document.body.classList.contains('nav-collapsed')));
  $('#btnRail').addEventListener('click', () => setCol('rail', !document.body.classList.contains('rail-collapsed')));

  /* ---------- mask session overview (prioritise epistemic) ---------- */
  function setSessionMasked(masked) {
    const body = $('#sessionBody'), btn = $('#btnMaskSession');
    if (!body || !btn) return;
    if (masked && !body.style.maxHeight) body.style.maxHeight = body.scrollHeight + 'px';
    requestAnimationFrame(() => {
      body.style.maxHeight = masked ? '0px' : (body.scrollHeight + 'px');
      body.classList.toggle('masked', masked);
    });
    if (!masked) setTimeout(() => { if (!body.classList.contains('masked')) body.style.maxHeight = 'none'; }, 300);
    btn.setAttribute('aria-expanded', String(!masked));
    btn.title = masked ? 'Show' : 'Hide';
    localStorage.setItem('hl_session_masked', masked ? '1' : '0');
  }
  $('#btnMaskSession') && $('#btnMaskSession').addEventListener('click', () => {
    setSessionMasked(!$('#sessionBody').classList.contains('masked'));
  });

  /* ---------- dark mode ---------- */
  function setDark(on) {
    document.body.classList.toggle('dark', on);
    $('#swDark').setAttribute('aria-checked', String(on));
    const ico = $('#darkIco');
    ico.innerHTML = on
      ? '<path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9z"/>'
      : '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/>';
    localStorage.setItem('hl_dark', on ? '1' : '0');
  }
  $('#btnDark').addEventListener('click', () => setDark(!document.body.classList.contains('dark')));
  $('#swDark').addEventListener('click', () => setDark(!document.body.classList.contains('dark')));

  /* ---------- layers switch (decorative) ---------- */
  $('#swLayers').addEventListener('click', function () {
    this.setAttribute('aria-checked', this.getAttribute('aria-checked') === 'true' ? 'false' : 'true');
  });

  /* ---------- reading comfort ---------- */
  const rc = $('#rcPanel'), scrim = $('#scrim'), doc = $('#answerDoc');
  function openRC() { rc.classList.add('show'); scrim.classList.add('show'); }
  function closeRC() { rc.classList.remove('show'); scrim.classList.remove('show'); }
  $('#btnRC').addEventListener('click', openRC);
  $('#rcClose').addEventListener('click', closeRC);
  scrim.addEventListener('click', closeRC);

  const RCdefault = { font: 'Inter', ls: '0', lh: '1.6', w: '68', cream: false, rag: false };
  let RC = Object.assign({}, RCdefault);
  try { RC = Object.assign(RC, JSON.parse(localStorage.getItem('hl_rc') || '{}')); } catch (e) {}

  function applyRC() {
    doc.style.setProperty('--rc-font', "'" + RC.font + "'");
    doc.style.setProperty('--rc-ls', RC.ls + 'em');
    doc.style.setProperty('--rc-lh', RC.lh);
    doc.style.setProperty('--rc-width', RC.w + 'ch');
    doc.style.setProperty('--rc-bg', RC.cream ? '#FDF6E3' : 'transparent');
    doc.style.setProperty('--rc-align', RC.rag ? 'left' : 'justify');
    doc.style.setProperty('--rc-pad', RC.cream ? '20px 22px' : '0');
    doc.classList.toggle('cream', RC.cream);
    $$('.rc-fopt').forEach(o => o.setAttribute('aria-checked', String(o.dataset.font === RC.font)));
    $('#sLs').value = RC.ls; $('#sLh').value = RC.lh; $('#sW').value = RC.w;
    $('#vLs').textContent = Number(RC.ls).toFixed(2) + 'em';
    $('#vLh').textContent = Number(RC.lh).toFixed(2);
    $('#vW').textContent = RC.w + 'ch';
    $('#tCream').setAttribute('aria-checked', String(RC.cream));
    $('#tCream').querySelector('.sw').setAttribute('aria-checked', String(RC.cream));
    $('#tRag').setAttribute('aria-checked', String(RC.rag));
    $('#tRag').querySelector('.sw').setAttribute('aria-checked', String(RC.rag));
    localStorage.setItem('hl_rc', JSON.stringify(RC));
  }
  $$('.rc-fopt').forEach(o => o.addEventListener('click', () => { RC.font = o.dataset.font; applyRC(); }));
  $('#sLs').addEventListener('input', e => { RC.ls = e.target.value; applyRC(); });
  $('#sLh').addEventListener('input', e => { RC.lh = e.target.value; applyRC(); });
  $('#sW').addEventListener('input', e => { RC.w = e.target.value; applyRC(); });
  $('#tCream').addEventListener('click', () => { RC.cream = !RC.cream; applyRC(); });
  $('#tRag').addEventListener('click', () => { RC.rag = !RC.rag; applyRC(); });
  $('#rcReset').addEventListener('click', () => { RC = Object.assign({}, RCdefault); applyRC(); });

  /* ---------- toast + share/export ---------- */
  let toastT;
  function toast(msg) {
    els.toast.textContent = msg;
    els.toast.classList.add('show');
    clearTimeout(toastT);
    toastT = setTimeout(() => els.toast.classList.remove('show'), 1900);
  }
  $('#btnShare').addEventListener('click', () => {
    const url = location.origin + location.pathname + '#q=' + encodeURIComponent(els.recapQ.textContent);
    if (navigator.clipboard) navigator.clipboard.writeText(url).then(() => toast('Share link copied to clipboard')).catch(() => toast('Copy failed'));
    else toast('Share link: ' + url);
  });
  $('#btnExport').addEventListener('click', () => toast('Exported answer + sources as Markdown'));

  /* ---------- cite click → open + flash source ---------- */
  document.addEventListener('click', e => {
    const c = e.target.closest('.cite');
    if (!c) return;
    const n = c.dataset.src;
    const src = $(`.src[data-n="${n}"]`);
    if (src) {
      if (!src.classList.contains('open')) src.querySelector('.src-head').click();
      src.style.transition = 'box-shadow .3s';
      src.style.boxShadow = '0 0 0 3px color-mix(in oklab, var(--sources) 40%, transparent)';
      setTimeout(() => { src.style.boxShadow = ''; }, 900);
    }
  });

  /* ---------- wire search ---------- */
  els.go.addEventListener('click', () => runSearch(els.q.value.trim()));
  els.q.addEventListener('keydown', e => {
    if (e.key === 'Enter') runSearch(els.q.value.trim());
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') runSearch(els.q.value.trim());
  });
  document.addEventListener('keydown', e => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') { e.preventDefault(); runSearch(els.q.value.trim()); }
    if (e.key === 'Escape') { closeRC(); $('#lightbox').classList.remove('show'); }
    if (e.key === '/' && document.activeElement !== els.q) { e.preventDefault(); els.q.focus(); }
  });
  $$('#suggest button').forEach(b => b.addEventListener('click', () => runSearch(b.dataset.q)));
  /* ---------- init ---------- */
  function init() {
    renderSources(); renderVideos(); renderImages(); renderHistory();
    setDark(localStorage.getItem('hl_dark') === '1');
    setCol('nav', localStorage.getItem('hl_col_nav') === '1');
    setCol('rail', localStorage.getItem('hl_col_rail') === '1');
    setSessionMasked(localStorage.getItem('hl_session_masked') === '1');
    applyRC();
    // share-link auto-load
    const m = location.hash.match(/q=([^&]+)/);
    if (m) { try { runSearch(decodeURIComponent(m[1])); } catch (e) {} }
  }
  init();
})();
