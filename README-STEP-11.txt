MOVEGO — STEP 11: PAYMENT METHOD SELECTION

New files:
- frontend/passenger/payment.html
- frontend/css/payment.css
- frontend/js/payment.js

Modified files:
- frontend/passenger/ride-options.html
- frontend/css/ride-options.css
- frontend/js/ride-options.js

Start local server from the frontend directory:
  python -m http.server 5500

Visit http://localhost:5500/passenger/home.html and choose pickup, destination, ride, then payment preference.

Payment methods are frontend-only preferences saved in sessionStorage. No card inputs, payment gateway connection, driver matching or real booking is included. The quoted fare is a DEMO amount, not a charge.

Your customized welcome-screen images can be preserved when merging this archive.
