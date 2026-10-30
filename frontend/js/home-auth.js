"use strict";
// UI-level guard only. Django API endpoints must enforce their own authentication and role checks.
(async () => {
  const block = document.getElementById("auth-gate");
  const reveal = () => { block.remove(); document.body.classList.remove("movego-auth-pending"); };
  try {
    const response = await fetch("/api/auth/profile/", { credentials: "same-origin", cache: "no-store" });
    if (response.status === 401) { location.replace("phone.html"); return; }
    if (!response.ok) throw new Error("Could not check your login session.");
    const { profile } = await response.json();
    if (!profile?.phone_verified || profile.role !== "passenger") { location.replace("role.html"); return; }
    if (!profile.first_name?.trim()) { location.replace("profile.html"); return; }
    sessionStorage.setItem("movego_first_name", profile.first_name);
    const displayName = [profile.first_name, profile.last_name].filter(Boolean).join(" ");
    document.getElementById("drawer-name").textContent = displayName;
    document.getElementById("drawer-avatar").textContent = profile.first_name[0].toUpperCase();
    reveal();
  } catch (e) {
    const message = block.querySelector("[data-auth-message]");
    message.textContent = e.message || "Connection unavailable. Please retry.";
    block.querySelector("button").hidden = false;
  }
})();
