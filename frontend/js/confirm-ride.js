"use strict";
(() => {
  const el = (id) => document.getElementById(id);
  const parse = (key) => { try { return JSON.parse(sessionStorage.getItem(key) || "null"); } catch { return null; } };
  const ride = parse("movego_ride_option_draft");
  const route = parse("movego_verified_route");
  const method = sessionStorage.getItem("movego_payment_method");
  const validPoint = (p) => p && Number.isFinite(p.lat) && Number.isFinite(p.lon);
  const valid = ride && route && validPoint(route.pickup) && validPoint(route.destination) &&
    typeof ride.pickup === "string" && typeof ride.destination === "string" &&
    ["Ride", "Comfort", "One Click", "Couriers"].includes(ride.option) && method === "cash";
  const button = el("continue");
  button.textContent = "Save ride request";
  const message = el("message");
  if (!valid) {
    message.textContent = "Select real locations, a ride category, and cash payment before continuing.";
    button.disabled = true;
    return;
  }
  el("pickup").textContent = ride.pickup.slice(0, 255);
  el("destination").textContent = ride.destination.slice(0, 255);
  el("service").textContent = ride.option;
  el("payment").textContent = "Cash (not collected)";
  el("fare").textContent = new Intl.NumberFormat("en-NG", {style:"currency",currency:"NGN",maximumFractionDigits:0}).format((ride.estimated_fare_kobo || 0) / 100) + " · starter estimate";
  button.disabled = false;
  button.addEventListener("click", async () => {
    button.disabled = true;
    button.textContent = "Saving request…";
    message.textContent = "";
    try {
      const csrfRes = await fetch("/api/auth/csrf/", {credentials:"same-origin"});
      if (!csrfRes.ok) throw new Error("Could not get security token.");
      const token = (await csrfRes.json()).csrfToken;
      const response = await fetch("/api/ride-requests/", {
        method:"POST", credentials:"same-origin",
        headers:{"Content-Type":"application/json", "X-CSRFToken":token},
        body:JSON.stringify({
          pickup:{label:ride.pickup, ...route.pickup},
          destination:{label:ride.destination, ...route.destination},
          category:ride.option, payment_method:method
        })
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || `Request failed (${response.status}).`);
      message.textContent = `Request #${result.ride_id} saved. No driver search or assignment is active yet. This is not a confirmed booking.`;
      button.textContent = "Request saved";
      sessionStorage.removeItem("movego_search_preview");
    } catch (error) {
      message.textContent = error.message;
      button.disabled = false;
      button.textContent = "Try saving again";
    }
  });
})();
