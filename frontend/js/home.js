'use strict';
const $ = (id) => document.getElementById(id);
const toast = (message) => { const el = $('toast'); el.textContent = message; el.hidden = false; clearTimeout(toast.timer); toast.timer = setTimeout(() => { el.hidden = true; }, 4000); };
let storedName = sessionStorage.getItem('movego_first_name');
try { const profile=JSON.parse(localStorage.getItem('movego_demo_profile')||'null'); if(profile?.firstName) storedName=[profile.firstName,profile.lastName].filter(Boolean).join(' '); } catch (_) {}
if (storedName) { $('drawer-name').textContent = storedName; $('drawer-avatar').textContent = storedName.charAt(0).toUpperCase(); }
function showPanel(id, backdropId, open) {
  $(id).classList.toggle('open', open);
  $(id).setAttribute('aria-hidden', String(!open));
  $(backdropId).hidden = !open;
  if (id === 'drawer') { $('menu-btn').setAttribute('aria-expanded', String(open)); $(id).inert = !open; }
}
$('menu-btn').addEventListener('click', () => showPanel('drawer','drawer-backdrop',true));
$('drawer-close').addEventListener('click', () => showPanel('drawer','drawer-backdrop',false));
$('drawer-backdrop').addEventListener('click', () => showPanel('drawer','drawer-backdrop',false));
$('alerts-btn').addEventListener('click', () => { window.location.href='notifications.html'; });
document.querySelector('[data-notifications]')?.addEventListener('click', () => { window.location.href='notifications.html'; });
try { const list=JSON.parse(localStorage.getItem('movego_demo_notifications_v1')||'[]'); const unread=Array.isArray(list)&&list.some(n=>!n.read); const dot=$('notice-dot'); if(dot) dot.hidden=!unread; }catch(_){ const dot=$('notice-dot'); if(dot) dot.hidden=true; }
document.querySelectorAll('[data-demo]').forEach(button => button.addEventListener('click', () => { if (button.dataset.demo === 'Request history') { location.href = 'history.html'; return; } if (button.dataset.demo === 'Safety') { location.href = 'safety.html'; return; } if (button.dataset.demo === 'Help' || button.dataset.demo === 'Support') { location.href = 'help.html'; return; } toast(`${button.dataset.demo} is coming in a future step.`); }));
let currentService = 'Ride';
document.querySelectorAll('[data-service]').forEach(button => button.addEventListener('click', () => {
  currentService = button.dataset.service;
  document.querySelectorAll('[data-service]').forEach(el => { const active = el === button; el.classList.toggle('active',active); el.setAttribute('aria-pressed',String(active)); });
  toast(`${currentService} selected. Search for a destination to continue.`);
}));
const places = ['Wuse 2, Abuja','Jabi Lake Mall, Abuja','Nnamdi Azikiwe International Airport','Gwarinpa, Abuja','Central Area, Abuja']; // Clearly labeled demo suggestions, not geocoded search results.
function renderSuggestions(term='') {
  const container = $('suggestions'); container.replaceChildren();
  const filtered = places.filter(place => place.toLowerCase().includes(term.toLowerCase()));
  if (!filtered.length) { const p=document.createElement('p'); p.className='hint'; p.textContent='No demo suggestions match. You can still enter a destination name.';container.append(p);return; }
  for(const place of filtered){ const b=document.createElement('button'); b.type='button'; b.textContent=place; b.addEventListener('click', () => selectPlace(place)); container.append(b); }
}
function selectPlace(place){ $('destination-input').value=place; const preview=$('trip-preview'); preview.hidden=false; preview.textContent=`${currentService} → ${place}. Destination saved as a demo selection. Route calculation, availability, and fare estimates will be enabled with the Django backend and live maps.`; }
function openSearch(){showPanel('search-panel','search-backdrop',true);$('trip-preview').hidden=true;renderSuggestions();setTimeout(()=>$('destination-input').focus(),270);}
function closeSearch(){showPanel('search-panel','search-backdrop',false);$('destination-btn').focus();}
$('destination-btn').addEventListener('click', () => { sessionStorage.setItem('movego_ride_service', currentService); window.location.href = 'destination.html'; });
$('search-back').addEventListener('click', closeSearch);
$('search-backdrop').addEventListener('click', closeSearch);
$('destination-input').addEventListener('input', e => { $('trip-preview').hidden=true;renderSuggestions(e.target.value.trim()); });
$('destination-input').addEventListener('keydown', e=>{if(e.key==='Enter'){e.preventDefault(); const value=e.target.value.trim();if(value)selectPlace(value);}});
document.addEventListener('keydown',e=>{if(e.key==='Escape'){closeSearch();showPanel('drawer','drawer-backdrop',false);}});
function locate(){ if (!navigator.geolocation) {toast('This browser does not support location access.');return;} toast('Requesting device location…'); navigator.geolocation.getCurrentPosition(p=>{toast(`Location received (${p.coords.latitude.toFixed(4)}, ${p.coords.longitude.toFixed(4)}). Live map positioning is not connected yet.`);}, e=>{toast(e.code===1?'Location permission denied. You can still explore the demo.':'Could not get your location. Check GPS and connection.');},{enableHighAccuracy:false,timeout:9000,maximumAge:30000}); }
$('locate-btn').addEventListener('click',locate); $('location-card').addEventListener('click',locate);

// Step 16: account screen navigation.
document.querySelector('[data-account]')?.addEventListener('click', () => { window.location.href = 'account.html'; });

// Step 20: saved places menu navigation.
document.querySelector('[data-saved-places]')?.addEventListener('click',()=>{window.location.href='saved-places.html';});
