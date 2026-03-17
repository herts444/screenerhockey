"""
Auth endpoint — handles register, login, and me via query param.
POST /api/auth?action=register
POST /api/auth?action=login
GET  /api/auth?action=me
GET  /api/auth?action=debug  (temporary)
"""

from http.server import BaseHTTPRequestHandler
import json
import re
import os
import sys
from datetime import datetime
from urllib.parse import urlparse, parse_qs

# Ensure api/ directory is on Python path for shared module imports
sys.path.insert(0, os.path.dirname(__file__))

_auth_error = None
try:
    from auth_helpers import (
        get_redis, hash_password, verify_password, create_token,
        get_current_user, send_json, handle_options,
    )
except Exception as e:
    import traceback
    _auth_error = traceback.format_exc()


class handler(BaseHTTPRequestHandler):
    def _parse_action(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        return params.get("action", [""])[0]

    def _read_body(self):
        try:
            return json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        except Exception:
            return None

    def do_GET(self):
        if _auth_error:
            send_json(self, 500, {"error": "Auth module failed", "details": _auth_error})
            return

        action = self._parse_action()

        if action == "me":
            user = get_current_user(self.headers)
            if not user:
                send_json(self, 401, {"error": "Не авторизован"})
                return
            send_json(self, 200, {"email": user["email"], "role": user["role"]})
        else:
            send_json(self, 400, {"error": "Unknown action"})

    def do_POST(self):
        if _auth_error:
            send_json(self, 500, {"error": "Auth module failed", "details": _auth_error})
            return

        action = self._parse_action()

        if action == "register":
            self._handle_register()
        elif action == "login":
            self._handle_login()
        else:
            send_json(self, 400, {"error": "Unknown action"})

    def _handle_register(self):
        body = self._read_body()
        if not body:
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

        if redis.get(f"user:{email}"):
            send_json(self, 409, {"error": "Пользователь с таким email уже существует"})
            return

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

    def _handle_login(self):
        body = self._read_body()
        if not body:
            send_json(self, 400, {"error": "Invalid JSON"})
            return

        email = (body.get("email") or "").strip().lower()
        password = body.get("password") or ""

        if not email or not password:
            send_json(self, 400, {"error": "Email и пароль обязательны"})
            return

        redis = get_redis()
        user_data = redis.get(f"user:{email}")

        if not user_data:
            send_json(self, 401, {"error": "Неверный email или пароль"})
            return

        user = json.loads(user_data) if isinstance(user_data, str) else user_data

        if not verify_password(password, user["password_hash"]):
            send_json(self, 401, {"error": "Неверный email или пароль"})
            return

        token = create_token(email, user["role"])

        send_json(self, 200, {
            "success": True,
            "token": token,
            "user": {"email": user["email"], "role": user["role"]},
        })

    def do_OPTIONS(self):
        handle_options(self)
