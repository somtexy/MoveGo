MoveGo STEP 13 — Driver Assigned & Trip Tracking Preview

NEW: frontend/passenger/driver-assigned.html, frontend/css/driver-assigned.css, frontend/js/driver-assigned.js
MODIFIED: frontend/passenger/driver-search.html (new preview navigation link)

Start a local server: cd movego/frontend && python -m http.server 5500
Open http://localhost:5500/passenger/home.html and follow destination > ride options > payment > confirmation > driver search > Preview assigned-driver screen.

Requires booking draft and preview session established by earlier screens. No real driver matched, no real GPS, no server request or payment. Status transitions are user-operated demo only.
Retain your custom onboarding images when merging. Light mode default; optional dark-mode switch remains in navigation menu.
