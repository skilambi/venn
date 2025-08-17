#!/bin/bash

# Quick start script for the chat server
# This script sets up and runs the chat server with all dependencies

set -e  # Exit on error

echo "🚀 Chat Server Quick Start"
echo "=========================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    echo "Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"
echo ""

# Check if .env file exists
if [ ! -f "../.env" ]; then
    echo "📝 Creating .env file from template..."
    cp ../.env.example ../.env
    
    # Generate a secure secret key
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || echo "change-this-secret-key-in-production")
    
    # Update secret key in .env
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/your-secret-key-change-this-in-production-use-secrets-module/$SECRET_KEY/" ../.env
    else
        # Linux
        sed -i "s/your-secret-key-change-this-in-production-use-secrets-module/$SECRET_KEY/" ../.env
    fi
    
    echo "⚠️  Please edit ../.env file and add:"
    echo "   - Your OpenAI API key"
    echo "   - Your Snowflake credentials (optional)"
    echo ""
    echo "Press Enter when you've updated the .env file..."
    read
fi

# Navigate to parent directory
cd ..

# Stop any running containers
echo "🛑 Stopping any existing containers..."
docker-compose down 2>/dev/null || true

# Build and start services
echo "🏗️  Building Docker images..."
docker-compose build

echo ""
echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to be ready
echo ""
echo "⏳ Waiting for services to be ready..."
sleep 5

# Check health
echo ""
echo "🏥 Checking service health..."

# Check PostgreSQL
if docker-compose exec -T postgres pg_isready -U chatuser -d chatdb &>/dev/null; then
    echo "✅ PostgreSQL is ready"
else
    echo "⚠️  PostgreSQL is not ready yet"
fi

# Check Redis
if docker-compose exec -T redis redis-cli ping | grep -q PONG; then
    echo "✅ Redis is ready"
else
    echo "⚠️  Redis is not ready yet"
fi

# Check API
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    echo "✅ API server is ready"
else
    echo "⚠️  API server is not ready yet"
fi

echo ""
echo "=========================================="
echo "✨ Chat Server is running!"
echo "=========================================="
echo ""
echo "📍 API URL: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo "📊 Logs: docker-compose logs -f"
echo ""
echo "🧪 To run the test flow:"
echo "   cd examples"
echo "   python3 test_flow.py"
echo ""
echo "🛑 To stop the server:"
echo "   docker-compose down"
echo ""
echo "💡 Quick Test Commands:"
echo ""
echo "1. Register a user:"
echo 'curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '"'"'{
    "email": "test@example.com",
    "username": "testuser",
    "password": "TestPass123!",
    "full_name": "Test User"
  }'"'"

echo ""
echo "2. Check API documentation:"
echo "   Open http://localhost:8000/docs in your browser"
echo ""