(() => {
  'use strict';
  const passenger = document.getElementById('ride-offer-panel');
  const driver = document.getElementById('driver-offer-panel');
  if (!passenger && !driver) return;
  const base='/api/dispatch/';
  let token;
  async function req(url, method='GET', data) {
    let opts={credentials:'same-origin',method,cache:'no-store'};
    if (method==='POST') {
      if (!token) {const r=await fetch('/api/auth/csrf/',{credentials:'same-origin'}); if(!r.ok)throw Error('Sign in again.'); token=(await r.json()).csrfToken;}
      opts.headers={'X-CSRFToken':token,'Content-Type':'application/json'};opts.body=JSON.stringify(data||{});
    }
    const r=await fetch(url,opts), d=await r.json().catch(()=>({})); if (!r.ok)throw Error(d.error||'Request failed.'); return d;
  }
  const show=(el,msg)=>{el.querySelector('[data-state]').textContent=msg;};
  if(passenger) {
    const button=passenger.querySelector('button'); let rideId=null;
    const load=async()=>{try{const active=await req('/api/ride-management/active/');rideId=active.ride?.id||null;
      if(!rideId || !['requested','searching'].includes(active.ride.status)){button.disabled=true;show(passenger,'No unassigned active ride.');return;}
      const state=await req(`${base}rides/${rideId}/status/`);
      button.disabled=state.state==='offered';show(passenger,state.state==='offered'?'Waiting for driver response…':state.state==='assigned'?'Driver accepted your ride.':'Ready to offer this ride to a nearby driver.');
    }catch(e){show(passenger,e.message);}};
    button.addEventListener('click',async()=>{if(!rideId)return;button.disabled=true;try{const x=await req(`${base}rides/${rideId}/offer/`,'POST',{});show(passenger,x.message);}catch(e){show(passenger,e.message);}await load();});
    load();setInterval(()=>{if(!document.hidden)load();},5000);
  }
  if(driver) {
    let offer=null;const accept=driver.querySelector('[data-accept]'),decline=driver.querySelector('[data-decline]');
    const refresh=async()=>{try{const d=await req(base+'driver/offer/');offer=d.offer;accept.disabled=decline.disabled=!offer;
      show(driver,offer?`${offer.pickup} → ${offer.destination} · ${offer.category} · ₦${((offer.estimated_fare_kobo||0)/100).toLocaleString()} · Expires ${new Date(offer.expires_at).toLocaleTimeString()}`:'No ride offers at the moment.');
    }catch(e){accept.disabled=decline.disabled=true;show(driver,e.message);}};
    async function respond(action){if(!offer)return;accept.disabled=decline.disabled=true;try{const x=await req(`${base}driver/offers/${offer.offer_id}/respond/`,'POST',{action});show(driver,action==='accept'?'Ride accepted. View your assigned trip in the next update.':'Offer declined.');offer=null;}catch(e){show(driver,e.message);}setTimeout(refresh,2000);}
    accept.addEventListener('click',()=>respond('accept'));decline.addEventListener('click',()=>respond('decline'));
    refresh();setInterval(()=>{if(!document.hidden)refresh();},5000);
  }
})();
