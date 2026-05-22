from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from src.database import get_db
from src import models, schemas, crud, auth

# App init
app = FastAPI(
    title="JobRadar API",
    description="Track job applications automatically. Chrome extension + FastAPI backend.",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check

@app.get("/health", tags=["Health"])
def health_check():
    """Liveness check. No auth required."""
    return {"status": "ok", "project": "JobRadar"}


# Auth routes

@app.post("/auth/register",
          response_model=schemas.UserResponse,
          status_code=status.HTTP_201_CREATED,
          tags=["Auth"])
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user account.
    Sends OTP verification email immediately after registration.
    User must verify OTP before they can login.
    """
    existing = crud.get_user_by_email(db, user.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    db_user = crud.create_user(db, user)

    from src.email_service import generate_otp, get_otp_expiry, send_otp_email
    otp     = generate_otp()
    expires = get_otp_expiry()
    crud.set_user_otp(db, db_user.id, otp, expires)
    send_otp_email(user.email, otp)

    return db_user


@app.post("/auth/verify-otp", tags=["Auth"])
def verify_otp(
    email: str,
    otp: str,
    db: Session = Depends(get_db)
):
    """
    Verify email with OTP code received by email.
    OTP expires after 10 minutes.
    After verification user can login normally.
    """
    verified = crud.verify_user_otp(db, email, otp)
    if not verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP"
        )
    return {"message": "Email verified successfully. You can now login."}


@app.post("/auth/login",
          response_model=schemas.Token,
          tags=["Auth"])
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login with email and password.
    Requires email to be verified first via OTP.
    Returns JWT access token valid for 30 minutes.
    """
    user = crud.get_user_by_email(db, form_data.username)

    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Check your inbox for the OTP code."
        )

    access_token = auth.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


# Job application routes

@app.post("/applications",
          response_model=schemas.JobApplicationResponse,
          status_code=status.HTTP_201_CREATED,
          tags=["Applications"])
def create_application(
    application: schemas.JobApplicationCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Save a new job application.
    If job_url provided and details missing, scraper auto-fetches them.
    """
    if application.job_url and (
        not application.company_name or not application.role_title
    ):
        from src.scraper import scrape_job
        scraped = scrape_job(application.job_url)

        if not application.company_name and scraped.get("company_name"):
            application.company_name = scraped["company_name"]
        if not application.role_title and scraped.get("role_title"):
            application.role_title = scraped["role_title"]
        if not application.job_description and scraped.get("job_description"):
            application.job_description = scraped["job_description"]

    return crud.create_application(db, application, current_user.id)


@app.get("/applications",
         response_model=list[schemas.JobApplicationResponse],
         tags=["Applications"])
def list_applications(
    status: str = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Returns all job applications for the logged-in user.
    Optional ?status=applied filter.
    """
    return crud.get_applications_by_status(db, current_user.id, status)


@app.get("/applications/{application_id}",
         response_model=schemas.JobApplicationResponse,
         tags=["Applications"])
def get_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Returns a single application by ID."""
    app = crud.get_application_by_id(db, application_id, current_user.id)
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    return app


@app.patch("/applications/{application_id}",
           response_model=schemas.JobApplicationResponse,
           tags=["Applications"])
def update_application(
    application_id: int,
    updates: schemas.JobApplicationUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Update status, notes, or date_applied. Send only changed fields."""
    app = crud.update_application(db, application_id, current_user.id, updates)
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    return app


@app.delete("/applications/{application_id}",
            status_code=status.HTTP_204_NO_CONTENT,
            tags=["Applications"])
def delete_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Permanently delete an application."""
    deleted = crud.delete_application(db, application_id, current_user.id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )


@app.post("/applications/{application_id}/resume",
          response_model=schemas.JobApplicationResponse,
          tags=["Applications"])
async def upload_resume(
    application_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Upload a resume PDF for a specific job application.
    Stored in AWS S3. Public URL saved to application record.
    """
    application = crud.get_application_by_id(
        db, application_id, current_user.id
    )
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )

    file_bytes = await file.read()

    from src.s3 import upload_resume as s3_upload
    resume_url = s3_upload(
        file_bytes=file_bytes,
        filename=file.filename,
        content_type=file.content_type,
        user_id=current_user.id
    )

    application.resume_url = resume_url
    db.commit()
    db.refresh(application)

    return application


# Dashboard

@app.get("/dashboard", response_class=HTMLResponse, tags=["Dashboard"])
def dashboard():
    """
    Web dashboard. View, filter, and manage all job applications.
    Served from src/templates/dashboard.html
    """
    import os
    template_path = os.path.join(
        os.path.dirname(__file__), "templates", "dashboard.html"
    )
    with open(template_path, "r") as f:
        return HTMLResponse(content=f.read())