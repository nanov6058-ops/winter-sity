from fastapi import FastAPI
from pydantic import BaseModel
import time, json, os, hashlib

app = FastAPI()

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
DATA_FILE = "server_data.json"
use_pg = False
pg_conn = None

if DATABASE_URL:
    try:
        import psycopg2
        if DATABASE_URL.startswith("postgres://"):
            DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        pg_conn = psycopg2.connect(DATABASE_URL)
        pg_conn.autocommit = True
        with pg_conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS wc_users (
                    nick_key TEXT PRIMARY KEY,
                    nick TEXT NOT NULL,
                    pw TEXT NOT NULL,
                    money BIGINT DEFAULT 5000,
                    businesses TEXT DEFAULT '[]',
                    play_time DOUBLE PRECISION DEFAULT 0.0,
                    created_at DOUBLE PRECISION DEFAULT 0.0
                );
            """)
            cur.execute("ALTER TABLE wc_users ADD COLUMN IF NOT EXISTS created_at DOUBLE PRECISION DEFAULT 0.0;")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS wc_meta (
                    k TEXT PRIMARY KEY,
                    v TEXT NOT NULL
                );
            """)
            cur.execute("INSERT INTO wc_meta (k, v) VALUES ('admins', '[\"колян\"]') ON CONFLICT (k) DO NOTHING;")
            cur.execute("INSERT INTO wc_meta (k, v) VALUES ('version', '2.4') ON CONFLICT (k) DO NOTHING;")
            cur.execute("INSERT INTO wc_meta (k, v) VALUES ('update_url', '') ON CONFLICT (k) DO NOTHING;")
        use_pg = True
    except Exception as e:
        print("PG init fallback to file:", e)

def load_file_db():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"users": {}, "admins": ["колян"], "version": "2.4", "update_url": ""}

file_db = load_file_db()

def save_file_db():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(file_db, f, ensure_ascii=False, indent=2)

def get_meta(k: str, default_val: str) -> str:
    if use_pg:
        with pg_conn.cursor() as cur:
            cur.execute("SELECT v FROM wc_meta WHERE k = %s", (k,))
            row = cur.fetchone()
            return row if row else default_val
    return str(file_db.get(k, default_val))

def set_meta(k: str, val: str):
    if use_pg:
        with pg_conn.cursor() as cur:
            cur.execute("INSERT INTO wc_meta (k, v) VALUES (%s, %s) ON CONFLICT (k) DO UPDATE SET v = EXCLUDED.v", (k, val))
    else:
        file_db[k] = val
        save_file_db()

def get_admins() -> list:
    raw = get_meta("admins", '["колян"]')
    try:
        arr = json.loads(raw) if isinstance(raw, str) else raw
    except:
        arr = ["колян"]
    if "колян" not in [a.lower() for a in arr]:
        arr.append("колян")
    return arr

def get_user(key: str):
    if use_pg:
        with pg_conn.cursor() as cur:
            cur.execute("SELECT nick, pw, money, businesses, play_time FROM wc_users WHERE nick_key = %s", (key,))
            row = cur.fetchone()
            if not row:
                return None
            return {
                "nick": row,
                "pw": row,
                "money": int(row),
                "businesses": json.loads(row or "[]"),
                "play_time": float(row)
            }
    return file_db["users"].get(key)

def upsert_user(key: str, nick: str, pw: str, money: int, businesses: list, play_time: float):
    if use_pg:
        with pg_conn.cursor() as cur:
            cur.execute("""
                INSERT INTO wc_users (nick_key, nick, pw, money, businesses, play_time, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (nick_key) DO UPDATE SET
                    money = EXCLUDED.money,
                    businesses = EXCLUDED.businesses,
                    play_time = EXCLUDED.play_time
            """, (key, nick, pw, money, json.dumps(businesses, ensure_ascii=False), play_time, time.time()))
    else:
        existing = file_db["users"].get(key, {})
        file_db["users"][key] = {
            "nick": nick,
            "pw": pw,
            "money": money,
            "businesses": businesses,
            "play_time": play_time,
            "created_at": existing.get("created_at", time.time())
        }
        save_file_db()

