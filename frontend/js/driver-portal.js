(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const message = $('message');
  const say = text => { if (message) message.textContent = text; };
  const API = '/api/drivers/';
  async function csrf() {
    const response = await fetch('/api/auth/csrf/', {credentials: 'same-origin'});
    if (!response.ok) throw new Error('Could not load security token. Please sign in again.');
    return (await response.json()).csrfToken;
  }
  async function api(path, method='GET', data=null) {
    const options = {method, credentials: 'same-origin'};
    if (method !== 'GET') {
      options.headers = {'Content-Type': 'application/json', 'X-CSRFToken': await csrf()};
      options.body = JSON.stringify(data);
    }
    const r = await fetch(API+path, options);
    const payload = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(payload.error || `Request failed (${r.status}).`);
    return payload;
  }
  const form = $('driver-form');
  if (form) {
    form.addEventListener('submit', async event => {
      event.preventDefault();
      const button = $('submit'); button.disabled = true; say('Submitting application…');
      try {
        const files = ['nin_document','license_photo','selfie_photo'];
        for (const name of files) {
          const f = form.elements[name].files?.[0];
          if (!f || !f.type.startsWith('image/') || f.size > 5 * 1024 * 1024) {
            throw new Error('Add all three document photos. Each must be an image under 5 MB.');
          }
        }
        const options = {method:'POST',credentials:'same-origin',
          headers:{'X-CSRFToken':await csrf()},body:new FormData(form)};
        const response = await fetch(API+'register/',options);
        const result = await response.json().catch(()=>({}));
        if (!response.ok) throw new Error(result.error || 'Application failed.');
        location.href = 'home.html';
      } catch (error) { say(error.message); button.disabled = false; }
    });
  }
  const toggle = $('online-toggle');
  if (toggle) {
    async function load() {
      try {
        const data = await api('me/');
        if (!data.registered) { location.replace('setup.html'); return; }
        $('review-status').textContent = data.review_status === 'approved' ? 'Approved' : data.review_status === 'rejected' ? 'Not approved' : 'Pending review';
        $('vehicle').textContent = `${data.vehicle_color} ${data.vehicle_make} ${data.vehicle_model} · ${data.plate_number}`;
        toggle.checked = data.is_online;
        toggle.disabled = data.review_status !== 'approved';
        $('online-description').textContent = data.review_status === 'approved' ?
          (data.is_online ? 'You are marked online.' : 'You are currently offline.') :
          'Availability unlocks after manual approval.';
      } catch (error) { say(error.message); }
    }
    toggle.addEventListener('change', async () => {
      const requested = toggle.checked;
      toggle.disabled = true; say('Saving availability…');
      try { await api('availability/', 'POST', {is_online: requested}); say(requested ? 'Marked online. Dispatch is not active yet.' : 'You are offline.'); }
      catch (error) { say(error.message); toggle.checked = !requested; }
      await load();
    });
    load();
  }
})();
