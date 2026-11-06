/* Nonblocking registration. Works on localhost or HTTPS; never stores credentials. */
(() => {
  if (!('serviceWorker' in navigator) || !window.isSecureContext) return;
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/app/movego-sw.js', { scope: '/app/' })
      .catch(error => console.warn('MoveGo image cache unavailable:', error));
  }, { once: true });
})();
