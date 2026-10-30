"use strict";
(() => {
  const el = id => document.getElementById(id);
  let draft = null;
  try { draft = JSON.parse(sessionStorage.getItem("movego_ride_option_draft") || "null"); } catch {}
  const valid = draft && typeof draft.pickup === "string" && typeof draft.destination === "string" && ["Ride","Comfort","One Click","Couriers"].includes(draft.option) && Number.isSafeInteger(draft.estimated_fare_kobo);
  const message = el("message"), save = el("save");
  if (valid) {
    el("pickup").textContent = draft.pickup;
    el("destination").textContent = draft.destination;
    el("service").textContent = draft.option;
    el("fare").textContent = new Intl.NumberFormat("en-NG",{style:"currency",currency:"NGN",maximumFractionDigits:0}).format(draft.estimated_fare_kobo/100) + " (starter estimate)";
  } else {
    message.textContent = "Select real locations and a calculated fare first.";
  }
  document.querySelectorAll('input[name="payment"]').forEach(input => {
    if (input.value !== "cash") { input.disabled = true; input.checked = false; }
    input.addEventListener("change", update);
  });
  function update() {
    const selected = document.querySelector('input[name="payment"]:checked');
    document.querySelectorAll(".method").forEach(c => c.classList.toggle("selected", !!c.querySelector("input:checked")));
    save.disabled = !valid || !selected || selected.value !== "cash";
    if (valid) message.textContent = "Cash selection only. No payment has been collected.";
  }
  const cash = document.querySelector('input[name="payment"][value="cash"]');
  if (cash) cash.checked = true;
  update();
  save.addEventListener("click", () => {
    if (!valid || !cash?.checked) return;
    sessionStorage.setItem("movego_payment_method", "cash");
    window.location.href = "confirm-ride.html";
  });
})();
