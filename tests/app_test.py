import pytest
import os
from shortenme.app import app, init_db

def setup_module(module):
    """ setup any state specific to the execution of the given module."""
    init_db()


def teardown_module(module):
    """ teardown any state that was previously setup with a setup_module
    method.
    """
    os.remove('app.db')


@pytest.fixture
def client():
    app.config["TESTING"] = True
  
    yield app.test_client()


def test_index(client):
    response = client.get("/", content_type="html/text")
    assert response.status_code == 200


def test_api_create_shorturl(client):
    """Ensure that short URLs can be created"""
    response = client.post('/api/create', json={
        "url": "google.com",
        "shorturl": "short7",
        "expiry": "2022-02-14T23:35:00"
    })
    assert response.status_code == 200
    assert response.json["result"] == "success"


def test_api_reject_create_duplicate(client):
    """Ensure that duplicates cannot be inserted"""
    response = client.post('/api/create', json={
        "url": "google.com",
        "shorturl": "short7",
        "expiry": "2022-02-14T23:35:00"
    })
    assert response.status_code == 409


def test_api_delete_shorturl(client):
    """Ensure that URLs can be deleted"""
    response = client.delete('/api/delete', json={
        "shorturl": "short7"
    })
    assert response.status_code == 200
    assert response.json["deleted"] == "success"

def test_api_delete_failure(client):
    """Ensure error response on a deletion of URL that does not exist"""
    response = client.delete('/api/delete', json={
        "shorturl": "short7"
    })
    assert response.status_code == 404
    assert "error" in response.json