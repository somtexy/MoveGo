"use strict";
(() => {
  const $ = id => document.getElementById(id);
  const categories = [
    {name:"Ride", desc:"Everyday affordable trips", icon:"car-front"},
    {name:"Comfort", desc:"Extra space and comfort", icon:"car"},
    {name:"One Click", desc:"Simple express option", icon:"zap"},
    {name:"Couriers", desc:"Deliver a parcel", icon:"package"}
  ];
  const format = new Intl.NumberFormat("en-NG", {style:"currency", currency:"NGN", maximumFractionDigits:0});
  let draft, route;
  try {
    draft = JSON.parse(sessionStorage.getItem("movego_trip_draft") || "null");
    route = JSON.parse(sessionStorage.getItem("movego_verified_route") || "null");
  } catch (_) {}
  const validPoint = p => p && typeof p.lat === "number" && typeof p.lon === "number" && Number.isFinite(p.lat) && Number.isFinite(p.lon);
  const valid = draft && typeof draft.pickup === "string" && typeof draft.destination === "string" && validPoint(route?.pickup) && validPoint(route?.destination);
  if (!valid) { $("notice").textContent = "Choose real pickup and destination locations, then tap Continue to calculate a route."; return; }
  $("pickup").textContent = draft.pickup.slice(0,120);
  $("dropoff").textContent = draft.destination.slice(0,120);
  const root = $("options");
  const chosen = document.createElement("strong");
  let quotes = [], selected = null;
  function display(name) {
    const quote = quotes.find(q => q.category === name);
    if (!quote) return;
    selected = name;
    root.querySelectorAll("button").forEach(b => {
      const active = b.dataset.option === name;
      b.classList.toggle("active", active);
      b.setAttribute("aria-pressed", String(active));
    });
    $("fare").textContent = format.format(quote.estimated_fare_kobo / 100) + " (starter estimate)";
    $("notice").textContent = "Calculated by Django using a live driving route and illustrative starter tariffs. Booking is not enabled.";
    sessionStorage.setItem("movego_ride_option_draft", JSON.stringify({
      ...draft, option: name, estimated_fare_kobo: quote.estimated_fare_kobo,
      pricing_status: "starter_tariffs_not_live"
    }));
  }
  async function loadQuotes() {
    $("notice").textContent = "Calculating fares from the live route…";
    try {
      const csrfResponse = await fetch("/api/auth/csrf/", {credentials:"same-origin"});
      if (!csrfResponse.ok) throw new Error("Could not load security token");
      const token = (await csrfResponse.json()).csrfToken;
      const response = await fetch("/api/fares/quotes/", {
        method:"POST", credentials:"same-origin",
        headers:{"Content-Type":"application/json", "X-CSRFToken":token},
        body:JSON.stringify({pickup:route.pickup, destination:route.destination})
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Fare estimation failed");
      quotes = data.quotes || [];
      if (!quotes.length) throw new Error("No fares available");
      $("duration").textContent = `${data.duration_min} min (live route)`;
      const detail = document.querySelector(".details .detail strong");
      if (detail) detail.textContent = `${data.distance_km} km (live route)`;
      root.replaceChildren();
      for (const item of categories) {
        const quote = quotes.find(q => q.category === item.name);
        if (!quote) continue;
        const btn = document.createElement("button");
        btn.type="button"; btn.className="option"; btn.dataset.option=item.name;
        btn.setAttribute("aria-pressed","false");
        const icon = document.createElement("span"); icon.className="vehicle";
        // Modern outline icons via CSS-free inline SVG; no emojis.
        icon.innerHTML = item.icon === "package" ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="m12 3 9 5-9 5-9-5 9-5Zm-9 5v10l9 5 9-5V8M12 13v10"/></svg>' : item.icon === "zap" ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="m13 2-9 12h7l-1 8 10-12h-7l0-8Z"/></svg>' : '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="m5 11 2-5h10l2 5M4 16v3h3v-2h10v2h3v-8H4v8M7 14h.01M17 14h.01" stroke-linecap="round" stroke-linejoin="round"/></svg>';
        icon.querySelector("svg").style.cssText="width:25px;height:25px";
        const middle=document.createElement("span"); middle.className="option-body";
        const title=document.createElement("strong"); title.textContent=item.name;
        const desc=document.createElement("span"); desc.textContent=item.desc;
        middle.append(title,desc);
        const price=document.createElement("span"); price.className="price";
        const amount=document.createElement("strong"); amount.textContent=format.format(quote.estimated_fare_kobo/100);
        const note=document.createElement("small"); note.textContent="Starter estimate";
        price.append(amount,note); btn.append(icon,middle,price);
        btn.addEventListener("click",()=>display(item.name)); root.append(btn);
      }
      display(quotes.some(q=>q.category===draft.service)?draft.service:"Ride");
      const request = $("request");
      request.disabled = false;
      request.textContent = "Continue to payment method";
      request.addEventListener("click", () => {
        if (!selected) return;
        sessionStorage.removeItem("movego_payment_method");
        window.location.href = "payment.html";
      });
    } catch (err) {
      $("notice").textContent = err.message + ". Return to destination selection and try again.";
      $("fare").textContent = "—";
    }
  }
  loadQuotes();
})();
