[![Docker Hub](https://img.shields.io/badge/Docker%20Hub-aisi27%2Fjobradar-blue)](https://hub.docker.com/r/aisi27/jobradar)

# 📡 JobRadar — Job Application Tracker

A full-stack job tracking system with a Chrome extension, FastAPI backend, and web dashboard. Save jobs from any job board with one click, manage your application pipeline, and upload resumes — all in one place.

**Live API:** https://jobradar-pyss.onrender.com/docs
**Dashboard:** https://jobradar-pyss.onrender.com/dashboard

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | FastAPI, Python 3.11 |
| Database | PostgreSQL, SQLAlchemy, Alembic |
| Auth | JWT, bcrypt, OTP email via Resend |
| Storage | AWS S3 |
| Testing | pytest |
| DevOps | Docker, docker-compose, GitHub Actions |
| Deployment | Render |
| Extension | Chrome Extension (Manifest V3) |

---

## Features

- One-click job saving from LinkedIn, StepStone, Indeed, XING, and 20+ job boards
- Auto-fetches company name, role, and job description from the URL
- JWT authentication with OTP email verification
- Resume PDF upload per application stored in AWS S3
- Web dashboard with status filters, inline editing, and resume download
- CI/CD pipeline runs 11 automated tests on every push to main

---

## Run Locally

Clone the repo and start the full stack with one command:

    git clone https://github.com/icy2701/JOBRADAR.git
    cd JOBRADAR
    cp .env.example .env
    docker-compose up --build

Open http://localhost:8000/docs for the Swagger UI.

# Or pull directly from Docker Hub
docker pull aisi27/jobradar:latest

---

## Project Structure

    src/
      main.py            FastAPI app and all routes
      models.py          SQLAlchemy database models
      schemas.py         Pydantic request and response schemas
      auth.py            JWT and bcrypt authentication
      crud.py            Database operations
      scraper.py         Auto-fetch job data from URLs
      s3.py              AWS S3 resume upload
      email_service.py   OTP email via Resend
      templates/         Dashboard HTML
    chrome-extension/    Browser extension source
    tests/               pytest test suite
    alembic/             Database migrations

---

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | /health | No | Liveness check |
| POST | /auth/register | No | Create account, sends OTP |
| POST | /auth/verify-otp | No | Verify 6-digit OTP |
| POST | /auth/login | No | Returns JWT token |
| POST | /applications | Yes | Save a job application |
| GET | /applications | Yes | List all, filter by status |
| PATCH | /applications/{id} | Yes | Update status or details |
| DELETE | /applications/{id} | Yes | Delete application |
| POST | /applications/{id}/resume | Yes | Upload resume to S3 |
| GET | /dashboard | No | Web dashboard |

---

## Environment Variables

Copy .env.example and fill in your values:

    DATABASE_URL=postgresql://user:password@localhost:5432/jobradar
    SECRET_KEY=your-secret-key
    ALGORITHM=HS256
    ACCESS_TOKEN_EXPIRE_MINUTES=30
    AWS_ACCESS_KEY_ID=your-key
    AWS_SECRET_ACCESS_KEY=your-secret
    AWS_BUCKET_NAME=your-bucket
    RESEND_API_KEY=your-resend-key

---

## Chrome Extension

Load the extension locally in Chrome:

1. Open chrome://extensions
2. Enable Developer mode
3. Click Load unpacked
4. Select the chrome-extension/ folder

The extension saves jobs from any job board directly to your live API.