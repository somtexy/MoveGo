# Step 21 — Frontend audit and Django setup

## Purpose
Create a working Django foundation without representing demo frontend flows as live services.

## Windows PowerShell quick start

```powershell
cd movego\backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py check
python manage.py migrate
python manage.py runserver 8000
```

If PowerShell prevents activation, use Command Prompt and `.venv\Scripts\activate.bat`, or run `.venv\Scripts\python.exe` directly.

Open http://127.0.0.1:8000/api/health/ to see `{ "service": "movego-api", "status": "ok", "version": "0.1" }`.

To view the existing passenger frontend, in a second terminal run `cd movego\frontend` and `py -m http.server 5500`, then open http://localhost:5500/passenger/home.html . Both servers remain separate for now.

`.env.example` documents environment variables. Django does **not** auto-load `.env`; configure environment variables in PowerShell before starting Django or add an environment loader in a later step. Default dev setup uses SQLite and an insecure dev-only secret; never deploy with the defaults.

## Review findings

- Passenger frontend has 20 HTML pages. Login, trip lifecycle, maps, sample fares, notifications, support tickets, and saved addresses are frontend demos rather than trusted server records.
- The booking flow goes: home → destination → ride options → payment → confirm ride → driver search preview → driver assigned preview → completion → history.
- The navigation currently includes working routes to History, Notifications, Settings, Help, Safety and Saved Places. Some menu sections remain placeholders.
- The new SVG icon system is preserved; optional dark mode remains a navigation-menu preference with light mode as its initial setting.
- Authentication, payments, real ride dispatch, and live driver tracking are NOT implemented in this step.

## Planned backend modules (not yet implemented)

- `accounts`: passenger/driver/admin identities, session/JWT strategy, OTP verification, profile APIs
- `drivers`: vehicles, eligibility, driver online availability and location updates
- `rides`: fares computed on the server, transactional dispatch/acceptance, state transitions
- `payments`: Paystack verification, webhooks, reconciliation and cash payment status
- `notifications`: persisted events, WebSocket delivery and push integration

## Important

Do not store API secrets in frontend source. Client fare values must never be treated as authoritative. Avoid exposing driver geolocation to unauthorized passengers. Implement payment verification and webhook signature validation before processing real money.
