import pytest
from fastapi.testclient import TestClient
from pymongo import MongoClient

from config import settings
from main import app


@pytest.fixture(scope="session")
def mongo():
    """Create a sync Mongo client for test cleanup."""
    mongo = MongoClient(settings.mongodb_url)
    mongo.drop_database(settings.database_name)
    yield mongo
    mongo.drop_database(settings.database_name)
    mongo.close()


@pytest.fixture(scope="session")
def client(mongo):
    """Create a sync FastAPI test client for the test session."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def clean_database(mongo):
    """Keep tests isolated while preserving the app lifespan event loop."""
    db = mongo[settings.database_name]
    for collection_name in db.list_collection_names():
        db[collection_name].delete_many({})


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_create_memory(client):
    memory_data = {
        "text": "Test memory",
        "mood": "Happy",
        "tags": ["test", "happy"],
    }

    response = client.post("/memories/", json=memory_data)
    assert response.status_code == 200
    data = response.json()
    assert data["text"] == "Test memory"
    assert data["mood"] == "Happy"
    assert "id" in data


def test_list_memories(client):
    response = client.get("/memories/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_update_memory(client):
    memory_data = {
        "text": "Original memory",
        "mood": "Happy",
        "tags": ["test"],
    }
    create_response = client.post("/memories/", json=memory_data)
    memory_id = create_response.json()["id"]

    update_data = {
        "text": "Updated memory",
        "mood": "Sad",
    }
    response = client.put(f"/memories/{memory_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["text"] == "Updated memory"
    assert data["mood"] == "Sad"


def test_delete_memory(client):
    memory_data = {
        "text": "Memory to delete",
        "mood": "Neutral",
        "tags": ["test"],
    }
    create_response = client.post("/memories/", json=memory_data)
    memory_id = create_response.json()["id"]

    response = client.delete(f"/memories/{memory_id}")
    assert response.status_code == 204
