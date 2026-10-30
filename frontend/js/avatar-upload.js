(()=>{'use strict';
const root=document.getElementById('movego-avatar-panel'),avatar=document.getElementById('avatar');
if(!root||!avatar)return;
const file=root.querySelector('#movego-avatar-file'),pick=root.querySelector('#movego-avatar-pick'),remove=root.querySelector('#movego-avatar-remove'),status=root.querySelector('#movego-avatar-status');
const URL='/api/auth/avatar/';
let imageUrl=null;
function clear(){if(imageUrl){URLRevoke(imageUrl);imageUrl=null;} avatar.replaceChildren(document.createTextNode((document.getElementById('first-name')?.value||'M').charAt(0).toUpperCase()));remove.hidden=true;}
function URLRevoke(url){window.URL.revokeObjectURL(url)}
async function csrf(){const res=await fetch('/api/auth/csrf/',{credentials:'same-origin'});if(!res.ok)throw Error('Could not obtain security token');const obj=await res.json();return obj.csrfToken;}
async function refresh(){const res=await fetch(URL,{credentials:'same-origin',cache:'no-store'});if(res.status===404){clear();return;}if(res.status===401){status.textContent='Sign in to add a photo.';pick.disabled=true;remove.hidden=true;return;}if(!res.ok)throw Error('Unable to load profile photo');const blob=await res.blob();if(imageUrl)URLRevoke(imageUrl);imageUrl=window.URL.createObjectURL(blob);const img=document.createElement('img');img.alt='Your profile picture';img.src=imageUrl;avatar.replaceChildren(img);remove.hidden=false;}
pick.addEventListener('click',()=>file.click());
file.addEventListener('change',async()=>{const photo=file.files?.[0];if(!photo)return;if(photo.size>5*1024*1024){status.textContent='Photo must be under 5 MB.';file.value='';return;}pick.disabled=true;status.textContent='Uploading photo…';try{const form=new FormData();form.append('photo',photo);const res=await fetch(URL,{method:'POST',credentials:'same-origin',headers:{'X-CSRFToken':await csrf()},body:form});const data=await res.json().catch(()=>({}));if(!res.ok)throw Error(data.error||'Upload failed');await refresh();status.textContent='Profile picture updated.';}catch(e){status.textContent=e.message||'Upload failed';}finally{pick.disabled=false;file.value='';}});
remove.addEventListener('click',async()=>{remove.disabled=true;status.textContent='Removing photo…';try{const res=await fetch(URL,{method:'DELETE',credentials:'same-origin',headers:{'X-CSRFToken':await csrf()}});if(!res.ok)throw Error('Could not remove photo');clear();status.textContent='Profile picture removed.';}catch(e){status.textContent=e.message||'Unable to remove photo';}finally{remove.disabled=false;}});
refresh().catch(e=>{status.textContent=e.message||'Photo unavailable';});
})();
