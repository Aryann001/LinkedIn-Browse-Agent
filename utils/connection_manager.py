from fastapi import WebSocket
from typing import List, Dict, Any

class ConnectionManager:
    def __init__(self):
        # Note: This simple manager broadcasts to *all* clients.
        # For a multi-user app, you'd use a Dict[str, WebSocket]
        # to send messages only to a specific user.
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print("A client connected.")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print("A client disconnected.")

    async def broadcast(self, data: Dict[str, Any]):
        """Sends a JSON message to all connected clients."""
        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except Exception as e:
                print(f"Error broadcasting to a websocket: {e}")

# Create a single instance to be imported by your app
manager = ConnectionManager()