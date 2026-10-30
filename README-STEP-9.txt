MoveGo Step 9 — Destination search and trip review (frontend demo)

What's new:
* frontend/passenger/destination.html
* frontend/css/destination.css
* frontend/js/destination.js
* frontend/js/home.js modified: home destination button opens new screen and stores service choice.

Launch from the frontend directory:
    python -m http.server 5500
Open: http://localhost:5500/passenger/home.html
Tap "Where to & for how much?" to open the new page.

Notes:
* Locations are named demo suggestions, not search API or geocoded addresses.
* You can manually enter pickup/destination or request GPS coordinates.
* Continue opens a trip review, NOT a real ride booking.
* No fare, ETA, dispatch, payments or Django APIs are connected; request button disabled intentionally.
* Post-registration light/dark mode preference is inherited from Step 8.
* Your customized onboarding assets remain yours: do not overwrite them when merging.
