/* Record only explicit booking progression, not unverified typed searches. */
(() => {
'use strict';
const KEY='movego_recent_destinations_v1';
const btn=document.getElementById('see-options');
if(!btn)return;
btn.addEventListener('click',()=>{
  const drop=document.getElementById('dropoff');
  const review=document.getElementById('review');
  const address=typeof drop?.value==='string'?drop.value.trim().slice(0,180):'';
  if(!address || review?.hidden)return;
  try {
    const old=JSON.parse(localStorage.getItem(KEY)||'[]');
    const items=Array.isArray(old)?old.filter(x=>typeof x==='string'):[];
    localStorage.setItem(KEY,JSON.stringify([address,...items.filter(x=>x.toLocaleLowerCase()!==address.toLocaleLowerCase())].slice(0,8)));
  } catch {}
});
})();
