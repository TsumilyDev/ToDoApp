from typing import TYPE_CHECKING
import logging
from backend.handlers.dbWrapper import server_interact_with_row
from memory import ObjectNotFoundError, DataExpiredError, Memory
from secrets import token_urlsafe
from http import HTTPStatus
from http.cookies import SimpleCookie

if TYPE_CHECKING:
    from backend.router.RequestHandler import request_handler

backendMemory = Memory()
backendMemory.add_container("get_request_limiting")
backendMemory.add_container("request_limiting")

logger = logging.getLogger(__name__)
logger.addHandler()

REQUESTS_RATE_LIMITING_CAP = 50
GET_REQUESTS_RATE_LIMITING_CAP = 500
RATE_LIMITING_INTERVAL = 30
ROLES = {
    "public": 0,
    "user": 1,
    "admin": 2,
    "developer": 3,
}


def server_firewall(self: request_handler) -> bool:
    """Responsible for setting security, parsing, and setting the
    context for the request.

    Returns True if the request was not blocked.
    """
    # Getting cookies
    cookie = SimpleCookie()
    cookie.load(self.headers.get("cookie", ""))
    self.cookies = cookie

    # Rate Limiting
    if self.command == "GET":
        result = _increment_rate_limit(
            "get_request_limiting", GET_REQUESTS_RATE_LIMITING_CAP
        )
    else:
        result = _increment_rate_limit("request_limiting", REQUESTS_RATE_LIMITING_CAP)
    if not result:
        return False

    # Parsing request
    _parse_path()

    if self.command not in ["HEAD", "GET"]:
        return parse_request_body()
    return True


def _increment_rate_limit(self: request_handler, container: str, cap: int) -> bool:
    """
    Limits the amount of requests that the server will handle in order to protect
    from DDOS attacks.

    Invoked by the server firewall.
    """
    request_identifier = get_request_identifier()
    try:
        requests_amount = backendMemory.retrieve_data(container, request_identifier)
        if requests_amount >= cap:
            self.send_error(
                HTTPStatus.TOO_MANY_REQUESTS,
                f"""Try again in
                {backendMemory[container][request_identifier].ttl} seconds.""",
            )
            return False
        backendMemory[container][request_identifier] += 1
        return True
    except (ObjectNotFoundError, DataExpiredError):
        backendMemory.add_data(
            container, request_identifier, RATE_LIMITING_INTERVAL, 1, overwrite=True
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
    """
    if self.cookies["session_id"] is not None:
        return self.cookies["session_id"]
    if self.cookies["public_id"]:
        return self.cookies["public_id"]
    self.set_cookie("public_id", token_urlsafe(64))
    return self.cookies["public_id"]


def parse_request_body(self: request_handler) -> bool:
    """
    Parses the request body and sets it as an attribute of the class under
    self.parsed_request_body
    """
    length = int(self.headers.get("Content-Length", None))
    if length > 1500:
        self.send_error(HTTPStatus.BAD_REQUEST)
        return False
    if length is None or length == 0:
        logger.debug(f"length is {length}", stack_info=True)
        self.parsed_request_body = ""
        return True
    self.parsed_request_body = self.rfile.read(length).decode()
    return True


def authenticate_request(self: request_handler) -> bool:
    """Uses the database to fully authenticate request then sets user information
    as a class attribute.

    Also sets self.is_logged_in.
    """
    if self.cookies["session_id"] is None:
        self.user_information["role"] = ROLES["public"]
        self.is_logged_in = False
        return True

    cursor = server_interact_with_row(
        self, "accounts", "session_id", self.cookies["session_id"], "select"
    )

    if cursor is None:
        self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR)
        self.is_logged_in = False
        return False
    user_information = cursor.fetchone()

    if user_information is None:
        self.remove_cookie("session_id")
        self.user_information["role"] = ROLES["public"]
        self.is_logged_in = False
        return True

    self.is_logged_in = True
    self.user_information = dict(user_information)
    return True