def get_city_snapshot():
    citizens = []
    city_businesses = []
    if use_pg:
        with pg_conn.cursor() as cur:
            cur.execute("SELECT nick, businesses FROM wc_users ORDER BY created_at ASC, nick_key ASC")
            rows = cur.fetchall()
            for idx, r in enumerate(rows):
                nick = r
                citizens.append({"nick": nick, "slot": idx})
                for b_id in json.loads(r or "[]"):
                    city_businesses.append({"owner": nick, "id": b_id})
    else:
        items = sorted(file_db["users"].items(), key=lambda x: x.get("created_at", 0))
        for idx, (k, u) in enumerate(items):
            nick = u["nick"]
            citizens.append({"nick": nick, "slot": idx})
            for b_id in u.get("businesses", []):
                city_businesses.append({"owner": nick, "id": b_id})
    if not citizens:
        citizens = [{"nick": "колян", "slot": 0}]
    return citizens, city_businesses

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
    cits, _ = get_city_snapshot()
    return {
        "status": "online",
        "db": "postgresql" if use_pg else "file",
        "players": len(players),
        "citizens": len(cits),
        "version": get_meta("version", "2.4"),
        "update_url": get_meta("update_url", "")
    }

@app.post("/register")
def register(req: AuthReq):
    nick = req.nick.strip()
    key = nick.lower()
    if len(nick) < 2 or len(req.password) < 3:
        return {"ok": False, "error": "Ник от 2 символов, пароль от 3"}
    if get_user(key):
        return {"ok": False, "error": "Этот ник уже занят!"}
    upsert_user(key, nick, hash_pw(req.password), 5000, [], 0.0)
    is_adm = key in [a.lower() for a in get_admins()]
    return {"ok": True, "nick": nick, "is_admin": is_adm, "money": 5000, "businesses": [], "play_time": 0.0}

@app.post("/login")
def login(req: AuthReq):
    nick = req.nick.strip()
    key = nick.lower()
    user = get_user(key)
    if not user or user["pw"] != hash_pw(req.password):
        return {"ok": False, "error": "Неверный ник или пароль"}
    is_adm = key in [a.lower() for a in get_admins()]
    return {
        "ok": True,
        "nick": user["nick"],
        "is_admin": is_adm,
        "money": user.get("money", 5000),
        "businesses": user.get("businesses", []),
        "play_time": user.get("play_time", 0.0),
        "version": get_meta("version", "2.4"),
        "update_url": get_meta("update_url", "")
    }

@app.post("/save_profile")
def save_profile(req: SaveProfileReq):
    key = req.nick.strip().lower()
    user = get_user(key)
    if not user or user["pw"] != hash_pw(req.password):
        return {"ok": False}
    upsert_user(key, user["nick"], user["pw"], req.money, req.businesses, req.play_time)
    return {"ok": True}

@app.post("/admin/add_admin")
def add_admin(req: AdminActionReq):
    key = req.admin_nick.strip().lower()
    user = get_user(key)
    admins = get_admins()
    if not user or user["pw"] != hash_pw(req.admin_password) or key not in [a.lower() for a in admins]:
        return {"ok": False, "error": "Нет прав админа"}
    target = req.target_nick.strip()
    if target and target.lower() not in [a.lower() for a in admins]:
        admins.append(target)
        set_meta("admins", json.dumps(admins, ensure_ascii=False))
    return {"ok": True, "admins": admins}

@app.post("/admin/publish_update")
def publish_update(req: AdminActionReq):
    key = req.admin_nick.strip().lower()
    user = get_user(key)
    admins = get_admins()
    if not user or user["pw"] != hash_pw(req.admin_password) or key not in [a.lower() for a in admins]:
        return {"ok": False, "error": "Нет прав админа"}
    if req.new_version.strip():
        set_meta("version", req.new_version.strip())
    set_meta("update_url", req.update_url.strip())
    return {"ok": True, "version": get_meta("version", "2.4")}

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
    citizens, city_businesses = get_city_snapshot()
    return {
        "players": active,
        "citizens": citizens,
        "city_businesses": city_businesses,
        "server_time": now
    }
