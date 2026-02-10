from typing import TYPE_CHECKING
import logging
from backend.handlers.dbWrapper import server_interact_with_row
from backend.memory import ObjectNotFoundError, DataExpiredError, Memory
from secrets import token_urlsafe
from time import time
from http import HTTPStatus
from http.cookies import BaseCookie, _unquote, _quote
import json


class SimpleCookie(BaseCookie):
    """
    SimpleCookie supports strings as cookie values.  When setting
    the value using the dictionary assignment notation, SimpleCookie
    calls the builtin str() to convert the value to a string.  Values
    received from HTTP are kept as strings.
    """

    def value_decode(self, val):
        return _unquote(val), val

    def value_encode(self, val):
        strval = str(val)
        return strval, _quote(strval)

    def __getitem__(self, key):
        cookie = self.get(key, None)
        return None if cookie is None else cookie.value


if TYPE_CHECKING:
    from backend.router.RequestHandler import request_handler

backendMemory = Memory("backendMemory")
backendMemory.add_container("get_request_limiting")
backendMemory.add_container("request_limiting")

logger = logging.getLogger(__name__)

REQUESTS_RATE_LIMITING_CAP = 50
GET_REQUESTS_RATE_LIMITING_CAP = 500
RATE_LIMITING_INTERVAL = 30
ROLES = {
    "public": 0,
    "account": 1,
    "admin": 2,
    "developer": 3,
}


def server_firewall(self: request_handler) -> bool:
    """Responsible for setting security, parsing, and setting the
    context for the request.

    Returns True if the request was not blocked.
    """
    # Getting cookies
    self.cookies = SimpleCookie()
    self.cookies.load(self.headers.get("cookie", {}))

    # Rate Limiting
    if self.command == "GET":
        result = _increment_rate_limit(
            self, "get_request_limiting", GET_REQUESTS_RATE_LIMITING_CAP
        )
    else:
        result = _increment_rate_limit(
            self, "request_limiting", REQUESTS_RATE_LIMITING_CAP
        )
    if not result:
        return False

    # Parsing request
    _parse_path(self)

    if self.command not in ["HEAD", "GET"]:
        return parse_request_body(self)
    return True


def _increment_rate_limit(
    self: request_handler, container: str, cap: int
) -> bool:
    """
    Limits the amount of requests that the server will handle in order to protect
    from DDOS attacks.

    Invoked by the server firewall.
    """
    request_identifier = get_request_identifier(self)
    try:
        requests_amount = backendMemory.retrieve_data(
            container, request_identifier
        )
        payload = backendMemory.memory[container].get(request_identifier)
        if requests_amount >= cap:
            remaining = 0
            if payload is not None:
                remaining = max(
                    0, int(payload.expiration_time - time())
                )
            self.send_error(
                HTTPStatus.TOO_MANY_REQUESTS,
                f"Try again in {remaining} seconds.",
            )
            return False
        if payload is not None:
            payload.data = requests_amount + 1
        else:
            backendMemory.add_data(
                container,
                request_identifier,
                RATE_LIMITING_INTERVAL,
                requests_amount + 1,
                overwrite=True,
            )
        return True
    except (ObjectNotFoundError, DataExpiredError):
        backendMemory.add_data(
            container,
            request_identifier,
            RATE_LIMITING_INTERVAL,
            1,
            overwrite=True,
        )
        return True


def _parse_path(self: request_handler) -> None:
    """
    Parses the path and initialises path variables inside the class.

    Invoked by the server firewall.
    """
    self.full_path = self.path
    waste_path = self.path

    if "#" in waste_path:
        waste_path, self.fragment = waste_path.split("#", 1)
    else:
        self.fragment = None
    if "?" in waste_path:
        self.path, self.parameters = waste_path.split("?", 1)
    else:
        self.path = waste_path
        self.parameters = None

    self.path = self.path.replace("\\", "/")
    self.path = self.path.lower().strip()
    self.path = self.path.rstrip("/")
    return None


def get_request_identifier(self: request_handler):
    """
    Returns a unique and presistant request identifier.
    creates one if there isn't one.

    Since this doesn't do proper authentication it is possible for several clients to be
    under the same session_id and public_id. That's only possible through intentional
    tampering and it only effects the client, so it isn't secured against.
    """
    if self.cookies["session_id"] is not None:
        return self.cookies["session_id"]
    if self.cookies["public_id"] is not None:
        return self.cookies["public_id"]
    self.set_cookie("public_id", token_urlsafe(64))
    return self.cookies["public_id"]


def parse_request_body(self: request_handler) -> bool:
    """
    Parses the request body and sets it as an attribute of the class under
    self.parsed_request_body
    """
    length = self.headers.get("Content-Length", None)
    if length is None or length == 0:
        logger.debug(f"length is {length}", stack_info=True)
        self.parsed_request_body = ""
        return True
    try:
        length = int(length)
    except (ValueError, TypeError):
        self.send_error(
            HTTPStatus.BAD_REQUEST, "Invalid content-length header"
        )
        return False

    if length > 1500:
        self.send_error(
            HTTPStatus.BAD_REQUEST, "The request body is too long"
        )
        return False
    body = self.rfile.read(length).decode()
    try:
        body = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError) as err:
        print(err)
        self.send_error(HTTPStatus.BAD_REQUEST, "Expected format is JSON")
        return False

    self.parsed_request_body = body
    return True


def authenticate_request(self: request_handler) -> bool:
    """Uses the database to fully authenticate request then sets user information
    as a class attribute.

    Also sets self.is_logged_in.
    """
    self.user_information = {"role": ROLES["public"]}
    self.is_logged_in = False

    if self.cookies["session_id"] is None:
        return True

    cursor = server_interact_with_row(
        self,
        "accounts",
        "session_id",
        self.cookies["session_id"],
        "select",
    )

    if cursor is None:
        return False

    if isinstance(cursor, list):
        user_information = cursor[0] if cursor else None
    else:
        user_information = cursor

    if user_information is None:
        self.remove_cookie("session_id")
        return True

    self.is_logged_in = True
    self.user_information = dict(user_information)
    return True
