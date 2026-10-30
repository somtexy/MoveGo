"use strict";
const $ = id => document.getElementById(id);
let draft = null;
try { draft = JSON.parse(sessionStorage.getItem('movego_ride_option_draft') || 'null'); } catch (_) {}
const stagesReady = sessionStorage.getItem('movego_search_preview') === 'active';
const valid = draft && typeof draft.pickup === 'string' && draft.pickup.trim().length >= 3 && typeof draft.destination === 'string' && draft.destination.trim().length >= 3 && ['Ride','Comfort','One Click','Couriers'].includes(draft.option) && stagesReady;
if (!valid) { location.replace('home.html'); }
else {
  $('pickup').textContent = draft.pickup.slice(0,120);
  $('destination').textContent = draft.destination.slice(0,120);
  $('service').textContent = draft.option;
  $('payment').textContent = sessionStorage.getItem('movego_payment_method') === 'cash' ? 'Cash (demo)' : 'Online (demo — not charged)';
  $('fare').textContent = Number.isFinite(draft.illustrativeFareNgn) && draft.illustrativeFareNgn >= 0 ? new Intl.NumberFormat('en-NG',{style:'currency',currency:'NGN',maximumFractionDigits:0}).format(draft.illustrativeFareNgn) + ' (demo)' : 'Not available';
  $('date').textContent = new Intl.DateTimeFormat('en-NG',{dateStyle:'medium'}).format(new Date());
  let rating = 0;
  const stars = [...$('stars').querySelectorAll('button')];
  function setRating(value){rating=value;stars.forEach((button,index)=>{button.textContent=index<rating?'★':'☆';button.setAttribute('aria-pressed',String(index+1===rating));});$('save-rating').disabled=false;$('feedback-status').textContent='';}
  stars.forEach(button => button.addEventListener('click',()=>setRating(Number(button.dataset.rating))));
  $('save-rating').addEventListener('click',()=>{
    if (!rating) return;
    const entry={rating,feedback:$('feedback').value.trim().slice(0,300),savedAt:new Date().toISOString(),demo:true};
    try {sessionStorage.setItem('movego_demo_rating',JSON.stringify(entry));$('feedback-status').textContent=`Your ${rating}-star demo rating was saved in this browser session. It was not sent to a driver.`;}catch(_){$('feedback-status').textContent='Your demo rating was selected, but browser storage is unavailable.';}
  });
}

// Explicitly save only a simulated trip. Never represent these records as real rides.
const saveTripHistory = document.getElementById('save-trip-history');
if (saveTripHistory) saveTripHistory.addEventListener('click',()=>{
  const out=document.getElementById('trip-history-status');
  if (!valid){out.textContent='No demo trip available.';return;}
  const key='movego_demo_trip_history_v1';
  let saved=[];try{saved=JSON.parse(localStorage.getItem(key)||'[]');if(!Array.isArray(saved))saved=[];}catch{saved=[];}
  const sessionKey='movego_demo_trip_receipt_id';
  let id=sessionStorage.getItem(sessionKey);
  if (!id){id='DEMO-'+Date.now().toString(36).toUpperCase()+'-'+Math.random().toString(36).slice(2,6).toUpperCase();sessionStorage.setItem(sessionKey,id);}
  if (saved.some(item=>item.id===id)){out.textContent='This demo trip is already in your history.';return;}
  const entry={id,createdAt:new Date().toISOString(),pickup:draft.pickup.slice(0,120),destination:draft.destination.slice(0,120),service:draft.option,payment:sessionStorage.getItem('movego_payment_method')==='cash'?'Cash (demo)':'Online (demo)',fare:Number.isFinite(draft.illustrativeFareNgn)?draft.illustrativeFareNgn:null,status:'completed',demo:true};
  try{localStorage.setItem(key,JSON.stringify([entry,...saved].slice(0,50)));out.textContent='Saved as a DEMO record on this device. No actual ride or payment occurred.';}catch{out.textContent='Could not save demo trip. Check browser storage settings.';}
});
