(()=>{'use strict';
const $=id=>document.getElementById(id), recovery=$('pin-recovery');if(!recovery)return;
const feedback=$('feedback');const say=s=>{feedback.textContent=s};
async function post(path,payload){const csrf=await fetch('/api/auth/csrf/',{credentials:'same-origin'});if(!csrf.ok)throw Error('Could not load security token');const json=await csrf.json();const r=await fetch('/api/auth/pin/recovery/'+path+'/',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-CSRFToken':json.csrfToken},body:JSON.stringify(payload||{})});const b=await r.json();if(!r.ok)throw Error(b.error||'Request failed');return b}
function phase(n){$('pin-recovery-request').hidden=n!==0;$('pin-recovery-check').hidden=n!==1;$('pin-recovery-reset').hidden=n!==2;}
$('pin-forgot').addEventListener('click',()=>{recovery.hidden=false;phase(0);say('A fresh SMS code will be sent to your verified phone number.')});
$('pin-recovery-cancel').addEventListener('click',()=>{recovery.hidden=true;say('')});
async function submit(ev,action,payload,success,next){ev.preventDefault();const b=ev.currentTarget.querySelector('[type=submit]');b.disabled=true;say('Processing…');try{await post(action,payload());say(success);if(next!==null)phase(next);ev.currentTarget.reset()}catch(err){say(err.message)}finally{b.disabled=false}}
$('pin-recovery-request').addEventListener('submit',e=>submit(e,'request',()=>({}),'Recovery SMS requested.',1));
$('pin-recovery-check').addEventListener('submit',e=>submit(e,'confirm',()=>({code:$('pin-recovery-code').value}),'SMS verified. Set a new PIN.',2));
$('pin-recovery-reset').addEventListener('submit',e=>submit(e,'reset',()=>({pin:$('pin-recovery-new').value,confirm:$('pin-recovery-confirm').value}),'PIN reset successfully.',null).then(()=>{if(feedback.textContent==='PIN reset successfully.'){recovery.hidden=true;window.location.reload()}}));
})();
