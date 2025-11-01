#!/usr/bin/env python3
"""Development script to seed memory with sample data."""

import asyncio
import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.core.db import async_session_maker, MemoryItem
from app.routers.memory import generate_placeholder_embedding

SAMPLE_MEMORIES = [
    {
        "text": "Remember to pick up groceries: milk, bread, eggs, and coffee",
        "tags": ["shopping", "groceries", "reminder"],
        "speaker_id": "user"
    },
    {
        "text": "Meeting with the team tomorrow at 3 PM to discuss the project roadmap",
        "tags": ["meeting", "work", "team"],
        "speaker_id": "user"
    },
    {
        "text": "Python is a high-level programming language with dynamic semantics",
        "tags": ["python", "programming", "knowledge"],
        "speaker_id": "assistant"
    },
    {
        "text": "FastAPI is a modern web framework for building APIs with Python",
        "tags": ["fastapi", "python", "api", "framework"],
        "speaker_id": "assistant"
    },
    {
        "text": "PostgreSQL with pgvector extension enables vector similarity search",
        "tags": ["postgres", "database", "vector", "search"],
        "speaker_id": "assistant"
    },
    {
        "text": "Docker Compose helps orchestrate multi-container applications",
        "tags": ["docker", "containers", "devops"],
        "speaker_id": "assistant"
    },
    {
        "text": "The weather is nice today, perfect for a walk in the park",
        "tags": ["weather", "outdoor", "personal"],
        "speaker_id": "user"
    },
    {
        "text": "Machine learning models require training data and validation",
        "tags": ["ml", "ai", "training", "data"],
        "speaker_id": "assistant"
    }
]


async def seed_memory():
    """Seed the database with sample memory items."""
    print("🌱 Seeding memory database with sample data...")
    
    async with async_session_maker() as session:
        try:
            # Clear existing data (optional)
            # await session.execute(text("DELETE FROM memory_items"))
            
            for i, memory_data in enumerate(SAMPLE_MEMORIES):
                print(f"  Adding memory {i + 1}: {memory_data['text'][:50]}...")
                
                # Generate embedding
                embedding = generate_placeholder_embedding(memory_data['text'])
                
                # Create memory item
                memory_item = MemoryItem(
                    text=memory_data['text'],
                    tags=memory_data['tags'],
                    speaker_id=memory_data['speaker_id'],
                    ts=datetime.utcnow(),
                    embedding=embedding
                )
                
                session.add(memory_item)
            
            await session.commit()
            print(f"✅ Successfully seeded {len(SAMPLE_MEMORIES)} memory items!")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Failed to seed memory: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(seed_memory())