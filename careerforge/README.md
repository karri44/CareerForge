# CareerForge — upgraded Django job portal

A complete responsive interface for the existing CareerForge backend, with database-backed candidate and employer workflows. No Node.js or separate frontend server is needed.

## Start on Windows (PowerShell)

Install Python 3.10 or later (3.12 recommended). Extract this ZIP into a new folder, then open the folder containing `manage.py` in VS Code. Do not reuse a virtual environment copied from another folder.

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver
```

Open http://127.0.0.1:8000/ in your browser. These commands do not require activating the virtual environment or changing PowerShell execution policy. If `py` is unavailable, use `python` for the first command.

On later starts, run only:

```powershell
.\.venv\Scripts\python.exe manage.py runserver
```

## Start on macOS / Linux

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver
```

## Try the full workflow

1. Create an **Employer** account using “Get started.” Enter a company name.
2. Open the dashboard and choose **Post a job**. Add responsibilities, location, annual salary in INR, skills, and a deadline. Mark it active to publish it.
3. Sign out and create a **Candidate** account. Add your profile and upload a PDF resume (maximum 5 MB).
4. Search for the job, save it, and send an application with an optional cover note.
5. Sign back in as the employer to review the applicant, download their resume, and update the status.
6. The candidate can track the status on the dashboard and view the notification in Updates. The unread badge refreshes every 30 seconds while the page is visible. Refresh the dashboard to load changed application details.

Roles are selected at registration. No public account receives Django administrator privileges.

## Optional sample listings

```powershell
.\.venv\Scripts\python.exe manage.py seed_demo
```

This adds six **fictional demonstration listings**, with demo company names and an explicit notice in each description. It is safe to run repeatedly. It does not overwrite existing jobs or create usable demo passwords. These are not vacancies sourced from real employers. Delete demo jobs through the admin panel when no longer needed.

## Admin panel and skills

```powershell
.\.venv\Scripts\python.exe manage.py createsuperuser
```

Visit http://127.0.0.1:8000/admin/ with the account you create. Manage users, jobs, skills, profiles, and applications. Add skills in the admin panel before posting jobs, or run `seed_demo` to populate a starter skill list. Superusers with no role can use the admin panel; use a separate Employer account for the employer dashboard.

## Included improvements

- Teal-and-cream responsive layout, compact job cards, accessible form labels, keyboard focus, empty states, and feedback messages.
- Keyword/company/skill search; location and employment filters; newest/salary sorting; pagination.
- Saved jobs persisted per account.
- Detailed role pages, copy-link action, application notes, duplicate protection, and closed/deadline checks.
- Candidate dashboard, profile editing, PDF resume upload, and application withdrawal.
- Employer job creation/editing, applicant review, and status changes.
- In-app notifications for applications and status updates through the website and REST API.
- Password validation, CSRF protection, user ownership checks, private resume downloads, and 15-minute session inactivity expiry.
- Original REST endpoints retained under `/api/` with stricter application and job validation.

## Existing data

The supplied SQLite database is retained, with an additive migration for saved jobs and notifications. Existing users, jobs, profiles, and applications are preserved. The old embedded development secret was replaced, so existing browser sessions or JWTs may need a fresh login. No passwords were reset.

The uploaded archive contained no resume media directory. If your original machine has a `media` directory, copy it into this project alongside `manage.py`. Keep a backup of your existing project and database before switching folders.

Do not publish the included SQLite database or uploaded resumes to GitHub. The included `.gitignore` excludes them, virtual environments, and secrets. The downloaded ZIP itself contains your retained database and should be treated as private.

## Verification

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py test core
```

See `VALIDATION.md` for the verified scope and limitations.

## Deployment boundary

This is a working local Django application, not a hosted service. The development server is for local use. Before public deployment, set `DJANGO_DEBUG=0`, supply a long random `DJANGO_SECRET_KEY`, and set comma-separated `DJANGO_ALLOWED_HOSTS`. Run migrations and `collectstatic`, serve static files through your hosting stack, and use HTTPS and a production WSGI/ASGI server. Do not serve the private `media` directory publicly: resumes are downloaded through an authenticated route. Configure backups, login rate limiting at the proxy, upload scanning, monitoring, and appropriate operational policies for a public service.

The app does not send emails, scrape vacancies, perform employer identity verification, or implement password-reset emails. Notifications are in-app polling, not WebSocket push. Applications expose the candidate's current profile/resume to the owning employer, not a frozen historical copy. Replacing a resume can leave older files in private storage; configure a retention/cleanup policy before production. PDF header and size checks do not replace malware scanning.
