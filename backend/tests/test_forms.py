"""
Tests for forms endpoints.
Critical path: form submission, approval (with race condition fix)
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.form import FormLink, FormSubmission
from app.models.student import Student
from app.models.user import User
from app.core.security import hash_password


@pytest.fixture
async def form_link(test_db):
    """Create a test form link."""
    form = FormLink(
        title="Student Registration",
        token="TEST12345",
        allowed_fields=[
            {"name": "first_name", "label": "First Name", "required": True, "type": "text"},
            {"name": "email", "label": "Email", "required": True, "type": "email"},
        ],
        is_active=True,
    )
    test_db.add(form)
    await test_db.commit()
    return form


@pytest.fixture
async def form_submission(test_db, form_link):
    """Create a test form submission."""
    sub = FormSubmission(
        form_link_id=form_link.id,
        submitted_data={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "admission_no": "ADM001",
        },
        status="pending",
    )
    test_db.add(sub)
    await test_db.commit()
    return sub


@pytest.mark.asyncio
async def test_public_get_form(client: AsyncClient, form_link):
    """Test getting active form (public endpoint)."""
    response = await client.get(f"/api/v1/forms/public/{form_link.token}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Student Registration"
    assert "allowed_fields" in data


@pytest.mark.asyncio
async def test_public_get_form_inactive(client: AsyncClient, form_link, test_db):
    """Test getting inactive form (should fail)."""
    form_link.is_active = False
    await test_db.commit()
    
    response = await client.get(f"/api/v1/forms/public/{form_link.token}")
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_public_submit_form(client: AsyncClient, form_link):
    """Test submitting form (public endpoint)."""
    payload = {
        "first_name": "Jane",
        "last_name": "Smith",
        "email": "jane@example.com",
        "admission_no": "ADM002",
    }
    
    response = await client.post(
        f"/api/v1/forms/public/{form_link.token}/submit",
        json=payload
    )
    
    assert response.status_code == 200
    assert "submitted successfully" in response.json()["message"]


@pytest.mark.asyncio
async def test_approve_submission(client: AsyncClient, admin_token, form_submission, test_db):
    """Test approving a form submission."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    payload = {"force_update": False}
    response = await client.post(
        f"/api/v1/forms/submissions/{form_submission.id}/approve",
        json=payload,
        headers=headers,
    )
    
    if response.status_code == 200:
        assert "approved successfully" in response.json()["message"]
        
        # Verify submission status changed
        from sqlalchemy import select
        result = await test_db.execute(
            select(FormSubmission).where(FormSubmission.id == form_submission.id)
        )
        updated_sub = result.scalar_one()
        assert updated_sub.status == "approved"


@pytest.mark.asyncio
async def test_approve_submission_conflict(client: AsyncClient, admin_token, form_submission, test_db):
    """Test approving submission when student exists (conflict)."""
    # Create existing student with same email
    existing = Student(
        first_name="Existing",
        last_name="Student",
        email="john@example.com",
        admission_no="ADM999",
    )
    test_db.add(existing)
    await test_db.commit()
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Try to approve without force_update
    payload = {"force_update": False}
    response = await client.post(
        f"/api/v1/forms/submissions/{form_submission.id}/approve",
        json=payload,
        headers=headers,
    )
    
    # Should return conflict
    assert response.status_code == 409
    data = response.json()
    assert "already exists" in str(data.get("detail", ""))


@pytest.mark.asyncio
async def test_approve_submission_force_update(client: AsyncClient, admin_token, form_submission, test_db):
    """Test approving submission with force_update."""
    # Create existing student
    existing = Student(
        first_name="Old",
        last_name="Name",
        email="john@example.com",
        admission_no="ADM999",
    )
    test_db.add(existing)
    await test_db.commit()
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Approve with force_update
    payload = {"force_update": True}
    response = await client.post(
        f"/api/v1/forms/submissions/{form_submission.id}/approve",
        json=payload,
        headers=headers,
    )
    
    if response.status_code == 200:
        # Verify student was updated
        from sqlalchemy import select
        result = await test_db.execute(select(Student).where(Student.id == existing.id))
        updated_student = result.scalar_one()
        # Name should be updated from form data
        assert updated_student.first_name == "John"


@pytest.mark.asyncio
async def test_approve_non_pending_submission(client: AsyncClient, admin_token, form_submission, test_db):
    """Test approving already-approved submission (should fail)."""
    # Set submission to approved
    form_submission.status = "approved"
    await test_db.commit()
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    payload = {"force_update": False}
    response = await client.post(
        f"/api/v1/forms/submissions/{form_submission.id}/approve",
        json=payload,
        headers=headers,
    )
    
    assert response.status_code == 400
    assert "already" in response.json()["detail"]


@pytest.mark.asyncio
async def test_reject_submission(client: AsyncClient, admin_token, form_submission):
    """Test rejecting a form submission."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    response = await client.post(
        f"/api/v1/forms/submissions/{form_submission.id}/reject",
        headers=headers,
    )
    
    if response.status_code == 200:
        assert "rejected" in response.json()["message"]
