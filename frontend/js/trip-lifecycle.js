(() => {
  'use strict';
  const driverPage = location.pathname.includes('/driver/');
  const panel = document.createElement('section');
  panel.id = 'movego-live-trip';
  panel.setAttribute('aria-live','polite');
  panel.style.cssText = 'margin:14px 12px;padding:15px;background:var(--card,#fff);color:var(--text,#17221d);border:1px solid #c8d4cc;border-radius:16px;box-shadow:0 4px 15px #0001;';
  const title = document.createElement('h3'); title.textContent='Current trip';
  const summary = document.createElement('p');
  const action = document.createElement('button'); action.type='button';
  action.style.cssText='padding:12px 18px;border:none;border-radius:12px;background:#087b57;color:white;font-weight:700;cursor:pointer;';
  const messages = {assigned:['depart','On my way'],arriving:['arrive','I have arrived'],arrived:['start','Start trip'],started:['complete','Complete trip']};
  panel.append(title,summary,action);
  const mount = document.querySelector('main') || document.body;
  mount.append(panel);
  function cookie(name) {return document.cookie.split(';').map(v=>v.trim()).find(v=>v.startsWith(name+'='))?.slice(name.length+1)||'';}
  async function refresh() {
    try {
      const r = await fetch('/api/trips/my/',{credentials:'same-origin',cache:'no-store'});
      if(!r.ok){panel.hidden=true;return;}
      const payload = await r.json(); const trip=payload.ride;
      if(!trip){panel.hidden=true;return;}
      panel.hidden=false;
      summary.textContent = `${trip.pickup} → ${trip.destination} · ${trip.status.replaceAll('_',' ')}`;
      const next = messages[trip.status];
      action.hidden = !driverPage || !next;
      if(!next)return;
      action.textContent = next[1];
      action.onclick = async () => {
        action.disabled=true;
        try {
          const csrf=await fetch('/api/auth/csrf/',{credentials:'same-origin'});
          if(!csrf.ok)throw new Error('Could not initialize security token');
          const res=await fetch(`/api/trips/${trip.ride_id}/advance/`,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-CSRFToken':decodeURIComponent(cookie('csrftoken'))},body:JSON.stringify({action:next[0]})});
          if(!res.ok){const data=await res.json();throw new Error(data.error||'Trip update failed');}
          await refresh();
        } catch(err){window.alert(err.message);} finally {action.disabled=false;}
      };
    } catch(e){panel.hidden=true;}
  }
  refresh();setInterval(()=>{if(!document.hidden)refresh();},10000);
})();
