import os
import json
import uuid
import random
import string
import secrets
import hashlib
import threading
from datetime import datetime, timedelta

if os.path.exists('/data') and os.access('/data', os.W_OK):
    DATA_DIR = os.environ.get('DATA_DIR', '/data')
else:
    DATA_DIR = os.environ.get('DATA_DIR', os.path.abspath('.'))

os.makedirs(DATA_DIR, exist_ok=True)

BOT_USERS_FILE = os.path.join(DATA_DIR, 'bot_users.json')
BOT_PLANS_FILE = os.path.join(DATA_DIR, 'bot_plans.json')
BOT_TRANSACTIONS_FILE = os.path.join(DATA_DIR, 'bot_transactions.json')
BOT_VIDEOS_FILE = os.path.join(DATA_DIR, 'bot_videos.json')

_lock = threading.Lock()

DEFAULT_PLANS = {
    "file": [
        {"id": 1, "name": "Starter", "ram": "128MB", "disk": "512MB", "cpu_limit": 10, "days": 7, "points": 50},
        {"id": 2, "name": "Basic", "ram": "256MB", "disk": "1GB", "cpu_limit": 25, "days": 7, "points": 100},
        {"id": 3, "name": "Standard", "ram": "512MB", "disk": "1GB", "cpu_limit": 50, "days": 15, "points": 200},
        {"id": 4, "name": "Plus", "ram": "512MB", "disk": "2GB", "cpu_limit": 50, "days": 30, "points": 350},
        {"id": 5, "name": "Pro", "ram": "1GB", "disk": "3GB", "cpu_limit": 80, "days": 30, "points": 500},
        {"id": 6, "name": "Business", "ram": "1GB", "disk": "5GB", "cpu_limit": 80, "days": 60, "points": 800},
        {"id": 7, "name": "Enterprise", "ram": "2GB", "disk": "10GB", "cpu_limit": 100, "days": 60, "points": 1200},
        {"id": 8, "name": "Premium", "ram": "2GB", "disk": "15GB", "cpu_limit": 100, "days": 90, "points": 1500},
        {"id": 9, "name": "Ultra", "ram": "4GB", "disk": "20GB", "cpu_limit": 100, "days": 90, "points": 2000},
        {"id": 10, "name": "Ultimate", "ram": "4GB", "disk": "50GB", "cpu_limit": 100, "days": 180, "points": 3500}
    ],
    "api": [
        {"id": 1, "name": "Starter", "max_apps": 1, "max_ram_mb": 128, "max_cpu": 0.1, "days": 7, "points": 50},
        {"id": 2, "name": "Basic", "max_apps": 2, "max_ram_mb": 256, "max_cpu": 0.5, "days": 7, "points": 100},
        {"id": 3, "name": "Standard", "max_apps": 3, "max_ram_mb": 512, "max_cpu": 0.5, "days": 15, "points": 200},
        {"id": 4, "name": "Plus", "max_apps": 5, "max_ram_mb": 512, "max_cpu": 1.0, "days": 30, "points": 350},
        {"id": 5, "name": "Pro", "max_apps": 5, "max_ram_mb": 1024, "max_cpu": 1.0, "days": 30, "points": 500},
        {"id": 6, "name": "Business", "max_apps": 10, "max_ram_mb": 1024, "max_cpu": 1.5, "days": 60, "points": 800},
        {"id": 7, "name": "Enterprise", "max_apps": 10, "max_ram_mb": 2048, "max_cpu": 2.0, "days": 60, "points": 1200},
        {"id": 8, "name": "Premium", "max_apps": 20, "max_ram_mb": 2048, "max_cpu": 2.0, "days": 90, "points": 1500},
        {"id": 9, "name": "Ultra", "max_apps": 30, "max_ram_mb": 4096, "max_cpu": 2.0, "days": 90, "points": 2000},
        {"id": 10, "name": "Ultimate", "max_apps": 50, "max_ram_mb": 4096, "max_cpu": 2.0, "days": 180, "points": 3500}
    ],
    "html": [
        {"id": 1, "name": "Starter", "max_sites": 1, "days": 7, "points": 50},
        {"id": 2, "name": "Basic", "max_sites": 1, "days": 7, "points": 100},
        {"id": 3, "name": "Standard", "max_sites": 2, "days": 15, "points": 200},
        {"id": 4, "name": "Plus", "max_sites": 3, "days": 30, "points": 350},
        {"id": 5, "name": "Pro", "max_sites": 5, "days": 30, "points": 500},
        {"id": 6, "name": "Business", "max_sites": 5, "days": 60, "points": 800},
        {"id": 7, "name": "Enterprise", "max_sites": 10, "days": 60, "points": 1200},
        {"id": 8, "name": "Premium", "max_sites": 10, "days": 90, "points": 1500},
        {"id": 9, "name": "Ultra", "max_sites": 20, "days": 90, "points": 2000},
        {"id": 10, "name": "Ultimate", "max_sites": 50, "days": 180, "points": 3500}
    ]
}

