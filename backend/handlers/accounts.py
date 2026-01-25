from sqlite3 import (
    Error as SqlErr,
    IntegrityError as SqlIntegrityErr,
)
from secrets import token_urlsafe
import bcrypt
import email_validator
import json
from backend.handlers.dbWrapper import (
    server_interact_with_row,
    server_insert_row,
    server_update_cells,
    update_cells,  # For lower level control
)
import logging
from http import HTTPStatus
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.router.RequestHandler import request_handler

logger = logging.getLogger(__name__)

# These are all the fields that are provided and modifiable by the user.
USER_FIELDS = {"user_email", "user_password", "username"}
PASSWORD_MAX_LENGTH, USERNAME_MAX_LENGTH = 30
PASSWORD_MIN_LENGTH = 8
USERNAME_MIN_LENGTH = 3


def invalid_information(self, msg: str = "Invalid Information"):
    destroy_session(self)
    self.send_http_response(HTTPStatus.BAD_REQUEST, msg)
    return None


def post_account_handler(self: request_handler) -> None:
    """
    This handler validiates account information then creates an account in the
    database.

    ### Expected schema
    A normal dictionary
    >>> {
    >>> "key": value
    >>> "key": value
    >>> }
    """
    try:
        user_email = str(self.body["email"]).strip().lower()
        username = str(self.body["username"]).strip()
        user_password = str(self.body["password"]).strip()
    except ValueError:
        invalid_information(self)
        return None

    if (
        not is_valid_email(user_email)
        or not is_valid_username(username)
        or not is_valid_password(user_password)
    ):
        invalid_information()
        return None

    user_password = bcrypt.hashpw(user_password.encode(), bcrypt.gensalt()).decode()

    # --- Creating the account
    server_insert_row(
        self,
        "accounts",
        ("email", "password", "username"),
        (user_email, user_password, username),
        user_err_msg="Username Or Email Is Already In Use",
        send_response_on_success=True,
        strict=True,
    )
    return None


def post_session_handler(self: request_handler) -> None:
    try:
        target_email = str(self.body["email"])
        target_password = str(self.body["password"])
    except (ValueError, TypeError):
        self.send_http_response(HTTPStatus.BAD_REQUEST)
        return None

    cursor = server_interact_with_row(self, "accounts", "email", target_email, "select")
    results = cursor.fetchall()
    stored_password = results["password"]

    if bcrypt.checkpw(target_password.encode(), stored_password.encode()):
        if create_session(self, target_email):
            self.send_http_response(HTTPStatus.CREATED)
            return None
        self.send_http_response(HTTPStatus.INTERNAL_SERVER_ERROR)
        return None
    else:
        self.send_http_response(HTTPStatus.UNAUTHORIZED)
        return None


def delete_account_handler(self: request_handler) -> None:
    self.remove_cookie("session_id")
    server_interact_with_row(
        self,
        "accounts",
        "session_id",
        self.session_id,
        "delete",
        strict=True,
        send_response_on_success=True,
    )
    return None


def get_account_handler(self: request_handler) -> None:
    del self.user_information["id"]
    self.send_http_response(HTTPStatus.OK, json.dumps(self.user_information))
    return None


def patch_account_handler(self: request_handler) -> None:
    """
    Expected Schema:
    >>> {
    >>> field: [new-value, old_value]
    >>> field: [new-value, old_value]
    >>> }
    """
    dict.keys()
    fields = list(self.body.keys())
    new_values = list(field(0) for field in fields)
    old_values = list(field(1) for field in fields)
    if len(fields) != len(new_values) != len(old_values):
        self.send_http_response(HTTPStatus.BAD_REQUEST)
        return None

    if "password" in fields:
        pass_idx = fields.index("password")
        if not is_valid_password(new_values[pass_idx]):
            self.send_http_response(HTTPStatus.BAD_REQUEST)
        old_values[pass_idx] = bcrypt.hashpw(
            old_values[pass_idx].encode, bcrypt.gensalt()
        ).decode()
        new_values[pass_idx] = bcrypt.hashpw(
            new_values[pass_idx].encode, bcrypt.gensalt()
        ).decode()

    if "username" in fields:
        username_idx = fields.index("username")
        if not is_valid_username(new_values[username_idx]):
            self.send_http_response(HTTPStatus.BAD_REQUEST)

    if "email" in fields:
        email_idx = fields.index("email")
        if not is_valid_email(new_values[email_idx]):
            self.send_http_response(HTTPStatus.BAD_REQUEST)

    server_update_cells(
        self,
        "account",
        fields,
        old_values,
        fields,
        new_values,
        strict=True,
        second_search_column="id",
        second_search_value=self.user_information["id"],
        send_response_on_success=True,
    )
    return None


def get_session_handler(self: request_handler) -> None:
    (
        self.send_http_response(HTTPStatus.UNAUTHORIZED)
        if self.is_logged_in
        else self.send_http_response(HTTPStatus.OK)
    )
    return None


def delete_session_handler(self: request_handler) -> None:
    self.remove_cookie("session_id")
    server_update_cells(
        self,
        "accounts",
        ["session_id"],
        [self.cookies["session_id"]],
        ["session_id"],
        [None],
        strict=True,
        send_response_on_success=True,
    )
    return None


# -------------------
# Helper Functions:


def create_session(self: request_handler) -> bool:
    session_id = token_urlsafe(64)
    try:
        update_cells(
            "accounts",
            ["email"],
            [self.user_information["email"]],
            ["session_id"],
            session_id,
        )
        # UPDATE : Make it so sessions get removed automatically from the db after the
        # cookie expiry.
    except SqlIntegrityErr:
        try:
            return create_session(self)
        except RecursionError:
            return False
    except SqlErr:
        return False

    self.set_cookie("session_id", session_id)
    return True


def destroy_session(self: request_handler) -> int:
    if self.cookies["session_id"]:
        self.remove_cookie("session_id")
    else:
        return HTTPStatus.BAD_REQUEST
    try:
        update_cells(
            "accounts",
            ["session_id"],
            [self.cookies["session_id"]],
            ["session_id"],
            [None],
        )
    except SqlErr:
        return (HTTPStatus.INTERNAL_SERVER_ERROR,)

    return HTTPStatus.OK


nameRegex = r"^[a-zA-Z0-9]{2-80}$"


def is_valid_username(username: str) -> bool:
    """
    The password must be: inclusive of letters; under max-length; above min-length,
    and fully ASCII.

    Usernames like '999999999999999999a' are allowed, which could be an issue
    """
    if not isinstance(username, str):
        return False
    if len(username) > USERNAME_MAX_LENGTH or len(username) < USERNAME_MIN_LENGTH:
        return False
    if not username.isalnum() and not username.isalpha():
        return False
    if re.fullmatch(nameRegex, username) is None:
        return False
    return True


def is_valid_password(password: str) -> bool:
    """
    The password must be: alpha-numeric; under max-length; above min-length,
    and fully ASCII.
    """
    if not isinstance(password, str):
        return False
    if len(password) > PASSWORD_MAX_LENGTH or len(password) < PASSWORD_MIN_LENGTH:
        return False
    if not password.isalnum():
        return False
    if not password.isascii():
        return False
    return True


def is_valid_email(email: str) -> bool:
    if not isinstance(email, str):
        return False
    try:
        email_validator.validate_email(email)
        return True
    except email_validator.EmailNotValidError:
        return False
