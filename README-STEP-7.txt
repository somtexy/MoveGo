MOVEGO — STEP 7: PASSENGER HOME (FRONTEND DEMO)

NEW:
 frontend/passenger/home.html
 frontend/css/home.css
 frontend/js/home.js
 frontend/assets/maps/demo-city.svg

MODIFIED:
 frontend/js/profile.js — valid profile submission now navigates to home.html.

RUN FROM movego/frontend:
 python -m http.server 5500

OPEN:
 http://localhost:5500/passenger/
 Or directly: http://localhost:5500/passenger/home.html

FUNCTIONAL DEMO UI:
 * Menu opens/closes, displays session name, and links to edit first name/role selection.
 * Ride types toggle selection.
 * Destination search opens a sheet, filters sample locations, and previews selected service/destination without inventing fares.
 * Escape closes panels.
 * Locate button explicitly requests browser geolocation permission. Map itself remains illustrative and is not georeferenced.
 * Alerts and unfinished drawer destinations show an informational message.

NOT IMPLEMENTED: live tiles/maps, routes, fare estimation, Django/API, driver positions, ride requests, user authentication. Sample locations are demo suggestions only.

NOTE: Keep YOUR already customized onboarding images when merging this ZIP. This step does not change those files. Browser image caches can be refreshed using Ctrl+Shift+R.
