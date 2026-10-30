"use strict";
const $ = id => document.getElementById(id);
let trip = null; try { trip = JSON.parse(sessionStorage.getItem('movego_ride_option_draft') || 'null'); } catch (_) {}
const allowed = ['Ride', 'Comfort', 'One Click', 'Couriers'];
const valid = trip && typeof trip.pickup === 'string' && trip.pickup.trim().length >= 3 && typeof trip.destination === 'string' && trip.destination.trim().length >= 3 && allowed.includes(trip.option) && sessionStorage.getItem('movego_search_preview') === 'active';
if (!valid) { location.replace('confirm-ride.html'); }
else {
  $('pickup').textContent = trip.pickup.slice(0,120);
  $('destination').textContent = trip.destination.slice(0,120);
  $('service').textContent = trip.option;
  $('payment').textContent = sessionStorage.getItem('movego_payment_method') === 'cash' ? 'Cash (demo)' : 'Online (demo, no charge)';
  const stages = [
    ['Driver assigned', 'Sample driver details are displayed. No real match occurred.'],
    ['Driver arriving', 'Preview of the driver travelling toward pickup.'],
    ['Driver arrived', 'Preview of the driver waiting at pickup.'],
    ['Trip started', 'Preview of an active journey. This is not live tracking.'],
    ['Trip completed', 'Simulation finished. No booking or payment was made.']
  ];
  let index = 0;
  function render() {
    $('stage-title').textContent = stages[index][0]; $('stage-description').textContent = stages[index][1];
    $('progress-track').style.setProperty('--pct', `${index * 25}%`);
    $('progress-steps').replaceChildren();
    for (let i = 0; i < stages.length; i++) {
      const item = document.createElement('div'); item.className = 'progress-step' + (i <= index ? ' done' : '') + (i === index ? ' current' : '');
      const dot = document.createElement('span'); dot.className='dot'; dot.textContent = i < index ? '✓' : String(i+1);
      const label = document.createElement('span'); label.textContent=stages[i][0];
      item.append(dot,label); $('progress-steps').append(item);
    }
    $('next-stage').disabled = index === stages.length - 1;
    $('next-stage').textContent = index === stages.length - 1 ? 'View demo receipt & rating →' : 'Next demo stage →';
    $('next-stage').disabled = false;
  }
  $('next-stage').addEventListener('click', () => { if(index < stages.length-1) { index++; render(); } else { location.href = 'trip-complete.html'; }});
  $('reset-stage').addEventListener('click', () => { index=0; render(); });
  render();
}
