(()=>{'use strict';
 const driver=location.pathname.includes('/driver/');
 const panel=document.createElement('section');panel.id='movego-payment-panel';
 panel.style.cssText='margin:14px 12px;padding:16px;border:1px solid #b9cfc4;border-radius:16px;background:var(--card,#fff);color:var(--text,#19291f)';
 panel.hidden=true;
 const title=document.createElement('h3'); title.textContent='Trip payment';
 const info=document.createElement('p');
 const msg=document.createElement('p');msg.setAttribute('role','status');
 const button=document.createElement('button');button.type='button';button.style.cssText='padding:12px 16px;background:#087b57;color:white;border:0;border-radius:12px;font-weight:700';
 panel.append(title,info,button,msg);(document.querySelector('main')||document.body).append(panel);
 const csrf=()=>decodeURIComponent(document.cookie.split(';').map(x=>x.trim()).find(x=>x.startsWith('csrftoken='))?.slice(10)||'');
 async function post(url,body){await fetch('/api/auth/csrf/',{credentials:'same-origin'});const r=await fetch(url,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-CSRFToken':csrf()},body:JSON.stringify(body)});const data=await r.json();if(!r.ok)throw Error(data.error||'Payment request failed');return data;}
 async function refresh(){
  try{const r=await fetch('/api/payments/latest/',{credentials:'same-origin',cache:'no-store'});if(!r.ok){panel.hidden=true;return;}const data=await r.json(),ride=data.ride;if(!ride){panel.hidden=true;return;}
   panel.hidden=false; const amount=ride.fare_kobo==null?'Fare unavailable':new Intl.NumberFormat('en-NG',{style:'currency',currency:'NGN'}).format(ride.fare_kobo/100);
   info.textContent=`${ride.pickup} → ${ride.destination} · ${amount}`;
   const p=ride.payment;
   if(p){msg.textContent=p.status==='cash_recorded'?'Driver reported cash collected (not independently verified).':`Payment: ${p.status.replaceAll('_',' ')}`;
    if(p.status==='pending'&&!driver){button.hidden=false;button.textContent='Check Paystack payment';button.onclick=async()=>{button.disabled=true;try{await post(`/api/payments/${ride.id}/verify/`,{});await refresh()}catch(e){msg.textContent=e.message}finally{button.disabled=false}};}else button.hidden=true;
   }else{msg.textContent='';button.hidden=false;button.textContent=driver?'Confirm cash received':'Pay online (test mode)';button.onclick=async()=>{button.disabled=true;try{if(driver){if(!confirm('Confirm that you actually collected cash for this completed trip?'))return;await post(`/api/payments/${ride.id}/cash/`,{confirm_collected:true});await refresh();}else{const data=await post(`/api/payments/${ride.id}/initialize/`,{});window.location.assign(data.authorization_url);}}catch(e){msg.textContent=e.message}finally{button.disabled=false}};}
  }catch(e){panel.hidden=true;}
 }
 // Paystack returns a reference to the callback page. Never treat that redirect as proof of payment.
 // Reconcile only when the returned reference matches the authenticated user's pending ride.
 async function reconcileReturn(){
  const params=new URLSearchParams(location.search);
  const ref=params.get('reference')||params.get('trxref');
  if(!ref)return;
  // Strip provider-supplied reference from the visible URL after it has been processed.
  try{const clean=new URL(location.href);clean.searchParams.delete('reference');clean.searchParams.delete('trxref');
      history.replaceState(history.state,'',clean.pathname+clean.search+clean.hash);}catch(_e){}
  try{
   const r=await fetch('/api/payments/latest/',{credentials:'same-origin',cache:'no-store'});
   if(!r.ok)return;
   const data=await r.json();const ride=data.ride;
   if(!ride||!ride.payment||ride.payment.method!=='paystack'||ride.payment.status!=='pending'||ride.payment.reference!==ref)return;
   panel.hidden=false;msg.textContent='Checking payment securely with Paystack…';
   await post(`/api/payments/${ride.id}/verify/`,{});
   await refresh();
  }catch(e){panel.hidden=false;msg.textContent='Payment is awaiting confirmation. Use Check Paystack payment to retry verification.';}
 }
 refresh().then(reconcileReturn);setInterval(()=>{if(!document.hidden)refresh()},15000);
})();
