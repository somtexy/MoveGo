"use strict";
const form = document.getElementById("profile-form");
const input = document.getElementById("first-name");
const error = document.getElementById("name-error");
const notice = document.getElementById("notice");
const submit = document.getElementById("next-btn");
let existing = null;
submit.disabled = true;
async function profileRequest() {
  const response = await fetch("/api/auth/profile/", { credentials: "same-origin", cache: "no-store" });
  if (response.status === 401) { location.replace("phone.html"); return null; }
  if (!response.ok) throw new Error("Cannot load your Django profile. Please refresh.");
  const { profile } = await response.json();
  if (!profile?.phone_verified || profile.role !== "passenger") throw new Error("A verified passenger account is required.");
  return profile;
}
(async () => {
  try {
    existing = await profileRequest();
    if (!existing) return;
    if (existing.first_name?.trim()) { location.replace("home.html"); return; }
    submit.disabled = false;
    input.focus();
  } catch (e) { error.textContent = e.message || "Could not access your account."; }
})();
form.addEventListener("submit", async (event) => {
  event.preventDefault();
  error.textContent = "";
  const name = input.value.trim().replace(/\s+/g, " ");
  if (name.length < 2 || name.length > 50 || !/^[\p{L}][\p{L}\p{M} .'-]*$/u.test(name)) {
    error.textContent = "Enter a valid first name (2–50 characters).";
    input.focus(); return;
  }
  if (!existing) { error.textContent = "Sign in before saving your name."; return; }
  submit.disabled = true;
  notice.textContent = "Saving to your account…";
  try {
    const csrf = await fetch("/api/auth/csrf/", { credentials: "same-origin" });
    if (!csrf.ok) throw new Error("Could not obtain a security token.");
    const token = (await csrf.json()).csrfToken;
    if (!token) throw new Error("Missing CSRF token. Refresh the page.");
    const response = await fetch("/api/auth/profile/", {
      method: "PATCH", credentials: "same-origin",
      headers: { "Content-Type": "application/json", "X-CSRFToken": token },
      body: JSON.stringify({ first_name: name, last_name: existing.last_name || "", email: existing.email || "" })
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(body.error || `Unable to save your name (${response.status}).`);
    sessionStorage.setItem("movego_first_name", body.profile.first_name);
    location.replace("home.html");
  } catch (e) {
    notice.textContent = "";
    error.textContent = e.message || "Unable to save name.";
    submit.disabled = false;
  }
});
