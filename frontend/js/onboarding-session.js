"use strict";
// Redirect returning verified passengers only; fail open to the welcome screen when API is unreachable.
(async () => {
  try {
    const response = await fetch("/api/auth/profile/", { credentials: "same-origin", cache: "no-store" });
    if (!response.ok) return;
    const { profile } = await response.json();
    if (!profile?.phone_verified || profile.role !== "passenger") return;
    location.replace(profile.first_name?.trim() ? "home.html" : "profile.html");
  } catch (_) { /* Let visitor use welcome screen if backend is offline. */ }
})();
