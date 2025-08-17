# Venn - Enterprise Slack-like Application with LLM Integration

A Python-based chat server with real-time messaging, threads, and LLM-powered data querying capabilities for enterprise environments.

## Features

- **Real-time Chat**: WebSocket-based real-time messaging
- **Channels & Threads**: Organized conversations with threading support
- **LLM Integration**: AI-powered responses in threads
- **Snowflake Integration**: Secure, read-only access to enterprise data
- **Enterprise Security**: JWT authentication, role-based access control
- **Data Query Assistant**: Natural language to SQL conversion with safety checks

## Architecture

```
chat_server/
├── api/              # REST API endpoints
├── models/           # SQLAlchemy data models
├── services/         # Business logic services
├── core/             # Core utilities (auth, database, websocket)
├── llm/              # LLM integration and handlers
├── database/         # Database connectors (Snowflake)
├── config/           # Configuration management
└── main.py           # FastAPI application entry point
```

## Setup Instructions

### 1. Prerequisites

- Python 3.9+
- PostgreSQL database
- Redis server
- Snowflake account (for data querying features)
- OpenAI API key (for LLM features)

### 2. Installation

```bash
# Clone the repository
cd chat_server

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Key configuration variables:
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `SNOWFLAKE_*`: Snowflake credentials (read-only user recommended)
- `OPENAI_API_KEY`: OpenAI API key for LLM features
- `SECRET_KEY`: Secret key for JWT tokens (generate a strong random key)

### 4. Database Setup

The application will automatically create tables on startup. Ensure your PostgreSQL database exists:

```sql
CREATE DATABASE chatdb;
```

### 5. Running the Server

```bash
# Development mode
python main.py

# Production mode with uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get tokens

### Users
- `GET /api/v1/users/me` - Get current user info
- `PATCH /api/v1/users/me` - Update current user
- `GET /api/v1/users/{user_id}` - Get user by ID

### Channels
- `POST /api/v1/channels/` - Create channel
- `GET /api/v1/channels/` - List user's channels
- `POST /api/v1/channels/{channel_id}/join` - Join channel

### Messages
- `POST /api/v1/messages/` - Send message
- `GET /api/v1/messages/channel/{channel_id}` - Get channel messages

### Threads
- `POST /api/v1/threads/` - Create thread
- `POST /api/v1/threads/{thread_id}/llm-query` - Execute LLM query
- `GET /api/v1/threads/{thread_id}/messages` - Get thread messages

### WebSocket
- `WS /ws/{token}` - WebSocket connection for real-time updates

## WebSocket Events

### Client to Server
- `join_channel` - Join a channel
- `leave_channel` - Leave a channel
- `typing` - Send typing indicator
- `ping` - Keep connection alive

### Server to Client
- `new_message` - New message in channel
- `typing_indicator` - User typing status
- `user_status` - User online/offline status
- `llm_response` - LLM query response

## LLM Data Query Features

### How It Works

1. Users can enable LLM in threads
2. Natural language queries are converted to SQL
3. Only SELECT queries are allowed (read-only)
4. Results are formatted and returned in the thread

### Security Features

- Read-only Snowflake user recommended
- SQL injection prevention
- Query validation before execution
- Configurable table access per thread
- Result size limits

### Example Usage

In a thread with LLM enabled:
```
User: "Show me the top 10 customers by revenue last month"
LLM: [Generates and executes SQL, returns formatted results]
```

## Security Considerations

1. **Database Access**: Use a read-only Snowflake role
2. **Query Limits**: Automatic LIMIT clauses added to queries
3. **Authentication**: JWT-based with refresh tokens
4. **WebSocket Security**: Token-based authentication required
5. **Rate Limiting**: Configurable per-minute limits

## Development

### Running Tests

```bash
pytest tests/
```

### Database Migrations

Using Alembic for migrations:

```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head
```

## Deployment Considerations

1. Use environment variables for sensitive configuration
2. Set up SSL/TLS for production
3. Configure CORS appropriately
4. Use a process manager (systemd, supervisor)
5. Set up monitoring and logging
6. Configure rate limiting and DDoS protection
7. Regular security audits of Snowflake access

## License

MIT
