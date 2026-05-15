import asyncio

import httpx
from motor.motor_asyncio import AsyncIOMotorClient


async def test_mongodb():
    """Test MongoDB connection."""
    try:
        client = AsyncIOMotorClient(
            "mongodb://localhost:27017",
            serverSelectionTimeoutMS=3000,
        )
        await client.admin.command("ping")
        print("MongoDB connection successful")
        return True
    except Exception as e:
        print(f"MongoDB connection failed: {e}")
        return False


async def test_api():
    """Test API endpoints."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health")
            if response.status_code == 200:
                print("API health check successful")
                print(f"   Response: {response.json()}")
            else:
                print(f"API health check failed: {response.status_code}")

            test_memory = {
                "text": "This is a test memory",
                "mood": "Happy",
                "tags": ["test"],
            }
            response = await client.post(
                "http://localhost:8000/memories/",
                json=test_memory,
            )
            if response.status_code == 200:
                print("Memory creation successful")
                memory_id = response.json().get("id")
                print(f"   Created memory ID: {memory_id}")

                response = await client.get("http://localhost:8000/memories/")
                if response.status_code == 200:
                    print("Memory retrieval successful")
                    print(f"   Total memories: {len(response.json())}")
            else:
                print(f"Memory creation failed: {response.status_code}")
                print(f"   Error: {response.text}")

    except httpx.ConnectError:
        print("Cannot connect to API. Make sure the backend is running on http://localhost:8000")
    except Exception as e:
        print(f"API test failed: {e}")


async def main():
    print("Testing Lifelink Backend...\n")

    await test_mongodb()
    await test_api()

    print("\nTest complete!")


if __name__ == "__main__":
    asyncio.run(main())
