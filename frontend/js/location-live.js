/* MoveGo Step 30: real location coordinates and verified routes. */
(() => {
  'use strict';
  const pickup = document.getElementById('pickup');
  const dropoff = document.getElementById('dropoff');
  const form = document.getElementById('route-form');
  const error = document.getElementById('form-error');
  const review = document.getElementById('review');
  if (!pickup || !dropoff || !form || !error || !review) return;

  const coords = { pickup: null, dropoff: null };
  let focused = 'dropoff';
  let debounceTimer;
  let searchController = null;
  let requestId = 0;
  const suggestions = document.createElement('div');
  suggestions.id = 'live-locations';
  suggestions.setAttribute('aria-label', 'Live address suggestions');
  suggestions.style.cssText = 'display:grid;gap:6px;margin:12px 0';
  const notice = document.createElement('p');
  notice.setAttribute('role', 'status');
  notice.style.cssText = 'font-size:13px;line-height:1.5;margin:8px 0';
  form.insertBefore(suggestions, document.querySelector('.ride-kind') || error);
  form.insertBefore(notice, suggestions);

  const valid = p => p && Number.isFinite(p.lat) && Number.isFinite(p.lon)
    && Math.abs(p.lat) <= 90 && Math.abs(p.lon) <= 180;
  const normalize = obj => {
    const p = {lat: Number(obj?.lat), lon: Number(obj?.lon)};
    return obj && valid(p) ? p : null;
  };
  function invalidate() {
    review.hidden = true;
    sessionStorage.removeItem('movego_verified_route');
  }
  function clear(which) {
    coords[which] = null;
    invalidate();
  }
  function cancelSearch() {
    clearTimeout(debounceTimer);
    searchController?.abort();
    searchController = null;
    ++requestId;
    suggestions.replaceChildren();
  }
  function choose(which, place) {
    const p = normalize(place);
    if (!p) return;
    coords[which] = p;
    (which === 'pickup' ? pickup : dropoff).value = place.label || `${p.lat}, ${p.lon}`;
    cancelSearch();
    invalidate();
    notice.textContent = `${which === 'pickup' ? 'Pickup' : 'Destination'} selected from live results.`;
  }
  async function search(which) {
    const field = which === 'pickup' ? pickup : dropoff;
    const query = field.value.trim();
    cancelSearch();
    notice.textContent = '';
    if (query.length < 3) return;
    const current = requestId;
    searchController = new AbortController();
    try {
      const response = await fetch(`/api/locations/autocomplete/?q=${encodeURIComponent(query)}`, {
        credentials: 'same-origin', signal: searchController.signal
      });
      const data = await response.json();
      if (current !== requestId || focused !== which) return;
      if (!response.ok) throw new Error(data.error || 'Address lookup failed');
      const matches = (data.results || []).filter(p => normalize(p));
      if (!matches.length) {
        notice.textContent = 'No matching addresses. Try a more specific Nigerian location.';
        return;
      }
      for (const place of matches) {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'place';
        button.textContent = place.label;
        button.addEventListener('click', () => choose(which, place));
        suggestions.append(button);
      }
    } catch (e) {
      if (e.name !== 'AbortError' && current === requestId) notice.textContent = e.message;
    }
  }
  for (const [which, field] of [['pickup', pickup], ['dropoff', dropoff]]) {
    field.addEventListener('focus', () => {
      focused = which;
      if (!coords[which] && field.value.trim().length >= 3) search(which);
      else cancelSearch();
    });
    field.addEventListener('input', () => {
      focused = which;
      clear(which);
      cancelSearch();
      debounceTimer = setTimeout(() => search(which), 350);
    });
  }

  // destination.js obtains GPS and dispatches exactly one event.
  window.addEventListener('movego:gps-pickup', async event => {
    const point = normalize(event.detail);
    if (!point) {
      error.textContent = 'GPS returned invalid coordinates.';
      return;
    }
    cancelSearch();
    coords.pickup = point;
    invalidate();
    const status = document.getElementById('location-status');
    const fallback = `GPS: ${point.lat.toFixed(5)}, ${point.lon.toFixed(5)}`;
    pickup.value = fallback;
    notice.textContent = 'GPS pickup captured. Looking up approximate address…';
    try {
      const response = await fetch(`/api/locations/reverse/?lat=${encodeURIComponent(point.lat)}&lon=${encodeURIComponent(point.lon)}`, {credentials:'same-origin'});
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Reverse lookup unavailable');
      if (coords.pickup !== point) return;
      pickup.value = data.label || fallback;
      notice.textContent = 'GPS pickup is ready. Select a live destination suggestion.';
      if (status) status.textContent = data.label ? 'Approximate address found.' : 'GPS coordinates captured.';
    } catch (_) {
      if (coords.pickup !== point) return;
      notice.textContent = 'GPS pickup is ready. Address lookup unavailable; coordinates remain valid.';
      if (status) status.textContent = 'GPS coordinates captured.';
    }
  });

  // destination.js swaps the visible input values; swap the matching coordinates too.
  document.getElementById('swap')?.addEventListener('click', () => {
    cancelSearch();
    [coords.pickup, coords.dropoff] = [coords.dropoff, coords.pickup];
    invalidate();
    notice.textContent = 'Locations swapped. Select any missing location from live suggestions.';
  });

  const routeInfo = document.createElement('dd');
  routeInfo.id = 'live-route-info';
  review.querySelector('dl')?.append(routeInfo);
  const continueButton = form.querySelector('button[type="submit"]');
  const continueOriginal = continueButton?.innerHTML || 'Continue';

  async function csrf() {
    const response = await fetch('/api/auth/csrf/', {credentials: 'same-origin'});
    if (!response.ok) throw new Error('Could not load security token');
    return (await response.json()).csrfToken;
  }

  // Continue is the single route calculation action. No separate calculate button.
  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (continueButton?.disabled) return;
    error.textContent = '';
    invalidate();
    const a = pickup.value.trim();
    const b = dropoff.value.trim();
    if (!valid(coords.pickup) || !valid(coords.dropoff)) {
      const missing = [!valid(coords.pickup) && 'pickup', !valid(coords.dropoff) && 'destination'].filter(Boolean).join(' and ');
      error.textContent = `Select a real ${missing} location from live suggestions${!valid(coords.pickup) ? ', or use GPS for pickup' : ''}.`;
      return;
    }
    if (coords.pickup.lat === coords.dropoff.lat && coords.pickup.lon === coords.dropoff.lon) {
      error.textContent = 'Pickup and destination must differ.';
      return;
    }
    const selectedPickup = {...coords.pickup};
    const selectedDestination = {...coords.dropoff};
    const selectedService = sessionStorage.getItem('movego_ride_service') || 'Ride';
    const startPickupLabel = a;
    const startDestinationLabel = b;
    if (continueButton) {
      continueButton.disabled = true;
      continueButton.textContent = 'Calculating route…';
    }
    try {
      const response = await fetch('/api/locations/route/', {
        method: 'POST', credentials: 'same-origin',
        headers: {'Content-Type': 'application/json', 'X-CSRFToken': await csrf()},
        body: JSON.stringify({pickup: selectedPickup, destination: selectedDestination})
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Unable to calculate route');
      // Discard results if a location or label was changed while requesting.
      if (coords.pickup?.lat !== selectedPickup.lat || coords.pickup?.lon !== selectedPickup.lon ||
          coords.dropoff?.lat !== selectedDestination.lat || coords.dropoff?.lon !== selectedDestination.lon ||
          pickup.value.trim() !== startPickupLabel || dropoff.value.trim() !== startDestinationLabel) {
        error.textContent = 'Locations changed. Tap Continue again.';
        return;
      }
      sessionStorage.setItem('movego_verified_route', JSON.stringify({
        ...data, pickup: selectedPickup, destination: selectedDestination
      }));
      routeInfo.textContent = `Driving route: ${data.distance_km} km, approximately ${data.duration_min} min. Fare not available yet.`;
      document.getElementById('review-pickup').textContent = a;
      document.getElementById('review-dropoff').textContent = b;
      document.getElementById('review-service').textContent = selectedService;
      review.hidden = false;
      review.scrollIntoView({behavior: 'smooth', block: 'start'});
    } catch (e) {
      error.textContent = e.message || 'Unable to calculate route.';
    } finally {
      if (continueButton) {
        continueButton.disabled = false;
        continueButton.innerHTML = continueOriginal;
      }
    }
  });

  document.getElementById('see-options')?.addEventListener('click', event => {
    const raw = sessionStorage.getItem('movego_verified_route');
    if (!raw) {
      event.preventDefault();
      error.textContent = 'Please select both live locations and tap Continue first.';
      return;
    }
    sessionStorage.setItem('movego_trip_draft', JSON.stringify({
      pickup: pickup.value.trim(),
      destination: dropoff.value.trim(),
      service: sessionStorage.getItem('movego_ride_service') || 'Ride'
    }));
  });
})();
