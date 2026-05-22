import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database import Base, get_db
from src.main import app

# Test database
SQLITE_URL = "sqlite:///./test.db"

engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session",autouse=True)
def setup_database():
    #Create all tables before tests run. Drop all tables after tests finish.
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="session")
def client():
    #FastAPI test client - simulates real HTTP requests.
    def override_get_db():
        db=TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    # Replace the real DB dependency with our test DB
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def auth_token(client):
    """
    Register a test user, manually verify them, then return their JWT token.
    Bypasses OTP email verification for testing purposes.
    """
    # Register test user
    client.post("/auth/register", json={
        "email": "testuser@jobradar.com",
        "password": "testpass123"
    })

    # Manually verify the user in the test database
    # bypasses OTP since we cannot send real emails in CI
    db = TestingSessionLocal()
    from src.models import User
    user = db.query(User).filter(
        User.email == "testuser@jobradar.com"
    ).first()
    if user:
        user.is_verified = True
        db.commit()
    db.close()

    # Now login
    response = client.post("/auth/login", data={
        "username": "testuser@jobradar.com",
        "password": "testpass123"
    })

    return response.json()["access_token"]

@pytest.fixture(scope="session")
def auth_headers(auth_token):
    #Returns Authorization header dict ready to pass into requests.
    return {"Authorization": f"Bearer {auth_token}"}

