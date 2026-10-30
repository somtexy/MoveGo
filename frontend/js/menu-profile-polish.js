/* Display the private, authenticated avatar inside the existing MoveGo menu. */
(()=>{'use strict';
 const node=document.getElementById('drawer-avatar');
 if(!node)return;
 let objectURL=null,seq=0;
 async function updateAvatar(){
   const request=++seq;
   try{
     const r=await fetch('/api/auth/avatar/',{credentials:'same-origin',cache:'no-store'});
     if(request!==seq)return;
     if(!r.ok){restoreInitial();return;}
     const blob=await r.blob();
     if(request!==seq)return;
     if(!blob.type.startsWith('image/'))return;
     const next=URL.createObjectURL(blob);
     const img=document.createElement('img');img.alt='Your MoveGo profile picture';
     img.onload=()=>{if(objectURL)URL.revokeObjectURL(objectURL);objectURL=next;};
     img.onerror=()=>{URL.revokeObjectURL(next);restoreInitial();};
     img.src=next;
     node.replaceChildren(img);
   }catch(err){/* Keep the initial-letter fallback when offline. */}
 }
 function restoreInitial(){
   if(objectURL){URL.revokeObjectURL(objectURL);objectURL=null;}
   if(node.querySelector('img')){
      const name=(document.getElementById('drawer-name')?.textContent||'MoveGo').trim();
      node.textContent=(name[0]||'M').toUpperCase();
   }
 }
 // Refresh on menu open, ensuring recent photo changes appear without a reload.
 document.getElementById('menu-btn')?.addEventListener('click',()=>{updateAvatar();});
 // The authentication guard sets the initial before or after this request.
 document.addEventListener('visibilitychange',()=>{if(!document.hidden)updateAvatar();});
 window.addEventListener('pageshow',()=>{
   if(!document.body.classList.contains('movego-auth-pending'))updateAvatar();
   else {
     const observer=new MutationObserver(()=>{
       if(!document.body.classList.contains('movego-auth-pending')){
         observer.disconnect();updateAvatar();
       }
     });
     observer.observe(document.body,{attributes:true,attributeFilter:['class']});
   }
 });
})();
