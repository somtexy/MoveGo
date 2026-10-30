STEP 10 — RIDE OPTIONS + ILLUSTRATIVE FARES

Added frontend/passenger/ride-options.html, frontend/css/ride-options.css and frontend/js/ride-options.js. Updated destination.html and destination.js so trip review links to ride options and stores a validated session-only draft.

IMPORTANT: Fare amounts use arbitrary illustrative prices for a FIXED 8 km demo route. They are NOT real fares, route calculations, live ETA values or driver availability. Booking is deliberately disabled.

To run: cd frontend && python -m http.server 5500
Then visit http://localhost:5500/passenger/home.html and complete the location selection/Continue/View ride options sequence.

For real bookings: add Django REST endpoints, map geocoding/routing, server-side fare computation, driver matching and verified authentication.

Preserve your custom images when merging this archive into your existing local working copy.
