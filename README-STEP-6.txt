MoveGo — Step 6: Welcome / First name

New files:
- frontend/passenger/profile.html
- frontend/css/profile.css
- frontend/js/profile.js
- frontend/assets/images/profile-welcome-art.jpg

Modified:
- frontend/js/role.js (Passenger opens profile.html; Driver remains a labeled demo).

How to test:
1. Open terminal in movego/frontend
2. Run: python -m http.server 5500
3. Browse to http://localhost:5500/passenger/role.html
4. Select Passenger, enter your first name, and click Next.

Notes:
- Frontend demo only. First name is saved in sessionStorage, not Django.
- The illustration is a cropped reference asset; replace with original art if available.
- Preserve your own customized onboarding image files when merging.
