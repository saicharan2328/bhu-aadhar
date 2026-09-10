import os
import sys

# Ensure backend directory is in path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from app import app

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="StrataMap 3D ULPIN REST Server")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", 8000)), help="Port to listen on")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host IP to bind to")
    args, _ = parser.parse_known_args()

    print(f"Starting StrataMap 3D ULPIN REST Server on http://127.0.0.1:{args.port} (Host: {args.host})")
    app.run(host=args.host, port=args.port, debug=True)
