from http.server import BaseHTTPRequestHandler
from http import HTTPStatus
from http.cookies import SimpleCookie
from backend.router.routes import routes
import logging
from sqlite3 import (
    Row,
    Error as sql_err,
    connect,
)
from os import environ
from memory import (
    ObjectNotFoundError,
    DataExpiredError,
    Memory
)
from secrets import token_urlsafe

backendMemory = Memory()
backendMemory.add_container("get_request_limiting")
backendMemory.add_container("request_limiting")

logger = logging.getLogger(__name__)
logger.addHandler()

SQLITE3_PATH = environ["SQLITE3_PATH"]

db = connect(SQLITE3_PATH)
db.row_factory = Row
cursor = db.cursor()

REQUESTS_RATE_LIMITING_CAP = 50
GET_REQUESTS_RATE_LIMITING_CAP = 500
RATE_LIMITING_INTERVAL = 30

ROLES = {
    "public": 0,
    "user": 1,
    "admin": 2,
    "developer": 3,
}

# Handler names from all files follow the same pattern: {method}_{name}_handler.

class request_handler(BaseHTTPRequestHandler):
    def __init__(self) -> None:
        self.server_locked: bool = False
        super.__init__()
        return None

    def handle_one_request(self) -> None:
        """Handle a single HTTP request."""
        if self.server_locked:
            self.requestline = ''
            self.request_version = ''
            self.command = ''
            self.send_error(HTTPStatus.SERVICE_UNAVAILABLE)
            return None
        self.close_connection = True
        self.response_headers = {}
        try:
            # No route in server should be longer than 399 characters
            self.raw_requestline = self.rfile.readline(400)
            if len(self.raw_requestline) > 399: 
                self.requestline = ''
                self.request_version = ''
                self.command = ''
                self.send_error(HTTPStatus.REQUEST_URI_TOO_LONG)
                return None

            if not self.raw_requestline:
                return None
            if not self.parse_request():
                return None
            try:
                if self.request_version.startswith("HTTP/"):
                    self.request_version_number = float(self.request_version[5:])
                else:
                    self.request_version_number = float(self.request_version)
                if self.request_version_number < 1.1:
                    self.send_error(HTTPStatus.HTTP_VERSION_NOT_SUPPORTED)
                    return None
            except Exception as error:
                print(error)
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR)
                return None 

            if not self.server_firewall():
                return None

            self.route()
        except TimeoutError as e:
            # Discarding this connection because a read or write timed out.
            self.log_error("Request timed out: %r", e)
            return None

    def server_firewall(self) -> bool:
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
            result = self._increment_rate_limit(
                "get_request_limiting", GET_REQUESTS_RATE_LIMITING_CAP)
        else:
            result = self._increment_rate_limit(
                "request_limiting", REQUESTS_RATE_LIMITING_CAP)
        if not result:
            return False

        # Parsing request
        self._parse_path()

        if self.command not in ["HEAD", "GET"]:
            return self.parse_request_body()
        return True

    def _increment_rate_limit(self, container:str, cap:int) -> bool:
        """
        Limits the amount of requests that the server will handle in order to protect
        from DDOS attacks. 

        Invoked by the server firewall.
        """
        request_identifier = self.get_request_identifier()
        try:
            requests_amount = backendMemory.retrieve_data(
                container,
                request_identifier
                ) 
            if requests_amount >= cap:
                self.send_error(
                    HTTPStatus.TOO_MANY_REQUESTS,
                    f"""Try again in
                    {backendMemory[container][request_identifier].ttl} seconds."""
                    )
                return False
            backendMemory[container][request_identifier] += 1
            return True
        except (ObjectNotFoundError, DataExpiredError):
            backendMemory.add_data(
                container,
                request_identifier,
                RATE_LIMITING_INTERVAL,
                1,
                overwrite = True
                )
            return True

    def _parse_path(self) -> None:
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
    
    def get_request_identifier(self):
        """
        Returns a unique and presistant request identifier.
        creates one if there isn't one.
        """
        if self.cookies["session_id"] is not None:
            return self.cookies["session_id"]
        if self.cookies["public_id"]:
            return self.cookies["public_id"]
        self.set_cookie("public_id") = token_urlsafe(64)
        return self.cookies["public_id"]

    def parse_request_body(self) -> bool:
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

    def authenticate_request(self) -> bool:
        """Uses the database to fully authenticate request then sets user information
        as a class attribute.
        
        Also sets self.is_logged_in.
        """
        if self.cookies["session_id"] is None:
            self.user_information["role"] = ROLES["public"]
            self.is_logged_in = False
            return True

        try:
            cursor.execute("SELECT * FROM accounts WHERE session_id = ?",
                           (self.cookies["session_id"],))
            user_information = cursor.fetchone()
        except sql_err:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR)
            self.is_logged_in = False
            return False

        if user_information is None:
            self.remove_cookie("session_id")
            self.user_information["role"] = ROLES["public"]
            self.is_logged_in = False
            return True

        self.is_logged_in = True
        self.user_information = dict(user_information)
        return True

    def send_http_response(
            self, code:int, *, body:bytes|str|None=None,
            body_type:str="application/json",
            content_length:None|int=None
        ) -> None:
        """Sends the HTTP response

        This automatically determines the content-length if the content-length is None, 
        otherwise, it will determine the content-length.

        Nothing can, or should, be done to the HTTP response after this is called.
        """
        if not isinstance(code, int):
            raise TypeError(f"Expected an integer but recieved {type(code)}")
        if not isinstance(body, bytes) and body is not None:
            # This will throw an error if body is not a string, that's intended.
            body = body.encode() 
        if content_length is None:
            content_length = len(body)
        self.response_headers["Content-Length"] = content_length
        self.response_headers["Content-Type"] = body_type
        for header, value in self.response_headers:
            self.send_header(header, value)
            continue
        self.end_headers()
        self.wfile.write(body)
        return None

    def route(self) -> None:
        method_routes: dict = routes.get(self.command)
        if method_routes is None:
            self.send_http_response(HTTPStatus.METHOD_NOT_ALLOWED)
            return None

        handler: dict = method_routes.get(self.path)
        if handler is None:
            self.send_http_response(HTTPStatus.NOT_FOUND)
            return None

        min_role = handler.get("role", 0)
        if min_role < ROLES["public"]:
            self.authenticate_request()
        if self.user_information["role"] < min_role:
            self.send_error(HTTPStatus.UNAUTHORIZED)
            return None

        if callable(handler):
            handler(self)
        else:
            open_mode = "rb" if handler.bytes else open_mode = "r"
            with open(handler.path, open_mode) as f:
                try:
                    file_info = f.read()
                except Exception as e:
                    logger.log(logging.ERROR, e, exc_info=True)
            self.send_http_response(200, body=file_info, type=handler[1])
        return None
        
    def set_cookie(
        self, key, value, /, *, 
        Max_Age=(60 * 60 * 24 * 365), SameSite="Strict"
        ) -> None:
        self.response_headers.append(("Set-Cookie",
            f"""{key}={value}; SameSite={SameSite};
            HttpOnly; Max-Age={Max_Age}; Path=/""",
        ))
        self.cookies[key] = value
        return None

    def remove_cookie(self, key:str) -> None:
        self.response_headers.append(("Set-Cookie", 
            f"""{key}=; SameSite=Strict; HttpOnly; Max-Age=0; Path=/"""
        ))
        del self.cookies[key]
        return None