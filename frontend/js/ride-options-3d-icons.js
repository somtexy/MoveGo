"use strict";
/* Step 42 UI repair: icon presentation only. Fare/selection logic stays in ride-options.js. */
(() => {
  const images = {"Ride":"ride.webp", "Comfort":"comfort.webp", "One Click":"inhurry.webp", "Couriers":"couriers.webp"};
  const prefix = "/app/assets/icons/ride-categories/";
  let scheduled = false;
  let updating = false;
  function update() {
    scheduled = false;
    const root = document.getElementById("options");
    if (!root || updating) return;
    updating = true;
    try {
      const buttons = Array.from(root.querySelectorAll("button.option[data-option]"));
      if (!buttons.length) return; // Avoid inserting a Keke-only row before fares render.
      for (const button of buttons) {
        const type = button.dataset.option;
        const filename = Object.prototype.hasOwnProperty.call(images, type) ? images[type] : null;
        if (!filename) continue;
        const holder = button.querySelector(".vehicle");
        if (holder && !holder.querySelector("img.movego-ride-3d")) {
          const image = document.createElement("img");
          image.className = "movego-ride-3d";
          image.src = prefix + filename;
          image.alt = "";
          image.setAttribute("aria-hidden", "true");
          image.decoding = "async";
          holder.replaceChildren(image);
        }
        if (type === "One Click") {
          const heading = button.querySelector(".option-body strong");
          if (heading && heading.textContent !== "inHurry") heading.textContent = "inHurry";
        }
      }
      if (!root.querySelector(".movego-keke-option")) {
        const card = document.createElement("button");
        card.type = "button";
        card.disabled = true;
        card.className = "option movego-keke-option";
        card.setAttribute("aria-disabled", "true");
        card.title = "Keke booking coming soon";
        const icon = document.createElement("span");
        icon.className = "vehicle";
        const image = document.createElement("img");
        image.className = "movego-ride-3d";
        image.src = prefix + "keke.webp";
        image.alt = "";
        image.setAttribute("aria-hidden", "true");
        icon.appendChild(image);
        const body = document.createElement("span");
        body.className = "option-body";
        const heading = document.createElement("strong");
        heading.textContent = "Keke";
        const caption = document.createElement("span");
        caption.textContent = "Coming soon";
        body.append(heading, caption);
        const price = document.createElement("span");
        price.className = "price";
        price.textContent = "Unavailable";
        card.append(icon, body, price);
        const comfort = root.querySelector('button.option[data-option="Comfort"]');
        if (comfort) comfort.insertAdjacentElement("afterend", card);
        else root.appendChild(card);
      }
    } finally { updating = false; }
  }
  function schedule() {
    if (!scheduled) { scheduled = true; queueMicrotask(update); }
  }
  function initialize() {
    const root = document.getElementById("options");
    if (!root) return;
    // Watch only structural changes, not attributes/text, to avoid an observer feedback loop.
    const observer = new MutationObserver(schedule);
    observer.observe(root, {childList: true, subtree: true});
    schedule();
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initialize, {once:true});
  else initialize();
})();
