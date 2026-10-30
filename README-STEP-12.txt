MoveGo Step 12: Ride Confirmation + Driver Search UI Preview

Added frontend/passenger/confirm-ride.html and driver-search.html, frontend/css/confirm-ride.css, frontend/js/confirm-ride.js and driver-search.js.
Updated frontend/passenger/payment.html and frontend/js/payment.js to route a selected payment method into confirmation.

Run: cd frontend && python -m http.server 5500
Open: http://localhost:5500/passenger/home.html
Choose destination > ride type > payment > confirmation > search preview.
No API calls, payment authorizations, real ride requests, driver matching, or driver assignment are implemented.
Keep your customized onboarding images when merging files. Existing optional dark-mode menu switch is preserved.
