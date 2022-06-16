import uuid
from fastapi import FastAPI,WebSocket, WebSocketDisconnect
from typing import List
app = FastAPI()

class ConnectionUser:
    def __init__(self, client_id,id,websocket:WebSocket):
        self.client_id = client_id
        self.id = id
        self.websocket : WebSocket= websocket
    
    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, ConnectionUser):
            return self.id == __o.id
        return False
        
class ConnectionManager:

    def __init__(self):
        self.active_connections: List[ConnectionUser] = []

    async def connect(self, client: ConnectionUser):
        await client.websocket.accept()
        self.active_connections.append(client)

    def disconnect(self, client: ConnectionUser):
        self.active_connections.remove(client)

    async def send_personal_message(self, message: str, client: ConnectionUser):
        await client.websocket.send_text(message)

    async def broadcast(self, message: str,senderClient: ConnectionUser):
        for client in self.active_connections:
            if client != senderClient:
                await client.websocket.send_text(message)

manager = ConnectionManager()

@app.get("/")
async def root():
    return "hello world 1"

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    client = ConnectionUser(client_id, str(uuid.uuid4()),websocket)
    await manager.connect(client)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"Client #{client.id} says: {data}",client)
    except WebSocketDisconnect:

        manager.disconnect(client)
        await manager.broadcast(f"Client #{client.id} left the chat",client)