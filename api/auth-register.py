"""POST /api/auth/register — Register a new user."""

from http.server import BaseHTTPRequestHandler
import json
import re
from datetime import datetime
from _auth import get_redis, hash_password, send_json, handle_options


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        except Exception:
            send_json(self, 400, {"error": "Invalid JSON"})
            return

        email = (body.get("email") or "").strip().lower()
        password = body.get("password") or ""

        if not email or not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
            send_json(self, 400, {"error": "Некорректный email"})
            return

        if len(password) < 6:
            send_json(self, 400, {"error": "Пароль минимум 6 символов"})
            return

        redis = get_redis()

        # Check if user already exists
        if redis.get(f"user:{email}"):
            send_json(self, 409, {"error": "Пользователь с таким email уже существует"})
            return

        # First user becomes admin
        members = redis.smembers("users_index")
        role = "admin" if not members or len(members) == 0 else "pending"

        user = {
            "email": email,
            "password_hash": hash_password(password),
            "role": role,
            "created_at": datetime.utcnow().isoformat(),
        }

        redis.set(f"user:{email}", json.dumps(user))
        redis.sadd("users_index", email)

        send_json(self, 201, {
            "success": True,
            "message": "Регистрация успешна" if role == "pending" else "Вы первый пользователь — вам выдана роль админа",
            "role": role,
        })

    def do_OPTIONS(self):
        handle_options(self)