def _load_json(path, default):
    if not os.path.exists(path): return default
    try:
        with open(path, 'r', encoding='utf-8') as f: return json.load(f)
    except: return default

def _save_json(path, data):
    with _lock:
        tmp = path + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f: json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, path)

# ---- Users ----
def load_bot_users(): return _load_json(BOT_USERS_FILE, {})
def save_bot_users(data): _save_json(BOT_USERS_FILE, data)
def get_bot_user(tid): return load_bot_users().get(str(tid))

def create_bot_user(tid, username, first_name):
    users = load_bot_users()
    if str(tid) in users: return users[str(tid)]
    new_user = {"telegram_id": int(tid), "username": username or f"user_{tid}", "first_name": first_name or "User", "points": 0, "joined_at": str(datetime.now()), "servers": []}
    users[str(tid)] = new_user
    save_bot_users(users)
    return new_user

def add_points(tid, points):
    users = load_bot_users()
    if str(tid) in users:
        users[str(tid)]["points"] = max(0, users[str(tid)].get("points", 0) + points)
        save_bot_users(users)
        return users[str(tid)]["points"]
    return None

# ---- Plans ----
def load_plans():
    data = _load_json(BOT_PLANS_FILE, None)
    return data if data and "file" in data else DEFAULT_PLANS

def get_plan(category, plan_id):
    for p in load_plans().get(category, []):
        if p.get("id") == plan_id: return p
    return None

# ---- Transactions ----
def load_transactions(): return _load_json(BOT_TRANSACTIONS_FILE, [])
def save_transactions(data): _save_json(BOT_TRANSACTIONS_FILE, data)

def create_transaction(tid, trx_type, points, **kwargs):
    transactions = load_transactions()
    trx = {"id": str(uuid.uuid4())[:12], "telegram_id": int(tid), "type": trx_type, "points": points, "created_at": str(datetime.now()), "status": "completed", **kwargs}
    transactions.append(trx)
    save_transactions(transactions)
    return trx

def update_transaction(trx_id, **kwargs):
    transactions = load_transactions()
    for t in transactions:
        if t.get("id") == trx_id:
            t.update(kwargs)
            save_transactions(transactions)
            return t

def get_transaction(trx_id):
    for t in load_transactions():
        if t.get("id") == trx_id: return t

def get_user_transactions(tid, limit=20):
    trx = [t for t in load_transactions() if t.get("telegram_id") == int(tid)]
    trx.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return trx[:limit]

def get_pending_transactions():
    trx = [t for t in load_transactions() if t.get("type") == "add_points" and t.get("status") == "pending"]
    trx.sort(key=lambda x: x.get("created_at", ""))
    return trx

def is_trxid_used(trx_id):
    for t in load_transactions():
        if t.get("type") == "add_points" and t.get("bikash_trx_id") == trx_id:
            if t.get("status") in ("approved", "pending"): return True
    return False

# ---- Videos ----
def load_videos(): return _load_json(BOT_VIDEOS_FILE, {})
def save_videos(data): _save_json(BOT_VIDEOS_FILE, data)
def set_video(cat, fid, uploaded_by): 
    videos = load_videos()
    videos[cat] = {"file_id": fid, "uploaded_at": str(datetime.now()), "uploaded_by": uploaded_by}
    save_videos(videos)
def get_video(cat): return load_videos().get(cat)

# ---- Server Creation ----
def _generate_username(base_name, tid):
    try: from app import load_users
    except: return f"tg_{tid}"
    users = load_users()
    base = ''.join(c for c in (base_name or '').lower() if c.isalnum() or c == '_')[:12] or 'user'
    candidate = f"{base}_{str(tid)[-4:]}"
    counter = 1
    while candidate in users:
        candidate = f"{base}_{str(tid)[-4:]}_{counter}"
        counter += 1
    return candidate

