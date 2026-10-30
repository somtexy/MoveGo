"use strict";
const el = id => document.getElementById(id);
const THEME_KEY = "movego_app_theme";
const FIRST_KEY = "movego_first_name";
let signedIn = false;

function showName() {
  const first = el("first-name").value.trim();
  const last = el("last-name").value.trim();
  el("display-name").textContent = [first, last].filter(Boolean).join(" ") || "MoveGo rider";
  el("avatar").textContent = (first || "M").slice(0,1).toUpperCase();
}
function theme() {
  const dark = localStorage.getItem(THEME_KEY) === "dark";
  document.documentElement.dataset.theme = dark ? "dark" : "light";
  el("theme-toggle").setAttribute("aria-checked", String(dark));
  document.querySelector('meta[name="theme-color"]').content = dark ? "#17231d" : "#fffdf8";
}
el("theme-toggle").addEventListener("click", () => {
  localStorage.setItem(THEME_KEY, document.documentElement.dataset.theme === "dark" ? "light" : "dark");
  theme();
});
theme();

async function loadProfile() {
  const message = el("session-message");
  try {
    const result = await fetch("/api/auth/profile/", { credentials:"same-origin", cache:"no-store" });
    if (result.status === 401) {
      message.textContent = "You are not signed in. Verify your phone number to edit your profile.";
      el("account-form").querySelector('button[type="submit"]').disabled = true;
      return;
    }
    if (!result.ok) throw new Error("Could not load profile.");
    const {profile} = await result.json();
    signedIn = true;
    el("first-name").value = profile.first_name || "";
    el("last-name").value = profile.last_name || "";
    el("email").value = profile.email || "";
    showName();
    message.textContent = profile.phone_verified ? `Signed in · Verified phone ${profile.phone}` : "Signed in to MoveGo";
    el("session-logout").hidden = false;
  } catch (error) { message.textContent = error.message || "MoveGo is temporarily unavailable"; }
}

el("account-form").addEventListener("submit", async event => {
  event.preventDefault();
  el("error").textContent = "";
  el("notice").textContent = "";
  if (!signedIn) { el("error").textContent = "Sign in before saving your profile."; return; }
  const button = el("account-form").querySelector('button[type="submit"]');
  const data = {
    first_name:el("first-name").value.trim().replace(/\s+/g," "),
    last_name:el("last-name").value.trim().replace(/\s+/g," "),
    email:el("email").value.trim()
  };
  button.disabled = true;
  try {
    const token = await window.MoveGoAPI.csrfToken();
    const response = await fetch("/api/auth/profile/", {
      method:"PATCH", credentials:"same-origin",
      headers:{"Content-Type":"application/json", "X-CSRFToken":token},
      body:JSON.stringify(data)
    });
    const body = await response.json().catch(()=>({}));
    if (!response.ok) throw new Error(body.error || `Save failed (${response.status})`);
    el("first-name").value=body.profile.first_name;
    el("last-name").value=body.profile.last_name;
    el("email").value=body.profile.email;
    sessionStorage.setItem(FIRST_KEY,body.profile.first_name);
    showName();
    el("notice").textContent = "Profile saved successfully.";
  } catch(error) {el("error").textContent = error.message || "Could not save profile";}
  finally {button.disabled=false;}
});

el("session-logout").addEventListener("click", async()=>{
  const button=el("session-logout");button.disabled=true;
  try {
    await window.MoveGoAPI.logout();
    signedIn=false;
    button.hidden=true;
    el("account-form").querySelector('button[type="submit"]').disabled=true;
    el("session-message").textContent="Logged out of MoveGo.";
    el("notice").textContent="";
  } catch(error) {el("error").textContent=error.message||"Could not sign out";button.disabled=false;}
});
loadProfile();
