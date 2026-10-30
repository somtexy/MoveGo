/* MoveGo post-registration theme. Intentionally never loaded on welcome/registration screens. */
(() => {
  'use strict';
  const KEY = 'movego_app_theme';
  let theme = 'light';
  try { theme = localStorage.getItem(KEY) === 'dark' ? 'dark' : 'light'; } catch (_) {}
  const apply = (dark) => {
    document.documentElement.dataset.theme = dark ? 'dark' : 'light';
    const toggle = document.getElementById('theme-toggle');
    if (toggle) toggle.setAttribute('aria-checked', String(dark));
    const meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.content = dark ? '#17231d' : '#fffdf8';
  };
  apply(theme === 'dark');
  document.addEventListener('DOMContentLoaded', () => {
    apply(theme === 'dark');
    const toggle = document.getElementById('theme-toggle');
    if (!toggle) return;
    toggle.addEventListener('click', () => {
      theme = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
      apply(theme === 'dark');
      try { localStorage.setItem(KEY, theme); } catch (_) {}
    });
  });
})();
