# VoiceDebate Database Design Document

## Overview
This document specifies the data persistence strategy for the VoiceDebate application.

## Database Selection
- SQLite for desktop deployment
- PostgreSQL for web deployment
- Supports easy migration path between the two

## Schema Design

### Users Table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

### Debate Sessions Table
```sql
CREATE TABLE debate_sessions (
    id UUID PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    topic TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    status VARCHAR(20) NOT NULL -- active, completed, archived
);
```

### Transcriptions Table
```sql
CREATE TABLE transcriptions (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES debate_sessions(id),
    speaker_id UUID REFERENCES users(id),
    content TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    confidence FLOAT,
    is_final BOOLEAN DEFAULT false
);
```

### Audio Segments Table
```sql
CREATE TABLE audio_segments (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES debate_sessions(id),
    speaker_id UUID REFERENCES users(id),
    audio_data BYTEA NOT NULL,
    duration INTEGER NOT NULL, -- in milliseconds
    timestamp TIMESTAMP NOT NULL
);
```

## Data Flow
1. User Authentication
   - Username/password verification
   - Session token management
   
2. Debate Session Flow
   - Create new session
   - Real-time transcription storage
   - Audio segment archival (optional)
   
3. Retrieval Patterns
   - Load user debate history
   - Fetch session transcripts
   - Stream audio playback

## Performance Considerations

### Indexing Strategy
```sql
CREATE INDEX idx_transcriptions_session ON transcriptions(session_id);
CREATE INDEX idx_transcriptions_speaker ON transcriptions(speaker_id);
CREATE INDEX idx_audio_session ON audio_segments(session_id);
CREATE INDEX idx_debates_user ON debate_sessions(created_by);
```

### Caching Strategy
- In-memory caching for active debate sessions
- Cache transcription results during active debates
- LRU cache for frequently accessed historical sessions

### Data Retention
- Transcriptions: Permanent storage
- Audio segments: Configurable retention period
- Session metadata: Permanent storage

## Backup and Recovery
1. Regular database backups
2. Point-in-time recovery capability
3. Transaction logging
4. Automated backup verification

## Migration Strategy
1. Version-controlled schema
2. Forward-only migrations
3. Automated migration testing
4. Rollback procedures
