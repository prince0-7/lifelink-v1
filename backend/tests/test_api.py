import pytest
from httpx import AsyncClient
from main import app
from models import Memory
import mongomock
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

@pytest.fixture
async def client():
    """Create test client"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
async def mock_db():
    """Setup mock database"""
    client = mongomock.MongoClient()
    db = client.db
    await init_beanie(database=db, document_models=[Memory])
    yield db

@pytest.mark.asyncio
async def test_health_check(client):
    """Test health check endpoint"""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data

@pytest.mark.asyncio
async def test_create_memory(client, mock_db):
    """Test creating a new memory"""
    memory_data = {
        "text": "Test memory",
        "mood": "Happy",
        "tags": ["test", "happy"]
    }
    
    response = await client.post("/memories/", json=memory_data)
    assert response.status_code == 200
    data = response.json()
    assert data["text"] == "Test memory"
    assert data["mood"] == "Happy"
    assert "id" in data

@pytest.mark.asyncio
async def test_list_memories(client, mock_db):
    """Test listing all memories"""
    response = await client.get("/memories/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

@pytest.mark.asyncio
async def test_update_memory(client, mock_db):
    """Test updating a memory"""
    # First create a memory
    memory_data = {
        "text": "Original memory",
        "mood": "Happy",
        "tags": ["test"]
    }
    create_response = await client.post("/memories/", json=memory_data)
    memory_id = create_response.json()["id"]
    
    # Update it
    update_data = {
        "text": "Updated memory",
        "mood": "Sad"
    }
    response = await client.put(f"/memories/{memory_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["text"] == "Updated memory"
    assert data["mood"] == "Sad"

@pytest.mark.asyncio
async def test_delete_memory(client, mock_db):
    """Test deleting a memory"""
    # First create a memory
    memory_data = {
        "text": "Memory to delete",
        "mood": "Neutral",
        "tags": ["test"]
    }
    create_response = await client.post("/memories/", json=memory_data)
    memory_id = create_response.json()["id"]
    
    # Delete it
    response = await client.delete(f"/memories/{memory_id}")
    assert response.status_code == 204
