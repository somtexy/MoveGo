'use strict';
(() => {
  // Capture before legacy onboarding notices. No tokens or credentials in browser storage.
  document.addEventListener('click', (event) => {
    const button = event.target.closest('[data-feature="google"]');
    if (!button) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    window.location.assign('/api/auth/google/start/');
  }, true);
})();
