"""POST /api/auth/login — Authenticate and return JWT."""

from http.server import BaseHTTPRequestHandler
import json
from _auth import get_redis, verify_password, create_token, send_json, handle_options


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        except Exception:
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
            "user": {
                "email": user["email"],
                "role": user["role"],
            },
        })

    def do_OPTIONS(self):
        handle_options(self)
