MoveGo STEP 3 — OTP screen (frontend preview)

Run:
  cd movego/frontend
  python -m http.server 5500
Then visit http://localhost:5500/passenger/

Flow: Continue with phone -> enter number -> Next -> verify.html
No WhatsApp message or OTP is sent. The countdown and code entry are UI-only, and no code is validated.

For users who already customized onboarding artwork, keep their current image files and copy only:
  frontend/passenger/verify.html (new)
  frontend/css/verify.css (new)
  frontend/js/verify.js (new)
  frontend/js/phone.js (replace)
  frontend/passenger/phone.html (replace, version links only)
  frontend/assets/images/otp-whatsapp-art.png (new)
