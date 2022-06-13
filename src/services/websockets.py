from fastapi import  WebSocket
from typing import List
class ConnectionManager:

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket,client):
        if client =='raspberry':
            self._raspberry = websocket
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str,client = None):
        for connection in self.active_connections:
            if client == 'raspberry'and connection == self._raspberry:
                continue
            else:
                await connection.send_text(message)