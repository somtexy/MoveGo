MOVEGO STEP 2 - PHONE NUMBER SCREEN

This archive contains Step 1 plus the new Step 2 files. If you have already customized your Step 1 images, DO NOT overwrite your images with the ones in this archive. Copy only these three new files:
- frontend/passenger/phone.html
- frontend/css/phone.css
- frontend/js/phone.js
Then update frontend/js/onboarding.js so that the Continue with phone button opens ./phone.html. The supplied onboarding.js already includes this change.

Run: cd movego/frontend && python -m http.server 5500
Visit: http://localhost:5500/passenger/

Phone validation works locally. The app does not send SMS or create an account. Django integration comes later.
