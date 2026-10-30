'use strict';
const byId = id => document.getElementById(id);
const pickup = byId('pickup');
const dropoff = byId('dropoff');
let service = sessionStorage.getItem('movego_ride_service') || 'Ride';
if (!['Ride','Comfort','One Click','Couriers'].includes(service)) service = 'Ride';
const serviceButtons = document.querySelectorAll('[data-service]');
function updateService() {
  serviceButtons.forEach(button => {
    const active = button.dataset.service === service;
    button.classList.toggle('selected', active);
    button.setAttribute('aria-pressed', String(active));
  });
}
serviceButtons.forEach(button => button.addEventListener('click', () => {
  service = button.dataset.service;
  sessionStorage.setItem('movego_ride_service', service);
  byId('review').hidden = true;
  updateService();
}));
updateService();

// location-live.js owns form submission, coordinate validation and routing.
byId('edit')?.addEventListener('click', () => {
  byId('review').hidden = true;
  pickup.focus();
});
byId('swap')?.addEventListener('click', () => {
  const value = pickup.value;
  pickup.value = dropoff.value;
  dropoff.value = value;
  byId('review').hidden = true;
});
byId('use-location')?.addEventListener('click', () => {
  const status = byId('location-status');
  if (!navigator.geolocation) {
    status.textContent = 'Location access is unavailable. Enter your pickup manually.';
    return;
  }
  status.textContent = 'Requesting GPS permission…';
  navigator.geolocation.getCurrentPosition(position => {
    status.textContent = 'Finding your approximate address…';
    window.dispatchEvent(new CustomEvent('movego:gps-pickup', {
      detail: { lat: position.coords.latitude, lon: position.coords.longitude }
    }));
  }, err => {
    status.textContent = err.code === 1
      ? 'Location permission denied. Enter pickup manually.'
      : 'Unable to get GPS coordinates. Enter pickup manually.';
  }, {timeout: 10000, maximumAge: 30000});
});

// Saved Places currently holds labels only. The passenger must select a
// live geocoded suggestion to get valid coordinates before requesting a route.
try {
  const saved = sessionStorage.getItem('movego_saved_destination');
  if (saved) {
    dropoff.value = saved;
    sessionStorage.removeItem('movego_saved_destination');
  }
} catch (_) {}
