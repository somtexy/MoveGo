/* MoveGo Part 2: local saved/recent destinations; no mock addresses or hidden geocoding. */
(() => {
  'use strict';
  const SAVED='movego_saved_places_demo_v1';
  const RECENT='movego_recent_destinations_v1';
  const HANDOFF='movego_saved_destination';
  const sheet=document.querySelector('.bottom-sheet');
  const search=document.getElementById('destination-btn');
  if(!sheet || !search || document.getElementById('movego-destination-suggestions'))return;
  const section=document.createElement('section');
  section.id='movego-destination-suggestions';
  section.className='movego-destination-suggestions';
  section.setAttribute('aria-label','Destination suggestions');
  search.insertAdjacentElement('afterend',section);
  const parse=(key)=>{try{const v=JSON.parse(localStorage.getItem(key)||'[]');return Array.isArray(v)?v:[]}catch{return[]}};
  const normalize=s=>typeof s==='string'?s.trim().slice(0,180):'';
  function go(address){
    if(!address)return;
    try {sessionStorage.setItem(HANDOFF,address)} catch {}
    window.location.href='destination.html';
  }
  function row(label,address,description){
    const button=document.createElement('button');button.type='button';button.className='movego-suggestion-row';
    const icon=document.createElement('span');icon.className='movego-suggestion-pin';icon.setAttribute('aria-hidden','true');
    icon.innerHTML='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M20 10c0 5-8 12-8 12S4 15 4 10a8 8 0 1 1 16 0Z"/><circle cx="12" cy="10" r="2.6"/></svg>';
    const content=document.createElement('span');content.className='movego-suggestion-content';
    const title=document.createElement('strong');title.textContent=label;
    content.append(title);
    if(description){const small=document.createElement('small');small.textContent=description;content.append(small)}
    button.append(icon,content);button.addEventListener('click',()=>go(address));return button;
  }
  function heading(title){const p=document.createElement('div');p.className='movego-suggestions-heading';p.textContent=title;return p}
  function render(){
    section.replaceChildren();
    const places=parse(SAVED).filter(p=>p&&typeof p==='object').map(p=>({label:normalize(p.label),address:normalize(p.address)})).filter(p=>p.label&&p.address).slice(0,4);
    const seen=new Set(places.map(p=>p.address.toLocaleLowerCase()));
    const recents=parse(RECENT).map(normalize).filter(address=>{const k=address.toLocaleLowerCase();if(!address||seen.has(k))return false;seen.add(k);return true}).slice(0,3);
    if(places.length){section.append(heading('Saved places'));places.forEach(p=>section.append(row(p.label,p.address,p.address)))}
    if(recents.length){section.append(heading('Recent destinations'));recents.forEach(p=>section.append(row(p,p,'')))}
    if(!places.length&&!recents.length){section.append(heading('Your destinations'));const p=document.createElement('p');p.className='movego-suggestion-empty';p.textContent='Save places or book a trip to see suggestions here.';section.append(p)}
    const link=document.createElement('a');link.href='saved-places.html';link.className='movego-suggestion-manage';link.textContent='Manage saved places';section.append(link);
  }
  render();window.addEventListener('pageshow',render);window.addEventListener('storage',render);
})();
