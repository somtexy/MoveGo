/* MoveGo Step 32: live Leaflet street map with EXPLICITLY simulated car markers. */
(() => {
  'use strict';
  const root = document.getElementById('live-map');
  const label = document.getElementById('map-status');
  if (!root) return;
  if (typeof window.L === 'undefined') {
    if (label) label.textContent = 'Map unavailable · Check connection';
    return;
  }
  const L = window.L;
  // Default camera only, not a claim about the user's real position.
  const start = [9.0765, 7.3986]; // Abuja city centre
  const map = L.map(root, {zoomControl:false, scrollWheelZoom:false, preferCanvas:true}).setView(start, 13);
  L.control.zoom({position:'topright'}).addTo(map);
  const tile = L.tileLayer(
  'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
  {
    maxZoom: 19,
    referrerPolicy: 'strict-origin-when-cross-origin',
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap contributors</a>'
  }
).addTo(map);


  tile.on('tileerror', () => { if (label) label.textContent='Map tiles unavailable · Check connection'; });
  // GPS marker is created only after browser geolocation succeeds.
  const userIcon = L.divIcon({className:'', html:'<div class="movego-user-dot" aria-hidden="true"></div>',iconSize:[20,20],iconAnchor:[10,10]});
  let userMarker;
  const demoIcon = L.divIcon({className:'',iconSize:[37,37],iconAnchor:[18,18],html:`<div class="movego-demo-car" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M5 17h14l-1-7a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2l-1 7ZM5 12h14M7 17v2M17 17v2M8 14h1M15 14h1"/></svg><span class="movego-demo-car-label">DEMO</span></div>`});
  const offsets = [[.006,.009],[-.006,.012],[.010,-.008]];
  const markers = offsets.map(([a,b])=>L.marker([start[0]+a,start[1]+b],{icon:demoIcon,interactive:false,keyboard:false}).addTo(map));
  let reference = start.slice();
  let motion = 0;
  const reduceMotion=window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
  function positionDemos(center) {
    reference=center;
    markers.forEach((marker,i)=>marker.setLatLng([center[0]+offsets[i][0],center[1]+offsets[i][1]]));
  }
  if (!reduceMotion) {
    setInterval(() => {
      if (document.hidden) return;
      motion += .15;
      markers.forEach((marker,i)=>{
        const [a,b]=offsets[i];
        marker.setLatLng([reference[0]+a+Math.sin(motion+i)*.00013,reference[1]+b+Math.cos(motion+i)*.00013]);
      });
    },1500);
  }
  // Capture before legacy home.js location listener so we avoid two GPS requests.
  function locate(event){
    event.preventDefault(); event.stopImmediatePropagation();
    if (!navigator.geolocation){if(label)label.textContent='GPS unsupported';return;}
    if(label) label.textContent='Finding your location…';
    navigator.geolocation.getCurrentPosition(({coords})=>{
      const point=[coords.latitude,coords.longitude];
      if (!Number.isFinite(point[0])||!Number.isFinite(point[1])) return;
      if(userMarker) userMarker.setLatLng(point);
      else userMarker=L.marker(point,{icon:userIcon,zIndexOffset:900}).addTo(map).bindPopup('Your approximate location');
      map.flyTo(point, 15, {animate:!reduceMotion,duration:1.1});
      positionDemos(point);
      if(label) label.textContent='YOUR LOCATION · CARS ARE DEMO';
      const text=document.querySelector('.origin-small');
      if(text) text.textContent='Approximate GPS position';
      // Only a convenience for the destination form, no claim of saved booking.
      sessionStorage.setItem('movego_home_gps',JSON.stringify({lat:point[0],lon:point[1],at:Date.now()}));
    }, (err)=>{
      if(label) label.textContent=err.code===1?'GPS permission denied':'GPS unavailable · Select pickup manually';
    }, {enableHighAccuracy:true,timeout:12000,maximumAge:30000});
  }
  for(const id of ['locate-btn','location-card'])document.getElementById(id)?.addEventListener('click',locate,true);
  // If a verified route exists from Step 30, show endpoint markers only.
  // Do not draw a straight line and misrepresent it as the actual road route.
  try {
    const route=JSON.parse(sessionStorage.getItem('movego_verified_route')||'null');
    const p=route?.pickup,d=route?.destination;
    if([p?.lat,p?.lon,d?.lat,d?.lon].every(v=>typeof v==='number'&&Number.isFinite(v))){
      const a=[p.lat,p.lon],b=[d.lat,d.lon];
      L.circleMarker(a,{radius:8,color:'#087c4a',weight:3,fillColor:'#fff',fillOpacity:1}).addTo(map).bindPopup('Pickup');
      L.circleMarker(b,{radius:8,color:'#e6a52a',weight:3,fillColor:'#fff',fillOpacity:1}).addTo(map).bindPopup('Destination');
      map.fitBounds(L.latLngBounds(a,b).pad(.3),{animate:false,maxZoom:14});
      if(label)label.textContent='ROUTE ENDPOINTS · CARS ARE DEMO';
    }
  }catch(_){/* No prior verified route. */}
  setTimeout(()=>map.invalidateSize(),400);
  document.addEventListener('visibilitychange',()=>{if(!document.hidden)map.invalidateSize()});
})();
