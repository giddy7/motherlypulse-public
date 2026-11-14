"""
MotherlyPulse Lightweight Local HTTP API Server
Built exclusively using Python standard library (http.server, json).
Zero external dependencies.
Endpoints:
- GET /health
- POST /api/chat
"""

import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Type
from .assistant import MotherlyPulseAssistant

class MotherlyPulseRequestHandler(BaseHTTPRequestHandler):
    assistant = MotherlyPulseAssistant()

    def do_GET(self):
        if self.path == "/health" or self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            payload = {
                "status": "healthy",
                "service": "MotherlyPulse Maternal & Infant Health Assistant API",
                "version": "1.1.0",
                "supported_languages": ["English", "Yoruba", "Nigerian Pidgin"],
                "triage_categories": ["EMERGENCY", "PRIORITY", "ROUTINE"]
            }
            self.wfile.write(json.dumps(payload, indent=2).encode("utf-8"))
        else:
            self.send_response(404)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode("utf-8"))

    def do_POST(self):
        if self.path == "/api/chat":
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length == 0:
                self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Empty request body"}).encode("utf-8"))
                return

            body = self.rfile.read(content_length).decode("utf-8")
            try:
                data = json.loads(body)
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": f"Invalid JSON: {str(e)}"}).encode("utf-8"))
                return

            message = data.get("message", "").strip()
            history = data.get("history", [])
            req_lang = data.get("language")

            if not message:
                self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Field 'message' is required"}).encode("utf-8"))
                return

            # 1. Run Dynamic Triage Classifier BEFORE language validation (Emergency is independent of language)
            triage = self.assistant.classifier.classify(message, history)
            if triage["urgency_category"] == "emergency":
                # Emergency must escalate immediately over HTTP regardless of language requested
                result = self.assistant.respond(message, conversation_history=history, language=req_lang)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(result, indent=2, ensure_ascii=False).encode("utf-8"))
                return

            target_lang = None
            if req_lang is not None:
                clean_lang = str(req_lang).strip()
                lang_mapping = {
                    "en": "English", "english": "English",
                    "yo": "Yoruba", "yoruba": "Yoruba",
                    "pcm": "Nigerian Pidgin", "pidgin": "Nigerian Pidgin", "nigerian pidgin": "Nigerian Pidgin"
                }
                if clean_lang.lower() not in lang_mapping:
                    self.send_response(400)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.end_headers()
                    err_payload = {
                        "error": f"Unsupported language '{clean_lang}'. Supported languages: English, Yoruba, Nigerian Pidgin."
                    }
                    self.wfile.write(json.dumps(err_payload, indent=2).encode("utf-8"))
                    return
                target_lang = lang_mapping[clean_lang.lower()]

            # Execute assistant pipeline for non-emergency inquiries
            result = self.assistant.respond(message, conversation_history=history, language=target_lang)

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(result, indent=2, ensure_ascii=False).encode("utf-8"))
        else:
            self.send_response(404)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode("utf-8"))

    def log_message(self, format, *args):
        # Clean logging
        pass

def run_server(port: int = 8080):
    server_address = ("127.0.0.1", port)
    httpd = HTTPServer(server_address, MotherlyPulseRequestHandler)
    print(f"MotherlyPulse HTTP API running on http://127.0.0.1:{port}")
    print("Endpoints: GET /health | POST /api/chat")
    httpd.serve_forever()

if __name__ == "__main__":
    run_server()

