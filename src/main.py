import json
from fastapi import FastAPI,WebSocket,WebSocketDisconnect,HTTPException
from .services.websockets import ConnectionManager
app = FastAPI()
manager = ConnectionManager()
db = {}
gpio_ports ={}
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

@app.put("/command/{key}")
def update_backup(key:str):
    global db
    if key not in db:
        raise HTTPException(status_code=400, detail="Bad request")
    port = db[key]
    action = 1 if not db[key] else 0
    db[key] = True if action == 1 else False
    manager.broadcast(json.dumps(db))
    return db


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"You wrote: {data}", websocket)
            await manager.broadcast(f"Client #{client_id} says: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client #{client_id} left the chat")