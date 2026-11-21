from fastapi import FastAPI
from pydantic import BaseModel
import time

app = FastAPI()

class PlayerState(BaseModel):
    id: str
    nick: str
    x: float
    y: float
    z: float
    rot_y: float
    vehicle: str = "walk"
    voice: str = ""

players = {}

@app.get("/")
def root():
    return {"status": "online", "players": len(players)}

@app.post("/sync")
def sync_player(state: PlayerState):
    now = time.time()
    players[state.id] = {
        "nick": state.nick,
        "x": state.x,
        "y": state.y,
        "z": state.z,
        "rot_y": state.rot_y,
        "vehicle": state.vehicle,
        "voice": state.voice,
        "voice_ts": now if state.voice else players.get(state.id, {}).get("voice_ts", 0),
        "last_seen": now
    }
    active = {pid: p for pid, p in players.items() if now - p["last_seen"] < 5.0}
    players.clear()
    players.update(active)
    return {"players": active}
