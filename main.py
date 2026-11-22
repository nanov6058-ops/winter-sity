from fastapi import FastAPI
from pydantic import BaseModel
import time, json, os, hashlib

app = FastAPI()

DATA_FILE = "server_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {
        "users": {},
        "admins": ["колян"],
        "version": "2.3",
        "update_url": ""
    }

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

db = load_data()
if "колян" not in [a.lower() for a in db["admins"]]:
    db["admins"].append("колян")
    save_data(db)

def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

class AuthReq(BaseModel):
    nick: str
    password: str

class SaveProfileReq(BaseModel):
    nick: str
    password: str
    money: int
    businesses: list[str] = []
    play_time: float = 0.0

class AdminActionReq(BaseModel):
    admin_nick: str
    admin_password: str
    target_nick: str = ""
    new_version: str = ""
    update_url: str = ""

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
    return {
        "status": "online",
        "players": len(players),
        "citizens": len(db.get("users", {})),
        "version": db.get("version", "2.3"),
        "update_url": db.get("update_url", "")
    }

@app.post("/register")
def register(req: AuthReq):
    nick = req.nick.strip()
    key = nick.lower()
    if len(nick) < 2 or len(req.password) < 3:
        return {"ok": False, "error": "Ник от 2 символов, пароль от 3"}
    if key in db["users"]:
        return {"ok": False, "error": "Этот ник уже занят!"}
    db["users"][key] = {
        "nick": nick,
        "pw": hash_pw(req.password),
        "money": 5000,
        "businesses": [],
        "play_time": 0.0
    }
    save_data(db)
    is_adm = key in [a.lower() for a in db["admins"]]
    return {
        "ok": True,
        "nick": nick,
        "is_admin": is_adm,
        "money": 5000,
        "businesses": [],
        "play_time": 0.0
    }

@app.post("/login")
def login(req: AuthReq):
    nick = req.nick.strip()
    key = nick.lower()
    user = db["users"].get(key)
    if not user or user["pw"] != hash_pw(req.password):
        return {"ok": False, "error": "Неверный ник или пароль"}
    is_adm = key in [a.lower() for a in db["admins"]]
    return {
        "ok": True,
        "nick": user["nick"],
        "is_admin": is_adm,
        "money": user.get("money", 5000),
        "businesses": user.get("businesses", []),
        "play_time": user.get("play_time", 0.0),
        "version": db.get("version", "2.3"),
        "update_url": db.get("update_url", "")
    }

@app.post("/save_profile")
def save_profile(req: SaveProfileReq):
    key = req.nick.strip().lower()
    user = db["users"].get(key)
    if not user or user["pw"] != hash_pw(req.password):
        return {"ok": False}
    user["money"] = req.money
    user["businesses"] = req.businesses
    user["play_time"] = req.play_time
    save_data(db)
    return {"ok": True}

@app.post("/admin/add_admin")
def add_admin(req: AdminActionReq):
    key = req.admin_nick.strip().lower()
    user = db["users"].get(key)
    if not user or user["pw"] != hash_pw(req.admin_password) or key not in [a.lower() for a in db["admins"]]:
        return {"ok": False, "error": "Нет прав админа"}
    target = req.target_nick.strip()
    if target and target.lower() not in [a.lower() for a in db["admins"]]:
        db["admins"].append(target)
        save_data(db)
    return {"ok": True, "admins": db["admins"]}

@app.post("/admin/publish_update")
def publish_update(req: AdminActionReq):
    key = req.admin_nick.strip().lower()
    user = db["users"].get(key)
    if not user or user["pw"] != hash_pw(req.admin_password) or key not in [a.lower() for a in db["admins"]]:
        return {"ok": False, "error": "Нет прав админа"}
    if req.new_version.strip():
        db["version"] = req.new_version.strip()
    db["update_url"] = req.update_url.strip()
    save_data(db)
    return {"ok": True, "version": db["version"]}

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
    citizens = [u["nick"] for u in db["users"].values()]
    if not citizens:
        citizens = ["колян"]
    return {"players": active, "citizens": citizens}