def _generate_password(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def create_server_from_plan(tid, category, plan):
    try: from app import load_users, save_users, hash_password, create_default_files, get_server_dir
    except Exception as e: return False, f"App import failed: {e}"
    users = load_users(); bot_users = load_bot_users(); key = str(tid)
    if key not in bot_users: return False, "User not registered"
    points = bot_users[key].get("points", 0); cost = plan.get("points", 0)
    if points < cost: return False, f"Not enough points (need {cost})"
    username = _generate_username(bot_users[key].get("first_name", "user"), tid)
    password = _generate_password(); expiry_str = str(datetime.now() + timedelta(days=plan.get("days", 7))); now_str = str(datetime.now())
    server_id = str(uuid.uuid4())[:8]

    if category == "file":
        create_default_files(get_server_dir(server_id))
        new_server = {"server_id": server_id, "type": "file_server", "ram": plan.get("ram", "512MB"), "disk": plan.get("disk", "1GB"), "status": "stopped", "pid": None, "created": now_str, "expiry": expiry_str, "main_file": "main.py", "requirements_file": "requirements.txt", "cpu_limit": plan.get("cpu_limit", 80), "rate_limit_exceeded": False, "stopped_by_user": False, "is_locked": False, "is_free_user": False, "from_bot": True, "bot_telegram_id": int(tid)}
        if username not in users: users[username] = {"password": hash_password(password), "raw_password": password, "role": "user", "servers": [], "sites": []}
        users[username]["servers"].append(new_server)
    elif category == "html":
        if username in users: username = username + "_h"
        users[username] = {"password": hash_password(password), "raw_password": password, "role": "html_user", "servers": [], "sites": [], "max_sites": plan.get("max_sites", 1), "created": now_str, "expiry": expiry_str, "expiry_display": expiry_str[:10], "from_bot": True, "bot_telegram_id": int(tid)}
    elif category == "api":
        if username in users: username = username + "_a"
        users[username] = {"password": hash_password(password), "raw_password": password, "role": "api_user", "servers": [], "sites": [], "api_apps": [], "api_limits": {"max_apps": plan.get("max_apps", 3), "max_files": 999, "max_disk_mb": 1024, "max_ram_mb": plan.get("max_ram_mb", 256), "max_cpu": plan.get("max_cpu", 0.5)}, "created": now_str, "expiry": expiry_str, "expiry_display": expiry_str[:10], "from_bot": True, "bot_telegram_id": int(tid)}
    else: return False, "Invalid category"
    
    save_users(users)
    bot_users[key]["servers"].append({"server_id": server_id, "type": category, "plan_id": plan.get("id"), "plan_name": plan.get("name"), "app_username": username, "app_password": password, "created_at": now_str, "expires_at": expiry_str, "status": "active", "last_warning": 0, "deleted": False})
    bot_users[key]["points"] = points - cost
    save_bot_users(bot_users)
    create_transaction(tid, "spend_server", -cost, category=category, plan_name=plan.get("name"), plan_id=plan.get("id"), server_id=server_id, app_username=username)
    return True, {"server_id": server_id, "username": username, "password": password, "ram": plan.get("ram"), "disk": plan.get("disk"), "cpu_limit": plan.get("cpu_limit"), "max_apps": plan.get("max_apps"), "max_sites": plan.get("max_sites"), "days": plan.get("days"), "expires_at": expiry_str, "points_spent": cost, "new_balance": points - cost}

def delete_server(tid, server_id):
    try: from app import load_users, save_users
    except: return False
    bot_users = load_bot_users(); key = str(tid)
    if key not in bot_users: return False
    target = next((s for s in bot_users[key].get("servers", []) if s.get("server_id") == server_id), None)
    if not target: return False
    users = load_users(); app_username = target.get("app_username")
    if app_username in users:
        users[app_username]["servers"] = [s for s in users[app_username].get("servers", []) if isinstance(s, dict) and s.get("server_id") != server_id]
        if target.get("type") in ("html", "api") or (not users[app_username].get("servers") and not users[app_username].get("sites")):
            del users[app_username]
        save_users(users)
    target["deleted"] = True; target["status"] = "deleted"; target["deleted_at"] = str(datetime.now())
    save_bot_users(bot_users)
    return True