(function () {
  'use strict';
  let controller;
  function init(root = document) {
    if (controller) controller.abort();
    controller = new AbortController();
    const signal = controller.signal;
    document.documentElement.classList.add('has-js');
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
