MoveGo Step 4 — Passkey screen
Run: cd movego/frontend && python -m http.server 5500
Open: http://localhost:5500/passenger/
On welcome tap Continue with Passkey; back returns to welcome.
This is a UI-only step. No passkey is created and no authentication is performed.
Keep your own customized onboarding images when merging.
New: passenger/passkey.html, css/passkey.css, js/passkey.js
Modified: js/onboarding.js, passenger/index.html (cache version).
