#!/usr/bin/env python3
"""
Simple script to view MongoDB data for Lifelink
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import json

async def view_data():
    # Connect to MongoDB
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["lifelink_db"]
    
    print("=" * 60)
    print("LIFELINK MONGODB DATA VIEWER")
    print("=" * 60)
    
    # Show collections
    collections = await db.list_collection_names()
    print(f"\nCollections in database: {collections}")
    
    # View memories
    print("\n--- MEMORIES ---")
    memories_collection = db["memories"]
    
    # Count total memories
    total = await memories_collection.count_documents({})
    print(f"Total memories: {total}")
    
    # Show recent memories
    print("\nRecent 5 memories:")
    async for memory in memories_collection.find().sort("date", -1).limit(5):
        print(f"\n[{memory.get('date', 'No date')}]")
        print(f"ID: {memory['_id']}")
        print(f"Text: {memory.get('text', 'No text')[:100]}...")
        print(f"Mood: {memory.get('mood', 'Unknown')} (Detected: {memory.get('detected_mood', 'N/A')})")
        print(f"Tags: {memory.get('tags', [])}")
        print(f"AI Response: {memory.get('ai_response', 'None')[:100]}...")
    
    # Show mood distribution
    print("\n--- MOOD DISTRIBUTION ---")
    pipeline = [
        {"$group": {"_id": "$mood", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    async for result in memories_collection.aggregate(pipeline):
        print(f"{result['_id']}: {result['count']} memories")
    
    # Show tag distribution
    print("\n--- TOP TAGS ---")
    pipeline = [
        {"$unwind": "$tags"},
        {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    async for result in memories_collection.aggregate(pipeline):
        print(f"{result['_id']}: {result['count']} times")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(view_data())
