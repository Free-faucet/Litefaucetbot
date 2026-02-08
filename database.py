import json, os, time

DB_PATH = "users.json"

def load_db():
    if not os.path.exists(DB_PATH):
        return {}
    with open(DB_PATH, "r") as f:
        return json.load(f)

def save_db(db):
    with open(DB_PATH, "w") as f:
        json.dump(db, f, indent=2)

def get_user(db, uid):
    uid = str(uid)
    if uid not in db:
        db[uid] = {
            "balance": 0,
            "last_claim": 0,
            "ref": None,
            "refs": 0
        }
    return db[uid]
