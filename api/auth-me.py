"""GET /api/auth/me — Return current user info."""

from http.server import BaseHTTPRequestHandler
from _auth import get_current_user, send_json, handle_options


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        user = get_current_user(self.headers)
        if not user:
            send_json(self, 401, {"error": "Не авторизован"})
            return

        send_json(self, 200, {
            "email": user["email"],
            "role": user["role"],
        })

    def do_OPTIONS(self):
        handle_options(self)
