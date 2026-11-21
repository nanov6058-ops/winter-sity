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
        "last_seen": now
    }
    # Удаляем игроков, которые вышли более 5 секунд назад
    active = {pid: p for pid, p in players.items() if now - p["last_seen"] < 5.0}
    players.clear()
    players.update(active)
    return {"players": active}
