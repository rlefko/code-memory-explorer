"""
WebSocket API endpoints for real-time updates.
"""

import json
import asyncio
from typing import Dict, Set
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from models.schemas import WSMessage
from services.qdrant_service import get_qdrant_service

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections and subscriptions."""

    def __init__(self):
        # Active connections by client ID
        self.active_connections: Dict[str, WebSocket] = {}
        # Subscriptions: collection -> set of client IDs
        self.subscriptions: Dict[str, Set[str]] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        """Remove a WebSocket connection and its subscriptions."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]

        # Remove from all subscriptions
        for collection in self.subscriptions:
            if client_id in self.subscriptions[collection]:
                self.subscriptions[collection].discard(client_id)

    def subscribe(self, client_id: str, collection: str):
        """Subscribe a client to collection updates."""
        if collection not in self.subscriptions:
            self.subscriptions[collection] = set()
        self.subscriptions[collection].add(client_id)

    def unsubscribe(self, client_id: str, collection: str):
        """Unsubscribe a client from collection updates."""
        if collection in self.subscriptions:
            self.subscriptions[collection].discard(client_id)

    async def send_personal_message(self, message: str, client_id: str):
        """Send a message to a specific client."""
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            await websocket.send_text(message)

    async def broadcast_to_collection(self, message: str, collection: str):
        """Broadcast a message to all clients subscribed to a collection."""
        if collection in self.subscriptions:
            disconnected_clients = []

            for client_id in self.subscriptions[collection]:
                if client_id in self.active_connections:
                    try:
                        websocket = self.active_connections[client_id]
                        await websocket.send_text(message)
                    except Exception:
                        disconnected_clients.append(client_id)

            # Clean up disconnected clients
            for client_id in disconnected_clients:
                self.disconnect(client_id)


# Global connection manager
manager = ConnectionManager()


@router.websocket("/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint for real-time updates.

    Args:
        websocket: WebSocket connection.
        client_id: Unique client identifier.
    """
    await manager.connect(websocket, client_id)

    try:
        # Send welcome message
        welcome_msg = WSMessage(
            type="update",
            data={
                "message": f"Connected to Claude Code Memory Explorer WebSocket",
                "client_id": client_id,
            },
        )
        await manager.send_personal_message(welcome_msg.model_dump_json(), client_id)

        # Start ping task to keep connection alive
        async def ping_task():
            while True:
                try:
                    await asyncio.sleep(30)
                    ping_msg = WSMessage(type="ping")
                    await manager.send_personal_message(
                        ping_msg.model_dump_json(),
                        client_id,
                    )
                except Exception:
                    break

        ping_task_handle = asyncio.create_task(ping_task())

        # Handle incoming messages
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            msg_type = message.get("type")
            collection = message.get("collection")

            if msg_type == "subscribe" and collection:
                # Subscribe to collection updates
                manager.subscribe(client_id, collection)
                response = WSMessage(
                    type="update",
                    collection=collection,
                    data={"message": f"Subscribed to {collection}"},
                )
                await manager.send_personal_message(
                    response.model_dump_json(),
                    client_id,
                )

            elif msg_type == "unsubscribe" and collection:
                # Unsubscribe from collection
                manager.unsubscribe(client_id, collection)
                response = WSMessage(
                    type="update",
                    collection=collection,
                    data={"message": f"Unsubscribed from {collection}"},
                )
                await manager.send_personal_message(
                    response.model_dump_json(),
                    client_id,
                )

            elif msg_type == "pong":
                # Client responded to ping
                pass

            else:
                # Echo unknown messages
                response = WSMessage(
                    type="error",
                    data={"message": f"Unknown message type: {msg_type}"},
                )
                await manager.send_personal_message(
                    response.model_dump_json(),
                    client_id,
                )

    except WebSocketDisconnect:
        manager.disconnect(client_id)
        ping_task_handle.cancel()
    except Exception as e:
        manager.disconnect(client_id)
        ping_task_handle.cancel()
        print(f"WebSocket error for client {client_id}: {e}")


@router.post("/broadcast/{collection}")
async def broadcast_update(collection: str, message: dict):
    """
    Broadcast an update to all clients subscribed to a collection.
    This is used internally when indexing completes or entities are updated.

    Args:
        collection: Collection name.
        message: Update message to broadcast.

    Returns:
        Number of clients notified.
    """
    update_msg = WSMessage(
        type="update",
        collection=collection,
        data=message,
    )

    await manager.broadcast_to_collection(
        update_msg.model_dump_json(),
        collection,
    )

    client_count = len(manager.subscriptions.get(collection, set()))
    return {"clients_notified": client_count}


@router.get("/status")
async def websocket_status():
    """
    Get WebSocket server status and statistics.

    Returns:
        Status information.
    """
    return {
        "active_connections": len(manager.active_connections),
        "subscriptions": {
            collection: len(clients)
            for collection, clients in manager.subscriptions.items()
        },
        "clients": list(manager.active_connections.keys()),
    }


@router.get("/test")
async def websocket_test_page():
    """
    Simple HTML page for testing WebSocket connections.
    """
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>WebSocket Test</title>
    </head>
    <body>
        <h1>Claude Code Memory Explorer - WebSocket Test</h1>
        <div id="status">Disconnected</div>
        <div id="messages"></div>
        <input type="text" id="collection" placeholder="Collection name" />
        <button onclick="subscribe()">Subscribe</button>
        <button onclick="unsubscribe()">Unsubscribe</button>

        <script>
            const clientId = 'test-' + Math.random().toString(36).substr(2, 9);
            const ws = new WebSocket(`ws://localhost:8000/ws/${clientId}`);
            const messages = document.getElementById('messages');
            const status = document.getElementById('status');

            ws.onopen = () => {
                status.innerHTML = 'Connected as ' + clientId;
            };

            ws.onmessage = (event) => {
                const msg = JSON.parse(event.data);
                const div = document.createElement('div');
                div.innerHTML = `${new Date().toLocaleTimeString()}: ${JSON.stringify(msg)}`;
                messages.appendChild(div);

                if (msg.type === 'ping') {
                    ws.send(JSON.stringify({type: 'pong'}));
                }
            };

            ws.onclose = () => {
                status.innerHTML = 'Disconnected';
            };

            function subscribe() {
                const collection = document.getElementById('collection').value;
                if (collection) {
                    ws.send(JSON.stringify({
                        type: 'subscribe',
                        collection: collection
                    }));
                }
            }

            function unsubscribe() {
                const collection = document.getElementById('collection').value;
                if (collection) {
                    ws.send(JSON.stringify({
                        type: 'unsubscribe',
                        collection: collection
                    }));
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)