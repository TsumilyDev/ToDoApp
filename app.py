from os import environ
from dotenv import load_dotenv
from typing import Any
from http.server import HTTPServer
from backend.router.RequestHandler import request_handler

load_dotenv()


def get_env(key: str) -> Any:
    try:
        return environ[key]
    except KeyError:
        raise RuntimeError(
            f"Could not find {key} inside the enviorment variables"
        )


PORT = int(get_env("PORT"))
DOMAIN = get_env("DOMAIN")

SERVER = HTTPServer((DOMAIN, PORT), request_handler, True)
print(f"Live at domain: {DOMAIN}, at port: {PORT}")
SERVER.serve_forever()
