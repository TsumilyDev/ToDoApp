"""
Main entry point for the To-Do App backend server.

Environment Variables:
  - SQLITE3_PATH: Path to SQLite database file (default: ./data/todo.db)
  - PORT: Server port number (default: 8000)
  - BASE_URL: Server listening address (default: localhost)
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from http.server import HTTPServer
from backend.router.RequestHandler import request_handler

# Load environment variables from .env file
load_dotenv()


def get_env(key: str, default: str | None = None) -> str:
    """Get environment variable with optional default value."""
    value = os.environ.get(key, default)
    if value is None:
        raise RuntimeError(
            f"Required environment variable '{key}' not set and no default available"
        )
    return value


def validate_sqlite_path(db_path: str) -> Path:
    """
    Validate and prepare SQLite database path.
    
    - Creates parent directories if they don't exist
    - Verifies write permissions
    - Returns Path object to the database file
    """
    db_path_obj = Path(db_path).resolve()
    parent_dir = db_path_obj.parent
    
    # Create parent directories if they don't exist
    try:
        parent_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise RuntimeError(
            f"Failed to create database directory '{parent_dir}': {e}"
        ) from e
    
    # Check write permissions on parent directory
    if not os.access(parent_dir, os.W_OK):
        raise RuntimeError(
            f"No write permission for database directory: {parent_dir}"
        )
    
    # Check if database file exists and is writable, or if we can create it
    if db_path_obj.exists():
        if not os.access(db_path_obj, os.W_OK):
            raise RuntimeError(
                f"Database file exists but is not writable: {db_path_obj}"
            )
    
    return db_path_obj


def main():
    """Initialize and start the HTTP server."""
    # Get and validate configuration
    sqlite3_path = get_env("SQLITE3_PATH", "./data/todo.db")
    port = int(get_env("PORT", "8000"))
    base_url = get_env("BASE_URL", "localhost")
    
    # Validate database path before starting server
    try:
        db_path = validate_sqlite_path(sqlite3_path)
        print(f"✓ Database path validated: {db_path}")
    except RuntimeError as e:
        print(f"✗ Database validation failed: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Create and start server
    try:
        server = HTTPServer((base_url, port), request_handler)
        server.allow_reuse_address = True
        print(f"✓ Server starting on {base_url}:{port}")
        print(f"✓ Database: {db_path}")
        server.serve_forever()
    except OSError as e:
        print(f"✗ Failed to start server: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nServer shutting down...")
        sys.exit(0)


if __name__ == "__main__":
    main()
