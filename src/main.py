import json
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI,WebSocket,WebSocketDisconnect,HTTPException
from .services.websockets import ConnectionManager
app = FastAPI()
manager = ConnectionManager()
db = {}
gpio_ports ={}

# cors
origins = [
    "*",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.put("/backup",status_code=201)
def make_backup(backup:dict):
    global db,gpio_ports
    if not ('db' in backup and 'gpio_ports' in backup):
        raise HTTPException(status_code=400, detail="Bad request")
    db = backup['db']
    gpio_ports = backup['gpio_ports']
    return "ok"

@app.get('/backup')
def get_bakup():
    global db,gpio_ports
    if db == {} or gpio_ports == {}:
        raise HTTPException(status_code=400, detail="Bad request")
    return {'db':db,'gpio_ports':gpio_ports}

@app.put("/{client}/command/{key}")
async def update_backup(client:str,key:str):
    global db
    if key not in db:
        await manager.broadcast(f'comand not found: {key}'.encode(),client=client)
        raise HTTPException(status_code=400, detail=f"Bad request {key}")
    port = db[key]
    action = 1 if not db[key] else 0
    db[key] = True if action == 1 else False
    await manager.broadcast(json.dumps(db),client=client)
    return db


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket,client_id)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"You wrote: {data}", websocket)
            await manager.broadcast(f"Client #{client_id} says: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client #{client_id} left the chat")