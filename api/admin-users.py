"""
GET  /api/admin/users — List all users (admin only)
POST /api/admin/users — Update user role (admin only)
"""

from http.server import BaseHTTPRequestHandler
import json
from _auth import get_redis, get_current_user, send_json, handle_options


class handler(BaseHTTPRequestHandler):
    def _require_admin(self):
        user = get_current_user(self.headers)
        if not user or user.get("role") != "admin":
            send_json(self, 403, {"error": "Доступ запрещён"})
            return None
        return user

    def do_GET(self):
        if not self._require_admin():
            return

        redis = get_redis()
        emails = redis.smembers("users_index")
        users = []

        for email in sorted(emails):
            data = redis.get(f"user:{email}")
            if data:
                user = json.loads(data) if isinstance(data, str) else data
                users.append({
                    "email": user["email"],
                    "role": user["role"],
                    "created_at": user.get("created_at", ""),
                })

        send_json(self, 200, {"users": users})

    def do_POST(self):
        admin = self._require_admin()
        if not admin:
            return

        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        except Exception:
            send_json(self, 400, {"error": "Invalid JSON"})
            return

        email = (body.get("email") or "").strip().lower()
        new_role = body.get("role", "")

        if new_role not in ("pending", "approved", "admin"):
            send_json(self, 400, {"error": "Роль должна быть: pending, approved или admin"})
            return

        redis = get_redis()
        user_data = redis.get(f"user:{email}")

        if not user_data:
            send_json(self, 404, {"error": "Пользователь не найден"})
            return

        user = json.loads(user_data) if isinstance(user_data, str) else user_data
        user["role"] = new_role
        redis.set(f"user:{email}", json.dumps(user))

        send_json(self, 200, {"success": True, "email": email, "role": new_role})

    def do_OPTIONS(self):
        handle_options(self)
