"""Dependency check endpoint"""
from http.server import BaseHTTPRequestHandler
import json
import sys
import subprocess


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        results = {}

        # Check installed packages
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "list", "--format=json"],
                capture_output=True, text=True, timeout=10
            )
            packages = {p["name"]: p["version"] for p in json.loads(result.stdout)}
            results["installed_packages"] = packages
        except Exception as e:
            results["pip_list_error"] = str(e)

        # Check imports
        for mod_name, import_path in [("httpx", "httpx"), ("bs4", "bs4"), ("beautifulsoup4", "bs4.builder")]:
            try:
                __import__(import_path)
                results[f"import_{mod_name}"] = "OK"
            except Exception as e:
                results[f"import_{mod_name}"] = str(e)

        # Check which requirements.txt was used
        import os
        for path in ["/var/task/requirements.txt", "/var/task/api/requirements.txt"]:
            try:
                with open(path) as f:
                    results[f"file_{path}"] = f.read()
            except Exception as e:
                results[f"file_{path}"] = str(e)

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(results, indent=2).encode('utf-8'))
