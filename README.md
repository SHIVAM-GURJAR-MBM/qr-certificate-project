# Certify — QR-Based E-Certification and Verification

A responsive React and Flask application for creating certificate templates, issuing single or bulk certificates, generating PDFs with verification QR codes, and managing revocation. SQLite stores issuer, template, recipient, certificate, import batch, email attempt and audit records.

## Requirements

- Python 3.10 or newer
- Node.js 18 or newer and npm

## Run locally

1. In a terminal, install backend dependencies and start Flask:

   ```powershell
   cd backend
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   python app.py
   ```

   The API runs at `http://localhost:5000`. On its first run, it creates the SQLite database and a demo administrator.

2. In a second terminal, install and start React:

   ```powershell
   cd frontend
   npm install
   npm run dev
   ```

   Open `http://localhost:5173`. Vite proxies `/api` and `/verify` to Flask.

Default local sign-in:

- Email: `admin@example.com`
- Password: `ChangeMe123!`

Set `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `ADMIN_NAME` and `SECRET_KEY` in the environment before the first backend launch to customize the demo account. The account is seeded only when the user table is empty. Copy `.env.example` to `.env` and load it with your preferred environment manager; Flask does not load `.env` automatically.

## Deploy to GitHub and publish the app

GitHub stores and versions this source code. It does not run the Flask server. For a simple public demo, deploy the repository to a host that supports a Python web service and a Node build step (for example, Render).

1. Install Git for Windows, then open PowerShell in the project root.
2. Review `.gitignore` and confirm `.env`, `instance/`, `generated_certificates/`, `.venv/` and `node_modules/` are ignored. Never add `.env`, database files, generated recipient certificates, or SMTP credentials to GitHub.
3. Create an empty repository on GitHub. Then initialize and push this project:

   ```powershell
   git init
   git add .
   git status --short
   git commit -m "Initial certificate verification app"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
   git push -u origin main
   ```

   Inspect `git status --short` before committing. If `.env` appears in the staged files, stop and remove it from the index before committing.

4. In your hosting provider, connect the GitHub repository and create one web service with:

   - **Build command:** `cd frontend && npm ci && npm run build && cd ../backend && pip install -r requirements.txt`
   - **Start command:** `cd backend && gunicorn --bind 0.0.0.0:$PORT app:app`
   - **Health check path:** `/api/health`

   The Flask service serves the built React files from `frontend/dist`, so the UI, API, session cookie and QR verification use one origin.

5. Add these environment variables in the hosting dashboard before the first deploy:

   - `APP_ENV=production`
   - `SECRET_KEY=` a long random secret generated for this deployment
   - `ADMIN_NAME=` issuer display name
   - `ADMIN_EMAIL=` your issuer login email
   - `ADMIN_PASSWORD=` a unique strong password
   - `DATABASE_PATH=` a path on a persistent disk, for example `/var/data/certificates.sqlite3`
   - `PDF_STORAGE_PATH=` a path on the same persistent disk, for example `/var/data/generated_certificates`
   - `PUBLIC_BASE_URL=` the final public service URL, for example `https://your-service.example.com`

   Attach a persistent disk and mount it at `/var/data`. SQLite records and generated PDFs are otherwise lost when many hosts replace an instance during redeploy. The hosting provider must support persistent storage for this prototype; use managed PostgreSQL/object storage for a scalable production system.

6. Deploy, open the service URL, sign in with the configured issuer account, create a template, and issue a test certificate. Scan its QR from a separate device/network to confirm its verification URL is publicly reachable.

The default development credentials are public in this README, so change them on the hosted service. The user account is seeded only when the database has no users; changing `ADMIN_PASSWORD` later does not reset an already-created account.

## SMTP email (optional)

Set `SMTP_HOST` to your email provider's real SMTP server (not `smtp.example.com`), along with `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD` and `SMTP_FROM`. For STARTTLS, set `SMTP_USE_TLS=true` (commonly port 587); for implicit TLS, set `SMTP_USE_SSL=true` and `SMTP_USE_TLS=false` (commonly port 465). Check your provider's SMTP instructions for the correct host, port and authentication requirements. Email failures are logged without undoing certificate issuance. You can retry from a certificate detail page. Without SMTP configuration, issuance, PDF download and public verification work normally.

## Implemented workflows

- Issuer login/logout with protected API routes.
- Dashboard counts and recent activity.
- Template creation, editing and certificate preview.
- Individual issuance and CSV/XLSX validation with row errors and bulk issuance.
- Backend-generated A4 landscape PDFs with unique random IDs and QR verification links.
- Private certificate downloads, issuer search and status filtering.
- Public verification with valid, revoked and not-found outcomes. Public responses omit email, internal IDs, audit data and file paths.
- Reason-required certificate revocation with audit history.
- Optional SMTP PDF delivery and stored send attempts.
- CSV report export.

## API overview

Issuer endpoints use the Flask session cookie. Frontend requests include credentials.

| Method | Endpoint | Access | Purpose |
| --- | --- | --- | --- |
| POST | `/api/auth/login` | Public | Create issuer session |
| POST | `/api/auth/logout` | Issuer | End issuer session |
| GET | `/api/dashboard/summary` | Issuer | KPI counts and recent activity |
| GET, POST | `/api/templates` | Issuer | List or create templates |
| PUT | `/api/templates/{id}` | Issuer | Update template |
| POST | `/api/recipients/import` | Issuer | Validate CSV/XLSX and return row-level errors |
| POST | `/api/certificates` | Issuer | Issue one certificate |
| POST | `/api/certificates/bulk` | Issuer | Issue up to 100 recipients |
| GET | `/api/certificates` | Issuer | Search by name/email/ID and filter by status |
| GET | `/api/certificates/{uid}` | Issuer | Read details and audit events |
| GET | `/api/certificates/{uid}/pdf` | Issuer | Protected PDF download |
| POST | `/api/certificates/{uid}/revoke` | Issuer | Revoke with reason |
| POST | `/api/certificates/{uid}/send-email` | Issuer | Send or retry certificate email |
| GET | `/api/verify/{uid}` | Public | Return approved public details only |
| GET | `/api/reports/issuance` | Issuer | Summary; add `?format=csv` to export |
| GET | `/verify/{uid}` | Public | Human-readable verification page |

## Configuration and deployment notes

- `DATABASE_PATH` defaults to `instance/certificates.sqlite3`.
- PDFs are stored in `generated_certificates/`, outside the frontend's static directory.
- `FRONTEND_ORIGIN` sets the allowed CORS origin(s), comma-separated.
- Use a long random `SECRET_KEY` and HTTPS in deployment. The development server uses non-secure cookies for localhost; enable `SESSION_COOKIE_SECURE=true` in the Flask configuration when serving over HTTPS.
- The development CORS origin defaults to `http://localhost:5173`.
- This MVP uses a single seeded issuer account and local SQLite/file storage. Add operational backup and access controls before production use.

## Project structure

```text
backend/                 Flask REST API and certificate services
frontend/                React + Vite responsive application
instance/                Local SQLite database (created at runtime)
generated_certificates/  Protected generated PDF storage
.env.example             Environment variable template
```

## Scope notes

Blockchain and formal W3C credentials are intentionally outside the MVP. A QR code is only a pointer; public verification checks the live server-side database status. Logo/signature uploads, pagination, dashboard date filters and password reset are not yet part of this first implementation.
