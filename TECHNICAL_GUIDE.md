# Venn Enterprise Chat Server - Technical Guide

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture & Technology Stack](#architecture--technology-stack)
3. [Directory Structure](#directory-structure)
4. [Database Models & Schema](#database-models--schema)
5. [API Endpoints](#api-endpoints)
6. [WebSocket Implementation](#websocket-implementation)
7. [LLM Integration](#llm-integration)
8. [Snowflake Integration](#snowflake-integration)
9. [Authentication & Security](#authentication--security)
10. [Real-time Messaging](#real-time-messaging)
11. [Docker & Deployment](#docker--deployment)
12. [Testing & Examples](#testing--examples)
13. [Configuration Guide](#configuration-guide)
14. [Security Implementation](#security-implementation)
15. [System Data Flow](#system-data-flow)

---

## Project Overview

Venn is a sophisticated enterprise chat server application built with Python and FastAPI that combines real-time messaging with LLM-powered data querying capabilities. It's designed to be a Slack-like platform with integrated AI assistance for enterprise data analysis.

### Key Features

- **Enterprise Chat**: Multi-channel messaging with real-time updates
- **AI Integration**: Natural language to SQL conversion using OpenAI GPT-4
- **Enterprise Data**: Secure Snowflake database integration
- **Real-time Communication**: WebSocket-based live messaging
- **Security First**: JWT authentication with role-based access control
- **Containerized**: Docker-based deployment with multi-service architecture

---

## Architecture & Technology Stack

### High-Level Architecture

```
Venn Chat Server
├── FastAPI REST API Layer
├── WebSocket Real-time Communication
├── PostgreSQL Database (Primary)
├── Redis (Caching/Sessions)
├── Snowflake Integration (Enterprise Data)
├── OpenAI LLM Integration
└── Docker Containerization
```

### Technology Stack

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **Backend Framework** | FastAPI | 0.104.1 | REST API and WebSocket server |
| **Database** | PostgreSQL | 15 | Primary data storage |
| **Cache/Sessions** | Redis | 7 | Session management and caching |
| **ORM** | SQLAlchemy | 1.4.48 | Database abstraction layer |
| **Enterprise Data** | Snowflake | 3.5.0 | Data warehouse integration |
| **AI/LLM** | OpenAI + LangChain | 1.3.5 + 0.0.340 | Natural language processing |
| **Authentication** | JWT + bcrypt | - | Token-based authentication |
| **Containerization** | Docker Compose | - | Multi-service orchestration |

---

## Directory Structure

### Core Application Structure

```
venn/
├── main.py                 # Application entry point
├── config/
│   └── settings.py         # Configuration management
├── models/                 # Database models
│   ├── base.py            # Base model class
│   ├── user.py            # User model
│   ├── channel.py         # Channel and membership models
│   └── message.py         # Message and thread models
├── api/                   # REST API endpoints
│   ├── auth.py            # Authentication endpoints
│   ├── users.py           # User management
│   ├── channels.py        # Channel operations
│   ├── messages.py        # Message handling
│   └── threads.py         # Thread and LLM queries
├── core/                  # Core infrastructure
│   ├── database.py        # Database connection
│   ├── security.py        # Security utilities
│   └── websocket.py       # WebSocket manager
├── services/              # Business logic
│   └── auth.py            # Authentication service
├── llm/                   # AI integration
│   └── llm_handler.py     # LLM query processing
├── database/              # External connectors
│   └── snowflake_connector.py  # Snowflake integration
├── examples/              # Documentation and tests
│   ├── test_flow.py       # Integration tests
│   ├── simple_client.html # Web client
│   ├── quick_start.sh     # Setup script
│   └── setup_guide.md     # User documentation
├── docker-compose.yml     # Service orchestration
├── Dockerfile             # Application container
└── requirements.txt       # Python dependencies
```

### File Purposes and Responsibilities

#### `/main.py` - Application Entry Point
- FastAPI application initialization
- CORS configuration for cross-origin requests
- Database initialization on startup
- WebSocket and API route registration
- Health check endpoint setup

#### `/config/settings.py` - Configuration Management
- Centralized configuration using Pydantic settings
- Environment variable management
- Database connection strings
- JWT secrets and expiration times
- Snowflake credentials
- OpenAI API configuration

---

## Database Models & Schema

### Base Model (`/models/base.py`)

```python
class BaseModel:
    id: UUID                    # Primary key
    created_at: datetime        # Record creation timestamp
    updated_at: datetime        # Last modification timestamp
```

### User Model (`/models/user.py`)

```python
class User(BaseModel):
    email: str                  # Unique email address
    username: str               # Unique username
    hashed_password: str        # Bcrypt-hashed password
    full_name: str              # Display name
    is_active: bool             # Account status
    is_superuser: bool          # Admin privileges
    avatar_url: str             # Profile image URL
    status: str                 # Online/offline indicator
```

### Channel Models (`/models/channel.py`)

```python
class Channel(BaseModel):
    name: str                   # Channel name
    description: str            # Channel purpose
    is_private: bool            # Access control
    is_direct_message: bool     # 1-on-1 chat flag
    owner_id: UUID              # Channel creator
    topic: str                  # Current discussion topic

class ChannelMember(BaseModel):
    channel_id: UUID            # Channel reference
    user_id: UUID               # User reference
    role: str                   # Member permissions
    last_read_message_id: UUID  # Read status tracking
    notification_level: str     # Alert preferences
```

### Message Models (`/models/message.py`)

```python
class Message(BaseModel):
    channel_id: UUID            # Destination channel
    author_id: UUID             # Message sender
    thread_id: UUID             # Optional thread association
    parent_message_id: UUID     # Reply reference
    content: str                # Message text
    message_type: str           # text/llm_response/system/file
    is_edited: bool             # Edit status
    is_deleted: bool            # Delete status
    llm_context: dict           # AI query context
    llm_model_used: str         # Which AI model processed
    attachments: list           # File attachments
    reactions: dict             # User reactions
    mentions: list              # Tagged users

class Thread(BaseModel):
    channel_id: UUID            # Parent channel
    root_message_id: UUID       # Starting message
    title: str                  # Thread topic
    is_llm_enabled: bool        # AI queries allowed
    llm_context: dict           # Thread-specific AI context
    participant_count: int      # Active participants
    message_count: int          # Total messages
    allowed_databases: list     # Permitted data sources
    allowed_tables: list        # Accessible table list
```

### Database Schema SQL

```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    avatar_url TEXT,
    status VARCHAR(50) DEFAULT 'offline',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Channels table
CREATE TABLE channels (
    id UUID PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_private BOOLEAN DEFAULT FALSE,
    is_direct_message BOOLEAN DEFAULT FALSE,
    owner_id UUID REFERENCES users(id),
    topic TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Messages table
CREATE TABLE messages (
    id UUID PRIMARY KEY,
    channel_id UUID REFERENCES channels(id) NOT NULL,
    author_id UUID REFERENCES users(id) NOT NULL,
    thread_id UUID REFERENCES threads(id),
    parent_message_id UUID REFERENCES messages(id),
    content TEXT NOT NULL,
    message_type VARCHAR(50) DEFAULT 'text',
    is_edited BOOLEAN DEFAULT FALSE,
    is_deleted BOOLEAN DEFAULT FALSE,
    llm_context JSON,
    llm_model_used VARCHAR(100),
    attachments JSON,
    reactions JSON,
    mentions JSON,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Threads table
CREATE TABLE threads (
    id UUID PRIMARY KEY,
    channel_id UUID REFERENCES channels(id) NOT NULL,
    root_message_id UUID REFERENCES messages(id),
    title VARCHAR(255),
    is_llm_enabled BOOLEAN DEFAULT TRUE,
    llm_context JSON,
    participant_count INTEGER DEFAULT 0,
    message_count INTEGER DEFAULT 0,
    allowed_databases JSON,
    allowed_tables JSON,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Channel members table
CREATE TABLE channel_members (
    id UUID PRIMARY KEY,
    channel_id UUID REFERENCES channels(id) NOT NULL,
    user_id UUID REFERENCES users(id) NOT NULL,
    role VARCHAR(50) DEFAULT 'member',
    last_read_message_id UUID REFERENCES messages(id),
    notification_level VARCHAR(50) DEFAULT 'all',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);
```

---

## API Endpoints

### Authentication Endpoints (`/api/auth.py`)

#### POST `/api/v1/auth/register`
**Purpose**: Register a new user account

**Request Body**:
```json
{
    "email": "user@example.com",
    "username": "username",
    "password": "password",
    "full_name": "Full Name"
}
```

**Response**:
```json
{
    "id": "uuid",
    "email": "user@example.com",
    "username": "username",
    "full_name": "Full Name",
    "is_active": true
}
```

**Features**:
- Password strength validation
- Email uniqueness checking
- Automatic password hashing with bcrypt
- Account activation

#### POST `/api/v1/auth/login`
**Purpose**: Authenticate user and get JWT tokens

**Request**: Form data with username/password
```
username=user@example.com&password=password
```

**Response**:
```json
{
    "access_token": "jwt_token_here",
    "refresh_token": "refresh_token_here",
    "token_type": "bearer"
}
```

**Features**:
- Email/password validation
- JWT token generation
- Refresh token creation
- Session establishment

### User Endpoints (`/api/users.py`)

#### GET `/api/v1/users/me`
**Purpose**: Get current user information
**Authentication**: Bearer token required
**Response**: Current user object with profile data

#### PATCH `/api/v1/users/me`
**Purpose**: Update current user profile
**Authentication**: Bearer token required
**Request Body**: Partial user update object

#### GET `/api/v1/users/{user_id}`
**Purpose**: Get user by ID
**Authentication**: Bearer token required
**Response**: User object (public fields only)

### Channel Endpoints (`/api/channels.py`)

#### POST `/api/v1/channels/`
**Purpose**: Create a new channel

**Request Body**:
```json
{
    "name": "channel-name",
    "description": "Channel description",
    "is_private": false
}
```

**Features**:
- Automatic owner assignment
- Member initialization
- Channel validation

#### GET `/api/v1/channels/`
**Purpose**: List user's accessible channels
**Response**: Array of channel objects with membership info

#### POST `/api/v1/channels/{channel_id}/join`
**Purpose**: Join an existing channel
**Response**: Updated membership information

### Message Endpoints (`/api/messages.py`)

#### POST `/api/v1/messages/`
**Purpose**: Send a message to a channel

**Request Body**:
```json
{
    "channel_id": "uuid",
    "content": "Message content",
    "thread_id": "uuid (optional)",
    "mentions": ["user_id1", "user_id2"]
}
```

**Features**:
- Real-time WebSocket broadcasting
- Mention notification processing
- Thread association
- Message validation

#### GET `/api/v1/messages/channel/{channel_id}`
**Purpose**: Get channel message history
**Query Parameters**: 
- `limit`: Number of messages (default: 50)
- `before`: Message ID for pagination
**Response**: Array of message objects

### Thread Endpoints (`/api/threads.py`)

#### POST `/api/v1/threads/`
**Purpose**: Create a new thread with LLM capabilities

**Request Body**:
```json
{
    "channel_id": "uuid",
    "root_message_id": "uuid",
    "title": "Thread title",
    "is_llm_enabled": true,
    "allowed_tables": ["TABLE1", "TABLE2"]
}
```

#### POST `/api/v1/threads/{thread_id}/llm-query`
**Purpose**: Submit an LLM query for data analysis

**Request Body**:
```json
{
    "query": "How many users signed up last month?",
    "context": {"additional": "context"}
}
```

**Features**:
- Natural language processing
- SQL generation
- Background execution
- Real-time result delivery

---

## WebSocket Implementation

### Connection Manager (`/core/websocket.py`)

The WebSocket system manages real-time communication through a `ConnectionManager` class:

#### Key Responsibilities
- **Connection Tracking**: Maintains active connections per user
- **Channel Subscriptions**: Maps users to channels for targeted broadcasting
- **Message Broadcasting**: Sends messages to specific channels or users
- **Connection Lifecycle**: Handles connect, disconnect, and cleanup

#### WebSocket Events

**Client to Server Events**:
```json
// Join a channel for real-time updates
{
    "type": "join_channel",
    "channel_id": "uuid"
}

// Leave a channel
{
    "type": "leave_channel", 
    "channel_id": "uuid"
}

// Send typing indicator
{
    "type": "typing",
    "channel_id": "uuid",
    "is_typing": true
}

// Keep connection alive
{
    "type": "ping"
}
```

**Server to Client Events**:
```json
// New message broadcast
{
    "type": "new_message",
    "message": {
        "id": "uuid",
        "content": "Hello world",
        "author": {...},
        "timestamp": "2024-01-01T00:00:00Z"
    }
}

// LLM query response
{
    "type": "llm_response",
    "thread_id": "uuid",
    "message": {
        "query": "original query",
        "sql": "generated SQL",
        "results": [...],
        "execution_time": 1.23
    }
}

// Typing indicator
{
    "type": "typing_indicator",
    "channel_id": "uuid",
    "user_id": "uuid",
    "is_typing": true
}

// User status change
{
    "type": "user_status",
    "user_id": "uuid", 
    "status": "online"
}
```

### WebSocket Authentication
- Token-based authentication via URL parameter: `/ws/{token}`
- Token validation on connection establishment
- Automatic disconnection for invalid tokens
- User identification for message routing

---

## LLM Integration

### LLM Handler (`/llm/llm_handler.py`)

The LLM integration provides natural language to SQL conversion with enterprise security.

#### Key Components

**Query Processing Pipeline**:
1. **Input Validation**: Sanitize and validate user queries
2. **Context Building**: Gather schema information from allowed tables
3. **Prompt Construction**: Build safety-aware prompts for the LLM
4. **SQL Generation**: Use OpenAI GPT-4 to convert natural language to SQL
5. **Safety Validation**: Ensure generated SQL is read-only and safe
6. **Query Execution**: Run SQL against Snowflake with limits
7. **Result Formatting**: Format results for chat display
8. **Real-time Delivery**: Send results via WebSocket

#### Security Implementation

```python
def validate_query_safety(self, query: str) -> bool:
    """Validate that SQL query is safe for execution"""
    query_upper = query.strip().upper()
    
    # Must be SELECT only
    if not query_upper.startswith('SELECT'):
        return False
    
    # Block dangerous operations
    dangerous_patterns = [
        'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 
        'ALTER', 'TRUNCATE', 'MERGE', 'CALL', 'EXECUTE',
        'GRANT', 'REVOKE', 'BACKUP', 'RESTORE'
    ]
    
    for pattern in dangerous_patterns:
        if pattern in query_upper:
            return False
    
    return True
```

#### LLM Configuration

```python
# OpenAI Configuration
MODEL = "gpt-4-turbo-preview"
TEMPERATURE = 0.1  # Low temperature for consistent SQL generation
MAX_TOKENS = 2000
TIMEOUT = 30  # Maximum processing time

# Safety Prompts
SYSTEM_PROMPT = """
You are a SQL expert. Convert natural language queries to SQL.
CRITICAL RULES:
1. Only generate SELECT statements
2. Always include LIMIT clauses (max 1000 rows)
3. Use proper table aliases
4. Validate column names exist
5. Never use DROP, DELETE, UPDATE, INSERT, or other modifying operations
"""
```

---

## Snowflake Integration

### Snowflake Connector (`/database/snowflake_connector.py`)

The Snowflake integration provides secure, read-only access to enterprise data warehouses.

#### Key Features

**Security-First Design**:
- Read-only database connections
- Query validation before execution
- Automatic LIMIT clause injection
- Connection timeout enforcement
- Resource usage monitoring

**Schema Introspection**:
```python
async def get_table_schema(self, table_name: str) -> dict:
    """Get schema information for LLM context"""
    query = f"""
    SELECT 
        column_name,
        data_type,
        is_nullable,
        column_default,
        comment
    FROM information_schema.columns 
    WHERE table_name = '{table_name.upper()}'
    ORDER BY ordinal_position
    """
    return await self.execute_query(query)
```

**Query Execution**:
```python
async def execute_query(self, query: str, limit: int = 1000) -> dict:
    """Execute read-only query with safety checks"""
    # Validate query safety
    if not self.validate_query_safety(query):
        raise ValueError("Unsafe query detected")
    
    # Add LIMIT if not present
    if 'LIMIT' not in query.upper():
        query = f"{query} LIMIT {limit}"
    
    # Execute with timeout
    async with self.get_connection() as conn:
        result = await asyncio.wait_for(
            conn.execute(query),
            timeout=30
        )
        return self.format_results(result)
```

#### Connection Configuration

```python
# Recommended Snowflake setup
connection_params = {
    'account': 'your-account.region',
    'user': 'readonly_user',        # Read-only user
    'password': 'secure_password',
    'warehouse': 'COMPUTE_WH',
    'database': 'ANALYTICS_DB',
    'schema': 'PUBLIC',
    'role': 'READONLY_ROLE'         # Read-only role
}
```

---

## Authentication & Security

### JWT Implementation (`/core/security.py`)

#### Token Management

**Token Types**:
- **Access Token**: Short-lived (30 minutes) for API access
- **Refresh Token**: Long-lived (7 days) for token renewal

**Token Creation**:
```python
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=30))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.secret_key, algorithm="HS256")
```

**Password Security**:
```python
# Bcrypt configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
```

### Security Features

**API Security**:
- Bearer token authentication for all protected endpoints
- CORS middleware for cross-origin request control
- Request validation with Pydantic models
- Rate limiting capability (configurable)

**Database Security**:
- Read-only access for LLM queries
- SQL injection prevention with validation layers
- Query type restriction (SELECT only)
- Connection timeout and resource limits

**Enterprise Security**:
- Role-based access control for data sources
- Table-level permissions per thread
- Query audit logging for compliance
- Secure credential management via environment variables

---

## Real-time Messaging

### Message Flow Architecture

1. **Client sends message** via REST API (`POST /api/v1/messages/`)
2. **Message validation** and storage in PostgreSQL
3. **WebSocket broadcast** to all channel subscribers
4. **Real-time delivery** to connected clients
5. **Read receipt tracking** for message status

### Threading System

**Thread Creation**:
- Root messages can spawn discussion threads
- Thread-specific LLM context for data queries
- Separate message streams for threads vs channels
- Participant tracking for engagement metrics

**LLM Thread Processing**:
```python
async def process_llm_query(thread_id: str, query: str):
    # Get thread context and permissions
    thread = await get_thread(thread_id)
    allowed_tables = thread.allowed_tables
    
    # Generate SQL using LLM
    sql = await llm_handler.generate_sql(query, allowed_tables)
    
    # Execute safely on Snowflake
    results = await snowflake.execute_query(sql)
    
    # Broadcast results in real-time
    await websocket_manager.broadcast_to_thread(thread_id, {
        "type": "llm_response",
        "query": query,
        "sql": sql,
        "results": results
    })
```

### Typing Indicators

- Real-time typing status via WebSocket
- Channel-specific broadcasting (excludes sender)
- Automatic timeout handling (5 seconds)
- Debounced updates to prevent spam

---

## Docker & Deployment

### Multi-Service Architecture

#### Docker Compose Configuration

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: chatuser
      POSTGRES_PASSWORD: chatpass
      POSTGRES_DB: chatdb
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U chatuser -d chatdb"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  chat_server:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://chatuser:chatpass@postgres:5432/chatdb
      REDIS_URL: redis://redis:6379/0
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./.env:/app/.env
    command: python main.py

volumes:
  postgres_data:
  redis_data:
```

#### Dockerfile Configuration

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 chatuser && \
    chown -R chatuser:chatuser /app

USER chatuser

EXPOSE 8000

CMD ["python", "main.py"]
```

### Production Deployment

#### Environment Configuration

```bash
# Database Configuration
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/database
REDIS_URL=redis://host:6379/0

# Snowflake Configuration (Enterprise)
SNOWFLAKE_ACCOUNT=your-account.region
SNOWFLAKE_USER=readonly_user
SNOWFLAKE_PASSWORD=secure_password
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_DATABASE=ANALYTICS_DB
SNOWFLAKE_SCHEMA=PUBLIC
SNOWFLAKE_ROLE=READONLY_ROLE

# LLM Integration
OPENAI_API_KEY=sk-your-openai-key
LLM_MODEL=gpt-4-turbo-preview
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=2000

# Security Configuration
SECRET_KEY=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Application Settings
DEBUG=false
PORT=8000
CORS_ORIGINS=["http://localhost:3000", "https://your-domain.com"]
```

#### Production Considerations

**Health Monitoring**:
- Health check endpoints for all services
- Automatic service restart on failure
- Resource usage monitoring
- Log aggregation and monitoring

**Security Hardening**:
- Non-root container users
- Secret management with environment variables
- Network isolation between services
- TLS termination at load balancer

**Scaling Considerations**:
- Horizontal scaling with multiple chat_server instances
- Redis cluster for session distribution
- PostgreSQL read replicas for performance
- Load balancer configuration for WebSocket sticky sessions

---

## Testing & Examples

### Integration Test Suite (`/examples/test_flow.py`)

Complete end-to-end testing covering all major functionality:

```python
async def test_complete_workflow():
    """Test the complete chat and LLM workflow"""
    
    # 1. User Registration and Authentication
    user1 = await register_user("alice@example.com", "alice", "password")
    user2 = await register_user("bob@example.com", "bob", "password")
    
    # 2. Channel Creation and Management
    channel = await create_channel("data-analysis", "Channel for data queries")
    await join_channel(channel.id, user2.id)
    
    # 3. Basic Messaging
    message = await send_message(channel.id, user1.id, "Hello team!")
    assert_message_delivered(message)
    
    # 4. Thread Creation with LLM
    thread = await create_thread(
        channel.id, 
        message.id, 
        "Sales Analysis", 
        allowed_tables=["sales", "customers"]
    )
    
    # 5. LLM Query Processing
    query_result = await submit_llm_query(
        thread.id, 
        "How many sales did we have last month?"
    )
    
    # 6. WebSocket Real-time Communication
    async with websocket_connect(f"/ws/{user1.token}") as ws:
        # Send typing indicator
        await ws.send_json({
            "type": "typing",
            "channel_id": channel.id,
            "is_typing": True
        })
        
        # Verify real-time message delivery
        await send_message(channel.id, user2.id, "Real-time test")
        message_event = await ws.receive_json()
        assert message_event["type"] == "new_message"
```

### Web Client (`/examples/simple_client.html`)

A complete web interface demonstrating all features:

**HTML Structure**:
```html
<!DOCTYPE html>
<html>
<head>
    <title>Venn Chat Client</title>
    <style>/* Responsive CSS styles */</style>
</head>
<body>
    <div id="app">
        <div id="auth-section">
            <!-- Login/Register forms -->
        </div>
        <div id="chat-section" style="display: none;">
            <div id="sidebar">
                <!-- Channel list -->
            </div>
            <div id="main-chat">
                <!-- Message display -->
                <div id="message-input">
                    <!-- Message composition -->
                </div>
            </div>
            <div id="llm-panel">
                <!-- LLM query interface -->
            </div>
        </div>
    </div>
    
    <script>/* Full JavaScript implementation */</script>
</body>
</html>
```

**JavaScript Features**:
- User authentication and session management
- Real-time WebSocket connection handling
- Channel creation and messaging
- LLM query submission and result display
- Responsive UI updates
- Error handling and notifications

### Quick Start Script (`/examples/quick_start.sh`)

Automated deployment script for immediate setup:

```bash
#!/bin/bash

echo "🚀 Chat Server Quick Start"

# Docker validation
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed"
    exit 1
fi

# Environment setup
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    
    # Generate secure secret key
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    sed -i "s/your-secret-key/$SECRET_KEY/" .env
fi

# Service deployment
echo "🏗️ Building Docker images..."
docker-compose build

echo "🚀 Starting services..."
docker-compose up -d

# Health validation
echo "🏥 Checking service health..."
sleep 5

# PostgreSQL check
if docker-compose exec -T postgres pg_isready -U chatuser -d chatdb; then
    echo "✅ PostgreSQL is ready"
fi

# Redis check
if docker-compose exec -T redis redis-cli ping | grep -q PONG; then
    echo "✅ Redis is ready"
fi

# API check
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    echo "✅ API server is ready"
fi

echo "✨ Chat Server is running!"
echo "📍 API URL: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
```

---

## Configuration Guide

### Environment Variables

#### Required Configuration

```bash
# Database (Required)
DATABASE_URL=postgresql+asyncpg://chatuser:chatpass@localhost:5432/chatdb
REDIS_URL=redis://localhost:6379/0

# Security (Required)
SECRET_KEY=your-super-secret-key-minimum-32-characters
JWT_ALGORITHM=HS256

# Application (Required)
DEBUG=false
PORT=8000
```

#### Optional Enterprise Features

```bash
# Snowflake Integration (Optional)
SNOWFLAKE_ACCOUNT=your-account.region.snowflakecomputing.com
SNOWFLAKE_USER=analytics_user
SNOWFLAKE_PASSWORD=secure_password
SNOWFLAKE_WAREHOUSE=ANALYTICS_WH
SNOWFLAKE_DATABASE=ENTERPRISE_DB
SNOWFLAKE_SCHEMA=PUBLIC
SNOWFLAKE_ROLE=ANALYST_ROLE

# OpenAI LLM Integration (Optional)
OPENAI_API_KEY=sk-your-openai-api-key
LLM_MODEL=gpt-4-turbo-preview
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=2000
LLM_TIMEOUT=30

# Advanced Security (Optional)
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
CORS_ORIGINS=["http://localhost:3000", "https://your-app.com"]
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
```

### Development vs Production

#### Development Settings
```bash
DEBUG=true
LOG_LEVEL=DEBUG
DATABASE_URL=postgresql+asyncpg://chatuser:chatpass@localhost:5432/chatdb_dev
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]
```

#### Production Settings
```bash
DEBUG=false
LOG_LEVEL=INFO
DATABASE_URL=postgresql+asyncpg://user:pass@prod-db:5432/chatdb
CORS_ORIGINS=["https://your-production-domain.com"]
HTTPS_ONLY=true
SECURE_COOKIES=true
```

---

## Security Implementation

### Authentication Flow

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Database
    participant JWT

    Client->>API: POST /auth/register
    API->>Database: Store hashed password
    Database-->>API: User created
    API-->>Client: User profile

    Client->>API: POST /auth/login
    API->>Database: Verify credentials
    Database-->>API: User validated
    API->>JWT: Generate tokens
    JWT-->>API: Access + Refresh tokens
    API-->>Client: JWT tokens

    Client->>API: API requests with Bearer token
    API->>JWT: Validate token
    JWT-->>API: Token valid
    API-->>Client: Protected resource
```

### Data Access Control

```python
# Thread-level table permissions
class Thread:
    allowed_databases: list = ["ANALYTICS", "SALES"]
    allowed_tables: list = ["customers", "orders", "products"]

# Query validation before execution
def validate_table_access(query: str, allowed_tables: list) -> bool:
    # Extract table names from SQL
    tables_in_query = extract_table_names(query)
    
    # Verify all tables are allowed
    for table in tables_in_query:
        if table.lower() not in [t.lower() for t in allowed_tables]:
            return False
    
    return True
```

### Audit Logging

```python
# LLM query audit log
@audit_log
async def execute_llm_query(user_id: str, thread_id: str, query: str):
    log_entry = {
        "timestamp": datetime.utcnow(),
        "user_id": user_id,
        "thread_id": thread_id,
        "original_query": query,
        "generated_sql": None,
        "execution_time": None,
        "result_count": None,
        "status": "started"
    }
    
    try:
        # Process query...
        log_entry.update({
            "generated_sql": sql,
            "execution_time": execution_time,
            "result_count": len(results),
            "status": "completed"
        })
    except Exception as e:
        log_entry.update({
            "error": str(e),
            "status": "failed"
        })
    finally:
        await audit_logger.log(log_entry)
```

---

## System Data Flow

### Complete Message Flow

```mermaid
graph TD
    A[User Types Message] --> B[REST API /messages]
    B --> C[Validate & Store in PostgreSQL]
    C --> D[WebSocket Manager]
    D --> E[Broadcast to Channel Members]
    E --> F[Real-time Delivery to Clients]
    
    G[User Types LLM Query] --> H[REST API /threads/llm-query]
    H --> I[LLM Handler]
    I --> J[Generate SQL with OpenAI]
    J --> K[Validate SQL Safety]
    K --> L[Execute on Snowflake]
    L --> M[Format Results]
    M --> N[WebSocket Broadcast]
    N --> O[Real-time Result Display]
```

### Enterprise Data Pipeline

```mermaid
graph LR
    A[Natural Language Query] --> B[Schema Context Building]
    B --> C[LLM Prompt Construction]
    C --> D[OpenAI GPT-4 Processing]
    D --> E[SQL Generation]
    E --> F[Safety Validation]
    F --> G{Query Safe?}
    G -->|Yes| H[Snowflake Execution]
    G -->|No| I[Reject Query]
    H --> J[Result Formatting]
    J --> K[Real-time Delivery]
    I --> K
```

---

## Conclusion

The Venn Enterprise Chat Server represents a comprehensive solution for modern workplace communication with integrated AI capabilities. By combining traditional chat functionality with enterprise data analytics, it provides organizations with a unified platform for both collaboration and data-driven decision making.

### Key Achievements

1. **Scalable Architecture**: Multi-service Docker deployment with health monitoring
2. **Enterprise Security**: JWT authentication with role-based data access
3. **Real-time Communication**: WebSocket-based messaging with typing indicators
4. **AI Integration**: Natural language to SQL conversion with safety validation
5. **Enterprise Data Access**: Secure Snowflake integration with read-only permissions
6. **Comprehensive Testing**: Full test suite with examples and documentation

### Future Enhancements

- **Mobile Application**: React Native or Flutter mobile client
- **Advanced Analytics**: Enhanced LLM capabilities with data visualization
- **Enterprise SSO**: SAML/OAuth integration for corporate authentication
- **Horizontal Scaling**: Kubernetes deployment with auto-scaling
- **Advanced Security**: End-to-end encryption for sensitive communications
- **Integration APIs**: Slack, Microsoft Teams, and other platform connectors

This technical guide provides the foundation for understanding, deploying, and extending the Venn chat server for enterprise use cases.

---

*Generated on: January 2024*  
*Version: 1.0.0*  
*Documentation for Venn Enterprise Chat Server*