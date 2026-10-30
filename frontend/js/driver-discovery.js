(() => {
  'use strict';
  const panel=document.createElement('section');
  panel.setAttribute('aria-live','polite');
  panel.style.cssText='margin:18px 16px;padding:16px;border:1px solid rgba(130,140,130,.3);border-radius:16px;background:var(--card-bg,transparent);color:inherit;font:inherit';
  const heading=document.createElement('strong');heading.textContent='Nearby drivers';
  const status=document.createElement('p');status.textContent='Checking current availability…';
  status.style.margin='10px 0 0';panel.append(heading,status);
  const target=document.querySelector('main')||document.body;
  target.appendChild(panel);
  async function refresh(){
    try{
      const active=await fetch('/api/ride-management/active/',{credentials:'same-origin',cache:'no-store'});
      if(!active.ok)throw Error('Sign in as a passenger to see availability.');
      const info=await active.json();
      if(!info.ride){status.textContent='No active ride request. Create a booking to check nearby drivers.';return;}
      if(!info.ride.can_cancel){status.textContent='This ride is no longer searching for a driver.';return;}
      const r=await fetch('/api/driver-discovery/nearby/?ride_id='+encodeURIComponent(info.ride.id),{credentials:'same-origin',cache:'no-store'});
      const data=await r.json();
      if(!r.ok)throw Error(data.error||'Availability could not be checked.');
      status.textContent=({none:'No eligible drivers nearby right now.',few:'A few eligible drivers are nearby.',several:'Several eligible drivers are nearby.'}[data.availability]||'Availability unavailable.')+' Discovery only — no driver is assigned yet.';
    }catch(e){status.textContent=e.message||'Unable to check nearby drivers.';}
  }
  refresh();
  const timer=setInterval(()=>{if(!document.hidden)refresh();},30000);
  window.addEventListener('pagehide',()=>clearInterval(timer),{once:true});
})();
