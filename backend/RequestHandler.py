from http.server import BaseHTTPRequestHandler
from http import HTTPStatus
from http.cookies import SimpleCookie

# Handler names from all files follow the same pattern: {method}_{name}_handler.

class request_handler(BaseHTTPRequestHandler):
    def handle_one_request(self):
        """Handle a single HTTP request."""
        self.close_connection = True
        try:
            # No status line request to this server should be longer than 400 characters
            self.raw_requestline = self.rfile.readline(400)
            if len(self.raw_requestline) > 399: 
                self.requestline = ''
                self.request_version = ''
                self.command = ''
                self.send_error(HTTPStatus.REQUEST_URI_TOO_LONG)
                return

            if not self.raw_requestline:
                return
            if not self.parse_request():
                return
            try:
                if self.request_version.startswith("HTTP/"):
                    self.request_version_number = float(self.request_version[5:])
                else:
                    self.request_version_number = float(self.request_version)
                if self.request_version_number < 1.1:
                    self.send_error(HTTPStatus.HTTP_VERSION_NOT_SUPPORTED)
                    return

                cookie = SimpleCookie()
                cookie.load(self.headers.get("cookie", ""))
                self.session_id = (
                    cookie["session_id"].value if "session_id" in cookie else None
                    )
            except Exception as error:
                print(error)
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR)
                return 

            if not self.server_firewall():
                return

            self.route()
        except TimeoutError as e:
            # Discarding this connection because a read or write timed out.
            self.log_error("Request timed out: %r", e)
            self.close_connection = True
            return

    def route(self):
        ...