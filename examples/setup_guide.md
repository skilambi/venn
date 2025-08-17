# Complete Setup and Usage Guide

## Quick Start with Docker

### 1. Prerequisites
- Docker and Docker Compose installed
- OpenAI API key
- Snowflake account (optional, for data querying)

### 2. Clone and Configure

```bash
# Navigate to chat_server directory
cd chat_server

# Edit .env file with your credentials
# IMPORTANT: Change these values:
# - SECRET_KEY: Generate with: python -c "import secrets; print(secrets.token_hex(32))"
# - OPENAI_API_KEY: Your OpenAI API key
# - SNOWFLAKE_*: Your Snowflake credentials (if using)
```

### 3. Start Services

```bash
# Start all services with Docker Compose
docker-compose up -d

# Check logs
docker-compose logs -f

# The server will be available at http://localhost:8000
```

## Manual Setup (Without Docker)

### 1. Install PostgreSQL and Redis

macOS:
```bash
brew install postgresql redis
brew services start postgresql
brew services start redis
```

Ubuntu:
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib redis-server
sudo systemctl start postgresql redis
```

### 2. Create Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database and user
CREATE DATABASE chatdb;
CREATE USER chatuser WITH PASSWORD 'chatpass';
GRANT ALL PRIVILEGES ON DATABASE chatdb TO chatuser;
\q
```

### 3. Setup Python Environment

```bash
cd chat_server

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Update .env file with your credentials
cp .env.example .env
# Edit .env with your actual values
```

### 4. Run Server

```bash
python main.py
# Server starts at http://localhost:8000
```

## API Usage Examples

### 1. Register a User

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "username": "john_doe",
    "password": "SecurePass123!",
    "full_name": "John Doe"
  }'
```

Response:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "john@example.com",
  "username": "john_doe",
  "full_name": "John Doe",
  "is_active": true
}
```

### 2. Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=john@example.com&password=SecurePass123!"
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

### 3. Create a Channel

```bash
TOKEN="your_access_token_here"

curl -X POST http://localhost:8000/api/v1/channels/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "general",
    "description": "General discussion channel"
  }'
```

### 4. Send a Message

```bash
CHANNEL_ID="channel_id_from_previous_response"

curl -X POST http://localhost:8000/api/v1/messages/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "channel_id": "'$CHANNEL_ID'",
    "content": "Hello everyone!"
  }'
```

### 5. Create a Thread with LLM

```bash
MESSAGE_ID="message_id_from_previous_response"

curl -X POST http://localhost:8000/api/v1/threads/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "channel_id": "'$CHANNEL_ID'",
    "root_message_id": "'$MESSAGE_ID'",
    "title": "Data Analysis Thread",
    "is_llm_enabled": true,
    "allowed_tables": ["CUSTOMERS", "ORDERS", "PRODUCTS"]
  }'
```

### 6. Query Data with LLM

```bash
THREAD_ID="thread_id_from_previous_response"

curl -X POST http://localhost:8000/api/v1/threads/'$THREAD_ID'/llm-query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "thread_id": "'$THREAD_ID'",
    "query": "Show me the top 5 customers by total order value"
  }'
```

## WebSocket Connection Example

### JavaScript/Browser Client

```javascript
// Connect to WebSocket
const token = "your_access_token";
const ws = new WebSocket(`ws://localhost:8000/ws/${token}`);

// Connection opened
ws.onopen = () => {
    console.log("Connected to chat server");
    
    // Join a channel
    ws.send(JSON.stringify({
        type: "join_channel",
        channel_id: "channel_uuid_here"
    }));
};

// Listen for messages
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    switch(data.type) {
        case "new_message":
            console.log("New message:", data.message);
            break;
        case "llm_response":
            console.log("LLM Response:", data.message);
            break;
        case "typing_indicator":
            console.log(`${data.user_id} is typing...`);
            break;
        case "user_status":
            console.log(`User ${data.user_id} is ${data.status}`);
            break;
    }
};

// Send typing indicator
function sendTypingIndicator(channelId, isTyping) {
    ws.send(JSON.stringify({
        type: "typing",
        channel_id: channelId,
        is_typing: isTyping
    }));
}

// Keep connection alive
setInterval(() => {
    ws.send(JSON.stringify({ type: "ping" }));
}, 30000);
```

### Python Client Example

```python
import asyncio
import websockets
import json

