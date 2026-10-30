"use strict";
(() => {
  const form = document.getElementById("phone-form");
  const input = document.getElementById("phone");
  const field = document.getElementById("number-field");
  const feedback = document.getElementById("phone-help");
  const submit = document.getElementById("next");
  const API = "/api/auth/phone/twilio/request/";
  const csrfUrl = "/api/auth/csrf/";
  const showError = message => {
    feedback.textContent = message;
    field.classList.add("invalid");
    input.setAttribute("aria-invalid", "true");
  };
  input.addEventListener("input", () => { feedback.textContent=""; field.classList.remove("invalid");input.removeAttribute("aria-invalid"); });
  async function send(url, payload) {
    const csrf = await fetch(csrfUrl, {credentials:"same-origin"});
    if (!csrf.ok) throw Error("Unable to start verification. Reload and try again.");
    const token = (await csrf.json()).csrfToken;
    if (!token) throw Error("CSRF token missing. Reload and try again.");
    const response = await fetch(url, {
      method:"POST",credentials:"same-origin",
      headers:{"Content-Type":"application/json","Accept":"application/json","X-CSRFToken":token},
      body:JSON.stringify(payload)
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw Error(data.error || data.message || `Could not send SMS (${response.status}).`);
    return data;
  }
  form.addEventListener("submit", async event => {
    event.preventDefault();
    const raw = input.value.trim().replace(/[\s().-]/g, "");
    let number=raw.replace(/^\+234/, "").replace(/^234/, "").replace(/^0/, "");
    if (!/^[789]\d{9}$/.test(number)) { showError("Enter a valid Nigerian mobile number (e.g. 08012345678)."); return; }
    const phone = "+234" + number;
    submit.disabled = true; submit.textContent = "Sending SMS…"; feedback.textContent = "Requesting a verification code…";
    try {
      const result = await send(API, {phone});
      sessionStorage.setItem("movego_phone",phone);
      sessionStorage.setItem("movego_otp_requested_at",String(Date.now()));
      sessionStorage.setItem("movego_otp_cooldown",String(result.resend_after_seconds || 60));
      window.location.assign("./verify.html");
    } catch (err) {
      showError(err.message || "SMS could not be sent. Try again.");
    } finally { submit.disabled=false;submit.innerHTML='Next <span aria-hidden="true" class="arrow">→</span>'; }
  });
})();
