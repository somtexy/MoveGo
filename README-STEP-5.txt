MOVEGO — STEP 5: ROLE SELECTION

NEW:
frontend/passenger/role.html
frontend/css/role.css
frontend/js/role.js
frontend/assets/images/role-passenger.jpg
frontend/assets/images/role-driver.jpg

MODIFIED:
frontend/js/passkey.js  (Skip now opens role selection)

IMPORTANT: All previous code is included for convenience. Preserve your customized onboarding images. Role choice is stored only in sessionStorage (demo). It does not authenticate or register anyone.

RUN: from frontend folder: python -m http.server 5500
OPEN: http://localhost:5500/passenger/
PATH: Continue with Passkey -> Skip -> Passenger / Driver.