async def chat_client(token):
    uri = f"ws://localhost:8000/ws/{token}"
    
    async with websockets.connect(uri) as websocket:
        # Join channel
        await websocket.send(json.dumps({
            "type": "join_channel",
            "channel_id": "your_channel_id"
        }))
        
        # Listen for messages
        async for message in websocket:
            data = json.loads(message)
            print(f"Received: {data}")

# Run client
token = "your_access_token"
asyncio.run(chat_client(token))
```

## Testing the Complete Flow

### 1. Setup Test Environment

```bash
# Terminal 1: Start services
docker-compose up

# Terminal 2: Run test script
python examples/test_flow.py
```

### 2. Manual Testing Flow

```bash
# 1. Register two users
./examples/create_users.sh

# 2. Create a channel
./examples/create_channel.sh

# 3. Send messages
./examples/send_messages.sh

# 4. Create thread with LLM
./examples/create_llm_thread.sh

# 5. Query data
./examples/query_data.sh
```

## Snowflake Setup for Read-Only Access

### 1. Create Read-Only Role in Snowflake

```sql
-- Connect as ACCOUNTADMIN
USE ROLE ACCOUNTADMIN;

-- Create read-only role
CREATE ROLE READONLY_ROLE;

-- Grant warehouse usage
GRANT USAGE ON WAREHOUSE COMPUTE_WH TO ROLE READONLY_ROLE;

-- Grant database and schema access
GRANT USAGE ON DATABASE YOUR_DATABASE TO ROLE READONLY_ROLE;
GRANT USAGE ON SCHEMA YOUR_DATABASE.PUBLIC TO ROLE READONLY_ROLE;

-- Grant SELECT on all tables
GRANT SELECT ON ALL TABLES IN SCHEMA YOUR_DATABASE.PUBLIC TO ROLE READONLY_ROLE;
GRANT SELECT ON FUTURE TABLES IN SCHEMA YOUR_DATABASE.PUBLIC TO ROLE READONLY_ROLE;

-- Create read-only user
CREATE USER readonly_user 
    PASSWORD = 'StrongPassword123!'
    DEFAULT_ROLE = READONLY_ROLE
    DEFAULT_WAREHOUSE = COMPUTE_WH;

-- Grant role to user
GRANT ROLE READONLY_ROLE TO USER readonly_user;
```

### 2. Test Connection

```python
import snowflake.connector

conn = snowflake.connector.connect(
    account='your_account',
    user='readonly_user',
    password='StrongPassword123!',
    warehouse='COMPUTE_WH',
    database='YOUR_DATABASE',
    schema='PUBLIC'
)

cursor = conn.cursor()
cursor.execute("SELECT CURRENT_VERSION()")
print(cursor.fetchone())
cursor.close()
conn.close()
```

## Monitoring and Logs

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f chat_server

# Check database
docker exec -it chat_postgres psql -U chatuser -d chatdb
\dt  # List tables
SELECT * FROM users;
```

### Health Check

```bash
curl http://localhost:8000/health
# Response: {"status": "healthy"}
```

## Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Change port in .env or docker-compose.yml
   PORT=8001
   ```

2. **Database connection failed**
   ```bash
   # Check PostgreSQL is running
   docker-compose ps
   # Restart services
   docker-compose restart postgres
   ```

3. **OpenAI API errors**
   - Verify API key in .env
   - Check API quota/limits
   - Try with gpt-3.5-turbo instead of gpt-4

4. **Snowflake connection issues**
   - Verify account format (include region)
   - Check firewall/network settings
   - Verify role permissions

## Production Deployment

### 1. Security Checklist

- [ ] Generate strong SECRET_KEY
- [ ] Use HTTPS with SSL certificates
- [ ] Configure CORS properly
- [ ] Set DEBUG=False
- [ ] Use environment variables for secrets
- [ ] Enable rate limiting
- [ ] Set up monitoring/logging

### 2. Scaling Considerations

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  chat_server:
    image: chat_server:latest
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
    environment:
      DEBUG: "False"
```

### 3. Nginx Reverse Proxy

```nginx
upstream chat_backend {
    server localhost:8000;
    server localhost:8001;
    server localhost:8002;
}

server {
    listen 443 ssl http2;
    server_name chat.example.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://chat_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /ws {
        proxy_pass http://chat_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }
}
```