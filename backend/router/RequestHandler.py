from http.server import BaseHTTPRequestHandler
from backend.router.routes import routes
from http import HTTPStatus
import logging
from backend.router.firewall import ROLES, authenticate_request

logger = logging.getLogger(__name__)

# Handler names from all files follow the same pattern: {method}_{name}_handler.


class request_handler(BaseHTTPRequestHandler):
    def __init__(self) -> None:
        self.server_locked: bool = False
        self.user_information: dict = {}
        self.is_logged_in: bool = False
        super.__init__()
        return None

    def handle_one_request(self) -> None:
        """Handle a single HTTP request."""
        if self.server_locked:
            self.requestline = ""
            self.request_version = ""
            self.command = ""
            self.send_error(HTTPStatus.SERVICE_UNAVAILABLE)
            return None
        self.close_connection = True
        self.response_headers = {}
        try:
            # No route in server should be longer than 399 characters
            self.raw_requestline = self.rfile.readline(400)
            if len(self.raw_requestline) > 399:
                self.requestline = ""
                self.request_version = ""
                self.command = ""
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

    def send_http_response(
        self,
        code: int,
        body: bytes | str | None = None,
        *,
        body_type: str = "text/plain",
        content_length: None | int = None,
    ) -> None:
        """Sends the HTTP response

        This automatically determines the content-length if the content-length is None,
        otherwise, it will determine the content-length.

        Nothing can, or should, be done to the HTTP response after this is called.
        """
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

        route_path: dict = method_routes.get(self.path)
        if route_path is None:
            self.send_http_response(HTTPStatus.NOT_FOUND)
            return None

        if isinstance(route_path, dict):
            min_role: int = route_path.get("min_role", 0)
        elif isinstance(route_path, tuple):
            handler, min_role = route_path
        else:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR)
            logger.error("Malicious Interal Route")
            return None

        if min_role > ROLES["public"]:
            authenticate_request(self)
        #     if self.user_information["role"] < min_role:
        #         self.send_error(HTTPStatus.UNAUTHORIZED)
        #         return None

        # if callable(route_path):
        #     route_path(self)
        # else:
        #     (open_mode := "rb") if route_path.bytes else (open_mode := "r")
        #     with open(route_path.path, open_mode) as f:
        #         try:
        #             file_info = f.read()
        #         except Exception as e:
        #             logger.log(logging.ERROR, e, exc_info=True)
        #     self.send_http_response(200, body=file_info, type=route_path[1])
        # return None

    def set_cookie(
        self, key, value, /, *, Max_Age=(60 * 60 * 24 * 365), SameSite="Strict"
    ) -> None:
        self.response_headers.append(
            (
                "Set-Cookie",
                f"""{key}={value}; SameSite={SameSite};
            HttpOnly; Max-Age={Max_Age}; Path=/""",
            )
        )
        self.cookies[key] = value
        return None

    def remove_cookie(self, key: str) -> None:
        self.response_headers.append(
            ("Set-Cookie", f"""{key}=; SameSite=Strict; HttpOnly; Max-Age=0; Path=/""")
        )
        del self.cookies[key]
        return None
