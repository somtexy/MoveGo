/* MoveGo Step 35: opt-in GPS updates to authenticated Django API. */
(() => {
  'use strict';
  const start = document.getElementById('gps-start');
  const stop = document.getElementById('gps-stop');
  const status = document.getElementById('gps-status');
  const toggle = document.getElementById('online-toggle');
  if (!start || !stop || !status || !toggle) return;
  let watchId = null, lastSent = 0, sending = false, running = false;
  let token = null;
  const tell = message => { status.textContent = message; };
  const controls = () => {
    start.disabled = running || !toggle.checked || toggle.disabled || !navigator.geolocation;
    stop.disabled = !running;
  };
  async function csrf() {
    if (token) return token;
    const response = await fetch('/api/auth/csrf/', {credentials:'same-origin'});
    if (!response.ok) throw new Error('Could not get security token.');
    token = (await response.json()).csrfToken;
    return token;
  }
  async function post(url, body) {
    const headers = {'X-CSRFToken':await csrf()};
    if (body) headers['Content-Type'] = 'application/json';
    const response = await fetch(url, {method:'POST', credentials:'same-origin', headers,
      ...(body ? {body:JSON.stringify(body)} : {})});
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.error || `GPS update failed (${response.status})`);
    return data;
  }
  function localStop() {
    running = false;
    if (watchId !== null) navigator.geolocation.clearWatch(watchId);
    watchId = null;
    controls();
  }
  async function stopSharing() {
    localStop();
    tell('Stopping GPS sharing…');
    try { await post('/api/drivers/location/stop/'); tell('GPS sharing stopped; last location deleted.'); }
    catch (error) { tell('GPS stopped on this device. Server cleanup failed: ' + error.message); }
  }
  async function upload(position) {
    if (!running || sending || !toggle.checked) return;
    const now = Date.now();
    if (now - lastSent < 12000) return;
    const {latitude:lat, longitude:lon, accuracy} = position.coords;
    if (!Number.isFinite(accuracy) || accuracy > 2000) { tell('GPS accuracy is too low. Move outdoors.'); return; }
    sending = true;
    try {
      await post('/api/drivers/location/', {lat, lon, accuracy_m:accuracy});
      lastSent = now;
      tell(`Location shared securely. GPS accuracy: about ${Math.round(accuracy)} m.`);
    } catch (error) {
      tell(error.message);
      if (/online|approved|login|driver required/i.test(error.message)) await stopSharing();
    } finally { sending = false; }
  }
  start.addEventListener('click', () => {
    if (!navigator.geolocation || !toggle.checked || toggle.disabled) return;
    running = true;
    controls();
    tell('Requesting GPS permission…');
    watchId = navigator.geolocation.watchPosition(upload, error => {
      tell(`Unable to read GPS: ${error.message}`);
      if (error.code === 1) { localStop(); }
    }, {enableHighAccuracy:true, maximumAge:0, timeout:20000});
  });
  stop.addEventListener('click', stopSharing);
  toggle.addEventListener('change', () => {
    if (!toggle.checked && running) stopSharing();
    controls();
  });
  // driver-portal.js updates the checkbox asynchronously after toggling.
  const observer = new MutationObserver(controls);
  observer.observe(toggle, {attributes:true, attributeFilter:['disabled']});
  const monitor = setInterval(() => {
    controls();
    if (running && (!toggle.checked || toggle.disabled)) stopSharing();
  }, 1500);
  document.addEventListener('visibilitychange', () => {
    // Browser GPS runs only while dashboard is in the foreground.
    if (document.hidden && running) stopSharing();
  });
  window.addEventListener('pagehide', () => {
    if (watchId !== null) navigator.geolocation.clearWatch(watchId);
    running = false;
    // best effort cleanup; server also ignores stale location after 90 seconds
    if (navigator.sendBeacon) {
      // CSRF-protected endpoint cannot reliably use beacon headers: TTL is fail-safe.
    }
    clearInterval(monitor);
  });
  controls();
})();
