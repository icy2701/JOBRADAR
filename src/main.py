from fastapi import FastAPI, Depends , HTTPException, status ,UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from src.database import get_db
from src import models, schemas, crud, auth
from fastapi.middleware.cors import CORSMiddleware

#App init
app=FastAPI(
    title="JobRadar API",
    description="Track job applications automatically. Chrome extension + FastAPI backend",
    version="1.0.0"
)

# CORS 
# Allows Chrome extension and any frontend to call the API
# Chrome extensions have origin: chrome-extension://<id>
# allow_origins=["*"] permits all origins — fine for a portfolio project
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#Health check
@app.get("/health",tags=["Health"])
def health_check():
    return {"status":"ok", "project":"JobRadar"}

# Auth routes
@app.post("/auth/register",
          response_model=schemas.UserResponse,
          status_code=status.HTTP_201_CREATED,
          tags=["Auth"])

def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Check email not already taken
    existing=crud.get_user_by_email(db, user.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    return crud.create_user(db, user)

@app.post("/auth/login",
          response_model=schemas.Token,
          tags=["Auth"])

@app.post("/auth/login",
          response_model=schemas.Token,
          tags=["Auth"])

def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    # Find user by email
    user = crud.get_user_by_email(db, form_data.username)

    # Same error for wrong email or wrong password
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
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
    # Only scrape if URL provided and details are missing
    if application.job_url and (
        not application.company_name or not application.role_title
    ):
        from src.scraper import scrape_job
        scraped = scrape_job(application.job_url)

        # Fill in only the fields that are missing
        # Never overwrite what the user explicitly provided
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
    status:str=None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    return crud.get_applications_by_status(db, current_user.id, status)


@app.get("/applications/{application_id}",
         response_model=schemas.JobApplicationResponse,
         tags=["Applications"])

def get_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
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
    # Verify application exists and belongs to current user
    application = crud.get_application_by_id(
        db, application_id, current_user.id
    )
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )

    # Read file bytes — async because file I/O is non-blocking
    file_bytes = await file.read()

    # Upload to S3 — returns public URL
    from src.s3 import upload_resume as s3_upload
    resume_url = s3_upload(
        file_bytes=file_bytes,
        filename=file.filename,
        content_type=file.content_type,
        user_id=current_user.id
    )

    # Save S3 URL to the application record
    application.resume_url = resume_url
    db.commit()
    db.refresh(application)

    return application


@app.get("/dashboard", response_class=HTMLResponse, tags=["Dashboard"])
def dashboard():
    # Web dashboard : view, filter, and manage all job applications.Served from src/templates/dashboard.html
    import os
    template_path=os.path.join(os.path.dirname(__file__), "templates", "dashboard.html")
    with open(template_path, "r") as f:
        return HTMLResponse(content=f.read(), status_code=200)
    


    