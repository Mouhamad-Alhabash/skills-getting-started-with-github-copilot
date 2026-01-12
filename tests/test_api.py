"""
Tests for the High School Management System API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset the activities data before each test"""
    from src.app import activities

    # Store original data
    original_activities = activities.copy()

    # Reset to initial state
    activities.clear()
    activities.update({
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        }
    })

    yield

    # Restore original data
    activities.clear()
    activities.update(original_activities)


class TestRootEndpoint:
    """Test the root endpoint"""

    def test_root_redirect(self, client):
        """Test that root endpoint redirects to static/index.html"""
        response = client.get("/")
        assert response.status_code == 200
        assert response.url.path == "/static/index.html"


class TestActivitiesEndpoint:
    """Test the activities endpoints"""

    def test_get_activities(self, client):
        """Test getting all activities"""
        response = client.get("/activities")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data

        # Check structure of activity data
        chess_club = data["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)

    def test_get_activities_has_correct_data(self, client):
        """Test that activities contain the expected data"""
        response = client.get("/activities")
        data = response.json()

        chess_club = data["Chess Club"]
        assert chess_club["description"] == "Learn strategies and compete in chess tournaments"
        assert chess_club["schedule"] == "Fridays, 3:30 PM - 5:00 PM"
        assert chess_club["max_participants"] == 12
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]


class TestSignupEndpoint:
    """Test the signup endpoint"""

    def test_signup_successful(self, client):
        """Test successful signup for an activity"""
        response = client.post("/activities/Chess%20Club/signup?email=test@mergington.edu")
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert "Signed up test@mergington.edu for Chess Club" in data["message"]

        # Verify the participant was added
        response = client.get("/activities")
        activities = response.json()
        assert "test@mergington.edu" in activities["Chess Club"]["participants"]

    def test_signup_activity_not_found(self, client):
        """Test signup for non-existent activity"""
        response = client.post("/activities/NonExistent/signup?email=test@mergington.edu")
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data
        assert data["detail"] == "Activity not found"

    def test_signup_already_signed_up(self, client):
        """Test signup when student is already signed up"""
        # First signup
        client.post("/activities/Chess%20Club/signup?email=test@mergington.edu")

        # Try to signup again
        response = client.post("/activities/Chess%20Club/signup?email=test@mergington.edu")
        assert response.status_code == 400

        data = response.json()
        assert "detail" in data
        assert data["detail"] == "Student already signed up for this activity"


class TestUnregisterEndpoint:
    """Test the unregister endpoint"""

    def test_unregister_successful(self, client):
        """Test successful unregister from an activity"""
        # First add a participant
        client.post("/activities/Chess%20Club/signup?email=test@mergington.edu")

        # Now unregister
        response = client.delete("/activities/Chess%20Club/unregister?email=test@mergington.edu")
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert "Unregistered test@mergington.edu from Chess Club" in data["message"]

        # Verify the participant was removed
        response = client.get("/activities")
        activities = response.json()
        assert "test@mergington.edu" not in activities["Chess Club"]["participants"]

    def test_unregister_activity_not_found(self, client):
        """Test unregister from non-existent activity"""
        response = client.delete("/activities/NonExistent/unregister?email=test@mergington.edu")
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data
        assert data["detail"] == "Activity not found"

    def test_unregister_not_signed_up(self, client):
        """Test unregister when student is not signed up"""
        response = client.delete("/activities/Chess%20Club/unregister?email=notsignedup@mergington.edu")
        assert response.status_code == 400

        data = response.json()
        assert "detail" in data
        assert data["detail"] == "Student is not signed up for this activity"