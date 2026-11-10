# Deploying ATS-Check to Render (free tier)

This guide deploys the current app (no login yet). Firebase steps are added when authentication is built.

## What you get on the free tier (checked against Render's docs)

- 512 MB RAM, 0.1 CPU, no credit card needed.
- The service **sleeps after 15 minutes without visitors**. The next visitor waits about a minute while it wakes up.
- 750 free instance hours per month.
- The disk is temporary. ATS-Check never stores resumes on disk after processing, so this is fine.
- Measured locally with the exact start command: the app uses about 78 MB.

## Files that configure the deployment

| File | Purpose |
|---|---|
| `render.yaml` | Tells Render how to build, start and health-check the app |
| `requirements.txt` | Packages to install (includes `gunicorn`, the production server) |
| `/health` route | Render pings this to know the app is alive |

## Step by step

### 1. Get the code onto GitHub's `main` branch
Render deploys from a branch. The simplest route:
1. Push your work branch: `git push -u origin <your-branch>`
2. On github.com open your repo, click **Compare & pull request**, then **Create pull request**, then **Merge pull request**.

### 2. Create a Render account
Go to render.com, click **Get Started**, and sign up **with GitHub**. Allow Render to access the `ATS-Check` repository when asked.

### 3. Create the service from `render.yaml` (Blueprint)
1. In the Render dashboard click **New +**, then **Blueprint**.
2. Pick the `ATS-Check` repo, then the `main` branch.
3. Render reads `render.yaml` and shows a service called `ats-check` on the **Free** plan. Click **Apply**.

**If Render asks for a payment method on this screen**, use the manual route instead: **New +**, then **Web Service**, then pick your repo, and enter:

| Field | Value |
|---|---|
| Runtime | Python 3 |
| Build command | `pip install -r requirements.txt` |
| Start command | `gunicorn app:app --workers 1 --threads 4 --timeout 60 --bind 0.0.0.0:$PORT` |
| Instance type | Free |
| Health check path | `/health` |

and add these environment variables:

| Key | Value |
|---|---|
| `PYTHON_VERSION` | `3.12.8` |
| `APP_ENV` | `production` |
| `SECRET_KEY` | a long random string (generate one: `python -c "import secrets; print(secrets.token_hex(32))"`) |
| `TRUST_PROXY` | `1` |
| `UPLOAD_FOLDER` | `/tmp/ats-uploads` |

### 4. Wait for the build
The first build takes a few minutes. Watch the **Logs** tab. When you see the service marked **Live**, open the `https://ats-check-xxxx.onrender.com` link at the top of the page.

### 5. Verify it works (production checklist)
- [ ] `/health` shows `{"status": "ok"}`
- [ ] The landing page loads with the green dark theme
- [ ] Upload a real PDF resume and reach the report
- [ ] Paste-text mode works
- [ ] The dark/light toggle works and is remembered after reload
- [ ] `/nope` shows the friendly 404 page, not an error dump
- [ ] On your phone, the pages fit the screen
- [ ] The privacy section does **not** mention Gemini (it only appears if `GEMINI_API_KEY` is set; leave it unset)
- [ ] Browser padlock shows HTTPS

## Environment variables explained

| Variable | Why |
|---|---|
| `APP_ENV=production` | Turns debug off and requires a real `SECRET_KEY`. The app refuses to start without one. |
| `SECRET_KEY` | Signs the session cookie. Keep it secret. Never commit it. |
| `TRUST_PROXY=1` | Makes the rate limiter see each visitor's real address (via Cloudflare's `True-Client-IP` header). Without it, everyone on the site would share one limit of 5 requests per minute. **Set this only on Render**, because on a server without such a proxy a visitor could fake the header. |
| `UPLOAD_FOLDER` | A temporary folder. Uploaded PDFs are deleted straight after reading. |
| `GEMINI_API_KEY` | **Do not set.** Optional and legacy. If set, resume text is sent to Google, and the privacy section will say so. |

## Troubleshooting

| Symptom | Likely cause and fix |
|---|---|
| Build fails | Open the Logs tab and read the red line. Check `PYTHON_VERSION` is `3.12.8`. |
| Log says `SECRET_KEY must be set...` | The variable is missing or shorter than 16 characters. Add it under **Environment**. |
| Deploy loops or "health check failed" | Check the start command is exactly as above, and the health path is `/health`. |
| First page takes about a minute | Normal on the free tier after 15 idle minutes. |
| Everyone gets "too quickly" | `TRUST_PROXY` is missing. Add `TRUST_PROXY=1`. |
| Site works but updates don't appear | Render redeploys when `main` changes. Check the **Events** tab for the latest deploy. |

## Known limits (honest list)

- Free-tier sleeping and cold starts, as above.
- The rate limiter lives in memory, so it resets when the app sleeps or restarts. Flask-Limiter replaces it in a later phase.
- Forms have no CSRF token yet (audit finding F9). The impact is low today because nothing is saved, but it is scheduled for Phase 10.
- No security headers yet (Phase 10).
- The `google-generativeai` package adds about 58 packages and a slower build. It is unused unless a key is set, and it goes away when the built-in engine replaces Gemini.
- Scoring is still the general keyword check. Career-field and job-description scoring come with the new engine.
