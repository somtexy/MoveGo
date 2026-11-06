"use strict";
/* Returning users are routed by the authenticated Django session, NEVER localStorage. */
(async function routeReturningUser() {
  // Only welcome/sign-in entry screens use this; other pages keep their own guards.
  try {
    const response = await fetch('/api/auth/me/', { credentials: 'same-origin', cache: 'no-store', redirect: 'error' });
    if (response.status === 401 || !response.ok) return;
    const user = (await response.json()).user;
    if (!user) return;
    const role = user.role;
    if (role === 'driver') {
      location.replace('/app/driver/home.html');
      return;
    }
    if (role !== 'passenger' || !user.phone_verified) return;
    // The profile endpoint determines if onboarding is finished, not browser storage.
    const profileResponse = await fetch('/api/auth/profile/', { credentials: 'same-origin', cache: 'no-store' });
    if (!profileResponse.ok) return;
    const profile = (await profileResponse.json()).profile;
    if (profile?.role !== 'passenger' || !profile.phone_verified) return;
    location.replace(profile.first_name?.trim() ? '/app/passenger/home.html' : '/app/passenger/profile.html');
  } catch (_) {
    // If offline, don't redirect on stale localStorage assumptions.
  }
})();
