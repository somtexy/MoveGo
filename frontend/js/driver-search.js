"use strict";
const e=id=>document.getElementById(id);
let trip=null;try{trip=JSON.parse(sessionStorage.getItem('movego_ride_option_draft')||'null')}catch{}
const valid=trip&&typeof trip.pickup==='string'&&typeof trip.destination==='string'&&typeof trip.option==='string'&&sessionStorage.getItem('movego_search_preview')==='active';
if(!valid){location.replace('confirm-ride.html')}else{e('pickup').textContent=trip.pickup.slice(0,120);e('destination').textContent=trip.destination.slice(0,120);e('service').textContent=trip.option;}
let paused=false;e('toggle-animation').addEventListener('click',()=>{paused=!paused;document.querySelector('.search-visual').classList.toggle('paused',paused);e('toggle-animation').textContent=paused?'Resume preview':'Pause preview';e('search-status').textContent=paused?'Animation paused. No live search is running.':'This animation is a UI preview. No drivers are being contacted.'});
