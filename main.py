from fastapi import FastAPI
from pydantic import BaseModel
import sqlite3
import uuid
import os

app = FastAPI()
# RelaxDev сам подставит порт, но для локального теста берем 8000
PORT = int(os.environ.get("PORT", 8000))
DB_PATH = "winter_town.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS players
                      (id TEXT PRIMARY KEY, name TEXT, money INTEGER, house TEXT)''')
    conn.commit()
    conn.close()

init_db()

class RegisterData(BaseModel):
    name: str

@app.post("/register")
def register(data: RegisterData):
    player_id = str(uuid.uuid4())
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO players (id, name, money, house) VALUES (?, ?, ?, ?)",
                   (player_id, data.name, 1000, "house.glb"))
    conn.commit()
    conn.close()
    return {"id": player_id, "name": data.name, "money": 1000}

@app.get("/players")
def get_players():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM players")
    players = cursor.fetchall()
    conn.close()
    return [{"id": p[0], "name": p[1], "money": p[2], "house": p[3]} for p in players]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)