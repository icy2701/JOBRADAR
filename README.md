# JobRadar — Job Application Tracker

A Chrome extension + FastAPI backend that auto-captures job listings from any job board and tracks your entire application pipeline.

**Live API:** https://jobradar-pyss.onrender.com/docs

## Tech Stack
- FastAPI + PostgreSQL + SQLAlchemy
- JWT Authentication
- AWS S3 (resume storage)
- Docker + docker-compose
- GitHub Actions CI/CD
- Deployed on Render

## Features
- Save job applications from any URL
- Auto-fetch company name, role, job description
- Upload resume PDF per application (stored in AWS S3)
- Track application status through pipeline
- Full REST API with Swagger documentation

## Run locally
```bash
docker-compose up --build
```

## API Docs
https://jobradar-pyss.onrender.com/docs
