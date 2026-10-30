# MoveGo — Google Login / Signup

This package is an INCREMENTAL install. It does not overwrite your existing passenger, driver, OTP, or back-button pages. It adds Django OIDC authorization-code login and wires the existing **Continue with Google** button.

## Setup

1. Unzip the package, then run the installer with Python from any directory:
   `python C:\movego-google-auth-step36\install_google.py C:\movego`
   (Adjust extracted folder path as needed.)
2. In Google Cloud Console, configure OAuth consent / Google Auth Platform and create a **Web application** OAuth client. Add exactly this authorized redirect URI for local development:
   `http://127.0.0.1:8000/api/auth/google/callback/`
   Add your own Google account as a test user if your OAuth app is in Testing mode.
3. In `C:\movego\backend\.env` add:
   `GOOGLE_OAUTH_CLIENT_ID=your-client-id`
   `GOOGLE_OAUTH_CLIENT_SECRET=your-secret`
   `GOOGLE_OAUTH_REDIRECT_URI=http://127.0.0.1:8000/api/auth/google/callback/`
   Keep values private; never put the client secret into frontend files.
4. Ensure your existing settings.py loads `.env` (your Twilio setup should already do that).
5. `cd C:\movego\backend`
   `.venv\Scripts\activate.bat`
   `python -m pip install "google-auth>=2.35,<3" "requests>=2.32,<3"`
   `python manage.py check`
   `python manage.py migrate`
   `python manage.py test apps.accounts apps.rides apps.drivers -v 2`
   `python manage.py runserver 8000`
6. Open `http://127.0.0.1:8000/app/passenger/index.html`, hard refresh, and choose Continue with Google.

## Security and design

- Server validates Google's signed ID token (issuer, audience, expiry), email verification, one-time nonce, OAuth state, and subject.
- Unique Google `sub` identifies accounts; no insecure silent merging by matching email.
- No Google API tokens saved. Django standard session cookie is used.
- Google email verification does NOT mark `phone_verified` true. Before real rides/driver onboarding, explicitly decide whether to require verified phone numbers. Existing OTP flows remain available.
- Do not deploy on live HTTP; use HTTPS, restricted redirect URIs and production secrets.
- App passcode is not implemented in this package.

## Test after setup

- New Google account → MoveGo account and session created.
- Same Google account → same user on return.
- A Google email identical to an existing phone/password account → rejected rather than linked silently.
- Wrong state or callback without prior start → HTTP 400.
- Existing phone OTP still works.
- Existing rounded-square back buttons remain unchanged.

**Important:** Only install on your local development project. Tested through static compilation / package checks; Google redirect needs live verification in your browser.
