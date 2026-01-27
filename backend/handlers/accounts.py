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
    update_cell,  # For lower level control
)
import logging
from http import HTTPStatus
from typing import TYPE_CHECKING
from valid8r import from_type, Maybe
import string

if TYPE_CHECKING:
    from backend.router.RequestHandler import request_handler

logger = logging.getLogger(__name__)

# These are all the fields that are provided and modifiable by the user.
USER_FIELDS = {"user_email", "user_password", "username"}
PASSWORD_MAX_LENGTH, USERNAME_MAX_LENGTH = 30, 30
PASSWORD_MIN_LENGTH, USERNAME_MIN_LENGTH = 8, 3


def server_validate_schema(
    self, annotation, *, send_failure_message=True
) -> None | Maybe:
    """
    Validates the schema, sending an HTTP response on failure.
    Returns None.
    """
    parser = from_type(annotation)
    # Implement a schema validator yourself to avoid all these annoyances and
    # preformance issues, # UPDATE
    result = parser(json.dumps(self.parsed_request_body))
    if result.value_or(None) is None:
        logger.debug("Schema failed")
        print("Class A")
        if send_failure_message:
            self.send_http_response(
                HTTPStatus.BAD_REQUEST, result.error_or("")
            )
            return None
        else:
            self.send_http_response(HTTPStatus.BAD_REQUEST)
            return None
    print("Class B")
    return result


def invalid_information(self, msg: str = "Invalid Information"):
    print("bruh")
    destroy_session(self)
    self.send_http_response(HTTPStatus.BAD_REQUEST, msg)
    return None


def post_account_handler(self: request_handler) -> None:
    """
    This handler validiates account information then creates an account in the
    database.

    ### Expected schema:
    A normal dictionary
    >>> {
    >>> "email": value
    >>> "username": value
    >>> "password": value
    >>> }
    """

    try:
        user_email: str = self.parsed_request_body["email"].strip().lower()
        username: str = self.parsed_request_body["username"].strip()
        user_password: str = self.parsed_request_body["password"].strip()
    except (KeyError, ValueError, TypeError) as err:
        print("Failed")
        print(err)
        invalid_information(self)
        return None

    if (
        not is_valid_email(user_email)
        or not is_valid_username(username)
        or not is_valid_password(user_password)
    ):
        print("Hmmm")
        invalid_information(self)
        return None

    user_password = bcrypt.hashpw(
        user_password.encode(), bcrypt.gensalt()
    ).decode()

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
    # UPDATE: Make this be able to use emails OR usernames
    """
    ### Expected schema:
    >>> {
    >>> "email": value
    >>> "password": value
    >>> }
    """

    if server_validate_schema(self, dict[str, str]) is None:
        return None

    if len(self.parsed_request_body) > 2:
        invalid_information(self)
        return None

    try:
        target_email = str(
            self.parsed_request_body["email"].lower().strip()
        )
        target_password = str(self.parsed_request_body["password"].strip())
    except (KeyError, ValueError, TypeError):
        invalid_information(self)
        return None

    results = server_interact_with_row(
        self, "accounts", "email", target_email, "select"
    )
    if results is None:
        return None
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
        self.cookies["session_id"],
        "delete",
        strict=True,
        send_response_on_success=True,
    )
    return None


def get_account_handler(self: request_handler) -> None:
    del self.user_information["id"]
    self.send_http_response(
        HTTPStatus.OK, json.dumps(self.user_information)
    )
    return None


def patch_account_handler(self: request_handler) -> None:
    """
    ### Expected Schema:
    >>> {
    >>> field: [new-value, old_value]
    >>> field: [new-value, old_value]
    >>> }
    """

    if server_validate_schema(self, dict[str, list[str, str]]) is None:
        return None

    fields = list(self.parsed_request_body.keys())
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


def create_session(self: request_handler, target_email: str) -> bool:
    session_id = token_urlsafe(64)
    try:
        update_cell(
            "accounts",
            "email",
            target_email,
            "session_id",
            session_id,
        )
        # UPDATE : Make it so sessions get removed automatically from the db after the
        # cookie expiry.
    except SqlIntegrityErr:
        try:
            return create_session(self, target_email)
        except RecursionError:
            return False
    except SqlErr:
        return False

    self.set_cookie("session_id", session_id)
    return True


def destroy_session(self: request_handler) -> int:
    if self.cookies["session_id"] is not None:
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


VALID_USERNAME_CHARACTERS = (
    {"-", "_", "."} | set(string.ascii_letters) | set(string.digits)
)


def is_valid_username(username: str) -> bool:
    """
    The username must be: valid-characters; under max-length; above min-length.

    Usernames like '999999999999999999a' are allowed, which could be an issue
    """
    if not isinstance(username, str):
        logger.debug("Username is not valid")
        print("Username is not valid instance(username, str):")
        return False
    if (
        len(username) > USERNAME_MAX_LENGTH
        or len(username) < USERNAME_MIN_LENGTH
    ):
        logger.debug("Username is not valid")
        print("Username is not valid ername) > USERNAME_MAX_LENGTH or")
        return False
    for char in username:
        if char not in VALID_USERNAME_CHARACTERS:
            logger.debug("Username is not valid")
            print("Username is not valid ername.isalnum() and not")
            return False
    logger.debug("Username is valid")
    print("valid user")
    return True


VALID_PASSWORD_CHARACTERS = (
    {"-", "_", ".", "@"} | set(string.ascii_letters) | set(string.digits)
)


def is_valid_password(password: str) -> bool:
    """
    The password must be: valid-characters; under max-length; and above min-length.

    This doesn't require having both letters and numbers, which is a weakness.
    """
    if not isinstance(password, str):
        logger.debug("Password is not valid")
        return False
    if (
        len(password) > PASSWORD_MAX_LENGTH
        or len(password) < PASSWORD_MIN_LENGTH
    ):
        logger.debug("Password is not valid")
        return False
    for char in password:
        if char not in VALID_PASSWORD_CHARACTERS:
            logger.debug("Password is not valid")
            print("Password is not valid ername.isalnum() and not")
            return False
    logger.debug("Password is valid")
    print("Valid pass")
    return True


def is_valid_email(email: str) -> bool:
    if not isinstance(email, str):
        logger.debug("Email is not valid")
        return False
    try:
        email_validator.validate_email(email)
        logger.debug("Email is valid")
        print("Valid mail")
        return True
    except email_validator.EmailNotValidError:
        logger.debug("Email is not valid")
        return False
