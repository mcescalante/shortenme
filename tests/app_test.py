import pytest
from shortenme.app import app, init_db

@pytest.fixture
def client():
    app.config["TESTING"] = True

    # Setup database - run schema to clear out data and recreate table
    runner = app.test_cli_runner()
    runner.invoke(init_db)

    yield app.test_client()

    # Teardown

def test_index(client):
    """Test that the index returns HTML with status 200"""
    response = client.get("/", content_type="html/text")
    assert response.status_code == 200


def test_analytics_page(client):
    """Test that the analytics page returns HTML with status 200"""
    response = client.get("/analytics/", content_type="html/text")
    assert response.status_code == 200 


def test_api_create_shorturl_random(client):
    """Ensure that random short URLs can be created by only providing a URL"""
    response = client.post('/api/create', json={
        "url": "google.com"
    })
    assert response.status_code == 200
    assert response.json["result"] == "success"
    assert "short_url" and "url" in response.json


def test_api_create_shorturl(client):
    """Ensure that short URLs can be created with custom short url and expiry"""
    response = client.post('/api/create', json={
        "url": "google.com",
        "shorturl": "short7",
        "expiry": "2022-02-14T23:35:00"
    })
    assert response.status_code == 200
    assert response.json["result"] == "success"
    assert response.json["short_url"] == "short7"
    assert "url" in response.json


def test_api_reject_create_duplicate(client):
    """Ensure that duplicates cannot be inserted"""
    client.post('/api/create', json={
        "url": "google.com",
        "shorturl": "short7",
        "expiry": "2022-02-14T23:35:00"
    })
    response = client.post('/api/create', json={
        "url": "google.com",
        "shorturl": "short7",
        "expiry": "2022-02-14T23:35:00"
    })
    assert response.status_code == 409


def test_api_create_bad_payload_failure(client):
    """Ensure that payloads missing url or other data errors fail"""
    response = client.post('/api/create', json={})
    assert response.status_code == 400
    assert "error" in response.json


def test_api_delete_shorturl(client):
    """Ensure that URLs can be deleted"""
    client.post('/api/create', json={
        "url": "google.com",
        "shorturl": "short7",
        "expiry": "2022-02-14T23:35:00"
    })
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


def test_api_analytics(client):
    """Ensure that analytics for a given short URL can be retrieved"""
    client.post('/api/create', json={
        "url": "google.com",
        "shorturl": "short7",
        "expiry": "2022-02-14T23:35:00"
    })
    response = client.get('/api/analytics/short7')
    assert response.status_code == 200
    assert response.json["source_url"] == "http://google.com"
    assert response.json["views"] == 0
    assert "created_utc" and "expiry" in response.json
