MoveGo Step 8 — Passenger menu + opt-in theme

Run: cd frontend && python -m http.server 5500
Open: http://localhost:5500/passenger/home.html

Menu options are explicitly DEMO placeholders, except Driver mode and Edit first name, which navigate to existing pages. Dark mode switch immediately updates the home/map panels, drawer and destination search and saves the preference in localStorage. The welcome and registration screens intentionally do NOT load theme.css or theme.js; they remain light. Add these two shared files to any NEW post-registration screen to inherit theme preference, and use matching CSS variables/element styling.

Keep your own edited onboarding images when merging this zip. Django backend is not yet connected.
