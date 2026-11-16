from copy import deepcopy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src import app


@pytest.fixture
def client():
    with TestClient(app.app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def restore_activities():
    original_activities = deepcopy(app.activities)
    yield
    app.activities.clear()
    app.activities.update(original_activities)


def test_root_redirects_to_static_index(client):
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_get_activities_returns_all_activities(client):
    # Arrange
    expected_activities = deepcopy(app.activities)

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected_activities


def test_signup_adds_student_to_activity(client):
    # Arrange
    activity_name = "Chess Club"
    email = "student@mergington.edu"
    signup_url = f"/activities/{quote(activity_name, safe='')}/signup"

    # Act
    response = client.post(signup_url, params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert email in app.activities[activity_name]["participants"]


def test_signup_rejects_duplicate_student(client):
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"
    signup_url = f"/activities/{quote(activity_name, safe='')}/signup"

    # Act
    response = client.post(signup_url, params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json() == {"detail": "Student already signed up for this activity"}


def test_signup_rejects_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Club"
    signup_url = f"/activities/{quote(activity_name, safe='')}/signup"

    # Act
    response = client.post(signup_url, params={"email": "student@mergington.edu"})

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_removes_student_from_activity(client):
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"
    signup_url = f"/activities/{quote(activity_name, safe='')}/signup"

    # Act
    response = client.delete(signup_url, params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {activity_name}"}
    assert email not in app.activities[activity_name]["participants"]


def test_unregister_rejects_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Club"
    signup_url = f"/activities/{quote(activity_name, safe='')}/signup"

    # Act
    response = client.delete(signup_url, params={"email": "student@mergington.edu"})

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_rejects_student_not_signed_up(client):
    # Arrange
    activity_name = "Chess Club"
    signup_url = f"/activities/{quote(activity_name, safe='')}/signup"

    # Act
    response = client.delete(
        signup_url,
        params={"email": "student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Student is not signed up for this activity"}
