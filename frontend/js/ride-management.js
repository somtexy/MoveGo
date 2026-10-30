/* Step 40: passenger ride cancellation UI. The backend is authoritative. */
(() => {
  'use strict';
  const status = document.createElement('section');
  status.id = 'movego-active-request';
  status.setAttribute('aria-label', 'Active ride request');
  status.style.cssText = 'margin:18px 0;padding:16px;border:1px solid #dbe5dc;border-radius:18px;background:var(--surface,#fff);color:inherit';
  const heading = document.createElement('h2');
  heading.textContent = 'Active ride request';
  heading.style.cssText = 'margin:0 0 8px;font-size:18px';
  const info = document.createElement('p');
  info.setAttribute('role','status');
  info.style.cssText='margin:6px 0 12px;font-size:14px;line-height:1.5';
  const cancel = document.createElement('button');
  cancel.type = 'button';
  cancel.textContent = 'Cancel request';
  cancel.style.cssText='border:1px solid #b42318;border-radius:12px;padding:12px 16px;background:transparent;color:#b42318;font-weight:650;cursor:pointer';
  cancel.hidden = true;
  status.append(heading,info,cancel);
  const main = document.querySelector('main');
  if (!main) return;
  const actions = document.querySelector('.actions');
  if (actions && actions.parentElement === main) main.insertBefore(status,actions);
  else main.append(status);
  let active = null;
  const csrf = async () => {
    const r = await fetch('/api/auth/csrf/',{credentials:'same-origin'});
    if(!r.ok) throw new Error('Could not load security token.');
    return (await r.json()).csrfToken;
  };
  async function load() {
    info.textContent = 'Checking active requests…';cancel.hidden=true;
    try {
      const response = await fetch('/api/ride-management/active/',{credentials:'same-origin',cache:'no-store'});
      const data=await response.json();
      if(!response.ok) throw new Error(data.error || 'Could not check requests.');
      active=data.ride;
      if(!active){info.textContent='You have no active ride request.';return;}
      info.textContent=`Request #${active.id} • ${active.pickup} → ${active.destination} • ${active.status}. Driver dispatch is not yet available.`;
      cancel.hidden=!active.can_cancel;
      if(!active.can_cancel) info.textContent+=' Cancellation is unavailable at this stage.';
    }catch(error){info.textContent=error.message;}
  }
  cancel.addEventListener('click', async()=>{
    if(!active || !active.can_cancel) return;
    if(!window.confirm(`Cancel request #${active.id}?`)) return;
    cancel.disabled=true;
    try{
      const response=await fetch(`/api/ride-management/${encodeURIComponent(active.id)}/cancel/`,{
        method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-CSRFToken':await csrf()},body:'{}'});
      const data=await response.json();
      if(!response.ok) throw new Error(data.error||'Cancellation failed.');
      await load();
      info.textContent='Request cancelled. You can now make another request. No payment was collected.';
    }catch(error){info.textContent=error.message;}
    finally{cancel.disabled=false;}
  });
  load();
})();
