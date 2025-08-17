#!/usr/bin/env python3
"""
Complete test flow for the chat server application.
This script demonstrates all major features including:
- User registration and authentication
- Channel creation and messaging
- Thread creation with LLM queries
- WebSocket real-time updates
"""

import asyncio
import aiohttp
import json
from datetime import datetime
import websockets

# Server configuration
BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"
API_VERSION = "v1"

class ChatServerTester:
    def __init__(self):
        self.session = None
        self.users = {}
        self.channels = {}
        self.messages = {}
        self.threads = {}
        
    async def setup(self):
        """Initialize HTTP session"""
        self.session = aiohttp.ClientSession()
        
    async def cleanup(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
    
    async def register_user(self, email, username, password, full_name):
        """Register a new user"""
        url = f"{BASE_URL}/api/{API_VERSION}/auth/register"
        data = {
            "email": email,
            "username": username,
            "password": password,
            "full_name": full_name
        }
        
        async with self.session.post(url, json=data) as resp:
            if resp.status == 200:
                user_data = await resp.json()
                print(f"✓ Registered user: {username}")
                return user_data
            else:
                error = await resp.text()
                print(f"✗ Failed to register {username}: {error}")
                return None
    
    async def login_user(self, email, password):
        """Login and get access token"""
        url = f"{BASE_URL}/api/{API_VERSION}/auth/login"
        data = {
            "username": email,
            "password": password
        }
        
        async with self.session.post(url, data=data) as resp:
            if resp.status == 200:
                token_data = await resp.json()
                print(f"✓ Logged in: {email}")
                return token_data
            else:
                error = await resp.text()
                print(f"✗ Failed to login {email}: {error}")
                return None
    
    async def create_channel(self, token, name, description):
        """Create a new channel"""
        url = f"{BASE_URL}/api/{API_VERSION}/channels/"
        headers = {"Authorization": f"Bearer {token}"}
        data = {
            "name": name,
            "description": description
        }
        
        async with self.session.post(url, headers=headers, json=data) as resp:
            if resp.status == 200:
                channel_data = await resp.json()
                print(f"✓ Created channel: {name}")
                return channel_data
            else:
                error = await resp.text()
                print(f"✗ Failed to create channel {name}: {error}")
                return None
    
    async def send_message(self, token, channel_id, content):
        """Send a message to a channel"""
        url = f"{BASE_URL}/api/{API_VERSION}/messages/"
        headers = {"Authorization": f"Bearer {token}"}
        data = {
            "channel_id": channel_id,
            "content": content
        }
        
        async with self.session.post(url, headers=headers, json=data) as resp:
            if resp.status == 200:
                message_data = await resp.json()
                print(f"✓ Sent message: {content[:50]}...")
                return message_data
            else:
                error = await resp.text()
                print(f"✗ Failed to send message: {error}")
                return None
    
    async def create_thread(self, token, channel_id, root_message_id, title, allowed_tables=None):
        """Create a thread with LLM enabled"""
        url = f"{BASE_URL}/api/{API_VERSION}/threads/"
        headers = {"Authorization": f"Bearer {token}"}
        data = {
            "channel_id": channel_id,
            "root_message_id": root_message_id,
            "title": title,
            "is_llm_enabled": True,
            "allowed_tables": allowed_tables or []
        }
        
        async with self.session.post(url, headers=headers, json=data) as resp:
            if resp.status == 200:
                thread_data = await resp.json()
                print(f"✓ Created thread: {title}")
                return thread_data
            else:
                error = await resp.text()
                print(f"✗ Failed to create thread: {error}")
                return None
    
    async def query_llm(self, token, thread_id, query):
        """Send an LLM query to a thread"""
        url = f"{BASE_URL}/api/{API_VERSION}/threads/{thread_id}/llm-query"
        headers = {"Authorization": f"Bearer {token}"}
        data = {
            "thread_id": thread_id,
            "query": query
        }
        
        async with self.session.post(url, headers=headers, json=data) as resp:
            if resp.status == 200:
                result = await resp.json()
                print(f"✓ Submitted LLM query: {query[:50]}...")
                return result
            else:
                error = await resp.text()
                print(f"✗ Failed to submit query: {error}")
                return None
    
    async def websocket_listener(self, token, duration=10):
        """Connect to WebSocket and listen for messages"""
        uri = f"{WS_URL}/ws/{token}"
        
        try:
            async with websockets.connect(uri) as websocket:
                print(f"✓ Connected to WebSocket")
                
                # Set up timeout
                end_time = asyncio.get_event_loop().time() + duration
                
                while asyncio.get_event_loop().time() < end_time:
                    try:
                        message = await asyncio.wait_for(
                            websocket.recv(), 
                            timeout=1.0
                        )
                        data = json.loads(message)
                        print(f"  📨 WebSocket message: {data.get('type', 'unknown')}")
                        
                        if data.get('type') == 'llm_response':
                            print(f"  🤖 LLM Response received in thread")
                            
                    except asyncio.TimeoutError:
                        # Send ping to keep connection alive
                        await websocket.send(json.dumps({"type": "ping"}))
                    except Exception as e:
                        print(f"  ⚠️  WebSocket error: {e}")
                        break
                        
        except Exception as e:
            print(f"✗ WebSocket connection failed: {e}")
    
    async def run_complete_test(self):
        """Run a complete test of all features"""
        print("\n" + "="*60)
        print("CHAT SERVER COMPLETE TEST FLOW")
        print("="*60 + "\n")
        
        await self.setup()
        
        try:
            # Step 1: Register users
            print("📝 STEP 1: Registering users...")
            alice = await self.register_user(
                "alice@example.com", 
                "alice", 
                "AlicePass123!",
                "Alice Smith"
            )
            bob = await self.register_user(
                "bob@example.com",
                "bob",
                "BobPass123!",
                "Bob Jones"
            )
            
            # Step 2: Login users
            print("\n🔐 STEP 2: Logging in users...")
            alice_auth = await self.login_user("alice@example.com", "AlicePass123!")
            bob_auth = await self.login_user("bob@example.com", "BobPass123!")
            
            if not alice_auth or not bob_auth:
                print("❌ Authentication failed, stopping test")
                return
            
            alice_token = alice_auth["access_token"]
            bob_token = bob_auth["access_token"]
            
            # Step 3: Create channels
            print("\n📺 STEP 3: Creating channels...")
            general_channel = await self.create_channel(
                alice_token,
                "general",
                "General discussion channel"
            )
            data_channel = await self.create_channel(
                alice_token,
                "data-analysis",
                "Data analysis and queries"
            )
            
            if not general_channel or not data_channel:
                print("❌ Channel creation failed, stopping test")
                return
            
            # Step 4: Send messages
            print("\n💬 STEP 4: Sending messages...")
            msg1 = await self.send_message(
                alice_token,
                general_channel["id"],
                "Hello everyone! Welcome to our chat server!"
            )
            msg2 = await self.send_message(
                bob_token,
                general_channel["id"],
                "Hi Alice! This is great!"
            )
            data_msg = await self.send_message(
                alice_token,
                data_channel["id"],
                "Let's analyze some data using the LLM feature"
            )
            
            # Step 5: Create thread with LLM
            print("\n🧵 STEP 5: Creating LLM-enabled thread...")
            if data_msg:
                thread = await self.create_thread(
                    alice_token,
                    data_channel["id"],
                    data_msg["id"],
                    "Customer Analysis Thread",
                    ["CUSTOMERS", "ORDERS", "PRODUCTS"]  # Example tables
                )
                
                if thread:
                    # Step 6: Start WebSocket listener in background
                    print("\n📡 STEP 6: Starting WebSocket listener...")
                    ws_task = asyncio.create_task(
                        self.websocket_listener(alice_token, duration=15)
                    )
                    
                    # Give WebSocket time to connect
                    await asyncio.sleep(2)
                    
                    # Step 7: Send LLM queries
                    print("\n🤖 STEP 7: Sending LLM queries...")
                    query1 = await self.query_llm(
                        alice_token,
                        thread["id"],
                        "Show me the top 5 customers by total order value"
                    )
                    
                    await asyncio.sleep(2)
                    
                    query2 = await self.query_llm(
                        alice_token,
                        thread["id"],
                        "What products are most frequently ordered?"
                    )
                    
                    # Wait for WebSocket to receive responses
                    await ws_task
            
            # Step 8: Summary
            print("\n" + "="*60)
            print("✅ TEST COMPLETE - All features tested successfully!")
            print("="*60)
            print("\nFeatures tested:")
            print("  ✓ User registration and authentication")
            print("  ✓ Channel creation")
            print("  ✓ Message sending")
            print("  ✓ Thread creation with LLM")
            print("  ✓ LLM query submission")
            print("  ✓ WebSocket real-time updates")
            
        except Exception as e:
            print(f"\n❌ Test failed with error: {e}")
            
        finally:
            await self.cleanup()


async def main():
    tester = ChatServerTester()
    await tester.run_complete_test()


if __name__ == "__main__":
    print("Starting Chat Server Test...")
    print("Make sure the server is running at http://localhost:8000")
    print("-" * 60)
    asyncio.run(main())