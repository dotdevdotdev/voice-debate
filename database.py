"""Database management for VoiceDebate."""

import asyncio
import logging
from pathlib import Path
from typing import Optional, Union, Any
import aiosqlite
import asyncpg
from .config import config

logger = logging.getLogger(__name__)

class Database:
    """Database connection manager."""
    
    def __init__(self):
        self.conn: Optional[Union[aiosqlite.Connection, asyncpg.Connection]] = None
        self._lock = asyncio.Lock()
        
    async def connect(self):
        """Connect to the database."""
        async with self._lock:
            if self.conn is not None:
                return
            
            if config.database.type == "sqlite":
                db_path = Path(config.data_dir) / config.database.database
                self.conn = await aiosqlite.connect(db_path)
                await self.conn.execute("PRAGMA foreign_keys = ON")
            else:
                self.conn = await asyncpg.connect(
                    host=config.database.host,
                    port=config.database.port,
                    user=config.database.username,
                    password=config.database.password,
                    database=config.database.database
                )
    
    async def disconnect(self):
        """Disconnect from the database."""
        async with self._lock:
            if self.conn is not None:
                await self.conn.close()
                self.conn = None
    
    async def execute(self, query: str, *args) -> Any:
        """Execute a query."""
        if self.conn is None:
            await self.connect()
        
        if isinstance(self.conn, aiosqlite.Connection):
            async with self.conn.execute(query, args) as cursor:
                await self.conn.commit()
                return cursor.rowcount
        else:
            return await self.conn.execute(query, *args)
    
    async def fetch_one(self, query: str, *args) -> Optional[dict]:
        """Fetch a single row."""
        if self.conn is None:
            await self.connect()
        
        if isinstance(self.conn, aiosqlite.Connection):
            async with self.conn.execute(query, args) as cursor:
                row = await cursor.fetchone()
                if row is None:
                    return None
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
        else:
            row = await self.conn.fetchrow(query, *args)
            return dict(row) if row else None
    
    async def fetch_all(self, query: str, *args) -> list[dict]:
        """Fetch all rows."""
        if self.conn is None:
            await self.connect()
        
        if isinstance(self.conn, aiosqlite.Connection):
            async with self.conn.execute(query, args) as cursor:
                rows = await cursor.fetchall()
                if not rows:
                    return []
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
        else:
            rows = await self.conn.fetch(query, *args)
            return [dict(row) for row in rows]

    async def initialize(self):
        """Initialize the database schema."""
        await self.connect()
        
        # Users table
        await self.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Debate sessions table
        await self.execute("""
            CREATE TABLE IF NOT EXISTS debate_sessions (
                id UUID PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                topic TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                created_by UUID REFERENCES users(id),
                status VARCHAR(20) NOT NULL
            )
        """)
        
        # Transcriptions table
        await self.execute("""
            CREATE TABLE IF NOT EXISTS transcriptions (
                id UUID PRIMARY KEY,
                session_id UUID REFERENCES debate_sessions(id),
                speaker_id UUID REFERENCES users(id),
                content TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                confidence FLOAT,
                is_final BOOLEAN DEFAULT false
            )
        """)
        
        # Audio segments table
        await self.execute("""
            CREATE TABLE IF NOT EXISTS audio_segments (
                id UUID PRIMARY KEY,
                session_id UUID REFERENCES debate_sessions(id),
                speaker_id UUID REFERENCES users(id),
                audio_data BYTEA NOT NULL,
                duration INTEGER NOT NULL,
                timestamp TIMESTAMP NOT NULL
            )
        """)
        
        # Create indexes
        await self.execute("CREATE INDEX IF NOT EXISTS idx_transcriptions_session ON transcriptions(session_id)")
        await self.execute("CREATE INDEX IF NOT EXISTS idx_transcriptions_speaker ON transcriptions(speaker_id)")
        await self.execute("CREATE INDEX IF NOT EXISTS idx_audio_session ON audio_segments(session_id)")
        await self.execute("CREATE INDEX IF NOT EXISTS idx_debates_user ON debate_sessions(created_by)")

# Global database instance
db = Database()
