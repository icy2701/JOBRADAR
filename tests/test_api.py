import pytest

# Health check

def test_health_returns_200(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"]== "ok"
    assert response.json()["project"]=="JobRadar"

# Auth tests   

def test_register_creates_user(client):
    response=client.post("/auth/register", json={
        "email": "newuser@jobradar.com",
        "password": "securepass123"
    })

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@jobradar.com"
    assert "id" in data
    assert "created_at" in data
    assert "password" not in data
    assert "hashed_password" not in data

def test_register_rejects_duplicate_email(client):
    # First registration should succeed
    response1 = client.post("/auth/register", json={
        "email": "duplicate@jobradar.com",
        "password": "pass123"
    })
    # Try to register again with same email
    response = client.post("/auth/register", json={
        "email": "duplicate@jobradar.com",
        "password": "different_pass"
    })
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]

def test_login_returns_token(client, auth_headers):
    response = client.post("/auth/login", data={
        "username": "testuser@jobradar.com",
        "password": "testpass123"
    })

    assert response.status_code == 200
    data=response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    # Token must be a real JWT — starts with eyJ
    assert data["access_token"].startswith("eyJ")

def test_login_rejects_wrong_password(client):
    response = client.post("/auth/login", data={
        "username": "testuser@jobradar.com",
        "password": "wrongpassword"
    })

    assert response.status_code == 401
    assert "Incorrect" in response.json()["detail"]

# Application tests

def test_create_application(client,auth_headers):
    response=client.post("/applications", json={
        "job_url": "https://jobs.sap.com/backend-engineer",
        "company_name": "SAP SE",
        "role_title": "Backend Engineer",
        "source": "linkedin",
        "notes": "Great opportunity"
    }, headers=auth_headers)
    
    assert response.status_code == 201
    data=response.json()
    assert data["company_name"] == "SAP SE"
    assert data["role_title"] == "Backend Engineer"
    assert data["source"] == "linkedin"
    assert data["resume_url"] is None
    assert "id" in data

def test_list_applications_returns_list(client,auth_headers):
    response = client.get("/applications", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    # Verify structure of first item
    assert "company_name" in data[0]
    assert "status" in data[0]
    assert "job_url" in data[0]

def test_get_application_by_id(client, auth_headers):
    """
    GET /applications/{id} must return the correct application.
    """
    # First create one
    create_response = client.post("/applications", json={
        "job_url": "https://careers.bmw.com/python-dev",
        "company_name": "BMW Group",
        "role_title": "Python Developer",
        "source": "xing"
    }, headers=auth_headers)

    app_id = create_response.json()["id"]

    # Now fetch it by id
    response = client.get(f"/applications/{app_id}",
                          headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == app_id
    assert data["company_name"] == "BMW Group"

def test_update_application_status(client, auth_headers):
    # Create application
    create_response = client.post("/applications", json={
        "job_url": "https://jobs.siemens.com/dev",
        "company_name": "Siemens",
        "role_title": "Software Engineer",
        "source": "stepstone"
    }, headers=auth_headers)

    app_id=create_response.json()["id"]
    original_company = create_response.json()["company_name"]

    # Update only status
    response = client.patch(f"/applications/{app_id}", json={
        "status": "applied"
    }, headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    # Status updated
    assert data["status"] == "applied"
    # Company name unchanged — PATCH only changes what we sent
    assert data["company_name"] == original_company

def test_delete_application(client, auth_headers):  
    # Create application to delete
    create_response = client.post("/applications", json={
        "job_url": "https://jobs.bosch.com/dev",
        "company_name": "Bosch",
        "role_title": "Junior Developer",
        "source": "other"
    }, headers=auth_headers)

    app_id = create_response.json()["id"]
    # Delete it
    delete_response = client.delete(f"/applications/{app_id}",
                                    headers=auth_headers)
    assert delete_response.status_code == 204

    # Try to fetch it — must be gone
    get_response = client.get(f"/applications/{app_id}",
                              headers=auth_headers)
    assert get_response.status_code == 404


def test_unauthorized_access_blocked(client):
    response = client.get("/applications")
    assert response.status_code == 401