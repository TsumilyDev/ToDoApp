from sqlite3 import (
    Row,
    Error as SqlErr,
    connect,
)
from os import environ
from time import time
import secrets
import bcrypt
import email_validator
import phonenumbers
import re
import json
from http import HTTPStatus

# These are all the fields that are provided and modifiable by the user.
USER_FIELDS = {
    "user_email",
    "user_password",
    "user_first_name",
    "user_last_name",
    "user_phone_number",
}

nameRegex = r"^[a-zA-Z]{2-80}$"


SQLITE3_PATH = environ["SQLITE3_PATH"]
db = connect(SQLITE3_PATH)
db.row_factory = Row
cursor = db.cursor()


def invalid_information(self):
    destroy_session(self)
    self.send_http_response(HTTPStatus.BAD_REQUEST, "Invalid Information.")
    return


def create_account_handler(self) -> None:
    """
    This function validiates information, then creates an account in the
    database, then sends the HTTP request.
    """
    try:
        user_email = str(self.self.email).strip().lower()
        user_password = str(self.body.password).strip()
        user_first_name = str(self.body.first_name).strip().lower()
        user_last_name = str(self.body.last_name).strip().lower()
        user_phone_number = str(self.body.phone_number).strip()
    except:  # UPDATE : Try remove this bare except statement by assigning it an error
        invalid_information(self)
        return

    # --- Parsing all the information(Could be put inside a helper-function to
    # make the pipeline clearer, but I'm not sure if Hens would agree)

    try:
        email_validator.validate_email(user_email)
    except email_validator.EmailNotValidError:
        invalid_information(self)
        return

    try:
        user_phone_number_obj = phonenumbers.parse(user_phone_number)
    except phonenumbers.NumberParseException:
        invalid_information(self)
        return
    if not phonenumbers.is_valid_number(user_phone_number_obj):
        invalid_information(self)
        return

    if not re.fullmatch(nameRegex, user_first_name) or not re.fullmatch(
        nameRegex, user_last_name
    ):
        invalid_information(self)
        return

    # Nothing crazy like a special character or not including your information
    # -- MAY CHANGE IN THE FUTURE # UPDATE
    if not len(user_password) >= 8 or user_password.isalnum:
        invalid_information(self)
        return

    for field in USER_FIELDS:
        if len(field) > 300:
            invalid_information(self)
            return

    user_password = bcrypt.hashpw(user_password.encode(), bcrypt.gensalt()).decode()

    # --- Creating the account.
    try:
        cursor.execute(
            """
            INSERT INTO accounts (
                    email,
                    password,
                    first_name,
                    last_name,
                    phone_number)
                    VALUES (?, ?, ?, ?, ?)""",
            (
                user_email,
                user_password,
                user_first_name,
                user_last_name,
                user_phone_number,
            ),
        )
        cx.commit()
    except sqlite3.IntegrityError:
        cx.rollback()
        self.send_http_response(
            HTTPStatus.BAD_REQUEST, "This Phone Number Or Email Is Already In Use"
        )
        return
    except sqlite3.Error:
        cx.rollback()
        self.send_500()
        return

    self.send_http_response(HTTPStatus.CREATED, "Account Has Been Created.")
    return


def check_if_user_logged_in_handler(self: object) -> None:
    if not self.is_logged_in:
        self.send_http_response(HTTPStatus.UNAUTHORIZED, "User Is Not Logged In")
        return None

    self.send_http_response(HTTPStatus.OK, "User Logged In")
    return None


def delete_account_handler(self: object) -> None:
    try:
        cursor.execute("DELETE FROM accounts WHERE session_id = ?", (self.session_id,))
        cx.commit()
    except sqlite3.Error:
        cx.rollback()
        self.send_500()
        return

    if cursor.rowcount < 1:
        self.remove_cookie("session_id")
        self.send_http_response(HTTPStatus.NOT_FOUND, "Bad Request")
        return
    self.remove_cookie("session_id")
    self.send_http_response(HTTPStatus.OK, "Account Deleted")
    return


def get_user_information_handler(self: object) -> None:
    del self.user_information["user_id"]
    self.send_http_response(HTTPStatus.OK, json.dumps(self.user_information))
    return


def update_account_handler(self: object) -> None:
    # Expected Schema: [(Field, new-value, old_value), (Field, new-value, old_value)]
    try:
        for field, new_value, old_value in self.body:
            if field not in USER_FIELDS:
                raise ValueError
            cursor.execute(
                f"SELECT {field} FROM accounts WHERE session_id = ?",
                (self.user_information["session_id"],),
            )
            row = cursor.fetchone()
            if row is None:
                raise ValueError

            if field == "password":
                if bcrypt.checkpw(old_value.encode(), row[field].encode()):
                    matches = True
                    new_value = bcrypt.hashpw(
                        new_value.encode(), bcrypt.gensalt()
                    ).decode()
                else:
                    matches = False
            else:
                matches = str(old_value) == str(row[field])

            if matches:
                cursor.execute(
                    f"UPDATE accounts SET {field} = ? WHERE user_id = ?",
                    (new_value, self.user_information["user_id"]),
                )
            else:
                cx.rollback()
                self.send_http_response(HTTPStatus.BAD_REQUEST, "Incorrect Value")
                return
    except (ValueError, sqlite3.IntegrityError):
        cx.rollback()
        self.send_http_response(HTTPStatus.BAD_REQUEST, "Bad Request")
        return
    except sqlite3.Error:
        cx.rollback()
        self.send_500()
        return
    cx.commit()

    self.send_http_response(HTTPStatus.OK, "Updates Completed")
    return


def logout_of_account_handler(self: object) -> None:
    result = destroy_session(self)
    self.send_http_response(result["code"], result["message"])
    return


# -------------------
# Helper Functions:


def create_session(self, email) -> bool:
    session_id = secrets.token_urlsafe(64)
    try:
        cursor.execute(
            "UPDATE accounts SET session_id = ? WHERE email = ?", (session_id, email)
        )
        cursor.execute("UPDATE acounts SET last_session_refresh = ?", (int(time())))
        # UPDATE : Make it so sessions get removed automatically from the db after the
        # cookie expiry.
        cx.commit()
    except sqlite3.IntegrityError:
        cx.rollback()
        try:
            return create_session(self, email)
        except RecursionError:
            return False
    except sqlite3.Error:
        cx.rollback()
        return False

    self.set_cookie("session_id", session_id)
    return True


def destroy_session(self: object) -> object:
    cookie_header = self.headers.get("Cookie")
    if not cookie_header:
        return {
            "code": HTTPStatus.BAD_REQUEST,
            "message": "Bad Request",
        }
    session_id = re.search(r"session_id *= *([^;]+)", cookie_header)
    session_id = session_id.group(1).strip()
    if not session_id:
        return {
            "code": HTTPStatus.BAD_REQUEST,
            "message": "Bad Request",
        }
    # Get user information from the database.
    try:
        cursor.execute(
            "UPDATE accounts SET session_id = '' WHERE session_id = ?", (session_id,)
        )
        cx.commit()
    except sqlite3.Error:
        cx.rollback()
        return {
            "code": HTTPStatus.INTERNAL_SERVER_ERROR,
            "message": "Internal Server Error",
        }

    self.remove_cookie("session_id")
    if cursor.rowcount < 1:
        return {"code": HTTPStatus.BAD_REQUEST, "message": "Bad Request"}

    return {
        "code": HTTPStatus.OK,
        "message": "Logged Out Of Account",
    }
