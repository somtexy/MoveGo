"use strict";
const feedback = document.getElementById("feedback");
const buttons = document.querySelectorAll("[data-role]");
let account = null;
let ready = false;
buttons.forEach(button => button.disabled = true);
(async () => {
  try {
    const response = await fetch("/api/auth/profile/", { credentials: "same-origin", cache: "no-store" });
    if (response.status === 401) { location.replace("phone.html"); return; }
    if (!response.ok) throw new Error("Unable to check your account. Please retry.");
    account = (await response.json()).profile;
    if (!account?.phone_verified) { location.replace("phone.html"); return; }
    if (account.role === "driver") { location.replace("../driver/home.html"); return; }
    if (account.role !== "passenger") { feedback.textContent = "This account isn't eligible for onboarding."; return; }
    ready = true;
    buttons.forEach(button => button.disabled = false);
    feedback.textContent = "Choose Passenger or apply to drive with MoveGo.";
  } catch (error) { feedback.textContent = error.message || "Django is unavailable. Refresh to retry."; }
})();
buttons.forEach(button => button.addEventListener("click", () => {
  if (!ready) return;
  if (button.dataset.role === "driver") {
    sessionStorage.setItem("movego_selected_role", "driver");
    location.assign("../driver/setup.html");
    return;
  }
  sessionStorage.setItem("movego_selected_role", "passenger");
  if (account?.first_name?.trim()) location.assign("home.html");
  else location.assign("profile.html");
}));
