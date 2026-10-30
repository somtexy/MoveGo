"use strict";
(() => {
  const inputs = [...document.querySelectorAll(".digit")];
  const feedback = document.getElementById("verify-message");
  const button = document.getElementById("verify-btn");
  const resend = document.getElementById("resend");
  const countdown = document.getElementById("countdown");
  const phone = sessionStorage.getItem("movego_phone");
  document.getElementById("phone-display").textContent=phone || "your phone number";
  if (!phone) feedback.textContent="Return to the previous screen to request a code.";
  async function post(url, payload) {
    const csrf = await fetch("/api/auth/csrf/",{credentials:"same-origin"});
    if (!csrf.ok) throw Error("Could not connect to Django. Please refresh.");
    const token = (await csrf.json()).csrfToken;
    if (!token) throw Error("CSRF token missing. Reload and try again.");
    const response = await fetch(url,{
      method:"POST",credentials:"same-origin",
      headers:{"Content-Type":"application/json","Accept":"application/json","X-CSRFToken":token},
      body:JSON.stringify(payload)
    });
    const data = await response.json().catch(()=>({}));
    if (!response.ok) throw Error(data.error || data.message || `Request failed (${response.status}).`);
    return data;
  }
  let pending=false;
  function update(){button.disabled=pending || !phone || !inputs.every(i=>/^\d$/.test(i.value));}
  function pasteFrom(index,text){
    const numbers=text.replace(/\D/g,"").slice(0,inputs.length-index);
    for(let i=0;i<numbers.length;i++)inputs[index+i].value=numbers[i];
    inputs[Math.min(index+numbers.length,inputs.length-1)].focus();
    feedback.textContent="";update();
  }
  inputs.forEach((input,index)=>{
    input.addEventListener("input",()=>{const raw=input.value;input.value="";pasteFrom(index,raw);});
    input.addEventListener("paste",e=>{e.preventDefault();pasteFrom(index,e.clipboardData.getData("text"));});
    input.addEventListener("keydown",e=>{
      if(e.key==="Backspace"){if(input.value){input.value="";}else if(index>0){inputs[index-1].value="";inputs[index-1].focus();}update();}
      if(e.key==="ArrowLeft" && index>0){e.preventDefault();inputs[index-1].focus();}
      if(e.key==="ArrowRight" && index<inputs.length-1){e.preventDefault();inputs[index+1].focus();}
    });
  });
  document.getElementById("verify-form").addEventListener("submit",async e=>{
    e.preventDefault();if(!phone || pending)return;
    const code=inputs.map(i=>i.value).join("");if(!/^\d{6}$/.test(code)){feedback.textContent="Enter all six digits.";return;}
    pending=true;update();feedback.textContent="Verifying your code…";
    try{
      const result=await post("/api/auth/phone/twilio/check/",{phone,code});
      if(!result.phone_verified)throw Error("Verification was not confirmed. Please try again.");
      const session=await fetch("/api/auth/me/",{credentials:"same-origin",headers:{Accept:"application/json"}});
      if(!session.ok)throw Error("Code approved, but your login session could not be confirmed. Please reload.");
      sessionStorage.removeItem("movego_otp_requested_at");
      sessionStorage.removeItem("movego_otp_cooldown");
      // Existing Google identity remains signed in; advance through onboarding.
      window.location.assign(result.next_url || "./role.html");
    }catch(err){feedback.textContent=err.message || "Verification failed. Please try again.";}
    finally{pending=false;update();}
  });
  function remain(){
    const sent=Number(sessionStorage.getItem("movego_otp_requested_at") || 0);
    const cooldown=Number(sessionStorage.getItem("movego_otp_cooldown") || 60);
    return Math.max(0,Math.ceil((sent+cooldown*1000-Date.now())/1000));
  }
  function tick(){const seconds=remain();countdown.textContent=seconds?`${String(Math.floor(seconds/60)).padStart(2,"0")}:${String(seconds%60).padStart(2,"0")}`:"";resend.disabled=pending || !phone || seconds>0;}
  setInterval(tick,1000);tick();
  resend.addEventListener("click",async()=>{
    if(!phone || pending || remain()>0)return;
    pending=true;update();resend.disabled=true;feedback.textContent="Requesting another SMS…";
    try{
      const result=await post("/api/auth/phone/twilio/request/",{phone});
      sessionStorage.setItem("movego_otp_requested_at",String(Date.now()));
      sessionStorage.setItem("movego_otp_cooldown",String(result.resend_after_seconds||60));
      inputs.forEach(i=>i.value="");inputs[0].focus();
      feedback.textContent="A new code has been requested by SMS.";
    }catch(err){feedback.textContent=err.message || "Could not resend SMS.";}
    finally{pending=false;update();tick();}
  });
  update();if(phone)inputs[0].focus();
})();
