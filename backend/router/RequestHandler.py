from http.server import BaseHTTPRequestHandler
from backend.router.routes import routes
from http import HTTPStatus
import logging
from backend.router.firewall import (
    server_firewall,
    ROLES,
    authenticate_request,
    backendMemory,
)
from backend.memory import ObjectNotFoundError, DataExpiredError

backendMemory.add_container(
    "loaded_files", "This container stores files that have been retrived"
)

logger = logging.getLogger(__name__)

# Handler names from all files follow the same pattern: {method}_{name}_handler.


class request_handler(BaseHTTPRequestHandler):
    def setup(self):
        super().setup()
        self.backend_locked: bool = False
        self.log_requests: bool = True

    def handle_one_request(self) -> None:
        """Handle a single HTTP request."""
        if self.backend_locked:
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
                    self.request_version_number = float(
                        self.request_version[5:]
                    )
                else:
                    self.request_version_number = float(
                        self.request_version
                    )
                if self.request_version_number < 1.1:
                    self.send_error(HTTPStatus.HTTP_VERSION_NOT_SUPPORTED)
                    return None
            except Exception as err:
                logger.error(err, exc_info=True)
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR)
                return None

            if not server_firewall(self):
                return None

            self.route()
        except TimeoutError as err:
            # Discarding this connection because a read or write timed out.
            self.log_error("Request timed out: %r", err)
            return None

    def log_request(self, code="-", size="-") -> None:
        """Log an accepted request.

        This is called by send_response().
        """
        if not self.log_requests:
            return None
        if isinstance(code, HTTPStatus):
            code = code.value
        self.log_message(
            '"%s" %s %s', self.requestline, str(code), str(size)
        )
        return None

    def send_http_response(
        self,
        code: int,
        body: bytes | str | None = None,
        /,
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
            try:
                body = body.encode()
            except (ValueError, TypeError) as err:
                logger.error(
                    "The server contains a malicious handler that returned"
                    f" the body {body}",
                    err,
                    exc_info=True,
                )
                return None
        self.send_response(code)
        if content_length is None and body is not None:
            content_length = len(body)
        self.response_headers["Content-Length"] = content_length
        self.response_headers["Content-Type"] = body_type
        for header, value in self.response_headers.items():
            self.send_header(header, value)
            continue
        self.end_headers()
        if body is not None:
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
        # A dict is a resource whereas a tuple is a handler
        # A resource is a file-like structure that requires reading
        if isinstance(route_path, dict):
            min_role: int = route_path.get("min_role", 0)
            route_path_type = "resource"
        elif isinstance(route_path, tuple):
            handler, min_role = route_path
            route_path_type = "handler"
        else:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR)
            logger.error(
                "Malicious Internal Route", route_path, exc_info=True
            )
            return None

        if min_role > ROLES["public"]:
            authenticate_request(self)
            if self.user_information["role"] < min_role:
                self.send_error(HTTPStatus.UNAUTHORIZED)
                return None

        if route_path_type == "handler":
            handler(self)
        else:
            self.resource_handler(route_path)
        return None

    def resource_handler(self, resource) -> None:
        # UPDATE: Consider sending the file directly from the kernal to the client
        # in order to maximize preformance
        try:
            file_info = backendMemory.retrieve_data(
                "loaded_files", resource["path"]
            )
            self.send_http_response(
                HTTPStatus.OK, file_info, body_type=resource["type"]
            )
            return None
        except (ObjectNotFoundError, DataExpiredError):
            pass
        (open_mode := "rb") if resource["bytes"] else (open_mode := "r")
        try:
            with open(resource["path"], open_mode) as f:
                file_info = f.read()
                self.send_http_response(
                    HTTPStatus.OK, file_info, body_type=resource["type"]
                )
                # UPDATE: Expiring this won't help with anything since the backendMemory
                # gets rid of data lazily. The memory class should not be lazy in order
                # to be more memory efficient.
                backendMemory.add_data(
                    "loaded_files", resource["path"], 30 * 60, file_info
                )
                return None
        except (OSError, IOError, FileNotFoundError) as err:
            logger.error(err, exc_info=True)
            self.send_http_response(HTTPStatus.INTERNAL_SERVER_ERROR)
            return None

    def set_cookie(
        self,
        key,
        value,
        /,
        *,
        Max_Age=(60 * 60 * 24 * 365),
        SameSite="Strict",
    ) -> None:
        self.response_headers["Set-Cookie"] = (
            f"""{key}={value}; SameSite={SameSite};
            HttpOnly; Max-Age={Max_Age}; Path=/""",
        )
        self.cookies[key] = value
        return None

    def remove_cookie(self, key: str) -> None:
        self.response_headers["Set-Cookie"] = (
            f"""{key}=; SameSite=Strict;
            HttpOnly; Max-Age=0; Path=/""",
        )
        del self.cookies[key]
        return None
