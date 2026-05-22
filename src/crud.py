from sqlalchemy.orm import Session
from src import models, schemas
from src.auth import hash_password


# ── User operations ──────────────────────────────────────────────────

def get_user_by_email(db: Session, email: str):
    """Fetch user by email. Returns None if not found."""
    return db.query(models.User).filter(
        models.User.email == email
    ).first()


def create_user(db: Session, user: schemas.UserCreate):
    """Create new user. Hashes password before storing."""
    db_user = models.User(
        email=user.email,
        hashed_password=hash_password(user.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# ── JobApplication operations ─────────────────────────────────────────

def create_application(
    db: Session,
    application: schemas.JobApplicationCreate,
    user_id: int
):
    """Save a new job application for the given user."""
    db_app = models.JobApplication(
        **application.model_dump(),
        user_id=user_id
    )
    db.add(db_app)
    db.commit()
    db.refresh(db_app)
    return db_app


def get_applications(db: Session, user_id: int):
    """Return all applications for a user, newest first."""
    return db.query(models.JobApplication).filter(
        models.JobApplication.user_id == user_id
    ).order_by(models.JobApplication.created_at.desc()).all()


def get_application_by_id(db: Session, application_id: int, user_id: int):
    """Return single application by id. user_id prevents cross-user access."""
    return db.query(models.JobApplication).filter(
        models.JobApplication.id == application_id,
        models.JobApplication.user_id == user_id
    ).first()


def update_application(
    db: Session,
    application_id: int,
    user_id: int,
    updates: schemas.JobApplicationUpdate
):
    """Update only the fields provided. Returns None if not found."""
    db_app = get_application_by_id(db, application_id, user_id)
    if not db_app:
        return None
    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_app, field, value)
    db.commit()
    db.refresh(db_app)
    return db_app


def delete_application(db: Session, application_id: int, user_id: int):
    """Permanently delete an application. Returns True if deleted."""
    db_app = get_application_by_id(db, application_id, user_id)
    if not db_app:
        return False
    db.delete(db_app)
    db.commit()
    return True

#Returns applications filtered by status.
def get_applications_by_status(db:Session, user_id:int, status:str = None):
    query = db.query(models.JobApplication).filter(
        models.JobApplication.user_id == user_id
    )
    if status:
        query = query.filter(models.JobApplication.status == status)
    return query.order_by(models.JobApplication.created_at.desc()).all()
    

