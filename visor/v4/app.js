(function () {
  'use strict';
  let controller;

  /* Vídeo de presentación: se pinta solo si video.json trae una ruta de vídeo. Sin ruta, el bloque queda oculto.
     No se carga el reproductor hasta que la persona pulsa «Ver el vídeo»; sin reproducción automática. */
  function initVideo(root, signal) {
    const sec = root.querySelector('[data-video]');
    if (!sec || typeof fetch !== 'function') return;
    fetch('video.json', {cache: 'no-cache'}).then(r => (r.ok ? r.json() : null)).then(cfg => {
      if (!cfg || typeof cfg.base !== 'string' || typeof cfg.video !== 'string' || !cfg.video) return;
      const join = p => (p ? cfg.base.replace(/\/+$/, '') + '/' + String(p).replace(/^\/+/, '') : '');
      const url = join(cfg.video);
      if (!/^https:\/\//.test(url)) return;
      const cuerpo = sec.querySelector('[data-video-cuerpo]');
      cuerpo.textContent = '';
      const boton = document.createElement('button');
      boton.type = 'button';
      boton.className = 'video-boton';
      boton.textContent = 'Ver el vídeo';
      const enlace = document.createElement('a');
      enlace.className = 'video-enlace';
      enlace.href = url;
      enlace.rel = 'noopener';
      enlace.textContent = 'Abrir el vídeo en otra pestaña';
      if (cfg.poster) {
        const img = document.createElement('img');
        img.className = 'video-poster';
        img.src = join(cfg.poster);
        img.alt = '';
        img.loading = 'lazy';
        cuerpo.appendChild(img);
      }
      cuerpo.append(boton, enlace);
      if (cfg.transcripcion) {
        const t = document.createElement('a');
        t.className = 'video-enlace';
        t.href = join(cfg.transcripcion);
        t.rel = 'noopener';
        t.textContent = 'Transcripción';
        cuerpo.appendChild(t);
      }
      boton.addEventListener('click', () => {
        const v = document.createElement('video');
        v.controls = true;
        v.preload = 'metadata';
        v.playsInline = true;
        v.src = url;
        if (cfg.poster) v.poster = join(cfg.poster);
        if (cfg.subtitulos) {
          const tr = document.createElement('track');
          tr.kind = 'subtitles';
          tr.srclang = 'es';
          tr.label = 'Español';
          tr.src = join(cfg.subtitulos);
          tr.default = true;
          v.appendChild(tr);
        }
        cuerpo.textContent = '';
        cuerpo.appendChild(v);
        v.focus();
      }, {signal});
      sec.hidden = false;
    }).catch(() => {});
  }
  function init(root = document) {
    if (controller) controller.abort();
    controller = new AbortController();
    const signal = controller.signal;
    document.documentElement.classList.add('has-js');
    initVideo(root, signal);
    const menu = root.querySelector('[data-menu]');
    const nav = root.querySelector('[data-nav]');
    if (menu && nav) {
      const close = (returnFocus = false) => {
        nav.classList.remove('is-open');
        menu.setAttribute('aria-expanded', 'false');
        menu.textContent = 'Menú';
        if (returnFocus) menu.focus();
      };
      menu.addEventListener('click', () => {
        const open = !nav.classList.contains('is-open');
        nav.classList.toggle('is-open', open);
        menu.setAttribute('aria-expanded', String(open));
        menu.textContent = open ? 'Cerrar' : 'Menú';
      }, {signal});
      nav.addEventListener('click', e => { if (e.target.closest('a')) close(); }, {signal});
      document.addEventListener('keydown', e => {
        if (e.key === 'Escape' && nav.classList.contains('is-open')) close(true);
      }, {signal});
      document.addEventListener('click', e => {
        if (!nav.contains(e.target) && !menu.contains(e.target)) close();
      }, {signal});
      window.addEventListener('resize', () => {
        if (window.innerWidth > 1000) close();
      }, {signal});
    }
    const list = root.querySelector('[data-doi-list]');
    if (!list) return;
    const search = root.querySelector('[data-doi-search]');
    const data = Array.isArray(window.DDD_MAPS)
      ? window.DDD_MAPS.filter(x => x && typeof x === 'object') : [];
    const create = (tag, cls, value) => {
      const n = document.createElement(tag);
      if (cls) n.className = cls;
      n.textContent = String(value ?? '');
      return n;
    };
    const normalise = value => String(value ?? '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('es');
    const validDoi = doi => typeof doi === 'string' && /^10\.\d{4,9}\/[^\s\u0000-\u001f\u007f]+$/.test(doi);
    function render() {
      list.replaceChildren();
      const q = normalise(search ? search.value.trim() : '');
      const records = data.filter(x => normalise([x.nombre, x.territorio, x.id, x.nivel].filter(Boolean).join(' ')).includes(q));
      if (!records.length) {
        list.append(create('p', 'empty', data.length
          ? 'Ningún mapa coincide con la búsqueda.'
          : 'Todavía no hay fichas de mapas incorporadas a este catálogo.'));
        return;
      }
      records.forEach(x => {
        const row = create('article', 'catalog-item', '');
        const label = create('div', '', '');
        label.append(create('strong', '', x.nombre || x.id || 'Mapa'));
        label.append(create('small', '', [x.territorio, x.version ? 'Versión ' + x.version : '', x.fecha].filter(Boolean).join(' · ')));
        let link;
        if (validDoi(x.doi)) {
          link = create('a', 'doi-anchor', x.doi);
          link.href = 'https://doi.org/' + encodeURIComponent(x.doi).replace(/%2F/gi, '/');
          link.target = '_blank';
          link.rel = 'noopener noreferrer';
        } else {
          link = create('span', 'doi-anchor', 'DOI pendiente de incorporar');
        }
        row.append(label, link);
        list.append(row);
      });
    }
    if (search) search.addEventListener('input', render, {signal});
    render();
  }
  window.DDDInit = init;
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', () => init(), {once: true});
  else init();
})();
