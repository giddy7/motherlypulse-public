"""
Main module entry point for motherlypulse_app
Usage:
- Interactive CLI: python -m motherlypulse_app
- Local HTTP API Server: python -m motherlypulse_app --serve [port]
"""

import sys
from .cli import run_cli
from .server import run_server

def main():
    if "--serve" in sys.argv:
        port = 8080
        idx = sys.argv.index("--serve")
        if idx + 1 < len(sys.argv):
            try:
                port = int(sys.argv[idx + 1])
            except ValueError:
                port = 8080
        run_server(port)
    else:
        run_cli()

if __name__ == "__main__":
    main()

